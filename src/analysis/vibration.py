"""Spec-bound preliminary body/gimbal/sensor vibration and fin-flutter screens.

Body: Euler-Bernoulli free-free beam reduction with actual CAD tube area/polar
inertia, distributed tube mass and lumped component mass/rotary inertia. Joint
stiffness and temperature are explicit uncertain reductions, not identified data.
Gimbal: gross drive-neck cantilever stiffness and CAD moving-group pivot inertia;
backlash/bearing/servo compliance and coupling remain separate open conclusions.
Flutter: Martin NACA TN4197 (1958), Eqs12/18; coefficient=(24*.25/pi)*1.4*p0 in SI.
Rectangular-section Saint-Venant J approximation (Roark, torsion of thin rectangles)
sets GE=6GJ/(ct^3), not an unexplained unit conversion. The source assumes constant
thickness ratio; this rocket's constant-thickness tapered fins violate that premise.
Results are screening sensitivities and cannot qualify stall/body/control flutter.
"""

from __future__ import annotations

from itertools import pairwise, product
from typing import Any

import numpy as np
from scipy.linalg import eigh

from src.analysis.beam_modes import PointMass, assemble_free_free_beam
from src.vehicle.mass import mass_properties
from src.vehicle.schema import Vehicle


def body_modes(
    vehicle: Vehicle,
    cfg: dict[str, Any],
    elements: int,
    stiffness_fraction: float,
    joint_fraction: float,
) -> dict[str, Any]:
    start = vehicle.airframe["nose"]["length_m"]
    end = vehicle.airframe["length_m"]
    tubes = [
        p
        for p in vehicle.parts
        if p.type == "body_tube" and p.cad_mass and "inner_radius_m" in p.geometry
    ]
    points = list(np.linspace(start, end, elements + 1))
    for p in tubes:
        points.extend([p.position_m, p.position_m + p.geometry["length_m"]])
    joint = next(p.position_m for p in vehicle.parts if p.id == "joint_stop")
    zone = cfg["vibration"]["joint_zone_half_length_m"]
    points.extend([joint - zone, joint + zone])
    x = np.array(sorted({max(start, min(end, float(v))) for v in points}))
    # Eliminate floating duplicate boundaries at adjacent parts.
    x = x[np.r_[True, np.diff(x) > 1e-9]]
    ei = np.zeros(len(x) - 1)
    mu = np.zeros(len(x) - 1)
    for i, (left, right) in enumerate(pairwise(x)):
        mid = (left + right) / 2
        for p in tubes:
            length = p.geometry["length_m"]
            if p.position_m - 1e-10 <= mid <= p.position_m + length + 1e-10:
                assert p.cad_mass
                xi = (mid - p.position_m) / length
                # Match the CAD axial centroid with a positive linear line-mass profile.
                a = 6 * ((p.cg_station_m - p.position_m) / length - 0.5)
                if abs(a) >= 1:
                    raise ValueError("Tube centroid cannot use positive linear mass profile")
                mu[i] += p.resolved_mass_kg / length * (1 + a * (2 * xi - 1))
                area = p.cad_mass.volume_m3 / length
                iy = 0.5 * area * p.cad_mass.inertia_per_kg_m2[0][0]
                ei[i] += cfg["materials"][p.material]["youngs_pa"] * iy * stiffness_fraction
        if abs(mid - joint) < zone:
            ei[i] *= joint_fraction
    tube_ids = {p.id for p in tubes}
    masses = []
    overhang = []
    for p in vehicle.parts:
        if p.id in tube_ids:
            continue
        station = max(start, min(end, p.cg_station_m))
        inertia = float(p.inertia_per_kg_m2[1, 1]) * p.resolved_mass_kg
        masses.append(PointMass(station, p.resolved_mass_kg, inertia))
        if station != p.cg_station_m:
            overhang.append((station, p.cg_station_m - station, p.resolved_mass_kg))
    k, m = assemble_free_free_beam(x.tolist(), ei.tolist(), mu.tolist(), masses)
    for station, lever, mass in overhang:
        node = 0 if station == start else len(x) - 1
        m[2 * node, 2 * node + 1] += mass * lever
        m[2 * node + 1, 2 * node] += mass * lever
        m[2 * node + 1, 2 * node + 1] += mass * lever**2
    values, vectors = eigh(k, m)
    if values[2] <= 0 or max(abs(values[:2])) > values[2] * 1e-3:
        raise ValueError("Unexpected rigid modes")
    frequency = np.sqrt(values[2:8]) / (2 * np.pi)
    translation = np.tile([1.0, 0.0], len(x))
    rotation = np.column_stack((x, np.ones(len(x)))).ravel()
    total = float(translation @ m @ translation)
    cg = float(translation @ m @ rotation / total)
    actual = mass_properties(vehicle)
    shapes = vectors[:, 2:8]
    norm = np.max(np.abs(shapes[::2]), axis=0)
    display = shapes[::2] / norm
    return {
        "elements": len(x) - 1,
        "requested_elements": elements,
        "stiffness_fraction": stiffness_fraction,
        "joint_stiffness_fraction": joint_fraction,
        "frequencies_hz": frequency.tolist(),
        "stations_m": x.tolist(),
        "normalized_transverse_shapes": display.T.tolist(),
        "modal_mass_kg": total,
        "cad_mass_kg": actual.mass_kg,
        "mass_error_kg": total - actual.mass_kg,
        "modal_rigid_cg_station_m": cg,
        "cad_cg_station_m": actual.cg_m,
        "cg_reduction_error_m": cg - actual.cg_m,
        "rigid_eigenvalues": values[:2].tolist(),
        "validity": "Free-flight 1D bending reduction, averaged tube section stiffness; bonded parallel sections and uncertain joint reduction. No torsion, guide-contact, local bearing, aeroelastic or closed-loop qualification.",
    }


