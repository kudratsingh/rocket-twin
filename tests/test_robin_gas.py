"""Consistent triangular quadrature, shared material corners and exact reactions."""

import numpy as np
import pytest

from src.analysis.gas_conduction import assemble_tetra_conductivity
from src.analysis.robin_gas import (
    BoundaryCondition,
    RobinGasMesh,
    factor_robin_gas,
    integrated_wall_terms,
    triangle_robin_matrix,
)


def tetra_mesh() -> RobinGasMesh:
    points = np.array([[0, 0, 0], [1, 0, 0], [-0.3, 0.2, 0], [0, 0, 1]], dtype=float)
    cells = np.array([[0, 1, 2, 3]])
    a = assemble_tetra_conductivity(points, cells, 1)
    faces = a.exterior_triangles.copy()
    xyz = points[faces]
    inward = (
        np.sum(
            np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
            * (points[a.exterior_opposite_nodes] - xyz[:, 0]),
            axis=1,
        )
        > 0
    )
    faces[inward, 1], faces[inward, 2] = faces[inward, 2].copy(), faces[inward, 1].copy()
    return RobinGasMesh(
        points, cells, faces, np.arange(4), {"source": "adversarial_algebra_fixture"}
    )


def test_triangle_mass_and_shared_corner_power_conjugacy() -> None:
    # Independent degree2 triangle quadrature integrates Ni*Nj exactly.
    bary = np.array([[2 / 3, 1 / 6, 1 / 6], [1 / 6, 2 / 3, 1 / 6], [1 / 6, 1 / 6, 2 / 3]])
    exact = 2.3 * 4.5 / 3 * (bary.T @ bary)
    assert triangle_robin_matrix(2.3, 4.5) == pytest.approx(exact, rel=1e-14)
    mesh = tetra_mesh()
    conditions = {i: BoundaryCondition("robin", bulk_id=f"b{i}", h_w_m2_k=i + 1) for i in range(4)}
    factor = factor_robin_gas(mesh, conditions, 1)
    bulk = np.array([310.0, 290.0, 305.0, 295.0])
    target = 300.0
    loads = np.array(
        [conditions[i].h_w_m2_k * factor.group_areas_m2[i] * (target - bulk[i]) for i in range(4)]
    )
    out = factor.evaluate(bulk, [], loads)
    assert out["nodal_temperature_k"] == pytest.approx(np.full(4, target), abs=1e-10)
    assert out["heat_into_bulk_w"] == pytest.approx(loads, abs=1e-10)
    assert abs(out["energy_balance_residual_w"]) < 1e-10
    assert abs(out["form_balance_difference_w_times_k"]) < 1e-8
    assert factor.diagnostics["algebra_checks_pass"]
    assert factor.diagnostics["K_positive_offdiagonals"]["count_above_declared_tolerance"] > 0
    assert not factor.diagnostics["raw_matrix_clipped_repaired_or_corner_prioritized"]


def test_prescribed_reaction_and_invalid_boundary_knowledge() -> None:
    mesh = tetra_mesh()
    conditions = {i: BoundaryCondition("robin", bulk_id="wall", h_w_m2_k=2) for i in range(4)}
    conditions[0] = BoundaryCondition("dirichlet", temperature_id="physical_gas_ambient")
    factor = factor_robin_gas(mesh, conditions, 1)
    out = factor.evaluate([300], [300], [0.2, 0, 0, 0])
    assert out["nodal_temperature_k"] == pytest.approx(np.full(4, 300), abs=1e-10)
    assert out["heat_into_prescribed_reservoir_w"] == pytest.approx([0.2], abs=1e-10)
    assert out["heat_into_bulk_w"] == pytest.approx([0], abs=1e-10)
    with pytest.raises(ValueError, match="Missing boundary"):
        factor_robin_gas(mesh, {}, 1)
    conditions[1] = BoundaryCondition("dirichlet", temperature_id="different_physical_case")
    with pytest.raises(ValueError, match="Conflicting prescribed"):
        factor_robin_gas(mesh, conditions, 1)
    incomplete = RobinGasMesh(
        mesh.points_m,
        mesh.tetrahedra,
        mesh.boundary_triangles[:-1],
        mesh.boundary_group_ids[:-1],
        {},
    )
    with pytest.raises(ValueError, match="ALL exterior"):
        factor_robin_gas(incomplete, conditions, 1)
    with pytest.raises(MemoryError, match="preflight"):
        factor_robin_gas(
            mesh,
            {i: BoundaryCondition("robin", bulk_id="wall", h_w_m2_k=1) for i in range(4)},
            1,
            max_factor_free_nodes=0,
        )


