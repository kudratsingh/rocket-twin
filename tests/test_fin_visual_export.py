"""Recorded schematic dimensions, never a new fin construction or solver."""

import json

from scripts.wo04_fin_visuals_export import ROOT, build


def test_recorded_visual_export_preserves_source_and_stock_dimensions():
    value = build()
    assert value == json.loads((ROOT / "web/src/data/rp1FinVisuals.json").read_text())
    assert value["profile"]["span_m"] == 0.06
    assert value["studies"][0]["core_m"] == 0.006
    assert value["studies"][1]["skin_each_m"] == 0.0005
    assert value["studies"][1]["bond_each_m"] == 0.00004
    assert value["studies"][2]["core_m"] == 0.003175
    assert all("status" in row for row in value["studies"])
    assert "not finished CAD" in value["scope"]
