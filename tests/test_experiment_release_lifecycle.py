"""Bounded lifecycle fixtures: no simulator campaign or owner data mutation."""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import experiments as api


class DeferredExecutor:
    def __init__(self):
        self.work = None

    def submit(self, function, *args):
        self.work = lambda: function(*args)


@pytest.fixture
def harness(tmp_path, monkeypatch):
    executor = DeferredExecutor()
    monkeypatch.setattr(api, "RUNS", tmp_path)
    monkeypatch.setattr(api, "_executor", executor)
    monkeypatch.setattr(api, "_busy", __import__("threading").Lock())
    monkeypatch.setattr(api, "_cancel", {})
    app = FastAPI()
    app.include_router(api.router)
    return TestClient(app), executor, tmp_path


def test_bounded_batch_failure_provenance_and_retry(harness, monkeypatch):
    client, worker, root = harness
    cases = [
        {"configuration": "modular-performance-v1", "preset": "tiny", "seed": 11},
        {"configuration": "modular-performance-v1", "preset": "tiny", "seed": 12, "wind_mps": 1},
    ]
    assert (
        client.post("/api/experiment-batches", json={"cases": cases, "concurrency": 2}).status_code
        == 422
    )
    assert client.post("/api/experiment-batches", json={"cases": cases * 3}).status_code == 422
    response = client.post(
        "/api/experiment-batches",
        json={"cases": cases},
        headers={"Idempotency-Key": "fixture-batch-one"},
    )
    assert response.status_code == 202
    ids = response.json()["run_ids"]
    assert len(ids) == 2 and ids[0] != ids[1]
    assert client.post("/api/experiments", json=cases[0]).status_code == 409
    duplicate = client.post(
        "/api/experiment-batches",
        json={"cases": cases},
        headers={"Idempotency-Key": "fixture-batch-one"},
    )
    assert duplicate.json()["run_ids"] == ids
    changed = client.post(
        "/api/experiment-batches",
        json={"cases": list(reversed(cases))},
        headers={"Idempotency-Key": "fixture-batch-one"},
    )
    assert changed.status_code == 409

    def finish(run_id, request):
        record = api._record(run_id)
        record.update(
            status="failed" if request.seed == 11 else "complete",
            error="Controlled fixture failure" if request.seed == 11 else None,
        )
        api._save(root / run_id, record)

    monkeypatch.setattr(api, "_execute", finish)
    worker.work()
    records = client.get("/api/runs").json()
    assert {r["status"] for r in records} == {"failed", "complete"}
    for record in records:
        assert record["batch_members"] == ids
        assert record["resources"]["concurrency"] == 1
        assert record["resources"]["max_steps"] == 9000
        assert record["random_seed"] in (11, 12)
        assert len(record["normalized_request_sha256"]) == 64
    frozen = (root / ids[0] / "record.json").read_bytes()
    retry = client.post(
        "/api/experiments", json=cases[0], headers={"Idempotency-Key": "fixture-new-retry"}
    )
    assert retry.status_code == 202 and retry.json()["run_id"] not in ids
    assert (root / ids[0] / "record.json").read_bytes() == frozen
    worker.work()


def test_cancel_acknowledgement_precedes_terminal_state_and_cancels_all_members(harness):
    client, worker, _ = harness
    case = {"configuration": "modular-performance-v1", "preset": "tiny"}
    result = client.post("/api/experiment-batches", json={"cases": [case, case]}).json()
    cancelled = client.post(f"/api/experiments/{result['run_id']}/cancel")
    assert cancelled.status_code == 202
    assert {r["status"] for r in cancelled.json()["members"]} == {"cancel_requested"}
    # Existing worker still owns the CPU slot until it acknowledges every queued member.
    assert client.post("/api/experiments", json=case).status_code == 409
    worker.work()
    records = client.get("/api/runs").json()
    assert {r["status"] for r in records} == {"cancelled"}
    assert all(r["cancel_requested_at"] and r["finished_at"] for r in records)
    assert not any((api.RUNS / r["run_id"] / "telemetry.parquet").exists() for r in records)
    again = client.post(f"/api/experiments/{result['run_id']}/cancel").json()
    assert {r["status"] for r in again["members"]} == {"cancelled"}


