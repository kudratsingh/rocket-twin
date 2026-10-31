"""Opaque first-hit radiation on the actual CAD fluid boundary.

Geometry is a closed Boolean air void. Its outward BRep normals point into the
solid/reservoir; diffuse emission uses the opposite direction, into the fluid.
The view-factor estimator is the cosine-weighted first-hit integral described by
Modest, Radiative Heat Transfer (3rd ed.), diffuse-enclosure chapters. No surface
temperature, emissivity fitting, thermal transient or engineering pass is inferred.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import cadquery as cq
import numpy as np


def load_placed_manifest(
    path: Path,
    expected_sha256: str,
    parts: dict[str, dict[str, Any]],
    opaque_roles: list[str],
    fore_mm: float,
    aft_mm: float,
    radius_mm: float,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    """Use supplied placed solids, preserving script-owned notches and seams.

    This branch never invokes a generic CAD generator or applies a second
    placement transform. Both manifest asset hashes are checked, but only STEP
    supplies opaque geometry. All declared CAD parts must appear exactly once.
    """
    import json

    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError("Placed geometry manifest hash mismatch")
    rows = json.loads(path.read_text())
    ids = [row["part_id"] for row in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(parts):
        raise ValueError("Placed geometry manifest has missing/duplicate/extra CAD parts")
    opaque = {}
    inventory = []
    excluded = []
    assets = {}
    for row in rows:
        name = row["part_id"]
        part = parts[name]
        if row["placed_frame"] != "CAD_mm_X_body_y_Y_minus_body_z_Z_aft_station":
            raise ValueError(f"Unsupported placed STEP frame: {name}")
        if row["material"] != part["material"] or row["cad_role"] != part["cad"]["role"]:
            raise ValueError(f"Placed geometry material/role mismatch: {name}")
        for kind in ["step", "stl"]:
            asset = path.parent / row[kind]
            value = hashlib.sha256(asset.read_bytes()).hexdigest()
            if value != row[kind + "_sha256"]:
                raise ValueError(f"Placed geometry asset hash mismatch: {name}/{kind}")
            assets[str(asset)] = value
        if row["cad_role"] not in opaque_roles:
            excluded.append(
                {"id": name, "reason": "Source budget/flexible role is not an opaque solid"}
            )
            continue
        shape: Any = cq.importers.importStep(str(path.parent / row["step"])).val()
        expected_volume = row["volume_m3"] * 1e9
        if not shape.isValid() or not row["valid"] or shape.Volume() <= 0:
            raise ValueError(f"Invalid placed STEP solid: {name}")
        if abs(shape.Volume() - expected_volume) > max(1e-6, 1e-7 * expected_volume):
            raise ValueError(f"Placed STEP volume disagrees with source manifest: {name}")
        box = shape.BoundingBox()
        if (
            box.zmax < fore_mm
            or box.zmin > aft_mm
            or box.xmin > radius_mm
            or box.xmax < -radius_mm
            or box.ymin > radius_mm
            or box.ymax < -radius_mm
        ):
            excluded.append(
                {"id": name, "reason": "Actual placed BRep bounds outside selected enclosure"}
            )
            continue
        opaque[name] = shape
        inventory.append(
            {
                "id": name,
                "placed_step_sha256": row["step_sha256"],
                "cad_role": row["cad_role"],
                "volume_mm3": shape.Volume(),
                "source_manifest_volume_mm3": expected_volume,
                "solid_count": len(shape.Solids()),
                "estimated_purchased_envelope": row["cad_role"] == "purchased_envelope",
                "custom_postprocessing_required": row["custom_postprocessing_required"],
                "source_frame_applied_exactly_once": True,
                "geometry_basis": "supplied placed STEP; no generic regeneration",
            }
        )
    return opaque, inventory, excluded, assets


def cut_fluid(
    enclosure: Any, opaque: dict[str, Any], tolerance_mm: float
) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
    """Subtract actual part solids at once, retaining Boolean face provenance."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse  # type: ignore[import-untyped]
    from OCP.TopAbs import TopAbs_FACE  # type: ignore[import-untyped]
    from OCP.TopExp import TopExp  # type: ignore[import-untyped]
    from OCP.TopTools import (  # type: ignore[import-untyped]
        TopTools_IndexedMapOfShape,
        TopTools_ListOfShape,
    )

    args = TopTools_ListOfShape()
    args.Append(enclosure.wrapped)
    tools = TopTools_ListOfShape()
    sources = []
    for index, face in enumerate(enclosure.Faces()):
        box = face.BoundingBox()
        owner = (
            "fore_reservoir"
            if box.zlen < 1e-7 and abs(box.zmin - enclosure.BoundingBox().zmin) < 1e-7
            else "aft_reservoir" if box.zlen < 1e-7 else "radial_reservoir"
        )
        sources.append((owner, index, [face.wrapped]))
    union_info = []
    for part_id, shape in opaque.items():
        solids = shape.Solids()
        union = None
        tool_shape = shape
        if len(solids) > 1:
            union_args = TopTools_ListOfShape()
            union_args.Append(solids[0].wrapped)
            union_tools = TopTools_ListOfShape()
            for solid in solids[1:]:
                union_tools.Append(solid.wrapped)
            union = BRepAlgoAPI_Fuse()
            union.SetArguments(union_args)
            union.SetTools(union_tools)
            union.SetNonDestructive(True)
            union.SetRunParallel(False)
            union.SetToFillHistory(True)
            union.SetFuzzyValue(tolerance_mm)
            union.Build()
            if not union.IsDone():
                raise RuntimeError(f"Opaque internal-contact union failed: {part_id}")
            tool_shape = cq.Shape.cast(union.Shape())
            change = tool_shape.Volume() - shape.Volume()
            if not tool_shape.isValid() or abs(change) > max(1e-5, 1e-10 * shape.Volume()):
                raise RuntimeError(
                    f"Opaque per-part union changed source volume: {part_id}: {change}"
                )
            union_info.append(
                {
                    "part_id": part_id,
                    "source_solid_count": len(solids),
                    "union_solid_count": len(tool_shape.Solids()),
                    "source_faces": len(shape.Faces()),
                    "union_faces": len(tool_shape.Faces()),
                    "volume_change_mm3": change,
                    "original_face_history_retained": True,
                }
            )
        tools.Append(tool_shape.wrapped)
        for index, face in enumerate(shape.Faces()):
            ancestors = [face.wrapped]
            if union is not None:
                ancestors += [
                    *list(union.Modified(face.wrapped)),
                    *list(union.Generated(face.wrapped)),
                ]
            sources.append((part_id, index, ancestors))
    operation = BRepAlgoAPI_Cut()
    operation.SetArguments(args)
    operation.SetTools(tools)
    operation.SetNonDestructive(True)
    operation.SetRunParallel(False)
    operation.SetToFillHistory(True)
    operation.SetFuzzyValue(tolerance_mm)
    if opaque:
        operation.Build()
    if opaque and not operation.IsDone():
        raise RuntimeError("Actual fluid Boolean did not complete")
    fluid = cq.Shape.cast(operation.Shape()) if opaque else enclosure
    if not fluid.isValid() or fluid.Volume() <= 0:
        raise RuntimeError("Actual fluid Boolean is invalid/empty")
    result_map = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(fluid.wrapped, TopAbs_FACE, result_map)
    lineage: dict[int, list[dict[str, Any]]] = {}
    for owner, index, ancestors in sources:
        descendants = []
        for face in ancestors:
            descendants.append(face)
            if opaque:
                descendants += [*list(operation.Modified(face)), *list(operation.Generated(face))]
        for shape in descendants:
            if shape.ShapeType() != TopAbs_FACE:
                continue
            target = result_map.FindIndex(shape)
            if target:
                item = {"part_id": owner, "source_face_index": index}
                if item not in lineage.setdefault(target, []):
                    lineage[target].append(item)
    inventory = []
    errors = []
    for index in range(1, result_map.Extent() + 1):
        owners = lineage.get(index, [])
        part_ids = sorted({x["part_id"] for x in owners})
        if len(part_ids) != 1:
            errors.append({"fluid_face": index, "owners": owners})
        face = cq.Shape.cast(result_map.FindKey(index))
        inventory.append(
            {
                "fluid_face_id": index,
                "part_id": part_ids[0] if len(part_ids) == 1 else None,
                "source_face_history": owners,
                "cad_area_mm2": face.Area(),
                "reservoir": len(part_ids) == 1 and part_ids[0].endswith("_reservoir"),
            }
        )
    info = {
        "cad_fluid_volume_mm3": fluid.Volume(),
        "fluid_solid_count": len(fluid.Solids()),
        "fluid_face_count": len(inventory),
        "ownership_errors": errors,
        "all_faces_have_unique_part_owner": not errors,
        "same_part_internal_contact_unions": union_info,
        "operation": "single actual BRep cut; internal contacts removed by Boolean",
    }
    return fluid, inventory, info


