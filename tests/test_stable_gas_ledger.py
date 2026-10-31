"""Stable saved-field heat is offset invariant and retains prescribed reactions."""

from typing import Any

import numpy as np
import pytest

from src.analysis.gas_conduction import assemble_tetra_conductivity
from src.analysis.robin_gas import BoundaryCondition, RobinGasMesh, factor_robin_gas


def mesh() -> RobinGasMesh:
    points = np.array([[0, 0, 0], [1, 0, 0], [-0.3, 0.2, 0], [0, 0, 1]], dtype=float)
    cells = np.arange(4).reshape(1, 4)
    assembly = assemble_tetra_conductivity(points, cells, 1)
    faces = assembly.exterior_triangles.copy()
    xyz = points[faces]
    flip = (
        np.sum(
            np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
            * (points[assembly.exterior_opposite_nodes] - xyz[:, 0]),
            axis=1,
        )
        > 0
    )
    faces[flip, 1], faces[flip, 2] = faces[flip, 2].copy(), faces[flip, 1].copy()
    return RobinGasMesh(points, cells, faces, np.arange(4), {"source": "stable_ledger_fixture"})


def forbidden_solve(*_args: Any) -> Any:
    raise AssertionError("Saved-field evaluation must not solve a PDE")


def test_exact_uniform_saved_field_and_no_solve(monkeypatch: pytest.MonkeyPatch) -> None:
    f = factor_robin_gas(
        mesh(),
        {g: BoundaryCondition("robin", bulk_id="wall", h_w_m2_k=0.1234567) for g in range(4)},
        1,
    )
    before = [
        f.A_w_k.data.copy(),
        f.B_w_k.data.copy(),
        f.D_bulk_w_k.copy(),
        f.L_per_area.data.copy(),
    ]
    monkeypatch.setattr(f, "_solve", forbidden_solve)
    for temperature in [300.0, 1e9]:
        field = np.full(4, temperature)
        a = f.evaluate_saved_field(field, [temperature], [], np.zeros(4))
        assert a["heat_into_bulk_w"] == [0.0]
        assert a["energy_balance_residual_w"] == 0
        assert a["form_balance_difference_w_times_k"] == 0
        assert np.array_equal(a["nodal_temperature_k"], field)
        assert "raw_assembled_energy_balance_residual_w" in a
    for expected, actual in zip(
        before, [f.A_w_k.data, f.B_w_k.data, f.D_bulk_w_k, f.L_per_area.data], strict=True
    ):
        assert np.array_equal(expected, actual)


def test_mixed_bulk_reference_offset_and_independent_heat() -> None:
    conditions = {
        g: BoundaryCondition("robin", bulk_id=f"wall{g}", h_w_m2_k=g + 1) for g in range(4)
    }
    f = factor_robin_gas(mesh(), conditions, 1)
    bulk = np.array([310.0, 290.0, 305.0, 295.0])
    loads = np.array([(g + 1) * f.group_areas_m2[g] * (300 - bulk[g]) for g in range(4)])
    a = f.evaluate_saved_field(np.full(4, 300.0), bulk, [], loads)
    b = f.evaluate_saved_field(np.full(4, 300.0 + 1e9), bulk + 1e9, [], loads)
    assert a["heat_into_bulk_w"] == pytest.approx(loads, abs=1e-13)
    assert a["heat_into_bulk_w"] == b["heat_into_bulk_w"]
    assert a["form_balance_difference_w_times_k"] == b["form_balance_difference_w_times_k"]
    assert abs(a["energy_balance_residual_w"]) < 1e-13
    assert abs(a["form_balance_difference_w_times_k"]) < 1e-12


def test_all_prescribed_reactions_with_no_robin_paths() -> None:
    f = factor_robin_gas(
        mesh(),
        {g: BoundaryCondition("dirichlet", temperature_id="physical_ambient") for g in range(4)},
        1,
    )
    a = f.evaluate_saved_field(np.full(4, 300.0), [], [300.0], [0.4, -0.1, 0.8, 0])
    assert a["heat_into_bulk_w"] == []
    assert a["heat_into_prescribed_reservoir_w"] == pytest.approx([1.1], abs=1e-14)
    assert abs(a["energy_balance_residual_w"]) < 1e-14
    assert abs(a["form_balance_difference_w_times_k"]) < 1e-14
