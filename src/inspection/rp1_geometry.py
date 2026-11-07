"""Bounded AD1 inspection meshes, never a vehicle model or manufacturing release.

The frozen definition supplies the corrected slot/tab dimensions. Integral panels,
tabs and gussets get separate stable source IDs, avoiding the legacy fin generator's
combined solids and stale tab dimensions. No mass or inertia is calculated.
"""

from __future__ import annotations

import copy
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from src.api import rp1_inspection

FOLDER = "output/rp1-inspection-geometry"
EVIDENCE = "docs/studies/rp1-inspection-geometry-20261107/manifest.json"
GEOMETRY_ID = "rp1-ad1-v2-inspection-geometry-v1"
FRAME = "X=body+y, Y=length-station, Z=body-z"
GENERATOR_SOURCES = (
    "src/inspection/rp1_geometry.py",
    "src/cad/parts.py",
    "src/cad/assembly.py",
    "src/vehicle/geometry.py",
)
SOURCE_SOLIDS = {
    "nose",
    "body",
    "fin_set",
    "fin_tabs",
    "motor_tube",
    "aft_ring",
    "nose_anchor_plate",
    "upper_body",
    "body_splice",
    "root_gussets",
}
MISSING = {
    "mount_external_shield": "Thermal sectors and terminations undefined; annulus would conflict with tabs.",
    "rp1_kevlar_wrap": "Dressed choker, knots, moving cord route and pack geometry unavailable; stale stowage box is not an installed route.",
    "rail_buttons": "Actual guide hardware and two attachment stations are unconfirmed; generic budget box is not installed geometry.",
    "rail_backers": "Backer shape, fasteners and actual guide stations unconfirmed.",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sources(root: Path) -> dict[str, str]:
    return {
        **rp1_inspection.PINS,
        **{path: sha((root / path).read_bytes()) for path in GENERATOR_SOURCES},
    }


def audit(root: Path) -> dict[str, Any]:
    """Classify every source record before loading a geometry dependency."""
    source = rp1_inspection.build(root)
    geometry_revision = sha(json.dumps(sources(root), sort_keys=True).encode())
    rows = []
    for part in source["parts"]:
        pid, raw = part["id"], part["raw"]
        role = raw["cad"]["role"]
        if pid in MISSING:
            maturity, explanation = "missing_geometry", MISSING[pid]
        elif pid in SOURCE_SOLIDS:
            maturity = "source_dimensioned"
            explanation = "Ideal source-dimensioned inspection solid; estimated dimensions and unverified installed joints."
        elif role == "distributed_budget":
            maturity = "mass_allowance"
            explanation = "Separate source mass/process allowance; no unique installed solid or qualified spatial distribution."
        else:
            maturity = "simplified_envelope"
            explanation = "Nominal source bounding envelope; supplier details, fit and installed form unverified."
        if pid == "forward_ring":
            explanation = "Ideal notched annulus; proposed 2 mm edge roundovers omitted. Not a finished passage or fit model."
        if pid == "motor_retainer":
            explanation = "Historical nominal annular envelope only; cap/sleeve details and current exact motor fit unavailable."
        rows.append(
            {
                "id": pid,
                "maturity": maturity,
                "description": explanation,
                "source": {
                    "path": rp1_inspection.SPEC,
                    "sha256": rp1_inspection.PINS[rp1_inspection.SPEC],
                    "part_id": pid,
                },
                "definition_source": {
                    "path": rp1_inspection.DEFINITION,
                    "sha256": rp1_inspection.PINS[rp1_inspection.DEFINITION],
                },
                "position_m": raw["position_m"],
                "lateral_offset_m": raw["lateral_offset_m"],
                "source_dimensions": raw["geometry"],
                "mesh": None,
                "bounds_m": None,
                "physical_verification": "open",
                "inspection_shape_sha256": sha(
                    json.dumps(
                        {"part_id": pid, "geometry_revision": geometry_revision}, sort_keys=True
                    ).encode()
                ),
            }
        )
    return {"source": source, "parts": rows}


def _local(raw: dict[str, Any], definition: dict[str, Any], parts: dict[str, Any]) -> Any:
    # Imports stay within explicit export, never a request to the read-only adapter.
    from src.cad.parts import box, compound, cq, local_shape, tube
    from src.vehicle.schema import Part

    pid, g = raw["id"], raw["geometry"]
    r = float(g.get("radius_m", 0)) * 1000
    if pid == "fin_tabs":
        dims = definition["fin_joints"]
        inner = dims["tab_inner_flat_radius_mm"]
        depth = g["bbox_m"][1] * 1000
        tab = box(depth, g["bbox_m"][2] * 1000, dims["tab_length_mm"]).translate(
            (inner + depth / 2, 0, 0)
        )
        return compound([tab.rotate((0, 0, 0), (0, 0, 1), a) for a in (0, 120, 240)])
    if pid == "root_gussets":
        dims = definition["fin_joints"]
        r = parts["fin_set"]["geometry"]["radius_m"] * 1000
        t = parts["fin_set"]["geometry"]["thickness_m"] * 1000
        body = cq.Solid.makeCylinder(r, dims["root_length_mm"] + 2, cq.Vector(0, 0, -1))
        wedges: list[Any] = []
        for side in (-1, 1):
            # Same cylindrical saddle convention as the existing source CAD generator.
            wedge = (
                cq.Workplane("XY")
                .polyline(
                    [
                        (r - 1, side * t / 2),
                        (r - 1, side * (t / 2 + dims["gusset_base_width_mm"])),
                        (r + dims["gusset_height_mm"], side * t / 2),
                    ]
                )
                .close()
                .extrude(dims["root_length_mm"])
                .val()
                .cut(body)
            )
            wedges.extend(wedge.rotate((0, 0, 0), (0, 0, 1), a) for a in (0, 120, 240))
        return compound(wedges)
    if pid == "forward_ring":
        route = definition["route"]
        shape = tube(r, g["inner_radius_m"] * 1000, g["length_m"] * 1000)
        cutter = (
            box(route["passage_depth_mm"] + 1, route["passage_width_mm"], g["length_m"] * 1000 + 2)
            .translate((g["inner_radius_m"] * 1000 + (route["passage_depth_mm"] - 1) / 2, 0, -1))
            .rotate((0, 0, 0), (0, 0, 1), route["passage_angle_deg"])
        )
        return shape.cut(cutter)
    if pid in SOURCE_SOLIDS:
        projected = copy.deepcopy(raw)
        if pid == "body":
            projected["cad"]["parameters"]["fin_slot_width_mm"] = definition["fin_joints"][
                "external_slot_width_mm"
            ]
        if pid == "fin_set":
            # Separate records own the integral tab and six gussets, exactly once.
            projected["cad"]["parameters"] = {}
        return local_shape(Part.model_validate(projected))
    if "bbox_m" in g:
        length, width, height = g["bbox_m"]
        return box(width * 1000, height * 1000, length * 1000)
    # Purchased axisymmetric envelopes are intentionally featureless.
    if "inner_radius_m" in g:
        return tube(r, g["inner_radius_m"] * 1000, g["length_m"] * 1000)
    return cq.Solid.makeCylinder(r, g["length_m"] * 1000, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))


