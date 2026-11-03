"""F2 saved-evidence integrity; no geometry/solver execution or qualification."""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.workbench_f2 import ROOT, SOURCES, build_f2


def test_f2_complete_record_preserves_separate_targets_and_failed_mesh():
    snapshot = build_f2()
    assert snapshot["identity"]["source_identity"] == "G80-F2-fixed-stock-ballast-v2"
    assert len(snapshot["components"]) == 50
    assert snapshot["cad_manifest"] is None
    selected = snapshot["cases"][:2]
    assert [c["total_mass_g"] for c in selected] == pytest.approx([917.559981, 937.559981])
    assert all(c["margin_cal"] > 1 for c in selected)
    assert all(15 < c["guide_speed_mps"] < 15.5 for c in selected)
    assert all(c["formal_headroom_g"] > 0 > c["planning_headroom_g"] for c in selected)
    assert sum(p["mass_g"] for p in snapshot["components"]) == pytest.approx(867.559981)
    assert sum(p["mass_g"] for p in snapshot["ledger"]) == pytest.approx(100.054068)
    failures = {f["id"]: f for f in snapshot["uncertainties"]}
    assert failures["ring-mesh"]["state"] == "failed"
    assert failures["inertia"]["state"] == "unavailable"
    ring = json.loads((ROOT / SOURCES["ring_diagnostic"]).read_text())
    assert ring["refinement_valid_for_acceptance"] is False
    assert ring["engineering_accepted"] is False
    assert ring["invalid_elements"]


def test_f2_changed_spec_fails_closed(tmp_path):
    for relative in SOURCES.values():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    spec = tmp_path / SOURCES["spec"]
    spec.write_text(spec.read_text() + "\n# changed source\n")
    with pytest.raises(ValueError, match="revision mismatch"):
        build_f2(tmp_path)


def test_f2_get_only_projects_saved_results(monkeypatch):
    import src.vehicle.benchmark

    def forbidden(*args, **kwargs):
        raise AssertionError("GET attempted an engineering calculation")

    monkeypatch.setattr(src.vehicle.benchmark, "screen_launch", forbidden)
    with TestClient(create_app()) as client:
        response = client.get("/api/engineering/workbench-g80-f2")
        assert response.status_code == 200
        assert response.json()["identity"]["candidate_id"] == "G80-F2"
        old = client.get("/api/engineering/workbench-g80-fixed")
        assert old.status_code == 200
        assert old.json()["identity"]["candidate_id"] == "G80-F1"
