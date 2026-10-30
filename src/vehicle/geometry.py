"""Coaxial shape integrals for WO-01 mass estimates.

References: Goldstein, Classical Mechanics, ch. 5 (rigid-body inertia);
Barrowman, The Practical Calculation of the Aerodynamic Characteristics of
Slender Finned Vehicles (1967), nose volume identity x_CP=L-V/A_base.

Circular slices give dV=π(ro²-ri²)dx, dIxx/dm=(ro²+ri²)/2,
dIyy/dm=(ro²+ri²)/4+(x-CG)². Gauss-Legendre integration is deterministic.
A nose wall is a radial thickness approximation, not a CAD normal offset.
No print voids, shoulders, ribs or fasteners are inferred from an envelope.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Any

import numpy as np
from numpy.typing import NDArray

_POINTS, _WEIGHTS = np.polynomial.legendre.leggauss(128)


@dataclass(frozen=True)
class ShapeProperties:
    volume_m3: float
    cg_offset_m: float
    inertia_per_kg_m2: NDArray[np.float64]


def nose_radius(
    x: NDArray[np.float64], length: float, radius: float, shape: str
) -> NDArray[np.float64]:
    if shape == "conical":
        return radius * x / length
    if shape == "elliptical":
        return radius * np.sqrt(np.maximum(0, 1 - (x / length - 1) ** 2))
    if shape == "ogive":
        rho = (length**2 + radius**2) / (2 * radius)
        return np.sqrt(np.maximum(0, rho**2 - (length - x) ** 2)) + radius - rho
    raise ValueError(f"unsupported nose shape: {shape}")


def nose_cp_offset(length: float, radius: float, shape: str) -> float:
    """Barrowman volume identity; use the external (solid envelope) volume."""
    if shape == "conical":
        return 2 * length / 3
    if shape == "elliptical":
        return length / 3
    x = (_POINTS + 1) * length / 2
    volume = float(np.sum(_WEIGHTS * pi * nose_radius(x, length, radius, shape) ** 2) * length / 2)
    return length - volume / (pi * radius**2)


def shape_properties(kind: str, geometry: dict[str, Any]) -> ShapeProperties:
    g = geometry
    if kind == "fin_set":
        # Uniform trapezoidal plates equally spaced in azimuth (n >= 3).
        # Radial quadrature integrates chord strips, including their x variance.
        u = (_POINTS + 1) * g["span_m"] / 2
        chord = g["root_chord_m"] + (g["tip_chord_m"] - g["root_chord_m"]) * u / g["span_m"]
        lead = g["sweep_m"] * u / g["span_m"]
        weights = _WEIGHTS * g["span_m"] / 2 * chord
        area = float(weights.sum())
        stations = lead + chord / 2
        cg = float(np.sum(weights * stations) / area)
        radial2 = float(np.sum(weights * (g["radius_m"] + u) ** 2) / area)
        axial_variance = float(np.sum(weights * ((stations - cg) ** 2 + chord**2 / 12)) / area)
        axial = radial2 + g["thickness_m"] ** 2 / 12
        transverse = axial_variance + axial / 2
        return ShapeProperties(
            area * g["thickness_m"] * g["count"], cg, np.diag([axial, transverse, transverse])
        )
    if "bbox_m" in g:
        x, y, z = g["bbox_m"]
        diagonal = np.array([y * y + z * z, x * x + z * z, x * x + y * y]) / 12
        return ShapeProperties(x * y * z, x / 2, np.diag(diagonal))
    length, radius = g["length_m"], g["radius_m"]
    x = (_POINTS + 1) * length / 2
    weights = _WEIGHTS * length / 2
    if kind == "nose_cone":
        outer = nose_radius(x, length, radius, g["shape"])
        inner = np.maximum(0, outer - g["wall_m"]) if "wall_m" in g else np.zeros_like(x)
    elif kind == "transition":
        outer = g["fore_radius_m"] + (radius - g["fore_radius_m"]) * x / length
        inner = np.maximum(0, outer - g["wall_m"]) if "wall_m" in g else np.zeros_like(x)
    else:
        outer = np.full_like(x, radius)
        inner = np.full_like(x, g.get("inner_radius_m", 0))
    slices = pi * (outer**2 - inner**2) * weights
    volume = float(slices.sum())
    if volume <= 0:
        raise ValueError("geometry must enclose positive material volume")
    cg = float(np.sum(x * slices) / volume)
    radial2 = outer**2 + inner**2
    axial = float(np.sum(radial2 / 2 * slices) / volume)
    transverse = float(np.sum((radial2 / 4 + (x - cg) ** 2) * slices) / volume)
    return ShapeProperties(volume, cg, np.diag([axial, transverse, transverse]))
