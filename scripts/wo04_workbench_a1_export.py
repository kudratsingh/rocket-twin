"""Prepare the independently versioned A1 snapshot without engineering execution."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.api.workbench_a1 import build_workbench_a1


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--output", type=Path, default=ROOT / "web/public/engineering-workbench/g80-a1.json"
    )
    a = p.parse_args()
    document = build_workbench_a1()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n")
    print(a.output)


if __name__ == "__main__":
    main()
