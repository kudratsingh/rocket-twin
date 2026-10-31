"""One physical area allocation: glue, open air, mixed coverage and opaque barriers."""

import math

import cadquery as cq
import numpy as np
import pytest

from src.analysis.finite_radiation import AnnularSolid, CoaxialTracer, enclosure_patches
from src.analysis.occupancy import annulus, cylindrical_interface, partition


def test_filled_open_and_half_bonded_interface_have_disjoint_expected_areas() -> None:
    region = annulus(9, 10, 0, 4)
    halfspace = cq.Workplane("XY").box(30, 15, 10).translate((0, 7.5, 2)).val()
    half = region.intersect(halfspace)
    expected = 2 * math.pi * 9.5 * 4
    for solids, fraction in (
        ({}, 0),
        ({"distant_solid": region.translate((0, 0, 100))}, 0),
        ({"glue": region}, 1),
        ({"glue": half}, 0.5),
    ):
        result = cylindrical_interface(9, 10, 0, 4, solids)
        assert result["open_volume_fraction"] == pytest.approx(1 - fraction, abs=1e-9)
        for row in result["area_probe_refinements"]:
            glued = row["material_area_mm2"].get("glue", 0)
            assert glued == pytest.approx(expected * fraction, rel=1e-7, abs=1e-7)
            assert row["open_area_mm2"] == pytest.approx(
                expected * (1 - fraction), rel=1e-7, abs=1e-7
            )
            assert glued + row["open_area_mm2"] == pytest.approx(expected, rel=1e-7)
    with pytest.raises(ValueError, match="Overlapping physical"):
        partition(region, {"glue": region, "another_material": half})


def test_opaque_barrier_blocks_direct_radiation_and_open_window_transmits() -> None:
    patches = enclosure_patches(
        [
            AnnularSolid("inner", 0.009, 0.010, 0, 0.1),
            AnnularSolid("barrier", 0.015, 0.016, 0, 0.04),
        ],
        0,
        0.1,
        0.025,
        0.02,
    )
    hits = CoaxialTracer(patches).first_hit(
        [[0.010, 0, 0.02], [0.010, 0, 0.08]], [[1, 0, 0], [1, 0, 0]]
    )
    assert patches[hits[0]].part_id == "barrier"
    assert patches[hits[1]].part_id == "aft_shell"
    assert np.isfinite([patches[i].area_m2 for i in hits]).all()
