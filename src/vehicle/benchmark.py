"""WO-01 preliminary design screens, distinct from flight authorization.

Rail: m*x_ddot = T(t) - m*g - friction - rho*Cd*A*v^2/2,
fixed worst-case mass, vertical guide, no wind force or mass-loss credit.
Reference: Newton's second law; Sutton & Biblarz, Rocket Propulsion Elements,
9th ed., ch. 4. This short guide-only integration is not a free-flight simulator.
Useful control time: longest contiguous post-guide interval with T >= k*m*g.
It is an authority-duration proxy, not a closed-loop stability/torque validation.
Recovery area uses steady terminal force balance mg=rho*Cd*A*v^2/2.
All thresholds are explicit provisional design requirements in each spec.
"""

from __future__ import annotations

import hashlib
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from src.sim.frames import STANDARD_GRAVITY_M_S2 as G
from src.vehicle.aero import center_of_pressure
from src.vehicle.mass import mass_properties
from src.vehicle.motors import load_rasp
from src.vehicle.schema import Vehicle


def screen_launch(vehicle: Vehicle, dt: float = 0.001) -> dict[str, Any]:
    if not np.isfinite(dt) or not 0 < dt <= 0.01:
        raise ValueError("rail screen timestep must be finite and in (0, 0.01]")
    if vehicle.design is None or vehicle.motor is None or not vehicle.motor.curve:
        raise ValueError("screen requires a design profile and source curve")
    d = vehicle.design
    curve = load_rasp(vehicle.motor.curve)
    mass = mass_properties(vehicle).mass_kg + d.mass_allowance_kg
    area = np.pi * (vehicle.airframe["body_diameter_m"] / 2) ** 2
    x = v = 0.0
    exit_time = exit_speed = None
    # Rail-only screening stops at departure; it predicts no apogee or trajectory.
    for t in np.arange(0, curve.burn_time_s, dt):
        thrust = curve.thrust_n(float(t + dt / 2)) * d.thrust_scale_lower
        drag = 0.5 * 1.225 * d.drag_coefficient_upper * area * v * v
        acceleration = (thrust - mass * G - d.rail_friction_n - drag) / mass
        new_v = max(0.0, v + acceleration * dt)
        new_x = x + (v + new_v) * dt / 2
        if new_x >= d.rail_length_m:
            fraction = (d.rail_length_m - x) / (new_x - x)
            exit_time = float(t + fraction * dt)
            exit_speed = float(v + fraction * (new_v - v))
            break
        x, v = new_x, new_v
    # Integrate durations at curve breakpoints, inserting exact threshold crossings.
    threshold = d.control_thrust_to_weight * mass * G / d.thrust_scale_lower
    start = max(exit_time or curve.burn_time_s, 0.0)
    points = sorted(
        {start, curve.burn_time_s, *[float(t) for t in curve.samples[:, 0] if t > start]}
    )
    durations: list[float] = []
    current = 0.0
    for a, b in pairwise(points):
        ta, tb = curve.thrust_n(a), curve.thrust_n(b)
        if ta >= threshold and tb >= threshold:
            current += b - a
        elif ta < threshold and tb < threshold:
            durations.append(current)
            current = 0.0
        else:
            crossing = a + (threshold - ta) * (b - a) / (tb - ta)
            if ta >= threshold:
                current += crossing - a
                durations.append(current)
                current = 0.0
            else:
                durations.append(current)
                current = b - crossing
    durations.append(current)
    return {
        "worst_case_mass_kg": mass,
        "rail_exit_time_s": exit_time,
        "rail_exit_speed_mps": exit_speed,
        "rail_screen_pass": exit_speed is not None and exit_speed >= d.minimum_rail_exit_mps,
        "longest_useful_control_interval_s": max(durations),
        "control_time_screen_pass": max(durations) >= d.minimum_control_time_s,
        "control_time_target_met": max(durations) >= d.target_control_time_s,
        "control_threshold_source_thrust_n": threshold,
        "screening_wind_mps": d.screening_wind_mps,
        "kinematic_crosswind_angle_rad": (
            None if not exit_speed else float(np.arctan(d.screening_wind_mps / exit_speed))
        ),
        "assumptions": "constant loaded mass plus allowance; 0.85 thrust (spec value); vertical guide; drag/friction estimates; no free flight, crosswind load or servo model",
    }