def flutter_screen(vehicle: Vehicle, cfg: dict[str, Any]) -> dict[str, Any]:
    fin = next((p for p in vehicle.parts if p.type == "fin_set"), None)
    if not fin:
        return {
            "applicable": False,
            "reason": "Actual configuration has no physical fins; body/control stability remains separate.",
        }
    g = fin.geometry
    vib = cfg["vibration"]
    root = g["root_chord_m"]
    tip = g["tip_chord_m"]
    span = g["span_m"]
    t = g["thickness_m"]
    mid = (root + tip) / 2
    quarter75 = root + 0.75 * (tip - root)
    aspect = span / mid
    taper = tip / root
    # Flat rectangular section, not the source's assumed thin airfoil J_s=ct^3/6.
    j = quarter75 * t**3 * (1 / 3 - 0.21 * t / quarter75 * (1 - t**4 / (12 * quarter75**4)))
    coefficient = 24 * 0.25 / np.pi * 1.4 * 101325
    rows = []
    for shear, hot, pressure, temperature, chord in product(
        vib["shear_modulus_pa"],
        vib["youngs_fraction"],
        vib["pressure_ratio"],
        vib["air_temperature_k"],
        [root, mid],
    ):
        ge = 6 * shear * hot * j / (quarter75 * t**3)
        denominator = (
            coefficient * aspect**3 / ((t / chord) ** 3 * (aspect + 2)) * (taper + 1) / 2 * pressure
        )
        speed = float(np.sqrt(1.4 * 287.05287 * temperature) * np.sqrt(ge / denominator))
        rows.append(
            {
                "shear_pa": shear,
                "stiffness_fraction": hot,
                "pressure_ratio": pressure,
                "air_temperature_k": temperature,
                "thickness_ratio_chord_m": chord,
                "equivalent_GE_pa": ge,
                "screen_speed_mps": speed,
                "ratio_to_speed_bound": speed / vib["speed_envelope_mps"],
            }
        )
    return {
        "applicable": True,
        "source": "https://ntrs.nasa.gov/api/citations/19930085030/downloads/19930085030.pdf Eq12/18",
        "geometry": g,
        "panel_aspect_ratio": aspect,
        "flat_plate_torsion_J_m4": j,
        "coefficient_pa": coefficient,
        "speed_envelope_mps": vib["speed_envelope_mps"],
        "speed_envelope_basis": vib["speed_envelope_basis"],
        "scenarios": rows,
        "screen_speed_range_mps": [
            min(r["screen_speed_mps"] for r in rows),
            max(r["screen_speed_mps"] for r in rows),
        ],
        "minimum_speed_ratio": min(r["ratio_to_speed_bound"] for r in rows),
        "quantitative_flutter_acceptance_passed": False,
        "validity_failures": [
            "Constant thickness tapered plate does not have the source constant thickness ratio.",
            "Effective installed torsion/root stiffness is unmeasured; homogeneous rectangular-section approximation only.",
            "No stall, body-pitch/fin-bending, gimbal/control or local panel coupling model is qualified.",
            "Current reconciled flight envelopes and damping/excitation measurements remain required.",
        ],
    }


