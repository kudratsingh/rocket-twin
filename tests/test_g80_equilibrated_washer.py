"""Known cases for the bounded equilibrated washer-resultant mapping."""

import math

import numpy as np
import pytest

from scripts.wo03_g80_bridge_adapter import (
    _emit_deck,
    _force_resultant,
    equilibrated_washer_loads,
    verify_serialized_loads,
)


def curved_triangle():
    import gmsh

    points0 = [(0, 0), (1, 0), (0, 1), (0.5, 0), (0.5, 0.5), (0, 0.5)]
    coords = {i: np.array([x, y * (1 + 0.2 * x), 0.0]) for i, (x, y) in enumerate(points0, 1)}
    gmsh.initialize()
    try:
        ips, weights = gmsh.model.mesh.getIntegrationPoints(9, "Gauss6")
    finally:
        gmsh.finalize()
    points = np.asarray(ips).reshape(-1, 3)[:, :2]
    return [(1, 2, 3, 4, 5, 6)], coords, points, weights, 1 + 0.2 * points[:, 0]


def test_asymmetric_quadratic_patch_force_and_moment():
    triangles, coords, pts, weights, det = curved_triangle()
    # Exact centroid for x=u, y=v(1+u/5) over the unit reference triangle.
    exact_centroid = np.array([11 / 32, 69 / 200, 0.0])
    target = exact_centroid + [1e-5, -1e-5, 0]
    nodal, info = equilibrated_washer_loads(triangles, coords, pts, weights, det, target)
    f, m = _force_resultant({k: 150 * v for k, v in nodal.items()}, coords)
    np.testing.assert_allclose(info["uncorrected_mesh_center_xyz_mm"], exact_centroid, atol=1e-12)
    np.testing.assert_allclose(f, [0, 0, 150], atol=1e-10)
    np.testing.assert_allclose(m, np.cross(target, [0, 0, 150]), atol=1e-9)
    assert 0 < info["maximum_absolute_relative_pressure_correction"] < 0.005
    with pytest.raises(ValueError, match="ceiling"):
        equilibrated_washer_loads(
            triangles, coords, pts, weights, det, exact_centroid + [0.01, 0, 0]
        )


def test_ill_conditioned_patch_is_rejected():
    triangles, coords, pts, weights, det = curved_triangle()
    for n in coords:
        coords[n][1] *= 1e-9
    with pytest.raises(ValueError, match="ill-conditioned"):
        equilibrated_washer_loads(triangles, coords, pts, weights, det * 1e-9, [0.34, 0, 0])


def test_analytic_annulus():
    import gmsh

    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.model.add("annulus")
        a = gmsh.model.occ.addDisk(0, 0, 0, 4.5, 4.5)
        b = gmsh.model.occ.addDisk(0, 0, 0, 1.6, 1.6)
        faces, _ = gmsh.model.occ.cut([(2, a)], [(2, b)])
        gmsh.model.occ.synchronize()
        face = faces[0][1]
        assert abs(gmsh.model.occ.getMass(2, face) - math.pi * (4.5**2 - 1.6**2)) < 1e-10
        gmsh.option.setNumber("Mesh.MeshSizeMax", 1.5)
        gmsh.model.mesh.generate(2)
        gmsh.model.mesh.setOrder(2)
        ids, xyz, _ = gmsh.model.mesh.getNodes()
        coords = {int(n): x for n, x in zip(ids, np.asarray(xyz).reshape(-1, 3), strict=True)}
        types, _, conn = gmsh.model.mesh.getElements(2, face)
        assert list(types) == [9]
        triangles = np.asarray(conn[0]).reshape(-1, 6)
        ips, weights = gmsh.model.mesh.getIntegrationPoints(9, "Gauss6")
        pts = np.asarray(ips).reshape(-1, 3)[:, :2]
        det = gmsh.model.mesh.getJacobians(9, ips, face)[1]
        nodal, info = equilibrated_washer_loads(triangles, coords, pts, weights, det, [0, 0, 0])
        f, m = _force_resultant({n: 50 * v for n, v in nodal.items()}, coords)
        np.testing.assert_allclose(f, [0, 0, 50], atol=1e-10)
        np.testing.assert_allclose(m, [0, 0, 0], atol=1e-9)
        assert info["maximum_absolute_relative_pressure_correction"] < 0.005
    finally:
        gmsh.finalize()


def test_final_serialized_deck_and_tampering():
    radius = 25.5
    nodes = {
        1: np.array([radius / 2, radius * math.sqrt(3) / 2, 0]),
        2: np.array([-radius, 0.0, 0.0]),
        3: np.array([radius / 2, -radius * math.sqrt(3) / 2, 0]),
    }
    regions = {"G11": [1], **{f"EPOXY_{i}": [i + 2] for i in range(6)}}
    deck = _emit_deck(
        nodes,
        {i: [1] * 10 for i in range(1, 8)},
        regions,
        [1],
        {"EQUAL": {1: 50, 2: 50, 3: 50}, "SINGLE": {1: 150}},
    )
    assert len(verify_serialized_loads(deck)) == 2
    with pytest.raises(ValueError, match="serialized|Serialized"):
        verify_serialized_loads(deck.replace("1,3,150", "1,3,149"))


def test_surface_gauss6_known_sixth_degree_moment():
    import gmsh

    gmsh.initialize()
    try:
        points, weights = gmsh.model.mesh.getIntegrationPoints(9, "Gauss6")
    finally:
        gmsh.finalize()
    x = np.asarray(points).reshape(-1, 3)[:, 0]
    assert abs(np.dot(weights, x**6) - 1 / 56) < 1e-12
