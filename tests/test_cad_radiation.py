"""Actual fluid boundaries, material ownership and opaque first-hit fixtures."""

from __future__ import annotations

import hashlib
import json

import cadquery as cq
import numpy as np
import pytest

from src.analysis.cad_radiation import (
    FirstHitLocator,
    aggregate_visibility,
    boundary_topology,
    cut_fluid,
    cylindrical_boundary_coverage,
    load_placed_manifest,
    physical_surface_groups,
    resolve_material_owners,
    sample_first_hit,
    triangulate_fluid,
)


def make_boundary(opaque: dict[str, object]) -> tuple[object, list[dict], dict]:
    fluid, rows, _ = cut_fluid(cq.Solid.makeBox(20, 20, 20), opaque, 1e-7)
    rows, owners = resolve_material_owners(fluid, rows, opaque, 1e-4)
    assert owners["all_material_owners_verified"]
    mesh = triangulate_fluid(fluid, rows, 0.05, 0.2, 1e-7, 150000, 1e-4)
    assert mesh["checks"]["watertight_two_manifold_edges"]
    assert abs(mesh["checks"]["relative_volume_error"]) < 1e-12
    return fluid, rows, mesh


@pytest.mark.parametrize("case", ["open", "full", "partial", "two_barriers"])
def test_actual_boolean_glue_and_nearest_opaque_hit(case: str) -> None:
    opaque = {}
    if case in ["full", "partial"]:
        opaque["glue"] = cq.Solid.makeBox(
            0.4, 20 if case == "full" else 10, 20, cq.Vector(9.8, 0, 0)
        )
    if case == "two_barriers":
        opaque = {
            "near": cq.Solid.makeBox(0.4, 20, 20, cq.Vector(8, 0, 0)),
            "far": cq.Solid.makeBox(0.4, 20, 20, cq.Vector(12, 0, 0)),
        }
    fluid, rows, mesh = make_boundary(opaque)
    locator = FirstHitLocator(mesh["vertices_mm"], mesh["triangles"])
    for y in [5.0, 15.0]:
        cell, distance = locator.hit(np.array([1.0, y, 10.0]), np.array([1.0, 0.0, 0.0]))
        assert cell >= 0
        owner = rows[mesh["triangle_face_index"][cell]]["part_id"]
        expected = (
            "near"
            if case == "two_barriers"
            else "glue" if case == "full" or (case == "partial" and y < 10) else "radial_reservoir"
        )
        assert owner == expected
        assert distance == pytest.approx(7 if owner == "near" else 8.8 if owner == "glue" else 19)
    if case == "full":
        # The four glue-to-enclosure contact faces are not fluid boundaries.
        assert len(fluid.Solids()) == 2
        assert sum(r["cad_area_mm2"] for r in rows if r["part_id"] == "glue") == pytest.approx(800)


def test_true_material_overlap_is_rejected_without_priority() -> None:
    slab = cq.Solid.makeBox(0.4, 20, 20, cq.Vector(9.8, 0, 0))
    opaque = {"material_a": slab, "material_b": slab.copy()}
    fluid, rows, _ = cut_fluid(cq.Solid.makeBox(20, 20, 20), opaque, 1e-7)
    rows, owners = resolve_material_owners(fluid, rows, opaque, 1e-4)
    assert not owners["all_material_owners_verified"]
    assert owners["ambiguous_or_unverified_area_mm2"] == pytest.approx(800)
    with pytest.raises(ValueError, match="ambiguous"):
        physical_surface_groups(fluid, rows)


def test_touching_same_part_screw_contact_removed_with_original_ancestry() -> None:
    screw = cq.Compound.makeCompound(
        [
            cq.Solid.makeCylinder(1.5, 10, cq.Vector(10, 10, 0)),
            cq.Solid.makeCylinder(2.75, 3, cq.Vector(10, 10, 10)),
        ]
    )
    fluid, rows, geometry = cut_fluid(cq.Solid.makeBox(20, 20, 20), {"screw": screw}, 1e-7)
    rows, owners = resolve_material_owners(fluid, rows, {"screw": screw}, 1e-4)
    assert owners["all_material_owners_verified"]
    union = geometry["same_part_internal_contact_unions"][0]
    assert union["source_solid_count"] == 2
    assert union["union_solid_count"] == 1
    assert union["volume_change_mm3"] == pytest.approx(0)
    assert union["original_face_history_retained"]
    # The head underside is an annulus; the coincident internal shank disk
    # must not remain a zero-thickness "radiating" fluid face.
    underside = [
        r
        for r in rows
        if r["part_id"] == "screw" and abs(r["ownership_interior_point_mm"][2] - 10) < 1e-7
    ]
    assert len(underside) == 1
    assert underside[0]["cad_area_mm2"] == pytest.approx(np.pi * (2.75**2 - 1.5**2))
    assert all(r["source_face_history"] for r in rows)


