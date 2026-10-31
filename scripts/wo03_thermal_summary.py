"""Project recorded thermal rows into a small auditable case table; no new solve."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def summarize(path: Path) -> Path:
    source = json.loads(path.read_text())
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in source["rows"]:
        groups[row["candidate_id"], row["case_id"]].append(row)
    rows = []
    for (candidate, case), cases in sorted(groups.items()):
        worst_row, worst_peak = min(
            ((row, peak) for row in cases for peak in row["peaks"] if peak["margin_k"] is not None),
            key=lambda item: item[1]["margin_k"],
        )
        rows.append(
            {
                "candidate_id": candidate,
                "case_id": case,
                "case_role": worst_row["case_role"],
                "source_case_basis": worst_row["case_source_basis"],
                "rows": len(cases),
                "rows_exceeding_limits": sum(
                    bool(row["parts_over_declared_limit"]) for row in cases
                ),
                "worst_limited_part": worst_peak,
                "worst_corner": {
                    key: worst_row.get(key)
                    for key in (
                        "candidate_vehicle_identity_sha256",
                        "bond_gap_k_variant",
                        "bond_interface_contact_conductance_w_k_per_ring",
                        "material_property_corner",
                        "ambient_c",
                    )
                },
            }
        )
    result = {
        "run_id": source["run_id"],
        "record_kind": "Projection of existing thermal rows; no new simulation or acceptance decision",
        "original_artifact": str(path),
        "original_artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "projection_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_hashes": source["source_hashes"],
        "source_rows": len(source["rows"]),
        "case_summary": rows,
        "flight_ready": False,
    }
    target = path.with_name("case-summary.json")
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite recorded projection: {target}")
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", type=Path, nargs="+")
    args = parser.parse_args()
    for path in args.artifacts:
        print(summarize(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
