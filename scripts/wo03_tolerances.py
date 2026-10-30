"""Execute source-driven WO-03 tolerance and thermal-expansion screens."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.tolerances import generate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/studies/wo03-tolerances.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    args = parser.parse_args()
    record = generate(args.config)
    print(record)
    if not json.loads(record.read_text()).get("inputs_unchanged", False):
        print(
            "Source provenance check failed: input hashes changed during the run.", file=sys.stderr
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
