"""Independent checks for the conservative annular adhesive budget."""

import pytest

from src.vehicle.geometry import shape_properties


def test_annular_budget_mass_and_inertia():
    length, outer, inner, density = 0.190, 0.0323, 0.0322, 1200.0
    props = shape_properties(
        "commercial", {"length_m": length, "radius_m": outer, "inner_radius_m": inner}
    )
    assert props.volume_m3 * density == pytest.approx(0.0046200261563692)
    assert props.cg_offset_m == pytest.approx(length / 2)
    assert props.inertia_per_kg_m2[0, 0] == pytest.approx((outer**2 + inner**2) / 2)
    assert props.inertia_per_kg_m2[1, 1] == pytest.approx(
        (outer**2 + inner**2) / 4 + length**2 / 12
    )
