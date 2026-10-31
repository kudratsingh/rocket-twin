"""Probe a real fixed fore-bay foil on the coherent TVC clearance candidate.

Uses the shared offline thermal network and exact exported frame/fin solids;
does not edit active specifications, physics, operating bounds or material limits.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import cadquery as cq
import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_recovery_clearance import distance, placed_solids
from scripts.wo03_thermal_matrix import case_config, mass_record, rebuild_part_mass
from src.analysis.thermal_topology import run_thermal_topology
from src.cad.kinematics import pose
from src.cad.parts import local_shape
from src.vehicle.schema import Part, load_vehicle

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-tvc-fore-shield.yaml"


def main() -> None:
    started = time.perf_counter()
    run_id = "wo03-tvc-fore-shield-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / "runs" / run_id
    cfg = yaml.safe_load(CONFIG.read_text())
    source = json.loads((ROOT / cfg["source_record"]).read_text())
    clearance = yaml.safe_load((ROOT / cfg["clearance_config"]).read_text())
    budget = yaml.safe_load((ROOT / cfg["budget_config"]).read_text())
    matrix = yaml.safe_load((ROOT / cfg["acceptance_matrix"]).read_text())
    engineering = yaml.safe_load((ROOT / matrix["engineering_inputs"]).read_text())
    topology = yaml.safe_load((ROOT / matrix["thermal_topology"]).read_text())
    v = load_vehicle(source["resolved_copy"])
    if (
        hashlib.sha256(Path(source["resolved_copy"]).read_bytes()).hexdigest()
        != source["resolved_copy_sha256"]
    ):
        raise ValueError("Clearance candidate changed after its record")
    if (
        hashlib.sha256(Path(source["frame_step"]["path"]).read_bytes()).hexdigest()
        != source["frame_step"]["sha256"]
    ):
        raise ValueError("Actual frame STEP changed")
    inputs = [
        CONFIG,
        ROOT / cfg["source_record"],
        ROOT / cfg["clearance_config"],
        ROOT / cfg["budget_config"],
        ROOT / cfg["acceptance_matrix"],
        Path(source["resolved_copy"]),
        Path(source["frame_step"]["path"]),
        Path(budget["trainer_fin_step"]),
        Path(__file__),
    ]
    inputs += list((ROOT / "src/cad").glob("*.py"))
    inputs += [
        ROOT / matrix["engineering_inputs"],
        ROOT / matrix["thermal_topology"],
        ROOT / "src/analysis/thermal_topology.py",
        ROOT / "src/analysis/thermal_radial.py",
        ROOT / "scripts/wo03_recovery_clearance.py",
        ROOT / "scripts/wo03_thermal_matrix.py",
        ROOT / "src/vehicle/schema.py",
        ROOT / "src/vehicle/mass.py",
    ]
    hashes = {
        str(p.resolve().relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in inputs
    }
    out.mkdir()
    for name, expected in hashes.items():
        raw = (ROOT / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f"Source changed while snapshotting {name}")
        target = out / "source-snapshot" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    parts = {p.id: p for p in v.parts}
    before = mass_record(v)
    foil = cfg["foil"]
    start, end = foil["start_station_m"], foil["end_station_m"]
    raw = parts["motor_radiant_shield"].model_dump(by_alias=True)
    raw.update(
        id="fore_bay_radiant_shield",
        parent="gimbal_frame",
        position_m=start,
        cad_mass=None,
        cg_offset_m=(end - start) / 2,
    )
    raw["geometry"] = {
        "length_m": end - start,
        "radius_m": foil["outer_radius_m"],
        "inner_radius_m": foil["outer_radius_m"] - foil["wall_m"],
        "wall_m": foil["wall_m"],
    }
    raw["cad"]["moving_group"] = "fixed"
    raw["engineering"]["tolerances_mm"] = {
        "radial_manufacturing_estimate": foil["radial_manufacturing_tolerance_mm_estimate"]
    }
    raw["learn"] = (
        "Experimental fixed fore-bay foil blocks direct radial radiation in its actual axial span. Short ends, wrinkles, contact and full gimbal clearance remain design/measurement gates."
    )
    shield = Part.model_validate(raw)
    rebuild_part_mass(shield)
    v.parts.append(shield)
    topology["part_ids"].append(shield.id)
    topology["annular_barrier_part_ids"].append(shield.id)
    pad_ids = []
    frame = parts["gimbal_frame"]
    options = frame.cad.parameters
    outer_flat = options["rail_radius_mm"] - options["rail_depth_mm"] / 2
    y = (options["rail_width_mm"] / 2 + options["fin_slot_width_mm"] / 2) / 2
    width = cfg["supports"]["tangential_width_mm"]
    radius = 1000 * foil["outer_radius_m"]
    xmin = math.sqrt(radius**2 - (y + width / 2) ** 2) - 0.1
    size = [outer_flat - xmin, width, 1000 * cfg["supports"]["axial_length_m"]]
    center = [(outer_flat + xmin) / 2, y, 0]
    for label, z in [("front", start), ("aft", end - cfg["supports"]["axial_length_m"])]:
        data = shield.model_dump(by_alias=True)
        data.update(
            id=f"fore_shield_mica_{label}",
            position_m=z,
            material="mica",
            cad_mass=None,
            cg_offset_m=cfg["supports"]["axial_length_m"] / 2,
            type="commercial",
        )
        data["geometry"] = {"length_m": cfg["supports"]["axial_length_m"], "radius_m": 0.031}
        extras = []
        for angle in [120, 240]:
            a = math.radians(angle)
            extras.append(
                {
                    "size_mm": size,
                    "angle_deg": angle,
                    "position_mm": [
                        center[0] * math.cos(a) - center[1] * math.sin(a),
                        center[0] * math.sin(a) + center[1] * math.cos(a),
                        0,
                    ],
                }
            )
        data["cad"].update(
            generator="brackets",
            parameters={
                "blocks": [{"size_mm": size, "position_mm": center}],
                "reinforcement_blocks": extras,
                "machining_holes": [
                    {
                        "diameter_mm": 2 * radius,
                        "length_mm": 3,
                        "start_mm": [0, 0, -1],
                        "axis": [0, 0, 1],
                    }
                ],
            },
        )
        data["engineering"]["material_profile"] = "mica"
        data["learn"] = (
            "Three curved-inner/flat-outer mica stand-offs meet actual G11 rail wings beyond the fin channel. Array geometry is explicit; retention and hot interfaces require tests."
        )
        pad = Part.model_validate(data)
        rebuild_part_mass(pad)
        v.parts.append(pad)
        pad_ids.append(pad.id)
        topology["part_ids"].append(pad.id)
        topology["pad_conduction_part_ids"].append(pad.id)
        topology.setdefault("pad_conduction_thickness_m", {})[pad.id] = cfg["supports"][
            "pad_conduction_path_m_conservative"
        ]
        topology["contact_pairs"].append([shield.id, pad.id])
    bond = parts["adhesive_finish"].model_copy(deep=True)
    bond.id = "fore_shield_bond_allowance"
    bond.parent = "gimbal_frame"
    bond.position_m = start
    bond.cg_offset_m = (end - start) / 2
    bond.mass_kg = cfg["supports"]["retaining_adhesive_and_application_allowance_kg"]
    bond.cad_mass = None
    bond.density_kg_m3 = None
    bond.learn = "Additional nonstructural shield retention/application allowance; interface geometry and hot adhesion are unmeasured. It is counted once in the mass/thermal network."
    v.parts.append(bond)
    topology["part_ids"].append(bond.id)
    for p in pad_ids:
        topology["contact_pairs"].append([p, bond.id])
    topology["contact_pairs"].append([bond.id, "gimbal_frame"])
    for a, b in topology["contact_pairs"]:
        if a in [shield.id, bond.id, *pad_ids] or b in [shield.id, bond.id, *pad_ids]:
            topology.setdefault("contact_pair_conductance_w_k", {})[f"{a}->{b}"] = cfg["supports"][
                "interface_contact_w_k_estimate"
            ]
    actual_frame = cq.importers.importStep(source["frame_step"]["path"]).val()
    solids = placed_solids(v, actual_frame, clearance, budget)
    added = [shield.id, *pad_ids]
    limits = np.linspace(
        -math.degrees(v.tvc.max_deflection_rad),
        math.degrees(v.tvc.max_deflection_rad),
        cfg["motion_grid_each_axis"],
    )
    collisions = []
    minima = {}
    excluded = {
        p.id for p in v.parts if p.cad and p.cad.role in {"soft_stowage", "distributed_budget"}
    }
    moving = {p.id for p in v.parts if p.cad and p.cad.moving_group != "fixed"} | {
        "gimbal_links",
        "servo_horns",
    }
    checked_fixed_pairs = set()
    for pitch in limits:
        for yaw in limits:
            moved = pose(v, solids, float(pitch), float(yaw))
            for a in added:
                for b in solids:
                    if a == b or b in excluded or (b in added and b < a):
                        continue
                    key = f"{a}/{b}"
                    if b not in moving:
                        if key in checked_fixed_pairs:
                            continue
                        checked_fixed_pairs.add(key)
                    d = distance(moved[a], moved[b])
                    minima[key] = min(minima.get(key, float("inf")), d)
                    if d < 1e-6:
                        volume = moved[a].intersect(moved[b]).Volume()
                        if volume > cfg["intersection_threshold_mm3"]:
                            collisions.append(
                                {
                                    "pitch_deg": float(pitch),
                                    "yaw_deg": float(yaw),
                                    "a": a,
                                    "b": b,
                                    "mm3": volume,
                                }
                            )
    case = next(c for c in matrix["cases"] if c["id"] == cfg["required_case"])
    corner = next(
        c
        for c in matrix["material_property_uncertainty"]["factors"]
        if c["id"] == cfg["property_corner"]
    )
    n = cfg["numerics"]
    thermal = run_thermal_topology(
        v,
        case_config(engineering, case, None, corner),
        topology,
        False,
        scenario_index=int(case["source_scenario_index"]),
        cells=n["radial_cells"],
        max_step_s=n["max_step_s"],
        heat_flow_step_s=n["heat_flow_step_s"],
    )
    (out / "resolved-candidate.json").write_text(v.model_dump_json(by_alias=True, indent=2))
    (out / "thermal-results.json").write_text(json.dumps(thermal))
    record = {
        "run_id": run_id,
        "source_sha256": hashes,
        "source_snapshot": "source-snapshot/ contains frozen bytes for every input hash; generated solids stay local",
        "inputs_unchanged": all(
            hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in hashes.items()
        ),
        "source_candidate": source["resolved_copy"],
        "mass_before": before,
        "mass_after": mass_record(v),
        "collisions": collisions,
        "sampled_minimum_distances_mm": minima,
        "pose_count": len(limits) ** 2,
        "motion_coverage": "25 nominal sampled poses; fixed pairs checked once; no continuous or tolerance-bound proof",
        "rigid_contact_exclusions": sorted(excluded),
        "thermal_peaks": thermal["peaks"],
        "energy_residual_j": thermal["energy_residual_j"],
        "limitations": cfg["limitations"],
        "active_adoption": False,
        "engineering_acceptance_passed": False,
        "elapsed_s": time.perf_counter() - started,
        "compute_cost_usd": 0,
        "flight_ready": False,
    }
    (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    for name in added:
        cq.exporters.export(
            local_shape(next(p for p in v.parts if p.id == name)), str(out / (name + ".step"))
        )
    print(out / "record.json", flush=True)
    print(
        json.dumps(
            {
                "mass_delta_g": 1000 * (mass_record(v)["mass_kg"] - before["mass_kg"]),
                "collisions": collisions,
                "worst": min(
                    (r for r in thermal["peaks"] if r["margin_k"] is not None),
                    key=lambda r: r["margin_k"],
                ),
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
