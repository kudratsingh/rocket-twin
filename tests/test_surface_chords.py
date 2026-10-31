"""Known geometry/sign and independent planar strip-integral fixtures."""

import math

import numpy as np
import pytest

from scripts.wo03_surface_chords import (
    disk_triangle_moments,
    known_cases,
    liner_triangle_basis,
    quadrature_wall,
)


def test_first_exit_sign_and_planar_strip_integrals():
    cfg = {"probe_offset_mm": 1e-6, "maximum_normal_chord_mm": 500, "minimum_normal_chord_mm": 1e-5}
    assert all(row["passed"] for row in known_cases(cfg))
    triangle = np.array([[0.0, 0.0], [2.0, 0.0], [0.0, 2.0]])
    moments = disk_triangle_moments(triangle, 1)
    assert moments == pytest.approx([math.pi / 4, 1 / 3, 1 / 3])
    assert disk_triangle_moments(triangle, 10) == pytest.approx([2, 4 / 3, 4 / 3])
    # An annular-sector-like facet straddles the radial cut at1.5mm. Explicit
    # first/last cell extension covers the entire FACET, not a centroid cell.
    facet = np.array([[1.0, 0.0], [2.0, 0.0], [1.0, 0.2]])
    result = liner_triangle_basis(facet, [0.9, 1.5, 2.1], 0.01)
    integrals = result["basis_integrals_m2"]
    assert (integrals >= 0).all()
    assert integrals.sum(axis=0) == pytest.approx(np.full(3, result["facet_area_m2"] / 3))
    assert (integrals.sum(axis=1) > 0).all()
    basis = np.array([[2 / 3, 1 / 6, 1 / 6], [1 / 6, 2 / 3, 1 / 6], [1 / 6, 1 / 6, 2 / 3]])
    matrix, load, diagonal = quadrature_wall(2.0, [5.0] * 3, basis)
    assert matrix == pytest.approx(10 * (np.eye(3) + np.ones((3, 3))) / 12)
    assert matrix.sum(axis=1) == pytest.approx(load)
    assert load.sum() == pytest.approx(diagonal)
    tgas, tbulk = np.array([300.0, 320.0, 310.0]), 290.0
    energy = tgas @ matrix @ tgas - 2 * tbulk * (load @ tgas) + diagonal * tbulk**2
    assert energy == pytest.approx(10 / 3 * np.sum((basis @ tgas - tbulk) ** 2))
