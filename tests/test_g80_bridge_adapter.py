"""Independent quadrature and deck-ownership checks for the G80 adapter."""

from __future__ import annotations

import numpy as np

from scripts.wo03_g80_bridge_adapter import (
    SOURCE,
    _emit_deck,
    _import_washer_patch,
    _surface_normal,
    quadratic_surface_loads,
    source_hashes,
    tetrahedral_gauss_volume,
)


def _unit_tri_fixture():
    coords = {
        1: np.array([0.0, 0.0, 0.0]),
        2: np.array([1.0, 0.0, 0.0]),
        3: np.array([0.0, 1.0, 0.0]),
        4: np.array([0.5, 0.0, 0.0]),
        5: np.array([0.5, 0.5, 0.0]),
        6: np.array([0.0, 0.5, 0.0]),
    }
    # Degree-three-exact symmetric four-point rule on a reference triangle.
    points = np.array([[1 / 3, 1 / 3], [0.2, 0.2], [0.6, 0.2], [0.2, 0.6]])
    weights = np.array([-27 / 96, 25 / 96, 25 / 96, 25 / 96])
    dets = np.ones(4)
    return [(1, 2, 3, 4, 5, 6)], coords, points, weights, dets


def _resultant_and_moment(nodal, coords):
    force = np.zeros(3)
    moment = np.zeros(3)
    for node, vector in nodal.items():
        force += vector
        moment += np.cross(coords[node], vector)
    return force, moment


def test_constant_traction_has_exact_force_and_first_moment():
    triangles, coords, points, weights, dets = _unit_tri_fixture()
    nodal, area = quadratic_surface_loads(
        triangles, coords, points, weights, dets, lambda _xyz: np.array([0.0, 0.0, 4.0])
    )
    force, moment = _resultant_and_moment(nodal, coords)
    assert abs(area - 0.5) < 1e-14
    np.testing.assert_allclose(force, [0.0, 0.0, 2.0], atol=1e-14)
    # Exact area centroid (1/3, 1/3, 0) crossed with the resultant.
    np.testing.assert_allclose(moment, [2 / 3, -2 / 3, 0.0], atol=1e-14)


def test_affine_traction_has_analytic_resultant_and_moment():
    triangles, coords, points, weights, dets = _unit_tri_fixture()

    def traction(xyz):
        x, y, _z = xyz
        return np.array([x + 2 * y, 2 * x - y, 1.0])

    nodal, area = quadratic_surface_loads(triangles, coords, points, weights, dets, traction)
    force, moment = _resultant_and_moment(nodal, coords)
    assert abs(area - 0.5) < 1e-14
    # Analytic integrals over x>=0, y>=0, x+y<=1; not adapter-derived values.
    np.testing.assert_allclose(force, [1 / 2, 1 / 6, 1 / 2], atol=1e-14)
    np.testing.assert_allclose(moment, [1 / 6, -1 / 6, -1 / 12], atol=1e-14)


