#!/usr/bin/env python3
"""Create a compact, hash-checked projection of the preserved reciprocity audit."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "build/wo03-g80-bridge-reciprocity-audit-v1/record.json"
OUT = Path(__file__).resolve().parent / "record.json"
CASE = ROOT / "build/wo03-g80-bridge-area-budget-coarse-v1/bridge_1p5mm"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    raw = json.loads(RAW.read_text())
    dat, inp, sta = CASE / "case.dat", CASE / "case.inp", CASE / "case.sta"
    tracked = {
        "raw_audit_record": RAW,
        "case_inp": inp,
        "case_dat": dat,
        "case_sta": sta,
        "mesh_meta": CASE / "mesh-meta.json",
        "prior_campaign_record": ROOT / "build/wo03-g80-bridge-area-budget-coarse-v1/record.json",
    }
    current_hashes = {name: sha256(path) for name, path in tracked.items()}

    # Preserve only exact step/increment/time rows, not generated nodal arrays.
    sta_rows = []
    for line in sta.read_text().splitlines():
        fields = line.split()
        if len(fields) == 7 and fields[0].isdigit() and fields[1].isdigit():
            sta_rows.append({
                "step": int(fields[0]),
                "increment": int(fields[1]),
                "attempt": int(fields[2]),
                "iterations": int(fields[3]),
                "total_time_token": fields[4],
                "step_time_token": fields[5],
                "increment_time_token": fields[6],
            })

    compact = {
        "status": "read_only_reciprocal_work_audit_compact_projection",
        "result": "reciprocity_failure_outside_print_rounding; prior force balance failure remains",
        "raw_record": "build/wo03-g80-bridge-reciprocity-audit-v1/record.json",
        "raw_record_sha256": current_hashes["raw_audit_record"],
        "source_sha256_before": raw["input_sha256_before"],
        "source_sha256_after": raw["source_sha256_after"],
        "source_hashes_unchanged_in_original_audit": raw["source_hashes_unchanged"],
        "current_source_hashes": current_hashes,
        "case": raw["case"],
        "model_and_steps": raw["linear_model_and_steps"],
        "field_completeness": {
            "nodes": raw["field_completeness"]["deck_node_count"],
            "support_nodes": raw["field_completeness"]["support_node_count"],
            "displacement_rows_by_step": raw["field_completeness"]["DAT_displacement_rows"],
            "support_force_rows_by_step": raw["field_completeness"]["DAT_support_force_rows"],
            "all_sets_complete_unique": raw["field_completeness"]["sets_complete_and_unique"],
            "DAT_table_headers": raw["field_completeness"]["DAT_table_headers"],
        },
        "native_status_rows": sta_rows,
        "load_row_counts": {
            "step1_equal_50_each": len(raw["serialized_cloads"]["step1_equal_50_each"]),
            "step2_single_150_on_patch0": len(raw["serialized_cloads"]["step2_single_150_on_patch0"]),
            "serialized_load_rows_omitted": len(raw["serialized_cloads"]["step1_equal_50_each"])
            + len(raw["serialized_cloads"]["step2_single_150_on_patch0"]),
        },
        "omissions": {
            "all_generated_nodal_displacement_arrays_omitted": True,
            "omitted_displacement_rows": sum(len(rows) for rows in raw["exact_as_run_displacements_mm"].values()),
            "omitted_support_reaction_vector_rows": sum(len(rows) for rows in raw["field_completeness"]["support_reaction_rows_exact"].values()),
            "omitted_serialized_CLOAD_rows": len(raw["serialized_cloads"]["step1_equal_50_each"])
            + len(raw["serialized_cloads"]["step2_single_150_on_patch0"]),
            "raw_audit_record_preserved_unchanged": True,
        },
        "reciprocal_work": raw["reciprocal_work"],
        "preserved_native_force_balance_failure": raw["preserved_native_force_balance_failure"],
        "resource_accounting": {
            "audit_cpu_s": None,
            "audit_wall_s": None,
            "note": "Not measured in the preserved audit record; no zero or cap-compliance inference.",
        },
        "output_backend_source_note": {
            "manual_2_23": "NODE OUTPUT documents mixed binary/ASCII FRD; no numeric width or double-width selector documented.",
            "official_master_frdvector": "asc writes text after float casts; bin writes float32 components; third/other branch writes double64 components; no user-facing selector for third branch found.",
            "version_match": "Master source is not pinned or verified identical to installed 2.23 source archive; installed RF encoding remains unresolved.",
            "execution_status": "No backend/output solver runs authorized or performed by the projection.",
        },
    }
    OUT.write_text(json.dumps(compact, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"record": str(OUT.relative_to(ROOT)), "sha256": sha256(OUT), "bytes": OUT.stat().st_size}, indent=2))


if __name__ == "__main__":
    main()
