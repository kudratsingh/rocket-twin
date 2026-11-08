"""Optional source-detail inspection assets, separate from frozen core geometry.

Only three internal exemplars are admitted. Three annular mesh replacements add
sampling/layer readability; undefined hardware and electronic internals stay missing.
No mass, inertia, structural solve or canonical vehicle geometry is produced.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import time
from pathlib import Path
from typing import Any

import yaml

from src.api import rp1_geometry, rp1_inspection

ID = "rp1-ad1-optional-source-detail-v1"
FOLDER = "web/public/engineering-workbench/rp1-detail"
CATALOG = "docs/studies/frontend-design-ux-20261108/detail-catalog.json"
CORE_GEOMETRY = "238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608"
REPLACEMENTS = ("forward_ring", "motor_tube", "aft_ring")
CODE_SOURCES = ("src/inspection/rp1_detail.py", "scripts/wo04_rp1_detail_export.py")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source(path: str, locator: str) -> dict[str, str]:
    return {"path": path, "sha256": rp1_inspection.PINS[path], "locator": locator}


def _position(x_mm: float, y_mm: float, station_mm: float, length_m: float) -> list[float]:
    return [x_mm / 1000, length_m - station_mm / 1000, y_mm / 1000]


def _dimension(
    pid: str,
    key: str,
    label: str,
    value: float,
    start: list[float],
    end: list[float],
    source: dict[str, str],
) -> dict[str, Any]:
    return {
        "id": key,
        "kind": "dimension",
        "part_id": pid,
        "label": label,
        "value": value,
        "units": "mm",
        "from_m": start,
        "to_m": end,
        "source": source,
        "status": "recorded nominal estimate/proposal",
        "annotation_only": True,
        "contributes_geometry_bounds": False,
    }


def catalog(root: Path) -> dict[str, Any]:
    """Read/verify all26 current assets and expose only source-supported refinements."""
    trimesh: Any = importlib.import_module("trimesh")

    document = rp1_inspection.build(root)
    core = rp1_geometry.build(root)
    if core["identity"]["inspection_geometry_sha256"] != CORE_GEOMETRY:
        raise ValueError("Optional detail/core geometry tuple mismatch")
    original = {p["id"]: p["raw"] for p in document["parts"]}
    definition = yaml.safe_load((root / rp1_inspection.DEFINITION).read_bytes())
    frozen = {**rp1_inspection.PINS, **{p: sha((root / p).read_bytes()) for p in CODE_SOURCES}}
    source_tuple = {
        "configuration_id": rp1_inspection.ID,
        "specification_sha256": rp1_inspection.PINS[rp1_inspection.SPEC],
        "inspection_geometry_sha256": CORE_GEOMETRY,
    }
    detail_sha = sha(
        json.dumps(
            {"id": ID, "sources": frozen, "source_tuple": source_tuple}, sort_keys=True
        ).encode()
    )
    audit = []
    for row in core["parts"]:
        if row["mesh"] is None:
            continue
        path = root / row["mesh"]["path"]
        raw = path.read_bytes()
        if sha(raw) != row["mesh"]["sha256"]:
            raise ValueError("Core mesh changed during detail audit")
        mesh = trimesh.load(path, force="scene").to_geometry()
        geometry = original[row["id"]]["geometry"]
        box_envelope = row["maturity"] == "simplified_envelope" and "bbox_m" in geometry
        disposition = (
            "Optional finer annulus/bore sampling; known source features only"
            if row["id"] in REPLACEMENTS
            else (
                "Exact planar source faces; extra tessellation would not add physical detail"
                if row["id"] in ("fin_set", "fin_tabs")
                else (
                    "Source supplies only a bounding envelope; supplier internals are unavailable"
                    if box_envelope
                    else "Retain frozen core; source/physical detail remains as recorded"
                )
            )
        )
        audit.append(
            {
                "id": row["id"],
                "maturity": row["maturity"],
                "mesh_sha256": row["mesh"]["sha256"],
                "inspection_shape_sha256": row["inspection_shape_sha256"],
                "vertices": len(mesh.vertices),
                "triangles": len(mesh.faces),
                "actual_bounds_m": mesh.bounds.tolist(),
                "box_envelope": box_envelope,
                "disposition": disposition,
            }
        )
    if len(audit) != 26:
        raise ValueError("Optional detail requires exact26-mesh core coverage")
    length = document["geometry"]["length_m"]
    ring = original["forward_ring"]
    g = ring["geometry"]
    station = ring["position_m"] * 1000
    ro, ri, height = g["radius_m"] * 1000, g["inner_radius_m"] * 1000, g["length_m"] * 1000
    route = definition["route"]
    # Two6mm stock layers+.2mm bond are explicit source notes, not invented ply internals.
    if "Two6mm plies+.2mm glue" not in ring["cad"]["notes"] or abs(height - 12.2) > 1e-8:
        raise ValueError("Forward-ring layer source unavailable")
    annotations = [
        _dimension(
            "forward_ring",
            "ring-bore",
            "Recorded ring bore",
            ri * 2,
            _position(-ri, 0, station + height / 2, length),
            _position(ri, 0, station + height / 2, length),
            _source(rp1_inspection.SPEC, "parts[id=forward_ring].geometry.inner_radius_m"),
        ),
        _dimension(
            "forward_ring",
            "ring-stack",
            "Recorded ring stock/bond stack",
            height,
            _position(ro + 3, 0, station, length),
            _position(ro + 3, 0, station + height, length),
            _source(rp1_inspection.SPEC, "parts[id=forward_ring].geometry.length_m"),
        ),
    ]
    angle = math.radians(route["passage_angle_deg"])
    radial = ri + route["passage_depth_mm"] / 2
    endpoints = [
        _position(
            radial * math.cos(angle) - t * math.sin(angle),
            radial * math.sin(angle) + t * math.cos(angle),
            station + height / 2,
            length,
        )
        for t in (-route["passage_width_mm"] / 2, route["passage_width_mm"] / 2)
    ]
    annotations.append(
        _dimension(
            "forward_ring",
            "notch-width",
            "Proposed straight notch width",
            route["passage_width_mm"],
            endpoints[0],
            endpoints[1],
            _source(rp1_inspection.DEFINITION, "route.passage_width_mm"),
        )
    )
    for pid in ("motor_tube", "aft_ring"):
        part = original[pid]
        dims = part["geometry"]
        r = dims["radius_m"] * 1000
        inner = dims["inner_radius_m"] * 1000
        z = part["position_m"] * 1000
        annotations.append(
            _dimension(
                pid,
                pid + "-bore",
                "Recorded bore diameter",
                inner * 2,
                _position(-inner, 0, z, length),
                _position(inner, 0, z, length),
                _source(rp1_inspection.SPEC, f"parts[id={pid}].geometry.inner_radius_m"),
            )
        )
        annotations.append(
            _dimension(
                pid,
                pid + "-wall",
                "Recorded radial wall",
                r - inner,
                _position(inner, 0, z, length),
                _position(r, 0, z, length),
                _source(rp1_inspection.SPEC, f"parts[id={pid}].geometry"),
            )
        )
    baro = original["baro"]
    l, w, h = [float(v) * 1000 for v in baro["geometry"]["bbox_m"]]
    bx, bz = baro["lateral_offset_m"][0] * 1000, -baro["lateral_offset_m"][1] * 1000
    station = baro["position_m"] * 1000
    annotations.extend(
        [
            _dimension(
                "baro",
                "baro-axial",
                "Nominal envelope axial length",
                l,
                _position(bx - w / 2, bz - h / 2, station, length),
                _position(bx - w / 2, bz - h / 2, station + l, length),
                _source(rp1_inspection.SPEC, "parts[id=baro].geometry.bbox_m[0]"),
            ),
            _dimension(
                "baro",
                "baro-width",
                "Nominal envelope width",
                w,
                _position(bx - w / 2, bz - h / 2, station, length),
                _position(bx + w / 2, bz - h / 2, station, length),
                _source(rp1_inspection.SPEC, "parts[id=baro].geometry.bbox_m[1]"),
            ),
            _dimension(
                "baro",
                "baro-thickness",
                "Nominal envelope thickness",
                h,
                _position(bx - w / 2, bz - h / 2, station, length),
                _position(bx - w / 2, bz + h / 2, station, length),
                _source(rp1_inspection.SPEC, "parts[id=baro].geometry.bbox_m[2]"),
            ),
        ]
    )
    cases = [
        {
            "id": "forward-ring-recovery",
            "label": "Forward ring and proposed cord passage",
            "part_ids": ["forward_ring", "rp1_kevlar_wrap"],
            "replacement_part_ids": ["forward_ring"],
            "supported_features": [
                "Source64.4mm outer/31.9mm bore annulus,12.2mm total",
                "Two6mm stock layers and0.2mm bond visualization",
                "Straight4.5mm-wide,5mm-deep notch at60degrees",
            ],
            "missing": [
                "Proposed2mm entrance/exit roundovers have no fully defined blended-surface topology here and remain omitted",
                "Actual dressed knot/rope topology, contact deformation and chafe geometry unavailable",
                "Layer grain/ply internals and conditioned bond quality unavailable",
            ],
        },
        {
            "id": "motor-support-retention",
            "label": "Motor support bores and unverified retainer",
            "part_ids": ["motor_tube", "aft_ring", "motor_retainer", "motor"],
            "replacement_part_ids": ["motor_tube", "aft_ring"],
            "supported_features": [
                "Higher-resolution source tube bore/wall",
                "Higher-resolution source aft centering-ring annulus",
                "Exact frozen nominal stations/dimensions; original retainer remains an envelope",
            ],
            "missing": [
                "Current retainer cap/sleeve split, threads, shoulders, motor seat/liner/closure contacts unavailable",
                "Source notes quote nominal kit sizes; frozen numerical geometry controls this display, not a controlled supplier drawing",
                "No installed interference, bond contact or exact motor fit acceptance",
            ],
        },
        {
            "id": "avionics-envelope",
            "label": "Barometer envelope and missing supplier internals",
            "part_ids": ["baro"],
            "replacement_part_ids": [],
            "supported_features": [
                "Recorded15×12×3mm nominal envelope edge/dimension guides; original12-triangle box retained"
            ],
            "missing": [
                "Actual PCB outline, component heights, sensors, connectors, solder, traces and mounting holes unavailable",
                "No PCB components or winding/thread details are fabricated by increasing polygon count",
            ],
        },
    ]
    return {
        "schema_version": 1,
        "id": ID,
        "source_tuple": source_tuple,
        "detail_sha256": detail_sha,
        "sources": frozen,
        "core_source_records": 55,
        "core_mesh_records": 26,
        "replacements_expected": list(REPLACEMENTS),
        "status": "Optional display-only source detail; source estimates and missingness unchanged",
        "render_contract": {
            "replace_only_matching_core_part": True,
            "preserve_asset_materials": True,
            "pick_parent_part_id": True,
            "apply_existing_part_display_transform_once": True,
            "keep_original_part_mesh_url_for_source_admission": True,
        },
        "units": {"assets": "m", "annotations": "m with recorded values in mm"},
        "viewer_frame": core["viewer_frame"],
        "core_asset_audit": audit,
        "cases": cases,
        "annotations": annotations,
        "parts": [],
        "mass_or_inertia_generated": False,
        "engineering_accepted": False,
        "manufacturing_clearance": False,
    }


def export(root: Path, *, cpu_limit_seconds: float = 120) -> dict[str, Any]:
    """Generate only three optional annular display assets; one bounded attempt."""
    started = time.process_time()
    packet = catalog(root)
    os.environ.setdefault("XDG_CACHE_HOME", str(root / ".cache"))
    cq: Any = importlib.import_module("cadquery")
    import numpy as np

    trimesh: Any = importlib.import_module("trimesh")

    document = rp1_inspection.build(root)
    parts = {p["id"]: p["raw"] for p in document["parts"]}
    definition = yaml.safe_load((root / rp1_inspection.DEFINITION).read_bytes())
    folder = (root / FOLDER).resolve()
    if not folder.is_relative_to(root.resolve()):
        raise ValueError("Optional detail output escapes repository")
    (folder / "parts").mkdir(parents=True, exist_ok=True)
    audit = {p["id"]: p for p in packet["core_asset_audit"]}
    for pid in REPLACEMENTS:
        if time.process_time() - started > cpu_limit_seconds:
            raise TimeoutError("Optional detail CPU budget exhausted; no automatic retry")
        part = parts[pid]
        g = part["geometry"]
        ro = g["radius_m"] * 1000
        ri = g["inner_radius_m"] * 1000
        total = g["length_m"] * 1000
        layers = (
            [
                ("stock_front", 0.0, 6.0, "#ceb087"),
                ("bond_reservation", 6.0, 0.2, "#75b4c6"),
                ("stock_aft", 6.2, 6.0, "#b99b75"),
            ]
            if pid == "forward_ring"
            else [("source_annulus", 0.0, total, "#d4b887")]
        )
        scene = trimesh.Scene()
        for name, start, height, color in layers:
            shape = (
                cq.Workplane("XY")
                .circle(ro)
                .circle(ri)
                .extrude(height)
                .val()
                .translate((0, 0, start))
            )
            if pid == "forward_ring":
                route = definition["route"]
                depth = route["passage_depth_mm"]
                width = route["passage_width_mm"]
                cutter = (
                    cq.Workplane("XY")
                    .box(depth + 1, width, total + 2, centered=(True, True, False))
                    .val()
                    .translate((ri + (depth - 1) / 2, 0, -1))
                    .rotate((0, 0, 0), (0, 0, 1), route["passage_angle_deg"])
                )
                shape = shape.cut(cutter)
            if not shape.isValid():
                raise ValueError(f"Optional detail shape invalid: {pid}/{name}; stop")
            shape = shape.translate(
                (
                    part["lateral_offset_m"][0] * 1000,
                    -part["lateral_offset_m"][1] * 1000,
                    part["position_m"] * 1000,
                )
            )
            vertices, faces = shape.tessellate(0.01, 0.035)
            points = np.array(
                [
                    [v.x / 1000, document["geometry"]["length_m"] - v.z / 1000, v.y / 1000]
                    for v in vertices
                ]
            )
            mesh = trimesh.Trimesh(vertices=points, faces=np.asarray(faces), process=False)
            mesh.visual.face_colors = trimesh.visual.color.hex_to_rgba(color)
            scene.add_geometry(mesh, node_name=f"{pid}/{name}", geom_name=f"{pid}/{name}")
        path = folder / "parts" / f"{pid}.glb"
        raw = scene.export(file_type="glb")
        path.write_bytes(raw)
        loaded = trimesh.load(path, force="scene").to_geometry()
        envelope = np.array(audit[pid]["actual_bounds_m"])
        if np.max(np.abs(loaded.bounds - envelope)) > 2e-5:
            raise ValueError("Optional detail no longer matches its frozen part envelope")
        packet["parts"].append(
            {
                "part_id": pid,
                "maturity": next(
                    p["maturity"] for p in packet["core_asset_audit"] if p["id"] == pid
                ),
                "core_mesh_sha256": audit[pid]["mesh_sha256"],
                "inspection_shape_sha256": audit[pid]["inspection_shape_sha256"],
                "asset_path": f"/engineering-workbench/rp1-detail/parts/{pid}.glb",
                "asset_sha256": sha(raw),
                "bounds_m": loaded.bounds.tolist(),
                "triangles": len(loaded.faces),
                "core_triangles": audit[pid]["triangles"],
                "layers": [
                    {"id": name, "local_station_start_mm": start, "thickness_mm": height}
                    for name, start, height, color in layers
                ],
                "display_only": True,
                "sampling": {"linear_tolerance_mm": 0.01, "angular_tolerance_rad": 0.035},
                "source": _source(rp1_inspection.SPEC, f"parts[id={pid}].geometry"),
            }
        )
    if time.process_time() - started > cpu_limit_seconds:
        raise TimeoutError("Optional detail CPU budget exhausted; no automatic retry")
    if any(sha((root / path).read_bytes()) != digest for path, digest in packet["sources"].items()):
        raise ValueError("Optional detail source changed during export")
    packet["tools"] = {
        "cadquery": cq.__version__,
        "trimesh": trimesh.__version__,
        "numpy": np.__version__,
    }
    encoded = json.dumps(packet, indent=2) + "\n"
    (folder / "manifest.json").write_text(encoded)
    return packet
