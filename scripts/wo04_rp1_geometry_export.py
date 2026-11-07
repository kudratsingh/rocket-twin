"""Export bounded RP1 inspection geometry, without physics or manufacturing CAD."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.inspection.rp1_geometry import EVIDENCE, export


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--record-evidence",
        action="store_true",
        help="Update the tracked audit manifest after a deliberate source/code change",
    )
    args = parser.parse_args()
    manifest = export(ROOT)
    if args.record_evidence:
        path = ROOT / EVIDENCE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"geometry_id": manifest["geometry_id"], "coverage": manifest["coverage"]}))


if __name__ == "__main__":
    main()
