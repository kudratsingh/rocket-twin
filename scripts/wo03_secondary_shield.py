"""Bounded second-shield radius trade for the current WO-03 candidate package.

This is an in-memory study: it never edits resolved vehicle specs or CAD sources.
The shield is modeled as an opaque radial-conduction annulus over the actual
motor foil axial span. Geometry screening rejects overlaps with the actual CAD
assembly; segmented coverage is not inferred as continuous coverage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_thermal_matrix import (
    apply_mount_bond_geometry,
    case_config,
    make_topology,
    mass_record,
    rebuild_part_mass,
    summarize_thermal,
)
from src.analysis.thermal_topology import run_thermal_topology
from src.cad.assembly import rigid_intersections
from src.cad.parts import local_shape
from src.vehicle.schema import Part, load_vehicle

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "configs/engineering/wo03-thermal-acceptance.yaml"
RADII_M = (0.018, 0.022)
FOIL_WALL_M = 20e-6


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_for_radius(
    source_path: Path, radius_m: float, contact_w_k: float = 2.0
) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    matrix = yaml.safe_load(MATRIX_PATH.read_text())
    topology = yaml.safe_load(Path(matrix["thermal_topology"]).read_text())
    vehicle = load_vehicle(source_path)
    parts = {part.id: part for part in vehicle.parts}
    original = parts["motor_radiant_shield"]
    nominal_mass = mass_record(vehicle)
    mount = apply_mount_bond_geometry(vehicle, 0.00068)
    mount_part = parts["motor_mount"]
    # The physical foil radius is radius_m. The extra 0.3 mm is bore clearance.
    required_bore_m = radius_m + 0.0003
    mount_part.geometry["inner_radius_m"] = required_bore_m
    mount_params = mount_part.cad.parameters
    mount_params["ring_inner_radii_mm"] = [required_bore_m * 1000] * len(
        mount_params["ring_stations_mm"]
    )
    mount_geometry = rebuild_part_mass(mount_part)
    mount["ring_bore_radius_m"] = required_bore_m
    mount["ring_inner_radii_mm"] = mount_params["ring_inner_radii_mm"]
    mount["mount_shape_sha256"] = mount_geometry["shape_sha256"]
    mount["mount_mass_kg"] = mount_part.resolved_mass_kg
    raw = original.model_dump(by_alias=True)
    # Existing aft retention blocks span local z=190..210 mm and reach
    # radially inward. Clear them with a 2 mm axial gap at R22.
    shield_length_m = float(original.geometry["length_m"])
    aft_trim_m = 0.0
    if radius_m == 0.022:
        aft_trim_m = 0.022
        shield_length_m -= aft_trim_m
    raw.update(id="secondary_radiant_shield", parent=original.parent, cad_mass=None, mass_kg=1e-6)
    raw["geometry"].update(
        length_m=shield_length_m,
        radius_m=radius_m,
        inner_radius_m=radius_m - FOIL_WALL_M,
    )
    shield = Part.model_validate(raw)
    rebuild_part_mass(shield)
    vehicle.parts.append(shield)
    study = make_topology(topology, vehicle, contact_w_k)
    study["part_ids"].append(shield.id)
    study["annular_barrier_part_ids"].append(shield.id)
    # End spacers are explicit thermal bridges, retained at the existing foil ends.
    shield_end_m = original.position_m + shield_length_m
    for side, z in (
        ("front", original.position_m),
        ("aft", shield_end_m - 0.001),
    ):
        spacer_data = original.model_dump(by_alias=True)
        spacer_data.update(
            id=f"shield_spacer_{side}",
            parent=original.id,
            position_m=z,
            cad_mass=None,
            mass_kg=1e-6,
            material="mica",
            cg_offset_m=0.0005,
        )
        spacer_data["geometry"] = {
            "length_m": 0.001,
            "radius_m": radius_m - FOIL_WALL_M,
            "inner_radius_m": float(original.geometry["radius_m"]),
            "wall_m": radius_m - FOIL_WALL_M - float(original.geometry["radius_m"]),
        }
        spacer_data["engineering"]["material_profile"] = "mica"
        spacer = Part.model_validate(spacer_data)
        rebuild_part_mass(spacer)
        vehicle.parts.append(spacer)
        study["part_ids"].append(spacer.id)
        study["pad_conduction_part_ids"].append(spacer.id)
        study.setdefault("pad_conduction_thickness_m", {})[spacer.id] = float(
            spacer.geometry["wall_m"]
        )
        study["contact_pairs"].extend([[original.id, spacer.id], [spacer.id, shield.id]])
        pairs = study.setdefault("contact_pair_conductance_w_k", {})
        pairs[f"{original.id}->{spacer.id}"] = contact_w_k
        pairs[f"{spacer.id}->{shield.id}"] = contact_w_k
    solids = {
        p.id: local_shape(p).translate(
            (p.lateral_offset_m[0] * 1000, -p.lateral_offset_m[1] * 1000, p.position_m * 1000)
        )
        for p in vehicle.parts
        if p.cad is not None
    }
    intersections = rigid_intersections(vehicle, solids)
    return (
        vehicle,
        {
            "mount_bond_geometry": mount,
            "nominal_mass": nominal_mass,
            "intersections": intersections,
            "shield_axial_start_m": original.position_m,
            "shield_axial_end_m": shield_end_m,
            "shield_axial_length_m": shield_length_m,
            "aft_trim_before_retainer_m": aft_trim_m,
        },
        study,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=("tiny", "sim"), default="tiny")
    parser.add_argument("--output", type=Path, default=Path("runs"))
    args = parser.parse_args()
    matrix = yaml.safe_load(MATRIX_PATH.read_text())
    engineering = yaml.safe_load(Path(matrix["engineering_inputs"]).read_text())
    candidate = next(row for row in matrix["candidates"] if row["id"] == "G54")
    case = next(row for row in matrix["cases"] if row["id"] == "combined_300C_eps09_at35C")
    corner = next(
        row
        for row in matrix["material_property_uncertainty"]["factors"]
        if row["id"] == "high_k_low_cp"
    )
    source = ROOT / candidate["candidate_yaml"]
    source_record = ROOT / "build/wo03-correction-package/latest-record.json"
    input_paths = [
        source,
        source_record,
        MATRIX_PATH,
        ROOT / matrix["engineering_inputs"],
        ROOT / matrix["thermal_topology"],
    ]
    hashes_before = {str(path.relative_to(ROOT)): file_sha256(path) for path in input_paths}
    cells = int(
        matrix["execution"]["tiny_cells"]
        if args.preset == "tiny"
        else matrix["execution"]["sim_cells"]
    )
    records = []
    for radius in RADII_M:
        vehicle, geometry, study = candidate_for_radius(source, radius)
        if geometry.get("geometry_rejected"):
            records.append(
                {
                    "candidate_id": f"G54_R{radius * 1000:.0f}mm",
                    "shield_radius_m": radius,
                    "status": "REJECTED_GEOMETRY",
                    "reason": geometry["geometry_rejected"],
                    "nominal_candidate_mass_cg_inertia": geometry["nominal_mass"],
                    "active_adoption": False,
                    "flight_ready": False,
                }
            )
            print(f"{radius * 1000:.0f} mm: REJECTED_GEOMETRY", flush=True)
            continue
        screen = run_thermal_topology(
            vehicle,
            case_config(engineering, case, 0.15, corner),
            study,
            False,
            cells=cells,
            scenario_index=3,
            max_step_s=float(matrix["execution"]["max_step_s"]),
            heat_flow_step_s=float(matrix["execution"]["heat_flow_postprocess_step_s"]),
        )
        record = summarize_thermal(
            screen,
            vehicle,
            geometry["nominal_mass"],
            {**case, "candidate_id": f"G54_R{radius * 1000:.0f}mm"},
            corner,
            geometry["mount_bond_geometry"],
            2.0,
        )
        record.update(
            {
                "shield_radius_m": radius,
                "mount_ring_bore_radius_m": radius + 0.0003,
                "foil_wall_m": FOIL_WALL_M,
                "shield_axial_start_m": geometry["shield_axial_start_m"],
                "shield_axial_end_m": geometry["shield_axial_end_m"],
                "shield_axial_length_m": geometry["shield_axial_length_m"],
                "aft_trim_before_retainer_m": geometry["aft_trim_before_retainer_m"],
                "cad_intersections_involving_new_parts": [
                    row
                    for row in geometry["intersections"]
                    if row["a"].startswith("secondary_radiant_shield")
                    or row["b"].startswith("secondary_radiant_shield")
                    or row["a"].startswith("shield_spacer_")
                    or row["b"].startswith("shield_spacer_")
                ],
                "cad_validity": {
                    p.id: bool(local_shape(p).isValid())
                    for p in vehicle.parts
                    if p.id.startswith("secondary_radiant_shield")
                    or p.id.startswith("shield_spacer_")
                },
                "source_candidate_yaml_sha256": file_sha256(source),
                "screen_cells": cells,
            }
        )
        records.append(record)
        print(
            f"{radius * 1000:.0f} mm: status={record['thermal_screen_status']} worst={record['worst_limited_part']} mass_delta_g={(record['candidate_mass_cg_inertia']['mass_kg'] - record['nominal_candidate_mass_cg_inertia']['mass_kg']) * 1000:.3f}",
            flush=True,
        )
    run_id = "wo03-secondary-shield-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / args.output / run_id
    output.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "source_candidate": str(candidate["candidate_yaml"]),
        "source_sha256": file_sha256(source),
        "source_inputs_sha256_before": hashes_before,
        "source_inputs_sha256_after": {
            str(path.relative_to(ROOT)): file_sha256(path) for path in input_paths
        },
        "case_id": case["id"],
        "geometry_candidates": list(RADII_M),
        "records": records,
        "active_adoption": False,
        "flight_ready": False,
    }
    (output / "record.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(output / "record.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