def triangulate_fluid(
    fluid: Any,
    inventory: list[dict[str, Any]],
    deflection_mm: float,
    angle_rad: float,
    weld_mm: float,
    max_triangles: int,
    offset_mm: float,
) -> dict[str, Any]:
    """Mesh shared BRep edges; verify orientation using projected interior UVs.

    Face.Center is never used to decide ownership or fluid side. Triangulation
    UV centroids produce actual points on the trimmed underlying CAD face; a
    face classifier verifies the sample before the solid-side test.
    """
    from OCP.BRep import BRep_Tool  # type: ignore[import-untyped]
    from OCP.BRepAdaptor import BRepAdaptor_Surface  # type: ignore[import-untyped]
    from OCP.BRepClass import BRepClass_FaceClassifier  # type: ignore[import-untyped]
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier  # type: ignore[import-untyped]
    from OCP.BRepMesh import BRepMesh_IncrementalMesh  # type: ignore[import-untyped]
    from OCP.BRepTools import BRepTools  # type: ignore[import-untyped]
    from OCP.gp import gp_Pnt, gp_Pnt2d, gp_Vec  # type: ignore[import-untyped]
    from OCP.TopAbs import TopAbs_FACE, TopAbs_IN, TopAbs_REVERSED
    from OCP.TopExp import TopExp
    from OCP.TopLoc import TopLoc_Location  # type: ignore[import-untyped]
    from OCP.TopTools import TopTools_IndexedMapOfShape

    # A finer cached triangulation must not make the three requested levels
    # identical or silently consume the triangle budget.
    BRepTools.Clean_s(fluid.wrapped)
    BRepMesh_IncrementalMesh(fluid.wrapped, deflection_mm, False, angle_rad, False)
    mapping = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(fluid.wrapped, TopAbs_FACE, mapping)
    vertex_map = {}
    vertices: list[np.ndarray] = []
    triangles: list[list[int]] = []
    face_ids = []
    face_checks = []
    zero_area_triangles = []
    classifiers = [BRepClass3d_SolidClassifier(s.wrapped) for s in fluid.Solids()]

    def inside(point: np.ndarray) -> bool:
        p = gp_Pnt(*map(float, point))
        for classifier in classifiers:
            classifier.Perform(p, weld_mm)
            if classifier.State() == TopAbs_IN:
                return True
        return False

    for face_index in range(1, mapping.Extent() + 1):
        face = cq.Shape.cast(mapping.FindKey(face_index))
        location = TopLoc_Location()
        mesh = BRep_Tool.Triangulation_s(face.wrapped, location)
        if mesh is None or mesh.NbTriangles() == 0:
            raise RuntimeError(f"Unmeshed fluid face {face_index}")
        if len(triangles) + mesh.NbTriangles() > max_triangles:
            raise RuntimeError("Boundary triangle budget exceeded")
        transform = location.Transformation()
        points = np.array(
            [
                [p.X(), p.Y(), p.Z()]
                for p in (mesh.Node(i).Transformed(transform) for i in range(1, mesh.NbNodes() + 1))
            ]
        )
        ids = []
        for point in points:
            key = tuple(np.rint(point / weld_mm).astype(np.int64))
            if key not in vertex_map:
                vertex_map[key] = len(vertices)
                vertices.append(point)
            ids.append(vertex_map[key])
        normal_samples = []
        projected_checks: list[dict[str, Any]] = []
        surface = BRepAdaptor_Surface(face.wrapped)
        reversed_face = face.wrapped.Orientation() == TopAbs_REVERSED
        for number in range(1, mesh.NbTriangles() + 1):
            a, b, c = mesh.Triangle(number).Get()
            local = [a - 1, b - 1, c - 1]
            if reversed_face:
                local = [local[0], local[2], local[1]]
            tri = [ids[i] for i in local]
            p3 = points[local]
            cross = np.cross(p3[1] - p3[0], p3[2] - p3[0])
            norm = float(np.linalg.norm(cross))
            if norm <= 1e-16:
                # OCP's periodic surfaces can emit collapsed pole triangles.
                # These have zero area, not a removed material patch; manifold
                # edge checks below must still pass after their explicit removal.
                zero_area_triangles.append({"fluid_face_id": face_index, "twice_area_mm2": norm})
                continue
            uv = np.mean([[mesh.UVNode(i + 1).X(), mesh.UVNode(i + 1).Y()] for i in local], axis=0)
            classifier = (
                BRepClass_FaceClassifier(
                    face.wrapped, gp_Pnt2d(float(uv[0]), float(uv[1])), weld_mm
                )
                if len(projected_checks) < 3
                else None
            )
            point = gp_Pnt()
            du = gp_Vec()
            dv = gp_Vec()
            surface.D1(float(uv[0]), float(uv[1]), point, du, dv)
            exact = np.array([point.X(), point.Y(), point.Z()])
            normal = np.array([du.Crossed(dv).X(), du.Crossed(dv).Y(), du.Crossed(dv).Z()])
            if reversed_face:
                normal = -normal
            normal /= np.linalg.norm(normal)
            alignment = float(np.dot(cross / norm, normal))
            if alignment <= 0:
                raise RuntimeError(f"Triangle winding disagrees with CAD face{face_index}")
            normal_samples.append(alignment)
            if classifier is not None and classifier.State() == TopAbs_IN:
                projected_checks.append(
                    {
                        "point_mm": exact.tolist(),
                        "minus_outward_is_fluid": inside(exact - offset_mm * normal),
                        "plus_outward_is_not_fluid": not inside(exact + offset_mm * normal),
                    }
                )
            triangles.append(tri)
            face_ids.append(face_index - 1)
        if not projected_checks or not all(
            c["minus_outward_is_fluid"] and c["plus_outward_is_not_fluid"] for c in projected_checks
        ):
            raise RuntimeError(
                f"Actual interior fluid-side verification failed face{face_index}: {projected_checks}"
            )
        face_checks.append(
            {
                "fluid_face_id": face_index,
                "minimum_normal_dot": min(normal_samples),
                "projected_interior_samples": projected_checks,
            }
        )
    vertex = np.asarray(vertices)
    triangle = np.asarray(triangles, dtype=np.int64)
    face_id = np.asarray(face_ids, dtype=np.int64)
    edges = np.sort(
        np.concatenate((triangle[:, [0, 1]], triangle[:, [1, 2]], triangle[:, [2, 0]])), axis=1
    )
    unique_edges, counts = np.unique(edges, axis=0, return_counts=True)
    if np.any(counts != 2):
        diagnostics = []
        for edge, count in zip(unique_edges[counts != 2], counts[counts != 2], strict=True):
            touching = np.flatnonzero(np.isin(triangle, edge).sum(axis=1) == 2)
            diagnostics.append(
                {
                    "edge_vertices_mm": vertex[edge].tolist(),
                    "incidence_count": int(count),
                    "incident_fluid_face_ids": (face_id[touching] + 1).tolist(),
                }
            )
        raise RuntimeError(
            f"Fluid triangulation has {int((counts!=2).sum())} non-two-manifold edges: {diagnostics}"
        )
    p = vertex[triangle]
    cross = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    area = np.linalg.norm(cross, axis=1) / 2
    signed_volume = float(np.einsum("ij,ij->i", p[:, 0], np.cross(p[:, 1], p[:, 2])).sum() / 6)
    cad_volume = fluid.Volume()
    return {
        "vertices_mm": vertex,
        "triangles": triangle,
        "triangle_face_index": face_id,
        "triangle_area_mm2": area,
        "outward_triangle_normal": cross / (2 * area[:, None]),
        "cad_face_area_mm2": np.array([row["cad_area_mm2"] for row in inventory]),
        "mesh_face_area_mm2": np.bincount(face_id, weights=area, minlength=len(inventory)),
        "checks": {
            "triangle_count": len(triangle),
            "vertex_count": len(vertex),
            "watertight_two_manifold_edges": True,
            "signed_mesh_volume_mm3": signed_volume,
            "cad_fluid_volume_mm3": cad_volume,
            "relative_volume_error": signed_volume / cad_volume - 1,
            "all_triangle_windings_match_actual_fluid_boundary": True,
            "discarded_exactly_collapsed_pole_triangles": zero_area_triangles,
            "face_checks": face_checks,
        },
    }


