"""Check free-body extrema for both signs of net axial drive."""

import pytest

from scripts.wo03_g80_axial_flight_bounds import freebody_bounds


def test_forward_freebody_known_values_and_negative_drive():
    assert freebody_bounds(0.2, 0.3, 1.0, 10.0, 2.0) == pytest.approx((1.6, 4.4))
    assert freebody_bounds(0.2, 0.3, 1.0, 2.0, 10.0) == pytest.approx((-2.4, 8.4))
    assert freebody_bounds(0.2, 0.3, 1.0, 5.0, 5.0) == pytest.approx((0.0, 5.0))


def test_invalid_mass_partition_rejected():
    with pytest.raises(ValueError):
        freebody_bounds(0.8, 1.1, 1.0, 10.0, 1.0)
