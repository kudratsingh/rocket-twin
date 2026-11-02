"""Frozen-source, mass-ledger and identity contract for the C1 walkthrough."""

import hashlib
import json
import math
import shutil
import subprocess
import sys

import pytest
import yaml

from src.api.workbench import MAPPING, ROOT, WorkbenchUnavailable, build_workbench


@pytest.fixture
def isolated_root(tmp_path):
    mapping = yaml.safe_load((ROOT / MAPPING).read_text())
    paths = [MAPPING, "src/api/workbench.py"] + [x["path"] for x in mapping["sources"].values()]
    for relative in paths:
        dest = tmp_path / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, dest)
    return tmp_path


def test_complete_frozen_document_preserves_candidate_identity_and_unavailable_evidence():
    doc = build_workbench()
    assert doc["schema_version"] == "1.0.0"
    assert doc["identity"]["configuration_id"] == "C1_closed_receiver_mass_balance"
    assert doc["identity"]["cad_revision"] is None
    assert all(p["geometry_maturity"] != "detailed_cad" for p in doc["parts"])
    assert "nose" in doc["identity"]["frame"] and "aft" in doc["identity"]["frame"]
    assert "mm" in doc["identity"]["units"]
    for source in doc["generated_from"]:
        assert hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"]
    assert {g["id"]: g["state"] for g in doc["gaps"]}["thermal"] == "unavailable"
    assert {g["id"]: g["state"] for g in doc["gaps"]}["inertia"] == "unavailable"
    assert {g["id"]: g["state"] for g in doc["gaps"]}["flutter"] == "unavailable"
    assert all(not item["browser_verified"] for item in doc["inventory"])
    assert any(
        h["id"] == "experimental-g80-retention-72" and h["state"] == "historical"
        for h in doc["historical_candidates"]
    )
    json.dumps(doc, allow_nan=False)


def test_mass_distribution_reconciles_once_without_removed_s3_or_double_fin_panels():
    doc = build_workbench()
    distribution = doc["mass_distribution"]
    ids = [p["id"] for p in doc["parts"]]
    assert len(ids) == len(set(ids))
    assert not any(i.startswith("S3_channel_") for i in ids)
    assert "aft_retainer" not in ids and "motor_mount" not in ids
    assert "fin_set" not in ids
    assert "c1_fin_panels" in ids and "fin_source_cad_residual" in ids
    assert len([i for i in ids if i.startswith("fin_tab_depth_delta_")]) == 3
    growth = [x for x in distribution if x["id"] == "separate_growth"]
    assert len(growth) == 1 and growth[0]["mass_g"] == 50 and growth[0]["station_mm"] == 1227
    assert math.fsum(x["mass_g"] for x in doc["parts"]) == pytest.approx(1079.8067509765392)
    total = math.fsum(x["mass_g"] for x in distribution)
    assert total == pytest.approx(1129.8067509765392)
    assert math.fsum(x["mass_g"] for x in doc["mass_groups"]) == pytest.approx(total)
    assert math.fsum(x["mass_g"] * x["station_mm"] for x in distribution) / total == pytest.approx(
        879.7979120857696
    )
    cases = {c["id"]: c for c in doc["cases"]}
    for case in cases.values():
        assert case["growth_g"] == 50
        assert case["total_g"] == case["nominal_g"] + 50
    assert cases["C1_plus20g_motorCG_probe"]["total_g"] - cases["C1_nominal"][
        "total_g"
    ] == pytest.approx(20)
    assert cases["R1_nominal"]["added_mass_g"] == pytest.approx(70.11101376993652)
    assert cases["R1_plus20g_motorCG_probe"]["loaded_margin_cal"] < 1
    assert cases["R1_nominal"]["planning_headroom_g"] < 0
    assert cases["C1_nominal"]["planning_headroom_g"] == pytest.approx(22.508722579979803)
    assert cases["C1_plus20g_motorCG_probe"]["planning_headroom_g"] == pytest.approx(
        2.5087225799798034
    )


