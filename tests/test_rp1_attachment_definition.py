"""Protect evidence boundaries and independent arithmetic of the saved AD1 packet."""

import hashlib
import json
import math
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def record(version):
    return json.loads(
        (ROOT / f"runs/wo03-rp1-attachment-definition-20261103-{version}/record.json").read_text()
    )


def test_exact_once_ledger_and_separate_adverse_mass():
    r = record("v2")
    baseline = json.loads(
        (ROOT / "runs/wo03-f2-recovery-balanced-20261103-v2/record.json").read_text()
    )
    assert len(r["ledger"]) == len({p["id"] for p in r["ledger"]}) == 55
    physical_g = sum(p["mass_g"] for p in r["ledger"])
    assert physical_g - sum(p["mass_g"] for p in baseline["ledger"]) == pytest.approx(3.4)
    assert sum(p["cost_usd"] for p in r["ledger"]) == pytest.approx(476.688)
    for case in r["cases"]:
        assert case["total_mass_g"] == pytest.approx(
            physical_g + 50 + case["extra_aft_g"] + case["nylon_mass_probe_g"] - 55
        )
        assert case["motor_cg_probe_mm"] == (12.8 if case["case"] == "adverse" else 0)
        assert case["whole_mean_proxy_N"] == pytest.approx(
            3 * case["total_mass_g"] / 1000 * (20.4**2 / (2 * 0.3) + 9.80665)
        )
    assert r["physical_inertia"] is None
    assert not r["adopted"]


def test_geometry_correction_reuses_only_unchanged_outputs():
    before, after = record("v1"), record("v2")
    for key in ["fin", "slot_clearance", "method_check", "recovery_connections"]:
        assert before[key] == after[key]
    for a, b in zip(before["cases"], after["cases"], strict=True):
        assert a["total_mass_g"] == b["total_mass_g"]
        assert a["guide_mps"] == b["guide_mps"]
        assert b["cg_mm"] - a["cg_mm"] == pytest.approx(
            1e6 * 0.002 * (1.020 - 1.0722) / a["total_mass_g"]
        )
    assert after["resources"]["guide_cases_reexecuted"] == 0
    assert after["resources"]["strip_cases_reexecuted"] == 0
    study = yaml.safe_load((ROOT / "configs/studies/rp1-attachment-definition-v2.yaml").read_text())
    assert study["route"]["heat_abrasion_sleeve"]["axial_station_mm"] == [980, 1060]


def test_independent_length_and_clearance_arithmetic_not_capacity():
    r = record("v2")
    c = r["cord_geometry"]
    expected = 1981.2 - 2 * 300 - math.pi * (31.369 + 3.8) - (1072.2 - 160 + 20)
    assert c["available_external_reach_mm"] == pytest.approx(expected)
    assert expected > 300 > expected - 152.4
    assert c["notch_min_per_flank_mm"] == pytest.approx(0.3)
    assert r["slot_clearance"]["previous_min_per_flank_mm"] < 0.1
    assert r["slot_clearance"]["proposed_min_per_flank_mm"] >= 0.1
    assert c["knot_box_not_a_verified_knot"]
    assert r["recovery_connections"]["finished_attachment_capacity_N"] is None


def test_converged_arithmetic_does_not_promote_failed_panel_or_missing_peel():
    r = record("v2")
    f = r["fin"]
    assert f["factored_moment_Nm"] == 8.83
    assert f["factored_force_N"] == pytest.approx(
        8.83 / (0.06 * (0.13 + 2 * 0.065) / (3 * (0.13 + 0.065)))
    )
    assert f["relative_delta_last_two"] < 0.0001
    assert r["method_check"]["relative_error"] < 1e-6
    last = f["ideal_composite_strip_lower_deflection_only"][-1]
    assert last["maximum_bending_Pa"] > 5e6
    assert last["deflection_m"] > 0.001
    assert not f["bonded_panel_stress_screen_pass_only"]
    assert f["required_joint_rotation_stiffness_Nm_rad"] is None
    assert f["normal_peel_capacity"] is None
    assert f["installed_displacement"] is None
    assert f["installed_flutter"].startswith("unavailable")


def test_formal_planning_and_metadata_sensitivity_remain_distinct():
    nominal, adverse, _, metadata_adverse = record("v2")["cases"]
    assert adverse["guide_mps"]["1.5"] > 15
    assert nominal["guide_mps"]["1.5"] < 15.5
    assert adverse["planning_mass_headroom_g"] < 0 < adverse["formal_mass_headroom_g"]
    assert metadata_adverse["guide_mps"]["1.5"] < 15
    assert not metadata_adverse["probe_is_bound"]


def test_sources_match_frozen_successful_execution():
    for v in ["v1", "v2"]:
        for path, expected in record(v)["sources"].items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
