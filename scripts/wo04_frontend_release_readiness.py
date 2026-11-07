"""Bounded read/hash-only release fixture inventory; no model or run execution."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CONFIGURATIONS = (
    "modular-performance-v1",
    "modular-performance-g54-hypothesis",
    "modular-tvc-finned-v1",
    "modular-tvc-finless-v1",
)
LONG_RUNS = (
    "exp-ab60bd4ac5c2412a9dd85f712072bca2",
    "exp-da02d58e35af404faf2802bea54c942b",
)
OUTPUT = "docs/studies/frontend-release-20261107/data-readiness.json"


def main() -> None:
    cpu_start, wall_start = time.process_time(), time.monotonic()

    import pyarrow.parquet as pq

    from src.analysis.records import AnalysisRecord
    from src.vehicle.cad_contract import digest

    def budget() -> None:
        if time.process_time() - cpu_start > 10 or time.monotonic() - wall_start > 20:
            raise TimeoutError("Readiness metadata audit exceeded 10 CPU / 20 wall seconds; stop")

    def hash_file(path: Path) -> str:
        budget()
        h = hashlib.sha256()
        with path.open("rb") as handle:
            while block := handle.read(1024 * 1024):
                h.update(block)
                budget()
        return h.hexdigest()

    def fingerprint(path: Path) -> dict[str, Any]:
        return {
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": hash_file(path),
        }

    def source_checks(expected: dict[str, str]) -> list[dict[str, Any]]:
        result = []
        for name, wanted in expected.items():
            path = (ROOT / name).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():
                actual = None
            else:
                actual = hash_file(path)
            result.append(
                {
                    "path": name,
                    "expected_sha256": wanted,
                    "current_sha256": actual,
                    "matches": wanted == actual,
                }
            )
        return result

    cad_paths = sorted((ROOT / "src/cad").glob("*.py"))
    cad_digest = hashlib.sha256(b"".join(p.read_bytes() for p in cad_paths)).hexdigest()
    configurations = []
    manifests = {}
    for configuration in CONFIGURATIONS:
        folder = ROOT / "build" / configuration
        manifest_path = folder / "manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifests[configuration] = manifest
        trace_path = folder / "traceability.json"
        trace = json.loads(trace_path.read_bytes())
        checks = source_checks(trace.get("source_sha256", {}))
        mesh_files = []
        for part in manifest["parts"]:
            path = folder / part["mesh"]
            mesh_files.append({"part_id": part["id"], **fingerprint(path)})
        identity = manifest["identity"]
        analyses = []
        paths = sorted(folder.glob("analysis/*/manifest.json"))
        if len(paths) > 256:
            raise ValueError("Analysis metadata exceeds the existing 256-manifest inspection limit")
        for path in paths:
            raw = json.loads(path.read_bytes())
            entry = {
                "manifest": fingerprint(path),
                "run_id": raw.get("run_id"),
                "compatible": False,
                "reason": None,
            }
            try:
                record = AnalysisRecord.model_validate(raw)
                same_identity = record.identity.model_dump() == identity
                asset_checks = []
                fields = []
                for field in record.fields:
                    if field.artifact:
                        asset = (path.parent / field.artifact).resolve()
                        if not asset.is_relative_to(path.parent.resolve()):
                            raise ValueError("Analysis artifact escapes its registered folder")
                        actual = hash_file(asset) if asset.is_file() else None
                        asset_checks.append(
                            {
                                "path": str(asset.relative_to(ROOT)),
                                "expected_sha256": field.artifact_sha256,
                                "current_sha256": actual,
                                "matches": actual == field.artifact_sha256,
                            }
                        )
                    fields.append(
                        {
                            "id": field.id,
                            "quantity": field.quantity,
                            "association": field.association,
                            "sample_count": field.sample_count,
                            "provenance": field.evidence.provenance,
                            "validation": field.evidence.validation,
                            "unavailable_reason": field.unavailable_reason,
                        }
                    )
                entry.update(
                    identity=record.identity.model_dump(),
                    identity_matches=same_identity,
                    asset_checks=asset_checks,
                    fields=fields,
                )
                entry["compatible"] = same_identity and all(a["matches"] for a in asset_checks)
                if not same_identity:
                    entry["reason"] = (
                        "Recorded analysis configuration/spec/CAD/part identity differs from archived mesh identity"
                    )
                elif not entry["compatible"]:
                    entry["reason"] = "Recorded analysis artifact missing or hash mismatch"
            except (ValueError, OSError, TypeError) as error:
                entry["reason"] = str(error)
            analyses.append(entry)
            budget()
        configurations.append(
            {
                "id": configuration,
                "manifest": fingerprint(manifest_path),
                "identity": identity,
                "current_legacy_cad_matches": identity["cad_revision_sha256"] == cad_digest,
                "traceability": fingerprint(trace_path),
                "traceability_source_checks": checks,
                "traceability_identity_matches": trace.get("resolved_spec_sha256")
                == identity["resolved_spec_sha256"]
                and trace.get("cad_identity", {}).get("part_shape_sha256")
                == identity["part_shape_sha256"]
                and trace.get("cad_identity", {}).get("cad_generator_sha256") == cad_digest,
                "listed_meshes": mesh_files,
                "analysis_inventory": analyses,
                "analysis_counts": {
                    "registered": len(analyses),
                    "identity_and_asset_hash_compatible": sum(a["compatible"] for a in analyses),
                },
            }
        )

    runs = []
    record_paths = sorted((ROOT / "runs").glob("exp-*/record.json"))
    if len(record_paths) > 1000:
        raise ValueError("Saved experiment audit exceeds 1000-record bound")
    for path in record_paths:
        record = json.loads(path.read_bytes())
        rid = path.parent.name
        parquet = path.parent / "telemetry.parquet"
        entry = {
            "run_id": rid,
            "record": fingerprint(path),
            "status": record.get("status"),
            "trajectory_complete": record.get("trajectory_complete"),
            "configuration": record.get("configuration"),
            "configuration_path": record.get("configuration_path"),
            "recorded_samples": record.get("telemetry_samples"),
            "recorded_events_s": record.get("events"),
            "recorded_dt_s": record.get("case", {}).get("dt_s"),
            "resolved_spec_sha256": record.get("resolved_sha256"),
            "cad_revision_sha256": record.get("cad_revision_sha256"),
            "simulation_code_sha256": record.get("code_sha256"),
            "error": record.get("error"),
            "telemetry_present": parquet.is_file(),
        }
        if parquet.is_file():
            footer = pq.ParquetFile(parquet)
            time_column = footer.schema.names.index("time_s")
            groups = []
            for index in range(footer.metadata.num_row_groups):
                stats = footer.metadata.row_group(index).column(time_column).statistics
                groups.append(
                    {
                        "row_group": index,
                        "min_s": stats.min if stats and stats.has_min_max else None,
                        "max_s": stats.max if stats and stats.has_min_max else None,
                        "null_count": stats.null_count if stats else None,
                    }
                )
            entry["parquet_metadata"] = {
                "rows": footer.metadata.num_rows,
                "row_groups": footer.metadata.num_row_groups,
                "columns": footer.schema.names,
                "time_s_statistics": groups,
            }
        if rid in LONG_RUNS:
            entry["telemetry"] = fingerprint(parquet)
            resolved_path = path.parent / "resolved.json"
            resolved = json.loads(resolved_path.read_bytes())
            entry["saved_resolved_file"] = fingerprint(resolved_path)
            entry["input_source_checks"] = source_checks(record.get("input_sha256", {}))
            saved_parts = {p["id"]: digest(p["geometry"], p["cad"]) for p in resolved["parts"]}
            expected = manifests[record["configuration"]]["identity"]
            entry["matches_archived_mesh"] = {
                "configuration": resolved["id"]
                == expected["configuration_id"]
                == record["configuration"],
                "resolved_spec_sha256": record.get("resolved_sha256")
                == expected["resolved_spec_sha256"],
                "cad_revision_sha256": record.get("cad_revision_sha256")
                == expected["cad_revision_sha256"],
                "saved_resolved_part_shapes": saved_parts == expected["part_shape_sha256"],
            }
            entry["rate_basis"] = (
                "Recorded case.dt_s=0.001 s declares 1000 Hz; Parquet footer establishes count/time range and no null time values. No time array was read, so uniform intervals were not independently reverified."
            )
        runs.append(entry)
        budget()

    status_counts = dict(Counter(r["status"] for r in runs))
    candidate = next(r for r in runs if r["run_id"] == LONG_RUNS[0])
    time_groups = candidate["parquet_metadata"]["time_s_statistics"]
    window = [min(g["min_s"] for g in time_groups), max(g["max_s"] for g in time_groups)]
    fixture_available = (
        candidate["status"] == "complete"
        and candidate["trajectory_complete"] is True
        and candidate["recorded_dt_s"] == 0.001
        and candidate["parquet_metadata"]["rows"] >= 120000
        and window[1] - window[0] >= 120
        and all(candidate["matches_archived_mesh"].values())
        and all(check["matches"] for check in candidate["input_source_checks"])
    )
    result = {
        "schema_version": 1,
        "date": "2026-11-07",
        "scope": "Read/hash-only saved JSON, Parquet footer metadata, meshes and analysis artifact bytes. No model instantiation, CAD/flight/solver execution, API _record mutation, browser, rendering or performance profiling.",
        "bounds": {"cpu_seconds": 10, "wall_seconds": 20, "full_snapshot_used": False},
        "legacy_cad_revision_sha256": cad_digest,
        "audit_script": fingerprint(Path(__file__).resolve()),
        "reader_sources": [
            fingerprint(ROOT / name)
            for name in ("src/api/experiments.py", "src/api/app.py", "src/analysis/records.py")
        ],
        "legacy_cad_sources": [fingerprint(p) for p in cad_paths],
        "configurations": configurations,
        "saved_runs": runs,
        "status_inventory": {
            "counts": status_counts,
            "failed_examples": [r["run_id"] for r in runs if r["status"] == "failed"],
            "nonterminal_examples": [
                r["run_id"]
                for r in runs
                if r["status"] not in ("complete", "failed", "cancelled", "interrupted")
            ],
            "incomplete_trajectory_examples": [
                r["run_id"] for r in runs if r["trajectory_complete"] is False
            ],
        },
        "rv_q30": {
            "candidate_run_id": LONG_RUNS[0],
            "data_fixture_available": fixture_available,
            "browser_performance_accepted": False,
            "representative_window_s": window,
            "raw_sample_count": candidate["parquet_metadata"]["rows"],
            "raw_declared_rate_hz": 1 / candidate["recorded_dt_s"],
            "current_endpoint_policy": "At most 3000 uniform native samples plus event neighbours; endpoints retained. Existing endpoint does not deliver the full 132856-row raw fixture.",
            "remaining": [
                "Designated-runtime browser ownership/access",
                "Measure and declare actual host, viewport and playback payload",
                "Frame-time distribution and 60 fps criterion",
                "Load, memory and scrub metrics",
                "Independent raw time-step verification if a strict full-rate timing audit is required",
            ],
        },
        "limitations": [
            "This sequential local audit is not an atomic runtime snapshot or remote revision",
            "Mesh byte hashes are current fingerprints; historical manifests lack original expected GLB byte digests",
            "Analysis compatibility is manifest identity and artifact hash readiness; field payload schema/sample values were not re-read or recomputed",
            "Saved status=complete is distinct from trajectory_complete=true",
            "No physical validation or flight acceptance follows",
        ],
        "timing": {
            "cpu_seconds": time.process_time() - cpu_start,
            "wall_seconds": time.monotonic() - wall_start,
        },
    }
    budget()
    target = ROOT / OUTPUT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status_inventory": result["status_inventory"],
                "analysis_counts": {c["id"]: c["analysis_counts"] for c in configurations},
                "timing": result["timing"],
            }
        )
    )


if __name__ == "__main__":
    main()
