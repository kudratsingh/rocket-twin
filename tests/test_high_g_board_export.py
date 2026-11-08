"""Source and omission checks for the separate manufacturer PCB drawing."""

import json
from pathlib import Path

import pytest

from scripts.wo04_high_g_board_export import BLOB, OUTPUT, SHA256, extract


def test_layout_retains_identity_dimensions_and_unknowns():
    data = json.loads(OUTPUT.read_text())
    assert data["source"]["git_blob_sha"] == BLOB
    assert data["source"]["sha256"] == SHA256
    assert data["pcb_size_mm"] == [25.4, 17.78]
    assert data["nominal_product_envelope_mm"] == [25.6, 17.7, 4.6]
    assert data["pcb_minus_nominal_xy_mm"] == [-0.2, 0.08]
    assert data["mating_tolerance_mm"] is None
    assert len(data["placements"]) == 26
    assert all(p["height_mm"] is None for p in data["placements"])
    assert next(p for p in data["placements"] if p["ref"] == "U1")["value"] == "ADXL343"
    assert len(data["mounting_holes"]) == 4
    assert {h["radius_mm"] for h in data["mounting_holes"]} == {1.25}
    assert data["license"]["spdx"] == "CC-BY-SA-3.0"
    assert "5374" in data["license"]["upstream_notice"]
    assert data["engineering_accepted"] is False


def test_wrong_artifact_is_rejected_before_parsing():
    with pytest.raises(ValueError, match="pinned immutable"):
        extract(b"<eagle/>", "Creative Commons 5374")


def test_checked_data_reproduces_if_optional_cached_source_exists():
    folder = Path(__file__).resolve().parents[1] / ".cache/hardware-detail-sources"
    raw = folder / "Adafruit_ADXL375_4a768fc9.brd"
    notice = folder / "Adafruit_ADXL375_README.md"
    if not raw.exists() or not notice.exists():
        pytest.skip("Optional upstream source cache is not committed")
    assert extract(raw.read_bytes(), notice.read_text().rstrip() + "\n") == json.loads(
        OUTPUT.read_text()
    )