def test_load_paths_use_corrected_datums_and_real_unavailable_connections():
    doc = build_workbench()
    part_ids = {p["id"] for p in doc["parts"]}
    paths = {p["id"]: p for p in doc["load_paths"]}
    assert set(paths) == {"fin_bending", "recovery", "motor_forward", "motor_reverse", "guide"}
    edges = paths["fin_bending"]["edges"]
    assert edges[0]["value"] == pytest.approx(8.830347836086943)
    assert edges[1]["value"] == pytest.approx(10.750948490435855)
    assert edges[3]["value"] == pytest.approx(16.115384800858674)
    for path in paths.values():
        node_ids = {n["id"] for n in path["nodes"]}
        assert path["state"] in {"failed", "unavailable"}
        assert path["free_body"]["part_id"] in part_ids
        for node in path["nodes"]:
            assert node["part_id"] is None or node["part_id"] in part_ids
        for edge in path["edges"]:
            assert edge["from"] in node_ids and edge["to"] in node_ids
            assert all(pid in part_ids for pid in edge["part_ids"])
            if edge["state"] == "unavailable":
                assert edge["value"] is None
    dims = {d["label"]: d for d in doc["joints"][0]["dimensions"]}
    old_c1 = dims["C1 recorded 3.179 mm aggregate: superseded receiver-lever proxy"]
    old_r1 = dims["R1 recorded 1.039 mm aggregate: superseded receiver-lever proxy"]
    assert old_c1["value"] == pytest.approx(3.1791788394317385)
    assert old_r1["value"] == pytest.approx(1.0389342402879547)
    assert old_c1["state"] == old_r1["state"] == "superseded"
    assert dims["C1 bridge minimum mean hot bond shear"]["value"] > 7
    assert all(pid in part_ids for joint in doc["joints"] for pid in joint["part_ids"])


def test_c2_record_supplies_only_rejected_history_and_saved_receiver_datum_scalars():
    doc = build_workbench()
    source = next(s for s in doc["generated_from"] if s["id"] == "c2_record")
    assert source["sha256"] == "c67d16a49378e6b462bec66c689c414750cf5e9a61f4524785d0ffa198e2eac3"
    record = json.loads((ROOT / source["path"]).read_text())
    correction = record["prior_receiver_radius_datum_correction"]
    joint = doc["joints"][0]
    assert "c2_record" in joint["source_ids"]
    assert "not installed displacement fields or acceptance" in " ".join(joint["findings"])
    dims = {d["label"]: d for d in joint["dimensions"]}
    for cid in ("C1", "R1"):
        aggregate = dims[
            f"Corrected calculated {cid} aggregate scalar proxy; axis-radius conversion only"
        ]
        assert aggregate["value"] == correction[cid]["panel_socket_play_receiver_only_tip_m"] * 1000
        assert aggregate["state"] == "failed"
        receiver = dims[f"Corrected calculated {cid} receiver-only tip-motion scalar proxy"]
        assert receiver["value"] == correction[cid]["receiver_only_tip_m"] * 1000
        assert receiver["state"] == "calculated"
    assert dims["Corrected rocket-axis-to-fin-tip radius for scalar conversion"]["value"] == 123
    c2 = next(c for c in doc["historical_candidates"] if c["id"] == "C2")
    assert c2["state"] == "failed" and c2["source_ids"] == ["c2_record"]
    for value in ("53.929488", "1183.736239", "1203.736239", "3.828311", "2.327521"):
        assert value in c2["reason"]
    assert len(doc["cases"]) == 4
    assert all(c["id"].startswith(("C1_", "R1_")) for c in doc["cases"])
    assert all(not p["id"].startswith("C2") for p in doc["parts"])
    assert doc["identity"]["cad_revision"] is None