def boundary_topology(fluid: Any) -> dict[str, Any]:
    """Check actual BRep incidences before spending a mesh or ray budget.

    Coincident/tangent opaque faces can leave a valid OCP solid with four
    incident faces along a contact line. Coordinate welding is not its cause.
    Exactly degenerated pole edges are separately reported, not finite edges.
    """
    from OCP.BRep import BRep_Tool
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
    from OCP.TopExp import TopExp
    from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape, TopTools_IndexedMapOfShape

    ancestry = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(fluid.wrapped, TopAbs_EDGE, TopAbs_FACE, ancestry)
    face_map = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(fluid.wrapped, TopAbs_FACE, face_map)
    counts: dict[int, int] = {}
    bad = []
    degenerated = []
    for index in range(1, ancestry.Extent() + 1):
        wrapped = ancestry.FindKey(index)
        edge: Any = cq.Shape.cast(wrapped)
        faces = list(ancestry.FindFromIndex(index))
        if BRep_Tool.Degenerated_s(edge.wrapped):
            degenerated.append({"cad_edge_id": index, "length_mm": edge.Length()})
            continue
        count = len(faces)
        counts[count] = counts.get(count, 0) + 1
        if count != 2:
            box = edge.BoundingBox()
            bad.append(
                {
                    "cad_edge_id": index,
                    "face_incidence_count": count,
                    "fluid_face_ids": [face_map.FindIndex(face) for face in faces],
                    "length_mm": edge.Length(),
                    "bounds_mm": {
                        "min": [box.xmin, box.ymin, box.zmin],
                        "max": [box.xmax, box.ymax, box.zmax],
                    },
                    "curve_type": edge.geomType(),
                }
            )
    return {
        "all_finite_edges_have_two_face_incidences": not bad,
        "finite_edge_incidence_counts": counts,
        "nonmanifold_edges": bad,
        "degenerated_pole_edges": degenerated,
        "verification": "actual BRep edge-face ancestry, before coordinate welding or triangulation",
    }


