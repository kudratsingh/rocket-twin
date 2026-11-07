"""One bounded in-process GET-only smoke against actual saved frontend data.

No sockets, browser, model/CAD execution, run creation, installs or owner-data writes.
Operational stop: 19 CPU / 59 wall seconds, with hard 20 CPU / 60 wall limits.
"""

from __future__ import annotations

import gc
import hashlib
import json
import os
import resource
import signal
import struct
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/studies/frontend-release-20261107/backend-smoke.json"
REPORT = OUTPUT.with_suffix(".md")
RUN = "exp-ab60bd4ac5c2412a9dd85f712072bca2"
RP1 = "G80-F2-RP1-AD1-definition-v2"


class BudgetStop(RuntimeError):
    """The single declared attempt stopped; do not retry automatically."""


def main() -> int:
    cpu_start, wall_start = time.process_time(), time.monotonic()
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "ARROW_NUM_THREADS",
    ):
        os.environ[name] = "1"
    sys.path.insert(0, str(ROOT))
    evidence: dict[str, Any] = {
        "schema": "rocket-twin-in-process-backend-smoke-v1",
        "started_at": datetime.now(UTC).isoformat(),
        "status": "running",
        "scope": "Actual saved data through TestClient(create_app(ROOT)); no socket/network/browser/new simulation",
        "budget": {
            "attempts": 1,
            "request_concurrency": 1,
            "numeric_arrow_threads": 1,
            "cpu_seconds_hard": 20,
            "wall_seconds_hard": 60,
            "operational_cpu_seconds": 19,
            "operational_wall_seconds": 59,
            "cpu_affinity": "Not asserted; numerical/Arrow parallelism restricted to one and total process CPU time limited",
        },
        "requests": [],
        "checks": {},
        "owner_records": {},
        "browser_observed": False,
        "normal_host_preview_observed": False,
        "engineering_accepted": False,
        "flight_ready": False,
    }

    def persist() -> None:
        evidence["elapsed_cpu_seconds"] = time.process_time() - cpu_start
        evidence["elapsed_wall_seconds"] = time.monotonic() - wall_start
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        temp = OUTPUT.with_suffix(".tmp")
        temp.write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n")
        os.replace(temp, OUTPUT)

    def stop(_signal: int, _frame: Any) -> None:
        raise BudgetStop("One-attempt CPU/wall budget reached; stopped without retry")

    def budget() -> None:
        if time.process_time() - cpu_start >= 19 or time.monotonic() - wall_start >= 59:
            raise BudgetStop(
                "One-attempt operational CPU/wall budget reached; stopped without retry"
            )

    def digest(path: Path) -> str:
        budget()
        h = hashlib.sha256()
        with path.open("rb") as handle:
            while block := handle.read(1024 * 1024):
                h.update(block)
                budget()
        return h.hexdigest()

    def records() -> dict[str, str]:
        return {
            str(path.relative_to(ROOT)): digest(path)
            for path in sorted((ROOT / "runs").glob("*/record.json"))
        }

    signal.signal(signal.SIGXCPU, stop)
    signal.signal(signal.SIGALRM, stop)
    _current_soft, current_hard = resource.getrlimit(resource.RLIMIT_CPU)
    hard = 20 if current_hard == resource.RLIM_INFINITY else min(20, current_hard)
    resource.setrlimit(resource.RLIMIT_CPU, (min(19, hard), hard))
    signal.setitimer(signal.ITIMER_REAL, 60)
    persist()
    before: dict[str, str] = {}
    files_before: dict[str, str] = {}
    try:
        before = records()
        files_before = {
            name: digest(ROOT / "runs" / RUN / name)
            for name in ("record.json", "resolved.json", "telemetry.parquet")
        }
        evidence["owner_records"]["before_sha256"] = before
        evidence["exact_run_files_before_sha256"] = files_before
        persist()
        import numpy as np
        import pyarrow as pa
        from fastapi.testclient import TestClient
        from pyarrow import ipc

        from src.api.app import create_app

        pa.set_cpu_count(1)
        pa.set_io_thread_count(1)
        construction_start = time.monotonic()
        app = create_app(ROOT)
        evidence["app_construction_wall_seconds"] = time.monotonic() - construction_start
        budget()
        with TestClient(app) as client:

            def get(url: str) -> Any:
                budget()
                if not url.startswith("/api/") or urlsplit(url).netloc:
                    raise ValueError("Only relative in-process API GET requests are allowed")
                evidence["current_stage"] = url
                persist()
                started_cpu, started_wall = time.process_time(), time.monotonic()
                response = client.get(url)
                evidence["requests"].append(
                    {
                        "method": "GET",
                        "url": url,
                        "status": response.status_code,
                        "response_bytes": len(response.content),
                        "response_sha256": hashlib.sha256(response.content).hexdigest(),
                        "cpu_seconds": time.process_time() - started_cpu,
                        "wall_seconds": time.monotonic() - started_wall,
                        "content_type": response.headers.get("content-type"),
                    }
                )
                persist()
                if response.status_code != 200:
                    raise RuntimeError(f"GET {url} returned {response.status_code}; no retry")
                budget()
                return response

            assert get("/api/health").json()["flight_ready"] is False
            catalog = get("/api/vehicles").json()
            assert catalog["default_design_id"] == RP1
            source = get(f"/api/vehicles/{RP1}").json()
            geometry = get(f"/api/design/{RP1}/inspection-geometry").json()
            assert source["id"] == RP1
            assert (
                source["identity"]["specification_sha256"]
                == geometry["identity"]["specification_sha256"]
            )
            represented = [part for part in source["parts"] if part.get("mesh_url")]
            assert len(source["parts"]) == 55 and len(represented) == 26
            mesh_checks = []
            for part in represented:
                response = get(part["mesh_url"])
                payload = response.content
                expected = parse_qs(urlsplit(part["mesh_url"]).query)["mesh"][0]
                actual = hashlib.sha256(payload).hexdigest()
                assert actual == expected
                assert len(payload) >= 20 and payload[:4] == b"glTF"
                version, length, json_length, json_kind = struct.unpack_from("<IIII", payload, 4)
                assert version == 2 and length == len(payload) and json_kind == 0x4E4F534A
                document = json.loads(payload[20 : 20 + json_length])
                assert document["asset"]["version"] == "2.0"
                mesh_checks.append(
                    {
                        "part_id": part["id"],
                        "bytes": len(payload),
                        "sha256": actual,
                        "glb_v2_header_and_json": True,
                    }
                )
            evidence["checks"]["rp1"] = {
                "source_parts": len(source["parts"]),
                "represented_glb_count": len(represented),
                "identity": source["identity"],
                "mesh_checks": mesh_checks,
                "complete_installed_geometry": False,
            }
            analyses = get(f"/api/vehicles/{RP1}/analyses").json()
            assert analyses["analyses"] == []
            evidence["checks"]["rp1_analyses"] = analyses
            record = get(f"/api/runs/{RUN}").json()
            assert record["status"] == "complete" and record["trajectory_complete"] is True
            vehicle = get(f"/api/vehicles/{record['vehicle_id']}").json()
            assert vehicle["id"] == record["configuration"] == record["vehicle_id"]
            assert vehicle["identity"]["resolved_spec_sha256"] == record["resolved_sha256"]
            assert vehicle["identity"]["cad_revision_sha256"] == record["cad_revision_sha256"]
            bounded = get(f"/api/runs/{RUN}/telemetry").json()
            assert bounded["frame"] == "NED; body x forward; quaternion scalar first"
            assert bounded["sampling"]["mode"] == "bounded"
            assert bounded["full_sample_count"] == 132856
            assert bounded["returned_sample_count"] <= 3000 + 2 * len(record["events"])
            bounded_count = bounded["returned_sample_count"]
            evidence["checks"]["bounded"] = {
                "returned_rows": bounded_count,
                "raw_rows": bounded["full_sample_count"],
                "channels": len(bounded["columns"]),
                "sampling": bounded["sampling"],
                "window_s": [bounded["columns"]["time_s"][0], bounded["columns"]["time_s"][-1]],
            }
            del bounded, response, payload, document
            gc.collect()
            native_response = get(f"/api/runs/{RUN}/telemetry?playback=full-rate-benchmark")
            native = native_response.json()
            assert native["run_id"] == RUN
            assert native["frame"] == "NED; body x forward; quaternion scalar first"
            assert native["source_identity"]["resolved_sha256"] == record["resolved_sha256"]
            assert native["source_identity"]["cad_revision_sha256"] == record["cad_revision_sha256"]
            assert native["sampling"]["mode"] == "full-rate-benchmark"
            assert native["full_sample_count"] == native["returned_sample_count"] == 132856
            assert len(native["columns"]) <= 73
            assert all(len(column) == 132856 for column in native["columns"].values())
            times = np.asarray(native["columns"]["time_s"])
            intervals = np.diff(times)
            assert np.isfinite(times).all() and (intervals > 0).all()
            assert np.allclose(intervals, 0.001, rtol=0, atol=1e-9)
            assert float(times[-1] - times[0]) >= 120
            evidence["checks"]["native"] = {
                "run_id": RUN,
                "configuration": record["configuration"],
                "record_sha256": files_before["record.json"],
                "resolved_sha256": record["resolved_sha256"],
                "cad_revision_sha256": record["cad_revision_sha256"],
                "recorded_simulation_code_sha256": record["code_sha256"],
                "returned_rows": len(times),
                "raw_rows": native["full_sample_count"],
                "channels": len(native["columns"]),
                "response_bytes": len(native_response.content),
                "window_s": [float(times[0]), float(times[-1])],
                "duration_between_endpoints_s": float(times[-1] - times[0]),
                "interval_min_s": float(intervals.min()),
                "interval_max_s": float(intervals.max()),
                "every_interval_matches_1ms_within_1ns": True,
                "sampling": native["sampling"],
                "all_channel_row_counts_match": True,
                "trajectory_complete": record["trajectory_complete"],
                "flight_ready": record["flight_ready"],
            }
            del native, native_response, times, intervals
            gc.collect()
            arrow_response = get(f"/api/runs/{RUN}/telemetry.arrow")
            with ipc.open_stream(arrow_response.content) as stream:
                metadata = json.loads(stream.schema.metadata[b"rocket-twin-playback"])
                table = stream.read_all()
                assert table.num_rows == bounded_count
                assert metadata["sampling"]["mode"] == "bounded"
                assert metadata["run_id"] == RUN and metadata["full_sample_count"] == 132856
                evidence["checks"]["arrow"] = {
                    "returned_rows": table.num_rows,
                    "channels": table.num_columns,
                    "response_bytes": len(arrow_response.content),
                    "profile": metadata["sampling"]["mode"],
                    "schema_source_identity_matches": metadata["source_identity"]["resolved_sha256"]
                    == record["resolved_sha256"],
                }
            del arrow_response, table
        budget()
        evidence["status"] = "passed"
    except Exception as error:  # noqa: BLE001 - persist failed evidence without retry
        evidence["status"] = "stopped" if isinstance(error, BudgetStop) else "failed"
        evidence["error"] = f"{type(error).__name__}: {error}"
    finally:
        # This cleanup is part of the same hard process budget, never a second attempt.
        try:
            after = records()
            evidence["owner_records"]["after_sha256"] = after
            evidence["owner_records"]["count"] = len(before)
            evidence["owner_records"]["all_records_unchanged"] = before == after
            evidence["owner_records"]["changed_paths"] = sorted(
                path for path in set(before) | set(after) if before.get(path) != after.get(path)
            )
            files_after = {name: digest(ROOT / "runs" / RUN / name) for name in files_before}
            evidence["exact_run_files_after_sha256"] = files_after
            evidence["exact_run_files_unchanged"] = files_before == files_after
            if before != after or files_before != files_after:
                evidence["status"] = "failed"
        except Exception as error:  # noqa: BLE001 - preserve cleanup failure evidence
            evidence["cleanup_error"] = f"{type(error).__name__}: {error}"
            evidence["status"] = "stopped"
        usage = resource.getrusage(resource.RUSAGE_SELF)
        evidence["peak_rss"] = {
            "value": usage.ru_maxrss,
            "units": "bytes" if sys.platform == "darwin" else "KiB",
            "scope": "Peak of this in-process Python API smoke, including imports/JSON parsing; not browser, GPU or normal-host preview memory",
        }
        evidence["finished_at"] = datetime.now(UTC).isoformat()
        persist()
        signal.setitimer(signal.ITIMER_REAL, 0)
        report(evidence)
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "requests": len(evidence["requests"]),
                "cpu_seconds": evidence["elapsed_cpu_seconds"],
                "wall_seconds": evidence["elapsed_wall_seconds"],
                "json": str(OUTPUT.relative_to(ROOT)),
                "report": str(REPORT.relative_to(ROOT)),
            }
        )
    )
    return 0 if evidence["status"] == "passed" else 1


