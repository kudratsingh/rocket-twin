"""Repeatably prepare only the frozen mechanical child GLBs; never run CAD.

Missing child cache may be reconstructed from matching existing parent GLBs in
temporary staging. Exact recorded child bytes/triangles/bounds must match before
publication. Missing/changed source files are unavailable, never regenerated here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import shutil
import signal
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = "docs/studies/frontend-component-depth-20261108/mechanical-detail-layout.json"
CATALOG_SHA256 = "1044bc7aeacad0802fe74add1fecbc77aeddcd0ed09f493c685bb639d271eda1"
EXPORTER_PATH = "scripts/wo04_rp1_mechanical_detail_export.py"
EXPORTER_SHA256 = "821d4783a6634dc44b1afc8316b4268c4fdf1daa2afc8e628f6689c0e762118e"
PUBLIC_PATH = "web/public/engineering-workbench/rp1-component-detail"
CACHE_PATH = "output/rp1-component-detail"


class UnavailableError(RuntimeError):
    """Pinned source or supply is absent/incompatible; no generation fallback."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_file(root: Path, relative: str, expected: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise UnavailableError(
            f"Required source unavailable: {relative}; prepare matching core/optional GLBs first"
        )
    if digest(path.read_bytes()) != expected:
        raise UnavailableError(
            f"Source hash mismatch: {relative}; no pin relaxation or CAD regeneration"
        )
    return path


def catalog(root: Path) -> dict[str, Any]:
    path = source_file(root, CATALOG_PATH, CATALOG_SHA256)
    packet: dict[str, Any] = json.loads(path.read_bytes())
    if (
        packet["configuration_id"] != "G80-F2-RP1-AD1-definition-v2"
        or len(set(packet["all55_part_ids"])) != 55
        or len(packet["parents"]) != 7
        or len(packet["children"]) != 18
        or packet["units"] != "m"
        or packet["engineering_accepted"] is not False
        or packet["canonical_vehicle_geometry_changed"] is not False
    ):
        raise UnavailableError("Frozen catalog shape/identity incompatible")
    source_file(root, EXPORTER_PATH, EXPORTER_SHA256)
    for relative, expected in packet["sources"].items():
        source_file(root, relative, expected)
    for child in packet["children"]:
        name = f"{child['parent_part_id']}--{child['sub_id']}.glb"
        if (
            child["url"] != f"/engineering-workbench/rp1-component-detail/{name}"
            or "/" in name
            or "\\" in name
        ):
            raise UnavailableError("Unregistered child filename")
    return packet


def filename(child: dict[str, Any]) -> str:
    return child["url"].rsplit("/", 1)[1]


def check_child(path: Path, child: dict[str, Any], *, geometry: bool = False) -> bool:
    if not path.exists():
        return False
    if not path.is_file() or digest(path.read_bytes()) != child["sha256"]:
        raise UnavailableError(f"Recorded child bytes differ: {path.name}")
    if geometry:
        import numpy as np
        import trimesh

        from scripts.wo04_rp1_mechanical_detail_export import triangle_fingerprint

        mesh = trimesh.load(path, force="scene").to_geometry()
        if triangle_fingerprint(mesh) != child["oriented_triangles_sha256"] or not np.array_equal(
            mesh.bounds, child["bounds_m"]
        ):
            raise UnavailableError(f"Recorded child triangles/bounds differ: {path.name}")
    return True


def reconstruct(
    root: Path, packet: dict[str, Any], staging: Path, missing: list[dict[str, Any]], guard: Any
) -> None:
    import numpy as np
    import trimesh

    from scripts.wo04_rp1_mechanical_detail_export import (
        EXPECTED,
        split_exact,
        triangle_fingerprint,
    )

    needed = {child["parent_part_id"] for child in missing}
    for parent in packet["parents"]:
        pid = parent["id"]
        if pid not in needed:
            continue
        guard()
        source = source_file(root, parent["source_path"], parent["source_mesh_sha256"])
        scene = trimesh.load(source, force="scene")
        whole = scene.to_geometry()
        if triangle_fingerprint(whole) != parent["source_oriented_triangles_sha256"]:
            raise UnavailableError(f"Parent triangle identity mismatch: {pid}")
        if pid == "forward_ring":
            pieces = []
            for name in ("stock_front", "bond_reservation", "stock_aft"):
                node = f"forward_ring/{name}"
                if node not in scene.graph.nodes_geometry:
                    raise UnavailableError("Existing forward-ring layer unavailable")
                transform, geometry = scene.graph[node]
                if not np.array_equal(transform, np.eye(4)):
                    raise UnavailableError("Forward-ring source transform changed")
                pieces.append((name, scene.geometry[geometry].copy()))
        else:
            components = split_exact(whole)
            if len(components) != EXPECTED[pid]:
                raise UnavailableError(f"Existing connected-component count differs: {pid}")
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
        expected = {c["sub_id"]: c for c in packet["children"] if c["parent_part_id"] == pid}
        if set(expected) != {sub for sub, _ in pieces}:
            raise UnavailableError("Reconstructed child IDs differ from catalog")
        union = np.array(
            [
                np.min([mesh.bounds[0] for _, mesh in pieces], axis=0),
                np.max([mesh.bounds[1] for _, mesh in pieces], axis=0),
            ]
        )
        if (
            not np.array_equal(union, parent["bounds_m"])
            or triangle_fingerprint(trimesh.util.concatenate([mesh for _, mesh in pieces]))
            != parent["source_oriented_triangles_sha256"]
        ):
            raise UnavailableError("Reconstruction changed source coordinates/triangles")
        for sub, mesh in pieces:
            child = expected[sub]
            path = staging / filename(child)
            path.write_bytes(trimesh.Scene(mesh).export(file_type="glb"))
            check_child(path, child, geometry=True)