def cylindrical_boundary_coverage(
    fluid: Any,
    inventory: list[dict[str, Any]],
    opaque: dict[str, Any],
    radius_mm: float,
    fore_mm: float,
    aft_mm: float,
) -> dict[str, Any]:
    """Independent inner-limit surface cuts audit a radial control boundary.

    A control surface can be covered by adjacent paper, genuinely open to a
    reservoir, or blocked on its fluid side by a finite part. The latter area
    has no fluid boundary face. Three inward-offset cylindrical surface cuts
    independently check exposed versus blocked area, without inventing air
    across the occupied regions or asserting visibility from area alone.
    """
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    full = 2 * np.pi * radius_mm * (aft_mm - fore_mm)
    area_by_owner: dict[str, float] = {}
    face_ids = []
    for face, row in zip(fluid.Faces(), inventory, strict=True):
        if face.geomType() != "CYLINDER":
            continue
        cylinder = BRepAdaptor_Surface(face.wrapped).Cylinder()
        if abs(cylinder.Radius() - radius_mm) > 1e-6:
            continue
        point = np.asarray(row["ownership_interior_point_mm"])
        normal = np.asarray(row["void_outward_normal"])
        if np.dot(point[:2], normal[:2]) <= 0:
            continue
        owner = str(row["part_id"])
        area_by_owner[owner] = area_by_owner.get(owner, 0.0) + row["cad_area_mm2"]
        face_ids.append(row["fluid_face_id"])
    exposed = sum(area_by_owner.values())
    probes = []
    for offset in [0.001, 0.0001, 0.00001]:
        r = radius_mm - offset
        cylinder_shape = cq.Solid.makeCylinder(r, aft_mm - fore_mm, cq.Vector(0, 0, fore_mm))
        radial = next(f for f in cylinder_shape.Faces() if f.geomType() == "CYLINDER")
        open_surface = radial.cut(*opaque.values(), tol=1e-7) if opaque else radial
        if not open_surface.isValid():
            raise RuntimeError("Invalid independent control-cylinder surface cut")
        projected_air = open_surface.Area() * radius_mm / r
        probes.append(
            {
                "inward_offset_mm": offset,
                "probe_radius_mm": r,
                "exposed_air_area_projected_mm2": projected_air,
                "opaque_blocked_area_projected_mm2": full - projected_air,
                "difference_from_actual_fluid_boundary_mm2": projected_air - exposed,
            }
        )
    tolerance = max(0.05, full * 1e-6)
    passed = abs(probes[-1]["difference_from_actual_fluid_boundary_mm2"]) <= tolerance and all(
        -tolerance <= p["opaque_blocked_area_projected_mm2"] <= full + tolerance for p in probes
    )
    return {
        "radius_mm": radius_mm,
        "full_control_cylinder_area_mm2": full,
        "actual_exposed_fluid_face_area_mm2": exposed,
        "actual_exposed_face_area_by_owner_mm2": area_by_owner,
        "actual_radial_fluid_face_ids": face_ids,
        "independent_inward_surface_cut_probes": probes,
        "finest_probe_absolute_tolerance_mm2": tolerance,
        "coverage_balance_passed": passed,
        "scope": "independent radial coverage; area is not line-of-sight visibility; uncovered adjacent boundary stays unknown reservoir",
    }


