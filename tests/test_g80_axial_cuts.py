"""Bounds remain honest for distributed mass crossing an axial cut."""

import pytest

from scripts.wo03_g80_axial_cuts import fraction_bounds


def test_uniform_bar_solution_lies_in_moment_only_bounds():
    low, high = fraction_bounds(0.0, 1.0, 0.5, 0.25)
    assert (low, high) == pytest.approx((0.0, 2.0 / 3.0))
    assert low <= 0.25 <= high
    assert 10.0 * (2.0 * 0.25) / 2.0 == pytest.approx(2.5)


def test_outside_cut_and_invalid_centroid():
    assert fraction_bounds(1.0, 2.0, 1.5, 0.5) == (0.0, 0.0)
    assert fraction_bounds(1.0, 2.0, 1.5, 2.5) == (1.0, 1.0)
    with pytest.raises(ValueError):
        fraction_bounds(1.0, 2.0, 2.1, 1.5)
