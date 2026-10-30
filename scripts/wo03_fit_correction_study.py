"""Compare copy-only clearance corrections for the fixed and finned-TVC aft fits."""

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

from src.cad.assembly import export_vehicle
from src.cad.verification import verify
from src.vehicle.mass import mass_properties
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import Vehicle, load_vehicle, vehicle_input_paths


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _material_data(
    material: str, engineering: dict[str, Any], study: dict[str, Any]
) -> tuple[float, float, float]:
    profile = engineering["materials"][material]
    expansion = study["material_expansion"].get(material)
    if expansion is None:
        raise ValueError(f"No CTE basis is configured for material {material!r}")
    low, high = (float(v) for v in expansion["cte_per_k"])
    return low, high, float(profile["limit_c"])


def _profile(part: Any) -> str:
    if part.engineering is None:
        return str(part.material)
    return str(part.engineering.material_profile)


def _thermal_shift_bounds(
    host_radius_mm: float,
    insert_radius_mm: float,
    host_material: str,
    insert_material: str,
    engineering: dict[str, Any],
    study: dict[str, Any],
) -> tuple[float, float]:
    ambient = float(study["ambient_c"])
    h_low, h_high, h_limit = _material_data(host_material, engineering, study)
    i_low, i_high, i_limit = _material_data(insert_material, engineering, study)
    h_dt = max(0.0, h_limit - ambient)
    i_dt = max(0.0, i_limit - ambient)
    shifts = [
        host_alpha * host_radius_mm * host_delta - insert_alpha * insert_radius_mm * insert_delta
        for host_alpha in (h_low, h_high)
        for insert_alpha in (i_low, i_high)
        for host_delta in (0.0, h_dt)
        for insert_delta in (0.0, i_dt)
    ]
    return min(shifts), max(shifts)


def _clearance(
    label: str,
    host_radius_mm: float,
    insert_radius_mm: float,
    host_tol_mm: float,
    insert_tol_mm: float,
    host_material: str,
    insert_material: str,
    required_mm: float,
    engineering: dict[str, Any],
    study: dict[str, Any],
    definition: str,
) -> dict[str, Any]:
    nominal = host_radius_mm - insert_radius_mm
    delta = _thermal_shift_bounds(
        host_radius_mm,
        insert_radius_mm,
        host_material,
        insert_material,
        engineering,
        study,
    )
    variation = host_tol_mm + insert_tol_mm
    minimum = nominal - variation + delta[0]
    maximum = nominal + variation + delta[1]
    return {
        "feature": label,
        "host_radial_feature_mm": host_radius_mm,
        "insert_radial_feature_mm": insert_radius_mm,
        "definition": definition,
        "manufacturing_tolerance_stack_mm": variation,
        "thermal_clearance_shift_bounds_mm": list(delta),
        "manufacturing_nominal_mm": nominal,
        "minimum_clearance_mm": minimum,
        "maximum_clearance_mm": maximum,
        "required_minimum_mm": required_mm,
        "status": "screen-pass" if minimum >= required_mm else "screen-fail",
        "qualification": "calculated interval screen; not as-built fit qualification",
    }


def _dimensional_only(
    label: str,
    host_diameter_mm: float,
    insert_diameter_mm: float,
    host_tol_diameter_mm: float,
    insert_tol_diameter_mm: float,
    required_mm: float,
) -> dict[str, Any]:
    nominal = (host_diameter_mm - insert_diameter_mm) / 2
    variation = (host_tol_diameter_mm + insert_tol_diameter_mm) / 2
    minimum = nominal - variation
    maximum = nominal + variation
    return {
        "feature": label,
        "nominal_radial_clearance_mm": nominal,
        "dimensional_minimum_radial_clearance_mm": minimum,
        "dimensional_maximum_radial_clearance_mm": maximum,
        "required_minimum_mm": required_mm,
        "dimensional_status": "screen-pass" if minimum >= required_mm else "screen-fail",
        "thermal_status": "unavailable: exact purchased pin/link material and CTE not identified",
        "overall_status": "open",
    }


