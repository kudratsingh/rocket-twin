"""Pinned manufacturer XY coverage and unknown-height boundaries; no CAD execution."""

import json
from pathlib import Path

import pytest

from scripts.wo04_high_g_pcb_detail_export import ID, OUTPUT, extract

ROOT = Path(__file__).resolve().parents[1]


def packet():
    return json.loads(OUTPUT.read_text())


def test_recorded_layer_packet_has_actual_features_and_retains_missing_z():
    data = packet()
    assert data["id"] == ID
    assert (
        data["source"]["sha256"]
        == "7c089eb8cc0756b7dc5e30abd240978dc272113d93f602b497f8f442d532d68c"
    )
    assert data["units"] == "mm"
    assert data["pcb_size_mm"] == [25.4, 17.78]
    assert data["nominal_product_envelope_mm"] == [25.6, 17.7, 4.6]
    assert data["pcb_minus_nominal_xy_mm"] == [-0.2, 0.08]
    assert data["pcb_thickness_mm"] is None
    assert data["component_heights_available"] is False
    assert all(p["height_mm"] is None for p in data["placements"] + data["pads"])
    assert next(p for p in data["placements"] if p["ref"] == "U1")["value"] == "ADXL343"
    assert {tuple(h["center_mm"]) for h in data["mounting_holes"]} == {
        (2.54, 15.24),
        (22.86, 15.24),
        (2.54, 2.54),
        (22.86, 2.54),
    }
    assert {h["radius_mm"] for h in data["mounting_holes"]} == {1.25}
    assert data["license"]["spdx"] == "CC-BY-SA-3.0"
    assert "5374" in data["license"]["upstream_notice"]
    assert data["canonical_vehicle_geometry_changed"] is False
    assert data["mass_or_inertia_generated"] is False
    assert data["engineering_accepted"] is False


def test_source_nets_pads_routes_and_real_artwork_have_complete_recorded_coverage():
    data = packet()
    assert data["counts"]["placements"] == 26
    assert data["counts"]["smd_pads"] == 68
    assert data["counts"]["through_pads"] == 14
    assert len(data["traces"]) == 208
    assert sum(t["layer"] == 1 for t in data["traces"]) == 151
    assert sum(t["layer"] == 16 for t in data["traces"]) == 57
    pads = {(p["ref"], p["name"]): p for p in data["pads"]}
    contacts = [(n["name"], c["ref"], c["pad"]) for n in data["nets"] for c in n["contacts"]]
    assert len(data["nets"]) == 14
    assert len(contacts) == 71
    assert all(pads[ref, pad]["net"] == net for net, ref, pad in contacts)
    assert len(data["vias"]) == 26
    assert all(v["diameter_mm"] is None and v["drill_mm"] > 0 for v in data["vias"])
    assert len(data["copper_polygon_boundaries"]) == 2
    assert all(
        p["net"] == "GND" and not p["poured_fill_available"]
        for p in data["copper_polygon_boundaries"]
    )
    groups = data["silkscreen"]["rectangle_groups"]
    assert sum(len(g["corners_mm"]) for g in groups) == 4876
    assert all(len(corners) == 8 for g in groups for corners in g["corners_mm"])
    assert {g["layer"] for g in groups} == {21, 22}
    assert len(data["silkscreen"]["texts"]) == 19
    assert all(not t["glyph_outlines_available"] for t in data["silkscreen"]["texts"])


def test_actual_mirrored_bottom_jumper_is_positioned_and_layered_without_inventing_z():
    data = packet()
    pad = next(p for p in data["pads"] if p["ref"] == "SJ1" and p["name"] == "1")
    assert pad["mirrored"] is True and pad["layer"] == 16
    assert pad["center_mm"] == [5.842, 12.7]
    assert pad["net"] == "N$2"
    assert any(
        pad["center_mm"] in trace["points_mm"] for trace in data["traces"] if trace["net"] == "N$2"
    )
    assert pad["height_mm"] is None


def test_wrong_source_stops_and_optional_original_cache_reproduces_exact_packet():
    with pytest.raises(ValueError, match="pinned immutable"):
        extract(b"<eagle/>", "Creative Commons 5374")
    source = ROOT / ".cache/hardware-detail-sources/Adafruit_ADXL375_4a768fc9.brd"
    notice = ROOT / ".cache/hardware-detail-sources/Adafruit_ADXL375_README.md"
    if not source.exists() or not notice.exists():
        pytest.skip("Original manufacturer bytes are optional local cache")
    assert extract(source.read_bytes(), notice.read_text().rstrip() + "\n") == packet()
