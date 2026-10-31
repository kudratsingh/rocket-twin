"""Exact mixed-boundary solve, independent derivatives and positive quadrature."""

from pathlib import Path

import numpy as np
import pytest
import yaml

from scripts.wo03_thermal_error_isolation import (
    manufactured,
    run_level,
    structured_box,
    triangle_quadrature,
    wall_conditions,
)
from src.analysis.robin_gas import triangle_robin_matrix

CONFIG = Path("configs/studies/wo03-thermal-error-isolation.yaml")


def test_independent_long_box_mixed_boundary_linear_solution(tmp_path: Path) -> None:
    cfg = yaml.safe_load(CONFIG.read_text())
    source = yaml.safe_load(Path(cfg["verification_source"]).read_text())
    row = run_level("A", 1, cfg, source, tmp_path / "A")
    assert row["nodes"] == 8 and row["tetrahedra"] == 6
    assert row["exact_linear_case_checks_pass"]
    assert row["actual_reservoir_heat_w"] == pytest.approx(
        row["expected_reservoir_heat_w"], rel=1e-6, abs=1e-10
    )


def test_manufactured_derivative_and_positive_spatial_partition() -> None:
    cfg = yaml.safe_load(CONFIG.read_text())
    points = np.array([[0.0001, 0.0003, 0.07], [0.00015, 0.0006, 0.14]])
    _, gradient = manufactured(points, cfg)
    for axis in range(3):
        step = np.eye(3)[axis] * 1e-5
        derivative = (
            manufactured(points + step, cfg)[0] - manufactured(points - step, cfg)[0]
        ) / 2e-5
        assert derivative == pytest.approx(gradient[:, axis], rel=1e-7, abs=1e-8)
    bary, weights = triangle_quadrature()
    assert weights.min() > 0
    assert weights.sum() == pytest.approx(1, abs=1e-14)
    assert bary.sum(axis=1) == pytest.approx(np.ones(16), abs=1e-15)
    assert np.einsum("qi,q,qj->ij", bary, weights, bary) == pytest.approx(
        triangle_robin_matrix(1, 1), abs=1e-14
    )
    mesh, sides = structured_box(cfg["dimensions_m"], 1)
    _, bulk, prescribed, extra = wall_conditions(mesh, sides, "B", cfg)
    assert bulk == {"cold": 300, "hot": 420} and not prescribed
    assert 0 <= extra["fraction_hot"].min() <= extra["fraction_hot"].max() <= 1
    assert extra["matrices_w_k"].sum(axis=2) == pytest.approx(
        extra["Bcold_w_k"] + extra["Bhot_w_k"], abs=1e-16
    )
    assert extra["exact_physical_facet_heat_w"].sum() == pytest.approx(0, abs=1e-14)
