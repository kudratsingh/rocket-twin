"""Saved offline-export evidence is separate from browser/visual acceptance."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/wo04-walkthrough-export-20261102-v2"


def test_frozen_sources_and_export_implementation_match_portable_artifact_manifest():
    manifest = json.loads((RUN / "source-manifest.json").read_text())
    assert manifest["identity"]["configuration_id"] == "C1_closed_receiver_mass_balance"
    assert manifest["identity"]["cad_revision"] is None
    assert manifest["source_count"] == 15
    for row in manifest["sources"] + manifest["export_implementation"]:
        assert hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    assert len(manifest["artifacts"]) == 25
    assert len({r["path"] for r in manifest["artifacts"]}) == 25
    for drawing in manifest["artifacts"]:
        assert drawing["portable_style_attributes"] is True
        assert drawing["browser_verified"] is False
        assert drawing["header_max_characters"] <= 120
        assert drawing["drawing_y"] >= 148
        assert drawing["width"] > 0 and drawing["height"] > 0


def test_failed_renderer_and_pending_visual_browser_evidence_stay_explicit():
    record = json.loads((RUN / "record.json").read_text())
    assert record["artifact_count"] == 25
    assert record["browser_acceptance"] is False
    assert record["browser_used"] is False
    assert record["visual_png_inspection"] is False
    assert record["renderer_attempts"] == []
    assert [a["exit_code"] for a in record["historical_v1_renderer_attempts"]] == [13, 255]
    assert record["physical_calculations_performed"] is False
    assert record["cad_generated"] is False
    previous = ROOT / record["previous_run"]["path"]
    for name, filename in (
        ("record_sha256", "record.json"),
        ("manifest_sha256", "source-manifest.json"),
        ("archived_exporter_sha256", "executed-script.mjs"),
    ):
        assert (
            hashlib.sha256((previous / filename).read_bytes()).hexdigest()
            == record["previous_run"][name]
        )
    assert record["offline_artifact_checks"]["result"] == "passed"
    assert record["offline_artifact_checks"]["png_visual_inspection"] is False
