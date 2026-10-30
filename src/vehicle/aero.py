"""Small-angle, subsonic Barrowman normal force buildup.

Reference: J. S. Barrowman, NASA/TM-2001-209983 (1967 thesis), slender finned
vehicles. Ogive CP uses L-V/A_base; cylinder normal-force slope is zero. A transition
uses CNa=2(r₂²-r₁²)/R² and CP=L/3*(1+(1-r₁/r₂)/(1-(r₁/r₂)²)).
Fin CP and interference use the trapezoidal-fin Barrowman approximation.
No body lift, viscous correction, supersonic or unsteady effects. Cd tables are
engineering estimates; later replace behind sim.aero.AeroModel (EXTENSIONS.md).
"""

from math import sqrt

import numpy as np

from src.vehicle.geometry import nose_cp_offset
from src.vehicle.schema import Vehicle


def fin_geometries(vehicle: Vehicle) -> list[dict[str, float]]:
    """Physical fin sets; legacy aero-only stubs retained for old sensitivity runs."""
    sets = [
        {**p.geometry, "position_m": p.position_m} for p in vehicle.parts if p.type == "fin_set"
    ]
    if vehicle.aero.passive_stubs.enabled:
        sets.append(vehicle.aero.passive_stubs.model_dump())
    return sets


def normal_force_surfaces(vehicle: Vehicle) -> list[tuple[float, float]]:
    radius = vehicle.airframe["body_diameter_m"] / 2
    forces: list[tuple[float, float]] = []
    for part in vehicle.parts:
        g = part.geometry
        if part.type == "nose_cone":
            forces.append(
                (
                    2 * (g["radius_m"] / radius) ** 2,
                    part.position_m + nose_cp_offset(g["length_m"], g["radius_m"], g["shape"]),
                )
            )
        elif part.type == "transition":
            r1, r2, length = g["fore_radius_m"], g["radius_m"], g["length_m"]
            if r1 != r2:
                slope = 2 * (r2 * r2 - r1 * r1) / radius**2
                cp = length / 3 * (1 + r2 / (r1 + r2))
                forces.append((slope, part.position_m + cp))
    for stubs in fin_geometries(vehicle):
        span, root, tip, sweep = (
            stubs[k] for k in ["span_m", "root_chord_m", "tip_chord_m", "sweep_m"]
        )
        mid = sqrt(span**2 + (sweep + (tip - root) / 2) ** 2)
        slope = (1 + radius / (radius + span)) * 4 * stubs["count"] * (span / (2 * radius)) ** 2
        slope /= 1 + sqrt(1 + (2 * mid / (root + tip)) ** 2)
        cp = sweep / 3 * (root + 2 * tip) / (root + tip)
        cp += (root + tip - root * tip / (root + tip)) / 6
        forces.append((slope, stubs["position_m"] + cp))
    return forces


def center_of_pressure(vehicle: Vehicle) -> float:
    forces = normal_force_surfaces(vehicle)
    denominator = sum(s for s, _ in forces)
    if abs(denominator) < 1e-12:
        raise ValueError("CP undefined for zero normal-force slope")
    return sum(s * x for s, x in forces) / denominator


def drag_coefficient(vehicle: Vehicle, mach: float, powered: bool = False) -> float:
    if not 0 <= mach <= 0.8:
        raise ValueError("WO-01 drag estimate supports Mach 0–0.8 only")
    model = vehicle.aero.cd_model.model_dump()
    cd = float(np.interp(mach, model["mach"], model["cd"]))
    return cd + (0 if powered else float(model["base_drag_cd"]))
