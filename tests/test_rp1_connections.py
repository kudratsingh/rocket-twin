"""AD1 connection source binding, evidence boundaries and drawing allowlist."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest
import yaml

from src.api import rp1_connections as c

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def source_root(tmp_path):
    manifest = json.loads((ROOT / c.MANIFEST).read_bytes())
    paths = [*c.PINS, *(entry["svg"]["path"] for entry in manifest["artifacts"])]
    for path in paths:
        dest = tmp_path / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, dest)
    return tmp_path


def test_real_source_connections_and_graphs():
    data = c.build(ROOT)
    spec = yaml.safe_load((ROOT / c.SPEC).read_bytes())
    assert data["configuration"] == {
        "id": c.rp1_inspection.ID,
        "path": c.SPEC,
        "sha256": c.PINS[c.SPEC],
    }
    assert data["part_ids"] == [p["id"] for p in spec["parts"]]
    assert len(data["part_ids"]) == len(set(data["part_ids"])) == 55
    assert [x["id"] for x in data["connections"]] == ["fin-root", "recovery"]
    assert [d["id"] for d in data["drawings"]] == list(c.DRAWING_IDS)
    sources = {s["id"] for s in data["sources"]}
    for connection in data["connections"]:
        assert set(connection["part_ids"]) <= set(data["part_ids"])
        nodes = {n["id"] for n in connection["nodes"]}
        for node in connection["nodes"]:
            assert set(node["part_ids"]) <= set(data["part_ids"])
        for edge in connection["edges"]:
            assert edge["from"] in nodes and edge["to"] in nodes
        assert all(
            item["source_id"] in sources
            for item in connection["dimensions"] + connection["findings"]
        )
        assert set(connection["drawing_ids"]) <= set(c.DRAWING_IDS)
    fin, recovery = data["connections"]
    assert {"failed-screen", "unknown", "requirement"} == {f["status"] for f in fin["findings"]}
    assert (
        next(d for d in recovery["dimensions"] if d["id"] == "finished-capacity")["value"] is None
    )
    assert not any("modular-performance" in json.dumps(x) for x in data["connections"])
    for drawing in data["drawings"]:
        path, expected = c.asset(ROOT, drawing["id"])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected == drawing["sha256"]


def test_unknown_asset_and_changed_sources_fail(source_root):
    with pytest.raises(ValueError, match="Unknown drawing ID"):
        c.asset(source_root, "../other")
    with (source_root / c.SPEC).open("ab") as handle:
        handle.write(b"changed")
    with pytest.raises(ValueError, match="source hash mismatch"):
        c.build(source_root)


def test_changed_drawing_fails(source_root):
    path = source_root / f"output/rp1-attachment-definition/{c.DRAWING_IDS[0]}.svg"
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Drawing hash mismatch"):
        c.build(source_root)


def test_repin_d1_record_does_not_bypass_source_identity(source_root, monkeypatch):
    path = source_root / c.D1
    record = json.loads(path.read_bytes())
    record["sources"][c.SPEC] = "0" * 64
    path.write_text(json.dumps(record))
    pins = copy.copy(c.PINS)
    pins[c.D1] = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(c, "PINS", pins)
    with pytest.raises(ValueError, match="source identity/linkage"):
        c.build(source_root)


def test_second_source_read_detects_race(source_root, monkeypatch):
    original = c._snapshot
    calls = 0

    def read(root):
        nonlocal calls
        calls += 1
        data = original(root)
        if calls == 2:
            data[c.SPEC] += b"changed"
        return data

    monkeypatch.setattr(c, "_snapshot", read)
    with pytest.raises(ValueError, match="changed during export"):
        c.build(source_root)


def test_unknown_graph_part_fails_even_with_55_source_rows(monkeypatch):
    original = c.yaml.safe_load

    def altered(value):
        parsed = original(value)
        if (
            isinstance(parsed, dict)
            and parsed.get("id") == c.rp1_inspection.ID
            and "parts" in parsed
        ):
            for part in parsed["parts"]:
                if part["id"] == "fin_tabs":
                    part["id"] = "unrelated_part"
        return parsed

    monkeypatch.setattr(c.yaml, "safe_load", altered)
    with pytest.raises(ValueError, match="unknown part IDs"):
        c.build(ROOT)
