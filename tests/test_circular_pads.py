"""Opt-in exact radial boundaries preserve contact without overlapping foil."""

import math

import cadquery as cq
import pytest

from src.cad.retention_parts import build_retention


def test_exact_pad_arcs_match_independent_volume_and_do_not_enter_foil() -> None:
    geometry = {"length_m": 0.001, "inner_radius_m": 0.017, "radius_m": 0.01823}
    parameters = {"sector_angle_deg": 10, "circular_boundaries": True}
    exact = build_retention("sector_pads", geometry, parameters)
    expected = 3 * 10 / 360 * math.pi * (18.23**2 - 17**2)
    assert exact.isValid()
    assert len(exact.Solids()) == 3
    assert exact.Volume() == pytest.approx(expected, rel=1e-10)
    foil = cq.Workplane("XY").circle(17).circle(16.98).extrude(1).val()
    assert exact.intersect(foil).Volume() == pytest.approx(0, abs=1e-8)
    # Keep the old primitive available for frozen historical input replay.
    legacy = build_retention("sector_pads", geometry, {"sector_angle_deg": 10})
    assert legacy.intersect(foil).Volume() > 0.005
    assert legacy.Volume() < exact.Volume()
