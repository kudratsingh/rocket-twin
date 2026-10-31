"""Geometry validity checks, independently known radiation cases and source gating."""

from __future__ import annotations

import numpy as np
import pytest

from scripts.wo03_finite_radiation import material_temperatures
from src.analysis.finite_radiation import (
    SIGMA,
    AnnularSolid,
    CoaxialTracer,
    Patch,
    enclosure_patches,
    known_cases,
    radiosity,
    sample_view_factors,
)


def test_opaque_contacts_first_hit_and_finite_window() -> None:
    # Two touching opaque layers: their common cylindrical face is not a cavity.
    patches = enclosure_patches(
        [
            AnnularSolid("mica", 0.009, 0.010, 0.0, 0.1),
            AnnularSolid("original_foil", 0.010, 0.01002, 0.0, 0.1),
            AnnularSolid("segment", 0.01498, 0.015, 0.0, 0.04),
            AnnularSolid("ring", 0.0105, 0.02, 0.045, 0.048),
        ],
        0.0,
        0.1,
        0.025,
        0.02,
    )
    assert not any(p.kind == "cylinder" and p.coordinate_m == 0.010 for p in patches)
    tracer = CoaxialTracer(patches)
    hits = tracer.first_hit(
        [[0.01002, 0.0, 0.02], [0.01002, 0.0, 0.044], [0.005, 0.0, 0.05]],
        [[1, 0, 0], [1, 0, 1], [1, 0, 0]],
    )
    # First radial ray hits the added shield. The diagonal end-window ray hits
    # the real ring face. The inner-cavity ray hits the opaque liner first.
    assert patches[hits[0]].part_id == "segment"
    assert patches[hits[1]].part_id == "ring"
    assert patches[hits[1]].kind == "annulus"
    assert patches[hits[2]].part_id == "mica"
    assert patches[hits[2]].face == "inner_cylinder"
    # Whole sampled closed enclosure has no missing boundary or escaping ray.
    sample = sample_view_factors(patches, 15000, 323)
    assert sample["sampling"]["escaped_rays"] == 0
    assert sample["sampling"]["raw_max_row_sum_error"] < 1e-12


def test_independent_radiation_cases_and_two_plate_equation() -> None:
    checks = known_cases(50000)
    assert checks["passed"]
    # Analytic closed two-plate enclosure, not a repeat of the ray estimator.
    area = 0.2
    temperatures = np.array([500.0, 300.0])
    eps = np.array([0.2, 0.9])
    result = radiosity(np.array([[0.0, 1.0], [1.0, 0.0]]), np.full(2, area), temperatures, eps)
    expected = area * SIGMA * (500**4 - 300**4) / (1 / eps[0] + 1 / eps[1] - 1)
    assert result["net_outward_w"] == pytest.approx([expected, -expected])
    assert result["energy_residual_w"] == pytest.approx(0.0, abs=1e-10)


def test_missing_temperatures_and_overlapping_solids_are_rejected() -> None:
    with pytest.raises(ValueError, match="Overlapping solids"):
        enclosure_patches(
            [AnnularSolid("a", 0.01, 0.02, 0, 1), AnnularSolid("b", 0.015, 0.025, 0, 1)],
            0,
            1,
            0.03,
            0.1,
        )
    with pytest.raises(KeyError):
        material_temperatures(
            [Patch("absent_part", "cylinder", 0.01, 0, 0.1, 1, "outer_cylinder")],
            {"part_ids": [], "temperature_k": [[]], "ambient_c": 35.0},
            0,
            573.15,
            False,
        )
    with pytest.raises(ValueError, match="temperatures"):
        radiosity([[0, 1], [1, 0]], [1, 1], [np.nan, 300], [0.9, 0.9])
