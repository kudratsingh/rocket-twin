"""Static motor trade study; no flight propagation and no motor selection.

Uses the parts-tree mass moments and source RASP data. A loaded RASP mass is
interpreted as an assembled motor hypothesis, so its dry casing mass is included
once. Mount reserves are incremental to the existing mount, not total mount mass.
No thrust trace is constructed from conflicting summary specifications.

Local checks cover axial bounds and nominal diameter only. Radial pose, thrust-ring
fit, gimbal sweeps, retention, thermal isolation and measured mass distributions
require CAD/component evidence. Candidate motor CG uses a geometric midpoint
assumption; numerical reference agreement cannot validate that assumption.
"""

from __future__ import annotations

from typing import Any

from src.sim.frames import STANDARD_GRAVITY_M_S2
from src.vehicle.mass import mass_properties
from src.vehicle.motors import load_rasp
from src.vehicle.reference import compare_rocketpy
from src.vehicle.schema import Vehicle


def candidate_vehicle(
    baseline: Vehicle, curve_path: str, reserve_kg: float, keep_aft_station: bool
) -> Vehicle:
    if reserve_kg < 0:
        raise ValueError("mount reserve cannot be negative")
    curve = load_rasp(curve_path)
    data = baseline.model_dump(by_alias=True)
    motor_part = next(p for p in data["parts"] if p["type"] == "motor")
    previous_aft = motor_part["position_m"] + motor_part["geometry"]["length_m"]
    station = previous_aft - curve.length_m if keep_aft_station else motor_part["position_m"]
    data["motor"].update(
        id=curve.designation,
        curve=curve_path,
        propellant_mass_kg=curve.propellant_mass_kg,
        casing_mass_kg=curve.loaded_mass_kg - curve.propellant_mass_kg,
        mount_position_m=station,
        burn_time_s=curve.burn_time_s,
        total_impulse_ns=curve.total_impulse_ns,
        average_thrust_n=curve.average_thrust_n,
        estimate=True,
        cite=f"{curve_path}; unselected local study hypothesis",
    )
    motor_part.update(
        position_m=station,
        mass_kg=curve.loaded_mass_kg,
        cg_offset_m=curve.length_m / 2,
        estimate=True,
        cite=f"{curve_path}; assembled mass hypothesis, midpoint CG estimate",
    )
    motor_part["geometry"].update(
        length_m=curve.length_m, diameter_m=curve.diameter_m, radius_m=curve.diameter_m / 2
    )
    if reserve_kg:
        mount = next(p for p in baseline.parts if p.id == "motor_mount")
        data["parts"].append(
            {
                "id": "study_mount_reserve",
                "type": "commercial",
                "parent": "motor_mount",
                "position_m": mount.cg_station_m - 0.005,
                "cg_offset_m": 0.005,
                "geometry": {"bbox_m": [0.01, 0.01, 0.01]},
                "mass_kg": reserve_kg,
                "material": "PETG",
                "estimate": True,
                "learn": "Incremental mounting and retention mass reserve beyond the original mount. This lumped mass is not an actual bracket design or a claim of fit.",
            }
        )
    return Vehicle.model_validate(data)


