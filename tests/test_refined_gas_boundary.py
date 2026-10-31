"""Linear partition/conformity, local interval rules and label selection."""

import numpy as np

from scripts.wo03_refined_gas_boundary import fixtures
from src.analysis.refined_gas_boundary import interval_near, targets


def test_partition_shared_edge_and_20um_barrier_fixtures() -> None:
    report = fixtures()
    assert report["passed"]
    assert len(report["seven_triangle_partition_templates"]) == 7
    assert report["shared_edge"]["old_vertices_bitwise_retained"]
    assert report["20um_barrier"]["two_manifold"]
    assert (
        report["20um_barrier"]["old_oriented_volume_mm3"]
        == report["20um_barrier"]["refined_oriented_volume_mm3"]
    )


def test_interval_intersection_grades_endpoints_and_respects_local_radius() -> None:
    assert interval_near(
        np.array([[12.0, 0.0, 1001.0]]), np.array([[12.0, 0.0, 1010.0]]), 1010, 1013, 16
    )[0]
    a, b = np.array([[20.0, 0.0, 0.0]]), np.array([[10.0, 0.0, 10.0]])
    assert not interval_near(a, b, 0, 1, 16)[0]
    assert interval_near(a, b, 9, 10, 16)[0]


def test_target_selection_uses_part_family_not_group_as_face_id() -> None:
    groups = [
        {
            "group_id": 0,
            "part_id": "motor",
            "physical_surface_family": {
                "kind": "CYLINDER",
                "radius_mm": 14.5,
                "void_normal_radial_sign": -1,
            },
        },
        {
            "group_id": 1,
            "part_id": "motor_liner",
            "physical_surface_family": {
                "kind": "CYLINDER",
                "radius_mm": 14.7,
                "void_normal_radial_sign": 1,
            },
        },
        {
            "group_id": 2,
            "part_id": "thrust_pads",
            "physical_surface_family": {
                "kind": "CYLINDER",
                "radius_mm": 14.2,
                "void_normal_radial_sign": -1,
            },
        },
        {
            "group_id": 3,
            "part_id": "retention",
            "physical_surface_family": {
                "kind": "PLANE",
                "normal": [0, 0, -1],
                "normal_station_mm": -1010,
            },
        },
        {
            "group_id": 4,
            "part_id": "motor",
            "physical_surface_family": {
                "kind": "PLANE",
                "normal": [0, 0, 1],
                "normal_station_mm": 1013,
            },
        },
        {
            "group_id": 5,
            "part_id": "motor",
            "physical_surface_family": {
                "kind": "PLANE",
                "normal": [0, 0, -1],
                "normal_station_mm": -1200,
            },
        },
    ]
    xyz = []
    for low, high in [
        (1013, 1200),
        (1013, 1200),
        (1010, 1013),
        (1010, 1010),
        (1013, 1013),
        (1200, 1200),
    ]:
        xyz.extend([[12.0, 0.0, low], [13.0, 0.0, high], [12.0, 1.0, low]])
    face = np.array([2, 5, 8, 11, 14, 17])
    face_to_group = np.zeros(18, dtype=np.int32)
    face_to_group[face] = np.arange(6)
    result = targets(
        {
            "groups": groups,
            "face_to_group": face_to_group,
            "boundary": {
                "vertices_mm": np.array(xyz),
                "triangles": np.arange(18).reshape(6, 3),
                "triangle_face_index": face,
            },
        }
    )
    assert result["target_original_face_ids"]["global_case_liner"] == [3, 6]
    assert result["target_original_face_ids"]["planar"] == [12, 15, 18]
    assert result["fore_mm"] == 1013 and result["aft_mm"] == 1200
