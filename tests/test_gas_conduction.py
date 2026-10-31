"""Exact affine tetrahedron field, raw nonmonotonicity and invalid-input gates."""

import numpy as np
import pytest

from src.analysis.gas_conduction import GasMesh, group_conductance


def tetra_mesh(*, obtuse: bool = False) -> GasMesh:
    points = np.array(
        [[0, 0, 0], [1, 0, 0], [-0.3, 0.2, 0] if obtuse else [0, 1, 0], [0, 0, 1]], dtype=float
    )
    return GasMesh(
        points,
        np.array([[0, 1, 2, 3]]),
        {f"point{i}": [i] for i in range(4)},
        {
            "unlisted_exterior_faces": "insulated",
            "scope": "Adversarial vertex constraints for algebra only, not physical isothermal face groups.",
        },
    )


def test_affine_field_and_nonmonotone_entries_are_preserved() -> None:
    for obtuse in (False, True):
        mesh = tetra_mesh(obtuse=obtuse)
        result = group_conductance(mesh, 2.0)
        # Independent exact affine field T=300+2x+3y+4z: |grad T|²=29.
        temperature = 300 + mesh.points_m @ np.array([2, 3, 4])
        rates = result.evaluate(temperature)
        expected = 2 * result.volumes_m3.sum() * 29
        assert rates["element_dirichlet_form_w_times_k"] == pytest.approx(expected, rel=1e-12)
        assert rates["matrix_dirichlet_form_w_times_k"] == pytest.approx(expected, rel=1e-10)
        assert abs(sum(rates["net_inward_to_boundary_w"])) < 1e-10
        assert result.diagnostics["algebra_checks_pass"]
        assert not result.diagnostics["raw_matrix_repaired_or_clipped"]
        if obtuse:
            assert result.matrix_w_k[1, 2] > 0
            assert result.diagnostics["negative_raw_pair_conductances"]
            assert (
                result.diagnostics["K_positive_offdiagonals"]["count_above_declared_tolerance"] > 0
            )


def test_invalid_mesh_and_missing_boundary_knowledge_fail() -> None:
    good = tetra_mesh()
    with pytest.raises(ValueError, match="classification"):
        group_conductance(GasMesh(good.points_m, good.tetrahedra, good.boundary_groups), 1)
    with pytest.raises(ValueError, match="ownership"):
        group_conductance(
            GasMesh(good.points_m, good.tetrahedra, {"a": [0], "b": [0, 1]}, good.metadata), 1
        )
    with pytest.raises(ValueError, match="Inverted"):
        group_conductance(
            GasMesh(good.points_m, np.array([[1, 0, 2, 3]]), good.boundary_groups, good.metadata), 1
        )
    points = np.vstack([good.points_m, good.points_m + [2, 0, 0]])
    tets = np.array([[0, 1, 2, 3], [4, 5, 6, 7]])
    with pytest.raises(ValueError, match="Disconnected"):
        group_conductance(GasMesh(points, tets, {"hot": [0]}, good.metadata), 1)


def test_interior_condensation_preserves_exact_affine_field() -> None:
    outer = tetra_mesh(obtuse=True)
    points = np.vstack([outer.points_m, outer.points_m.mean(axis=0)])
    cells = np.array([[4, 1, 2, 3], [0, 4, 2, 3], [0, 1, 4, 3], [0, 1, 2, 4]])
    refined = group_conductance(GasMesh(points, cells, outer.boundary_groups, outer.metadata), 2)
    coarse = group_conductance(outer, 2)
    assert refined.matrix_w_k == pytest.approx(coarse.matrix_w_k, abs=1e-13)
    boundary_t = 300 + outer.points_m @ np.array([2, 3, 4])
    field = refined.evaluate(boundary_t)
    assert field["nodal_temperature_k"][4] == pytest.approx(boundary_t.mean(), abs=1e-12)
    assert field["interior_residual_max_w"] < 1e-12
    assert refined.diagnostics["algebra_checks_pass"]
