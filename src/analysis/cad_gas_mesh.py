"""Labelled gas PLC tetrahedralization without temperature ownership.

The closed boundary is the frozen actual-CAD radiation tessellation; native STEP
faces are independently matched by area and projected interior samples. Gmsh
fills that unchanged piecewise-linear complex (PLC). Interior lattice spacing
controls volume refinement; it does not alter any solid, opening or boundary.
Tet volume is det([x1-x0,x2-x0,x3-x0])/6; exterior facets occur once in the tet
face incidence table. References: Gmsh 4.15.2 reference manual, discrete geometry,
embedded entities and mesh API; Zienkiewicz & Taylor, The Finite Element Method,
linear tetrahedron geometry. No conduction equation or factorization is solved.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import cadquery as cq
import gmsh  # type: ignore[import-untyped]
import numpy as np


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_source(cfg: dict[str, Any]) -> dict[str, Any]:
    handoff = Path(cfg["handoff"])
    if sha(handoff) != cfg["handoff_sha256"]:
        raise ValueError("Frozen gas handoff hash mismatch")
    source = json.loads(handoff.read_text())
    if source["candidate_identity"] != cfg["candidate_identity"]:
        raise ValueError("Frozen gas candidate identity mismatch")
    paths = {
        key: Path(cfg[key]) for key in ["step", "inventory", "groups", "boundary", "ray_record"]
    }
    for path in paths.values():
        if sha(path) != source["files_sha256"][str(path)]:
            raise ValueError(f"Frozen actual geometry input changed: {path}")
    with np.load(paths["boundary"], allow_pickle=False) as archive:
        boundary = {name: archive[name] for name in archive.files}
    faces = json.loads(paths["inventory"].read_text())
    groups = json.loads(paths["groups"].read_text())
    face_to_group = np.full(len(faces), -1, dtype=np.int32)
    for group in groups:
        for face_id in group["fluid_face_ids"]:
            if face_to_group[face_id - 1] != -1:
                raise ValueError("Source fluid face has duplicate group ownership")
            face_to_group[face_id - 1] = group["group_id"]
    if (face_to_group < 0).any() or any(face["part_id"] is None for face in faces):
        raise ValueError("Source has unassigned material/reservoir faces")
    validate_boundary(boundary, len(faces))
    return {
        "handoff": source,
        "paths": paths,
        "boundary": boundary,
        "faces": faces,
        "groups": groups,
        "face_to_group": face_to_group,
        "source_sha256": {str(p): sha(p) for p in [handoff, *paths.values()]},
    }


def validate_boundary(boundary: dict[str, Any], face_count: int) -> dict[str, Any]:
    points, triangles = boundary["vertices_mm"], boundary["triangles"]
    ids = boundary["triangle_face_index"]
    if set(np.unique(ids)) != set(range(face_count)):
        raise ValueError("Frozen boundary lacks an original CAD face")
    edges = np.sort(
        np.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]]), axis=1
    )
    if (np.unique(edges, axis=0, return_counts=True)[1] != 2).any():
        raise ValueError("Frozen PLC boundary is not closed two-manifold")
    p = points[triangles]
    cross = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    area = np.linalg.norm(cross, axis=1) / 2
    if (area <= 0).any():
        raise ValueError("Frozen PLC has zero-area triangles")
    volume = float(np.einsum("ij,ij->i", p[:, 0], np.cross(p[:, 1], p[:, 2])).sum() / 6)
    if volume <= 0:
        raise ValueError("Frozen PLC winding does not enclose positive fluid volume")
    return {
        "points": len(points),
        "triangles": len(triangles),
        "two_manifold": True,
        "signed_volume_mm3": volume,
    }


def initialize_gmsh() -> dict[str, float]:
    gmsh.initialize()
    settings = {
        "General.Terminal": 1,
        "General.NumThreads": 1,
        "Mesh.MaxNumThreads1D": 1,
        "Mesh.MaxNumThreads2D": 1,
        "Mesh.MaxNumThreads3D": 1,
        "Geometry.Tolerance": 1e-9,
        "Geometry.OCCFixDegenerated": 0,
        "Geometry.OCCFixSmallEdges": 0,
        "Geometry.OCCFixSmallFaces": 0,
        "Geometry.OCCSewFaces": 0,
        "Geometry.OCCMakeSolids": 0,
        "Geometry.OCCScaling": 1,
    }
    for key, value in settings.items():
        gmsh.option.setNumber(key, value)
    return settings


def native_face_mapping(
    step: Path, faces: list[dict[str, Any]], boundary: dict[str, Any], cfg: dict[str, Any]
) -> dict[str, Any]:
    """Bijection from original face IDs to imported entities, never enum order."""
    settings = initialize_gmsh()
    try:
        gmsh.model.add("native_actual_fluid_mapping")
        gmsh.model.occ.setMaxTag(2, 10000)
        gmsh.model.occ.importShapes(str(step), highestDimOnly=False)
        gmsh.model.occ.synchronize()
        surfaces = [tag for _, tag in gmsh.model.getEntities(2)]
        if len(surfaces) != len(faces):
            raise ValueError(f"Native STEP face count changed: {len(surfaces)} versus {len(faces)}")
        areas = np.array([gmsh.model.occ.getMass(2, tag) for tag in surfaces])
        boxes = np.array([gmsh.model.getBoundingBox(2, tag) for tag in surfaces])
        rows = []
        used = set()
        for row in faces:
            point = np.asarray(row["ownership_interior_point_mm"])
            normal = np.asarray(row["void_outward_normal"])
            eps = cfg["point_tolerance_mm"]
            possible = np.flatnonzero(
                (
                    abs(areas - row["cad_area_mm2"])
                    <= max(
                        cfg["area_absolute_tolerance_mm2"],
                        cfg["area_relative_tolerance"] * row["cad_area_mm2"],
                    )
                )
                & (boxes[:, :3] <= point + eps).all(axis=1)
                & (boxes[:, 3:] >= point - eps).all(axis=1)
            )
            matches = []
            for index in possible:
                tag = surfaces[index]
                projected, uv = gmsh.model.getClosestPoint(2, tag, point)
                distance = float(np.linalg.norm(np.asarray(projected) - point))
                if distance > eps or not gmsh.model.isInside(2, tag, uv, parametric=True):
                    continue
                native_normal = np.asarray(gmsh.model.getNormal(tag, uv))
                dot = float(np.dot(native_normal, normal) / np.linalg.norm(native_normal))
                if abs(dot) < cfg["minimum_normal_alignment"]:
                    continue
                matches.append((tag, distance, dot))
            if len(matches) != 1 or matches[0][0] in used:
                raise ValueError(
                    f"Original face{row['fluid_face_id']} has ambiguous/missing native ownership: {matches}"
                )
            tag, distance, dot = matches[0]
            ids = np.flatnonzero(boundary["triangle_face_index"] == row["fluid_face_id"] - 1)
            extra = []
            for i in np.linspace(0, len(ids) - 1, min(len(ids), 9)).astype(int):
                triangle = boundary["triangles"][ids[i]]
                trial = boundary["vertices_mm"][triangle].mean(axis=0)
                projected, uv = gmsh.model.getClosestPoint(2, tag, trial)
                residual = float(np.linalg.norm(np.asarray(projected) - trial))
                if residual <= cfg["facet_projection_tolerance_mm"] and gmsh.model.isInside(
                    2, tag, uv, parametric=True
                ):
                    extra.append({"triangle_id": int(ids[i]), "projection_residual_mm": residual})
                    if len(extra) == min(3, len(ids)):
                        break
            if len(extra) < min(3, len(ids)):
                raise ValueError(
                    f"Insufficient verified interior facet samples for face{row['fluid_face_id']}"
                )
            up, _ = gmsh.model.getAdjacencies(2, tag)
            if len(up) != 1:
                raise ValueError("Imported surface does not bound exactly one gas volume")
            used.add(tag)
            rows.append(
                {
                    "original_face_id": row["fluid_face_id"],
                    "native_entity_tag": tag,
                    "native_area_mm2": gmsh.model.occ.getMass(2, tag),
                    "cad_area_mm2": row["cad_area_mm2"],
                    "exact_sample_residual_mm": distance,
                    "native_to_outward_fluid_normal_sign": 1 if dot > 0 else -1,
                    "normal_alignment_abs": abs(dot),
                    "projected_facet_samples": extra,
                    "part_id": row["part_id"],
                    "source_face_history": row["source_face_history"],
                }
            )
        volume = sum(gmsh.model.occ.getMass(3, tag) for _, tag in gmsh.model.getEntities(3))
        return {
            "rows": rows,
            "all_faces_bijective": len(used) == len(surfaces),
            "native_volume_mm3": volume,
            "source_step_sha256": sha(step),
            "surface_tags_deliberately_offset_from_face_ids": True,
            "settings": settings,
            "gmsh_version": gmsh.__version__,
        }
    finally:
        gmsh.finalize()


def interior_seeds(
    step: Path, boundary: dict[str, Any], spacing_mm: float, clearance_mm: float, max_nodes: int
) -> tuple[np.ndarray, dict[str, Any]]:
    """Analysis points only; classify in actual STEP and avoid PLC uncertainty."""
    import vtk  # type: ignore[import-untyped]
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier  # type: ignore[import-untyped]
    from OCP.gp import gp_Pnt  # type: ignore[import-untyped]
    from OCP.TopAbs import TopAbs_IN  # type: ignore[import-untyped]
    from vtk.util.numpy_support import (  # type: ignore[import-untyped]
        numpy_to_vtk,
        numpy_to_vtkIdTypeArray,
    )

    fluid: Any = cq.importers.importStep(str(step)).val()
    classifiers = [BRepClass3d_SolidClassifier(s.wrapped) for s in fluid.Solids()]
    points = boundary["vertices_mm"]
    lower, upper = points.min(axis=0), points.max(axis=0)
    axes = [
        np.arange(lower[i] + fraction * spacing_mm, upper[i], spacing_mm)
        for i, fraction in enumerate([0.371, 0.217, 0.413])
    ]
    candidates = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, 3)
    rng = np.random.default_rng(319451)
    candidates += rng.uniform(-0.04, 0.04, candidates.shape) * spacing_mm
    vtk.vtkSMPTools.Initialize(1)
    poly = vtk.vtkPolyData()
    vtk_points = vtk.vtkPoints()
    vtk_points.SetData(numpy_to_vtk(points, deep=True))
    poly.SetPoints(vtk_points)
    cells = vtk.vtkCellArray()
    tri = boundary["triangles"]
    cells.SetData(
        numpy_to_vtkIdTypeArray(np.arange(0, 3 * len(tri) + 1, 3, dtype=np.int64), deep=True),
        numpy_to_vtkIdTypeArray(tri.ravel(), deep=True),
    )
    poly.SetPolys(cells)
    locator = vtk.vtkStaticCellLocator()
    locator.SetDataSet(poly)
    locator.BuildLocator()
    closest = [0.0, 0.0, 0.0]
    cell_id, sub_id, distance2 = vtk.mutable(0), vtk.mutable(0), vtk.mutable(0.0)
    retained = []
    near = 0
    for point in candidates:
        inside = False
        for classifier in classifiers:
            classifier.Perform(gp_Pnt(*map(float, point)), 1e-7)
            if classifier.State() == TopAbs_IN:
                inside = True
                break
        if not inside:
            continue
        locator.FindClosestPoint(point, closest, cell_id, sub_id, distance2)
        if float(distance2) <= clearance_mm**2:
            near += 1
            continue
        retained.append(point)
        if len(retained) + len(points) > max_nodes:
            raise RuntimeError("Interior seed plus fixed boundary node cap exceeded before meshing")
    result = np.asarray(retained, dtype=float).reshape(-1, 3)
    return result, {
        "lattice_spacing_mm": spacing_mm,
        "deterministic_jitter_fraction": 0.04,
        "candidate_points": len(candidates),
        "retained_actual_fluid_seeds": len(result),
        "boundary_uncertainty_clearance_mm": clearance_mm,
        "inside_points_omitted_near_boundary": near,
        "no_boundary_or_solid_modified": True,
    }


def tetrahedralize(
    boundary: dict[str, Any], mapping: dict[str, Any], seeds: np.ndarray
) -> dict[str, Any]:
    """Fill the fixed per-face PLC. No surface remeshing or boundary repair."""
    settings = initialize_gmsh()
    try:
        gmsh.model.add("fixed_actual_labelled_PLC")
        points, triangles = boundary["vertices_mm"], boundary["triangles"]
        by_face = {row["original_face_id"]: row["native_entity_tag"] for row in mapping["rows"]}
        tags = [gmsh.model.addDiscreteEntity(2, by_face[i + 1]) for i in range(len(by_face))]
        gmsh.model.mesh.addNodes(2, tags[0], np.arange(1, len(points) + 1), points.ravel())
        for face_index, tag in enumerate(tags):
            selected = triangles[boundary["triangle_face_index"] == face_index]
            gmsh.model.mesh.addElementsByType(tag, 2, [], (selected + 1).ravel())
        gmsh.model.mesh.reclassifyNodes()
        loop = gmsh.model.geo.addSurfaceLoop(tags)
        volume = gmsh.model.geo.addVolume([loop])
        seed_tags = [gmsh.model.geo.addPoint(*map(float, point), 1e6) for point in seeds]
        gmsh.model.geo.synchronize()
        if seed_tags:
            gmsh.model.mesh.embed(0, seed_tags, 3, volume)
        options = {
            "Mesh.Algorithm3D": 1,
            "Mesh.ElementOrder": 1,
            "Mesh.MeshOnlyEmpty": 1,
            "Mesh.MeshSizeMax": 1e6,
            "Mesh.MeshSizeFromPoints": 0,
            "Mesh.MeshSizeFromCurvature": 0,
            "Mesh.MeshSizeExtendFromBoundary": 0,
            "Mesh.Optimize": 0,
            "Mesh.OptimizeNetgen": 0,
            "Mesh.Renumber": 0,
        }
        for key, value in options.items():
            gmsh.option.setNumber(key, value)
        gmsh.model.mesh.generate(3)
        node_tags, coord, _ = gmsh.model.mesh.getNodes()
        order = np.argsort(node_tags)
        node_tags, xyz = np.asarray(node_tags)[order], np.asarray(coord).reshape(-1, 3)[order]
        element_types, _, node_blocks = gmsh.model.mesh.getElements(3)
        if list(element_types) != [4]:
            raise ValueError("Expected only actual linear four-node tetrahedra")
        tet_tags = np.asarray(node_blocks[0]).reshape(-1, 4)
        tetrahedra = np.searchsorted(node_tags, tet_tags)
        fixed_ids = np.searchsorted(node_tags, np.arange(1, len(points) + 1))
        if not np.array_equal(
            node_tags[fixed_ids], np.arange(1, len(points) + 1)
        ) or not np.allclose(xyz[fixed_ids], points, rtol=0, atol=1e-10):
            raise ValueError("Gmsh moved/removed fixed boundary vertices")
        surface_triangles: list[np.ndarray] = []
        surface_face_ids = []
        surface_entity_tags = []
        for face_id, tag in by_face.items():
            types, _, blocks = gmsh.model.mesh.getElements(2, tag)
            if list(types) != [2]:
                raise ValueError(f"Original face{face_id} lacks linear triangle boundary")
            tri_nodes = np.asarray(blocks[0]).reshape(-1, 3)
            surface_triangles.extend(np.searchsorted(node_tags, tri_nodes))
            surface_face_ids.extend([face_id] * len(tri_nodes))
            surface_entity_tags.extend([tag] * len(tri_nodes))
        return {
            "points_m": xyz * 0.001,
            "tetrahedra": tetrahedra.astype(np.int64),
            "gmsh_boundary_triangles": np.asarray(surface_triangles, dtype=np.int64),
            "gmsh_boundary_face_ids": np.asarray(surface_face_ids, dtype=np.int32),
            "gmsh_boundary_entity_tags": np.asarray(surface_entity_tags, dtype=np.int32),
            "fixed_boundary_triangles": fixed_ids[triangles],
            "source_boundary_nodes": len(points),
            "settings": {**settings, **options},
            "automatic_size_refinement_disabled": True,
        }
    finally:
        gmsh.finalize()


def verify_volume_mesh(
    mesh: dict[str, Any],
    boundary: dict[str, Any],
    faces: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    face_to_group: np.ndarray,
    caps: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Exact facet/label coverage plus oriented tet/volume/area diagnostics."""
    points, tet = mesh["points_m"], mesh["tetrahedra"]
    if len(points) > caps["max_nodes"] or len(tet) > caps["max_tetrahedra"]:
        raise RuntimeError(f"Volume resource cap exceeded: {len(points)} nodes/{len(tet)} tets")
    p = points[tet]
    determinant = np.einsum(
        "ij,ij->i", p[:, 1] - p[:, 0], np.cross(p[:, 2] - p[:, 0], p[:, 3] - p[:, 0])
    )
    zero = np.flatnonzero(determinant == 0)
    if len(zero):
        raise ValueError(
            f"Zero-volume tetrahedra: count={len(zero)}, first IDs={zero[:12].tolist()}"
        )
    reversed_count = int((determinant < 0).sum())
    tet[determinant < 0] = tet[determinant < 0][:, [1, 0, 2, 3]]
    determinant = abs(determinant)
    all_faces = np.concatenate([tet[:, c] for c in [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]])
    parent = np.tile(np.arange(len(tet)), 4)
    unique, first, incidence = np.unique(
        np.sort(all_faces, axis=1), axis=0, return_index=True, return_counts=True
    )
    if (incidence > 2).any():
        raise ValueError("Nonmanifold tetrahedral face incidence")
    exterior = unique[incidence == 1]
    exterior_parent = parent[first[incidence == 1]]
    fixed = mesh["fixed_boundary_triangles"]
    fixed_key = np.sort(fixed, axis=1)
    source_order = np.lexsort(fixed_key.T[::-1])
    exterior_order = np.lexsort(exterior.T[::-1])
    if not np.array_equal(exterior[exterior_order], fixed_key[source_order]):
        raise ValueError(
            "Tetra exterior differs from fixed actual PLC facets (holes/extra/filled boundary)"
        )
    gmsh_key = np.sort(mesh["gmsh_boundary_triangles"], axis=1)
    gmsh_order = np.lexsort(gmsh_key.T[::-1])
    if not np.array_equal(gmsh_key[gmsh_order], fixed_key[source_order]):
        raise ValueError("Gmsh split/deleted/added boundary facets")
    source_face_ids = boundary["triangle_face_index"] + 1
    if not np.array_equal(
        mesh["gmsh_boundary_face_ids"][gmsh_order], source_face_ids[source_order]
    ):
        raise ValueError("Boundary physical face provenance changed")
    adjacent = np.empty(len(fixed), dtype=np.int64)
    adjacent[source_order] = exterior_parent[exterior_order]
    xyz = points[fixed]
    cross = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    if (
        np.einsum("ij,ij->i", cross, xyz.mean(axis=1) - points[tet[adjacent]].mean(axis=1)) <= 0
    ).any():
        raise ValueError("Actual fixed facet winding is not outward from gas tets")
    area = np.linalg.norm(cross, axis=1) / 2
    face_area = np.bincount(source_face_ids - 1, weights=area * 1e6, minlength=len(faces))
    cad_face_area = np.array([row["cad_area_mm2"] for row in faces])
    face_error = face_area / cad_face_area - 1
    group_area = np.bincount(face_to_group, weights=face_area, minlength=len(groups))
    group_cad_area = np.bincount(face_to_group, weights=cad_face_area, minlength=len(groups))
    group_error = group_area / group_cad_area - 1
    if (
        abs(face_error).max() > caps["max_face_area_relative_error"]
        or abs(group_error).max() > caps["max_group_area_relative_error"]
    ):
        raise ValueError(
            "Actual CAD face/group area coverage exceeds declared approximation limits"
        )
    plc = validate_boundary(boundary, len(faces))
    volume_mm3 = float(determinant.sum() / 6 * 1e9)
    relative_volume_error = volume_mm3 / plc["signed_volume_mm3"] - 1
    if abs(relative_volume_error) > caps["relative_PLC_volume_tolerance"]:
        raise ValueError("Tetra volume fails frozen PLC volume closure")
    max_edge = np.zeros(len(tet))
    for a, b in [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]]:
        max_edge = np.maximum(max_edge, np.linalg.norm(p[:, a] - p[:, b], axis=1))
    scaled = determinant / max_edge**3
    if (scaled <= caps["minimum_scaled_determinant"]).any():
        raise ValueError("Numerically degenerate actual tetrahedron")
    entity_tags = np.empty(len(fixed), dtype=np.int32)
    entity_tags[source_order] = mesh["gmsh_boundary_entity_tags"][gmsh_order]
    arrays = {
        "points_m": points,
        "tetrahedra": tet,
        "boundary_triangles": fixed.astype(np.int64),
        "boundary_group_ids": face_to_group[source_face_ids - 1],
        "boundary_face_ids": source_face_ids.astype(np.int32),
        "boundary_entity_tags": entity_tags,
        "boundary_area_m2": area,
        "boundary_outward_normal": cross / (2 * area[:, None]),
    }
    diagnostics = {
        "node_count": len(points),
        "boundary_node_count": len(np.unique(fixed)),
        "interior_node_count": len(points) - len(np.unique(fixed)),
        "potential_free_gas_dofs_before_primary_prescription": len(points),
        "prescribed_gas_node_ownership_assigned": False,
        "tetrahedron_count": len(tet),
        "boundary_triangle_count": len(fixed),
        "all_fixed_boundary_coordinates_and_facets_preserved": True,
        "all_exterior_facets_exactly_once": True,
        "boundary_nodes_may_have_multiple_group_labels": True,
        "tet_orientation_index_only_reversals": reversed_count,
        "minimum_tet_volume_m3": float(determinant.min() / 6),
        "minimum_scaled_determinant": float(scaled.min()),
        "scaled_determinant_quantiles": np.quantile(scaled, [0, 0.01, 0.1, 0.5, 1]).tolist(),
        "tetra_volume_mm3": volume_mm3,
        "source_PLC_volume_mm3": plc["signed_volume_mm3"],
        "relative_tet_to_PLC_volume_error": relative_volume_error,
        "maximum_abs_face_area_error_vs_CAD": float(abs(face_error).max()),
        "maximum_abs_group_area_error_vs_CAD": float(abs(group_error).max()),
        "face_area_mm2": face_area.tolist(),
        "group_area_mm2": group_area.tolist(),
        "source_boundary_approximation_is_separate": True,
        "conduction_solved": False,
    }
    return arrays, diagnostics


def source_facet_correspondence(
    arrays: dict[str, Any], boundary: dict[str, Any]
) -> dict[str, np.ndarray]:
    """Exact gas-local→original local-basis map for Robin M/B transfer.

    This exporter deliberately retains source facet order/winding. It refuses
    reordering or coordinate rounding rather than inventing a correspondence.
    Mgas[j,k]=Msource[source_id,perm[j],perm[k]] and Bgas[j]=Bsource[source_id,perm[j]].
    """
    count = len(arrays["boundary_triangles"])
    if count != len(boundary["triangles"]):
        raise ValueError("Original source facets are not one-to-one")
    actual = arrays["points_m"][arrays["boundary_triangles"]]
    expected = boundary["vertices_mm"][boundary["triangles"]] * 0.001
    if not np.array_equal(actual, expected):
        raise ValueError("Source facet correspondence is not bitwise exact in SI")
    if not np.array_equal(arrays["boundary_face_ids"], boundary["triangle_face_index"] + 1):
        raise ValueError("Source facet original face IDs differ")
    return {
        "boundary_source_triangle_ids": np.arange(count, dtype=np.int64),
        "boundary_source_vertex_permutation": np.tile(
            np.array([0, 1, 2], dtype=np.int8), (count, 1)
        ),
    }
