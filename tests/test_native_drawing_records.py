"""Saved offline image observations/provenance never imply browser acceptance."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_native_image_packet_keeps_actual_observations_separate_from_release():
    run = ROOT / "runs/wo04-offline-render-feasibility-20261102-v4"
    record = json.loads((run / "record.json").read_text())
    assert len(record["rendered"]) == 25
    assert record["elapsed_seconds"] < 120
    assert record["browser_used"] is False
    assert record["ui_window_created"] is False
    assert record["new_dependencies"] is False
    assert record["physics_or_cad_run"] is False
    assert record["visual_inspection"]
    assert (
        hashlib.sha256((run / "executed-script.py").read_bytes()).hexdigest()
        == record["renderer_script_sha256"]
    )
    export = ROOT / "runs/wo04-walkthrough-export-20261102-v4"
    fixture = json.loads((export / "known-arrow-render.json").read_text())
    assert fixture["exit_code"] == 0
    assert fixture["visual_observation"]["method"] == "view_image"
    assert hashlib.sha256((export / "executed-script.mjs").read_bytes()).hexdigest() == (
        "62085e1ce6eb0f1d21415ce34885cd0c4e6a2e850ae2147a7246bb5e20e698b3"
    )


def test_extension_electrical_correction_preserves_facts_and_unverified_interactions():
    run = ROOT / "runs/wo04-extended-drawings-20261102-v4"
    record = json.loads((run / "record.json").read_text())
    route = json.loads((run / "electrical-route-check.json").read_text())
    assert record["artifact_count"] == 11 and record["source_count"] == 33
    assert record["native"]["elapsed_seconds"] < 120
    assert route["source_nodes"] == 12 and route["source_edges"] == 11
    assert route["source_endpoints_preserved"] is True
    assert route["source_nets_pins_quantities_unchanged"] is True
    assert route["unrelated_node_intersections"] == []
    assert route["samples_per_curve"] == 401
    assert "not physical" in route["scope"]
    metadata = json.loads(
        (ROOT / "runs/wo04-export-provenance-20261102-v1/record.json").read_text()
    )
    assert metadata["browser_download_clicked"] is False
    assert metadata["new_native_render"] is False
    assert metadata["old"]["svg"] == metadata["current"]["svg"]
    assert metadata["current"]["export_source_count"] == 33
    for path, expected in metadata["source_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
