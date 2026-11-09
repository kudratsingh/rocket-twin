"""Actual frozen source, accounting semantics and fail-closed prepared snapshots."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest
import yaml

from scripts import wo04_parts_bank_export as exporter
from src.api import parts_bank as bank
from src.api import rp1_inspection

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def source_root(tmp_path):
    for relative in rp1_inspection.PINS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    return tmp_path


def _rows(document):
    return {d["source_part_id"]: d for d in document["definitions"]}


def test_actual_catalog_deterministic_and_source_groups_read_only():
    paths = list(rp1_inspection.PINS)
    before = {p: (ROOT / p).read_bytes() for p in paths}
    result = bank.build(ROOT)
    assert bank.build(ROOT) == result
    spec = yaml.safe_load(before[rp1_inspection.SPEC])
    assert [i["id"] for i in result["instances"]] == [p["id"] for p in spec["parts"]]
    assert len(result["definitions"]) == len(result["instances"]) == 55
    assert len({d["id"] for d in result["definitions"]}) == 55
    assert result["identity"]["specification_sha256"] == rp1_inspection.PINS[rp1_inspection.SPEC]
    assert result["capabilities"] == {"editable": False, "draft_builder": False}
    definitions = _rows(result)
    instances = {i["id"]: i for i in result["instances"]}
    for raw in spec["parts"]:
        d, i = definitions[raw["id"]], instances[raw["id"]]
        assert i["definition_id"] == d["id"]
        assert i["definition_revision_sha256"] == d["revision_sha256"]
        assert i["quantity"] == 1
        assert i["counting_basis"] == "source_record"
        assert i["group_count"] == raw["geometry"].get("count", 1)
        assert i["position_m"] == raw["position_m"]
        assert d["mass_kg"] == raw["mass_kg"]
        assert d["price"]["amount_usd"] == raw["build"]["cost_usd"]
        assert d["price"]["current_verified"] is False
        assert d["price"]["owner_stock_credit"] is False
        if raw["build"]["cost_usd"] == 0:
            zero = next(issue for issue in d["issues"] if issue["id"] == "zero_source_budget")
            assert "not a free part" in zero["message"]
        assert d["dimensions"]["values"] == raw["geometry"]
        assert d["geometry"]["reusable_local_geometry"] is False
        assert d["geometry"]["registered_instance_id"] == i["id"]
        if d["geometry"]["mesh_available"]:
            assert d["geometry"]["mesh_scope"] == "installed_reference"
            assert d["geometry"]["frame"] == "X=body+y, Y=length-station, Z=body-z"
        else:
            assert d["geometry"]["mesh_scope"] is None
            assert d["geometry"]["frame"] is None
        unsigned = {k: v for k, v in d.items() if k != "revision_sha256"}
        assert bank.digest(unsigned) == d["revision_sha256"]
    assert instances["fin_set"]["group_count"] == 3
    assert instances["fin_set"]["quantity"] == 1
    assert "per-piece" in definitions["fin_set"]["mass_basis"]
    assert before == {p: (ROOT / p).read_bytes() for p in paths}
    revision = result.pop("revision_sha256")
    assert bank.digest(result) == revision


def test_source_only_missing_optional_geometry_and_explicit_conflicts(source_root):
    result = bank.build(source_root)
    rows = _rows(result)
    assert result["identity"]["inspection_geometry_sha256"] is None
    assert result["summary"]["mesh_available"] == 0
    assert result["summary"]["engineering_accepted"] is False
    assert all(d["physical_verification"] == "open" for d in rows.values())
    assert all(d["geometry"]["mesh"] is None for d in rows.values())
    assert all(d["geometry"]["mesh_scope"] is None for d in rows.values())
    assert all(d["geometry"]["frame"] is None for d in rows.values())
    assert all(d["geometry"]["reusable_local_geometry"] is False for d in rows.values())
    assert all(d["geometry"]["registered_instance_id"] == pid for pid, d in rows.items())
    assert rows["fin_set"]["geometry"]["maturity"] == "source_dimensioned"
    assert rows["avionics_sled"]["source_cad_role"] == "distributed_budget"
    assert rows["avionics_sled"]["reuse_status"] == "allowance_only"
    assert rows["rp1_kevlar_wrap"]["geometry"]["maturity"] == "missing_geometry"
    retainer = rows["motor_retainer"]
    assert "19002" in retainer["issues"][0]["message"]
    assert "009750" in retainer["issues"][0]["message"]
    assert retainer["reuse_status"] == "identity_unresolved"
    assert "1.210" in rows["motor_tube"]["issues"][0]["message"]
    assert "EasyMini" in rows["independent_recovery"]["issues"][0]["message"]
    assert "Apogee" in rows["independent_recovery"]["issues"][0]["message"]
    assert rows["independent_recovery"]["interfaces"] is None
    assert bank.definition(source_root, "rp1:fin_set")["source_part_id"] == "fin_set"
    with pytest.raises(KeyError, match="Unknown"):
        bank.definition(source_root, "../../fin_set")


def test_absent_unknown_numbers_remain_null(source_root, monkeypatch):
    original = rp1_inspection.build

    def without_optional_values(root):
        doc = original(root)
        doc["parts"][0]["raw"].pop("mass_kg")
        doc["parts"][0]["raw"]["build"].pop("cost_usd")
        return doc

    monkeypatch.setattr(rp1_inspection, "build", without_optional_values)
    first = bank.build(source_root)["definitions"][0]
    assert first["mass_kg"] is None and first["mass_basis"] == "unavailable"
    assert first["price"]["amount_usd"] is None


def test_drift_duplicate_and_invalid_group_rejected(source_root, monkeypatch):
    original = rp1_inspection.build

    def duplicate(root):
        doc = original(root)
        doc["parts"][-1] = copy.deepcopy(doc["parts"][0])
        return doc

    monkeypatch.setattr(rp1_inspection, "build", duplicate)
    with pytest.raises(ValueError, match="duplicate"):
        bank.build(source_root)

    def bad_group(root):
        doc = original(root)
        doc["parts"][0]["raw"]["geometry"]["count"] = -1
        return doc

    monkeypatch.setattr(rp1_inspection, "build", bad_group)
    with pytest.raises(ValueError, match="group count"):
        bank.build(source_root)
    path = source_root / rp1_inspection.SPEC
    path.write_bytes(path.read_bytes() + b"\n# drift\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        bank.build(source_root)


def test_corrupt_optional_geometry_not_silently_hidden(source_root, monkeypatch):
    def corrupt(root):
        raise ValueError("Inspection geometry mesh hash mismatch")

    monkeypatch.setattr(bank.rp1_geometry, "build", corrupt)
    with pytest.raises(ValueError, match="mesh hash mismatch"):
        bank.build(source_root)


def test_snapshot_atomic_repeatable_fixed_path_and_refuses_foreign(source_root):
    result = exporter.prepare(source_root)
    target = source_root / exporter.OUTPUT
    snapshot = target.read_bytes()
    assert json.loads(snapshot) == bank.build(source_root)
    assert result["status"] == "prepared"
    assert exporter.prepare(source_root)["status"] == "verified_existing"
    assert target.read_bytes() == snapshot
    with pytest.raises(ValueError, match="fixed"):
        exporter.prepare(source_root, "../../user.json")
    target.write_text('{"id":"foreign"}')
    before = hashlib.sha256(target.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="unrelated"):
        exporter.prepare(source_root)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == before


def test_mid_read_module_change_rejected(source_root, monkeypatch):
    original = bank._snapshot
    calls = 0

    def changed(root):
        nonlocal calls
        result = original(root)
        calls += 1
        if calls == 2:
            result[bank.MODULE_PATHS[0]] += b"changed"
        return result

    monkeypatch.setattr(bank, "_snapshot", changed)
    with pytest.raises(ValueError, match="changed during read"):
        bank.build(source_root)
