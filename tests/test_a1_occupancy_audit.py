"""Known annular-volume arithmetic exposes the retained material conflict."""

import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_declared_material_intersection_is_positive_and_not_adopted():
    run = ROOT / "runs/wo03-a1-occupancy-audit-20261102-v1"
    r = json.loads((run / "record.json").read_text())
    mica, foil = r["intersections"]
    assert mica["overlap_z_mm"] == [1193, 1195]
    assert mica["intersection_mm3"] == pytest.approx(23.84 * math.pi)
    assert foil["intersection_mm3"] == pytest.approx(1.2088 * math.pi)
    assert all(i["declared_coaxial_material_overlap"] for i in (mica, foil))
    assert r["original_A1_results_rerun"] is False
    assert r["geometry_mass_or_thermal_correction_executed"] is False
    assert r["cpu_s"] < 1
    assert (run / "executed-script.py").read_bytes() == (
        ROOT / "scripts/wo03_a1_occupancy_audit.py"
    ).read_bytes()
