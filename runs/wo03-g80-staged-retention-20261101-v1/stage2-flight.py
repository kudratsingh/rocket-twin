"""Run existing candidate-flight wrapper, then report ground-relative landing speeds."""

import json
import runpy
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

root = Path(__file__).resolve().parents[1]
sys.argv = [
    str(root / "scripts/wo03_g80_candidate_flight.py"),
    "--config",
    str(root / "configs/studies/wo03-g80-stage2-flight.yaml"),
    "--output",
    str(root / "build/wo03-g80-stage2-flight"),
]
runpy.run_path(sys.argv[0], run_name="__main__")
out = root / "build/wo03-g80-stage2-flight"
record = json.loads((out / "record.json").read_text())
landing = {}
for row in record["cases"]:
    path = out / (row["case_name"] + ".parquet")
    table = pq.read_table(path, columns=["landed", "vn_mps", "ve_mps", "vd_mps"])
    a = {name: np.asarray(table[name]) for name in table.column_names}
    hits = np.flatnonzero(a["landed"] > 0)
    if len(hits):
        idx = max(int(hits[0]) - 1, 0)
        horizontal = float(np.hypot(a["vn_mps"][idx], a["ve_mps"][idx]))
        total = float(
            np.sqrt(a["vn_mps"][idx] ** 2 + a["ve_mps"][idx] ** 2 + a["vd_mps"][idx] ** 2)
        )
        landing[row["case_name"]] = {
            "horizontal_ground_speed_mps": horizontal,
            "total_ground_speed_mps": total,
            "screen_6mps": total <= 6,
            "velocity_sample": "last pre-landed telemetry row; 5 ms grid",
            "physical_acceptance": False,
        }
    else:
        landing[row["case_name"]] = {
            "horizontal_ground_speed_mps": None,
            "total_ground_speed_mps": None,
            "screen_6mps": None,
            "velocity_sample": "no landing in horizon",
            "physical_acceptance": False,
        }
(out / "landing-screens.json").write_text(json.dumps(landing, indent=2) + "\n")
