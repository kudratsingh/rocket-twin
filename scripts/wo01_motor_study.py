"""Reproduce WO-01 motor screening without changing or approving the main spec."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.vehicle.schema import load_vehicle
from src.vehicle.selection import evaluate_candidate, screen_summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/studies/motor-selection.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    parser.add_argument("--compare", choices=["rocketpy"])
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    baseline_path = Path(config["baseline"])
    initial_bytes = baseline_path.read_bytes()
    baseline = load_vehicle(baseline_path)
    rows = []
    for c in config["candidates"]:
        for pose in [False, True]:
            for reserve in config["mount_reserve_kg"]:
                row = evaluate_candidate(baseline, c["curve"], reserve, pose, bool(args.compare))
                row.update(candidate=c["id"], evidence_status=c["evidence_status"])
                rows.append(row)
    screening = [
        screen_summary(baseline, item, max(config["mount_reserve_kg"]))
        for item in config.get("screening_only", [])
    ]
    assert baseline_path.read_bytes() == initial_bytes, "study must not modify the baseline"
    run_id = datetime.now(UTC).strftime("wo01-motors-%Y%m%dT%H%M%S%fZ")
    output = Path("runs") / run_id
    output.mkdir(parents=True)
    paths = [args.config, baseline_path, *[Path(c["curve"]) for c in config["candidates"]]]
    record = {
        "run_id": run_id,
        "work_order": "01",
        "preset": args.preset,
        "cost_usd": 0,
        "validation_status": "unvalidated motor selection; static math comparisons scoped per row",
        "input_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "code_sha256": hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted(Path("src/vehicle").glob("*.py")))
            + Path(__file__).read_bytes()
        ).hexdigest(),
        "source_urls": config["sources"],
        "rows": rows,
        "summary_screening": screening,
        "motor_selected": False,
        "main_spec_unchanged": True,
        "wo01_complete": False,
    }
    (output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    for row in rows:
        if row["pose"] == "hold_aft_station":
            print(
                f"{row['candidate']} +{row['incremental_mount_mass_kg']*1000:.0f} g mount: "
                f"{row['liftoff_mass_kg']*1000:.1f} g, TWR {row['mean_thrust_to_liftoff_weight']:.3f}, "
                f"burn {row['burn_time_s']:.3f} s, front shift {row['front_shift_m']*1000:.1f} mm; "
                f"reference {row.get('reference_comparison',{}).get('passed','not run')}"
            )
    for row in screening:
        print(
            f"{row['id']}: SUMMARY ONLY, worst listed-mass TWR {row['summary_only_twr']:.3f}; not eligible for selection"
        )
    print(f"No selection made. Source/fit evidence unresolved. Record: {output}/record.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
