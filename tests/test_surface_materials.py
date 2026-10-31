"""Independent Fourier resistance and radial-strip mapping fixtures."""

import math

import numpy as np
import pytest

from scripts.wo03_surface_materials import cylindrical_delta, liner_end_strips, property_bounds


def test_cylindrical_halfwall_and_explicit_liner_end_strips():
    ri, ro, length, k = 0.0147, 0.0151, 0.187, 0.45
    rm = math.sqrt(ri * ro)
    g_from_robin = k / cylindrical_delta(ri, rm) * (2 * math.pi * ri * length)
    exact = 2 * math.pi * k * length / math.log(rm / ri)
    assert g_from_robin == pytest.approx(exact)
    strips = liner_end_strips(ri, ro, length, 16)
    assert len({row["material_state_id"] for row in strips}) == 16
    assert sum(row["area_m2"] for row in strips) == pytest.approx(math.pi * (ro**2 - ri**2))
    bulk = np.arange(16) + 300.0
    surface = 290.0
    q = sum(
        k * row["area_m2"] / row["delta_halfwall_m"] * (bulk[i] - surface)
        for i, row in enumerate(strips)
    )
    radii = np.linspace(ri, ro, 17)
    expected = 2 * k * math.pi / length * np.dot(np.diff(radii**2), bulk - surface)
    assert q == pytest.approx(expected)
    assert property_bounds(
        {"conductivity_w_m_k": 0.45, "conductivity_range_w_m_k": [0.2, 0.7]}, "mica"
    )["bounds_w_m_k"] == [0.2, 0.7]
