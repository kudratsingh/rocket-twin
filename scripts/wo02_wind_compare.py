"""Ancillary steady-crosswind reference check from an existing WO-02 study record."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.sim.reference import reference_flight
from src.vehicle.schema import load_vehicle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Full WO-02 study record.json")
    parser.add_argument("--preset", choices=["tiny", "sim"], default="sim")
    args = parser.parse_args()
    data = json.loads(args.config.read_text())
    rows = []
    for path in [
        "configs/vehicle/platform/performance.yaml",
        "configs/vehicle/platform/tvc-finned.yaml",
    ]:
        vehicle = load_vehicle(path)
        ref = reference_flight(vehicle, {"wind_east_mps": 1})
        own = next(
            x for x in data["cases"] if x["vehicle"] == vehicle.id and x.get("scenario") == "wind_1"
        )
        row = {
            "vehicle": vehicle.id,
            "case": {"wind_east_mps": 1},
            "reference": ref,
            "own_metrics": own["metrics"],
            "errors": {
                k: abs(own["metrics"][k] / ref[k] - 1) for k in ["apogee_agl_m", "apogee_time_s"]
            },
        }
        rows.append(row)
        print(vehicle.id, row["errors"])
    run = datetime.now(UTC).strftime("wo02-wind-%Y%m%dT%H%M%S%fZ")
    out = Path("runs") / run
    out.mkdir()
    record = {
        "run_id": run,
        "work_order": "02",
        "validation_scope": "Ancillary steady 1m/s crosswind comparison; not wind-gust/attitude/flight qualification",
        "base_run": str(args.config),
        "base_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_sha256": data["input_sha256"],
        "rows": rows,
        "flight_ready": False,
        "cost_usd": 0,
    }
    (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(out / "record.json")


if __name__ == "__main__":
    main()
