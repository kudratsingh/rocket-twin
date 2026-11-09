"""Verify/copy the four fixed archived CAD registries without CAD generation.

Run without --prepare to verify only. Public copying must await the primary's
explicit browser-hold release. Existing nonempty destinations are never replaced.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/studies/frontend-desktop-detail-20261108/archived-cad-access.json"
REGISTRY_SHA256 = "cd3cc2557c61df5f051fbc5a48002ef62678831e1639379364a19ead6398f49f"
CATALOG_EQUIVALENCE = (
    ROOT / "docs/studies/frontend-parts-bank-20261109/archived-catalog-equivalence.json"
)
CATALOG_EQUIVALENCE_SHA256 = "d45d186543fb4416a0a051b1f12c92087cb64d3cbafd169ef63a1e5e592a190a"
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


def verify_catalog_equivalence(content: bytes, proof: dict[str, Any], original_sha: str) -> None:
    """Admit only the exact bank-route extension, not a relaxed catalogue pin."""
    if (
        proof["id"] != "fw2-parts-bank-routes-only-catalog-equivalence-v1"
        or proof["registry"]["sha256"] != REGISTRY_SHA256
        or proof["catalog_source_path"] != "src/api/app.py"
        or proof["original"]["sha256"] != original_sha
        or proof["geometry_or_asset_changed"] is not False
        or proof["engineering_accepted"] is not False
        or sha(content) != proof["compatible_source"]["sha256"]
    ):
        raise ValueError("API catalogue source is outside the exact recorded compatibility proof")
    if sys.version_info[:2] != (3, 11):
        raise ValueError("Catalogue equivalence requires pinned Python 3.11; use .venv/bin/python")
    tree = ast.parse(content)
    nodes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "CatalogEntry"
        or isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "CATALOG" for target in node.targets)
    ]
    catalog = ast.Module(body=nodes, type_ignores=[])
    catalog_hash = sha(ast.dump(catalog, include_attributes=False).encode())
    if len(nodes) != 2 or catalog_hash != proof["original"]["catalog_ast_sha256"]:
        raise ValueError("Archived vehicle catalogue declaration changed")
    create = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "create_app"
    )
    allowed = ["source_parts_bank", "source_part_definition"]
    removed = [
        node.name
        for node in create.body
        if isinstance(node, ast.FunctionDef) and node.name in allowed
    ]
    if removed != allowed or proof["compatible_source"]["removed_new_route_functions"] != allowed:
        raise ValueError("Compatibility proof permits only the two recorded parts-bank routes")
    create.body = [
        node
        for node in create.body
        if not isinstance(node, ast.FunctionDef) or node.name not in allowed
    ]
    if (
        sha(ast.dump(tree, include_attributes=False).encode())
        != proof["original"]["module_ast_sha256"]
    ):
        raise ValueError("Existing API behavior changed beyond the recorded new routes")


def checked_catalog_source(registry: dict[str, Any]) -> None:
    source = registry["catalog_source"]
    path = (ROOT / source["path"]).resolve()
    if not path.is_relative_to(ROOT) or source["path"] != "src/api/app.py":
        raise ValueError("Unknown archived catalogue source path")
    content = path.read_bytes()
    if sha(content) == source["sha256"]:
        return
    proof_bytes = CATALOG_EQUIVALENCE.read_bytes()
    if sha(proof_bytes) != CATALOG_EQUIVALENCE_SHA256:
        raise ValueError("Catalogue compatibility proof changed or is unavailable")
    proof = json.loads(proof_bytes)
    if proof["cad_revision_sha256"] != registry["cad_revision_sha256"]:
        raise ValueError("Compatibility proof cannot change the archived CAD revision")
    verify_catalog_equivalence(content, proof, source["sha256"])


def registered_files() -> list[tuple[Path, str, str]]:
    if sha(REGISTRY.read_bytes()) != REGISTRY_SHA256:
        raise ValueError("Archived CAD audit changed; do not update pins or regenerate")
    registry = json.loads(REGISTRY.read_bytes())
    if tuple(row["id"] for row in registry["configurations"]) != CONFIGURATIONS:
        raise ValueError("Only the four registered configurations are admitted")
    checked_catalog_source(registry)
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
