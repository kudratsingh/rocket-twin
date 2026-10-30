"""Run the read-only WO-03 recovery integration report for every active mode."""

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

from src.analysis.recovery_integration import recovery_integration
from src.cad.parts import shape_digest
from src.vehicle.schema import load_vehicle, vehicle_input_paths


def digest_sources(paths: set[Path]) -> dict[str, str]:
    return {
        path.resolve()
        .relative_to(Path.cwd())
        .as_posix(): hashlib.sha256(path.read_bytes())
        .hexdigest()
        for path in sorted(paths)
        if path.is_file()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    args = parser.parse_args()

    engineering_path = Path("configs/engineering/wo03.yaml")
    engineering = yaml.safe_load(engineering_path.read_text())
    platform = yaml.safe_load(args.config.read_text())
    vehicle_paths = [Path(value) for value in platform["vehicles"]]
    g54_path = Path("configs/vehicle/wo02/performance-g54.yaml")
    if g54_path not in vehicle_paths:
        vehicle_paths.append(g54_path)

    run_id = datetime.now(UTC).strftime("wo03-recovery-integration-%Y%m%dT%H%M%S%fZ")
    output = Path("runs") / run_id
    output.mkdir(parents=True, exist_ok=False)
    # Fail closed if CAD caches do not match the active source revision. Mass,
    # CG, and BRep geometry must all come from a normal validated resolution.
    vehicles = [(path, load_vehicle(path)) for path in vehicle_paths]

    source_paths: set[Path] = {
        args.config,
        engineering_path,
        Path(__file__).resolve().relative_to(Path.cwd()),
        Path("src/analysis/recovery_integration.py"),
        Path("src/vehicle/schema.py"),
        Path("src/vehicle/mass.py"),
        Path("src/vehicle/geometry.py"),
    }
    source_paths.update(Path("src/cad").glob("*.py"))
    for path, _ in vehicles:
        source_paths.update(vehicle_input_paths(path))
    hashes_before = digest_sources(source_paths)

    results: list[dict[str, Any]] = []
    for path, vehicle in vehicles:
        results.append(
            {
                "source_spec_path": path.as_posix(),
                "configuration_id": vehicle.id,
                "resolved_spec_sha256": hashlib.sha256(
                    vehicle.model_dump_json(by_alias=True).encode()
                ).hexdigest(),
                "part_shape_sha256": {
                    part.id: shape_digest(part) for part in vehicle.parts if part.cad
                },
                "result": recovery_integration(vehicle, engineering),
            }
        )

    hashes_after = digest_sources(source_paths)
    cad_sources = sorted(Path("src/cad").glob("*.py"))
    cad_revision = hashlib.sha256(b"".join(path.read_bytes() for path in cad_sources)).hexdigest()
    record = {
        "run_id": run_id,
        "run_kind": "read-only calculated integration screens using normal validated Vehicle loads, reconciled CAD mass caches, and current source geometry",
        "cad_cache_validation": "All vehicle sources passed the standard loader with reconciled CAD caches. No cache was edited during analysis.",
        "inputs_unchanged": hashes_before == hashes_after,
        "source_hashes_before": hashes_before,
        "source_hashes_after": hashes_after,
        "cad_revision_sha256": cad_revision,
        "recovery_load_basis": engineering["loads"].get("recovery_basis"),
        "results": results,
        "acceptance_closed": False,
        "flight_ready": False,
    }
    (output / "record.json").write_text(
        json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(output / "record.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