def report(evidence: dict[str, Any]) -> None:
    native = evidence["checks"].get("native", {})
    mesh = evidence["checks"].get("rp1", {})
    text = f"""# Actual-data in-process backend smoke — 2026-11-07

Result: **{evidence['status']}**. One serial GET-only TestClient(create_app(ROOT))
attempt; no socket, network, browser, installation, CAD/model solve or new run.
Declared limit:20 process CPU seconds /60 wall seconds, numerical and Arrow
parallelism1; CPU affinity is not asserted. Measured CPU
{evidence['elapsed_cpu_seconds']:.3f} s / wall{evidence['elapsed_wall_seconds']:.3f} s.

- API requests completed: {len(evidence['requests'])}.
- RP1 source parts / validated GLBs: {mesh.get('source_parts', 'unavailable')} /
  {mesh.get('represented_glb_count', 'unavailable')}; every served GLB hash is
  checked against its source-pinned URL, with GLB2 header/length/JSON validation.
- RP1 compatible analyses remain an empty list; no substitute field is attached.
- Exact conditional G54 run: `{RUN}`. Matching archived configuration/resolved
  specification/CAD checks are required before telemetry checks.
- Native returned/raw rows: {native.get('returned_rows', 'unavailable')} /
  {native.get('raw_rows', 'unavailable')}; channels{native.get('channels', 'unavailable')}.
- Native window: {native.get('window_s', 'unavailable')} s;
  span{native.get('duration_between_endpoints_s', 'unavailable')} s. Every interval
  is checked against1 ms within1 ns when this stage completes.
- Native response body: {native.get('response_bytes', 'unavailable')} bytes in
  process. This is not a socket/network transfer or browser load measurement.
- Default JSON and Arrow retain the event-preserving bounded profile.
- Raw owner record files checked: {evidence['owner_records'].get('count', 'unavailable')};
  all unchanged: {evidence['owner_records'].get('all_records_unchanged', 'unavailable')}.
  Exact record/resolved/Parquet byte hashes unchanged:
  {evidence.get('exact_run_files_unchanged', 'unavailable')}.
- Peak RSS: {evidence['peak_rss']['value']} {evidence['peak_rss']['units']}, for
  this Python process including API/import/parsing costs. It is not browser
  memory, GPU usage, normal-host preview memory or a60 fps measurement.

{('Failure/stop: ' + evidence['error']) if evidence.get('error') else ''}

The complete request status/timing/byte-digest evidence and before/after owner
file hashes are in [backend-smoke.json](backend-smoke.json). Bulk telemetry and
GLB payloads are neither printed nor stored by this smoke. No `/api/runs` list
or nonterminal/failed experiment endpoint is requested; raw record fingerprints
are computed directly without lifecycle normalization.

This establishes backend startup and actual saved-data endpoint behavior inside
TestClient. Normal-host preview serving, browser rendering/interactions,
full-rate playback/scrub/memory/FPS acceptance, engineering acceptance and every
physical/build/test/paid-run/WO-10/flight gate remain open. RP1 AD1 does not inherit
this separate archived G54 flight dataset. All five inquiries remain UNSENT.
"""
    REPORT.write_text(text)


if __name__ == "__main__":
    raise SystemExit(main())
