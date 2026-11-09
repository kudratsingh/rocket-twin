"""Separate existing source mesh components, preserving every source triangle.

No CAD generation, geometry refinement, physical dimensions, mass/inertia or
adhesive solids. Exact coincident vertex welding repairs representation seams
only; original coordinate values and oriented triangles remain unchanged.
"""

from __future__ import annotations

import hashlib
import json
import resource
import shutil
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CATALOG = ROOT / "docs/studies/frontend-component-depth-20261108/mechanical-detail-layout.json"
OUTPUT = ROOT / "output/rp1-component-detail"
PUBLIC = ROOT / "web/public/engineering-workbench/rp1-component-detail"
IDS = ("fin_set", "fin_tabs", "root_gussets", "body", "motor_tube", "aft_ring", "forward_ring")
EXPECTED = {
    "fin_set": 3,
    "fin_tabs": 3,
    "root_gussets": 6,
    "body": 1,
    "motor_tube": 1,
    "aft_ring": 1,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def triangle_fingerprint(mesh: Any) -> str:
    """Oriented triangle-coordinate multiset; independent of vertex/face indexing."""
    import numpy as np

    rows = []
    for triangle in np.asarray(mesh.triangles, dtype=np.float32):
        a, b, c = [vertex.tobytes() for vertex in triangle]
        rows.append(min(a + b + c, b + c + a, c + a + b))
    return sha(b"".join(sorted(rows)))


def split_exact(mesh: Any) -> list[Any]:
    import numpy as np
    import trimesh

    unique, inverse = np.unique(mesh.vertices, axis=0, return_inverse=True)
    welded = trimesh.Trimesh(
        vertices=unique, faces=inverse[mesh.faces], visual=mesh.visual.copy(), process=False
    )
    if triangle_fingerprint(welded) != triangle_fingerprint(mesh):
        raise ValueError("Exact vertex indexing changed oriented source triangles")
    return list(welded.split(only_watertight=False))


def export() -> dict[str, Any]:
    started_wall, started_cpu = time.monotonic(), time.process_time()
    import numpy as np
    import trimesh

    from src.api import rp1_geometry, rp1_inspection

    if OUTPUT.exists() or PUBLIC.exists() or CATALOG.exists():
        raise ValueError("Mechanical detail output/catalog already exists; no overwrite or repeat")
    core = rp1_geometry.build(ROOT)
    document = rp1_inspection.build(ROOT)
    feature_path = (
        ROOT / "docs/studies/frontend-component-depth-20261108/mechanical-feature-map.json"
    )
    feature = json.loads(feature_path.read_bytes())
    detail_path = ROOT / "web/public/engineering-workbench/rp1-detail/manifest.json"
    detail = json.loads(detail_path.read_bytes())
    if (
        core["identity"]["inspection_geometry_sha256"]
        != "238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608"
    ):
        raise ValueError("Frozen core identity mismatch")
    if (
        detail["source_tuple"]["inspection_geometry_sha256"]
        != core["identity"]["inspection_geometry_sha256"]
    ):
        raise ValueError("Optional detail/core mismatch")
    if feature.get("configuration_id", feature.get("identity", {}).get("configuration_id")) not in (
        None,
        rp1_inspection.ID,
    ):
        raise ValueError("Mechanical feature-map configuration mismatch")
    snapshots = {
        str(detail_path.relative_to(ROOT)): sha(detail_path.read_bytes()),
        str(feature_path.relative_to(ROOT)): sha(feature_path.read_bytes()),
        **core["sources"],
    }
    parts = {p["id"]: p for p in document["parts"]}
    rows = {p["id"]: p for p in core["parts"]}
    optional = {p["part_id"]: p for p in detail["parts"]}
    packet = {
        "schema_version": 1,
        "id": "rp1-existing-source-mechanical-components-v1",
        "configuration_id": rp1_inspection.ID,
        "specification_sha256": core["identity"]["specification_sha256"],
        "inspection_geometry_sha256": core["identity"]["inspection_geometry_sha256"],
        "all55_part_ids": [p["id"] for p in core["parts"]],
        "units": "m",
        "viewer_frame": core["viewer_frame"],
        "source_datum": core["source_datum"],
        "sources": snapshots,
        "parents": [],
        "children": [],
        "callout_only_part_ids": [
            "fin_internal_bonds",
            "outer_fin_fillets",
            "ring_bonds",
            "ad1_slot_fill",
        ],
        "limits": [
            "Existing source triangles separated into selectable components only; no geometry or dimensions invented",
            "Body cutaway and child separation are frontend display operations only, not physical material removal or extraction paths",
            "Forward-ring middle layer is an existing visual bond reservation, not a newly qualified adhesive solid",
            "No mass/inertia, installed joint, manufacturing or flight qualification",
            "Other adhesive/mass allowances remain callouts without geometry",
            "Fin panel/tab source records remain separate; continuity and capacity are not established",
        ],
        "engineering_accepted": False,
        "mass_or_inertia_generated": False,
        "canonical_vehicle_geometry_changed": False,
    }
    OUTPUT.mkdir(parents=True)
    for pid in IDS:
        if time.process_time() - started_cpu > 80 or time.monotonic() - started_wall > 110:
            raise TimeoutError("Mechanical extraction reserve reached; no automatic retry")
        row, part = rows[pid], parts[pid]
        selected = optional.get(pid) if pid in ("forward_ring", "motor_tube", "aft_ring") else None
        relative = "web/public" + selected["asset_path"] if selected else row["mesh"]["path"]
        expected_sha = selected["asset_sha256"] if selected else row["mesh"]["sha256"]
        source_path = ROOT / relative
        if sha(source_path.read_bytes()) != expected_sha:
            raise ValueError(f"Source mesh mismatch: {pid}")
        snapshots[relative] = expected_sha
        scene = trimesh.load(source_path, force="scene")
        source_mesh = scene.to_geometry()
        pieces = []
        if pid == "forward_ring":
            for name in ("stock_front", "bond_reservation", "stock_aft"):
                node = f"forward_ring/{name}"
                if node not in scene.graph.nodes_geometry:
                    raise ValueError("Existing forward-ring named layers unavailable; stop")
                transform, geometry = scene.graph[node]
                if not np.array_equal(transform, np.eye(4)):
                    raise ValueError("Optional ring layer transform changed")
                pieces.append((name, scene.geometry[geometry].copy()))
        else:
            components = split_exact(source_mesh)
            if len(components) != EXPECTED[pid]:
                raise ValueError(
                    f"Meaningful source components unavailable: {pid}, got{len(components)}"
                )
            components.sort(
                key=lambda mesh: float(
                    np.arctan2(mesh.bounds.mean(axis=0)[2], mesh.bounds.mean(axis=0)[0])
                    % (2 * np.pi)
                )
            )
            prefix = {"fin_set": "panel", "fin_tabs": "tab", "root_gussets": "gusset"}.get(
                pid, "source"
            )
            pieces = [(f"{prefix}-{index + 1:02d}", mesh) for index, mesh in enumerate(components)]
        joined = trimesh.util.concatenate([mesh for _, mesh in pieces])
        if triangle_fingerprint(joined) != triangle_fingerprint(source_mesh):
            raise ValueError(f"Source triangle coverage changed: {pid}")
        union = np.array(
            [
                np.min([mesh.bounds[0] for _, mesh in pieces], axis=0),
                np.max([mesh.bounds[1] for _, mesh in pieces], axis=0),
            ]
        )
        if not np.array_equal(union, source_mesh.bounds):
            raise ValueError("Child union bounds differ from selected source")
        core_bounds = np.asarray(row["bounds_m"])
        if np.max(np.abs(union - core_bounds)) > 2e-5:
            raise ValueError("Selected detail no longer matches frozen core envelope")
        parent = {
            "id": pid,
            "material": part["material"],
            "function": part["function"],
            "maturity": row["maturity"],
            "core_mesh_sha256": row["mesh"]["sha256"],
            "source_mesh_sha256": expected_sha,
            "source_kind": "existing_optional_detail" if selected else "frozen_core_glb",
            "source_path": relative,
            "bounds_m": source_mesh.bounds.tolist(),
            "core_bounds_m": row["bounds_m"],
            "source_oriented_triangles_sha256": triangle_fingerprint(source_mesh),
            "source_faces": len(source_mesh.faces),
            "child_count": len(pieces),
            "child_union_bounds_exact": True,
            "source_triangles_retained": True,
        }
        packet["parents"].append(parent)
        for sub_id, mesh in pieces:
            filename = f"{pid}--{sub_id}.glb"
            path = OUTPUT / filename
            path.write_bytes(trimesh.Scene(mesh).export(file_type="glb"))
            loaded = trimesh.load(path, force="scene").to_geometry()
            if triangle_fingerprint(loaded) != triangle_fingerprint(mesh) or not np.array_equal(
                loaded.bounds, mesh.bounds
            ):
                raise ValueError("Child GLB readback changed source triangles/bounds")
            packet["children"].append(
                {
                    "id": f"{pid}:{sub_id}",
                    "parent_part_id": pid,
                    "sub_id": sub_id,
                    "label": f"{pid.replace('_', ' ')} · {sub_id.replace('_', ' ')}",
                    "url": f"/engineering-workbench/rp1-component-detail/{filename}",
                    "sha256": sha(path.read_bytes()),
                    "bytes": path.stat().st_size,
                    "bounds_m": mesh.bounds.tolist(),
                    "source_kind": parent["source_kind"],
                    "source_mesh_sha256": expected_sha,
                    "material": (
                        "Unspecified bond reservation (display only)"
                        if sub_id == "bond_reservation"
                        else parent["material"]
                    ),
                    "source_parent_material": parent["material"],
                    "maturity": parent["maturity"],
                    "faces": len(mesh.faces),
                    "oriented_triangles_sha256": triangle_fingerprint(mesh),
                    "visual_bond_reservation_only": sub_id == "bond_reservation",
                }
            )
    for relative, expected_sha in snapshots.items():
        if sha((ROOT / relative).read_bytes()) != expected_sha:
            raise ValueError("Input changed during extraction")
    rp1_geometry.build(ROOT)
    PUBLIC.mkdir(parents=True)
    for child in packet["children"]:
        name = child["url"].rsplit("/", 1)[1]
        shutil.copyfile(OUTPUT / name, PUBLIC / name)
        if sha((PUBLIC / name).read_bytes()) != child["sha256"]:
            raise ValueError("Public child copy differs")
    packet["counts"] = {
        "source_records": 55,
        "parent_records": len(packet["parents"]),
        "child_assets": len(packet["children"]),
    }
    packet["runtime"] = {
        "wall_seconds": time.monotonic() - started_wall,
        "cpu_seconds": time.process_time() - started_cpu,
    }
    CATALOG.write_text(json.dumps(packet, separators=(",", ":")) + "\n")
    return packet


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (89, 90))
    result = export()
    print(
        json.dumps(
            {
                "counts": result["counts"],
                "runtime": result["runtime"],
                "catalog_sha256": sha(CATALOG.read_bytes()),
            }
        )
    )
