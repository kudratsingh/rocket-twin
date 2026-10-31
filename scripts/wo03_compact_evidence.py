"""Save compact numerical evidence while retaining raw report hashes and locations.

Per-edge mesh samples, per-section stress diagnostics and display-mode arrays are omitted.
Global quantities, all failure/validation flags and source identities are retained.
The complete original report stays in ignored build output; no solve is rerun.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def compact(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in {
                "root_band_corner_edge_lengths_mm",
                "regional_stress_by_actual_thickness_mm",
                "normalized_transverse_shapes",
            }:
                result[key] = {
                    "omitted_from_compact_record": True,
                    "entries": len(item),
                    "canonical_json_sha256": hashlib.sha256(
                        json.dumps(item, sort_keys=True, allow_nan=False).encode()
                    ).hexdigest(),
                    "availability": "Complete diagnostic retained in original report.",
                }
            else:
                result[key] = compact(item)
        return result
    if isinstance(value, list):
        return [compact(item) for item in value]
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", type=Path, nargs="+")
    parser.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    parser.add_argument("--output", type=Path, default=Path("runs"))
    parser.add_argument(
        "--record-id",
        help="Group reports without run IDs into a named projection; original report contents and hashes stay intact.",
    )
    parser.add_argument(
        "--suffix",
        default="",
        help="Artifact-folder suffix; original computation run ID is retained.",
    )
    args = parser.parse_args()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in args.reports:
        data = path.read_bytes()
        source = json.loads(data)
        record_id = args.record_id or source.get("run_id")
        if not record_id:
            raise ValueError(f"{path}: report has no run ID; supply --record-id for its projection")
        grouped[record_id].append(
            {
                "original_report": str(path),
                "original_report_sha256": hashlib.sha256(data).hexdigest(),
                "summary": compact(source),
            }
        )
    for run_id, reports in grouped.items():
        record = {
            "run_id": run_id,
            "work_order": "03",
            "record_kind": "Compact projection of original offline analysis reports; no new solve or acceptance decision.",
            "projection_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "reports": reports,
            "inputs_unchanged": all(r["summary"].get("inputs_unchanged", False) for r in reports),
            "acceptance_passed": False,
            "flight_ready": False,
            "cost_usd": 0,
        }
        folder = args.output / (run_id + args.suffix)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "record.json"
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite existing evidence: {path}")
        path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
