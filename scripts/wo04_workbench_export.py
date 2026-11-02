"""Export the frozen C1 walkthrough and its hash manifest; never run analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.api.workbench import WorkbenchUnavailable, build_workbench


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "build/engineering-workbench/g80-c1.json"
    )
    args = parser.parse_args()
    try:
        document = build_workbench(args.root)
    except WorkbenchUnavailable as error:
        print(f"Workbench export unavailable: {error}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n")
    manifest_path = args.output.with_name(f"{args.output.stem}-source-manifest.json")
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": document["schema_version"],
                "id": document["id"],
                "identity": document["identity"],
                "sources": document["generated_from"],
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Exported {args.output} and {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
