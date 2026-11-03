"""F1 revision/evidence boundaries, independent from physical qualification."""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.workbench_g80_fixed import ROOT, SOURCES, build_conventional_g80
from src.vehicle.schema import load_vehicle


def test_f1_is_dedicated_and_preserves_failed_cases():
    v = load_vehicle("configs/vehicle/candidates/g80-f1.yaml")
    assert v.tvc is None
    assert not any(p.type in ["servo", "tvc_gimbal"] for p in v.parts)
    s = build_conventional_g80()
    assert s["identity"]["cad_revision"] is None and s["cad_manifest"] is None
    assert all(c["margin_cal"] < 1 for c in s["cases"])
    assert len({c["id"] for c in s["cases"]}) == 4
    assert all(c["guide_speed_mps"] > 15.5 for c in s["cases"])
    assert any(c["state"] == "failed" for c in s["connections"])
    assert len(s["components"]) == 42
    assert next(f for f in s["uncertainties"] if f["id"] == "inertia")["state"] == "unavailable"


def test_f1_source_edit_fails_closed(tmp_path):
    for source in SOURCES.values():
        target = tmp_path / source
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, target)
    p = tmp_path / SOURCES["spec"]
    p.write_text(p.read_text() + "\n# changed\n")
    with pytest.raises(ValueError, match="revision mismatch"):
        build_conventional_g80(tmp_path)


def test_f1_source_api_does_not_run_engineering(monkeypatch):
    import src.vehicle.benchmark

    monkeypatch.setattr(
        src.vehicle.benchmark,
        "screen_launch",
        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("solver called")),
    )
    with TestClient(create_app()) as c:
        r = c.get("/api/engineering/workbench-g80-fixed")
        assert r.status_code == 200
        assert r.json()["identity"]["candidate_id"] == "G80-F1"


def test_recorded_distributed_beam_matches_uniform_known_answer():
    r = json.loads((ROOT / SOURCES["result"]).read_text())["fin_screen"]
    assert r["uniform_beam_relative_error"] < 2e-6
    assert r["panel_deflection_m"] < r["all_load_at_tip_upper_bound_m"]
    assert r["required_root_rotational_stiffness_Nm_rad"] > 0