def evaluate_candidate(
    baseline: Vehicle,
    curve_path: str,
    reserve_kg: float,
    keep_aft_station: bool,
    compare: bool = True,
) -> dict[str, Any]:
    curve = load_rasp(curve_path)
    old_motor = next(p for p in baseline.parts if p.type == "motor")
    station = (
        old_motor.position_m + old_motor.geometry["length_m"] - curve.length_m
        if keep_aft_station
        else old_motor.position_m
    )
    aft = station + curve.length_m
    mount = next(p for p in baseline.parts if p.id == "motor_mount")
    row: dict[str, Any] = {
        "curve": curve_path,
        "designation": curve.designation,
        "pose": "hold_aft_station" if keep_aft_station else "hold_motor_front_station",
        "motor_front_m": station,
        "motor_aft_m": aft,
        "front_shift_m": station - old_motor.position_m,
        "body_wall_m": next(p.geometry["wall_m"] for p in baseline.parts if p.type == "body_tube"),
        "motor_loaded_mass_kg": curve.loaded_mass_kg,
        "motor_dry_mass_included_kg": curve.loaded_mass_kg - curve.propellant_mass_kg,
        "propellant_mass_kg": curve.propellant_mass_kg,
        "existing_mount_mass_kg": mount.resolved_mass_kg,
        "incremental_mount_mass_kg": reserve_kg,
        "burn_time_s": curve.burn_time_s,
        "mean_thrust_n": curve.average_thrust_n,
        "axial_bounds_pass": station >= 0 and aft <= baseline.airframe["length_m"] + 1e-9,
        "nominal_bore_pass": curve.diameter_m <= mount.geometry["id_m"],
        "mechanical_fit_verified": False,
        "selected": False,
    }
    if not row["axial_bounds_pass"]:
        row["rejection"] = (
            "Candidate exceeds unchanged vehicle axial envelope at fixed front station"
        )
        return row
    candidate = candidate_vehicle(baseline, curve_path, reserve_kg, keep_aft_station)
    launch, end = mass_properties(candidate), mass_properties(candidate, 1)
    twr = curve.average_thrust_n / (launch.mass_kg * STANDARD_GRAVITY_M_S2)
    row.update(
        liftoff_mass_kg=launch.mass_kg,
        burnout_mass_kg=end.mass_kg,
        cg_liftoff_m=launch.cg_m,
        cg_burnout_m=end.cg_m,
        mean_thrust_to_liftoff_weight=twr,
        additional_mass_headroom_to_twr_3_kg=curve.average_thrust_n / (3 * STANDARD_GRAVITY_M_S2)
        - launch.mass_kg,
        nominal_performance_pass=twr >= 3 and curve.burn_time_s >= 3,
        cg_model="uniform motor midpoint, unvalidated; same assumption given to reference",
    )
    if compare:
        row["reference_comparison"] = compare_rocketpy(candidate)
    return row


def screen_summary(baseline: Vehicle, item: dict[str, Any], reserve_kg: float) -> dict[str, Any]:
    """Conservative published-summary screening, never a time trace or fit approval.

    Preserve contradictory mass hypotheses separately. A lower post-test impulse
    is a second evidence case, not a replacement for any archived thrust samples.
    The necessary maximum burn time follows I/T >= target_TWR * m * g; it is not
    a prediction of the actual burn duration.
    """
    import math

    masses = item.get("assembled_mass_hypotheses_kg")
    if masses is None:
        masses = [item["published_total_mass_kg"]]
    if (
        not masses
        or not math.isfinite(reserve_kg)
        or reserve_kg < 0
        or any(not math.isfinite(m) or m <= 0 for m in masses)
    ):
        raise ValueError("mass hypotheses must be positive and reserve nonnegative, all finite")
    original_motor = next(p for p in baseline.parts if p.type == "motor")
    airframe_mass = mass_properties(baseline).mass_kg - original_motor.resolved_mass_kg
    scenarios = []
    for motor_mass in masses:
        mass = airframe_mass + motor_mass + reserve_kg
        scenario = {
            "assumed_assembled_motor_mass_kg": motor_mass,
            "liftoff_mass_kg": mass,
            "summary_only_twr": item["published_average_thrust_n"] / (mass * STANDARD_GRAVITY_M_S2),
        }
        if item.get("posttest_total_impulse_ns") is not None:
            scenario["max_burn_time_for_twr_3_at_posttest_impulse_s"] = item[
                "posttest_total_impulse_ns"
            ] / (3 * mass * STANDARD_GRAVITY_M_S2)
        scenarios.append(scenario)
    worst = max(scenarios, key=lambda row: row["liftoff_mass_kg"])
    return {
        **item,
        "mass_scenarios": scenarios,
        "incremental_mount_mass_kg": reserve_kg,
        "screening_liftoff_mass_with_max_mount_reserve_kg": worst["liftoff_mass_kg"],
        "summary_only_twr": worst["summary_only_twr"],
        "reference_comparison": None,
        "selected": False,
        "selection_eligible": False,
        "note": "Summary evidence only: no thrust trace, CG, mechanical fit, certification correspondence or purchase availability validated",
    }
