"""Finite planar adhesive contact matrix with explicit rigid adherends.

K = integral B.T D B dA, using translation X/Y and rotation Z. Extracted
unchanged from the historical installed-root study so reusable analysis does
not import that study's unpublished CAD/recovery driver. This verifies ideal
contact integration; actual backing stiffness and peel capacity remain inputs.
Reference: linear elastic contact-spring energy; Gere and Goodno, Mechanics of
Materials, elastic strain energy. No installed assembly qualification.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def finite_contact_matrix(
    faces: list[dict[str, Any]], young: float, shear: float, n: int
) -> tuple[Any, list[tuple[Any, Any, Any, Any, float]]]:
    """Finite planar adhesive contact patches; rigid adherends are explicit."""
    points, weights = np.polynomial.legendre.leggauss(n)
    matrix = np.zeros((3, 3))
    quadrature = []
    for face in faces:
        lo, hi = face["interval_m"]
        normal = np.asarray(face["normal"])
        tangent = np.array([-normal[1], normal[0]])
        d = (young * np.outer(normal, normal) + shear * np.outer(tangent, tangent)) / face["gap_m"]
        for p, w in zip(points, weights, strict=True):
            coordinate = (lo + hi) / 2 + p * (hi - lo) / 2
            x, y = (
                (coordinate, face["fixed_coordinate_m"])
                if face["varying_axis"] == "x"
                else (face["fixed_coordinate_m"], coordinate)
            )
            b = np.array([[1, 0, -y], [0, 1, x]], dtype=float)
            area = w * (hi - lo) / 2 * face["axial_width_m"]
            matrix += b.T @ d @ b * area
            quadrature.append((b, d, normal, tangent, float(area)))
    return matrix, quadrature
