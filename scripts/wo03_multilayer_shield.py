"""Execute a bounded multilayer-foil correction using actual fixed-mode CAD copies.

The existing opaque-wall thermal solver supplies heat transfer; this runner only
constructs candidate parts, consistent serial spacer links and source-bound cases.
No active specification, material screen or operating boundary is changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_thermal_matrix import (
    apply_mount_bond_geometry,
    case_config,
    identity,
    make_topology,
    mass_record,
    rebuild_part_mass,
    summarize_thermal,
)
from src.analysis.thermal_topology import run_thermal_topology
from src.cad.assembly import rigid_intersections
from src.cad.parts import local_shape
from src.vehicle.cad_contract import digest
from src.vehicle.schema import Part, Vehicle, load_vehicle, vehicle_input_paths

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-multilayer-shield.yaml"


def subtract_intervals(
    start: float, end: float, cuts: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    """Physical shield intervals; removed ring windows never become opaque coverage."""
    intervals = [(start, end)]
    for lo, hi in sorted(cuts):
        remaining = []
        for a, b in intervals:
            if hi <= a or lo >= b:
                remaining.append((a, b))
            else:
                if a < lo:
                    remaining.append((a, lo))
                if hi < b:
                    remaining.append((hi, b))
        intervals = remaining
    return intervals


def append_spacers(
    vehicle: Vehicle,
    study: dict[str, Any],
    cfg: dict[str, Any],
    previous: Part,
    shield: Part,
    original: Part,
) -> None:
    for side, z in (
        ("front", shield.position_m),
        ("aft", shield.position_m + shield.geometry["length_m"] - cfg["spacer_axial_length_m"]),
    ):
        raw = original.model_dump(by_alias=True)
        inner_r = previous.geometry["radius_m"]
        outer_r = shield.geometry["inner_radius_m"]
        raw.update(
            id=f"shield_spacer_{shield.id}_{side}",
            parent=previous.id,
            position_m=z,
            material="mica",
            cad_mass=None,
            cg_offset_m=cfg["spacer_axial_length_m"] / 2,
        )
        raw["geometry"] = {
            "radius_m": outer_r,
            "inner_radius_m": inner_r,
            "wall_m": outer_r - inner_r,
            "length_m": cfg["spacer_axial_length_m"],
        }
        raw["engineering"]["material_profile"] = "mica"
        if cfg.get("spacer_sector_angle_deg") is not None:
            raw["cad"]["generator"] = "sector_pads"
            raw["cad"]["parameters"] = {"sector_angle_deg": cfg["spacer_sector_angle_deg"]}
        spacer = Part.model_validate(raw)
        rebuild_part_mass(spacer)
        vehicle.parts.append(spacer)
        study["part_ids"].append(spacer.id)
        study["pad_conduction_part_ids"].append(spacer.id)
        study.setdefault("pad_conduction_thickness_m", {})[spacer.id] = outer_r - inner_r
        study["contact_pairs"].extend([[previous.id, spacer.id], [spacer.id, shield.id]])
        for a, b in ((previous.id, spacer.id), (spacer.id, shield.id)):
            study.setdefault("contact_pair_conductance_w_k", {})[f"{a}->{b}"] = cfg["scope"][
                "interface_contact_conductance_w_k"
            ]


def construct_candidate(
    vehicle: Vehicle, cfg: dict[str, Any], radii: list[float], base_topology: dict[str, Any]
) -> tuple[Vehicle, dict[str, Any], dict[str, Any]]:
    """Return an isolated copy; spacers bridge adjacent shields at their real ends."""
    vehicle = vehicle.model_copy(deep=True)
    parts = {p.id: p for p in vehicle.parts}
    mount = parts["motor_mount"]
    original = parts["motor_radiant_shield"]
    if mount.cad is None or mount.cad.generator != "mount":
        raise ValueError("This study supports fixed mounts only, not a moving cassette")
    if radii != sorted(set(radii)):
        raise ValueError("Additional shield radii must be unique and increasing")
    if radii and radii[0] <= original.geometry["radius_m"] + cfg["foil_wall_m"]:
        raise ValueError("Shield radii must leave a positive gap beyond the original foil")
    nominal = mass_record(vehicle)
    gap = float(cfg["scope"]["fixed_mount_radial_bond_gap_m"])
    bond = apply_mount_bond_geometry(vehicle, gap)
    bore = float(mount.geometry["inner_radius_m"])
    preserve_rings = bool(cfg.get("preserve_ring_bores", False))
    if not preserve_rings and radii:
        bore = radii[-1] + cfg["mount_bore_radial_clearance_m"]
        mount.geometry["inner_radius_m"] = bore
        mount.cad.parameters["ring_inner_radii_mm"] = [
            1000 * bore for _ in mount.cad.parameters["ring_stations_mm"]
        ]
    ring_cuts = (
        [
            (
                mount.position_m + station * 0.001 - cfg["ring_axial_clearance_m"],
                mount.position_m + (station + width) * 0.001 + cfg["ring_axial_clearance_m"],
            )
            for station, width in zip(
                mount.cad.parameters["ring_stations_mm"],
                mount.cad.parameters.get(
                    "ring_thicknesses_mm",
                    [mount.cad.parameters["ring_thickness_mm"]]
                    * len(mount.cad.parameters["ring_stations_mm"]),
                ),
                strict=True,
            )
        ]
        if preserve_rings
        else []
    )
    mount_props = rebuild_part_mass(mount)
    bond.update(
        mount_shape_sha256=mount_props["shape_sha256"],
        mount_mass_kg=mount.resolved_mass_kg,
        mount_volume_m3=mount_props["volume_m3"],
    )
    study = make_topology(base_topology, vehicle, cfg["scope"]["interface_contact_conductance_w_k"])
    blocks = mount.cad.parameters.get("retainer_blocks", [])
    if not blocks:
        raise ValueError("Explicit aft retention block geometry is required")
    added: list[dict[str, Any]] = []
    previous_layer = [original]
    for i, radius in enumerate(radii):
        start = original.position_m + cfg["front_axial_clearance_m"]
        end = original.position_m + original.geometry["length_m"]
        for block in blocks:
            inner = (block["position_mm"][0] - block["size_mm"][0] / 2) * 0.001
            if radius >= inner - cfg["mount_bore_radial_clearance_m"]:
                end = min(
                    end,
                    mount.position_m
                    + block["position_mm"][2] * 0.001
                    - cfg["retention_axial_clearance_m"],
                )
        if end - start <= 2 * cfg["spacer_axial_length_m"]:
            raise ValueError("No usable shield interval remains ahead of retention")
        layer = []
        for j, (a, b) in enumerate(subtract_intervals(start, end, ring_cuts)):
            if b - a <= 2 * cfg["spacer_axial_length_m"]:
                raise ValueError("Ring window leaves an unsupported short shield segment")
            previous = next(
                p
                for p in previous_layer
                if p.position_m <= a + 1e-10 and p.position_m + p.geometry["length_m"] >= b - 1e-10
            )
            raw = original.model_dump(by_alias=True)
            raw.update(
                id=f"additional_shield_{i + 1}_{j + 1}",
                cad_mass=None,
                position_m=a,
            )
            raw["cg_offset_m"] = (b - a) / 2
            raw["geometry"].update(
                radius_m=radius,
                inner_radius_m=radius - cfg["foil_wall_m"],
                wall_m=cfg["foil_wall_m"],
                length_m=b - a,
            )
            shield = Part.model_validate(raw)
            rebuild_part_mass(shield)
            vehicle.parts.append(shield)
            study["part_ids"].append(shield.id)
            study["annular_barrier_part_ids"].append(shield.id)
            added.append({"id": shield.id, "radius_m": radius, "start_m": a, "end_m": b})
            append_spacers(vehicle, study, cfg, previous, shield, original)
            layer.append(shield)
        previous_layer = layer
    solids = {
        p.id: local_shape(p).translate(
            (1000 * p.lateral_offset_m[0], -1000 * p.lateral_offset_m[1], 1000 * p.position_m)
        )
        for p in vehicle.parts
        if p.cad
    }
    intersections = rigid_intersections(vehicle, solids)
    return (
        vehicle,
        study,
        {
            "nominal_mass_cg_inertia": nominal,
            "candidate_mass_cg_inertia": mass_record(vehicle),
            "mount_bore_radius_m": bore,
            "preserve_ring_bores": preserve_rings,
            "ring_windows_with_clearance_m": ring_cuts,
            "mount_bond_geometry": bond,
            "shield_intervals": added,
            "all_nominal_intersections": intersections,
            "new_part_intersections": [
                row
                for row in intersections
                if any(
                    str(value).startswith(("additional_shield_", "shield_spacer_"))
                    for value in row.values()
                )
            ],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--mode", choices=("G80", "G54"), default="G54")
    parser.add_argument("--candidate", default="four_total_foils")
    parser.add_argument("--preset", choices=("tiny", "sim"), default="tiny")
    parser.add_argument("--spacers", choices=("full_ring", "three_10deg_pads"), default="full_ring")
    parser.add_argument("--rings", choices=("preserved", "enlarged"), default="enlarged")
    args = parser.parse_args()
    started = time.perf_counter()
    args.config = args.config.resolve()
    cfg = yaml.safe_load(args.config.read_text())
    cfg["spacer_sector_angle_deg"] = cfg["spacer_variants"][args.spacers]
    cfg["preserve_ring_bores"] = args.rings == "preserved"
    matrix_path = ROOT / cfg["acceptance_matrix"]
    matrix = yaml.safe_load(matrix_path.read_text())
    source = ROOT / cfg["configurations"][args.mode]
    engineering_path = ROOT / matrix["engineering_inputs"]
    topology_path = ROOT / matrix["thermal_topology"]
    engineering = yaml.safe_load(engineering_path.read_text())
    topology = yaml.safe_load(topology_path.read_text())
    selection = next(row for row in cfg["candidates"] if row["id"] == args.candidate)
    case = next(row for row in matrix["cases"] if row["id"] == cfg["scope"]["required_case"])
    corner = next(
        row
        for row in matrix["material_property_uncertainty"]["factors"]
        if row["id"] == cfg["scope"]["material_corner"]
    )
    paths = [
        source,
        args.config,
        matrix_path,
        engineering_path,
        topology_path,
        Path(__file__),
        ROOT / cfg["source_record"],
        ROOT / "scripts/wo03_thermal_matrix.py",
        ROOT / "src/vehicle/mass.py",
        ROOT / "src/vehicle/materials.py",
        ROOT / "src/vehicle/schema.py",
        ROOT / "src/vehicle/cad_contract.py",
        ROOT / "src/analysis/engineering.py",
    ]
    paths += list(vehicle_input_paths(source))
    paths += list((ROOT / "src/cad").glob("*.py"))
    paths += [ROOT / "src/analysis/thermal_topology.py", ROOT / "src/analysis/thermal_radial.py"]
    before = {
        str(p.resolve().relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in paths
    }
    run_id = "wo03-multilayer-shield-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "runs" / run_id
    folder.mkdir(parents=True)
    for name, expected in before.items():
        data = (ROOT / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("Source changed during immutable snapshot creation")
        target = folder / "source-snapshot" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    v, study, geometry = construct_candidate(
        load_vehicle(source), cfg, selection["additional_radii_m"], topology
    )
    numerics = cfg["numerics"][args.preset]
    output = run_thermal_topology(
        v,
        case_config(engineering, case, cfg["scope"]["adhesive_conductivity_w_m_k"], corner),
        study,
        False,
        cells=numerics["radial_cells"],
        max_step_s=numerics["max_step_s"],
        heat_flow_step_s=numerics["heat_flow_step_s"],
        scenario_index=int(case["source_scenario_index"]),
    )
    result = summarize_thermal(
        output,
        v,
        geometry["nominal_mass_cg_inertia"],
        {**case, "candidate_id": args.mode + "_" + selection["id"]},
        corner,
        geometry["mount_bond_geometry"],
        cfg["scope"]["interface_contact_conductance_w_k"],
    )
    (folder / "resolved-candidate.json").write_text(v.model_dump_json(by_alias=True, indent=2))
    (folder / "thermal-results.json").write_text(json.dumps(output))
    record = {
        "run_id": run_id,
        "candidate_identity": identity(v),
        "configuration_id": v.id,
        "candidate_label": selection["id"],
        "cad_revision_sha256": hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted((ROOT / "src/cad").glob("*.py")))
        ).hexdigest(),
        "part_shape_sha256": {
            p.id: digest(p.geometry, p.cad.model_dump() if p.cad else None) for p in v.parts
        },
        "mode": args.mode,
        "spacer_variant": args.spacers,
        "ring_variant": args.rings,
        "numerics": numerics,
        "source_sha256": before,
        "source_snapshot": "source-snapshot/ contains immutable bytes for every recorded source hash",
        "inputs_unchanged": all(
            hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in before.items()
        ),
        "geometry": geometry,
        "thermal": result,
        "active_adoption": False,
        "flight_ready": False,
        "structural_acceptance": "unavailable; changed mount bores require analysis",
        "limitations": cfg["limitations"],
        "elapsed_s": time.perf_counter() - started,
        "cost_usd": 0,
    }
    (folder / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "record": str(folder / "record.json"),
                "thermal": result["worst_limited_part"],
                "mass_delta_g": 1000
                * (mass_record(v)["mass_kg"] - geometry["nominal_mass_cg_inertia"]["mass_kg"]),
                "new_intersections": geometry["new_part_intersections"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