def _make_candidate(vehicle: Vehicle, package: dict[str, Any]) -> tuple[Vehicle, set[str]]:
    raw = vehicle.model_dump(by_alias=True)
    parts = {item["id"]: item for item in raw["parts"]}
    changed: set[str] = set()
    if not vehicle.tvc:
        mount = parts["motor_mount"]
        mount["geometry"]["radius_m"] = float(package["fixed_mount_outer_radius_mm"]) / 1000
        mount["cad_mass"] = None
        changed.add("motor_mount")
    else:
        mount = parts["motor_mount"]
        mount["cad"]["parameters"]["rail_radial_width_mm"] = float(
            package["tvc_rail_radial_width_mm"]
        )
        mount["cad"]["parameters"]["rail_center_radius_mm"] = float(
            package["tvc_rail_center_radius_mm"]
        )
        mount["cad_mass"] = None
        changed.add("motor_mount")
        inner = parts["gimbal_inner"]
        inner["geometry"]["inner_radius_m"] = (
            float(package["tvc_inner_gimbal_bore_radius_mm"]) / 1000
        )
        inner["cad_mass"] = None
        changed.add("gimbal_inner")
    return Vehicle.model_validate(raw), changed


def _reconcile_copy(vehicle: Vehicle, changed: set[str], manifest: dict[str, Any]) -> Vehicle:
    rows = {row["id"]: row for row in manifest["parts"]}
    raw = vehicle.model_dump(by_alias=True)
    for item in raw["parts"]:
        if item["id"] not in changed:
            continue
        row = rows[item["id"]]
        props = row["properties"]
        item["cad_mass"] = {
            "shape_sha256": row["shape_sha256"],
            "volume_m3": props["volume_m3"],
            "cg_local_body_m": props["cg_local_body_m"],
            "inertia_per_kg_m2": props["inertia_per_kg_m2"],
            "basis": props["basis"],
        }
        offset = -props["cg_local_body_m"][0]
        item["cg_offset_m"] = 0.0 if -1e-12 < offset < 0 else offset
        if item["cad"]["mass_basis"] == "volume_density":
            item["mass_kg"] = props["volume_m3"] * DENSITY_KG_M3[item["material"]]
            item["density_kg_m3"] = None
    return Vehicle.model_validate(raw)