def test_deck_resets_loads_and_keeps_regions_separate():
    coords = {
        1: np.array([0.0, 0.0, 0.0]),
        2: np.array([1.0, 0.0, 0.0]),
        3: np.array([0.0, 1.0, 0.0]),
        4: np.array([0.5, 0.0, 0.0]),
        5: np.array([0.5, 0.5, 0.0]),
        6: np.array([0.0, 0.5, 0.0]),
        7: np.array([1.5, 0.0, 0.0]),
        8: np.array([2.0, 0.0, 0.0]),
        9: np.array([2.0, 1.0, 0.0]),
    }
    elements = {i: [1, 2, 3, 4, 5, 6, 1, 2, 3, 4] for i in range(1, 8)}
    regions = {"G11": [1], **{f"EPOXY_{i}": [i + 2] for i in range(6)}}
    regions["EPOXY_0"] = [2]
    support = [1]
    # Distinct patch nodes avoid accidental cross-axis load carry-over in the fixture.
    equal = {4: 25.0, 5: 25.0, 6: 25.0, 7: 25.0, 8: 25.0, 9: 25.0}
    single = {4: 75.0, 5: 75.0}
    deck = _emit_deck(coords, elements, regions, support, {"EQUAL": equal, "SINGLE": single})

    assert deck.count("*CLOAD,OP=NEW") == 2
    assert deck.count("*STEP\n") == 2
    assert "*NODE PRINT,NSET=ALL\nU" in deck
    assert "*NODE PRINT,NSET=SUPPORT\nRF" in deck
    assert "*EL PRINT,ELSET=BRIDGE\nS\nENER" in deck
    assert "*EL PRINT,ELSET=ADHESIVE\nS\nENER" in deck
    assert "*ELSET,ELSET=BRIDGE\n1" in deck
    for eid in range(2, 8):
        assert str(eid) in deck

    # Independently read each CLOAD section: step two contains only one 150 N
    # patch, proving the previous 50/50/50 pattern has been replaced.
    sections = []
    current = None
    for line in deck.splitlines():
        if line == "*CLOAD,OP=NEW":
            current = {}
            sections.append(current)
        elif line.startswith("*"):
            current = None
        elif current is not None:
            node, dof, value = line.split(",")
            current[(int(node), int(dof))] = float(value)
    assert sum(sections[0].values()) == 150.0
    assert sum(sections[1].values()) == 150.0
    assert {node for node, dof in sections[1] if dof == 3} == {4, 5}


def test_bridge_recipe_and_mesh_order_sources_are_pinned():
    hashes = source_hashes()
    assert hashes["bridge"] == "f92832b8cf272ef0f4a2f38b6e62312321b80f899e7efba98a004879806408ed"
    assert (
        hashes["film_recipe_source"]
        == "f4124ec5932bd648306f16426d19a28118a8d4d4d0419dc0da5fc89960e68a05"
    )


def test_gmsh_gauss_jacobians_reproduce_affine_triangle_integral():
    import gmsh

    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("adapter_affine_triangle")
        points = [
            gmsh.model.occ.addPoint(0, 0, 0, 1),
            gmsh.model.occ.addPoint(1, 0, 0, 1),
            gmsh.model.occ.addPoint(0, 1, 0, 1),
        ]
        lines = [
            gmsh.model.occ.addLine(points[0], points[1]),
            gmsh.model.occ.addLine(points[1], points[2]),
            gmsh.model.occ.addLine(points[2], points[0]),
        ]
        loop = gmsh.model.occ.addCurveLoop(lines)
        face = gmsh.model.occ.addPlaneSurface([loop])
        gmsh.model.occ.synchronize()
        gmsh.model.mesh.generate(2)
        gmsh.model.mesh.setOrder(2)
        node_tags, xyz_raw, _ = gmsh.model.mesh.getNodes()
        coords = {
            int(tag): np.asarray(xyz_raw[3 * i : 3 * i + 3], dtype=float)
            for i, tag in enumerate(node_tags)
        }
        types, _element_tags, connectivity = gmsh.model.mesh.getElements(2, face)
        if list(types) != [9]:
            raise AssertionError(
                f"Expected only six-node triangles, got Gmsh element types {types}"
            )
        triangles = np.asarray(connectivity[0], dtype=int).reshape(-1, 6)
        local, qweights = gmsh.model.mesh.getIntegrationPoints(9, "Gauss4")
        local_points = np.asarray(local, dtype=float).reshape(-1, 3)[:, :2]
        _jacobians, determinants, _xyz_at_ip = gmsh.model.mesh.getJacobians(9, local, face)
        nodal, area = quadratic_surface_loads(
            triangles,
            coords,
            local_points,
            qweights,
            determinants,
            lambda xyz: np.array([xyz[0] + 2 * xyz[1], 2 * xyz[0] - xyz[1], 1.0]),
        )
        force, moment = _resultant_and_moment(nodal, coords)
        assert abs(area - 0.5) < 1e-12
        np.testing.assert_allclose(force, [1 / 2, 1 / 6, 1 / 2], atol=1e-12)
        np.testing.assert_allclose(moment, [1 / 6, -1 / 6, -1 / 12], atol=1e-12)
    finally:
        gmsh.finalize()


