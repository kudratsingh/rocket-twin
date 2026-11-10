"""Prepare the pinned RP1 read-only template registry for the web workbench."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.vehicle.part_templates import REGISTRY_ID, build

OUTPUT = "web/public/engineering-workbench/rp1-part-templates.json"


def prepare(root: Path, output: str = OUTPUT, *, check: bool = False) -> dict[str, str | int]:
    """Write only this project's registered snapshot, refusing foreign outputs."""
    root = root.resolve()
    target = root / OUTPUT
    requested = Path(output)
    requested = requested if requested.is_absolute() else root / requested
    if requested != target or not target.resolve().is_relative_to(root) or target.is_symlink():
        raise ValueError("Template output must be the fixed registered project path")
    catalog = build(root)
    data = (json.dumps(catalog, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if target.exists():
        try:
            previous = json.loads(target.read_bytes())
        except (ValueError, OSError) as error:
            raise ValueError("Refusing to overwrite a foreign template output") from error
        if (
            not isinstance(previous, dict)
            or previous.get("id") != REGISTRY_ID
            or previous.get("configuration_id") != catalog["configuration_id"]
            or previous.get("schema_version") != 1
        ):
            raise ValueError("Refusing to overwrite a foreign template output")
    if check:
        if not target.is_file() or target.read_bytes() != data:
            raise ValueError("Prepared template snapshot is missing or differs from pinned source")
    elif not target.is_file() or target.read_bytes() != data:
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".rp1-part-templates-", dir=target.parent)
        staging = Path(temporary)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if build(root) != catalog:
                raise ValueError("Template registry changed during preparation")
            if json.loads(staging.read_bytes()) != catalog:
                raise ValueError("Template snapshot readback mismatch")
            if target.is_symlink():
                raise ValueError("Template output became a symlink during preparation")
            os.replace(staging, target)
        finally:
            staging.unlink(missing_ok=True)
    return {"path": str(target), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository source root")
    parser.add_argument(
        "--output",
        default=OUTPUT,
        help="Only the fixed registered project path is accepted",
    )
    parser.add_argument("--check", action="store_true", help="Require existing bytes to match")
    args = parser.parse_args()
    try:
        result = prepare(args.root, args.output, check=args.check)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"{result['path']}: {result['bytes']} bytes SHA256 {result['sha256']}")


if __name__ == "__main__":
    main()
