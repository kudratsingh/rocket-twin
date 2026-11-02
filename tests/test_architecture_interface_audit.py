"""Read saved retained-interface failure; do not execute another construction."""

import hashlib
import json
from pathlib import Path

import pytest

from src.api.workbench import build_workbench

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/wo03-architecture-interface-audit-20261102-v1"


def test_cold_fit_failure_and_missing_hot_evidence_cannot_become_admission():
    audit = json.loads((RUN / "record.json").read_text())
    for path, expected in audit["input_sha256"].items():
        data = (
            (json.dumps(build_workbench(), indent=2, allow_nan=False) + "\n").encode()
            if path.startswith("web/public/")
            else (ROOT / path).read_bytes()
        )
        assert hashlib.sha256(data).hexdigest() == expected
    assert audit["nominal_coupler_od_mm"] == 64
    assert audit["proposed_bore_diameter_mm"] == 64.4
    assert audit["minimum_radial_gap_mm"] == pytest.approx(0, abs=1e-12)
    assert audit["minimum_radial_gap_mm"] < audit["required_radial_gap_mm"]
    assert audit["deficit_mm"] == pytest.approx(0.1)
    assert audit["maximum_nominal_coupler_od_for_same_bore_and_bounds_mm"] == 63.8
    assert audit["hot_fit_and_actual_supplier_or_manufacturing_tolerances"] is None
    assert audit["joint_stop_envelope"]["actual_CAD_interference"] is None
    assert audit["engineering_or_geometry_changed"] is False
    assert audit["previous_stopped_calculation_repeated"] is False
    assert 0 < audit["cpu_s"] < audit["cpu_limit_s"]


def test_archived_drawing_source_survives_safe_default_maintenance():
    run = ROOT / "runs/wo03-architecture-drawings-20261102-v1"
    maintenance = json.loads((run / "safe-default-maintenance.json").read_text())
    old = (run / "executed-script.py").read_bytes()
    maintained = (ROOT / "scripts/wo03_architecture_drawings.py").read_bytes()
    assert hashlib.sha256(old).hexdigest() == maintenance["original_sha256"]
    assert hashlib.sha256(maintained).hexdigest() == maintenance["maintained_sha256"]
    assert (
        old.replace(
            b'ROOT / "runs/wo03-architecture-drawings-20261102-v1"',
            b'ROOT / "build/wo03-architecture-drawings"',
        )
        == maintained
    )
    assert maintenance["native_or_engineering_rerun"] is False
