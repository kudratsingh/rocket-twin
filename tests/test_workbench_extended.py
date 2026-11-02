"""One recorded extension packet: identity, compatible scope and logical topology."""

import hashlib
import json
import shutil
import subprocess
import sys

import pytest
import yaml
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.workbench import MAPPING as BASE_MAPPING
from src.api.workbench import ROOT, WorkbenchUnavailable, build_workbench
from src.api.workbench_extended import MAPPING, build_workbench_extended


@pytest.fixture
def copied_sources(tmp_path):
    paths = {MAPPING, BASE_MAPPING, "src/api/workbench.py", "src/api/workbench_extended.py"}
    for mapping_path in (MAPPING, BASE_MAPPING):
        mapping = yaml.safe_load((ROOT / mapping_path).read_text())
        paths.update(entry["path"] for entry in mapping["sources"].values())
    for relative in paths:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    return tmp_path


def test_extension_identity_and_all_links_match_frozen_base():
    extended = build_workbench_extended()
    base = build_workbench()
    assert extended["schema_version"] == "1.0.0"
    assert extended["identity"] == base["identity"]
    assert extended["identity"]["cad_revision"] is None
    for source in extended["generated_from"]:
        assert hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"]
    part_ids = {part["id"] for part in base["parts"]}
    source_ids = {source["id"] for source in extended["generated_from"]}

    def check(value):
        if isinstance(value, dict):
            assert set(value.get("part_ids", [])) <= part_ids
            assert set(value.get("source_ids", [])) <= source_ids
            if "nodes" in value and "edges" in value:
                ids = [node["id"] for node in value["nodes"]]
                assert len(ids) == len(set(ids))
                assert all(edge["from"] in ids and edge["to"] in ids for edge in value["edges"])
            for child in value.values():
                check(child)
        elif isinstance(value, list):
            for child in value:
                check(child)

    check(extended)
    json.dumps(extended, allow_nan=False)


def test_candidate_comparison_copies_eight_complete_saved_cases_without_adoption():
    doc = build_workbench_extended()
    candidates = {row["id"]: row for row in doc["candidate_comparison"]}
    assert set(candidates) == {"C1", "R1", "C2", "C3", "A_motor_fin_can", "B_outer_captured_roots"}
    assert all(len(row["cases"]) == 2 for row in candidates.values())
    assert all(
        row["active"] is False and row["full_intrinsic_inertia"] is None
        for row in candidates.values()
    )
    assert candidates["C1"]["cases"][0]["total_g"] == pytest.approx(1129.8067509765392)
    assert candidates["R1"]["net_added_mass_g"] == pytest.approx(70.11101376993652)
    for cid, relative in [
        ("C2", "runs/wo03-c2-sandwich-socket-20261102-v2/record.json"),
        ("C3", "runs/wo03-c3-continuous-connection-20261102-v1/record.json"),
    ]:
        saved = json.loads((ROOT / relative).read_text())
        assert candidates[cid]["stop_reason"] == saved["decision"]
        assert candidates[cid]["net_added_mass_g"] == saved["net_added_mass_g"]
        for row, original in zip(candidates[cid]["cases"], saved["cases"], strict=True):
            assert row["total_g"] == original["total_g"]
            assert row["growth_g"] == 50
            assert row["total_g"] == row["nominal_g"] + row["growth_g"]
            assert row["cg_mm"] == original["cg_mm"]
            assert row["loaded_margin_cal"] == original["loaded_margin_cal"]
            assert row["recovery_force_n"] == original["severe_recovery_DF3_mean_N"]
            assert (
                row["guide_results"][0]["speed_mps"] == original["guides"][0]["rail_exit_speed_mps"]
            )
    assert candidates["C3"]["stop_joint_ids"] == ["receiver_end", "motor_service"]
    assert candidates["C3"]["cases"][1]["loaded_margin_cal"] < 1


def test_architecture_concepts_append_saved_values_and_preserve_prior_four_candidates():
    doc = build_workbench_extended()
    original = doc["candidate_comparison"][:4]
    assert (
        hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest()
        == "67c5556907e00391a66a0ba696696af23b69bc54557cb7dd55b6501320215926"
    )
    source = next(s for s in doc["generated_from"] if s["id"] == "architecture_record")
    assert source["sha256"] == "7f4a0262a7ed5be0427bb7a1fe22c8870697014a6f2c807032091561511a82d2"
    saved = json.loads((ROOT / source["path"]).read_text())
    concepts = doc["candidate_comparison"][4:]
    assert len(concepts) == 2
    for concept, arrangement in zip(concepts, saved["arrangements"], strict=True):
        assert concept["id"] == arrangement["id"]
        assert concept["candidate_identity"] == arrangement["id"]
        assert concept["geometry_maturity"] == "concept" and concept["state"] == "failed"
        assert concept["part_ids"] == concept["stop_joint_ids"] == []
        assert concept["full_intrinsic_inertia"] is None and concept["active"] is False
        assert concept["net_added_mass_g"] == arrangement["net_mass_delta_g"]
        for case, row in zip(concept["cases"], arrangement["cases"], strict=True):
            assert case["total_g"] == row["total_g"]
            assert case["nominal_g"] == row["subtotal_without_separate_growth_g"]
            assert case["growth_g"] == 50
            assert case["loaded_margin_cal"] == row["loaded_static_cal"]
            assert case["recovery_force_n"] == row["required_severe_recovery_DF3_mean_N"]
            assert case["baseline_formal_headroom_g"] == row["baseline_formal_headroom_g"] < 0
            assert case["formal_headroom_g"] == row["conditional1p971_formal_headroom_g"]
            assert case["guide_results"][0]["speed_mps"] == row["guides"][0]["rail_exit_speed_mps"]
            assert case["guide_results"][0]["formal_margin_mps"] < 0
            assert case["guide_results"][1]["planning_margin_mps"] > 0
    assert concepts[0]["preferred_for_next_joint_study"] is True
    assert concepts[1]["preferred_for_next_joint_study"] is False
    assert concepts[0]["cases"][1]["baseline_formal_headroom_g"] == pytest.approx(
        -29.910926471393736
    )


