"""Trace archived G12 contact wrenches, with no installed load distribution model.

At one common reference point a wrench is [F, M]. Moving it from A to B
uses M_B = M_A + (r_A - r_B) cross F. Coordinates are radial X, tangential
Y, axial Z. Three unmodelled wrench components are conditionally zero only for
the archived planar and uniform-chord model; physical values are unknown.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import time
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
for variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[variable] = "1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cross(a: list[float], b: list[float]) -> list[float]:
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def move(force: list[float], moment: list[float], a: list[float], b: list[float]) -> list[float]:
    arm = [x - y for x, y in zip(a, b, strict=True)]
    offset = cross(arm, force)
    return [x + y for x, y in zip(moment, offset, strict=True)]


def known_case() -> dict[str, Any]:
    force, origin, target = [0.0, 4.0, 0.0], [2.0, 0.0, 3.0], [0.0, 0.0, 1.0]
    transported = move(force, [0.0, 0.0, 0.0], origin, target)
    returned = move(force, transported, target, origin)
    assert transported == [-8.0, 0.0, 8.0] and returned == [0.0, 0.0, 0.0]
    return {
        "passed": True,
        "expected_moment_nm": [-8.0, 0.0, 8.0],
        "calculated_moment_nm": transported,
        "round_trip_moment_nm": returned,
    }


def archived_rail_sections(step: Path, frame_start: float, station: float) -> list[dict[str, Any]]:
    """Slice original STEP, matching the archived 0.1 mm section method."""
    import cadquery as cq

    shape = cq.importers.importStep(str(step)).val()
    local_z = (station - frame_start) * 1000
    slab = (
        cq.Workplane("XY")
        .box(70, 70, 0.1, centered=(True, True, False))
        .val()
        .translate((0, 0, local_z))
    )
    solids = shape.intersect(slab).Solids()
    rows = []
    for solid in solids:
        center = solid.Center()
        area = solid.Volume() / 0.1
        if not math.isclose(area, 15.8355088817, rel_tol=1e-7):
            raise ValueError("STEP section area differs from archived G12 evidence")
        rows.append(
            {
                "area_mm2": area,
                "centroid_xyz_m": [center.x / 1000, center.y / 1000, frame_start + center.z / 1000],
            }
        )
    if len(rows) != 3:
        raise ValueError("STEP section does not contain exactly three rails")
    return sorted(rows, key=lambda x: -x["centroid_xyz_m"][0])


def run(config: Path, output: Path) -> dict[str, Any]:
    start = time.monotonic()
    start_cpu = time.process_time()
    cfg = yaml.safe_load(config.read_text())
    paths = {
        key: ROOT / cfg[key]
        for key in [
            "contact_audit",
            "contact_table",
            "hoop_copy",
            "hoop_record",
            "thermal_candidate",
            "thermal_candidate_record",
        ]
    }
    audit = json.loads(paths["contact_audit"].read_text())
    hoop = yaml.safe_load(paths["hoop_copy"].read_text())
    other = json.loads(paths["thermal_candidate"].read_text())
    other_record = json.loads(paths["thermal_candidate_record"].read_text())
    if sha(paths["hoop_copy"]) != audit["source_identity"]["hoop_resolved_copy_sha256"]:
        raise ValueError("Hoop copy hash differs from audited source")
    if (
        other_record["candidate_identity"]
        != "69df790ec9bcba1465be4fa9861a7ad5fbc467091cbf58f44dee069e56e00bac"
    ):
        raise ValueError("Unexpected 69df candidate identity")
    fin = next(p for p in hoop["parts"] if p["id"] == "fin_set")
    other_fin = next(p for p in other["parts"] if p["id"] == "fin_set")
    geometry = fin["geometry"]
    radius, chord = geometry["radius_m"], geometry["root_chord_m"]
    z = fin["position_m"] + chord / 2
    tab = fin["cad"]["parameters"]
    tab_center = fin["position_m"] + (tab["tab_offset_mm"] + tab["tab_length_mm"] / 2) / 1000
    if not math.isclose(z, tab_center, abs_tol=1e-12):
        raise ValueError(
            "Tab and foot centroid stations differ; do not assume uniform chord mapping"
        )
    origin = [radius, 0.0, z]
    frame_step = ROOT / "build/wo03-recovery-clearance/hoop/recovery-cap-frame.step"
    fin_step = ROOT / "build/wo03-trainer-fin-root/pvc5-forward25-backed-reconciled/fin-layers.step"
    if (
        sha(frame_step) != audit["source_identity"]["actual_frame_step_sha256"]
        or sha(fin_step) != audit["source_identity"]["layered_fin_step_sha256"]
    ):
        raise ValueError("Frozen STEP source hash mismatch")
    frame = next(p for p in hoop["parts"] if p["id"] == "gimbal_frame")
    sections = archived_rail_sections(frame_step, frame["position_m"], 1.13)
    external = audit["load_coordinates"]["resultants_Fx_Fy_Mz"]
    hypotheses = [
        x
        for x in audit["common_root_load_sharing"]
        if math.isclose(x["foot_bondline_m"], cfg["foot_bond_m"], abs_tol=1e-12)
    ]
    if not hypotheses:
        raise ValueError("No archived contact hypothesis matches requested bond")
    output_rows = []
    for hyp in hypotheses:
        records = []
        for branch in hyp["branches"]:
            fx, fy, mz = branch["resultant_Fx_Fy_Mz_N_N_Nm"]
            f, m = [fx, fy, 0.0], [0.0, 0.0, mz]
            at_axis = move(f, m, origin, [0.0, 0.0, z])
            at_stations = [
                {
                    "station_m": s,
                    "wrench_about_axis_point": f + move(f, m, origin, [0.0, 0.0, s]),
                    "interpretation": "wrench about point, not internal section resultant or assigned reaction",
                }
                for s in cfg["reference_stations_m"]
            ]
            records.append(
                {
                    "branch": branch["branch"],
                    "physical_unknown_components": {"Fz": None, "Mx": None, "My": None},
                    "wrench_array_scope": "known planar contribution only; physical unknown contributions omitted",
                    "contact_wrench_about_tangent": f + m,
                    "body_axis_wrench_at_contact_center": f + at_axis,
                    "axis_points": at_stations,
                    "wrench_about_each_rail_centroid": [
                        {
                            "centroid_xyz_m": section["centroid_xyz_m"],
                            "wrench": f + move(f, m, origin, section["centroid_xyz_m"]),
                            "interpretation": "same whole branch transported to a reference; not a rail reaction",
                        }
                        for section in sections
                    ],
                    "normal_DF3_pa": branch["required_hot_normal_strength_DF3_pa"],
                    "shear_DF3_pa": branch["required_hot_shear_strength_DF3_pa"],
                    "normal_allowable_pa": None,
                    "installed_reactions": None,
                }
            )
        actual = [sum(b["contact_wrench_about_tangent"][i] for b in records) for i in range(6)]
        expected = [external[0], external[1], 0.0, 0.0, 0.0, external[2]]
        if max(abs(a - b) for a, b in zip(actual, expected, strict=True)) > 1e-8:
            raise ValueError("Archived forces or moments do not balance")
        output_rows.append(
            {
                "hypothesis": hyp["hypothesis"],
                "branches": records,
                "tangent_total": actual,
                "body_axis_total": [
                    sum(b["body_axis_wrench_at_contact_center"][i] for b in records)
                    for i in range(6)
                ],
                "total_tip_deflection_m": hyp["total_panel_plus_root_tip_motion_m"],
                "input_contact_residual": [a - b for a, b in zip(actual, expected, strict=True)],
            }
        )
    relevant = [
        config,
        Path(__file__),
        *paths.values(),
        ROOT / "build/wo03-trainer-fin-root/pvc5-forward25-backed-reconciled/fin-layers.step",
        ROOT / "build/wo03-recovery-clearance/hoop/recovery-cap-frame.step",
    ]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in relevant}
    # The physical signs of out-of-plane components and true axial distributions are unmeasured.
    result = {
        "status": "wrench_transport_complete_load_path_unclosed",
        "accepted": False,
        "flight_ready": False,
        "source_sha256": hashes,
        "known_case": known_case(),
        "identity": {
            "g12_copy_sha256": sha(paths["hoop_copy"]),
            "g12_historical_resolved_spec_sha256": audit["source_identity"][
                "hoop_resolved_spec_sha256"
            ],
            "g12_current_schema_valid": audit["source_identity"]["current_schema_validation"][
                "passed"
            ],
            "g54_candidate_identity": other_record["candidate_identity"],
            "g54_resolved_candidate_file_sha256": sha(paths["thermal_candidate"]),
            "same_candidate": False,
            "g12_fin": {"position_m": fin["position_m"], "geometry": geometry},
            "69df_fin": {"position_m": other_fin["position_m"], "geometry": other_fin["geometry"]},
            "g12_contact_applied_to_69df": False,
        },
        "coordinates": {
            "axes": ["radial X", "tangential Y", "axial Z"],
            "tangent_origin_m": origin,
            "branch_force_sign": "force exerted on support by fin",
            "other_components": "physical Fz, Mx, My unknown; arrays are known planar contributions, not full physical wrench",
            "unknown_component_order": ["Fz", "Mx", "My"],
            "physical_unknown_components": {"Fz": None, "Mx": None, "My": None},
            "body_axis_reference_is_rail_centroid": False,
        },
        "archived_step_rail_section": {
            "station_nominal_m": 1.13,
            "slice_thickness_mm": 0.1,
            "rails": sections,
            "basis": "three solids sliced from hash-verified historical frame STEP; geometric slice, no torsion constant or reaction",
        },
        "contact_hypotheses": output_rows,
        "limitations": {
            "rail_torque_distribution": None,
            "ring_reactions": None,
            "shell_traction": None,
            "joint_allowables": None,
            "actual_root_stiffness": None,
            "installed_strength_pass": False,
            "torsion_constant": None,
            "material_shear_modulus": None,
        },
        "elapsed_wall_s": time.monotonic() - start,
        "process_cpu_s": time.process_time() - start_cpu,
        "process_max_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "no_FEA_or_new_CAD_generation": True,
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "record.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/studies/wo03-fin-load-routing.yaml"
    )
    parser.add_argument("--preset", choices=["tiny"], default="tiny")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    cfg = yaml.safe_load(args.config.read_text())
    run(args.config, args.output or ROOT / cfg["default_output"])


if __name__ == "__main__":
    main()
