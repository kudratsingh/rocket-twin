"""Exercise a real bounded CPU experiment and its persisted identity."""

import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import experiments


def test_experiment_real_rollout_and_saved_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(experiments, "RUNS", tmp_path)
    app = FastAPI()
    app.include_router(experiments.router)
    client = TestClient(app)
    assert (
        client.post(
            "/api/experiments", json={"configuration": "modular-tvc-finless-v1"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/experiments", json={"configuration": "modular-performance-v1", "wind_mps": 100}
        ).status_code
        == 422
    )
    response = client.post(
        "/api/experiments",
        json={
            "configuration": "modular-performance-v1",
            "preset": "tiny",
            "wind_mps": 1,
            "wind_direction_deg": 90,
        },
    )
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        record = client.get("/api/runs/" + run_id).json()
        if record["status"] in ("complete", "failed"):
            break
        time.sleep(0.1)
    assert record["status"] == "complete", record.get("error")
    assert record["vehicle_id"] == "modular-performance-v1"
    assert record["resolved_sha256"] and record["input_sha256"] and record["code_sha256"]
    assert record["case"]["wind_east_mps"] == 1
    assert record["flight_ready"] is False
    assert any("angle of attack" in note for note in record["validity"])
    assert any("Peak powered Mach" in note for note in record["validity"])
    assert (tmp_path / run_id / "resolved.json").is_file()
    assert (tmp_path / run_id / "telemetry.parquet").is_file()
    telemetry = client.get("/api/runs/" + run_id + "/telemetry").json()
    assert len(telemetry["columns"]["time_s"]) > 10
    assert "tilt_deg" in telemetry["columns"]
    assert telemetry["channel_metadata"]["tilt_deg"]["source"] == "backend-derived"
    assert telemetry["channel_metadata"]["tilt_deg"]["unit"] == "°"
    assert telemetry["channel_metadata"]["mass_kg"]["source"] == "recorded-parquet"
    assert telemetry["channel_metadata"]["mass_kg"]["unit"] == "kg"
    assert telemetry["columns"]["height_ft"][-1] == pytest.approx(
        telemetry["columns"]["height_m"][-1] / 0.3048
    )
    assert telemetry["columns"]["speed_mph"][-1] == pytest.approx(
        telemetry["columns"]["speed_mps"][-1] * 2.2369362920544
    )
    assert len(telemetry["columns"]["net_acceleration_mps2"]) == len(telemetry["columns"]["time_s"])
    assert all(value >= 0 for value in telemetry["columns"]["net_acceleration_mps2"])
    assert client.get("/api/runs/../../bad").status_code == 404


def test_replay_frame_basis():
    """Exercise the matrices used by the viewer at north-facing and nose-up poses."""
    import re
    from pathlib import Path

    import numpy as np

    source = (
        Path(__file__).resolve().parents[1] / "web/src/experiments/Experiment.tsx"
    ).read_text()

    def matrix(name):
        match = re.search(rf"const\s+{name}\s*=\s*new Matrix4\(\)\s*\.set\(([^)]*)\)", source)
        assert match, f"{name} frame matrix missing"
        return np.array([float(v) for v in match.group(1).split(",")]).reshape(4, 4)[:3, :3]

    body_from_cad = matrix("bodyFromCad")
    scene_from_ned = matrix("sceneFromNed")
    # Identity attitude: CAD nose points north, GLB X points east and GLB Z points up.
    identity_pose = scene_from_ned @ body_from_cad
    np.testing.assert_allclose(identity_pose @ [0, 1, 0], [0, 0, -1], atol=1e-12)
    np.testing.assert_allclose(identity_pose @ [1, 0, 0], [1, 0, 0], atol=1e-12)
    np.testing.assert_allclose(identity_pose @ [0, 0, 1], [0, 1, 0], atol=1e-12)
    # +90° about body y maps body +x to NED up, placing the CAD nose up.
    nose_up = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])
    displayed = scene_from_ned @ nose_up @ body_from_cad
    np.testing.assert_allclose(displayed @ [0, 1, 0], [0, 1, 0], atol=1e-12)
    assert np.linalg.det(displayed) == 1


def test_unknown_telemetry_metadata_never_invents_units_or_semantics():
    from src.api.experiments import _channel_metadata

    metadata = _channel_metadata({"future_sensor"}, ["future_sensor"])["future_sensor"]
    assert metadata["source"] == "recorded-parquet"
    assert metadata["unit"] is None
    assert metadata["semantic_id"] is None
