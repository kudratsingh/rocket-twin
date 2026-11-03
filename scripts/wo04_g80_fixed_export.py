"""Prepare exact-source F1 drawings; no numerical or CAD execution."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.api.workbench_g80_fixed import build_conventional_g80

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(build_conventional_g80(), indent=2) + "\n")
    print(a.output)