def _candidate_clearances(
    vehicle: Vehicle,
    package: dict[str, Any],
    engineering: dict[str, Any],
    study: dict[str, Any],
) -> list[dict[str, Any]]:
    parts = {part.id: part for part in vehicle.parts}
    req = study["required_minimum_clearance_mm"]
    tolerances = study["tolerance_basis"]
    if not vehicle.tvc:
        shell, mount = parts["aft_shell"], parts["motor_mount"]
        return [
            _clearance(
                "fixed mount outer envelope to aft-shell bore",
                shell.geometry["inner_radius_m"] * 1000,
                mount.geometry["radius_m"] * 1000,
                float(tolerances["fixed_shell_bore_radial_mm"]),
                float(tolerances["fixed_mount_outer_radius_mm"]),
                _profile(shell),
                _profile(mount),
                float(req["fixed_mount_to_shell"]),
                engineering,
                study,
                "Minimum clearance = shell inner radius minus the mount's trimmed outer cylindrical envelope; the rail rectangular corners are clipped by its CAD trim cylinder.",
            )
        ]

    mount = parts["motor_mount"]
    shield = parts["motor_radiant_shield"]
    inner = parts["gimbal_inner"]
    if mount.cad is None:
        raise ValueError("TVC motor mount must retain CAD parameters")
    p = mount.cad.parameters
    center = float(package["tvc_rail_center_radius_mm"])
    radial = float(package["tvc_rail_radial_width_mm"])
    tangential = float(p["rail_tangential_width_mm"])
    rail_inner = center - radial / 2
    rail_outer_corner = math.hypot(center + radial / 2, tangential / 2)
    grip = float(p["grip_outer_radius_mm"])
    gimbal_bore = inner.geometry["inner_radius_m"] * 1000
    return [
        _clearance(
            "TVC outer-foil radius to rectangular rail inner face",
            rail_inner,
            shield.geometry["radius_m"] * 1000,
            float(tolerances["tvc_rail_inner_feature_mm"]),
            float(tolerances["tvc_foil_outer_radius_mm"]),
            _profile(mount),
            _profile(shield),
            float(req["tvc_foil_to_rail_inner_face"]),
            engineering,
            study,
            "Radial one-sided clearance from the foil OD to the inward rail face. The rectangle's radial half-depth is used; no equivalent bounding circle is used.",
        ),
        _clearance(
            "TVC grip ring OD to inner-gimbal bore",
            gimbal_bore,
            grip,
            float(tolerances["tvc_gimbal_bore_radial_mm"]),
            float(tolerances["tvc_grip_outer_radius_mm"]),
            _profile(inner),
            _profile(mount),
            float(req["tvc_grip_to_inner_gimbal_bore"]),
            engineering,
            study,
            "Radial clearance between specified grip ring outer radius and inner-gimbal bore.",
        ),
        _clearance(
            "TVC rectangular rail outer corner to inner-gimbal bore",
            gimbal_bore,
            rail_outer_corner,
            float(tolerances["tvc_gimbal_bore_radial_mm"]),
            float(tolerances["tvc_rail_inner_feature_mm"]),
            _profile(inner),
            _profile(mount),
            float(req["tvc_rail_corner_to_inner_gimbal_bore"]),
            engineering,
            study,
            "Rail outer extent is the furthest corner of the rectangular radial-by-tangential section, hypot(center+depth/2,width/2), compared to the circular gimbal bore.",
        ),
    ]


def _source_paths(
    config_path: Path, engineering_path: Path, vehicle_configs: dict[str, str]
) -> set[Path]:
    paths = {
        config_path,
        engineering_path,
        Path(__file__).resolve(),
        Path("src/cad/verification.py"),
    }
    for config in vehicle_configs.values():
        paths.update(vehicle_input_paths(config))
    paths.update(Path("src/cad").glob("*.py"))
    return {path.resolve() for path in paths if path.is_file()}


