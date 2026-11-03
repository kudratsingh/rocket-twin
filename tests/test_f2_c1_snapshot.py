"""Saved connection study cannot attach incompatible fields or execute analysis."""

import shutil

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.workbench_f2_c1 import ROOT, SOURCES, build_f2_c1


def test_f2_c1_graph_uses_own_parts_and_preserves_open_criteria():
    result = build_f2_c1()
    assert result["identity"]["candidate_id"] == "G80-F2-C1"
    assert result["identity"]["cad_revision"] is None
    ids = {p["id"] for p in result["parts"]}
    assert len(ids) == 53
    assert all(set(n["part_ids"]) <= ids for n in result["graph"]["nodes"])
    assert result["numerical"]["completed_grids"] == 2
    assert result["numerical"]["required_grids"] == 3
    assert result["numerical"]["fine_nodes"] > result["numerical"]["node_limit"]
    assert not result["field_export"]["active_compatible"]
    assert not result["numerical"]["installed_strength_accepted"]
    assert result["audit"]["source_variant"] == "frozen_F2"
    assert all(c["burnout_margin_cal"] > 1 for c in result["cases"])


def test_f2_c1_source_change_fails_closed(tmp_path):
    for relative in SOURCES.values():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    path = tmp_path / SOURCES["spec"]
    path.write_text(path.read_text() + "\n# changed\n")
    with pytest.raises(ValueError, match="identity mismatch"):
        build_f2_c1(tmp_path)


def test_f2_c1_get_only_projects_saved_sources(monkeypatch):
    import src.vehicle.benchmark
    import src.vehicle.mass

    app = create_app()

    def forbidden(*args, **kwargs):
        raise AssertionError("Source GET attempted physics")

    monkeypatch.setattr(src.vehicle.benchmark, "screen_launch", forbidden)
    monkeypatch.setattr(src.vehicle.mass, "mass_properties", forbidden)
    with TestClient(app) as client:
        response = client.get("/api/engineering/workbench-g80-f2-c1")
        assert response.status_code == 200
        assert response.json()["identity"]["candidate_id"] == "G80-F2-C1"