def test_r1_added_mass_locations_reuse_saved_ledger_without_changing_c1_distribution():
    doc = build_workbench()
    source = next(s for s in doc["generated_from"] if s["id"] == "attachment_record")
    record = json.loads((ROOT / source["path"]).read_text())
    rows = doc["revision_mass_changes"]
    assert len(rows) == len(record["R1_added_ledger"]) == 14
    assert math.fsum(row["mass_g"] for row in rows) == pytest.approx(70.11101376993652)
    pids = {p["id"] for p in doc["parts"]}
    for row, saved in zip(rows, record["R1_added_ledger"], strict=True):
        assert row["id"] == saved["id"]
        assert row["mass_g"] == saved["mass_g"]
        assert row["station_mm"] == saved["station_mm"]
        assert row["state"] == "estimated" and row["revision"] == "R1"
        assert all(pid in pids for pid in row["part_ids"])
    changes = {row["id"]: row for row in rows}
    assert changes["R1_closed_receiver_thickness_increment"]["part_ids"] == [
        "C1_closed_G11_body_annulus"
    ]
    assert changes["R1_three_end_keys_0"]["part_ids"] == []
    assert changes["R1_three_end_keys_1"]["part_ids"] == []
    assert len(doc["cases"]) == 4
    for case, saved in zip(doc["cases"], record["coupled_cases"], strict=True):
        assert case["id"] == saved["id"]
        assert case["total_g"] == saved["total_with_growth_g"]
        assert case["nominal_g"] == saved["nominal_without_growth_g"]
        assert case["cg_mm"] == saved["cg_mm"]
    assert math.fsum(row["mass_g"] for row in doc["mass_distribution"]) == pytest.approx(
        1129.8067509765392
    )


def test_guide_baseline_and_conditional_start_geometry_stay_separate():
    doc = build_workbench()
    launch = doc["launch"]
    assert launch["baseline_usable_m"] == 1.5
    assert launch["formal_mps"] == 15 and launch["planning_mps"] == 15.5
    assert launch["equipment_confirmed"] is False
    assert launch["upper_guide_front_mm"] == 250
    assert launch["lower_guide_front_mm"] == 430
    assert launch["assumed_pad_offset_mm"] == 100
    assert launch["old_lug_start_loss_mm"] == pytest.approx(1077)
    assert launch["illustrative_overall_mm"] - launch["old_lug_start_loss_mm"] == pytest.approx(
        launch["illustrative_usable_mm"]
    )
    guide_1p8 = next(g for g in doc["cases"][0]["guide_results"] if g["usable_m"] == 1.8)
    assert guide_1p8["speed_mps"] == pytest.approx(14.975462403267386)
    assert guide_1p8["formal_margin_mps"] < 0
    assert doc["criteria"]["minimum_static_margin_cal"] == 1
    assert doc["criteria"]["service_tip_limit_mm"] == 1
    assert doc["criteria"]["hot_bond_shear_screen_mpa"] == 1


@pytest.mark.parametrize("source_id", ["attachment_record", "c2_record"])
def test_changed_or_missing_record_fails_closed(isolated_root, source_id):
    mapping = yaml.safe_load((isolated_root / MAPPING).read_text())
    path = isolated_root / mapping["sources"][source_id]["path"]
    original = path.read_bytes()
    path.write_bytes(original + b"\n")
    with pytest.raises(WorkbenchUnavailable, match="hash mismatch"):
        build_workbench(isolated_root)
    path.unlink()
    with pytest.raises(WorkbenchUnavailable, match="source unavailable"):
        build_workbench(isolated_root)


def test_source_path_cannot_escape_root(isolated_root):
    path = isolated_root / MAPPING
    mapping = yaml.safe_load(path.read_text())
    mapping["sources"]["source_lock"]["path"] = "../outside.json"
    path.write_text(yaml.safe_dump(mapping))
    with pytest.raises(WorkbenchUnavailable, match="escapes repository"):
        build_workbench(isolated_root)


def test_updated_presentation_hash_cannot_disguise_disconnected_audit(isolated_root):
    mapping_path = isolated_root / MAPPING
    mapping = yaml.safe_load(mapping_path.read_text())
    item = mapping["sources"]["connection_audit"]
    path = isolated_root / item["path"]
    audit = json.loads(path.read_text())
    audit["source_record_sha256"] = "0" * 64
    path.write_text(json.dumps(audit))
    item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    mapping_path.write_text(yaml.safe_dump(mapping))
    with pytest.raises(WorkbenchUnavailable, match="does not identify"):
        build_workbench(isolated_root)


def test_cli_exports_document_and_manifest_without_solver(tmp_path):
    output = tmp_path / "g80-c1.json"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/wo04_workbench_export.py"), "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    document = json.loads(output.read_text())
    manifest = json.loads(output.with_name("g80-c1-source-manifest.json").read_text())
    assert manifest["identity"] == document["identity"]
    assert manifest["sources"] == document["generated_from"]
    assert document == build_workbench()
