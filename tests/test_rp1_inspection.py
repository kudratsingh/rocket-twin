"""Verify frozen AD1 source projection and fail-closed provenance."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest
import yaml

from src.api import rp1_inspection as inspection

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def source_root(tmp_path):
    for path in inspection.PINS:
        dest = tmp_path / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, dest)
    return tmp_path


def test_exact_source_parts_and_unavailable_cad():
    result = inspection.build(ROOT)
    spec = yaml.safe_load((ROOT / inspection.SPEC).read_bytes())
    record = json.loads((ROOT / inspection.RECORD).read_bytes())
    assert result["id"] == inspection.ID
    assert result["identity"]["specification_sha256"] == inspection.PINS[inspection.SPEC]
    assert result["identity"]["resolved_spec_sha256"] is None
    assert result["identity"]["record_sha256"] == inspection.PINS[inspection.RECORD]
    assert result["identity"]["cad_revision_sha256"] is None
    assert len(result["parts"]) == 55
    assert [p["id"] for p in result["parts"]] == [p["id"] for p in spec["parts"]]
    for projected, original in zip(result["parts"], spec["parts"], strict=True):
        assert projected["raw"] == original
        assert projected["geometry"] == original["geometry"]
        assert projected["dimensions"] == original["geometry"]
        assert projected["location"]["position_m"] == original["position_m"]
        assert projected["location"]["lateral_offset_m"] == original["lateral_offset_m"]
        assert projected["mass_kg"] == original["mass_kg"]
        assert projected["learn"] == original["learn"]
        assert projected["build"] == original["build"]
        assert projected["material"] == original["material"]
        assert "failure_modes" not in projected  # No structured failure modes in this source.
        assert "mesh_url" not in projected
        assert projected["representation"]["role"] == "source envelope / concept"
    assert result["summary"]["length_m"] == spec["airframe"]["length_m"]
    assert result["summary"]["diameter_m"] == spec["airframe"]["body_diameter_m"]
    assert result["summary"]["engineering_acceptance"] == "open"
    assert result["summary"]["flight_ready"] is False
    assert "Direct frozen source YAML" in result["evidence"]["specification_basis"]
    assert result["summary"]["mass_cases"] == record["cases"]
    assert result["summary"]["saved_static_reference"] == record["rocketpy_static_reference"]
    assert result["summary"]["physical_inertia"] is None
    assert result["mass_samples"] == []
    assert (
        result["evidence"]["drawing_datum"]
        == "Millimetres aft from nose tip; angle0 at first fin, positive about body axis."
    )
    assert inspection.catalog_entry(ROOT)["id"] == inspection.ID


def test_source_drift_and_missing_rejected(source_root):
    path = source_root / inspection.SPEC
    path.write_bytes(path.read_bytes() + b"\n# drift\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        inspection.build(source_root)
    (source_root / inspection.RECORD).unlink()
    with pytest.raises(FileNotFoundError):
        inspection.catalog_entry(source_root)


def test_record_linkage_fails_even_if_repinning(source_root, monkeypatch):
    record_path = source_root / inspection.RECORD
    record = json.loads(record_path.read_text())
    record["sources"][inspection.SPEC] = "0" * 64
    record_path.write_text(json.dumps(record))
    pins = copy.copy(inspection.PINS)
    pins[inspection.RECORD] = hashlib.sha256(record_path.read_bytes()).hexdigest()
    monkeypatch.setattr(inspection, "PINS", pins)
    with pytest.raises(ValueError, match="source linkage"):
        inspection.build(source_root)


def test_source_changes_between_reads_rejected(source_root, monkeypatch):
    original = inspection._read
    calls = 0

    def read(root):
        nonlocal calls
        calls += 1
        data = original(root)
        if calls == 2:
            data[inspection.SPEC] += b"changed"
        return data

    monkeypatch.setattr(inspection, "_read", read)
    with pytest.raises(ValueError, match="changed during export"):
        inspection.build(source_root)