def export(root: Path, *, cpu_limit_seconds: float = 300) -> dict[str, Any]:
    """One bounded CPU geometry export; unsupported/tool errors stop the packet."""
    import yaml

    from src.cad.assembly import mesh, trimesh

    started = time.process_time()
    frozen = sources(root)
    projection = audit(root)
    source, rows = projection["source"], projection["parts"]
    definition = yaml.safe_load((root / rp1_inspection.DEFINITION).read_bytes())
    folder = root / FOLDER
    (folder / "parts").mkdir(parents=True, exist_ok=True)
    scene = trimesh.Scene()
    mesh_bounds = []
    originals = {p["id"]: p["raw"] for p in source["parts"]}
    for raw, row in zip(originals.values(), rows, strict=True):
        if row["maturity"] in ("mass_allowance", "missing_geometry"):
            continue
        if time.process_time() - started > cpu_limit_seconds:
            raise TimeoutError(
                "AD1 inspection geometry CPU budget exhausted; stop, no automatic retry"
            )
        shape = _local(raw, definition, originals)
        shape = shape.translate(
            (
                raw["lateral_offset_m"][0] * 1000,
                -raw["lateral_offset_m"][1] * 1000,
                raw["position_m"] * 1000,
            )
        )
        if not shape.isValid():
            raise ValueError(f"Invalid inspection shape: {row['id']}; stop, no automatic retry")
        display = mesh(shape, source["geometry"]["length_m"], raw["cad"]["color"])
        relative = f"parts/{row['id']}.glb"
        path = folder / relative
        scene.add_geometry(display, node_name=row["id"], geom_name=row["id"])
        path.write_bytes(trimesh.Scene(display).export(file_type="glb"))
        row["mesh"] = {
            "path": f"{FOLDER}/{relative}",
            "sha256": sha(path.read_bytes()),
            "units": "m",
        }
        row["bounds_m"] = display.bounds.tolist()
        mesh_bounds.append(display.bounds)
    import numpy as np

    scene_path = folder / "assembly.glb"
    scene_path.write_bytes(scene.export(file_type="glb"))
    counts = dict(Counter(row["maturity"] for row in rows))
    result = {
        "schema_version": 1,
        "id": rp1_inspection.ID,
        "geometry_id": GEOMETRY_ID,
        "identity": {
            **source["identity"],
            "inspection_geometry_sha256": sha(
                json.dumps({"sources": frozen, "geometry_id": GEOMETRY_ID}, sort_keys=True).encode()
            ),
        },
        "sources": frozen,
        "viewer_frame": FRAME,
        "units": {
            "source": "m except explicitly named mm definition fields",
            "cad": "mm",
            "glb": "m",
            "bounds": "m",
        },
        "origin": "Viewer origin at aft datum station length_m; nose tip at [0,length_m,0]",
        "source_datum": definition["route"]["datum"],
        "length_m": source["geometry"]["length_m"],
        "bounds_m": [
            np.min([b[0] for b in mesh_bounds], axis=0).tolist(),
            np.max([b[1] for b in mesh_bounds], axis=0).tolist(),
        ],
        "coverage": {
            "source_parts": len(rows),
            "mesh_parts": sum(row["mesh"] is not None for row in rows),
            "by_maturity": counts,
            "complete_installed_geometry": False,
        },
        "assembly": {"path": f"{FOLDER}/assembly.glb", "sha256": sha(scene_path.read_bytes())},
        "parts": rows,
        "status": "Inspection representation only; source estimates, simplified envelopes and explicit omissions",
        "engineering_accepted": False,
        "flight_ready": False,
        "mass_or_inertia_generated": False,
        "browser_verified": False,
    }
    if time.process_time() - started > cpu_limit_seconds:
        raise TimeoutError("AD1 inspection geometry CPU budget exhausted; stop, no automatic retry")
    if sources(root) != frozen:
        raise ValueError("Geometry sources changed during export")
    (folder / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
