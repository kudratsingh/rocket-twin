"""Write source-pinned AD1 connection metadata for the static preview."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.api.rp1_connections import build


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "web/public/engineering-workbench/rp1-connections.json",
    )
    args = parser.parse_args()
    content = json.dumps(build(ROOT), ensure_ascii=False, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".rp1-connections-", suffix=".tmp", dir=args.output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(name, args.output)
    finally:
        Path(name).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
