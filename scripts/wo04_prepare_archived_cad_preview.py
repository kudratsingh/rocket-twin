"""Verify/copy the four fixed archived CAD registries without CAD generation.

Run without --prepare to verify only. Public copying must await the primary's
explicit browser-hold release. Existing nonempty destinations are never replaced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/studies/frontend-desktop-detail-20261108/archived-cad-access.json"
REGISTRY_SHA256 = "cd3cc2557c61df5f051fbc5a48002ef62678831e1639379364a19ead6398f49f"
PUBLIC = ROOT / "web/public/engineering-workbench/archived-cad"
CONFIGURATIONS = (
    "modular-performance-v1",
    "modular-performance-g54-hypothesis",
    "modular-tvc-finned-v1",
    "modular-tvc-finless-v1",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_file(relative: str, expected: str) -> Path:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or sha(path.read_bytes()) != expected:
        raise ValueError(f"Registered source/asset changed or unavailable: {relative}")
    return path


def registered_files() -> list[tuple[Path, str, str]]:
    if sha(REGISTRY.read_bytes()) != REGISTRY_SHA256:
        raise ValueError("Archived CAD audit changed; do not update pins or regenerate")
    registry = json.loads(REGISTRY.read_bytes())
    if tuple(row["id"] for row in registry["configurations"]) != CONFIGURATIONS:
        raise ValueError("Only the four registered configurations are admitted")
    checked_file(registry["catalog_source"]["path"], registry["catalog_source"]["sha256"])
    for path, expected in registry["cad_source_sha256"].items():
        checked_file(path, expected)
    current_cad = sha(b"".join(p.read_bytes() for p in sorted((ROOT / "src/cad").glob("*.py"))))
    if current_cad != registry["cad_revision_sha256"]:
        raise ValueError("CAD source revision changed")
    sys.path.insert(0, str(ROOT))
    from src.vehicle.cad_contract import digest
    from src.vehicle.schema import load_vehicle

    files = []
    for configuration in registry["configurations"]:
        cid = configuration["id"]
        for path, expected in configuration["input_sha256"].items():
            checked_file(path, expected)
        vehicle = load_vehicle(ROOT / configuration["path"])
        identity = {
            "configuration_id": vehicle.id,
            "resolved_spec_sha256": sha(vehicle.model_dump_json(by_alias=True).encode()),
            "cad_revision_sha256": current_cad,
            "part_shape_sha256": {
                part.id: digest(part.geometry, part.cad.model_dump() if part.cad else None)
                for part in vehicle.parts
            },
        }
        if identity != configuration["identity"] or identity != configuration["recorded_identity"]:
            raise ValueError(f"Resolved spec/CAD/part shape identity changed: {cid}")
        manifest = configuration["manifest"]
        path = checked_file(manifest["path"], manifest["sha256"])
        if json.loads(path.read_bytes())["identity"] != identity:
            raise ValueError("Recorded CAD manifest identity differs")
        if set(identity["part_shape_sha256"]) != {row["id"] for row in configuration["parts"]}:
            raise ValueError("Registered part inventory differs")
        for row in configuration["parts"]:
            pid = row["id"]
            if not re.fullmatch(r"[a-z][a-z0-9_]*", pid):
                raise ValueError("Unregistered part filename")
            for fmt in ("glb", "step", "stl"):
                asset = row["assets"][fmt]
                relative = f"parts/{pid}.{fmt}"
                if asset["path"] != f"build/{cid}/{relative}" or asset["format"] != fmt:
                    raise ValueError("Unregistered part format/path")
                source = checked_file(asset["path"], asset["sha256"])
                files.append((source, f"{cid}/{relative}", asset["sha256"]))
        if configuration["assemblies"]["stl"] is not None:
            raise ValueError("Assembly STL is not registered")
        for fmt in ("glb", "step"):
            asset = configuration["assemblies"][fmt]
            if asset["path"] != f"build/{cid}/assembly.{fmt}":
                raise ValueError("Unregistered assembly format/path")
            source = checked_file(asset["path"], asset["sha256"])
            files.append((source, f"{cid}/assembly.{fmt}", asset["sha256"]))
        files.append((REGISTRY, f"{cid}/provenance.json", REGISTRY_SHA256))
    if len(files) != 576 or len({relative for _, relative, _ in files}) != 576:
        raise ValueError("Expected572 fixed assets and4 provenance files")
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--destination", type=Path, default=PUBLIC)
    args = parser.parse_args()
    destination = args.destination.resolve()
    temporary_root = Path(tempfile.gettempdir()).resolve()
    if destination != PUBLIC.resolve() and not destination.is_relative_to(temporary_root):
        raise ValueError("Destination must be the fixed public folder or a temporary test folder")
    files = registered_files()
    if args.prepare:
        if destination.exists() and any(destination.iterdir()):
            raise ValueError("Destination is nonempty; no overwrite or mixed registry")
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".archived-cad-stage-", dir=destination.parent))
        try:
            for source, relative, expected in files:
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                if sha(target.read_bytes()) != expected:
                    raise ValueError(f"Copied bytes differ: {relative}")
                if relative.endswith("provenance.json"):
                    target.chmod(0o444)
            registered_files()
            if destination.exists():
                destination.rmdir()
            staging.replace(destination)
        except Exception:
            shutil.rmtree(staging)
            raise
    print(
        json.dumps(
            {
                "status": "prepared" if args.prepare else "verified_no_copy",
                "configurations": len(CONFIGURATIONS),
                "files": len(files),
                "registry_sha256": REGISTRY_SHA256,
                "destination": str(destination) if args.prepare else None,
            }
        )
    )


if __name__ == "__main__":
    main()