def generate(config_path: Path, output_override: Path | None = None) -> Path:
    root = Path.cwd()
    config_path = config_path.resolve()
    study = yaml.safe_load(config_path.read_text())
    engineering_path = root / study["engineering_config"]
    engineering = yaml.safe_load(engineering_path.read_text())
    source_paths = _source_paths(config_path, engineering_path, study["vehicle_configs"])
    before = {str(path.relative_to(root)): _sha256(path) for path in sorted(source_paths)}
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    run_id = f"wo03-fit-correction-{stamp}"
    output_root = output_override or root / study["output_directory"] / stamp
    output_root.mkdir(parents=True, exist_ok=False)
    results: list[dict[str, Any]] = []
    for package in study["packages"]:
        package_results = []
        for config_id, config in study["vehicle_configs"].items():
            vehicle = load_vehicle(config)
            candidate, changed = _make_candidate(vehicle, package)
            candidate_root = output_root / package["id"] / vehicle.id
            manifest, solids = export_vehicle(candidate, candidate_root / "cad", export=False)
            candidate = _reconcile_copy(candidate, changed, manifest)
            candidate_path = candidate_root / "resolved-candidate.yaml"
            candidate_path.write_text(
                yaml.safe_dump(candidate.model_dump(by_alias=True), sort_keys=False)
            )
            before_mass = mass_properties(vehicle)
            after_mass = mass_properties(candidate)
            motion = verify(candidate, solids)
            clearances = _candidate_clearances(candidate, package, engineering, study)
            if candidate.tvc:
                dim = study["pin_and_link_dimensions"]
                current = dim["current"]
                tolerances = study["tolerance_basis"]
                pivot = _dimensional_only(
                    "pivot bore to pin, radial",
                    current["pivot_bore_diameter_mm"],
                    current["pivot_pin_diameter_mm"],
                    tolerances["pivot_bore_diameter_mm"],
                    tolerances["pivot_pin_diameter_mm"],
                    float(study["required_minimum_clearance_mm"]["pivot_pin_radial"]),
                )
                proposal = dim["proposals"]
                pivot_proposed = _dimensional_only(
                    "parameterized proposal pivot bore to pin, radial",
                    proposal["pivot_bearing_bore_diameter_mm"],
                    proposal["pin_source"]["nominal_diameter_mm"],
                    proposal["pivot_bearing_bore_diameter_tolerance_plus_minus_mm"] * 2,
                    max(proposal["pin_source"]["diameter_tolerance_plus_mm"]),
                    float(study["required_minimum_clearance_mm"]["pivot_pin_radial"]),
                )
                pin_low = float(proposal["pin_source"]["nominal_diameter_mm"]) + min(
                    proposal["pin_source"]["diameter_tolerance_plus_mm"]
                )
                pin_high = float(proposal["pin_source"]["nominal_diameter_mm"]) + max(
                    proposal["pin_source"]["diameter_tolerance_plus_mm"]
                )
                bore_low = float(proposal["pivot_bearing_bore_diameter_mm"]) - float(
                    proposal["pivot_bearing_bore_diameter_tolerance_plus_minus_mm"]
                )
                bore_high = float(proposal["pivot_bearing_bore_diameter_mm"]) + float(
                    proposal["pivot_bearing_bore_diameter_tolerance_plus_minus_mm"]
                )
                pivot_proposed.update(
                    {
                        "pin_diameter_bounds_mm": [pin_low, pin_high],
                        "bore_diameter_bounds_mm": [bore_low, bore_high],
                        "total_diametral_clearance_bounds_mm": [
                            bore_low - pin_high,
                            bore_high - pin_low,
                        ],
                        "per_side_radial_clearance_bounds_mm": [
                            (bore_low - pin_high) / 2,
                            (bore_high - pin_low) / 2,
                        ],
                        "temperature_fit_status": "open",
                        "retention_status": "open; plain dowel has no axial retainer",
                    }
                )
                pivot_proposed["minimum_clearance_mm"] = (bore_low - pin_high) / 2
                pivot_proposed["maximum_clearance_mm"] = (bore_high - pin_low) / 2
                pivot_proposed["status"] = (
                    "screen-pass"
                    if (bore_low - pin_high) / 2
                    >= float(study["required_minimum_clearance_mm"]["pivot_pin_radial"])
                    else "screen-fail"
                )
                linkage = _dimensional_only(
                    "link bore to rod, radial",
                    current["linkage_bore_diameter_mm"],
                    current["linkage_rod_diameter_mm"],
                    tolerances["linkage_bore_diameter_mm"],
                    tolerances["linkage_rod_diameter_mm"],
                    float(study["required_minimum_clearance_mm"]["linkage_radial"]),
                )
                pivot["parameterized_proposal"] = pivot_proposed
                clearances.extend([pivot, linkage])
                retention = {
                    "current_resolved_pin_geometry": current,
                    "positive_axial_retention_feature": False,
                    "paper_shell_stop_credited": False,
                    "retention_demand_and_capacity": "unavailable",
                    "proposal": proposal["retention_candidate"],
                    "status": "open; clip envelope needs local relief and exact CAD sweep; no capacity evidence",
                }
            else:
                retention = None
            item = {
                "configuration_id": config_id,
                "vehicle_id": candidate.id,
                "changed_parts": sorted(changed),
                "resolved_candidate_yaml": str(candidate_path.relative_to(root)),
                "resolved_candidate_yaml_sha256": _sha256(candidate_path),
                "part_shape_sha256": {
                    part_id: manifest["identity"]["part_shape_sha256"][part_id]
                    for part_id in changed
                },
                "actual_cad_manifest_identity": manifest["identity"],
                "copy_geometry_reconciled_mass": {
                    "baseline_total_mass_kg": before_mass.mass_kg,
                    "candidate_total_mass_kg": after_mass.mass_kg,
                    "delta_mass_kg": after_mass.mass_kg - before_mass.mass_kg,
                    "baseline_cg_m": before_mass.cg_m,
                    "candidate_cg_m": after_mass.cg_m,
                    "delta_cg_m": after_mass.cg_m - before_mass.cg_m,
                    "candidate_inertia_kg_m2": after_mass.inertia_kg_m2.tolist(),
                    "method": "Copy CAD regenerated from actual resolved parts; changed bulk part CADMass/mass/CG reconciled using local CAD geometry and material density; no analytic mass substitution.",
                },
                "clearance_stacks": clearances,
                "pin_retention_screen": retention,
                "actual_cad_motion_verification": motion,
                "motion_scope": "25 inclusive pitch/yaw poses at configured limits on regenerated candidate CAD. Includes actual foreplate, guard, rails, foil, motor, gimbals, rods and pin solids under the CAD verification sweep. Finite sampling and small joint zones mean no continuous/full mechanism proof.",
                "status": "proposal-only; no active spec mutation, no physical fit or qualification",
            }
            package_results.append(item)
        results.append(
            {
                "package_id": package["id"],
                "description": package["description"],
                "parameters": package,
                "configurations": package_results,
            }
        )
    after = {str(path.relative_to(root)): _sha256(path) for path in sorted(source_paths)}
    report = {
        "run_id": run_id,
        "work_order": "WO-03 expanded tolerance/motion correction study",
        "study_version": study["version"],
        "study_config_sha256": _sha256(config_path),
        "engineering_config_sha256": _sha256(engineering_path),
        "input_sha256_before": before,
        "input_sha256_after": after,
        "inputs_unchanged": before == after,
        "active_adoption": False,
        "flight_ready": False,
        "physical_fit_verified": False,
        "continuous_full_mechanism_verified": False,
        "acceptance": "open",
        "acceptance_passed": False,
        "cost_usd": 0,
        "material_expansion_basis": study["material_expansion"],
        "tolerance_basis": study["tolerance_basis"],
        "pin_link_parametric_proposal": study["pin_and_link_dimensions"],
        "unresolved": [
            "Exact assembled materials, lot-specific CTE, adhesive/foil fit and measured manufacturing capability are unverified.",
            "Purchased pins and rod-end materials/dimensions, bore process, positional tolerance, lubrication and wear are unavailable; thermal fit remains open.",
            "The 25-pose rigid CAD check is a finite sample. Joint zones are not articulation or supplier-fit evidence; wiring, continuous swept clearance and access remain unresolved.",
            "Reducing the G11 rail radial width changes structural section strength and requires updated load-path analysis; no rail strength credit is inferred from fit clearance.",
            "Clearance intervals are proposal-level calculated sensitivities; assembled fit and thermal correlation require as-built metrology and paired thermal measurement.",
        ],
        "packages": results,
    }
    report_path = output_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    run_root = root / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    record = {
        "run_id": run_id,
        "report": str(report_path.relative_to(root)),
        "report_sha256": _sha256(report_path),
        "study_config_sha256": report["study_config_sha256"],
        "inputs_unchanged": report["inputs_unchanged"],
        "active_adoption": False,
        "flight_ready": False,
        "physical_fit_verified": False,
        "acceptance": "open",
        "acceptance_passed": False,
        "cost_usd": 0,
    }
    (run_root / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-fit-correction.yaml")
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    path = generate(args.config, args.output)
    report = json.loads(path.read_text())
    print(path)
    print(f"run_id={report['run_id']} inputs_unchanged={report['inputs_unchanged']}")
    return 0 if report["inputs_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
