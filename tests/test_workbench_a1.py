"""A1 is a source-checked held concept, never an accepted C1 CAD overlay."""

import json
import shutil

import pytest
import yaml
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.workbench import ROOT, WorkbenchUnavailable
from src.api.workbench_a1 import MAPPING, build_workbench_a1


def test_a1_keeps_failed_findings_and_separate_identity():
    d = build_workbench_a1()
    assert d["identity"]["candidate_id"] == "A1"
    assert d["identity"]["cad_revision"] is None
    assert "NOT ADMITTED" in d["status"]
    assert d["fit_rows"][0]["result"]["state"] == "failed"
    assert d["fit_rows"][1]["result"]["value"] == pytest.approx(0.1171)
    assert {r["id"] for r in d["findings"] if r["state"] == "failed"} == {"bolt", "mass"}
    assert len(d["cases"]) == 2
    paths = {p["id"]: p for p in d["paths"]}
    assert "motor_forward" in paths and "motor_reverse" in paths
    assert not any("Reverse" in step for step in paths["motor_forward"]["sequence"])
    assert len(paths) == 5
    assert d["cases"][1]["baseline_formal_headroom_g"] < 0
    assert d["joint_detail"]["minimum_protrusion_mm"] == 2.7
    ids = {x["id"] for x in d["generated_from"]}

    def walk(x):
        if isinstance(x, dict):
            assert set(x.get("source_ids", [])) <= ids
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(d)
    json.dumps(d, allow_nan=False)


def test_source_mismatch_stays_unavailable(tmp_path):
    cfg = yaml.safe_load((ROOT / MAPPING).read_text())
    for relative in [MAPPING] + [s["path"] for s in cfg["sources"]]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    assert build_workbench_a1(tmp_path)["identity"]["candidate_id"] == "A1"
    source = tmp_path / cfg["sources"][0]["path"]
    source.write_text(source.read_text() + "\n")
    with pytest.raises(WorkbenchUnavailable, match="revision mismatch"):
        build_workbench_a1(tmp_path)


def test_a1_endpoint_displays_saved_results_without_running_solver():
    client = TestClient(create_app())
    reply = client.get("/api/engineering/workbench-a1")
    assert reply.status_code == 200
    assert reply.json()["cases"][0]["total_mass_g"] == pytest.approx(1074.7624351942488)