def prepare(
    root: Path = ROOT,
    *,
    destination: Path | None = None,
    cache: Path | None = None,
    publish: bool = False,
) -> dict[str, Any]:
    started_wall, started_cpu = time.monotonic(), time.process_time()
    root = root.resolve()
    sys.path.insert(0, str(root))
    target = (destination or root / PUBLIC_PATH).resolve()
    cache = (cache or root / CACHE_PATH).resolve()
    packet = catalog(root)
    allowed = {filename(c) for c in packet["children"]}
    if target.exists() and (
        not target.is_dir()
        or any(p.name not in allowed or not p.is_file() for p in target.iterdir())
    ):
        raise UnavailableError("Destination contains unregistered files; no replacement")
    public_states = [check_child(target / filename(c), c) for c in packet["children"]]
    public_ok = all(public_states)
    if public_ok:
        return {
            "status": "verified_existing_public",
            "catalog_sha256": CATALOG_SHA256,
            "children": 18,
            "reconstructed": 0,
            "public_writes": 0,
        }
    existing = {c["id"]: check_child(cache / filename(c), c) for c in packet["children"]}
    missing = [c for c in packet["children"] if not existing[c["id"]]]
    if not publish:
        return {
            "status": "verified_cache_copy_required"
            if not missing
            else "unavailable_missing_children",
            "catalog_sha256": CATALOG_SHA256,
            "children": 18,
            "missing_children": len(missing),
            "reconstructed": 0,
            "public_writes": 0,
        }
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".component-detail-stage-", dir=target.parent))
    backup: Path | None = None

    def guard() -> None:
        if time.process_time() - started_cpu > 80 or time.monotonic() - started_wall > 110:
            raise TimeoutError("Production reconstruction budget reached; no retry")

    try:
        for child in packet["children"]:
            if existing[child["id"]]:
                shutil.copyfile(cache / filename(child), staging / filename(child))
        if missing:
            reconstruct(root, packet, staging, missing, guard)
        for child in packet["children"]:
            guard()
            if not check_child(staging / filename(child), child, geometry=True):
                raise UnavailableError("Child unavailable after staging")
        catalog(root)
        if target.exists():
            backup = Path(tempfile.mkdtemp(prefix=".component-detail-backup-", dir=target.parent))
            backup.rmdir()
            target.rename(backup)
        staging.rename(target)
        if backup:
            shutil.rmtree(backup)
        return {
            "status": "prepared",
            "catalog_sha256": CATALOG_SHA256,
            "children": 18,
            "reconstructed": len(missing),
            "public_writes": 18,
            "runtime": {
                "wall_seconds": time.monotonic() - started_wall,
                "cpu_seconds": time.process_time() - started_cpu,
            },
        }
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if backup and backup.exists() and not target.exists():
            backup.rename(target)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--verify", action="store_true", help="Read-only default")
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.destination:
        destination = args.destination.resolve()
        if destination != (ROOT / PUBLIC_PATH).resolve() and not destination.is_relative_to(
            Path(tempfile.gettempdir()).resolve()
        ):
            parser.error("Destination must be the fixed public folder or temporary test directory")
    resource.setrlimit(resource.RLIMIT_CPU, (89, 90))

    def timeout(*_: Any) -> None:
        raise TimeoutError("120-second production preparation wall limit; no retry")

    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(120)
    try:
        result = prepare(destination=args.destination, publish=args.prepare)
        print(json.dumps(result))
        return 1 if result["status"].startswith("unavailable") else 0
    except (ImportError, OSError, ValueError, RuntimeError, TimeoutError) as error:
        print(
            json.dumps(
                {
                    "status": "unavailable",
                    "reason": str(error),
                    "catalog_changed": False,
                    "cad_generated": False,
                }
            )
        )
        return 1
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    raise SystemExit(main())