def test_exact_split_cell_integrals_and_quadrature_are_equivalent() -> None:
    area, h = 2.3, 4.5
    integrals = {
        "left": area * np.array([1 / 6, 1 / 4, 1 / 12]),
        "right": area * np.array([1 / 6, 1 / 12, 1 / 4]),
    }
    split = integrated_wall_terms(
        BoundaryCondition("robin", h_w_m2_k=h, bulk_basis_integrals_m2=integrals), area
    )
    bary = np.array([[2 / 3, 1 / 6, 1 / 6], [1 / 6, 2 / 3, 1 / 6], [1 / 6, 1 / 6, 2 / 3]])
    parent = np.eye(3)
    mid = (parent[1] + parent[2]) / 2
    matrix = np.zeros((3, 3))
    vectors = {}
    diagonal = {}
    for name, vertices in [
        ("left", np.array([parent[0], parent[1], mid])),
        ("right", np.array([parent[0], mid, parent[2]])),
    ]:
        shape = bary @ vertices
        weight = area / 6
        matrix += h * weight * shape.T @ shape
        vectors[name] = h * weight * shape.sum(axis=0)
        diagonal[name] = h * area / 2
    general = integrated_wall_terms(
        BoundaryCondition(
            "robin",
            wall_matrix_w_k=matrix,
            bulk_load_vectors_w_k=vectors,
            bulk_diagonal_w_k=diagonal,
        ),
        area,
    )
    assert split["matrix"] == pytest.approx(general["matrix"], rel=1e-14)
    for name in integrals:
        assert split["vectors"][name] == pytest.approx(general["vectors"][name], rel=1e-14)
    # Independent positive, nonconstant-h quadrature energy at three points.
    weighted = area / 3 * np.array([1.0, 2.0, 4.0])
    m = (bary.T * weighted) @ bary
    b = weighted @ bary
    d = float(weighted.sum())
    variable = integrated_wall_terms(
        BoundaryCondition(
            "robin",
            wall_matrix_w_k=m,
            bulk_load_vectors_w_k={"wall": b},
            bulk_diagonal_w_k={"wall": d},
        ),
        area,
    )
    nodal = np.array([293.0, 301.0, 317.0])
    bulk = 305.0
    quadratic = float(
        nodal @ variable["matrix"] @ nodal
        - 2 * bulk * (variable["vectors"]["wall"] @ nodal)
        + d * bulk**2
    )
    assert quadratic == pytest.approx(
        float(np.sum(weighted * (bary @ nodal - bulk) ** 2)), rel=1e-11
    )
    bad = {**integrals, "left": integrals["left"] * 1.01}
    with pytest.raises(ValueError, match="partition"):
        integrated_wall_terms(
            BoundaryCondition("robin", h_w_m2_k=h, bulk_basis_integrals_m2=bad), area
        )
    mesh = tetra_mesh()
    merged = RobinGasMesh(
        mesh.points_m,
        mesh.tetrahedra,
        mesh.boundary_triangles,
        np.zeros(4, dtype=int),
        mesh.metadata,
    )
    conditions = [BoundaryCondition("robin", bulk_id=f"component{i}", h_w_m2_k=2) for i in range(4)]
    factor = factor_robin_gas(merged, conditions, 1)
    assert len(factor.group_ids) == 1 and len(factor.bulk_ids) == 4
    assert factor.evaluate([300] * 4, [], [0])["nodal_temperature_k"] == pytest.approx(
        np.full(4, 300), abs=1e-10
    )