def test_restart_retains_interrupted_attempt_and_rejects_unsupported_inputs(harness):
    client, _, root = harness
    run_id = "exp-" + "1" * 32
    folder = root / run_id
    folder.mkdir()
    (folder / "record.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "status": "running",
                "created_at": "fixture",
                "worker_session": "ended-process",
            }
        )
    )
    record = client.get(f"/api/runs/{run_id}").json()
    assert record["status"] == "interrupted"
    frozen = (folder / "record.json").read_bytes()
    assert client.get(f"/api/runs/{run_id}").json() == record
    assert (folder / "record.json").read_bytes() == frozen
    assert client.get(f"/api/runs/{run_id}/telemetry").status_code == 409
    for case in [
        {"configuration": "G80-F2-RP1-AD1-definition-v2"},
        {"configuration": "modular-performance-v1", "seed": -1},
        {"configuration": "modular-performance-v1", "seed": 2**32},
        {"configuration": "modular-performance-v1", "seed": 1.5},
    ]:
        assert client.post("/api/experiments", json=case).status_code == 422


def test_unexpected_worker_exit_marks_remaining_members_interrupted(harness, monkeypatch):
    client, worker, _ = harness
    case = {"configuration": "modular-performance-v1", "preset": "tiny"}
    result = client.post("/api/experiment-batches", json={"cases": [case, case]}).json()

    def broken_worker(*args):
        raise RuntimeError("Controlled worker interruption")

    monkeypatch.setattr(api, "_execute", broken_worker)
    with pytest.raises(RuntimeError, match="Controlled worker interruption"):
        worker.work()
    assert {client.get(f"/api/runs/{run_id}").json()["status"] for run_id in result["run_ids"]} == {
        "interrupted"
    }
    assert api._busy.acquire(blocking=False)
    api._busy.release()


def test_arrow_export_retains_bounded_columns_and_schema_provenance(harness, monkeypatch):
    from pyarrow import ipc

    client, _, _ = harness
    payload = {
        "run_id": "fixture-arrow",
        "frame": "NED; body x forward; quaternion scalar first",
        "full_sample_count": 120001,
        "returned_sample_count": 3,
        "sampling": {"uniform_limit": 3000, "interpolated": False},
        "channel_metadata": {"height_m": {"source": "backend-derived", "unit": "m"}},
        "columns": {"time_s": [0.0, 60.0, 120.0], "height_m": [0.0, 100.0, None]},
    }
    monkeypatch.setattr(api, "telemetry", lambda run_id: {**payload})
    result = client.get("/api/runs/fixture-arrow/telemetry.arrow")
    assert result.status_code == 200
    assert result.headers["content-type"] == "application/vnd.apache.arrow.stream"
    with ipc.open_stream(result.content) as stream:
        metadata = json.loads(stream.schema.metadata[b"rocket-twin-playback"])
        assert metadata["full_sample_count"] == 120001
        assert metadata["channel_metadata"]["height_m"]["unit"] == "m"
        assert stream.read_all().to_pydict() == payload["columns"]


def test_running_cancel_waits_for_rollout_boundary_without_admitting_output(harness, monkeypatch):
    """Mock the compiled rollout only; no additional flight propagation is executed."""
    from types import SimpleNamespace

    from src.sim import env

    client, worker, root = harness
    case = {"configuration": "modular-performance-v1", "preset": "tiny", "seed": 99}
    result = client.post("/api/experiments", json=case).json()
    run_id = result["run_id"]
    boundaries = []

    def in_flight_rollout(*args, **kwargs):
        boundaries.append(api._record(run_id)["status"])
        acknowledgement = api.cancel_experiment(run_id)
        boundaries.append(acknowledgement["members"][0]["status"])
        assert not api._busy.acquire(blocking=False)
        return SimpleNamespace(rigid=SimpleNamespace(block_until_ready=lambda: None)), []

    monkeypatch.setattr(env, "rollout", in_flight_rollout)
    worker.work()
    assert boundaries == ["running", "cancel_requested"]
    record = client.get(f"/api/runs/{run_id}").json()
    assert record["status"] == "cancelled"
    assert record["random_seed"] == 99
    assert record["effective_settings"]["seed"] == 99
    assert record["cancel_requested_at"]
    assert not (root / run_id / "telemetry.parquet").exists()
    assert client.get(f"/api/runs/{run_id}/telemetry").status_code == 409
    assert api._busy.acquire(blocking=False)
    api._busy.release()