def test_recovery_branches_and_opening_assumptions_do_not_claim_equal_forces():
    recovery = build_workbench_extended()["recovery"]
    loops = [node for node in recovery["topology"]["nodes"] if node["id"].startswith("raw_Bally")]
    assert len(loops) == 3
    for node in loops:
        capacity = next(q for q in node["quantities"] if "capacity" in q["label"])
        assert capacity["value"] is None and capacity["state"] == "unavailable"
    assumptions = {q["label"]: q["value"] for q in recovery["opening_assumptions"]}
    assert assumptions["Severe opening speed"] == 20.4
    assert assumptions["Stopping distance"] == 0.3
    assert assumptions["Design factor applied once"] == 3
    assert all(step["state"] in {"estimated", "unavailable"} for step in recovery["packing_steps"])


def test_thermal_history_is_incompatible_and_no_current_field_or_time_series_is_created():
    thermal = build_workbench_extended()["thermal"]
    assert thermal["compatible_spatial_field"] is None
    assert thermal["topology"]["compatible_with_c1"] is False
    assert all(node["part_ids"] == [] for node in thermal["topology"]["nodes"])
    assert len(thermal["history"]) == 39
    assert all(row["compatible_with_c1"] is False for row in thermal["history"])
    assert all("samples" not in row and "field" not in row for row in thermal["history"])
    for node in thermal["current_interfaces"]["nodes"]:
        assert all(q["value"] is None for q in node["quantities"])
    opening = next(o for o in thermal["openings"] if o["id"] == "service-ports")
    assert opening["dimensions"][0]["value"] == 12
    assert opening["dimensions"][1]["value"] == 11.5
    assert next(m for m in thermal["materials"] if m["id"] == "commercial")["part_ids"] == []


def test_electrical_netlist_is_exact_with_no_pins_or_added_main_recovery_connection():
    doc = build_workbench_extended()
    saved = yaml.safe_load(
        (ROOT / "runs/wo03-g80-canopy-stage3-20261101-v1/sensitivity.yaml").read_text()
    )["netlist"]
    nets = doc["electrical"]["nets"]
    assert len(nets) == len(saved) == 10
    for row, original in zip(nets, saved, strict=True):
        assert row["net"] == original["net"]
        assert row["from"] == original["from"]
        assert row["to"] == (
            original["to"] if isinstance(original["to"], list) else [original["to"]]
        )
        assert row["pin"] == original["pin"] is None
        assert row["gauge_awg"] == original["gauge_awg"]
    assert not any(row["from"] == "battery" and "independent_recovery" in row["to"] for row in nets)
    assert doc["electrical"]["control_blocks"]["compatible_with_c1"] is False
    assert all(
        node["state"] == "unavailable" for node in doc["electrical"]["control_blocks"]["nodes"]
    )


@pytest.mark.parametrize("action", ["change", "missing"])
def test_changed_or_missing_extension_record_fails_closed(copied_sources, action):
    path = copied_sources / "runs/wo03-c3-continuous-connection-20261102-v1/record.json"
    if action == "change":
        path.write_bytes(path.read_bytes() + b"\n")
    else:
        path.unlink()
    with pytest.raises(WorkbenchUnavailable, match="hash mismatch|source unavailable"):
        build_workbench_extended(copied_sources)


def test_minimal_endpoint_returns_record_and_source_failure_is_explicit(copied_sources):
    client = TestClient(create_app(copied_sources, catalog=()))
    response = client.get("/api/engineering/workbench-extended")
    assert response.status_code == 200
    assert response.json()["identity"]["cad_revision"] is None
    (copied_sources / "configs/engineering/workbench-extended.yaml").unlink()
    response = client.get("/api/engineering/workbench-extended")
    assert response.status_code == 409
    assert "source unavailable" in response.json()["detail"]


def test_cli_exports_prepared_extension_and_source_manifest(tmp_path):
    path = tmp_path / "g80-extended.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/wo04_workbench_extended_export.py"),
            "--output",
            str(path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    doc = json.loads(path.read_text())
    manifest = json.loads(path.with_name("g80-extended-source-manifest.json").read_text())
    assert manifest["sources"] == doc["generated_from"]
    assert doc == build_workbench_extended()
