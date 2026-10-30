"""Execute the explicit WO-03 thermal acceptance matrix on resolved candidates."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.engineering import material_profile
from src.analysis.thermal_topology import run_thermal_topology
from src.cad.parts import local_shape, properties
from src.sim.inputs import source_hashes
from src.vehicle.mass import mass_properties
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import CADMass, Part, Vehicle, load_vehicle, vehicle_input_paths


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(vehicle: Vehicle) -> str:
    return hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()


def mass_record(vehicle: Vehicle) -> dict[str, Any]:
    value = mass_properties(vehicle)
    return {
        "mass_kg": float(value.mass_kg),
        "cg_m": float(value.cg_m),
        "cg_lateral_m": list(value.cg_lateral_m),
        "inertia_kg_m2": value.inertia_kg_m2.tolist(),
        "budget_kg": value.budget_kg,
    }


def rebuild_part_mass(part: Part) -> dict[str, Any]:
    """Recompute exact local CAD mass properties after a study-only geometry edit."""
    if part.cad is None:
        raise ValueError(f"{part.id}: geometry sensitivity requires CAD definition")
    props = properties(part, local_shape(part))
    part.cad_mass = CADMass.model_validate(props)
    part.mass_kg = float(props["volume_m3"]) * DENSITY_KG_M3[part.material]
    part.density_kg_m3 = None
    part.cg_offset_m = max(0.0, -float(props["cg_local_body_m"][0]))
    return props


def apply_mount_bond_geometry(vehicle: Vehicle, radial_gap_m: float) -> dict[str, Any]:
    """Apply a bounded mount gap and rebuild mount/bond solids and mass properties."""
    parts = {part.id: part for part in vehicle.parts}
    mount = parts["motor_mount"]
    shell = parts["aft_shell"]
    bonds = sorted(
        (part for part in vehicle.parts if part.id.startswith("mount_shell_bond_")),
        key=lambda part: part.id,
    )
    if not bonds or mount.cad is None:
        raise ValueError(f"{vehicle.id}: Package A fixed mount/bond geometry is absent")
    shell_inner = float(shell.geometry["inner_radius_m"])
    mount.geometry["radius_m"] = shell_inner - radial_gap_m
    mount_props = rebuild_part_mass(mount)
    bond_rows = []
    for bond in bonds:
        if bond.cad is None:
            raise ValueError(f"{bond.id}: bond ring requires CAD definition")
        bond.geometry["radius_m"] = shell_inner
        bond.geometry["inner_radius_m"] = float(mount.geometry["radius_m"])
        bond.geometry["wall_m"] = radial_gap_m
        props = rebuild_part_mass(bond)
        bond_rows.append(
            {
                "part_id": bond.id,
                "gap_m": radial_gap_m,
                "axial_position_m": bond.position_m,
                "axial_width_m": float(bond.geometry["length_m"]),
                "cad_volume_m3": float(props["volume_m3"]),
                "cad_area_m2": float(props["volume_m3"]) / radial_gap_m,
                "mass_kg": bond.resolved_mass_kg,
                "shape_sha256": props["shape_sha256"],
                "slot_interrupted": bool(bond.cad.parameters.get("fin_slots")),
            }
        )
    return {
        "radial_gap_m": radial_gap_m,
        "mount_outer_radius_m": float(mount.geometry["radius_m"]),
        "shell_inner_radius_m": shell_inner,
        "mount_mass_kg": mount.resolved_mass_kg,
        "mount_volume_m3": float(mount_props["volume_m3"]),
        "mount_shape_sha256": mount_props["shape_sha256"],
        "bonds": bond_rows,
        "bond_mass_kg": sum(row["mass_kg"] for row in bond_rows),
        "bond_area_m2": sum(row["cad_area_m2"] for row in bond_rows),
        "bond_volume_m3": sum(row["cad_volume_m3"] for row in bond_rows),
    }


def make_topology(base: dict[str, Any], vehicle: Vehicle, contact_w_k: float) -> dict[str, Any]:
    """Remove legacy broad mount/shell link and model the actual serial bond rings."""
    study = copy.deepcopy(base)
    bonds = [part for part in vehicle.parts if part.id.startswith("mount_shell_bond_")]
    if not bonds:
        return study
    study["contact_pairs"] = [
        pair for pair in study["contact_pairs"] if set(pair) != {"motor_mount", "aft_shell"}
    ]
    study["part_ids"] = list(dict.fromkeys([*study["part_ids"], *(part.id for part in bonds)]))
    study["required_case_coupled_part_ids"] = list(
        dict.fromkeys([*study["required_case_coupled_part_ids"], *(part.id for part in bonds)])
    )
    study["pad_conduction_part_ids"] = list(
        dict.fromkeys([*study["pad_conduction_part_ids"], *(part.id for part in bonds)])
    )
    study.setdefault("pad_conduction_thickness_m", {}).update(
        {part.id: float(part.geometry["wall_m"]) for part in bonds}
    )
    pair_values = study.setdefault("contact_pair_conductance_w_k", {})
    for bond in bonds:
        study["contact_pairs"].extend([["motor_mount", bond.id], [bond.id, "aft_shell"]])
        pair_values[f"motor_mount->{bond.id}"] = float(contact_w_k)
        pair_values[f"{bond.id}->aft_shell"] = float(contact_w_k)
    return study


def apply_property_corner(
    cfg: dict[str, Any], corner: dict[str, Any], bond_k_w_m_k: float | None
) -> dict[str, Any]:
    """Scale thermal k/cp coherently, clamped to source-published explicit profile ranges."""
    result = copy.deepcopy(cfg)
    for name, profile in result["materials"].items():
        if not isinstance(profile, dict):
            continue
        for field, factor_key, bounds_key in (
            ("conductivity_w_m_k", "conductivity_factor", "conductivity_range_w_m_k"),
            ("cp_j_kg_k", "cp_factor", "cp_range_j_kg_k"),
        ):
            if field not in profile:
                continue
            if name == "epoxy" and field == "conductivity_w_m_k" and bond_k_w_m_k is not None:
                profile[field] = bond_k_w_m_k
                profile["conductivity_range_w_m_k"] = [bond_k_w_m_k, bond_k_w_m_k]
                continue
            value = float(profile[field]) * float(corner[factor_key])
            bounds = profile.get(bounds_key)
            if bounds:
                value = min(float(bounds[1]), max(float(bounds[0]), value))
            profile[field] = value
    return result


def case_config(
    cfg: dict[str, Any], case: dict[str, Any], bond_k_w_m_k: float | None, corner: dict[str, Any]
) -> dict[str, Any]:
    result = apply_property_corner(cfg, corner, bond_k_w_m_k)
    scenario = int(case["source_scenario_index"])
    result["thermal"]["ambient_c"][scenario] = float(case["ambient_c"])
    result["thermal"]["external_case_peak_c"][scenario] = float(case["case_peak_c"])
    result["thermal"]["post_burn_cooling_tau_s"][scenario] = float(case["cooling_tau_s"])
    result["materials"]["aluminum"]["surface_emissivity_by_scenario"][scenario] = float(
        case["outer_foil_emissivity"]
    )
    return result


def summarize_thermal(
    output: dict[str, Any],
    candidate: Vehicle,
    reference_mass: dict[str, Any],
    case: dict[str, Any],
    property_corner: dict[str, Any],
    gap_row: dict[str, Any] | None,
    contact_w_k: float | None,
) -> dict[str, Any]:
    peaks = []
    violations = []
    for row in output["peaks"]:
        peak = {
            "part_id": row["part_id"],
            "peak_c": float(row["peak_c"]),
            "peak_time_s": float(row["peak_time_s"]),
            "screen_limit_c": row["screen_limit_c"],
            "margin_k": row["margin_k"],
            "material_profile": material_profile(
                next(part for part in candidate.parts if part.id == row["part_id"])
            ),
            "evidence": "calculated using estimated/assumed thermal properties and prescribed boundary",
        }
        peaks.append(peak)
        if peak["margin_k"] is not None and float(peak["margin_k"]) < 0:
            violations.append(peak)
    return {
        "candidate_id": case["candidate_id"],
        "mode": candidate.id,
        "candidate_vehicle_identity_sha256": identity(candidate),
        "case_id": case["id"],
        "role": case["role"],
        "ambient_c": float(output["ambient_c"]),
        "prescribed_case_peak_c": float(output["prescribed_case_peak_c"]),
        "prelaunch_powered_soak_s": float(output["prelaunch_powered_soak_s"]),
        "prelaunch_energy_balance": output["prelaunch_energy_balance"],
        "initial_condition": output["initial_condition"],
        "cooling_tau_s": float(output["post_burn_cooling_tau_s"]),
        "burn_time_s": float(candidate.motor.burn_time_s) if candidate.motor else None,
        "soak_end_time_s": float(output["times_s"][-1]),
        "screen_limit_substrate_c": 45.0,
        "bond_geometry_sensitivity": gap_row,
        "bond_interface_contact_conductance_w_k_per_ring": contact_w_k,
        "material_property_corner": property_corner["id"],
        "material_property_factors": {
            "conductivity": property_corner["conductivity_factor"],
            "specific_heat": property_corner["cp_factor"],
        },
        "max_temperature_c": max(float(p["peak_c"]) for p in peaks),
        "worst_limited_part": min(
            (p for p in peaks if p["margin_k"] is not None),
            key=lambda p: float(p["margin_k"]),
            default=None,
        ),
        "parts_over_declared_limit": violations,
        "thermal_screen_status": "FAIL_SCREEN" if violations else "PASS_SCREEN",
        "energy_residual_j": float(output["energy_residual_j"]),
        "peaks": peaks,
        "limitations": output["limitations"],
        "acceptance_interpretation": (
            "required robustness case; a numerical screen pass does not close the absent exact motor history or foil-aging correlation"
            if case["role"] == "required_robustness_case"
            else (
                "operating-restriction proposal only; not acceptance and not an approved ambient boundary change"
                if str(case["role"]).startswith("proposed_operating_restriction")
                else "bounded numerical screen only; no hardware qualification"
            )
        ),
        "candidate_mass_cg_inertia": mass_record(candidate),
        "nominal_candidate_mass_cg_inertia": reference_mass,
        "active_adoption": False,
        "flight_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    parser.add_argument(
        "--warm-start-only",
        action="store_true",
        help="run the configured powered prelaunch soak for the 25 C combined robustness proposal only",
    )
    parser.add_argument(
        "--ignition-bound-only",
        action="store_true",
        help="run the 25 C combined robustness proposal with configured component temperature bounds at ignition",
    )
    args = parser.parse_args()
    if args.warm_start_only and args.ignition_bound_only:
        raise ValueError("choose either warm-start-only or ignition-bound-only")

    matrix_path = Path("configs/engineering/wo03-thermal-acceptance.yaml")
    matrix = yaml.safe_load(matrix_path.read_text())
    engineering_path = Path(matrix["engineering_inputs"])
    thermal_path = Path(matrix["thermal_topology"])
    package_record_path = Path(matrix["source_record"])
    package_record = json.loads(package_record_path.read_text())
    if not package_record.get("inputs_unchanged"):
        raise ValueError("source correction package does not have unchanged inputs")
    source_package_rows = {
        path: row
        for row in package_record["results"]
        for path in (row["candidate_path"], row.get("candidate_alias_path", row["candidate_path"]))
    }

    platform = yaml.safe_load(args.config.read_text())
    if not isinstance(platform, dict) or not platform.get("vehicles"):
        raise ValueError(f"platform config {args.config} has no configured vehicle list")
    cfg = yaml.safe_load(engineering_path.read_text())
    base_study = yaml.safe_load(thermal_path.read_text())
    candidate_inputs: list[dict[str, Any]] = []
    vehicles: dict[str, Vehicle] = {}
    input_paths: set[Path] = {
        args.config,
        matrix_path,
        engineering_path,
        thermal_path,
        package_record_path,
        Path(__file__).resolve().relative_to(Path.cwd()),
        Path("scripts/wo03_correction_package.py"),
        Path("scripts/wo03_fit_correction_study.py"),
        Path("scripts/wo03_fit_structure.py"),
        Path("configs/studies/wo03-correction-package.yaml"),
        Path("src/analysis/thermal_topology.py"),
        Path("src/analysis/thermal_radial.py"),
        Path("src/analysis/engineering.py"),
        Path("src/cad/parts.py"),
        Path("src/vehicle/mass.py"),
        Path("src/vehicle/materials.py"),
        Path("src/vehicle/schema.py"),
    }
    for candidate_cfg in matrix["candidates"]:
        candidate_path = Path(candidate_cfg["candidate_yaml"])
        path_key = candidate_path.as_posix()
        if path_key not in source_package_rows:
            raise ValueError(f"candidate {candidate_path} is not listed in source package record")
        expected_sha = source_package_rows[path_key].get("candidate_sha256")
        if expected_sha and sha256(candidate_path) != expected_sha:
            raise ValueError(f"candidate {candidate_path} differs from the recorded package")
        candidate_vehicle = load_vehicle(candidate_path)
        if candidate_vehicle.id != candidate_cfg["mode"]:
            raise ValueError(f"candidate {candidate_path} resolved to unexpected mode")
        vehicles[candidate_cfg["id"]] = candidate_vehicle
        input_paths.add(candidate_path)
        input_paths.update(vehicle_input_paths(candidate_path))
        candidate_inputs.append(
            {
                **candidate_cfg,
                "candidate_path_sha256": sha256(candidate_path),
                "candidate_identity_sha256": identity(candidate_vehicle),
                "source_package_result": source_package_rows[path_key],
            }
        )
    for vehicle in vehicles.values():
        for source_path in source_hashes(vehicle):
            path = Path(source_path)
            if path.exists():
                input_paths.add(path)

    before_hashes = {path.as_posix(): sha256(path) for path in sorted(input_paths)}
    for vehicle in vehicles.values():
        before_hashes.update(source_hashes(vehicle))

    cells = int(
        matrix["execution"]["tiny_cells"]
        if args.preset == "tiny"
        else matrix["execution"]["sim_cells"]
    )
    property_corners = matrix["material_property_uncertainty"]["factors"]
    gap_variants = matrix["bonded_brace_sensitivities"]["gap_k_bounds"]
    wetting_bounds = matrix["bonded_brace_sensitivities"][
        "interface_contact_conductance_w_k_per_ring"
    ]
    cases = matrix["cases"]
    if args.warm_start_only or args.ignition_bound_only:
        proposal = (
            matrix["warm_start_proposal"]
            if args.warm_start_only
            else matrix["ignition_bound_proposal"]
        )
        cases = [case for case in cases if case["id"] == proposal["case_id"]]
        if len(cases) != 1:
            raise ValueError("warm-start case id must resolve to exactly one matrix case")
    result_rows: list[dict[str, Any]] = []
    gap_geometry: dict[str, dict[str, Any]] = {}

    for candidate_cfg in matrix["candidates"]:
        candidate_id = candidate_cfg["id"]
        source_vehicle = vehicles[candidate_id]
        is_fixed = bool(candidate_cfg["mount_shell_bond_applicable"])
        if is_fixed:
            variants = gap_variants
            interface_levels: list[float | None] = [float(value) for value in wetting_bounds]
        else:
            variants = [
                {
                    "id": "not_applicable_to_tvc_cassette",
                    "radial_gap_m": None,
                    "adhesive_conductivity_w_m_k": None,
                }
            ]
            interface_levels = [None]
        for gap_variant in variants:
            for property_corner in property_corners:
                for case in cases:
                    if (
                        case["id"]
                        in {
                            "upper_hot_soak_250C_eps03_at25C",
                            "case_300C_eps03_at25C",
                            "contaminated_250C_eps09_at25C",
                        }
                        and property_corner["id"] != "nominal"
                    ):
                        # These are secondary operating probes; combined-case 25 C
                        # receives the full material/contact/gap uncertainty sweep.
                        continue
                    for contact_w_k in interface_levels:
                        candidate = source_vehicle.model_copy(deep=True)
                        gap_row = None
                        if is_fixed:
                            gap_row = apply_mount_bond_geometry(
                                candidate, float(gap_variant["radial_gap_m"])
                            )
                            gap_geometry[f"{candidate_id}:{gap_variant['id']}"] = gap_row
                        nominal_mpi = mass_record(source_vehicle)
                        candidate_study = make_topology(
                            base_study,
                            candidate,
                            float(contact_w_k) if contact_w_k is not None else 0.0,
                        )
                        if args.warm_start_only:
                            candidate_study["prelaunch_powered_soak_s"] = float(
                                matrix["warm_start_proposal"]["prelaunch_powered_soak_s"]
                            )
                        elif args.ignition_bound_only:
                            candidate_study["initial_temperature_c"] = float(
                                matrix["ignition_bound_proposal"]["initial_temperature_c"]
                            )
                            candidate_study["initial_part_temperature_c"] = dict(
                                matrix["ignition_bound_proposal"]["initial_part_temperature_c"]
                            )
                        case_cfg = case_config(
                            cfg,
                            case,
                            float(gap_variant["adhesive_conductivity_w_m_k"]) if is_fixed else None,
                            property_corner,
                        )
                        run_case = {**case, "candidate_id": candidate_id}
                        output = run_thermal_topology(
                            candidate,
                            case_cfg,
                            candidate_study,
                            False,
                            cells=cells,
                            max_step_s=float(matrix["execution"]["max_step_s"]),
                            scenario_index=int(case["source_scenario_index"]),
                            heat_flow_step_s=float(
                                matrix["execution"]["heat_flow_postprocess_step_s"]
                            ),
                        )
                        row = summarize_thermal(
                            output,
                            candidate,
                            nominal_mpi,
                            run_case,
                            property_corner,
                            gap_row,
                            contact_w_k,
                        )
                        row.update(
                            {
                                "candidate_role": candidate_cfg["role"],
                                "bond_gap_k_variant": gap_variant["id"],
                                "evidence_level": "calculated candidate-copy analysis; all inputs estimated, assumed or source-transcribed",
                                "case_source_basis": case["case_source_basis"],
                                "status_basis": case["status_basis"],
                                "case_role": case["role"],
                            }
                        )
                        result_rows.append(row)
                        if len(result_rows) % 50 == 0:
                            print(f"matrix_rows_completed {len(result_rows)}", flush=True)

    after_hashes = {path.as_posix(): sha256(path) for path in sorted(input_paths)}
    for vehicle in vehicles.values():
        after_hashes.update(source_hashes(vehicle))
    if before_hashes != after_hashes:
        changed = sorted(
            key
            for key in before_hashes.keys() | after_hashes.keys()
            if before_hashes.get(key) != after_hashes.get(key)
        )
        raise RuntimeError(f"study inputs changed while running: {changed}")

    run_prefix = (
        "wo03-thermal-warm-matrix"
        if args.warm_start_only
        else (
            "wo03-thermal-ignition-bound-matrix"
            if args.ignition_bound_only
            else "wo03-thermal-matrix"
        )
    )
    run_id = datetime.now(UTC).strftime(f"{run_prefix}-%Y%m%dT%H%M%S%fZ")
    run_dir = Path("runs") / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    detail_path = run_dir / "matrix-results.json"
    detail = {
        "run_id": run_id,
        "configuration": matrix,
        "candidate_inputs": candidate_inputs,
        "bond_gap_geometry_rows": gap_geometry,
        "rows": result_rows,
        "source_hashes": after_hashes,
        "input_hashes_unchanged": True,
        "warm_start_only": args.warm_start_only,
        "ignition_bound_only": args.ignition_bound_only,
        "prelaunch_powered_soak_s": (
            float(matrix["warm_start_proposal"]["prelaunch_powered_soak_s"])
            if args.warm_start_only
            else 0.0
        ),
        "initial_temperature_c": (
            float(matrix["ignition_bound_proposal"]["initial_temperature_c"])
            if args.ignition_bound_only
            else None
        ),
        "initial_part_temperature_c": (
            matrix["ignition_bound_proposal"]["initial_part_temperature_c"]
            if args.ignition_bound_only
            else {}
        ),
        "acceptance_decision": {
            "classification": "OPEN",
            "required_robustness_case": matrix["acceptance"]["required_robustness_case"],
            "reason": matrix["acceptance"]["uncertainty_rule"],
            "screen_limit_c": float(matrix["acceptance"]["substrate_screen_c"]),
            "all_active_limits_preserved": True,
            "active_adoption": False,
            "flight_ready": False,
        },
    }
    detail_bytes = (json.dumps(detail, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    detail_path.write_bytes(detail_bytes)
    role_status = Counter(
        f"{row['case_role']}::{row['thermal_screen_status']}" for row in result_rows
    )
    record = {
        "run_id": run_id,
        "preset": args.preset,
        "record_version": (
            "wo03-thermal-warm-acceptance-matrix-v1"
            if args.warm_start_only
            else (
                "wo03-thermal-ignition-bound-matrix-v1"
                if args.ignition_bound_only
                else "wo03-thermal-acceptance-matrix-v1"
            )
        ),
        "detail_artifact": detail_path.as_posix(),
        "detail_artifact_sha256": hashlib.sha256(detail_bytes).hexdigest(),
        "source_record": package_record_path.as_posix(),
        "source_record_sha256": sha256(package_record_path),
        "candidate_count": len(candidate_inputs),
        "case_count": len(cases),
        "matrix_row_count": len(result_rows),
        "warm_start_only": args.warm_start_only,
        "ignition_bound_only": args.ignition_bound_only,
        "prelaunch_powered_soak_s": (
            float(matrix["warm_start_proposal"]["prelaunch_powered_soak_s"])
            if args.warm_start_only
            else 0.0
        ),
        "initial_temperature_c": (
            float(matrix["ignition_bound_proposal"]["initial_temperature_c"])
            if args.ignition_bound_only
            else None
        ),
        "case_status_counts": dict(sorted(role_status.items())),
        "source_input_count": len(after_hashes),
        "source_hashes": after_hashes,
        "inputs_unchanged": True,
        "acceptance_classification": "OPEN",
        "required_robustness_case": "combined_300C_eps09_at35C",
        "active_adoption": False,
        "thermal_acceptance_passed": False,
        "flight_ready": False,
        "cost_usd": 0,
        "physical_work_performed": False,
    }
    record_bytes = (json.dumps(record, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    record_path = run_dir / "record.json"
    record_path.write_bytes(record_bytes)
    print(f"record {record_path}")
    print(f"inputs_unchanged {record['inputs_unchanged']}")
    print(f"matrix_rows {len(result_rows)}")
    print(f"acceptance_classification {record['acceptance_classification']}")
    print(f"record_sha256 {hashlib.sha256(record_bytes).hexdigest()}")
    print(f"matrix_artifact_sha256 {record['detail_artifact_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
