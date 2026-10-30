"""Evaluate all actual modular configurations at WO-01 preliminary design scope."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.vehicle.benchmark import evaluate_preliminary
from src.vehicle.schema import load_vehicle, vehicle_input_paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    parser.add_argument("--compare", choices=["rocketpy"])
    parser.add_argument("--require-benchmark", action="store_true")
    args = parser.parse_args()
    start = time.perf_counter()
    platform = yaml.safe_load(args.config.read_text())
    vehicles = [load_vehicle(p) for p in platform["vehicles"]]
    common_ids = {
        p["id"] for p in yaml.safe_load(Path(platform["shared_upper"]).read_text())["parts"]
    }
    shared_parts = [
        {p.id: p.model_dump(by_alias=True) for p in v.parts if p.id in common_ids} for v in vehicles
    ]
    shared_consistent = all(parts == shared_parts[0] for parts in shared_parts)
    rows = [evaluate_preliminary(v, bool(args.compare)) for v in vehicles]
    paths = {args.config, Path(platform["shared_upper"])}
    for p, vehicle in zip(platform["vehicles"], vehicles):
        paths.update(vehicle_input_paths(p))
        assert vehicle.motor and vehicle.motor.curve
        paths.update([Path(vehicle.motor.curve), Path(vehicle.motor.curve).with_suffix(".yaml")])
    run_id = datetime.now(UTC).strftime("wo01-platform-%Y%m%dT%H%M%S%fZ")
    out = Path("runs") / run_id
    out.mkdir()
    checks = {
        "all_three_modes_present": {v.design.mode for v in vehicles if v.design}
        == {"performance", "tvc_finned", "tvc_finless"},
        "shared_upper_consistent": shared_consistent,
        "all_mode_benchmarks_pass": all(row["preliminary_design_benchmark_passed"] for row in rows),
        "cpu_runtime_under_120s": time.perf_counter() - start < 120,
    }
    record = {
        "run_id": run_id,
        "work_order": "01",
        "preset": args.preset,
        "cost_usd": 0,
        "checks": checks,
        "wo01_preliminary_benchmark_passed": all(checks.values()),
        "flight_ready": False,
        "vehicles": rows,
        "input_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},
        "code_sha256": hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted(Path("src/vehicle").glob("*.py")))
            + Path(__file__).read_bytes()
        ).hexdigest(),
        "elapsed_s": time.perf_counter() - start,
    }
    (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    for v, row in zip(vehicles, rows):
        # Derived inventory preview; CAD/build pack implementations remain WO-03/09.
        inventory = [p.model_dump(by_alias=True, exclude_none=True) for p in v.parts]
        (out / (v.id + "-inventory.json")).write_text(json.dumps(inventory, indent=2) + "\n")
        (out / (v.id + "-resolved.json")).write_text(
            v.model_dump_json(by_alias=True, indent=2) + "\n"
        )
        screen = row["launch_screen"]
        print(
            f"{v.id}: {row['nominal_mass_kg']*1000:.1f} g + allowance -> {screen['worst_case_mass_kg']*1000:.1f} g; rail {screen['rail_exit_speed_mps']} m/s; useful control {screen['longest_useful_control_interval_s']:.2f} s"
        )
        print("  " + ", ".join(f"{k}={v}" for k, v in row["checks"].items()))
    print(f"Preliminary model only, flight_ready=false. Record: {out}/record.json")
    return int(args.require_benchmark and not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
