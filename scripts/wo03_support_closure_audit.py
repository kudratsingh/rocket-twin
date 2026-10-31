"""Bounded complete-path calculation audit; no design adoption or new FEA."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

for variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
):
    os.environ[variable] = "1"

import numpy as np
import yaml
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_fit_structure import section
from src.vehicle.mass import mass_properties
from src.vehicle.motors import load_rasp
from src.vehicle.schema import Vehicle

BAFFLE = Path("runs/wo03-baffle-fit-20261031T035358211715Z")
SUPPORT = Path("build/wo03-support-fea/20261031T000000Z")
RECOVERY = Path("build/wo03-recovery-budget-closure/record.json")
HOOP = Path("build/wo03-recovery-clearance/hoop/record.json")
RAILS = Path("build/wo03-tvc-rail-strength/record.json")
PRESSURE = Path("build/wo03-pressure-seal/record.json")
REC_CFG = Path("configs/studies/wo03-recovery-budget-closure.yaml")
BONDED = Path("build/wo03-bonded-reduced-20261030-final-v3/report.json")
FIT = Path("runs/wo03-fit-structure-20261030T221226140993Z/record.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> Any:
    return (
        json.loads(path.read_text()) if path.suffix == ".json" else yaml.safe_load(path.read_text())
    )


def vehicle(path: Path) -> Vehicle:
    return Vehicle.model_validate(read(path))


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def scan_thrust(v: Vehicle) -> list[dict[str, float]]:
    curve = load_rasp(v.motor.curve)
    loaded = mass_properties(v).mass_kg
    motor = next(p for p in v.parts if p.id == "motor")
    upstream = sum(p.resolved_mass_kg for p in v.parts if p.position_m < 0.922)
    rows = []
    for time_s, raw_thrust in curve.samples:
        mmotor = v.motor.casing_mass_kg + v.motor.propellant_mass_kg * (
            1 - curve.burned_fraction(float(time_s))
        )
        mass = loaded - motor.resolved_mass_kg + mmotor + v.design.mass_allowance_kg
        thrust = float(raw_thrust) * 1.15
        acceleration = thrust / mass
        rows.append(
            {
                "time_s": float(time_s),
                "source_thrust_multiplier": 1.15,
                "thrust_n": thrust,
                "mass_with_full_growth_kg": mass,
                "motor_mass_kg": mmotor,
                "specific_acceleration_mps2": acceleration,
                "motor_flank_n": thrust - mmotor * acceleration,
                "joint_n_forward_growth": (upstream + v.design.mass_allowance_kg) * acceleration,
                "joint_n_aft_growth": upstream * acceleration,
            }
        )
    return rows


def threshold(force_factored_n: float, area_mm2: float, screen_mpa: float) -> dict[str, float]:
    demand = force_factored_n / area_mm2
    return {
        "factored_force_n": force_factored_n,
        "area_mm2": area_mm2,
        "required_strength_mpa": demand,
        "existing_screen_mpa": screen_mpa,
        "screen_capacity_n": area_mm2 * screen_mpa,
        "screen_margin": screen_mpa / demand - 1,
    }


def axial_reactions(
    force_n: float, plate_inertia_n: float, radius_mm: float, port_xy: list[float]
) -> dict[str, Any]:
    angles = np.deg2rad([0, 120, 240])
    points = radius_mm * np.column_stack((np.cos(angles), np.sin(angles)))
    a = np.vstack((np.ones(3), points.T))
    rhs = np.array([force_n - plate_inertia_n, force_n * port_xy[0], force_n * port_xy[1]])
    reactions = np.linalg.solve(a, rhs)
    return {
        "port_xy_mm": port_xy,
        "rail_centroid_radius_mm": radius_mm,
        "input_aft_factored_n": force_n,
        "plate_inertia_removed_once_n": plate_inertia_n,
        "rail_forces_n_tension_positive": reactions.tolist(),
        "force_moment_balance_max_n_or_nmm": float(np.abs(a @ reactions - rhs).max()),
        "scope": "Determinate axial-only rigid foreplate/three-support fixture; does NOT include radial rope force, finite bending/torsion or qualified plate/rail continuity",
    }


def audit(output: Path) -> dict[str, Any]:
    started = time.monotonic()
    baffle_record, support_record = read(BAFFLE / "record.json"), read(SUPPORT / "report.json")
    recovery, hoop, rails, _pressure, bonded, fit = [
        read(p) for p in [RECOVERY, HOOP, RAILS, PRESSURE, BONDED, FIT]
    ]
    rec_cfg = read(REC_CFG)
    current_path = BAFFLE / "resolved-candidate.json"
    source_paths = [
        Path(__file__),
        current_path,
        BAFFLE / "record.json",
        SUPPORT / "report.json",
        SUPPORT / "resolved-braced-candidate.yaml",
        RECOVERY,
        HOOP,
        RAILS,
        PRESSURE,
        BONDED,
        FIT,
        REC_CFG,
        Path("configs/studies/wo03-recovery-anchor.yaml"),
        Path("configs/studies/wo03-bonded-support.yaml"),
        Path("configs/studies/wo03-g11-load-properties.yaml"),
        Path("src/analysis/bonded_support.py"),
        Path("scripts/wo03_fit_structure.py"),
        Path("scripts/wo03_recovery_budget_closure.py"),
        Path("src/vehicle/schema.py"),
        Path("src/vehicle/mass.py"),
        Path("src/vehicle/motors.py"),
        Path("src/cad/parts.py"),
        Path("src/cad/retention_parts.py"),
    ]
    source_paths.extend(Path(row["resolved_mass_copy"]) for row in recovery["modes"])
    source_paths.append(Path(hoop["resolved_copy"]))
    current = vehicle(current_path)
    source_paths.append(Path(current.motor.curve))
    hashes = {str(p): sha(p) for p in source_paths}
    if (
        baffle_record["candidate_identity"]
        != "69df790ec9bcba1465be4fa9861a7ad5fbc467091cbf58f44dee069e56e00bac"
    ):
        raise ValueError("Unexpected selected fitted-baffle identity")
    if sha(SUPPORT / "resolved-braced-candidate.yaml") != support_record["candidate_yaml_sha256"]:
        raise ValueError("Frame-only FEA source identity mismatch")
    recovery_alias_audits = []
    for row in recovery["modes"]:
        path = Path(row["resolved_mass_copy"])
        alias = read(path)
        masses = {p["id"]: p["mass_kg"] for p in alias["parts"]}
        embedded = {p["part_id"]: p["mass_g"] / 1000 for p in row["all_mass_ledger"]}
        schema_errors = 0
        try:
            Vehicle.model_validate(alias)
        except ValidationError as exc:
            schema_errors = exc.error_count()
        recovery_alias_audits.append(
            {
                "vehicle": row["vehicle"],
                "path": str(path),
                "recorded_sha256": row["resolved_mass_copy_sha256"],
                "current_sha256": sha(path),
                "file_identity_matches": sha(path) == row["resolved_mass_copy_sha256"],
                "part_ids_match_embedded_ledger": set(masses) == set(embedded),
                "current_alias_explicit_mass_max_difference_kg": max(
                    (abs(masses[p] - embedded[p]) for p in masses.keys() & embedded.keys()),
                    default=0,
                ),
                "current_alias_schema_error_count": schema_errors,
                "historical_mechanical_geometry_accepted_from_alias": False,
            }
        )
    if sha(Path(hoop["resolved_copy"])) != hoop["resolved_copy_sha256"]:
        raise ValueError("Hoop source copy changed")
    parts = {p.id: p for p in current.parts}
    mount, shell, upper = [parts[name] for name in ["motor_mount", "aft_shell", "body_upper"]]
    # Two local BRep slices only; never a full-vehicle CAD/FEA regeneration.
    sections = [section(mount, station) for station in [30.0, 125.0]]
    critical = min(sections, key=lambda x: x["area_mm2"])
    area = critical["area_mm2"]
    weak_i = min(x["principal_second_moments_mm4"][0] for x in sections)
    load_samples = scan_thrust(current)
    peak = max(load_samples, key=lambda x: x["motor_flank_n"])
    joint_peak = max(load_samples, key=lambda x: x["joint_n_forward_growth"])
    upper_area = math.pi * (
        (upper.geometry["radius_m"] * 1000) ** 2 - (upper.geometry["inner_radius_m"] * 1000) ** 2
    )
    shell_area = math.pi * (
        (shell.geometry["radius_m"] * 1000) ** 2 - (shell.geometry["inner_radius_m"] * 1000) ** 2
    )
    gap = (shell.geometry["inner_radius_m"] - mount.geometry["radius_m"]) * 1000
    bonds = [p for p in current.parts if p.id.startswith("mount_shell_bond_")]
    bond_areas = [p.cad_mass.volume_m3 * 1e9 / gap for p in bonds]
    positions = list(mount.cad.parameters["ring_stations_mm"])
    clear = max(b - a - 3 for a, b in pairwise(positions))
    fullspan = positions[-1] - positions[0] - 3
    hot = read(Path("configs/studies/wo03-bonded-support.yaml"))["materials"]
    thrust_rows = []
    for df in [1, 3]:
        f = df * peak["motor_flank_n"]
        thrust_rows.append(
            {
                "design_factor_sensitivity": df,
                "required_factor_is_3": True,
                "rail_equal_share": threshold(f, 3 * area, hot["plywood"]["strength_hot_mpa"]),
                "aft_shell_gross_only": threshold(f, shell_area, hot["cardboard"]["strength_mpa"]),
                "upper_joint_gross_only": threshold(
                    df * joint_peak["joint_n_forward_growth"],
                    upper_area,
                    hot["cardboard"]["strength_mpa"],
                ),
                "bond_average_all5_rings": threshold(
                    f, sum(bond_areas), hot["epoxy"]["shear_hot_mpa"]
                ),
                "bond_average_one_smallest_ring": threshold(
                    f, min(bond_areas), hot["epoxy"]["shear_hot_mpa"]
                ),
                "unbraced_required_rail_E_mpa": f * fullspan**2 / (3 * math.pi**2 * weak_i),
                "ideal_braces_required_rail_E_mpa": f * clear**2 / (3 * math.pi**2 * weak_i),
                "maximum_df_at_2mpa_aft_shell_gross": 2 * shell_area / peak["motor_flank_n"],
            }
        )
    old_ring = bonded["circumferential_ring_sensitivities"][0]
    ri, ro = mount.geometry["inner_radius_m"] * 1000, mount.geometry["radius_m"] * 1000
    ring_i = 3 * (ro - ri) ** 3 / 12
    ring_k = 1000 * ring_i / ((math.pi / 4 - 2 / math.pi) * ((ro + ri) / 2) ** 3)
    minimum_lambda = support_record["buckling_mesh_sensitivity"][-1]["critical_positive_factor"]
    frame = {
        "historical_FEA_candidate_file_sha256": support_record["candidate_yaml_sha256"],
        "historical_FEA_resolved_spec_sha256": support_record["candidate_resolved_spec_sha256"],
        "historical_reference_thrust_n": support_record["load"]["axial_thrust_n"],
        "critical_lambda": minimum_lambda,
        "required_lambda": 3,
        "last_mesh_relative_change": support_record[
            "critical_buckling_factor_medium_to_fine_relative_change"
        ],
        "frame_only_required_E_mpa_at_original_geometry_and_DF3": 1000 * 3 / minimum_lambda,
        "original_radius_mm": old_ring["outer_radius_mm"],
        "current_radius_mm": ro,
        "current_bore_mm": ri,
        "current_unperforated_ring_I_mm4": ring_i,
        "current_unperforated_ring_k_N_mm": ring_k,
        "unperforated_k_ratio_current_to_original": ring_k
        / old_ring["ideal_diametric_stiffness_n_mm"],
        "historical_FEA_pass_transferred_to_current_geometry": False,
        "full_body_bond_support_represented_by_frame_FEA": False,
    }
    rec_results = []
    for row in recovery["modes"]:
        if row["vehicle"] not in ["modular-performance-v1", "modular-performance-g54-hypothesis"]:
            continue
        cases = []
        for stored in row["force_cases"]:
            # Reproduce immutable EMBEDDED branch ledgers, not changed/stale aliases.
            case = stored
            acceleration = 3 * (case["speed_mps"] ** 2 / (0.6) + 9.80665)
            recomputed = [
                (b["part_mass_kg"] + b["growth_kg"]) * acceleration for b in case["branches"]
            ]
            balance = sum(recomputed) - case["whole_vehicle_factored_force_n"]
            if abs(balance) > 1e-8 or any(
                abs(f - b["factored_force_n"]) > 1e-8
                for f, b in zip(recomputed, case["branches"], strict=True)
            ):
                raise ValueError("Embedded recovery force reproduction failed")
            area_legacy = (
                rec_cfg["fixed_rail_screen"]["count"]
                * rec_cfg["fixed_rail_screen"]["clipped_area_each_mm2_estimate"]
            )
            cases.append(
                {
                    "scenario": case["scenario"],
                    "speed_mps": case["speed_mps"],
                    "whole_df3_n": case["whole_vehicle_factored_force_n"],
                    "aft_df3_n": next(
                        x["factored_force_n"] for x in case["branches"] if x["branch"] == "aft"
                    ),
                    "post_plate_df3_n": case["aft_post_plate_transfer_n"],
                    "full50g_on_aft_branch": True,
                    "balance_residual_n": case["balance_residual_n"],
                    "source_rail_collective_screen": threshold(
                        case["aft_post_plate_transfer_n"], area_legacy, 5
                    ),
                    "body_gross_proxy_mpa": case["body_uniform_axial_proxy_mpa"],
                    "body_gross_screen_mpa": 2,
                    "branches": case["branches"],
                }
            )
        rec_results.append(
            {
                "vehicle": row["vehicle"],
                "resolved_copy": row["resolved_mass_copy"],
                "resolved_sha256": row["resolved_mass_copy_sha256"],
                "loaded_total_g": sum(p["mass_g"] for p in row["all_mass_ledger"]),
                "separate_growth_g": 50,
                "recovery_baseline_g": recovery["existing_baseline_recovery_g"],
                "recovery_increment_g": row["recovery_increment_g"],
                "recovery_total_allocation_g": row["recovery_total_allocated_g"],
                "cases": cases,
            }
        )
    g54 = next(x for x in rec_results if x["vehicle"] == "modular-performance-g54-hypothesis")
    late = g54["cases"][-1]
    aft, plate = late["aft_df3_n"], late["aft_df3_n"] - late["post_plate_df3_n"]
    # This sensitivity is NOT composed with the different current baffle mount.
    reference_fit = next(
        x
        for x in fit["results"]
        if x["configuration"] == "G54" and x["candidate"] == "package-a-braced"
    )
    radius = min(reference_fit["sections"], key=lambda x: x["area_mm2"])["section_centroid_mm"][0]
    reactions = [
        axial_reactions(aft, plate, radius, point) for point in [[22, 0], [22, 5], [22, -5]]
    ]
    max_reaction = max(max(x["rail_forces_n_tension_positive"]) for x in reactions)
    one_rail_area = rec_cfg["fixed_rail_screen"]["clipped_area_each_mm2_estimate"]
    for x in reactions:
        x["one_rail_required_strength_mpa_at_44mm2"] = (
            max(x["rail_forces_n_tension_positive"]) / one_rail_area
        )
    requiredstop = late["speed_mps"] ** 2 / (
        2
        * (
            660
            / (
                3
                * (late["post_plate_df3_n"] / (3 * (late["speed_mps"] ** 2 / (2 * 0.3) + 9.80665)))
            )
            - 9.80665
        )
    )
    # Record known safe subitems without upgrading estimated capacity to rating.
    unresolved = {
        "canopy_shroud_leader_and18_ends": "No installed termination/heat/rate rating;200mm preparation remains an envelope, not qualified splice length",
        "junction": "Rounded G11 geometry only; crowding, laminate bending/contact and individual branch load introduction unrated",
        "nose": "Separate positive attachment not rated",
        "body": "Bands/bulkhead retention, paper tear, local peel and slip not rated; current gross branch screen already fails severe cases",
        "coupler": "Independent collar/pins still allowance; positive retention not implemented/rated; keys are not retention",
        "sled_cell_board": "Carrier fit/service geometry does not rate tabs, boards/cell restraint or output routing",
        "fixed_foreplate_rail_interface": "New recovery9.5mm web/long fingers differs from selected9mm/18mm thrust plate; no combined source or hot mixed-mode interface pass",
        "ring_bond_shell_joint": "No accepted hot peel/mixed-mode/paper normal bound, actual ring sharing/contact, shell buckling or finite joint retention stiffness",
        "motor_retention_pivots": "Exact motor shoulder/closure/nozzle, hardware grade/captive nut and axial pin retention remain dependencies",
    }
    original_fea = read(SUPPORT / "resolved-braced-candidate.yaml")
    oldparts = {p["id"]: p for p in original_fea["parts"]}
    compatibility = {
        name: {
            "old_geometry": oldparts[name]["geometry"],
            "current_geometry": parts[name].geometry,
            "old_parameters": oldparts[name]["cad"]["parameters"],
            "current_parameters": parts[name].cad.parameters,
            "same_geometry_parameters": oldparts[name]["geometry"] == parts[name].geometry
            and oldparts[name]["cad"]["parameters"] == parts[name].cad.parameters,
        }
        for name in ["motor_mount", "retention", "aft_shell", "body_upper"]
    }
    record = {
        "run_id": datetime.now(UTC).strftime("wo03-support-closure-audit-%Y%m%dT%H%M%S%fZ"),
        "elapsed_s": time.monotonic() - started,
        "input_sha256_before": hashes,
        "input_sha256_after": {str(p): sha(p) for p in source_paths},
        "inputs_unchanged": all(sha(p) == hashes[str(p)] for p in source_paths),
        "selected_fixed_candidate": {
            "id": current.id,
            "baffle_identity": baffle_record["candidate_identity"],
            "resolved_file": str(current_path),
            "resolved_sha256": sha(current_path),
            "loaded_mass_g": mass_properties(current).mass_kg * 1000,
            "full_growth_g": 50,
            "mount_mass_g": mount.resolved_mass_kg * 1000,
            "two_added_brace_rings_present": len(positions) == 5,
            "ring_stations_mm": positions,
            "bond_gap_mm": gap,
            "bond_material_mean_gap_contact_areas_mm2": bond_areas,
            "full_path_integrated_with_latest_independent_recovery": False,
        },
        "current_actual_mount_two_BRep_sections": sections,
        "current_motor_knot_loads": load_samples,
        "peak_motor_flank": peak,
        "peak_upper_joint": joint_peak,
        "thrust_path_floor_sensitivities": thrust_rows,
        "frame_only_evidence": frame,
        "old_frame_current_geometry_compatibility": compatibility,
        "fixed_recovery_exact_mass_and_force_partitions": rec_results,
        "recovery_mutable_alias_identity_audits": recovery_alias_audits,
        "fixed_single_port_axial_equilibrium_fixture": {
            "source_scope": "SourceG54recovery force and originalPackageA section-centroid sensitivity, NOT combined/adopted actual baffle layout",
            "cases": reactions,
            "required_hot_rail_strength_mpa_maximum": max_reaction / one_rail_area,
            "all3_rail_collective_hot_capacity_n": 660,
            "late_postplate_n": late["post_plate_df3_n"],
            "stop_distance_to_meet_collective660N_only_m": requiredstop,
            "stopping_distance_qualified_or_changed": False,
        },
        "G12_hoop_path": {
            "resolved_copy": hoop["resolved_copy"],
            "resolved_sha256": hoop["resolved_copy_sha256"],
            "mass": hoop["mass"],
            "rail_bounds": hoop["unchanged_rail_path_bounds"],
            "guide_cases": hoop["guide_mass_hypotheses"],
            "connected_cap_one_route_fails": True,
            "complete_path_verified": False,
        },
        "G12_strengthened_family_retained_failure": {
            "source_record": str(RAILS),
            "mass": rails["mass"],
            "required_minimum_area_mm2": rails[
                "required_minimum_area_for_largest_retained_axial_case_mm2"
            ],
            "buckling": rails["buckling"],
            "guide_cases": rails["guide_mass_hypotheses"],
            "adopted": False,
        },
        "pressure_seal_mass_credit_accepted_g": 0,
        "pressure_source_record": str(PRESSURE),
        "unresolved_installed_capacities": unresolved,
        "decision_inputs_required": [
            "Chosen actual paper tube layup/lot: hot/wet directional axial compression/tension, end crush, hoop stiffness and interlaminar peel/tear; nominal2MPa does not clear current full-path floor",
            "Actual adhesive/substrate preparation/cure/gap with hot mixed-mode shear/peel and stiffness; aluminum-lap typical data cannot rate paper/plywood",
            "Exact G11 grade/stock/lamination orientation: hot axial, bearing, interlaminar and flexural properties; supplier label conflict remains",
            "Qualified rope product/end construction, actual prepared length/EA/length spread, abrasion/heat and opening/snatch force-stroke envelope; no assumed0.3m stop qualification",
            "Exact certified motor variant, case/closure/nozzle envelope, hot-case history and G54 CG; retained thrust curve is an explicit hypothesis",
            "Actual5m usable guide and hardware; no budget credit from assumed equipment or unadopted fin/rail/pressure/thermal saving",
        ],
        "closed_subitems": [
            "Recorded source identities and complete dedicated-recovery bill are distinguishable from vehicle total and50g growth",
            "Recomputed fixed branch forces partition every source-copy part once and balance",
            "CurrentG54actual rail sections and bond-gap mean areas calculated without a fullvehicleCAD orFEA run",
            "Originalframe-only buckling result remains a limited verified fixture; no fictitious ground support added",
        ],
        "complete_path_acceptance": False,
        "new_design_family": False,
        "active_adoption": False,
        "new_FEA_or_flight": False,
        "flight_ready": False,
        "compute_cost_usd": 0,
    }
    if not record["inputs_unchanged"] or any(
        abs(x["force_moment_balance_max_n_or_nmm"]) > 1e-8 for x in reactions
    ):
        raise ValueError("Input identity/equilibrium audit failed")
    write_json(output / "audit.json", record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("build/wo03-support-closure-audit-v1"))
    args = parser.parse_args()
    if args.worker:
        audit(args.output)
        return 0
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "worker.log").open("w") as log:
        try:
            process = subprocess.run(
                [sys.executable, str(Path(__file__)), "--worker", "--output", str(args.output)],
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=120,
                check=False,
            )
            code, capped = process.returncode, False
        except subprocess.TimeoutExpired:
            code, capped = None, True
    result = {
        "child_returncode": code,
        "child120s_cap_reached": capped,
        "one_CPU": True,
        "maximum_total_CPU_budget_s": 600,
        "source_sha256": sha(Path(__file__)),
        "no_new_full_FEA": True,
        "acceptance": False,
    }
    if (args.output / "audit.json").exists():
        result["audit_sha256"] = sha(args.output / "audit.json")
    write_json(args.output / "record.json", result)
    print(args.output / "record.json")
    return 0 if code == 0 and not capped else 1


if __name__ == "__main__":
    raise SystemExit(main())
