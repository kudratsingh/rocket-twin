"""Independent planar tests for strict washer boundary selection."""

import math
from pathlib import Path

import gmsh
import numpy as np
import pytest

from scripts.wo03_g80_bridge_adapter import quadratic_surface_weights
from scripts.wo03_g80_washer_boundary import apply_washer_boundary, verify_source_hashes


def _annulus_and_unrelated():
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setNumber("General.NumThreads", 1)
    gmsh.model.add("fixture")
    a = gmsh.model.occ.addCircle(0, 0, 0, 4.5)
    b = gmsh.model.occ.addCircle(0, 0, 0, 1.7)
    face = gmsh.model.occ.addPlaneSurface(
        [gmsh.model.occ.addCurveLoop([a]), gmsh.model.occ.addCurveLoop([b])]
    )
    other = gmsh.model.occ.addDisk(20, 0, 0, 2, 2)
    gmsh.model.occ.synchronize()
    unrelated = gmsh.model.getBoundary([(2, other)], oriented=False)[0][1]
    gmsh.model.mesh.setTransfiniteCurve(unrelated, 13)
    return face, unrelated


def test_verified_circles_only_area_and_distribution():
    face, unrelated = _annulus_and_unrelated()
    try:
        result = apply_washer_boundary(gmsh, [{"face_tags": [face], "center_xyz_mm": [0, 0, 0]}])
        assert unrelated not in result["sized_curve_tags"]
        gmsh.option.setNumber("Mesh.MeshSizeMax", 1.5)
        gmsh.model.mesh.generate(2)
        gmsh.model.mesh.setOrder(2)
        assert len(gmsh.model.mesh.getElements(1, unrelated)[1][0]) == 12
        for item in result["patches"][0]["curves"]:
            tag, n = item["curve_tag"], item["segments"]
            assert n == (96 if item["ring"] == "outer" else 32)
            assert len(gmsh.model.mesh.getElements(1, tag)[1][0]) == n
            _, xyz, _ = gmsh.model.mesh.getNodes(1, tag, includeBoundary=True)
            xy = np.asarray(xyz).reshape(-1, 3)[:, :2]
            angles = np.unique(np.round(np.mod(np.arctan2(xy[:, 1], xy[:, 0]), 2 * math.pi), 10))
            gaps = np.diff(np.r_[np.sort(angles), np.sort(angles)[0] + 2 * math.pi])
            assert np.max(gaps) <= 2 * math.pi / n + 1e-8
        ids, xyz, _ = gmsh.model.mesh.getNodes()
        coords = {int(n): p for n, p in zip(ids, np.asarray(xyz).reshape(-1, 3), strict=True)}
        types, _, conn = gmsh.model.mesh.getElements(2, face)
        assert list(types) == [9]
        ips, q = gmsh.model.mesh.getIntegrationPoints(9, "Gauss6")
        det = gmsh.model.mesh.getJacobians(9, ips, face)[1]
        _, area = quadratic_surface_weights(
            np.asarray(conn[0]).reshape(-1, 6),
            coords,
            np.asarray(ips).reshape(-1, 3)[:, :2],
            q,
            det,
        )
        assert abs(area - math.pi * (4.5**2 - 1.7**2)) < 0.0002
    finally:
        gmsh.finalize()


def test_unrecognized_center_rejected_before_any_sizing():
    face, _ = _annulus_and_unrelated()
    try:
        with pytest.raises(ValueError, match="Unsupported or ambiguous"):
            apply_washer_boundary(gmsh, [{"face_tags": [face], "center_xyz_mm": [0.1, 0, 0]}])
    finally:
        gmsh.finalize()


def test_noncircular_trim_rejected():
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        face = gmsh.model.occ.addRectangle(0, 0, 0, 2, 2)
        gmsh.model.occ.synchronize()
        with pytest.raises(ValueError, match="Unsupported or ambiguous"):
            apply_washer_boundary(gmsh, [{"face_tags": [face], "center_xyz_mm": [0, 0, 0]}])
    finally:
        gmsh.finalize()


def test_hash_pin_rejects_different_source(tmp_path: Path):
    import hashlib

    p = tmp_path / "source.step"
    p.write_bytes(b"known")
    item = {"path": "source.step", "sha256": hashlib.sha256(b"known").hexdigest()}
    config = {"bridge_step": item, "washer_center_source_step": []}
    assert verify_source_hashes(tmp_path, config)["source.step"] == item["sha256"]
    p.write_bytes(b"changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_source_hashes(tmp_path, config)


def test_split_circle_arcs_use_length_proportional_segments():
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        outer = [
            gmsh.model.occ.addCircle(0, 0, 0, 4.5, angle1=a, angle2=b)
            for a, b in [(0, math.pi / 3), (math.pi / 3, 2 * math.pi)]
        ]
        inner = [
            gmsh.model.occ.addCircle(0, 0, 0, 1.7, angle1=a, angle2=b)
            for a, b in [(0, math.pi), (math.pi, 2 * math.pi)]
        ]
        face = gmsh.model.occ.addPlaneSurface(
            [gmsh.model.occ.addCurveLoop(outer), gmsh.model.occ.addCurveLoop(inner)]
        )
        gmsh.model.occ.synchronize()
        report = apply_washer_boundary(gmsh, [{"face_tags": [face], "center_xyz_mm": [0, 0, 0]}])
        for curve in report["patches"][0]["curves"]:
            radius = 4.5 if curve["ring"] == "outer" else 1.7
            assert curve["segments"] == math.ceil(
                curve["full_circle_equivalent"] * curve["arc_length_mm"] / (2 * math.pi * radius)
                - 1e-10
            )
        gmsh.model.mesh.generate(2)
        for curve in report["patches"][0]["curves"]:
            assert (
                len(gmsh.model.mesh.getElements(1, curve["curve_tag"])[1][0]) == curve["segments"]
            )
    finally:
        gmsh.finalize()
