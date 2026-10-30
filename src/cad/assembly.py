"""Deterministic CAD export, material mass and interface diagnostics.

STEP retains millimetres; viewer meshes are metres, X=body+y, Y=length-station,
Z=body-z. Mesh transforms are a display convention, never a second physics model.
Intersecting rigid parts are reported by exact BRep volume, not a screenshot.
Soft/budget envelopes are explicitly excluded from rigid collision validation.
Reference: CadQuery Shape/Assembly and trimesh glTF exporter documentation.
"""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

cq: Any = importlib.import_module("cadquery")
import numpy as np

trimesh: Any = importlib.import_module("trimesh")

from src.cad.parts import local_shape, properties, shape_digest
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import Vehicle


def print_layout(
    shape: Any, rotation: tuple[float, float, float]
) -> tuple[Any, list[dict[str, Any]]]:
    """Orient and bed-pack separate kit solids; never change assembly geometry."""
    transformed = shape
    for axis, angle in zip([(1, 0, 0), (0, 1, 0), (0, 0, 1)], rotation):
        if angle:
            transformed = transformed.rotate((0, 0, 0), axis, angle)
    packed = []
    placements = []
    x = y = row_height = 0.0
    for i, solid in enumerate(transformed.Solids()):
        bbox = solid.BoundingBox()
        if x and x + bbox.xlen > 220:
            x = 0
            y += row_height + 5
            row_height = 0
        translation = (x - bbox.xmin, y - bbox.ymin, -bbox.zmin)
        packed.append(solid.translate(translation))
        placements.append({"piece": i + 1, "rotation_deg": rotation, "translation_mm": translation})
        x += bbox.xlen + 5
        row_height = max(row_height, bbox.ylen)
    return cq.Compound.makeCompound(packed), placements


def mesh(shape: Any, total_length_m: float, color: str) -> Any:
    vertices, triangles = shape.tessellate(0.15, 0.15)
    points = np.array([[v.x * 1e-3, total_length_m - v.z * 1e-3, v.y * 1e-3] for v in vertices])
    result = trimesh.Trimesh(vertices=points, faces=np.asarray(triangles), process=False)
    result.visual.face_colors = trimesh.visual.color.hex_to_rgba(color)
    return result


def export_vehicle(
    vehicle: Vehicle, folder: Path, export: bool = True
) -> tuple[dict[str, Any], dict[str, Any]]:
    folder.mkdir(parents=True, exist_ok=True)
    parts_dir = folder / "parts"
    parts_dir.mkdir(exist_ok=True)
    scene = trimesh.Scene()
    solids = {}
    rows = []
    local = {}
    for part in vehicle.parts:
        assert part.cad
        shape = local_shape(part)
        local[part.id] = shape
        placed = shape.translate(
            (
                part.lateral_offset_m[0] * 1000,
                -part.lateral_offset_m[1] * 1000,
                part.position_m * 1000,
            )
        )
        solids[part.id] = placed
        props = properties(part, shape)
        geometric = part.cad.mass_basis == "volume_density"
        mass = (
            props["volume_m3"] * DENSITY_KG_M3[part.material]
            if geometric
            else part.resolved_mass_kg
        )
        delta = abs(mass / part.resolved_mass_kg - 1)
        bbox = shape.BoundingBox()
        printable = part.build and part.build.method == "printed"
        print_shape, layout = (
            print_layout(shape, part.print_settings.rotation_deg)
            if printable and part.print_settings
            else (shape, [])
        )
        print_bbox = print_shape.BoundingBox()
        row = {
            "id": part.id,
            "type": part.type,
            "parent": part.parent,
            "method": part.build.method if part.build else None,
            "role": part.cad.role,
            "moving_group": part.cad.moving_group,
            "mass_basis": part.cad.mass_basis,
            "cad_mass_kg": mass,
            "spec_mass_kg": part.resolved_mass_kg,
            "mass_relative_error": delta,
            "mass_within_10pct": delta <= 0.1,
            "properties": props,
            "shape_sha256": shape_digest(part),
            "bbox_mm": [bbox.xlen, bbox.ylen, bbox.zlen],
            "print_layout": layout,
            "print_bbox_mm": [print_bbox.xlen, print_bbox.ylen, print_bbox.zlen],
            "valid_solid": shape.isValid() and shape.Volume() > 0,
            "print_fits": not printable
            or (print_bbox.xlen <= 220 and print_bbox.ylen <= 220 and print_bbox.zlen <= 250),
            "learn": part.learn,
            "notes": part.cad.notes,
            "material": part.material,
            "color": part.cad.color,
            "mesh": f"parts/{part.id}.glb",
            "step": f"parts/{part.id}.step",
            "stl": f"parts/{part.id}.stl",
        }
        rows.append(row)
        if export:
            display = mesh(placed, vehicle.airframe["length_m"], part.cad.color)
            scene.add_geometry(display, node_name=part.id, geom_name=part.id)
            trimesh.Scene(display).export(parts_dir / (part.id + ".glb"))
            cq.exporters.export(shape, str(parts_dir / (part.id + ".step")))
            cq.exporters.export(
                print_shape,
                str(parts_dir / (part.id + ".stl")),
                tolerance=0.15,
                angularTolerance=0.15,
            )
    manifest = {
        "vehicle": vehicle.id,
        "identity": {
            "configuration_id": vehicle.id,
            "resolved_spec_sha256": hashlib.sha256(
                vehicle.model_dump_json(by_alias=True).encode()
            ).hexdigest(),
            "cad_revision_sha256": hashlib.sha256(
                b"".join(p.read_bytes() for p in sorted(Path("src/cad").glob("*.py")))
            ).hexdigest(),
            "part_shape_sha256": {r["id"]: r["shape_sha256"] for r in rows},
        },
        "units": {"step": "mm", "stl": "mm", "glb": "m"},
        "viewer_frame": "X=body+y, Y=length-station, Z=body-z",
        "parts": rows,
        "mass_benchmark_passed": all(r["mass_within_10pct"] for r in rows),
        "print_volume_passed": all(r["print_fits"] for r in rows),
        "flight_ready": False,
    }
    if export:
        scene.export(folder / "assembly.glb")
        cq.exporters.export(
            cq.Compound.makeCompound(list(solids.values())), str(folder / "assembly.step")
        )
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (folder / "parts.md").write_text(
            "# "
            + vehicle.name
            + "\n\nPreliminary CAD; no structural, thermal or flight release.\n\n"
            + "\n\n".join(
                "## "
                + r["id"]
                + "\n\n"
                + r["learn"]
                + "\n\nMass basis: "
                + r["mass_basis"]
                + "; "
                + r["notes"]
                for r in rows
            )
            + "\n"
        )
    return manifest, solids


def rigid_intersections(vehicle: Vehicle, solids: dict[str, Any]) -> list[dict[str, Any]]:
    parts = [
        p
        for p in vehicle.parts
        if p.cad and p.cad.role not in ("soft_stowage", "distributed_budget")
    ]
    collisions = []
    for i, a in enumerate(parts):
        for b in parts[i + 1 :]:
            sa, sb = solids[a.id], solids[b.id]
            ba, bb = sa.BoundingBox(), sb.BoundingBox()
            if any(
                getattr(ba, ax + "max") <= getattr(bb, ax + "min") + 1e-6
                or getattr(bb, ax + "max") <= getattr(ba, ax + "min") + 1e-6
                for ax in ["x", "y", "z"]
            ):
                continue
            volume = sa.intersect(sb).Volume()
            if volume > 0.05:
                collisions.append({"a": a.id, "b": b.id, "intersection_mm3": volume})
    return collisions
