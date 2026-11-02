"""Export the source-checked engineering extension without running analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.api.workbench import WorkbenchUnavailable
from src.api.workbench_extended import build_workbench_extended


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "build/engineering-workbench/g80-extended.json"
    )
    args = parser.parse_args()
    try:
        document = build_workbench_extended(args.root)
    except WorkbenchUnavailable as error:
        print(f"Engineering extension unavailable: {error}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n")
    manifest = args.output.with_name(f"{args.output.stem}-source-manifest.json")
    manifest.write_text(
        json.dumps(
            {
                "id": document["id"],
                "schema_version": document["schema_version"],
                "identity": document["identity"],
                "sources": document["generated_from"],
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Exported {args.output} and {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
