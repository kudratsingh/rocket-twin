"""Preliminary load-path calculations and bounded transient thermal network.

Loads: Newton force balance, cantilever beam bending/deflection, Euler buckling,
and energy-based recovery stopping load (Roark/Shigley; USDA Wood Handbook ch.9).
Thermal: C*dT/dt=sum(G*(Tj-Ti))+radiation+power (Incropera heat-transfer network).
Gaps use cylindrical conduction; radiation is exact grey-body T^4 with an explicit
view-area approximation. External motor-case temperature is a prescribed bounded
scenario, not a measured history or an internal motor combustion calculation.
Material bounds and contact/BC uncertainty live in the engineering YAML. This
screen identifies design failures; it does not qualify strength, heat or recovery.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

from src.vehicle.mass import mass_properties
from src.vehicle.motors import load_rasp
from src.vehicle.schema import Part, Vehicle


def material_profile(part: Part) -> str:
    return part.engineering.material_profile if part.engineering else part.material


def structural(vehicle: Vehicle, cfg: dict[str, Any]) -> dict[str, Any]:
    assert vehicle.motor and vehicle.motor.curve and vehicle.design
    parts = {p.id: p for p in vehicle.parts}
    m = mass_properties(vehicle)
    allowance = vehicle.design.mass_allowance_kg
    curve = load_rasp(vehicle.motor.curve)
    loads = cfg["loads"]
    factor = float(loads["design_factor"])
    peak = float(curve.samples[:, 1].max()) * loads["thrust_multiplier"]
    acceleration = peak / m.mass_kg
    rows = []

    def row(id: str, case: str, stress: float, detail: dict[str, Any]) -> None:
        part = parts[id]
        material = cfg["materials"].get(part.material, {})
        strength = float(material.get("strength_pa", 0))
        margin = strength / (factor * stress) - 1 if stress > 0 and strength > 0 else None
        rows.append(
            {
                "part_id": id,
                "case": case,
                "stress_pa": stress,
                "strength_bound_pa": strength or None,
                "design_factor": factor,
                "margin": margin,
                "evidence": "calculated using estimated properties",
                "passed": bool(margin is not None and margin >= 0),
                **detail,
            }
        )

    mount = parts["motor_mount"]
    g = mount.geometry
    o = mount.cad.parameters if mount.cad else {}
    # Cut across the actual longitudinal rails; do not assign a full annular-tube area.
    area = (
        3 * 2 * 4 * 1e-6
        if o.get("tie_rails")
        else 3 * o.get("rail_width_mm", 6) * o.get("rail_depth_mm", 3) * 1e-6
    )
    rail_length = g["length_m"]
    dim = (
        np.array([2, 4]) * 1e-3
        if o.get("tie_rails")
        else np.array([o.get("rail_width_mm", 6), o.get("rail_depth_mm", 3)]) * 1e-3
    )
    young = float(cfg["materials"].get(mount.material, {}).get("youngs_pa", 1e9))
    buckling = 3 * np.pi**2 * young * float(np.max(dim) * np.min(dim) ** 3 / 12) / rail_length**2
    row(
        "motor_mount",
        "motor_thrust",
        peak / area,
        {
            "axial_force_n": peak,
            "rail_area_m2": area,
            "elastic_shortening_m": peak * rail_length / (area * young),
            "pinned_rail_euler_load_n": buckling,
            "buckling_margin": buckling / (factor * peak) - 1,
            "boundary": "Three rails share thrust; pinned unsupported length is conservative. Slot notches and real end restraint require FEA.",
        },
    )
    for p in vehicle.parts:
        if p.type == "fin_set":
            g = p.geometry
            span = g["span_m"]
            root = g["root_chord_m"]
            tip = g["tip_chord_m"]
            thickness = g["thickness_m"]
            area = span * (root + tip) / 2
            ar = 2 * span**2 / area
            slope = 2 * np.pi * ar / (2 + np.sqrt(4 + ar**2))
            force = (
                loads["fin_dynamic_pressure_pa"] * area * slope * np.deg2rad(loads["fin_alpha_deg"])
            )
            # Trapezoid area centroid along the span under uniform pressure.
            arm = span * (root + 2 * tip) / (3 * (root + tip))
            moment = force * arm
            young = cfg["materials"][p.material]["youngs_pa"]
            inertia = root * thickness**3 / 12
            deflection = force * span**3 / (3 * young * inertia)
            row(
                p.id,
                "fin_bending",
                6 * moment / (root * thickness**2),
                {
                    "force_per_fin_n": force,
                    "root_moment_nm": moment,
                    "tip_deflection_upper_m": deflection,
                    "deflection_limit_m": loads["fin_deflection_limit_m"],
                    "boundary": "Finite-aspect-ratio small-angle panel estimate; load resultant at area centroid. Tip-load deflection upper screen; flutter/large-alpha and root-tab connection need separate validation.",
                },
            )
    recovery = []
    for speed in loads["recovery_velocity_mps"]:
        for travel in loads["recovery_stopping_distance_m"]:
            load = (m.mass_kg + allowance) * (speed**2 / (2 * travel) + 9.80665)
            recovery.append(
                {
                    "opening_speed_mps": speed,
                    "stopping_distance_m": travel,
                    "total_harness_load_n": load,
                    "factored_load_n": factor * load,
                }
            )
    if vehicle.tvc:
        servo = parts[vehicle.tvc.servo_ids[0]]
        assert servo.electrical and servo.electrical.stall_torque_nm
        horn_arm = 0.006
        rod = servo.electrical.stall_torque_nm / horn_arm
        row(
            "tvc_gimbal",
            "gimbal_servo",
            rod / (4e-3 * 4e-3),
            {
                "stall_rod_force_n": rod,
                "boundary": "Axial neck-only stress, excludes drive eccentricity, holes, transverse rod force and print anisotropy. FEA required; this row cannot close the gimbal gate.",
                "conclusion_complete": False,
            },
        )
    return {
        "peak_scaled_thrust_n": peak,
        "peak_liftoff_specific_acceleration_g": acceleration / 9.80665,
        "rows": rows,
        "guide_side_force_n": loads["guide_side_force_n"],
        "recovery_cases": recovery,
        "unclosed_load_paths": [
            "Modular retention fastener/bond geometry and bearing/crush loads",
            "Recovery bulkhead/anchor, harness and local bonds",
            "Guide attachment and local shell reinforcement",
            "Gimbal bearing, clamp/retention and full servo/transverse reactions",
        ],
        "analysis_complete": False,
        "flight_ready": False,
    }


def thermal(
    vehicle: Vehicle,
    cfg: dict[str, Any],
    severe: bool,
    output_dt: float = 1.0,
    max_step_s: float = 2.0,
) -> dict[str, Any]:
    assert vehicle.motor
    burn_time = vehicle.motor.burn_time_s
    parts = {p.id: p for p in vehicle.parts}
    settings = cfg["thermal"]
    j = int(severe)
    ambient = float(settings["ambient_c"][j]) + 273.15
    peak = float(settings["external_case_peak_c"][j]) + 273.15
    tau = float(settings["post_burn_cooling_tau_s"][j])
    kair = settings["air_conductivity_w_m_k"][j]
    h = settings["surface_h_w_m2_k"][1 - j]
    eps = settings["emissivity"][j]
    ids = [
        i
        for i in [
            "motor_liner",
            "motor_mount",
            "gimbal_inner",
            "tvc_gimbal",
            "gimbal_frame",
            "thermal_guard",
            "aft_shell",
            "servo_support",
            "servo_pitch",
            "servo_yaw",
            "fin_bonds",
            "flight_computer",
            "battery",
        ]
        if i in parts
    ]
    index = {name: i for i, name in enumerate(ids)}
    caps = np.array(
        [
            parts[i].resolved_mass_kg
            * cfg["materials"].get(material_profile(parts[i]), cfg["materials"]["commercial"])[
                "cp_j_kg_k"
            ]
            for i in ids
        ]
    )
    edges = []

    def edge(a: str, b: str, g: float) -> None:
        if a in index and b in index:
            edges.append((index[a], index[b], g))

    liner = parts["motor_liner"]
    g = liner.geometry
    case_r = parts["motor"].geometry["radius_m"]
    length = g["length_m"]
    case_conduction = 2 * np.pi * kair * length / np.log(g["inner_radius_m"] / case_r)
    case_area = 2 * np.pi * case_r * length
    mount = parts["motor_mount"]
    mount_length = 0.018 if mount.cad and mount.cad.generator == "cradle" else 0.006
    gap = max(mount.geometry["inner_radius_m"] - g["radius_m"], 0.0001)
    edge("motor_liner", "motor_mount", 2 * np.pi * kair * g["radius_m"] * mount_length / gap)
    contact = settings["contact_conductance_w_k"][j]
    for a, b in [
        ("motor_mount", "gimbal_inner"),
        ("gimbal_inner", "tvc_gimbal"),
        ("tvc_gimbal", "gimbal_frame"),
        ("gimbal_frame", "aft_shell"),
        ("gimbal_frame", "servo_support"),
        ("servo_support", "servo_pitch"),
        ("servo_support", "servo_yaw"),
        ("motor_mount", "aft_shell"),
        ("aft_shell", "fin_bonds"),
    ]:
        edge(a, b, contact)
    edge("aft_shell", "flight_computer", 0.01 if not severe else 0.04)
    edge("flight_computer", "battery", 0.02)
    areas = np.array(
        [
            max(
                0.0005,
                2
                * np.pi
                * parts[i].geometry.get("radius_m", 0.015)
                * parts[i].geometry.get("length_m", parts[i].geometry.get("bbox_m", [0.025])[0]),
            )
            for i in ids
        ]
    )
    exposure = {
        i: 2
        * np.pi
        * parts[i].geometry.get("radius_m", 0.02)
        * min(length, parts[i].geometry.get("length_m", 0.02))
        * 0.25
        for i in ids
        if parts[i].position_m >= 0.6 and i != "motor_liner"
    }

    def boundary(t: float) -> float:
        return (
            peak if t <= burn_time else ambient + (peak - ambient) * np.exp(-(t - burn_time) / tau)
        )

    def rhs(t: float, state: Any) -> Any:
        state = state[: len(ids)]
        q = h * areas * (ambient - state)
        q[index["motor_liner"]] += case_conduction * (
            boundary(t) - state[index["motor_liner"]]
        ) + eps * 5.670374419e-8 * case_area * (boundary(t) ** 4 - state[index["motor_liner"]] ** 4)
        for name, area in exposure.items():
            # Direct view factor 0.25 is an explicit unverified enclosure approximation.
            n = index[name]
            q[n] += eps * 5.670374419e-8 * area * (boundary(t) ** 4 - state[n] ** 4)
        q[index["flight_computer"]] += settings["electronics_heat_w"][j]
        external_sum = float(q.sum())
        for a, b, conductance in edges:
            flux = conductance * (state[b] - state[a])
            q[a] += flux
            q[b] -= flux
        return np.concatenate((q / caps, [external_sum]))

    end = burn_time + settings["soak_s"]
    times = np.arange(0, end, output_dt)
    times = np.append(times, end)
    solution = solve_ivp(
        rhs,
        (0, end),
        np.append(np.full(len(ids), ambient), 0.0),
        t_eval=times,
        rtol=1e-8,
        atol=1e-7,
        max_step=max_step_s,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    values = solution.y[: len(ids)].T
    peaks = []
    stored = (values - ambient) @ caps
    residual = float(np.max(np.abs(stored - solution.y[-1])))
    for name, n in index.items():
        limit = cfg["materials"].get(material_profile(parts[name]), cfg["materials"]["commercial"])[
            "limit_c"
        ]
        temperature = float(values[:, n].max() - 273.15)
        peaks.append(
            {
                "part_id": name,
                "peak_c": temperature,
                "peak_time_s": float(times[np.argmax(values[:, n])]),
                "screen_limit_c": limit,
                "margin_k": limit - temperature,
                "passed": temperature <= limit,
                "evidence": "calculated, estimated properties and case boundary",
            }
        )
    return {
        "energy_residual_j": residual,
        "solver_max_step_s": max_step_s,
        "case": "upper-hot-soak" if severe else "lower-case-scenario",
        "times_s": times.tolist(),
        "part_ids": ids,
        "temperature_k": values.tolist(),
        "external_case_peak_c": peak - 273.15,
        "ambient_c": ambient - 273.15,
        "cooling_tau_s": tau,
        "peaks": peaks,
        "model": "Lumped part means; gap conduction and approximate radiation/contact. No resolved gradients, plume, hot-gas flow or electrical thermal qualification.",
        "case_boundary_basis": settings["case_boundary_basis"],
        "flight_ready": False,
    }