def test_tetrahedral_rule_allows_signed_weights_but_requires_positive_jacobians():
    # Gmsh's 11-point Gauss4 rule has a negative reference weight. Positive
    # physical Jacobians and the signed integrated volume are separate checks.
    import gmsh

    gmsh.initialize()
    try:
        gmsh.model.add("signed_tet_rule")
        _local, weights = gmsh.model.mesh.getIntegrationPoints(11, "Gauss4")
        assert len(weights) == 11
        assert min(weights) < 0
        determinants = [1.0] * len(weights)
        assert abs(tetrahedral_gauss_volume(determinants, weights) - 1 / 6) < 1e-12
    finally:
        gmsh.finalize()
    try:
        tetrahedral_gauss_volume([1.0, -0.1], [0.5, 0.1])
    except ValueError as exc:
        assert "positive Jacobians" in str(exc)
    else:
        raise AssertionError("Negative Jacobian must be rejected")


def test_saved_step_washer_face_selector_uses_z_axis_and_padding_tolerance():
    import gmsh

    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("saved_washer_axis_regression")
        expected_center = (12.75, 22.083647796503)
        face = _import_washer_patch(gmsh, SOURCE / "washer_0.step", expected_center)
        bbox = gmsh.model.getBoundingBox(2, face)
        center = gmsh.model.occ.getCenterOfMass(2, face)
        area = float(gmsh.model.occ.getMass(2, face))
        normal = _surface_normal(gmsh, face, center)

        # The saved part deliberately has Y around 22 mm and Z around 170 mm.
        # OCC pads the bounding box by ~1e-7 mm, so 1e-5 mm accepts this exact
        # planar face while remaining far below the physical 0.1 mm gap.
        assert abs(bbox[2] - 170.1) < 1e-5
        assert abs(bbox[5] - 170.1) < 1e-5
        assert abs(bbox[4] - 170.1) > 100
        assert abs(center[0] - expected_center[0]) < 1e-5
        assert abs(center[1] - expected_center[1]) < 1e-5
        assert abs(center[2] - 170.1) < 1e-5
        assert abs(area - 55.574774042) < 2e-5
        np.testing.assert_allclose(normal, [0.0, 0.0, 1.0], atol=1e-8)
    finally:
        gmsh.finalize()


def test_generated_step_washer_face_selector_is_self_contained(tmp_path):
    import math

    import gmsh

    center_xy = (12.75, 22.083647796503)
    z0, z1 = 169.2, 170.1
    outer_radius, inner_radius = 4.5, 1.6
    step_path = tmp_path / "offset_annular_washer.step"

    # Create a minimal annular solid with the same top-face area and center as
    # the production washer, but deliberately keep Y (~22 mm) unlike Z (170.1 mm).
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("generated_offset_washer")
        outer = gmsh.model.occ.addCylinder(
            center_xy[0], center_xy[1], z0, 0, 0, z1 - z0, outer_radius
        )
        inner = gmsh.model.occ.addCylinder(
            center_xy[0], center_xy[1], z0, 0, 0, z1 - z0, inner_radius
        )
        annulus, _ = gmsh.model.occ.cut(
            [(3, outer)], [(3, inner)], removeObject=True, removeTool=True
        )
        gmsh.model.occ.synchronize()
        assert len([tag for dim, tag in annulus if dim == 3]) == 1
        gmsh.write(str(step_path))
    finally:
        gmsh.finalize()

    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("reimported_offset_washer")
        face = _import_washer_patch(gmsh, step_path, center_xy)
        bbox = gmsh.model.getBoundingBox(2, face)
        center = gmsh.model.occ.getCenterOfMass(2, face)
        area = float(gmsh.model.occ.getMass(2, face))
        normal = _surface_normal(gmsh, face, center)
        analytic_area = math.pi * (outer_radius**2 - inner_radius**2)

        assert abs(bbox[2] - z1) < 1e-5
        assert abs(bbox[5] - z1) < 1e-5
        assert abs(bbox[4] - z1) > 100
        np.testing.assert_allclose(center, [*center_xy, z1], atol=1e-5)
        assert abs(area - analytic_area) < 2e-5
        np.testing.assert_allclose(normal, [0.0, 0.0, 1.0], atol=1e-8)
    finally:
        gmsh.finalize()
