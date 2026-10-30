"""Run preliminary motor support load-path screens for resolved configurations."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.engineering import structural
from src.analysis.motor_support import motor_support
from src.vehicle.schema import load_vehicle, vehicle_input_paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    parser.add_argument("--reverse-load-n", type=float, default=150.0)
    args = parser.parse_args()
    cfg_path = Path("configs/engineering/wo03.yaml")
    cfg = yaml.safe_load(cfg_path.read_text())
    platform = yaml.safe_load(args.config.read_text())
    paths = [Path(path) for path in platform["vehicles"]]
    g54 = Path("configs/vehicle/wo02/performance-g54.yaml")
    if g54 not in paths:
        paths.append(g54)
    run = datetime.now(UTC).strftime("wo03-motor-support-%Y%m%dT%H%M%S%fZ")
    out = Path("runs") / run
    out.mkdir(parents=True, exist_ok=False)
    summaries: list[dict[str, Any]] = []
    source_paths: set[Path] = {
        args.config,
        cfg_path,
        Path(__file__).resolve().relative_to(Path.cwd()),
        Path("src/analysis/motor_support.py"),
        Path("src/analysis/engineering.py"),
        Path("src/vehicle/schema.py"),
        Path("src/vehicle/geometry.py"),
    }
    source_paths.update(Path("src/cad").glob("*.py"))
    vehicles = []
    for vehicle_path in paths:
        source_paths.update(vehicle_input_paths(vehicle_path))
        vehicles.append((vehicle_path, load_vehicle(vehicle_path)))

    def digest_sources() -> dict[str, str]:
        return {
            p.resolve()
            .relative_to(Path.cwd())
            .as_posix(): hashlib.sha256(p.read_bytes())
            .hexdigest()
            for p in sorted(source_paths)
            if p.is_file()
        }

    hashes_before = digest_sources()
    for vehicle_path, vehicle in vehicles:
        screen = structural(vehicle, cfg)
        summaries.append(
            {
                "vehicle_path": vehicle_path.as_posix(),
                "peak_scaled_thrust_source": "src.analysis.engineering.structural using configs/engineering/wo03.yaml; thrust multiplier applied by that function",
                "result": motor_support(
                    vehicle,
                    cfg,
                    float(screen["peak_scaled_thrust_n"]),
                    args.reverse_load_n,
                ),
            }
        )
    hashes_after = digest_sources()
    payload = {
        "run_id": run,
        "inputs_unchanged": hashes_before == hashes_after,
        "run_kind": "calculated preliminary analytical screens; not acceptance evidence",
        "source_hashes_before": hashes_before,
        "source_hashes_after": hashes_after,
        "assumptions": {
            "G11_modulus_pa": cfg["materials"]["G11"]["youngs_pa"],
            "G11_strength_cold_pa": cfg["materials"]["G11"]["strength_pa"],
            "G11_strength_hot_screen_pa": cfg["materials"]["G11"]["hot_strength_screen_pa"],
            "plywood_modulus_pa": cfg["materials"]["plywood"]["youngs_pa"],
            "plywood_strength_pa": cfg["materials"]["plywood"]["strength_pa"],
            "bond_strength_cold_estimate_pa": cfg["materials"]["epoxy"]["cold_strength_screen_pa"],
            "bond_strength_hot_estimate_pa": cfg["materials"]["epoxy"]["hot_strength_screen_pa"],
            "mica_compression_screen_pa": 20e6,
            "design_factor": cfg["loads"]["design_factor"],
            "reverse_load_n": args.reverse_load_n,
        },
        "results": summaries,
        "acceptance_closed": False,
        "flight_ready": False,
        "notes": [
            "No material/property values are qualified allowables; stated cold/hot screens are assumptions.",
            "No physical case, shoulder, nozzle, closure or fastener dimensions are verified.",
            "No measured proof load or assembled contact/bond data are represented.",
        ],
    }
    (out / "record.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    print(out / "record.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
