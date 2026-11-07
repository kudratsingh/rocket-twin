"""VP1 snapshot invariants and fail-closed source handling."""

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "vp1_export", ROOT / "scripts/wo04_vp1_validation_export.py"
)
export = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(export)


@pytest.fixture
def fixture_root(tmp_path):
    manifest = yaml.safe_load((ROOT / export.MANIFEST).read_bytes())
    for path in [export.MANIFEST, *manifest["source_sha256"]]:
        destination = tmp_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, destination)
    return tmp_path


def repin(root, path):
    manifest_path = root / export.MANIFEST
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest["source_sha256"][path] = hashlib.sha256((root / path).read_bytes()).hexdigest()
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))


def test_actual_snapshot_contract():
    result = export.build()
    assert result["id"] == "RP1-VP1-inspection-preview-v1"
    assert result["configuration"]["sha256"] == export.CONFIG_HASH
    assert result["costs"]["room_materials_usd"] == "236.75"
    assert result["costs"]["full_materials_usd"] == "269.49"
    assert result["costs"]["all_in_usd"] is None
    assert not any(result["approvals"].values())
    assert [s["id"] for s in result["stages"]] == ["S0", "S1", "S2a", "S2b"]
    assert all(s["status"] == "not-authorized" for s in result["stages"])
    assert all(p["status"] == "unverified" for p in result["parts"])
    assert [m["id"] for m in result["messages"]] == list(export.MESSAGE_IDS)
    for message in result["messages"]:
        assert message["text"] == (ROOT / message["source"]["path"]).read_text()
        assert message["source"]["sha256"] == hashlib.sha256(message["text"].encode()).hexdigest()
    assert all(link["part_id"] in {p["id"] for p in result["parts"]} for link in result["links"])


def test_missing_source_fails(fixture_root):
    (fixture_root / export.PROTOCOL).unlink()
    with pytest.raises(FileNotFoundError):
        export.build(fixture_root)


def test_source_drift_fails(fixture_root):
    with (fixture_root / export.MESSAGE_PATHS[0]).open("a") as f:
        f.write("changed")
    with pytest.raises(ValueError, match="Source hash mismatch"):
        export.build(fixture_root)


def test_configuration_drift_fails_even_if_repinning(fixture_root):
    with (fixture_root / export.VEHICLE).open("a") as f:
        f.write("\n# changed\n")
    repin(fixture_root, export.VEHICLE)
    with pytest.raises(ValueError, match="Configuration identity"):
        export.build(fixture_root)


def test_approval_change_fails_even_if_records_repinned(fixture_root):
    plan_path = fixture_root / export.PLAN
    plan = yaml.safe_load(plan_path.read_text())
    plan["supplier_contact_authorized"] = True
    plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))
    repin(fixture_root, export.PLAN)
    accounting_path = fixture_root / export.ACCOUNTING
    accounting = json.loads(accounting_path.read_text())
    accounting["plan_sha256"] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    accounting_path.write_text(json.dumps(accounting))
    repin(fixture_root, export.ACCOUNTING)
    with pytest.raises(ValueError, match="Approval state changed"):
        export.build(fixture_root)


def test_accounting_provenance_fails(fixture_root):
    path = fixture_root / export.ACCOUNTING
    data = json.loads(path.read_text())
    data["plan_sha256"] = "0" * 64
    path.write_text(json.dumps(data))
    repin(fixture_root, export.ACCOUNTING)
    with pytest.raises(ValueError, match="Accounting provenance"):
        export.build(fixture_root)
