"""Native BRep analysis mesh with original material-face ownership.

Gmsh generates a new linear surface/volume discretization of the exact frozen
STEP, with no Boolean or topology simplification. Geometric errors below are
observations at specified samples, not certified global distance bounds.
References: Gmsh 4.15.2 reference manual, mesh size fields and OCC/API; linear
tet determinant geometry as in Zienkiewicz & Taylor, Finite Element Method.
No optical transport, wall quadrature or thermal equation is solved.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gmsh  # type: ignore[import-untyped]
import numpy as np

from src.analysis.cad_gas_mesh import initialize_gmsh, verify_volume_mesh


def surface_crossings(points: np.ndarray, triangles: np.ndarray) -> dict[str, Any]:
    """Check all unique edges against nonadjacent facets; no repair.

    VTK's line/triangle predicate is a numerical crossing test, not a proof
    against every coplanar overlap or unsampled curved-CAD deviation.
    """
    import vtk  # type: ignore[import-untyped]
    from vtk.util.numpy_support import (  # type: ignore[import-untyped]
        numpy_to_vtk,
        numpy_to_vtkIdTypeArray,
    )

    vtk.vtkSMPTools.Initialize(1)
    poly = vtk.vtkPolyData()
    vertices = vtk.vtkPoints()
    vertices.SetData(numpy_to_vtk(points, deep=True))
    poly.SetPoints(vertices)
    cells = vtk.vtkCellArray()
    cells.SetData(
        numpy_to_vtkIdTypeArray(np.arange(0, len(triangles) * 3 + 1, 3, dtype=np.int64), deep=True),
        numpy_to_vtkIdTypeArray(triangles.ravel(), deep=True),
    )
    poly.SetPolys(cells)
    locator = vtk.vtkStaticCellLocator()
    locator.SetDataSet(poly)
    locator.BuildLocator()
    edge_blocks = np.sort(
        np.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]]), axis=1
    )
    edges, counts = np.unique(edge_blocks, axis=0, return_counts=True)
    if (counts != 2).any():
        raise ValueError("Native surface is not a closed two-manifold before volume fill")
    hit_points, ids, cell = vtk.vtkPoints(), vtk.vtkIdList(), vtk.vtkGenericCell()
    hit_points.SetDataTypeToDouble()
    crossings = []
    checked = 0
    for edge in edges:
        ids.Reset()
        hit_points.Reset()
        locator.IntersectWithLine(points[edge[0]], points[edge[1]], 1e-9, hit_points, ids, cell)
        checked += 1
        for j in range(ids.GetNumberOfIds()):
            target = int(ids.GetId(j))
            shared = np.intersect1d(edge, triangles[target])
            if len(shared) == 2:
                continue
            hit = np.asarray(hit_points.GetPoint(j))
            if len(shared) and np.linalg.norm(points[shared] - hit, axis=1).min() < 1e-7:
                continue
            crossings.append(
                {"edge_nodes": edge.tolist(), "target_triangle": target, "point_mm": hit.tolist()}
            )
            if len(crossings) >= 16:
                return {
                    "crossings": crossings,
                    "all_edges_checked": False,
                    "checked_edges": checked,
                    "scope": "Nonadjacent edge/facet crossing; stopped after16 findings",
                }
    return {
        "crossings": crossings,
        "all_edges_checked": True,
        "checked_edges": checked,
        "scope": "Nonadjacent edge/facet crossings only; coplanar overlap not certified absent",
    }


def native_mesh(
    source: dict[str, Any], mapping: dict[str, Any], cfg: dict[str, Any], output: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    settings = initialize_gmsh()
    audit: dict[str, Any] = {
        "global_geometry_fidelity_validated": False,
        "new_wall_quadrature_required": True,
        "no_topology_simplification": True,
    }
    try:
        gmsh.model.add("native_exact_fluid")
        gmsh.model.occ.setMaxTag(2, 10000)
        gmsh.model.occ.importShapes(str(source["paths"]["step"]), highestDimOnly=False)
        gmsh.model.occ.synchronize()
        by_tag = {row["native_entity_tag"]: row for row in mapping["rows"]}
        if {tag for _, tag in gmsh.model.getEntities(2)} != set(by_tag):
            raise ValueError("Proven native face tags changed after identical STEP import")
        for tag, row in by_tag.items():
            face = source["faces"][row["original_face_id"] - 1]
            point = np.asarray(face["ownership_interior_point_mm"])
            projected, uv = gmsh.model.getClosestPoint(2, tag, point)
            if np.linalg.norm(np.asarray(projected) - point) > 1e-5 or not gmsh.model.isInside(
                2, tag, uv, parametric=True
            ):
                raise ValueError(
                    "Proven source face interior sample no longer matches native entity"
                )
            if abs(gmsh.model.occ.getMass(2, tag) - face["cad_area_mm2"]) > max(
                1e-6, face["cad_area_mm2"] * 1e-7
            ):
                raise ValueError("Proven native source face area changed")
        corner_tags = [tag for _, tag in gmsh.model.getEntities(0)]
        curve_tags = [tag for _, tag in gmsh.model.getEntities(1)]
        options = {
            "Mesh.Algorithm": 6,
            "Mesh.Algorithm3D": 1,
            "Mesh.ElementOrder": 1,
            "Mesh.MeshSizeMin": cfg["minimum_size_mm"],
            "Mesh.MeshSizeMax": cfg["bulk_mm"],
            "Mesh.MinimumCirclePoints": cfg["circle_points"],
            "Mesh.MinimumCurvePoints": 3,
            "Mesh.MeshSizeFromCurvature": cfg["curvature_points"],
            "Mesh.MeshSizeFromPoints": 0,
            "Mesh.MeshSizeExtendFromBoundary": 0,
            "Mesh.Optimize": 1,
            "Mesh.OptimizeNetgen": 0,
            "Mesh.OptimizeThreshold": 0.3,
        }
        for key, value in options.items():
            gmsh.option.setNumber(key, value)
        audit.update(
            settings={**settings, **options},
            source_face_count=len(by_tag),
            source_corner_count=len(corner_tags),
            source_curve_count=len(curve_tags),
        )
        gmsh.model.mesh.generate(2)
        rows = []
        all_triangles = []
        all_faces = []
        all_entities = []
        for tag, row in by_tag.items():
            types, _, blocks = gmsh.model.mesh.getElements(2, tag)
            if list(types) != [2]:
                raise ValueError(
                    f"Original face{row['original_face_id']} has missing/nonlinear boundary"
                )
            tri = np.asarray(blocks[0]).reshape(-1, 3)
            all_triangles.append(tri)
            all_faces.extend([row["original_face_id"]] * len(tri))
            all_entities.extend([tag] * len(tri))
        node_tags, coord, _ = gmsh.model.mesh.getNodes()
        order = np.argsort(node_tags)
        node_tags, xyz = np.asarray(node_tags)[order], np.asarray(coord).reshape(-1, 3)[order]
        corner_errors = []
        for tag in corner_tags:
            tags, points, _ = gmsh.model.mesh.getNodes(0, tag)
            if len(tags) != 1:
                raise ValueError(f"Native BRep corner{tag} missing or duplicated")
            corner_errors.append(
                float(np.linalg.norm(np.asarray(points) - gmsh.model.getValue(0, tag, [])))
            )
        missing_curves = [
            tag
            for tag in curve_tags
            if not sum(len(block) for block in gmsh.model.mesh.getElements(1, tag)[1])
        ]
        if missing_curves or max(corner_errors, default=0) > cfg["corner_tolerance_mm"]:
            raise ValueError("Original CAD corners/edges were not preserved")
        for (tag, row), block in zip(by_tag.items(), all_triangles, strict=True):
            local = xyz[np.searchsorted(node_tags, block)]
            cross = np.cross(local[:, 1] - local[:, 0], local[:, 2] - local[:, 0])
            area = np.linalg.norm(cross, axis=1) / 2
            selected = np.linspace(
                0, len(local) - 1, min(cfg["sample_triangles_per_face"], len(local))
            ).astype(int)
            chosen = local[selected]
            samples = np.concatenate(
                [
                    chosen.mean(axis=1),
                    (chosen[:, 0] + chosen[:, 1]) / 2,
                    (chosen[:, 1] + chosen[:, 2]) / 2,
                    (chosen[:, 2] + chosen[:, 0]) / 2,
                ]
            )
            projected, uv = gmsh.model.getClosestPoint(2, tag, samples.ravel())
            distances = np.linalg.norm(np.asarray(projected).reshape(-1, 3) - samples, axis=1)
            inside = gmsh.model.isInside(2, tag, uv, parametric=True)
            all_normal = np.asarray(gmsh.model.getNormal(tag, uv)).reshape(-1, 3)
            normal = all_normal[: len(selected)]
            penetration = np.einsum(
                "ij,ij->i",
                samples - np.asarray(projected).reshape(-1, 3),
                all_normal * row["native_to_outward_fluid_normal_sign"],
            )
            original_face = source["faces"][row["original_face_id"] - 1]
            family = source["groups"][source["face_to_group"][row["original_face_id"] - 1]].get(
                "physical_surface_family", {}
            )
            part = row["part_id"]
            known_20um = (
                part.startswith(("motor_radiant_shield", "additional_shield_"))
                and family.get("kind") == "CYLINDER"
            ) or (
                part.startswith("fitting_baffle_")
                and len(part.split("_")) == 4
                and abs(original_face["void_outward_normal"][2]) > 0.999
            )
            triangle_normal = cross[selected] / (2 * area[selected, None])
            align = abs(np.einsum("ij,ij->i", triangle_normal, normal))
            rows.append(
                {
                    "original_face_id": row["original_face_id"],
                    "native_entity_tag": tag,
                    "part_id": row["part_id"],
                    "triangle_count": len(local),
                    "cad_area_mm2": row["cad_area_mm2"],
                    "mesh_area_mm2": float(area.sum()),
                    "relative_area_error": float(area.sum() / row["cad_area_mm2"] - 1),
                    "samples": len(samples),
                    "sampled_max_underlying_surface_projection_mm": float(distances.max()),
                    "projected_samples_outside_trim": len(samples) - inside,
                    "minimum_sampled_abs_normal_alignment": float(align.min()),
                    "global_distance_bound_certified": False,
                    "sampled_max_into_opaque_mm": float(max(0.0, penetration.max())),
                    "sampled_max_into_gas_mm": float(max(0.0, -penetration.min())),
                    "known_20um_barrier_normal": known_20um,
                    "sampled_penetration_fraction_of_20um": (
                        float(max(0.0, penetration.max()) / 0.02) if known_20um else None
                    ),
                }
            )
        audit.update(
            face_geometry=rows,
            surface_nodes=len(node_tags),
            boundary_triangles=sum(len(block) for block in all_triangles),
            all_corners_preserved=True,
            maximum_corner_error_mm=max(corner_errors, default=0),
            all_curves_have_line_elements=True,
            distance_scope="Underlying surface projection samples can lie outside trimmed faces; outside-trim counts are retained, not certified away. Corner preservation is exact within tolerance; sampled errors are not global bounds.",
        )
        (output / "surface-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
        print(
            f"Native2D: {len(node_tags)} nodes; {audit['boundary_triangles']} triangles; every{len(rows)} source faces present",
            flush=True,
        )
        if len(node_tags) > cfg["caps"]["max_nodes"]:
            raise RuntimeError("Native surface node cap exceeded before volume generation")
        if any(
            row["known_20um_barrier_normal"] and row["sampled_max_into_opaque_mm"] >= 0.02
            for row in rows
        ):
            raise ValueError(
                "Observed curved facet penetration traverses a known20um opaque foil barrier"
            )
        native_triangles = np.searchsorted(node_tags, np.concatenate(all_triangles))
        audit["edge_facet_selfintersection"] = surface_crossings(xyz, native_triangles)
        (output / "surface-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
        if audit["edge_facet_selfintersection"]["crossings"]:
            raise ValueError(
                "Native curved facets cross nonadjacent material faces; barrier approximation invalid"
            )
        gmsh.option.setNumber("Mesh.MeshOnlyEmpty", 1)
        gmsh.model.mesh.generate(3)
        node_tags, coord, _ = gmsh.model.mesh.getNodes()
        order = np.argsort(node_tags)
        node_tags, xyz = np.asarray(node_tags)[order], np.asarray(coord).reshape(-1, 3)[order]
        types, _, blocks = gmsh.model.mesh.getElements(3)
        if list(types) != [4]:
            raise ValueError("Native volume contains no/unsupported tet4 cells")
        tet = np.searchsorted(node_tags, np.asarray(blocks[0]).reshape(-1, 4))
        if len(xyz) > cfg["caps"]["max_nodes"] or len(tet) > cfg["caps"]["max_tetrahedra"]:
            raise RuntimeError(f"Native resource cap: {len(xyz)} nodes/{len(tet)} tets")
        surface = []
        face_ids = []
        entities = []
        for tag, row in by_tag.items():
            tri = np.searchsorted(
                node_tags, np.asarray(gmsh.model.mesh.getElements(2, tag)[2][0]).reshape(-1, 3)
            )
            p = xyz[tri]
            _, uv = gmsh.model.getClosestPoint(2, tag, p.mean(axis=1).ravel())
            normal = (
                np.asarray(gmsh.model.getNormal(tag, uv)).reshape(-1, 3)
                * row["native_to_outward_fluid_normal_sign"]
            )
            flip = np.einsum("ij,ij->i", np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), normal) < 0
            tri[flip] = tri[flip][:, [0, 2, 1]]
            surface.append(tri)
            face_ids.extend([row["original_face_id"]] * len(tri))
            entities.extend([tag] * len(tri))
        triangles = np.concatenate(surface)
        face_array = np.asarray(face_ids, dtype=np.int32)
        native_boundary = {
            "vertices_mm": xyz,
            "triangles": triangles,
            "triangle_face_index": face_array - 1,
        }
        raw = {
            "points_m": xyz * 0.001,
            "tetrahedra": tet,
            "fixed_boundary_triangles": triangles,
            "gmsh_boundary_triangles": triangles.copy(),
            "gmsh_boundary_face_ids": face_array,
            "gmsh_boundary_entity_tags": np.asarray(entities, dtype=np.int32),
        }
        arrays, checks = verify_volume_mesh(
            raw,
            native_boundary,
            source["faces"],
            source["groups"],
            source["face_to_group"],
            cfg["caps"],
        )
        cad_volume = mapping["native_volume_mm3"]
        checks["relative_tet_to_exact_CAD_volume_error"] = (
            checks["tetra_volume_mm3"] / cad_volume - 1
        )
        if abs(checks["relative_tet_to_exact_CAD_volume_error"]) > cfg["maximum_CAD_volume_error"]:
            raise ValueError("Native volume approximation exceeds declared bound")
        checks.update(
            new_wall_quadrature_required=True,
            optical_facet_transfer_forbidden=True,
            global_geometry_fidelity_validated=False,
            boundary_triangulation_changed=True,
        )
        return arrays, {
            "mesh_checks": checks,
            "surface_audit": audit,
            "frozen_optical_mesh_node_count": 80186,
            "potential_gas_DOF_ratio_vs_optical_PLC": len(xyz) / 80186,
        }
    finally:
        gmsh.finalize()
