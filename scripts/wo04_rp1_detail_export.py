"""Explicit optional RP1 display-detail export; frozen core GLBs are untouched."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.inspection.rp1_detail import CATALOG, export


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--record-catalog",
        action="store_true",
        help="Deliberately refresh tracked source-detail catalog",
    )
    args = parser.parse_args()
    packet = export(ROOT)
    if args.record_catalog:
        path = ROOT / CATALOG
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(packet, indent=2) + "\n")
    print(
        json.dumps(
            {
                "id": packet["id"],
                "detail_sha256": packet["detail_sha256"],
                "parts": [
                    {
                        "id": p["part_id"],
                        "core_triangles": p["core_triangles"],
                        "detail_triangles": p["triangles"],
                    }
                    for p in packet["parts"]
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