def evaluate_preliminary(vehicle: Vehicle, compare: bool = False) -> dict[str, Any]:
    if vehicle.design is None or vehicle.motor is None or not vehicle.motor.curve:
        raise ValueError("rebaselined benchmark requires an explicit mode and curve")
    curve_path = Path(vehicle.motor.curve)
    meta = yaml.safe_load(curve_path.with_suffix(".yaml").read_text())
    curve = load_rasp(curve_path)
    props = [mass_properties(vehicle, f) for f in (0, 1)]
    cp = center_of_pressure(vehicle)
    d = vehicle.design
    # Place all uncertain additional mass at the aft end for conservative CG.
    margins = [
        (
            cp
            - (p.mass_kg * p.cg_m + d.mass_allowance_kg * vehicle.airframe["length_m"])
            / (p.mass_kg + d.mass_allowance_kg)
        )
        / vehicle.airframe["body_diameter_m"]
        for p in props
    ]
    summary = {
        "loaded_mass_kg": curve.loaded_mass_kg,
        "propellant_mass_kg": curve.propellant_mass_kg,
        "length_m": curve.length_m,
        "diameter_m": curve.diameter_m,
        "total_impulse_ns": curve.total_impulse_ns,
        "average_thrust_n": curve.average_thrust_n,
        "burn_time_s": curve.burn_time_s,
    }
    source_ok = (
        hashlib.sha256(curve_path.read_bytes()).hexdigest() == meta.get("sha256")
        and bool(meta.get("source_url"))
        and meta.get("review_status") == "preliminary_numerical_hypothesis"
        and all(
            np.isclose(value, meta.get(key, float("nan")), rtol=1e-9)
            for key, value in summary.items()
        )
    )
    motor_part = next(p for p in vehicle.parts if p.type == "motor")
    configured_ok = np.allclose(
        [
            vehicle.motor.propellant_mass_kg,
            motor_part.resolved_mass_kg,
            motor_part.geometry["length_m"],
            motor_part.geometry["radius_m"] * 2,
            vehicle.motor.burn_time_s,
            vehicle.motor.total_impulse_ns,
            vehicle.motor.average_thrust_n,
        ],
        [
            curve.propellant_mass_kg,
            curve.loaded_mass_kg,
            curve.length_m,
            curve.diameter_m,
            curve.burn_time_s,
            curve.total_impulse_ns,
            curve.average_thrust_n,
        ],
        rtol=1e-9,
    )
    launch = screen_launch(vehicle)
    reference = None
    if compare:
        from src.vehicle.reference import compare_rocketpy

        reference = compare_rocketpy(vehicle)
    checks = {
        "spec_valid": True,
        "mass_with_growth_below_1p5kg": launch["worst_case_mass_kg"] < 1.5,
        "single_G_scope_evidence_declared": vehicle.motor.qualification is not None
        and curve.total_impulse_ns <= 160,
        "source_traceable_and_config_consistent": bool(source_ok and configured_ok),
        "all_parts_have_build_and_cost": all(p.build is not None for p in vehicle.parts),
        "rail_departure_screen": launch["rail_screen_pass"],
        "mode_static_margin_screen": d.minimum_static_margin_cal is None
        or min(margins) >= d.minimum_static_margin_cal,
        "mode_useful_control_time_screen": launch["control_time_screen_pass"],
        "independent_static_reference": bool(reference and reference["passed"]),
    }
    return {
        "vehicle": vehicle.id,
        "mode": d.mode,
        "checks": checks,
        "preliminary_design_benchmark_passed": all(checks.values()),
        "flight_ready": False,
        "validation_scope": "WO-01 source-consistent preliminary numerical model only; not structural, thermal, flight, control or launch approval",
        "nominal_mass_kg": props[0].mass_kg,
        "burnout_mass_kg": props[1].mass_kg,
        "cg_liftoff_m": props[0].cg_m,
        "cg_burnout_m": props[1].cg_m,
        "cg_lateral_liftoff_m": props[0].cg_lateral_m,
        "cg_lateral_burnout_m": props[1].cg_lateral_m,
        "inertia_liftoff_kg_m2": props[0].inertia_kg_m2.tolist(),
        "inertia_burnout_kg_m2": props[1].inertia_kg_m2.tolist(),
        "cp_m": cp,
        "static_margins_with_aft_mass_allowance_cal": margins,
        "average_TWR_diagnostic_only": curve.average_thrust_n / (props[0].mass_kg * G),
        "source_terminal_time_s": curve.burn_time_s,
        "launch_screen": launch,
        "reference_comparison": reference,
        "parts_budget_kg": props[0].budget_kg,
        "parts_cost_estimate_usd": sum(p.build.cost_usd for p in vehicle.parts if p.build),
        "recovery_area_for_6mps_m2": 2 * launch["worst_case_mass_kg"] * G / (1.1 * 0.75 * 6**2),
        "source_assumptions": meta,
        "later_required_gates": [
            "exact sold motor/source/envelope and California approval",
            "WO-02 rail/trajectory/recovery and crosswind validation",
            "WO-03 CAD, measured masses, proof loads and temperatures",
            "WO-06/07 realistic PID and RL validation",
            "WO-09/10 independent recovery, abort and HIL",
            "WO-11 club approval and staged flight evidence; finless burnout-to-recovery qualification",
        ],
    }
