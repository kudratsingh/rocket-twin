"""Run the bounded G54 Package-A motor-mount support FEA sensitivity."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_fit_correction_study import _reconcile_copy
from scripts.wo03_fit_structure import make_candidate
from src.analysis.fea import axial_bar
from src.analysis.support_fea import (
    euler_buckling_fixture,
    solve_braced_buckling_case,
    solve_support_case,
)
from src.cad.assembly import export_vehicle
from src.vehicle.schema import load_vehicle, vehicle_input_paths


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(source_config: Path, output: Path, buckling_only: bool = False) -> Path:
    root = Path.cwd()
    source_config = source_config.resolve()
    output = output.resolve()
    vehicle = load_vehicle(source_config)
    study_cfg = root / "configs/studies/wo03-fit-correction.yaml"
    study = yaml.safe_load(study_cfg.read_text())
    hash_paths = [
        *[path.resolve() for path in vehicle_input_paths(source_config)],
        study_cfg,
        root / "configs/engineering/wo03.yaml",
        root / "src/cad/parts.py",
        root / "src/cad/retention_parts.py",
        root / "src/cad/assembly.py",
        root / "scripts/wo03_fit_structure.py",
        root / "scripts/wo03_fit_correction_study.py",
        root / "scripts/wo03_support_fea.py",
        root / "src/analysis/support_fea.py",
        root / "src/analysis/fea.py",
        root / "src/analysis/motor_support.py",
        root / "src/vehicle/schema.py",
        root / "src/vehicle/materials.py",
    ]
    hash_paths = sorted(set(hash_paths))
    input_hashes_before = {str(p.relative_to(root)): sha256(p) for p in hash_paths}
    package = next(p for p in study["packages"] if p["id"] == "fit-package-a")
    candidate = make_candidate(vehicle, package, True)
    output.mkdir(parents=True, exist_ok=False)
    source_vehicle = source_config
    source_hash = sha256(source_vehicle)
    cad_root = output / "cad"
    manifest, _ = export_vehicle(candidate, cad_root, export=True)
    candidate = _reconcile_copy(candidate, {"motor_mount"}, manifest)
    candidate_yaml = output / "resolved-braced-candidate.yaml"
    candidate_yaml.write_text(yaml.safe_dump(candidate.model_dump(by_alias=True), sort_keys=False))
    mount = next(p for p in candidate.parts if p.id == "motor_mount")
    params = mount.cad.parameters if mount.cad else {}
    plate = next(p for p in candidate.parts if p.id == "retention")
    plate_params = plate.cad.parameters if plate.cad else {}
    finger = plate_params.get("bond_fingers", {})
    step_path = cad_root / "parts" / "motor_mount.step"
    geometry_id = manifest["identity"]["part_shape_sha256"]["motor_mount"]
    static_reference_path = root / "build/wo03-support-fea/20261030T235500Z/report.json"
    static_reference: dict[str, Any] | None = None
    if buckling_only and static_reference_path.exists():
        prior = json.loads(static_reference_path.read_text())
        static_reference = {
            "report": str(static_reference_path.relative_to(root)),
            "report_sha256": sha256(static_reference_path),
            "geometry_shape_sha256": prior.get("geometry_shape_sha256"),
            "cad_revision_sha256": prior.get("candidate_cad_revision_sha256"),
            "inputs_unchanged": prior.get("inputs_unchanged"),
            "same_motor_mount_geometry": prior.get("geometry_shape_sha256") == geometry_id,
            "same_cad_revision": prior.get("candidate_cad_revision_sha256")
            == manifest["identity"]["cad_revision_sha256"],
            "scope": "prior axial static/reference-reaction study; different ring constraints than this buckling case",
        }
    stations = [float(s) for s in params.get("ring_stations_mm", [])]
    ring_thickness = float(params.get("ring_thickness_mm", 3.0))
    load_n = 139.97
    results: dict[str, Any] = {}
    if not buckling_only:
        for sign_name, sign in [("noseward", -1), ("aftward", 1)]:
            levels = []
            for size in (4.0, 3.0, 2.0):
                levels.append(
                    solve_support_case(
                        step_path,
                        output / sign_name / str(size),
                        size,
                        load_n,
                        sign,
                        young_mpa=1000.0,
                        poisson=0.25,
                        ring_stations_mm=stations,
                        ring_thickness_mm=ring_thickness,
                    )
                )
            results[sign_name] = levels
    buckling_levels = [
        solve_braced_buckling_case(
            step_path,
            output / "buckling" / str(size),
            size,
            load_n,
            stations,
            ring_thickness,
            young_mpa=1000.0,
            poisson=0.25,
            mode_count=5,
        )
        for size in (4.0, 3.0, 2.0)
    ]
    known = euler_buckling_fixture(output / "known-euler-buckling", young_mpa=1000.0)
    axial_bar_known = (
        [axial_bar(output / "known-axial" / str(size), size) for size in (2.0, 1.5, 1.0)]
        if not buckling_only
        else None
    )
    convergence: dict[str, Any] = {}
    for direction, levels in results.items():
        medium, fine = levels[1], levels[2]
        relative_changes = {
            key: abs(float(fine[key]) / float(medium[key]) - 1.0)
            for key in (
                "regional_szz_max_abs_mpa",
                "regional_szz_mean_abs_mpa",
                "maximum_displacement_mm",
            )
        }
        convergence[direction] = {
            "medium_to_fine_relative_change": relative_changes,
            "criterion_fraction": 0.1,
            "criterion_passed": all(value < 0.1 for value in relative_changes.values()),
            "scope": "numerical sensitivity only for this mesh and idealized static support model",
        }
    buckle_change = abs(
        float(buckling_levels[2]["critical_positive_factor"])
        / float(buckling_levels[1]["critical_positive_factor"])
        - 1.0
    )
    report = {
        "run_id": f"wo03-support-fea-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}",
        "candidate_yaml": str(candidate_yaml.relative_to(root)),
        "candidate_yaml_sha256": sha256(candidate_yaml),
        "candidate_vehicle_id": candidate.id,
        "candidate_resolved_spec_sha256": manifest["identity"]["resolved_spec_sha256"],
        "candidate_cad_revision_sha256": manifest["identity"]["cad_revision_sha256"],
        "source_vehicle_yaml": str(source_vehicle.relative_to(root)),
        "source_vehicle_sha256": source_hash,
        "geometry_shape_sha256": geometry_id,
        "load": {"axial_thrust_n": load_n, "directions": {"noseward": -1, "aftward": 1}},
        "material_model": {
            "young_mpa": 1000.0,
            "poisson": 0.25,
            "basis": "estimated hot weak-direction plywood; not measured or qualified",
            "strength_bound_mpa": 5.0,
            "design_factor": 3,
        },
        "support_model": {
            "actual_ring_stations_mm": stations,
            "ring_thickness_mm": ring_thickness,
            "description": "buckling case restrains Z only at aft-most ring OD nodes; all intermediate rings remain axially and laterally free and brace rails only through actual solid connectivity; two minimal XY anchor nodes remove in-plane rigid modes",
        },
        "load_distribution": "Uniform traction integrated over six actual mount rail-flank surfaces, clipped exactly to z=11..29 mm by facet polygon clipping and quadratic shape-function quadrature; mesh-reported area and radial bounds are included; bond state remains unverified.",
        "mating_finger_geometry": {
            "bond_finger_parameters": finger,
            "inward_face_tangential_coordinate_mm": float(finger["side_center_mm"])
            - float(finger["wall_mm"]) / 2,
            "plate_outer_radius_mm": float(plate.geometry["radius_m"]) * 1000,
            "outer_radial_clip_at_inward_face_mm": math.sqrt(
                (float(plate.geometry["radius_m"]) * 1000) ** 2
                - (float(finger["side_center_mm"]) - float(finger["wall_mm"]) / 2) ** 2
            ),
            "qualification": "CAD-derived finger envelope only; bondline and exact contact stress are not modeled",
        },
        "mesh_sensitivity_by_direction": results,
        "buckling_mesh_sensitivity": buckling_levels,
        "prior_static_ring_support_reference": static_reference,
        "buckling_method": {
            "solver": "CalculiX 2.23 *BUCKLE linear eigenvalue step",
            "manual": "https://github.com/Dhondtguido/CalculiX/blob/master/doc/CalculiX.tex",
            "manual_section": "6.9.4 Buckling analysis and *BUCKLE keyword",
            "load_factor_definition": "Each eigenvalue multiplies the specified 1.15× service-load reference load.",
            "nonperturbation_basis": "No PERTURBATION parameter; initial stiffness is unloaded and stress stiffness is generated from only the buckle-step loading.",
        },
        "critical_buckling_factor_medium_to_fine_relative_change": buckle_change,
        "critical_buckling_factor_convergence_below_5pct": buckle_change < 0.05,
        "buckling_requirement_factor": 3.0,
        "buckling_screen_passed": (
            buckle_change < 0.05
            and float(buckling_levels[2]["critical_positive_factor"]) > 3.0
            and bool(known["passed"])
        ),
        "euler_buckling_known_case": known,
        "regional_mesh_convergence": convergence,
        "known_axial_bar_fixture": axial_bar_known,
        "input_sha256_before": input_hashes_before,
        "input_sha256_after": {str(p.relative_to(root)): sha256(p) for p in hash_paths},
        "inputs_unchanged": input_hashes_before
        == {str(p.relative_to(root)): sha256(p) for p in hash_paths},
        "active_adoption": False,
        "flight_ready": False,
        "acceptance": "open",
        "acceptance_passed": False,
        "physical_validation": False,
        "unresolved": [
            "Support idealization can divert load among nearby rings and does not prove actual joint load path.",
            "The six actual rail-flank tractions are clipped exactly to z=11..29 mm; CAD-derived contact envelope does not certify adhesive bond transfer or peel.",
            "Plywood orthotropy, hot strength, defects, moisture, bond properties and load sharing are estimates or unavailable.",
            "Peak stresses at load/support singularities are retained and are not allowables comparisons; regional assessment is required.",
            "This is a static axial support sensitivity, not a complete motor retention, buckling, fatigue, thermal or flight qualification.",
        ],
    }
    path = output / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    record_dir = root / "runs" / report["run_id"]
    record_dir.mkdir(parents=True, exist_ok=False)
    (record_dir / "record.json").write_text(
        json.dumps(
            {
                "run_id": report["run_id"],
                "report": str(path.relative_to(root)),
                "report_sha256": sha256(path),
                "candidate_yaml_sha256": report["candidate_yaml_sha256"],
                "source_vehicle_sha256": source_hash,
                "input_sha256_before": input_hashes_before,
                "input_sha256_after": report["input_sha256_after"],
                "inputs_unchanged": report["inputs_unchanged"],
                "acceptance": "open",
                "acceptance_passed": False,
                "cost_usd": 0,
            },
            indent=2,
        )
        + "\n"
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-config",
        type=Path,
        default=Path("configs/vehicle/wo02/performance-g54.yaml"),
    )
    parser.add_argument(
        "--buckling-only",
        action="store_true",
        help="Skip repeating the earlier static ring-supported sensitivity cases.",
    )
    parser.add_argument("--output", type=Path, default=Path("build/wo03-support-fea"))
    args = parser.parse_args()
    path = run(args.source_config, args.output, buckling_only=args.buckling_only)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
