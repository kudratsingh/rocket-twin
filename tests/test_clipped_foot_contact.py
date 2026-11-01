"""Check analytic clipping and spring loss on independent small shapes."""

import math

import numpy as np
import pytest

from scripts.wo03_clipped_foot_contact import foot_matrix, supported_area


def test_clipped_arc_and_positive_semidefinite_lost_foundation():
    radius, y0, half, y1, chord, slot = 1.0, 0.1, 0.3, 0.5, 2.0, 1.0
    expected = radius * (
        (chord - slot) * (math.asin(y1) - math.asin(y0)) + slot * (math.asin(y1) - math.asin(half))
    )
    assert math.isclose(supported_area(radius, y0, y1, half, chord, slot), expected)
    full, _ = foot_matrix(radius, y0, y1, [(y0, chord)], 1000.0, 0.3, 0.1, 16)
    clipped, _ = foot_matrix(
        radius, y0, y1, [(y0, chord - slot), (half, slot)], 1000.0, 0.3, 0.1, 16
    )
    assert np.linalg.eigvalsh(full - clipped).min() > -1e-8
    assert clipped[1, 1] < full[1, 1]
    with pytest.raises(ValueError):
        supported_area(radius, y0, y1, y1 + 0.1, chord, slot)
