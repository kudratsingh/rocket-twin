"""Prepare one deterministic read-only RP1 parts-bank snapshot; never generate CAD."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.api.parts_bank import ID, build

OUTPUT = "web/public/engineering-workbench/rp1-parts-bank.json"


def prepare(root: Path, output: str = OUTPUT) -> dict[str, Any]:
    """Compute before writing, refuse foreign files, then atomically replace this snapshot."""
    root = root.resolve()
    target = root / OUTPUT
    requested = Path(output)
    requested = requested if requested.is_absolute() else root / requested
    if requested != target or not target.resolve().is_relative_to(root) or target.is_symlink():
        raise ValueError("Parts bank output must be the fixed registered project path")
    catalog = build(root)
    if target.exists():
        try:
            previous = json.loads(target.read_bytes())
        except (ValueError, OSError) as error:
            raise ValueError("Refusing to overwrite an unrelated parts-bank output") from error
        if (
            not isinstance(previous, dict)
            or previous.get("id") != ID
            or previous.get("configuration_id") != catalog["configuration_id"]
            or previous.get("schema_version") != 1
        ):
            raise ValueError("Refusing to overwrite an unrelated parts-bank output")
    data = (json.dumps(catalog, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if target.is_file() and target.read_bytes() == data:
        return {"status": "verified_existing", "revision_sha256": catalog["revision_sha256"]}
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".rp1-parts-bank-", dir=target.parent)
    staging = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # No source/module or asset availability may change during preparation.
        if build(root) != catalog:
            raise ValueError("Parts bank changed during preparation")
        if json.loads(staging.read_bytes()) != catalog:
            raise ValueError("Parts bank snapshot readback mismatch")
        os.replace(staging, target)
    finally:
        staging.unlink(missing_ok=True)
    return {"status": "prepared", "revision_sha256": catalog["revision_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", default=OUTPUT, help="Only the fixed registered path is accepted"
    )
    args = parser.parse_args()
    try:
        result = prepare(ROOT, args.output)
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "unavailable", "reason": str(error)}))
        return 1
    print(json.dumps({**result, "path": OUTPUT, "cad_or_physics_generated": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