def gimbal_sensor_screen(vehicle: Vehicle, cfg: dict[str, Any]) -> dict[str, Any]:
    vib = cfg["vibration"]
    parts = {p.id: p for p in vehicle.parts}
    out: dict[str, Any] = {
        "servo_model_bandwidth_hz": vib["servo_model_omega_rad_s"] / (2 * np.pi),
        "propulsion_excitation_band_hz": vib["propulsion_excitation_band_hz"],
        "propulsion_spectrum_basis": vib["propulsion_spectrum_basis"],
        "damping_ratio": vib["damping_ratio"],
        "sensor_mount_modes": [],
        "gimbal_modes": [],
        "physical_validation": False,
    }
    for name in ["imu", "high_g_accel"]:
        if name in parts:
            out["sensor_mount_modes"].append(
                {
                    "part_id": name,
                    "mass_kg": parts[name].resolved_mass_kg,
                    "frequency_range_hz": [
                        float(np.sqrt(k / parts[name].resolved_mass_kg) / (2 * np.pi))
                        for k in vib["sensor_mount_stiffness_n_m"]
                    ],
                    "basis": vib["sensor_mount_stiffness_basis"],
                    "aliasing_clearance": "Unresolved until mount, bandwidth/filter and sample timing are measured.",
                }
            )
    if vehicle.tvc:
        pivot = vehicle.tvc.pivot_position_m
        moving = [p for p in vehicle.parts if p.cad and p.cad.moving_group in ("motor", "yaw")]
        for id, axis in [("tvc_gimbal", 2), ("gimbal_inner", 1)]:
            p = parts[id]
            assert p.cad
            bridge = p.cad.parameters["bridge"]
            a, b, length = np.array(bridge["size_mm"]) * 0.001
            drive = np.array(p.cad.parameters["lug_center_mm"][:2]) * 0.001
            arm = abs(drive[0] if id == "tvc_gimbal" else drive[1])
            inertia = sum(
                q.resolved_mass_kg
                * (
                    q.inertia_per_kg_m2[axis, axis]
                    + (q.cg_station_m - pivot) ** 2
                    + sum(v * v for v in q.cg_lateral_m)
                )
                for q in moving
                if id == "tvc_gimbal" or (q.cad and q.cad.moving_group == "motor")
            )
            weak_i = max(a, b) * min(a, b) ** 3 / 12
            young = cfg["materials"][p.material]["youngs_pa"]
            gross_stiffness = 3 * young * weak_i / length**3 * arm**2
            out["gimbal_modes"].append(
                {
                    "part_id": id,
                    "pivot_inertia_kg_m2": float(inertia),
                    "gross_neck_stiffness_nm_rad": float(gross_stiffness),
                    "gross_frequency_cold_hz": float(
                        np.sqrt(gross_stiffness / inertia) / (2 * np.pi)
                    ),
                    "gross_frequency_half_E_hz": float(
                        np.sqrt(0.5 * gross_stiffness / inertia) / (2 * np.pi)
                    ),
                    "validity": "Gross-neck stiffness upper screen; bore ligaments, pin/backlash, rod/shaft/servo compliance omitted. Not an independent loaded-actuator resonance prediction.",
                }
            )
    return out
