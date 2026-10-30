"""Generate WO-03 per-configuration traceability exports and readable registers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.traceability import generate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/engineering/traceability.yaml")
    )
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    args = parser.parse_args()
    outputs = generate(args.config, args.preset)
    for output in outputs:
        print(output)
    print("docs/requirements.md\ndocs/interfaces.md\ndocs/fmea.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