def test_diffuse_cube_integral_closure_and_preserved_faces() -> None:
    fluid, rows, mesh = make_boundary({})
    groups, mapping = physical_surface_groups(fluid, rows)
    assert sorted(face for group in groups for face in group["fluid_face_ids"]) == list(range(1, 7))
    result = sample_first_hit(mesh, mapping, 12000, 100, 713451, 1e-5)
    view = result["raw_view_factors"]
    assert result["escaped_rays"] == result["near_origin_hits"] == 0
    assert result["max_row_closure_error"] < 1e-12
    assert np.diag(view).sum() == 0
    normals = np.array([group["physical_surface_family"]["normal"] for group in groups])
    observed = view[normals @ normals.T < -0.9].mean()
    expected = 0.199824895698387
    assert abs(observed - expected) < 5 * np.sqrt(expected * (1 - expected) / 12000)
    assert not result["reciprocity_projection_applied"]


@pytest.mark.parametrize("angle", [180, 360])
def test_exact_inner_control_wall_coverage_and_real_reservoir(angle: int) -> None:
    paper = cq.Solid.makeCylinder(11, 10, angleDegrees=angle).cut(cq.Solid.makeCylinder(10, 10))
    fluid, rows, _ = cut_fluid(cq.Solid.makeCylinder(10, 10), {"paper": paper}, 1e-7)
    rows, ownership = resolve_material_owners(fluid, rows, {"paper": paper}, 1e-4)
    assert ownership["all_material_owners_verified"]
    assert boundary_topology(fluid)["all_finite_edges_have_two_face_incidences"]
    coverage = cylindrical_boundary_coverage(fluid, rows, {"paper": paper}, 10, 0, 10)
    assert coverage["coverage_balance_passed"]
    areas = coverage["actual_exposed_face_area_by_owner_mm2"]
    assert areas["paper"] == pytest.approx(2 * np.pi * 10 * 10 * angle / 360)
    assert areas.get("radial_reservoir", 0) == pytest.approx(
        2 * np.pi * 10 * 10 * (1 - angle / 360)
    )


def test_outer_tangent_root_rejected_as_cad_nonmanifold_before_meshing() -> None:
    shell = cq.Solid.makeCylinder(10, 10).cut(cq.Solid.makeCylinder(9, 10))
    root = cq.Solid.makeBox(3, 4, 2, cq.Vector(10, -2, 4))
    fluid, _, _ = cut_fluid(cq.Solid.makeCylinder(11, 10), {"shell": shell, "root": root}, 1e-7)
    assert fluid.isValid()
    topology = boundary_topology(fluid)
    assert not topology["all_finite_edges_have_two_face_incidences"]
    assert topology["nonmanifold_edges"]
    assert all(e["face_incidence_count"] == 4 for e in topology["nonmanifold_edges"])


def test_placed_manifest_preserves_notch_and_placement_and_rejects_tamper(tmp_path) -> None:
    shape = cq.Solid.makeBox(4, 4, 2, cq.Vector(2, 3, 1001)).cut(
        cq.Solid.makeCylinder(0.5, 2, cq.Vector(4, 5, 1001))
    )
    step, stl = tmp_path / "notched.step", tmp_path / "notched.stl"
    cq.exporters.export(shape, str(step))
    cq.exporters.export(shape, str(stl))
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    row = {
        "part_id": "notched",
        "material": "aluminum",
        "cad_role": "manufactured",
        "step": step.name,
        "step_sha256": digest(step),
        "stl": stl.name,
        "stl_sha256": digest(stl),
        "placed_frame": "CAD_mm_X_body_y_Y_minus_body_z_Z_aft_station",
        "volume_m3": shape.Volume() * 1e-9,
        "valid": True,
        "custom_postprocessing_required": True,
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([row]))
    parts = {
        "notched": {"material": "aluminum", "cad": {"role": "manufactured"}, "position_m": 100}
    }
    opaque, inventory, _, assets = load_placed_manifest(
        manifest, digest(manifest), parts, ["manufactured"], 990, 1010, 32.5
    )
    assert opaque["notched"].BoundingBox().zmin == pytest.approx(1001)
    assert opaque["notched"].Volume() == pytest.approx(32 - np.pi * 0.5**2 * 2)
    assert inventory[0]["custom_postprocessing_required"]
    assert len(assets) == 2
    step.write_text("tampered")
    with pytest.raises(ValueError, match="asset hash"):
        load_placed_manifest(manifest, digest(manifest), parts, ["manufactured"], 990, 1010, 32.5)


def test_visibility_confidence_preserves_area_weights_and_zero_hit_bound() -> None:
    operator = {
        "counts": np.array([100, 100, 20]),
        "hits": np.array([[90, 0, 10], [0, 60, 40], [0, 0, 20]]),
        "group_area_m2": np.array([2.0, 1.0, 1.0]),
    }
    result = aggregate_visibility(operator, [0, 1], [2], 4)
    assert result["direct_exchange_area_m2"] == pytest.approx(0.6)
    assert result["area_weighted_F"] == pytest.approx(0.2)
    assert result["F_confidence_bound"][0] < 0.2 < result["F_confidence_bound"][1]
    empty = aggregate_visibility(operator, [2], [0], 1)
    assert empty["area_weighted_F"] == 0
    assert empty["F_confidence_bound"][0] == 0
    assert empty["F_confidence_bound"][1] == pytest.approx(1 - 0.025 ** (1 / 20))
