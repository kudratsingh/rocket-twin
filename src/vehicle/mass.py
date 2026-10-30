"""Mass moments: m=Σmᵢ, CG=Σmᵢxᵢ/m, I=Σ(Iᵢ+mᵢdᵢ²).

Reference: Goldstein et al., Classical Mechanics, 3rd ed., ch. 5 (parallel-axis theorem).
Parts have axial stations and optional body y/z offsets. Nose inertia integrates circular shell slices; boxes and
annular cylinders represent other parts. Gimbal envelopes remain estimates until CAD (WO-03).
Uniform motor depletion fixes grain CG; no evolving internal grain shape is modelled.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from src.vehicle.geometry import shape_properties
from src.vehicle.schema import Vehicle


@dataclass(frozen=True)
class MassProperties:
    mass_kg: float
    cg_m: float
    inertia_kg_m2: NDArray[np.float64]
    budget_kg: dict[str, float]
    cg_lateral_m: tuple[float, float] = (0.0, 0.0)


def mass_properties(vehicle: Vehicle, burn_fraction: float = 0) -> MassProperties:
    if not 0 <= burn_fraction <= 1:
        raise ValueError("burn_fraction must be within [0, 1]")
    budget = {p.id: p.resolved_mass_kg for p in vehicle.parts}
    if vehicle.motor:
        for p in vehicle.parts:
            if p.type == "motor":
                budget[p.id] -= vehicle.motor.propellant_mass_kg * burn_fraction
    total = sum(budget.values())
    cg = sum(budget[p.id] * p.cg_station_m for p in vehicle.parts) / total
    lateral = tuple(
        sum(budget[p.id] * p.lateral_offset_m[i] for p in vehicle.parts) / total for i in (0, 1)
    )
    inertia = np.zeros((3, 3))
    for p in vehicle.parts:
        m, g = budget[p.id], p.geometry
        local = shape_properties(p.type, g).inertia_per_kg_m2 * m
        # Body +x points noseward, opposite the positive-aft station coordinate.
        displacement = np.array(
            [
                cg - p.cg_station_m,
                p.lateral_offset_m[0] - lateral[0],
                p.lateral_offset_m[1] - lateral[1],
            ]
        )
        inertia += local + m * (
            np.dot(displacement, displacement) * np.eye(3) - np.outer(displacement, displacement)
        )
    return MassProperties(total, cg, inertia, budget, (lateral[0], lateral[1]))