def save_mesh(mesh: dict[str, Any], path: Path) -> str:
    arrays = {key: value for key, value in mesh.items() if isinstance(value, np.ndarray)}
    np.savez_compressed(path, **arrays)  # type: ignore[arg-type]
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interior_sample(face: Any, tolerance_mm: float = 0.1) -> tuple[np.ndarray, np.ndarray]:
    """Project an actual triangle interior onto its trimmed CAD face, never Center."""
    from OCP.BRepClass import BRepClass_FaceClassifier
    from OCP.gp import gp_Pnt2d
    from OCP.TopAbs import TopAbs_IN

    vertices, triangles = face.tessellate(tolerance_mm, 0.1)
    for triangle in triangles:
        trial = np.mean([vertices[i].toTuple() for i in triangle], axis=0)
        u, v = face.paramAt(cq.Vector(*map(float, trial)))
        classifier = BRepClass_FaceClassifier(face.wrapped, gp_Pnt2d(u, v), 1e-8)
        if classifier.State() != TopAbs_IN:
            continue
        normal, point = face.normalAt(u, v)
        return np.array(point.toTuple()), np.array(normal.toTuple())
    raise RuntimeError("No verified projected interior point found on a fluid face")


def resolve_material_owners(
    fluid: Any, inventory: list[dict[str, Any]], opaque: dict[str, Any], offset_mm: float
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Retain ancestry; resolve only through actual material-side occupancy.

    True multi-material overlap is rejected. A tolerance or an arbitrarily
    selected material never turns overlapping foil/pad geometry into a pass.
    """
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.gp import gp_Pnt
    from OCP.TopAbs import TopAbs_IN

    part_classifiers = {
        name: [BRepClass3d_SolidClassifier(s.wrapped) for s in shape.Solids()]
        for name, shape in opaque.items()
    }
    fluid_classifiers = [BRepClass3d_SolidClassifier(s.wrapped) for s in fluid.Solids()]
    bounds = {name: shape.BoundingBox() for name, shape in opaque.items()}

    def inside(classifiers: list[Any], point: np.ndarray) -> bool:
        for classifier in classifiers:
            classifier.Perform(gp_Pnt(*map(float, point)), 1e-8)
            if classifier.State() == TopAbs_IN:
                return True
        return False

    faces = fluid.Faces()
    errors = []
    resolved = []
    for row, face in zip(inventory, faces, strict=True):
        item = dict(row)
        point, normal = interior_sample(face)
        owners = sorted({history["part_id"] for history in row["source_face_history"]})
        probes = []
        reservoirs = [name for name in owners if name.endswith("_reservoir")]
        materials = [name for name in owners if name in opaque]
        # A control boundary exactly coincident with the tube inner wall may
        # retain only enclosure ancestry. Verify adjacent actual material, never
        # assign every cylinder to paper or treat a covered wall as a reservoir.
        if reservoirs:
            q = point + offset_mm * normal
            materials = sorted(
                set(materials)
                | {
                    name
                    for name, b in bounds.items()
                    if b.xmin - offset_mm <= q[0] <= b.xmax + offset_mm
                    and b.ymin - offset_mm <= q[1] <= b.ymax + offset_mm
                    and b.zmin - offset_mm <= q[2] <= b.zmax + offset_mm
                }
            )
        candidates = []
        for eps in [offset_mm, offset_mm / 10, offset_mm / 100]:
            occupants = [
                name for name in materials if inside(part_classifiers[name], point + eps * normal)
            ]
            probes.append(
                {
                    "offset_mm": eps,
                    "plus_outward_material_occupants": occupants,
                    "minus_outward_is_fluid": inside(fluid_classifiers, point - eps * normal),
                }
            )
            candidates.append(tuple(occupants))
        stable = len(set(candidates)) == 1 and all(
            probe["minus_outward_is_fluid"] for probe in probes
        )
        material_owner = candidates[-1][0] if stable and len(candidates[-1]) == 1 else None
        reservoir_owner = (
            reservoirs[0] if stable and not candidates[-1] and len(reservoirs) == 1 else None
        )
        valid = material_owner is not None or reservoir_owner is not None
        item["part_id"] = material_owner or reservoir_owner
        item["reservoir"] = reservoir_owner is not None
        item["adjacent_control_boundary_material_verified"] = (
            material_owner is not None and material_owner not in owners
        )
        item["ownership_interior_point_mm"] = point.tolist()
        item["void_outward_normal"] = normal.tolist()
        item["material_side_probes"] = probes
        if not valid:
            errors.append(
                {
                    "fluid_face_id": row["fluid_face_id"],
                    "cad_area_mm2": row["cad_area_mm2"],
                    "ancestry": row["source_face_history"],
                    "probes": probes,
                }
            )
        resolved.append(item)
    return resolved, {
        "all_material_owners_verified": not errors,
        "errors": errors,
        "ambiguous_or_unverified_area_mm2": sum(row["cad_area_mm2"] for row in errors),
        "face_center_used": False,
        "actual_material_side_occupancy_used": True,
    }


def physical_surface_groups(
    fluid: Any, inventory: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], np.ndarray]:
    """Suggest isothermal groups without deleting or changing visibility geometry.

    Distinct materials/reservoirs always stay distinct. Cylinders retain radius,
    axis and inward/outward side; planes retain station and oriented normal.
    The primary surface solver owns the final temperature/half-wall mapping.
    """
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    groups: list[dict[str, Any]] = []
    lookup = {}
    face_group = []
    for row, face in zip(inventory, fluid.Faces(), strict=True):
        if row["part_id"] is None:
            raise ValueError("Cannot group an ambiguous material face")
        if "ownership_interior_point_mm" in row:
            point = np.asarray(row["ownership_interior_point_mm"])
            normal = np.asarray(row["void_outward_normal"])
        else:
            point, normal = interior_sample(face)
        adaptor = BRepAdaptor_Surface(face.wrapped)
        kind = face.geomType()
        geometry: dict[str, Any] = {"kind": kind}
        if kind == "CYLINDER":
            cylinder = adaptor.Cylinder()
            axis = cylinder.Axis()
            origin = axis.Location()
            direction = axis.Direction()
            center = np.array([origin.X(), origin.Y(), origin.Z()])
            vector = np.array([direction.X(), direction.Y(), direction.Z()])
            # Canonical axis point nearest the origin and deterministic direction.
            if vector[np.argmax(abs(vector))] < 0:
                vector = -vector
            center -= np.dot(center, vector) * vector
            radial = point - center - np.dot(point - center, vector) * vector
            geometry.update(
                radius_mm=round(cylinder.Radius(), 7),
                axis_point_mm=(np.round(center, 7) + 0.0).tolist(),
                axis_direction=(np.round(vector, 9) + 0.0).tolist(),
                void_normal_radial_sign=int(np.sign(np.dot(normal, radial))),
            )
        elif kind == "PLANE":
            geometry.update(
                normal=(np.round(normal, 9) + 0.0).tolist(),
                normal_station_mm=round(float(np.dot(normal, point)), 7) + 0.0,
            )
        elif kind == "SPHERE":
            sphere = adaptor.Sphere()
            center = sphere.Location()
            geometry.update(
                radius_mm=round(sphere.Radius(), 7),
                center_mm=[round(center.X(), 7), round(center.Y(), 7), round(center.Z(), 7)],
                void_normal_radial_sign=int(
                    np.sign(np.dot(normal, point - np.array([center.X(), center.Y(), center.Z()])))
                ),
            )
        else:
            geometry["fluid_face_id"] = row["fluid_face_id"]
        import json

        key = json.dumps([row["part_id"], geometry], sort_keys=True)
        if key not in lookup:
            lookup[key] = len(groups)
            groups.append(
                {
                    "group_id": len(groups),
                    "part_id": row["part_id"],
                    "physical_surface_family": geometry,
                    "fluid_face_ids": [],
                    "reservoir": row["reservoir"],
                    "temperature_assignment_available": False,
                }
            )
        index = lookup[key]
        groups[index]["fluid_face_ids"].append(row["fluid_face_id"])
        face_group.append(index)
    return groups, np.asarray(face_group, dtype=np.int64)


class FirstHitLocator:
    """VTK first opaque triangle hit; all analysis geometry stays present."""

    def __init__(self, vertices_mm: np.ndarray, triangles: np.ndarray) -> None:
        import vtk  # type: ignore[import-untyped]
        from vtk.util.numpy_support import (  # type: ignore[import-untyped]
            numpy_to_vtk,
            numpy_to_vtkIdTypeArray,
        )

        vtk.vtkSMPTools.Initialize(1)
        points = vtk.vtkPoints()
        points.SetData(numpy_to_vtk(np.ascontiguousarray(vertices_mm), deep=True))
        cells = vtk.vtkCellArray()
        cells.SetData(
            numpy_to_vtkIdTypeArray(
                np.arange(0, 3 * len(triangles) + 1, 3, dtype=np.int64), deep=True
            ),
            numpy_to_vtkIdTypeArray(np.ascontiguousarray(triangles).ravel(), deep=True),
        )
        self.poly = vtk.vtkPolyData()
        self.poly.SetPoints(points)
        self.poly.SetPolys(cells)
        self.locator = vtk.vtkStaticCellLocator()
        self.locator.SetDataSet(self.poly)
        self.locator.BuildLocator()
        self.t = vtk.mutable(0.0)
        self.point = [0.0, 0.0, 0.0]
        self.uv = [0.0, 0.0, 0.0]
        self.sub = vtk.mutable(0)
        self.cell = vtk.mutable(0)
        self.max_distance = float(np.linalg.norm(np.ptp(vertices_mm, axis=0)) * 3)

    def hit(self, start: np.ndarray, direction: np.ndarray) -> tuple[int, float]:
        end = start + direction * self.max_distance
        found = self.locator.IntersectWithLine(
            start, end, 1e-9, self.t, self.point, self.uv, self.sub, self.cell
        )
        return (int(self.cell), float(self.t) * self.max_distance) if found else (-1, float("inf"))


def sample_first_hit(
    mesh: dict[str, Any],
    face_group: np.ndarray,
    ray_budget: int,
    minimum_per_group: int,
    seed: int,
    offset_mm: float,
    max_seconds: float = 600,
) -> dict[str, Any]:
    """Cosine-weighted first-hit estimator with raw counts and no reciprocity fix."""
    started = time.monotonic()
    vertices = mesh["vertices_mm"]
    triangles = mesh["triangles"]
    areas = mesh["triangle_area_mm2"]
    triangle_group = face_group[mesh["triangle_face_index"]]
    groups = int(face_group.max()) + 1
    group_area = np.bincount(triangle_group, weights=areas, minlength=groups)
    base = minimum_per_group * groups
    if base > ray_budget:
        raise ValueError("Ray budget cannot cover every preserved surface group")
    counts = np.full(groups, minimum_per_group, dtype=np.int64)
    extra = (ray_budget - base) * group_area / group_area.sum()
    counts += np.floor(extra).astype(np.int64)
    order = np.argsort(-(extra - np.floor(extra)))
    counts[order[: ray_budget - int(counts.sum())]] += 1
    hits = np.zeros((groups, groups), dtype=np.int64)
    locator = FirstHitLocator(vertices, triangles)
    rng = np.random.default_rng(seed)
    digest = hashlib.sha256()
    escaped = 0
    near = 0
    for source in range(groups):
        ids = np.flatnonzero(triangle_group == source)
        cdf = np.cumsum(areas[ids])
        cdf /= cdf[-1]
        chosen = ids[np.searchsorted(cdf, rng.random(counts[source]))]
        bary = rng.random((counts[source], 2))
        root = np.sqrt(bary[:, 0])
        points = (
            (1 - root)[:, None] * vertices[triangles[chosen, 0]]
            + (root * (1 - bary[:, 1]))[:, None] * vertices[triangles[chosen, 1]]
            + (root * bary[:, 1])[:, None] * vertices[triangles[chosen, 2]]
        )
        normal = -mesh["outward_triangle_normal"][chosen]
        reference = np.tile([0.0, 0.0, 1.0], (len(chosen), 1))
        reference[abs(normal[:, 2]) > 0.9] = [1.0, 0.0, 0.0]
        tangent = np.cross(normal, reference)
        tangent /= np.linalg.norm(tangent, axis=1)[:, None]
        bitangent = np.cross(normal, tangent)
        uv = rng.random((len(chosen), 2))
        cosine = np.sqrt(uv[:, 0])
        sine = np.sqrt(1 - uv[:, 0])
        azimuth = 2 * np.pi * uv[:, 1]
        direction = (
            cosine[:, None] * normal
            + (sine * np.cos(azimuth))[:, None] * tangent
            + (sine * np.sin(azimuth))[:, None] * bitangent
        )
        target = np.full(len(chosen), -1, dtype=np.int64)
        for index, (point, ray, n) in enumerate(zip(points, direction, normal, strict=True)):
            if index % 1024 == 0 and time.monotonic() - started > max_seconds:
                raise RuntimeError("First-hit ray time budget exceeded")
            cell, distance = locator.hit(point + offset_mm * n, ray)
            target[index] = cell
            if cell < 0:
                escaped += 1
                continue
            if distance < offset_mm * 0.5:
                near += 1
            hits[source, triangle_group[cell]] += 1
        digest.update(chosen.tobytes())
        digest.update(points.tobytes())
        digest.update(direction.tobytes())
        digest.update(target.tobytes())
    view = hits / counts[:, None]
    area_m2 = group_area * 1e-6
    exchange = area_m2[:, None] * view
    difference = exchange - exchange.T
    return {
        "hits": hits,
        "counts": counts,
        "raw_view_factors": view,
        "group_area_m2": area_m2,
        "ray_trace_sha256": digest.hexdigest(),
        "rays": int(counts.sum()),
        "escaped_rays": escaped,
        "near_origin_hits": near,
        "max_row_closure_error": float(abs(view.sum(axis=1) - 1).max()),
        "raw_area_weighted_reciprocity_l1": float(abs(difference).sum() / (2 * area_m2.sum())),
        "max_absolute_exchange_reciprocity_m2": float(abs(difference).max()),
        "reciprocity_projection_applied": False,
        "elapsed_s": time.monotonic() - started,
        "zero_hit_probability_upper95_by_source": -np.log(0.05) / counts,
    }


def aggregate_visibility(
    operator: dict[str, Any], sources: list[int], targets: list[int], components: int
) -> dict[str, Any]:
    """Area-weighted direct visibility with conservative binomial intervals.

    Each source row is a binomial target-union count. Exact Clopper-Pearson
    bounds use tail 0.05/(2*components), allowing a Bonferroni joint 95% bound
    over the source rows in one before/after comparison. No independence is
    required between rows or between designs. Geometry/mesh error is separate.
    """
    from scipy.stats import beta

    if (
        not sources
        or not targets
        or components < len(sources)
        or len(set(sources)) != len(sources)
        or len(set(targets)) != len(targets)
    ):
        raise ValueError("Explicit nonempty visibility source/target rows required")
    counts = operator["counts"][sources]
    hits = operator["hits"][np.ix_(sources, targets)].sum(axis=1)
    area = operator["group_area_m2"][sources]
    if (
        (counts <= 0).any()
        or (hits < 0).any()
        or (hits > counts).any()
        or not np.isfinite(area).all()
        or (area <= 0).any()
    ):
        raise ValueError("Invalid visibility counts or source areas")
    probability = hits / counts
    tail = 0.05 / (2 * components)
    lower = np.zeros(len(sources))
    upper = np.ones(len(sources))
    mask = hits > 0
    lower[mask] = beta.ppf(tail, hits[mask], counts[mask] - hits[mask] + 1)
    mask = hits < counts
    upper[mask] = beta.ppf(1 - tail, hits[mask] + 1, counts[mask] - hits[mask])
    exchange = float(np.dot(area, probability))
    return {
        "source_group_ids": sources,
        "target_group_ids": targets,
        "source_area_m2": float(area.sum()),
        "target_area_m2": float(operator["group_area_m2"][targets].sum()),
        "source_rays": int(counts.sum()),
        "target_hits": int(hits.sum()),
        "area_weighted_F": exchange / float(area.sum()),
        "F_confidence_bound": [
            float(np.dot(area, lower) / area.sum()),
            float(np.dot(area, upper) / area.sum()),
        ],
        "direct_exchange_area_m2": exchange,
        "exchange_area_confidence_bound_m2": [
            float(np.dot(area, lower)),
            float(np.dot(area, upper)),
        ],
        "component_binomial_tail": tail,
        "component_count_for_joint95_bound": components,
    }


def compare_ring_end_visibility(
    before_operator: Path,
    before_groups: Path,
    after_operator: Path,
    after_groups: Path,
    contact_ledger: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare combined candidates without inheriting visibility or temperatures."""
    import json

    groups = [json.loads(p.read_text()) for p in [before_groups, after_groups]]
    operators = []
    for path, group in zip([before_operator, after_operator], groups, strict=True):
        with np.load(path, allow_pickle=False) as archive:
            op = {name: archive[name] for name in archive.files}
        if op["hits"].shape != (len(group), len(group)) or (op["counts"] <= 0).any():
            raise ValueError("Visibility operator/group dimensions or counts incompatible")
        operators.append(op)

    def target_ids(group: list[dict[str, Any]], entry: dict[str, Any]) -> list[int]:
        wanted_normal = 1 if entry["side"] == "front" else -1
        ids = []
        for item in group:
            family = item["physical_surface_family"]
            if item["part_id"] != "motor_mount" or family["kind"] != "PLANE":
                continue
            normal_z = family["normal"][2]
            if normal_z * wanted_normal < 0.999999:
                continue
            if abs(family["normal_station_mm"] / normal_z - 1000 * entry["ring_face_m"]) < 1e-4:
                ids.append(item["group_id"])
        if not ids:
            raise ValueError(f"Actual exposed ring-end surface unavailable: {entry['baffle_id']}")
        return ids

    def shield(item: dict[str, Any]) -> bool:
        return bool(
            item["part_id"].startswith(("motor_radiant_shield", "additional_shield_"))
            and item["physical_surface_family"]["kind"] == "CYLINDER"
        )

    def key(item: dict[str, Any]) -> str:
        return json.dumps([item["part_id"], item["physical_surface_family"]], sort_keys=True)

    common = [
        {key(item): item for item in group if item["part_id"] == "motor" or shield(item)}
        for group in groups
    ]
    categories: list[tuple[str, list[int], list[int]]] = []
    predicates: list[tuple[str, Callable[[dict[str, Any]], bool]]] = [
        ("motor_envelope_all_exposed_sides", lambda g: bool(g["part_id"] == "motor")),
        ("longitudinal_shield_cylinders_both_sides", shield),
    ]
    for label, predicate in predicates:
        categories.append(
            (
                label,
                [g["group_id"] for g in groups[0] if predicate(g)],
                [g["group_id"] for g in groups[1] if predicate(g)],
            )
        )
    for item_key in sorted(set(common[0]) & set(common[1])):
        categories.append(
            (item_key, [common[0][item_key]["group_id"]], [common[1][item_key]["group_id"]])
        )
    comparisons = []
    new_baffle_views = []
    for entry in contact_ledger:
        target = [target_ids(group, entry) for group in groups]
        for label, old_ids, new_ids in categories:
            components = len(old_ids) + len(new_ids)
            old = aggregate_visibility(operators[0], old_ids, target[0], components)
            new = aggregate_visibility(operators[1], new_ids, target[1], components)
            comparisons.append(
                {
                    "ring_index": entry["ring_index"],
                    "side": entry["side"],
                    "ring_face_m": entry["ring_face_m"],
                    "source": label,
                    "before": old,
                    "after": new,
                    "delta_F_after_minus_before": new["area_weighted_F"] - old["area_weighted_F"],
                    "joint95_delta_F_bound": [
                        new["F_confidence_bound"][0] - old["F_confidence_bound"][1],
                        new["F_confidence_bound"][1] - old["F_confidence_bound"][0],
                    ],
                    "delta_exchange_area_m2": new["direct_exchange_area_m2"]
                    - old["direct_exchange_area_m2"],
                    "joint95_delta_exchange_bound_m2": [
                        new["exchange_area_confidence_bound_m2"][0]
                        - old["exchange_area_confidence_bound_m2"][1],
                        new["exchange_area_confidence_bound_m2"][1]
                        - old["exchange_area_confidence_bound_m2"][0],
                    ],
                }
            )
        for item in groups[1]:
            family = item["physical_surface_family"]
            if (
                item["part_id"] == entry["baffle_id"]
                and family["kind"] == "PLANE"
                and abs(family["normal"][2]) > 0.999999
            ):
                new_baffle_views.append(
                    {
                        "baffle_id": entry["baffle_id"],
                        "source_surface_family": family,
                        "ring_index": entry["ring_index"],
                        "side": entry["side"],
                        "after_only": aggregate_visibility(
                            operators[1], [item["group_id"]], target[1], 1
                        ),
                        "baseline_surface_did_not_exist": True,
                        "physical_parallel_path_reference": entry["baffle_id"],
                    }
                )
    return {
        "source_sha256": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [before_operator, before_groups, after_operator, after_groups]
        },
        "comparisons": comparisons,
        "new_baffle_face_to_adjacent_ring_views": new_baffle_views,
        "physical_parallel_paths_once_per_baffle": {
            entry["baffle_id"]: {
                "parallel_air_w_k_estimate": entry[
                    "parallel_axial_air_gap_conductance_w_k_estimate"
                ],
                "bulk_support_w_k_estimate": entry["bulk_support_conductance_w_k_estimate"],
                "path": entry["path"],
                "temperature_assignment_unavailable": True,
            }
            for entry in contact_ledger
        },
        "scope": "direct diffuse first-hit visibility of combined candidates; shortened wraps and new baffles both changed; no isolated causal or thermal benefit claim",
        "confidence": "Exact component Clopper-Pearson with Bonferroni joint95% per before/after comparison, area-weighted bounds; not simultaneous across every reported comparison; mesh/source uncertainty separate",
        "mesh_errors_separate": True,
        "temperature_assignment_available": False,
        "thermal_acceptance_passed": False,
    }
