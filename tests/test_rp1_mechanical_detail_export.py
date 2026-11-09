"""Existing component separation/coordinates, not engineering or CAD qualification."""

import json

import numpy as np
import pytest
import trimesh

from scripts.wo04_rp1_mechanical_detail_export import (
    CATALOG,
    ROOT,
    sha,
    split_exact,
    triangle_fingerprint,
)


def test_catalog_keeps_all_source_ids_and_only_existing_component_geometry():
    packet = json.loads(CATALOG.read_text())
    assert packet["configuration_id"] == "G80-F2-RP1-AD1-definition-v2"
    assert (
        packet["inspection_geometry_sha256"]
        == "238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608"
    )
    assert len(set(packet["all55_part_ids"])) == 55
    assert packet["viewer_frame"] == "X=body+y, Y=length-station, Z=body-z"
    assert packet["units"] == "m"
    assert len(packet["parents"]) == 7 and len(packet["children"]) == 18
    assert {p["id"]: p["child_count"] for p in packet["parents"]} == {
        "fin_set": 3,
        "fin_tabs": 3,
        "root_gussets": 6,
        "body": 1,
        "motor_tube": 1,
        "aft_ring": 1,
        "forward_ring": 3,
    }
    assert all(c["parent_part_id"] in packet["all55_part_ids"] for c in packet["children"])
    assert not set(packet["callout_only_part_ids"]) & {
        c["parent_part_id"] for c in packet["children"]
    }
    middle = next(c for c in packet["children"] if c["sub_id"] == "bond_reservation")
    assert middle["visual_bond_reservation_only"] is True
    assert middle["material"] == "Unspecified bond reservation (display only)"
    assert all(
        p["source_triangles_retained"] and p["child_union_bounds_exact"] for p in packet["parents"]
    )
    assert packet["engineering_accepted"] is False
    assert packet["mass_or_inertia_generated"] is False
    assert packet["canonical_vehicle_geometry_changed"] is False


def test_actual_child_bytes_readback_preserve_oriented_source_triangles_and_union_bounds():
    packet = json.loads(CATALOG.read_text())
    if any(not (ROOT / p["source_path"]).exists() for p in packet["parents"]):
        pytest.skip("Original source GLBs are optional generated files")
    if any(not (ROOT / "web/public" / c["url"].lstrip("/")).exists() for c in packet["children"]):
        pytest.skip("Generated mechanical child GLBs are not committed")
    for parent in packet["parents"]:
        source = ROOT / parent["source_path"]
        assert sha(source.read_bytes()) == parent["source_mesh_sha256"]
        actual = trimesh.load(source, force="scene").to_geometry()
        pieces = []
        for child in [c for c in packet["children"] if c["parent_part_id"] == parent["id"]]:
            path = ROOT / "web/public" / child["url"].lstrip("/")
            assert sha(path.read_bytes()) == child["sha256"]
            mesh = trimesh.load(path, force="scene").to_geometry()
            assert triangle_fingerprint(mesh) == child["oriented_triangles_sha256"]
            np.testing.assert_array_equal(mesh.bounds, child["bounds_m"])
            pieces.append(mesh)
        assert triangle_fingerprint(trimesh.util.concatenate(pieces)) == triangle_fingerprint(
            actual
        )
        union = np.array(
            [
                np.min([p.bounds[0] for p in pieces], axis=0),
                np.max([p.bounds[1] for p in pieces], axis=0),
            ]
        )
        np.testing.assert_array_equal(union, actual.bounds)


def test_exact_welding_finds_three_actual_fin_components_without_mutating_coordinates():
    path = ROOT / "output/rp1-inspection-geometry/parts/fin_set.glb"
    if not path.exists():
        pytest.skip("Original fin mesh is optional generated output")
    mesh = trimesh.load(path, force="scene").to_geometry()
    vertices, faces = mesh.vertices.copy(), mesh.faces.copy()
    pieces = split_exact(mesh)
    assert len(pieces) == 3
    assert [len(p.faces) for p in pieces] == [12, 12, 12]
    assert triangle_fingerprint(trimesh.util.concatenate(pieces)) == triangle_fingerprint(mesh)
    np.testing.assert_array_equal(mesh.vertices, vertices)
    np.testing.assert_array_equal(mesh.faces, faces)


def test_all_current_core_source_pins_are_unchanged():
    packet = json.loads(CATALOG.read_text())
    for relative, expected in packet["sources"].items():
        path = ROOT / relative
        if not path.exists():
            pytest.skip("Optional source asset cache is not present")
        assert sha(path.read_bytes()) == expected
