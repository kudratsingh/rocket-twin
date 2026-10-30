"""Closed-form section fixture for the clipped motor-rail integration."""

import math

import pytest

from src.analysis.motor_support import _rail_section_mm


def test_clipped_section_against_semicircle_centroidal_integrals() -> None:
    radius = 10
    area, ix, iy = _rail_section_mm(radius / 2, radius, 2 * radius, 100, 1, 1, outer_radius=radius)
    expected_area = math.pi * radius**2 / 2
    expected_ix = math.pi * radius**4 / 8
    expected_iy = expected_ix - expected_area * (4 * radius / (3 * math.pi)) ** 2
    assert area == pytest.approx(expected_area, rel=2e-6)
    assert ix == pytest.approx(expected_ix, rel=5e-6)
    assert iy == pytest.approx(expected_iy, rel=5e-6)
