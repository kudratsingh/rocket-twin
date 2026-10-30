"""Conservative finite-volume radial conduction and opaque-gap heat exchange.

For an annular wall R=ln(ro/ri)/(2*pi*k*L); cell capacities are exact annular
volumes times volumetric heat capacity. Logarithmic cell centres preserve the
steady cylindrical solution. Internal exchanges enter the two nodes with opposite
sign. Grey diffuse concentric-surface radiation uses reciprocal areas; solid half
walls remain in series with the gap instead of radiating through an opaque wall.
References: DOE-HDBK-1012/2-92, HT-02 pp.11-13 (cylindrical composite walls),
https://www.energy.gov/documents/doe-hdbk-1012-92vol2 ; COMSOL surface-to-surface
radiation theory/view factors, https://doc.comsol.com/6.3/doc/com.comsol.help.heat/heat_ug_theory.07.053.html .
A 1D wall/gap reduction does not resolve finite-end view factors or moving 3D parts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import brentq

SIGMA = 5.670374419e-8


@dataclass(frozen=True)
class RadialWall:
    faces_m: Any
    centres_m: Any
    capacities_j_k: Any
    internal_conductance_w_k: Any
    inner_half_resistance_k_w: float
    outer_half_resistance_k_w: float


def annular_wall(
    inner_radius_m: float,
    outer_radius_m: float,
    length_m: float,
    conductivity_w_m_k: float,
    heat_capacity_j_k: float,
    cells: int,
) -> RadialWall:
    """Discretize a homogeneous wall using its actual whole-part heat capacity."""
    if not (
        0 < inner_radius_m < outer_radius_m
        and length_m > 0
        and conductivity_w_m_k > 0
        and heat_capacity_j_k > 0
        and cells >= 1
    ):
        raise ValueError("Positive ordered wall geometry, properties and cell count required")
    faces = np.linspace(inner_radius_m, outer_radius_m, cells + 1)
    centres = np.sqrt(faces[:-1] * faces[1:])
    volume_weights = np.diff(faces**2) / (outer_radius_m**2 - inner_radius_m**2)
    factor = 2 * np.pi * conductivity_w_m_k * length_m
    return RadialWall(
        faces,
        centres,
        volume_weights * heat_capacity_j_k,
        factor / np.log(centres[1:] / centres[:-1]),
        float(np.log(centres[0] / inner_radius_m) / factor),
        float(np.log(outer_radius_m / centres[-1]) / factor),
    )


def wall_heat_rates(wall: RadialWall, temperature_k: Any) -> Any:
    """Internal cell heat rates in watts; their sum is identically zero."""
    temperatures = np.asarray(temperature_k, dtype=float)
    if temperatures.shape != wall.centres_m.shape:
        raise ValueError("Wall temperatures must cover exactly its cells")
    heat = np.zeros_like(temperatures)
    flow = wall.internal_conductance_w_k * np.diff(temperatures)
    heat[:-1] += flow
    heat[1:] -= flow
    return heat


def opaque_gap_flux(
    inner_node_k: float,
    outer_node_k: float,
    inner_half_resistance_k_w: float,
    outer_half_resistance_k_w: float,
    inner_surface_radius_m: float,
    outer_surface_radius_m: float,
    length_m: float,
    air_conductivity_w_m_k: float,
    emissivity: float,
) -> float:
    """W positive radially outward; surface temperatures solved behind half walls.

    This is a coaxial, closed long-cylinder approximation (F_inner_to_outer=1).
    Exact radius reciprocity applies within that reduction. It is not a ray-traced
    view factor of the rocket. No exchange path bypasses either opaque half wall.
    """
    if not (
        0 < inner_surface_radius_m < outer_surface_radius_m
        and length_m > 0
        and air_conductivity_w_m_k >= 0
        and 0 < emissivity <= 1
        and inner_half_resistance_k_w >= 0
        and outer_half_resistance_k_w >= 0
        and min(inner_node_k, outer_node_k) > 0
    ):
        raise ValueError("Invalid absolute temperatures or gap geometry/properties")
    area = 2 * np.pi * inner_surface_radius_m * length_m
    conduction = (
        2
        * np.pi
        * air_conductivity_w_m_k
        * length_m
        / np.log(outer_surface_radius_m / inner_surface_radius_m)
    )
    radiation = (
        SIGMA
        * area
        / (1 / emissivity + inner_surface_radius_m / outer_surface_radius_m * (1 / emissivity - 1))
    )

    def flux_at(q: float) -> float:
        a = inner_node_k - q * inner_half_resistance_k_w
        b = outer_node_k + q * outer_half_resistance_k_w
        return float(conduction * (a - b) + radiation * (a**4 - b**4) - q)

    resistance = inner_half_resistance_k_w + outer_half_resistance_k_w
    difference = inner_node_k - outer_node_k
    if difference == 0:
        return 0.0
    if resistance == 0:
        return flux_at(0)
    bound = difference / resistance
    return float(brentq(flux_at, min(0.0, bound), max(0.0, bound), xtol=1e-11))


def known_cases() -> dict[str, Any]:
    """Executed independent cylindrical steady solution and two-capacity transient."""
    from scipy.integrate import solve_ivp

    levels = []
    # Independently use the continuum logarithmic solution, not a second copy of
    # the assembled finite-volume linear system, for temperatures and heat rate.
    for cells in [4, 8, 16]:
        wall = annular_wall(0.01, 0.02, 0.1, 0.2, 10.0, cells)
        matrix = np.zeros((cells, cells))
        forcing = np.zeros(cells)
        for i, conductance in enumerate(wall.internal_conductance_w_k):
            matrix[i, i] += conductance
            matrix[i + 1, i + 1] += conductance
            matrix[i, i + 1] -= conductance
            matrix[i + 1, i] -= conductance
        gi, go = 1 / wall.inner_half_resistance_k_w, 1 / wall.outer_half_resistance_k_w
        matrix[0, 0] += gi
        matrix[-1, -1] += go
        forcing[0], forcing[-1] = gi * 400, go * 300
        values = np.linalg.solve(matrix, forcing)
        expected = 400 - 100 * np.log(wall.centres_m / 0.01) / np.log(2)
        expected_q = 2 * np.pi * 0.2 * 0.1 * 100 / np.log(2)
        heat = gi * (400 - values[0])
        levels.append(
            {
                "cells": cells,
                "max_temperature_error_k": float(np.max(np.abs(values - expected))),
                "relative_heat_rate_error": abs(float(heat / expected_q - 1)),
            }
        )
    c1, c2, conductance = 2.0, 5.0, 0.3
    times = np.linspace(0, 100, 101)

    def rhs(t: float, y: Any) -> Any:
        q = conductance * (y[1] - y[0])
        return np.array([q / c1, -q / c2])

    result = solve_ivp(rhs, (0, 100), [400, 300], t_eval=times, rtol=1e-10, atol=1e-10)
    equilibrium = (c1 * 400 + c2 * 300) / (c1 + c2)
    difference = 100 * np.exp(-conductance * (1 / c1 + 1 / c2) * times)
    expected = np.array(
        [
            equilibrium + c2 / (c1 + c2) * difference,
            equilibrium - c1 / (c1 + c2) * difference,
        ]
    )
    transient_error = float(np.max(np.abs(result.y - expected)))
    energy_error = float(np.max(np.abs(np.array([c1, c2]) @ result.y - 2300)))
    return {
        "cylindrical_steady_levels": levels,
        "two_capacity_transient_max_error_k": transient_error,
        "two_capacity_energy_error_j": energy_error,
        "passed": all(
            level["max_temperature_error_k"] < 1e-8 and level["relative_heat_rate_error"] < 1e-9
            for level in levels
        )
        and transient_error < 1e-6
        and energy_error < 1e-8,
        "scope": "Numerical verification of reductions only; not rocket temperature validation.",
    }
