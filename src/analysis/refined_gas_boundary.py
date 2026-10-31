"""Conforming linear subdivision of the frozen optical gas PLC.

Only existing triangle edges are bisected at their linear midpoint. No point is
projected to CAD, and old vertices retain their bits. Child barycentric maps
identify their ORIGINAL optical parent triangle, not merely a physical face.
Red/green templates preserve orientation; marking an edge splits every incident
triangle. References: standard conforming red/green triangular refinement,
Braess, Finite Elements, adaptive subdivision; affine barycentric coordinates.
This is analysis discretization only, without new physical geometry or solve.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def edge_table(triangles: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    flat = np.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]])
    edges, inverse, counts = np.unique(
        np.sort(flat, axis=1), axis=0, return_inverse=True, return_counts=True
    )
    return edges, inverse.reshape(3, len(triangles)).T, counts


def split_edges(mesh: dict[str, Any], marked: np.ndarray) -> dict[str, Any]:
    points, triangles = mesh["vertices_mm"], mesh["triangles"]
    edges, tri_edges, _ = edge_table(triangles)
    midpoint = np.full(len(edges), -1, dtype=np.int64)
    midpoint[marked] = np.arange(len(points), len(points) + len(marked))
    new_points = np.concatenate(
        [points, (points[edges[marked, 0]] + points[edges[marked, 1]]) * 0.5]
    )
    touched = (midpoint[tri_edges] >= 0).any(axis=1)
    if not touched.any():
        return {**mesh, "vertices_mm": new_points}
    out_tri, out_parent, out_bary = [], [], []
    for i in np.flatnonzero(touched):
        a, b, c = triangles[i]
        m = midpoint[tri_edges[i]]
        active = m >= 0
        nodes = [int(a), int(b), int(c), int(m[0]), int(m[1]), int(m[2])]
        bary = np.concatenate(
            [
                mesh["child_vertex_parent_barycentric"][i],
                (
                    mesh["child_vertex_parent_barycentric"][i][[0, 1, 2]]
                    + mesh["child_vertex_parent_barycentric"][i][[1, 2, 0]]
                )
                * 0.5,
            ]
        )
        count = int(active.sum())
        if count == 0:
            templates = [[0, 1, 2]]
        elif count == 1:
            k = int(np.flatnonzero(active)[0])
            x, y, z = k, (k + 1) % 3, (k + 2) % 3
            templates = [[x, 3 + k, z], [3 + k, y, z]]
        elif count == 2:
            k = next(k for k in range(3) if active[k] and active[(k + 1) % 3])
            x, y, z = k, (k + 1) % 3, (k + 2) % 3
            templates = [[x, 3 + k, z], [3 + k, 3 + (k + 1) % 3, z], [3 + k, y, 3 + (k + 1) % 3]]
        else:
            templates = [[0, 3, 5], [3, 1, 4], [5, 4, 2], [3, 4, 5]]
        for template in templates:
            out_tri.append([nodes[k] for k in template])
            out_parent.append(mesh["original_optical_parent_triangle_ids"][i])
            out_bary.append(bary[template])
    return {
        "vertices_mm": new_points,
        "triangles": np.concatenate([triangles[~touched], np.asarray(out_tri, dtype=np.int64)]),
        "original_optical_parent_triangle_ids": np.concatenate(
            [
                mesh["original_optical_parent_triangle_ids"][~touched],
                np.asarray(out_parent, dtype=np.int64),
            ]
        ),
        "child_vertex_parent_barycentric": np.concatenate(
            [mesh["child_vertex_parent_barycentric"][~touched], np.asarray(out_bary)]
        ),
    }


def initial_mesh(boundary: dict[str, Any]) -> dict[str, Any]:
    return {
        "vertices_mm": boundary["vertices_mm"].copy(),
        "triangles": boundary["triangles"].copy(),
        "original_optical_parent_triangle_ids": np.arange(len(boundary["triangles"])),
        "child_vertex_parent_barycentric": np.tile(np.eye(3), (len(boundary["triangles"]), 1, 1)),
    }


def targets(source: dict[str, Any]) -> dict[str, Any]:
    groups = source["groups"]
    face_to_group = source["face_to_group"]
    parent_group = face_to_group[source["boundary"]["triangle_face_index"]]
    part = np.array([groups[i]["part_id"] for i in parent_group])
    kind = np.array([groups[i]["physical_surface_family"]["kind"] for i in parent_group])
    case = (part == "motor") & (kind == "CYLINDER")
    if not case.any():
        raise ValueError("Actual motor case cylinder unavailable")
    points = source["boundary"]["vertices_mm"][source["boundary"]["triangles"][case]]
    fore, aft = float(points[:, :, 2].min()), float(points[:, :, 2].max())
    liner_groups = [
        g
        for g in groups
        if g["part_id"] == "motor_liner"
        and g["physical_surface_family"]["kind"] == "CYLINDER"
        and g["physical_surface_family"]["void_normal_radial_sign"] == 1
    ]
    if not liner_groups:
        raise ValueError("Actual liner inner cylinder unavailable")
    inner_radius = min(g["physical_surface_family"]["radius_mm"] for g in liner_groups)
    liner_inner_group = {
        g["group_id"]
        for g in liner_groups
        if g["physical_surface_family"]["radius_mm"] == inner_radius
    }
    liner = np.isin(parent_group, list(liner_inner_group))
    pad = part == "thrust_pads"
    if not pad.any():
        raise ValueError("Actual fore thrust pads unavailable")
    pad_points = source["boundary"]["vertices_mm"][source["boundary"]["triangles"][pad]]
    pad_fore = float(pad_points[:, :, 2].min())
    retention_planes = [
        g
        for g in groups
        if g["part_id"] == "retention"
        and g["physical_surface_family"]["kind"] == "PLANE"
        and abs(g["physical_surface_family"]["normal"][2]) > 0.999
    ]
    candidates = [
        (
            g["physical_surface_family"]["normal_station_mm"]
            / g["physical_surface_family"]["normal"][2],
            g["group_id"],
        )
        for g in retention_planes
    ]
    below = [(z, g) for z, g in candidates if z < fore]
    if not below:
        raise ValueError("Actual fore retention plane unavailable")
    retention_z, retention_group = max(below)
    endcap_groups = {
        g["group_id"]
        for g in groups
        if g["part_id"] == "motor"
        and g["physical_surface_family"]["kind"] == "PLANE"
        and abs(g["physical_surface_family"]["normal"][2]) > 0.999
    }
    masks = {
        "global_case_liner": case | liner,
        "local_ends": np.isin(
            part,
            [
                "motor",
                "motor_liner",
                "motor_radiant_shield",
                "thrust_pads",
                "aft_thrust_pads",
                "retention",
                "aft_retainer",
            ],
        ),
        "fore_corner": np.isin(part, ["thrust_pads", "retention"]),
        "planar": np.isin(parent_group, list(endcap_groups | {retention_group})),
    }
    return {
        "masks": masks,
        "fore_mm": fore,
        "aft_mm": aft,
        "pad_fore_mm": pad_fore,
        "retention_plane_mm": retention_z,
        "inner_liner_radius_mm": inner_radius,
        "target_original_face_ids": {
            name: sorted(set((source["boundary"]["triangle_face_index"][mask] + 1).tolist()))
            for name, mask in masks.items()
        },
        "selection_basis": "part_id plus physical surface family; group IDs only resolve family membership, never used as face IDs",
    }


def interval_near(
    a: np.ndarray, b: np.ndarray, low: float, high: float, radius: float
) -> np.ndarray:
    dz = b[:, 2] - a[:, 2]
    nonflat = dz != 0
    lo = np.zeros(len(a))
    hi = np.ones(len(a))
    lo[nonflat] = np.maximum(
        0, np.minimum((low - a[nonflat, 2]) / dz[nonflat], (high - a[nonflat, 2]) / dz[nonflat])
    )
    hi[nonflat] = np.minimum(
        1, np.maximum((low - a[nonflat, 2]) / dz[nonflat], (high - a[nonflat, 2]) / dz[nonflat])
    )
    valid = (lo <= hi) & (nonflat | ((a[:, 2] >= low) & (a[:, 2] <= high)))
    d = b[:, :2] - a[:, :2]
    dd = np.einsum("ij,ij->i", d, d)
    t = np.divide(-np.einsum("ij,ij->i", a[:, :2], d), dd, out=np.zeros(len(a)), where=dd > 0)
    t = np.minimum(hi, np.maximum(lo, t))
    r = np.linalg.norm(a[:, :2] + t[:, None] * d, axis=1)
    return np.asarray(valid & (r < radius), dtype=np.bool_)


def scores(
    mesh: dict[str, Any], selection: dict[str, Any], rules: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, float]]:
    tri = mesh["triangles"]
    edges, tri_edges, counts = edge_table(tri)
    if (counts != 2).any():
        raise ValueError("Actual refinement boundary is not two-manifold")
    parent = mesh["original_optical_parent_triangle_ids"]
    masks = {key: value[parent] for key, value in selection["masks"].items()}
    score = np.zeros(len(edges))
    maxima: dict[str, float] = {}
    for j in range(3):
        ids = tri_edges[:, j]
        a, b = mesh["vertices_mm"][tri[:, j]], mesh["vertices_mm"][tri[:, (j + 1) % 3]]
        dz = abs(b[:, 2] - a[:, 2])
        dxy = np.linalg.norm(b[:, :2] - a[:, :2], axis=1)
        near = interval_near(
            a,
            b,
            selection["fore_mm"] - rules["end_band_mm"],
            selection["fore_mm"] + rules["end_band_mm"],
            rules["local_radius_mm"],
        ) | interval_near(
            a,
            b,
            selection["aft_mm"] - rules["end_band_mm"],
            selection["aft_mm"] + rules["end_band_mm"],
            rules["local_radius_mm"],
        )
        corner = interval_near(
            a, b, selection["pad_fore_mm"], selection["fore_mm"], rules["local_radius_mm"]
        )
        for name, mask, value, limit in [
            ("global_case_liner_maxZ", masks["global_case_liner"], dz, rules["global_axial_mm"]),
            ("near_end_maxZ", masks["local_ends"] & near, dz, rules["local_axial_mm"]),
            ("fore_corner_maxZ", masks["fore_corner"] & corner, dz, rules["local_axial_mm"]),
            ("selected_planar_maxXY", masks["planar"], dxy, rules["plane_edge_mm"]),
        ]:
            maxima[name] = max(
                maxima.get(name, 0.0), float(value[mask].max()) if mask.any() else 0.0
            )
            np.maximum.at(score, ids[mask], value[mask] / limit)
    return edges, tri_edges, score, maxima


def refine(
    boundary: dict[str, Any], selection: dict[str, Any], rules: dict[str, Any], caps: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    mesh = initial_mesh(boundary)
    history = []
    for iteration in range(64):
        edges, tri_edges, score, maxima = scores(mesh, selection, rules)
        violating = np.flatnonzero(score > 1 + 1e-12)
        history.append(
            {
                "iteration": iteration,
                "nodes": len(mesh["vertices_mm"]),
                "triangles": len(mesh["triangles"]),
                "violating_edges": len(violating),
                "actual_maxima_mm": maxima,
            }
        )
        if not len(violating):
            mesh["triangle_face_index"] = boundary["triangle_face_index"][
                mesh["original_optical_parent_triangle_ids"]
            ]
            return mesh, {
                "rules_completed": True,
                "history": history,
                "actual_maxima_mm": maxima,
                "maximum_iterations": iteration,
            }
        # Longest-ratio independent batch avoids unnecessary isotropic red refinement.
        inverse = tri_edges.T.ravel()
        occurrence = np.argsort(inverse, kind="stable")
        incidents = np.tile(np.arange(len(mesh["triangles"])), 3)[occurrence].reshape(-1, 2)
        occupied = np.zeros(len(mesh["triangles"]), dtype=bool)
        priority = violating[
            np.lexsort((edges[violating, 1], edges[violating, 0], -score[violating]))
        ]
        selected = []
        for edge in priority:
            if not occupied[incidents[edge]].any():
                selected.append(edge)
                occupied[incidents[edge]] = True
        selected_array = np.asarray(selected, dtype=np.int64)
        predicted_nodes = len(mesh["vertices_mm"]) + len(selected)
        predicted_triangles = len(mesh["triangles"]) + 2 * len(selected)
        if (
            predicted_nodes > caps["max_boundary_nodes"]
            or predicted_triangles > caps["max_boundary_triangles"]
        ):
            return mesh, {
                "rules_completed": False,
                "status": "incomplete_boundary_count_cap_before_Gmsh",
                "history": history,
                "actual_maxima_mm": maxima,
                "next_predicted_nodes": predicted_nodes,
                "next_predicted_triangles": predicted_triangles,
            }
        mesh = split_edges(mesh, selected_array)
    return mesh, {
        "rules_completed": False,
        "status": "incomplete_iteration_cap_before_Gmsh",
        "history": history,
    }


def validate_partition(
    original: dict[str, Any], refined: dict[str, Any], closed: bool = True
) -> dict[str, Any]:
    points, triangles = refined["vertices_mm"], refined["triangles"]
    parent = refined["original_optical_parent_triangle_ids"]
    bary = refined["child_vertex_parent_barycentric"]
    if not np.array_equal(points[: len(original["vertices_mm"])], original["vertices_mm"]):
        raise ValueError("An original boundary vertex changed bits")
    old = original["vertices_mm"][original["triangles"]]
    new = points[triangles]
    expected = np.einsum("tij,tjk->tik", bary, old[parent])
    reconstruction = np.linalg.norm(new - expected, axis=2)
    tolerance = 128 * np.finfo(float).eps * max(1.0, float(abs(original["vertices_mm"]).max())) * 64
    if (
        bary.min() < 0
        or not np.array_equal(bary.sum(axis=2), np.ones(bary.shape[:2]))
        or reconstruction.max() > tolerance
    ):
        raise ValueError("Child barycentric/in-parent/linear reconstruction failed")
    old_cross = np.cross(old[:, 1] - old[:, 0], old[:, 2] - old[:, 0])
    new_cross = np.cross(new[:, 1] - new[:, 0], new[:, 2] - new[:, 0])
    if (np.einsum("ij,ij->i", new_cross, old_cross[parent]) <= 0).any():
        raise ValueError("Child orientation/positive area failed")
    old_area = np.linalg.norm(old_cross, axis=1) / 2
    new_area = np.linalg.norm(new_cross, axis=1) / 2
    areas = np.bincount(parent, weights=new_area, minlength=len(old))
    area_error = abs(areas / old_area - 1)
    coplanarity = (
        abs(np.einsum("tij,tj->ti", new - old[parent, :1], old_cross[parent]))
        / np.linalg.norm(old_cross[parent], axis=1)[:, None]
    )
    if area_error.max() > 1e-8 or coplanarity.max() > tolerance:
        raise ValueError("Per-parent area/coplanarity conservation failed")
    _, _, edge_counts = edge_table(triangles)
    if closed and (edge_counts != 2).any():
        raise ValueError("Refined boundary is not closed two-manifold")
    old_volume = float(np.einsum("ij,ij->i", old[:, 0], np.cross(old[:, 1], old[:, 2])).sum() / 6)
    new_volume = float(np.einsum("ij,ij->i", new[:, 0], np.cross(new[:, 1], new[:, 2])).sum() / 6)
    if closed and abs(new_volume / old_volume - 1) > 1e-10:
        raise ValueError("Oriented boundary volume changed")
    return {
        "old_vertices_bitwise_retained": True,
        "nodes": len(points),
        "triangles": len(triangles),
        "all_children_inside_original_parent_barycentric": True,
        "maximum_reconstruction_roundoff_mm": float(reconstruction.max()),
        "maximum_coplanarity_roundoff_mm": float(coplanarity.max()),
        "maximum_relative_original_parent_area_error": float(area_error.max()),
        "all_child_orientations_preserved": True,
        "two_manifold": bool((edge_counts == 2).all()),
        "old_oriented_volume_mm3": old_volume,
        "refined_oriented_volume_mm3": new_volume,
        "linear_midpoint_only": True,
        "no_CAD_projection_or_vertex_movement": True,
        "roundoff_coordinate_tolerance_mm": tolerance,
        "new_wall_quadrature_required": True,
    }