def test_full_rate_opt_in_keeps_native_rows_and_normal_arrow_remains_bounded(harness):
    import numpy as np
    import pyarrow as pa
    import pyarrow.parquet as pq
    from pyarrow import ipc

    client, _, root = harness
    run_id = "exp-" + "3" * 32
    folder = root / run_id
    folder.mkdir()
    api._save(folder, {"run_id": run_id, "status": "complete", "events": {"burnout": 1.234}})
    names = [
        "time_s",
        "down_m",
        "north_m",
        "east_m",
        "vn_mps",
        "ve_mps",
        "vd_mps",
        "specific_x_mps2",
        "specific_y_mps2",
        "specific_z_mps2",
        "qw",
        "qx",
        "qy",
        "qz",
    ]
    columns = {name: np.zeros(4001) for name in names}
    columns["time_s"] = np.arange(4001) * 0.001
    columns["qw"] = np.ones(4001)
    pq.write_table(pa.table(columns), folder / "telemetry.parquet")
    normal = client.get(f"/api/runs/{run_id}/telemetry").json()
    native = client.get(f"/api/runs/{run_id}/telemetry?playback=full-rate-benchmark").json()
    assert native["full_sample_count"] == native["returned_sample_count"] == 4001
    assert native["columns"]["time_s"] == columns["time_s"].tolist()
    assert native["sampling"]["mode"] == "full-rate-benchmark"
    assert native["sampling"]["benchmark_bounds"]["max_native_rows"] == 150000
    assert native["sampling"]["benchmark_bounds"]["max_returned_channels"] == 73
    assert normal["returned_sample_count"] <= 3002
    assert normal["sampling"]["mode"] == "bounded"
    assert client.get(f"/api/runs/{run_id}/telemetry?playback=other").status_code == 422
    with ipc.open_stream(client.get(f"/api/runs/{run_id}/telemetry.arrow").content) as stream:
        assert stream.read_all().num_rows == normal["returned_sample_count"]
        assert (
            json.loads(stream.schema.metadata[b"rocket-twin-playback"])["sampling"]["mode"]
            == "bounded"
        )


def test_full_rate_rejects_row_or_channel_cap_before_materializing(harness, monkeypatch):
    from types import SimpleNamespace

    import pyarrow as pa
    import pyarrow.parquet as pq

    client, _, root = harness
    run_id = "exp-" + "4" * 32
    folder = root / run_id
    folder.mkdir()
    api._save(folder, {"run_id": run_id, "status": "complete", "events": {}})
    monkeypatch.setattr(
        pq,
        "read_table",
        lambda *args, **kwargs: pytest.fail("Over-budget telemetry must not be materialized"),
    )
    monkeypatch.setattr(
        pq, "ParquetFile", lambda *args: SimpleNamespace(metadata=SimpleNamespace(num_rows=150001))
    )
    assert (
        client.get(f"/api/runs/{run_id}/telemetry?playback=full-rate-benchmark").status_code == 413
    )
    monkeypatch.setattr(
        pq,
        "ParquetFile",
        lambda *args: SimpleNamespace(
            metadata=SimpleNamespace(num_rows=100),
            schema_arrow=pa.schema([(f"col{i}", pa.float64()) for i in range(65)]),
        ),
    )
    assert (
        client.get(f"/api/runs/{run_id}/telemetry?playback=full-rate-benchmark").status_code == 413
    )
