"""Protect the frozen C1 evidence boundary and coupled admission decision."""

import hashlib
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/wo03-c1-fin-attachment-20261102-v1"


def record():
    return json.loads((RUN / "record.json").read_text())


def test_source_identity_and_growth_cannot_be_replaced_by_rounded_summary():
    r = record()
    for relative, expected in r["input_sha256"].items():
        # The staged helpers were byte-identical to the maintained source at run
        # time. Verify those published source files, not excluded generated bulk.
        if relative.startswith("build/"):
            relative = relative.split("/checkout/", 1)[1]
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    cases = {x["id"]: x for x in r["coupled_cases"]}
    assert cases["C1_nominal"]["total_with_growth_g"] == pytest.approx(1129.8067509765393)
    for case in cases.values():
        assert case["separate_growth_g"] == 50
        assert case["nominal_without_growth_g"] + 50 == case["total_with_growth_g"]
        assert case["full_intrinsic_inertia_kg_m2"] is None
        assert case["installed_acceptance"] is False
    assert cases["R1_plus20g_motorCG_probe"]["static_margin_cal"] < 1
    assert cases["R1_nominal"]["illustrative_1p971m_planning_headroom_g"] < 0
    assert cases["C1_nominal"]["illustrative_1p971m_planning_headroom_g"] > 22
    assert 2 < cases["C1_plus20g_motorCG_probe"]["illustrative_1p971m_planning_headroom_g"] < 3


def test_contact_moment_includes_transfer_arm_without_second_design_factor():
    r = record()
    load = r["load_case"]
    assert load["force_DF3_once_N"] == pytest.approx(3 * load["force_unfactored_N"])
    assert load["moment_DF3_once_Nm"] == pytest.approx(3 * load["moment_unfactored_Nm"])
    for structure in r["structures"].values():
        a = structure["attachment"]
        expected = load["moment_DF3_once_Nm"] + load["force_DF3_once_N"] * 0.0087
        assert a["socket_center_moment_DF3_Nm"] == pytest.approx(expected)
        pos, neg = a["contact_positive_negative_N"]
        assert pos - neg == pytest.approx(load["force_DF3_once_N"])
        assert (pos + neg) * 0.003 == pytest.approx(expected)
        assert a["bond_peel_capacity"] is None
        assert structure["installed_strength_deflection_and_flutter_accepted"] is False


def test_known_answer_refinement_does_not_turn_failed_installed_screen_into_pass():
    r = record()
    known = r["known_rectangular_beam"]
    assert known["final_relative_error"] < 0.0001
    errors = [abs(x["tip_m"] - known["exact_tip_m"]) for x in known["levels"]]
    assert errors[0] > errors[1] > errors[2]
    audit = json.loads((RUN / "connection-audit.json").read_text())
    assert (
        audit["source_record_sha256"]
        == hashlib.sha256((RUN / "record.json").read_bytes()).hexdigest()
    )
    for key, structure in r["structures"].items():
        assert len(structure["panel_states"]) == 2
        for state in structure["panel_states"]:
            assert len(state["levels"]) == 3
            assert state["final_relative_change"] < 0.0001
        assert audit["structures"][key]["corrected_1mm_remaining_m"] < 0
        assert audit["structures"][key]["socket_bridge_hot_1MPa_shear_estimate_ratio"] < 1


def test_added_mass_recovery_and_conditional_guides_use_same_complete_case():
    r = record()
    extra_g = math.fsum(x["mass_g"] for x in r["R1_added_ledger"])
    assert extra_g == pytest.approx(r["R1_added_mass_g"])
    cases = {x["id"]: x for x in r["coupled_cases"]}
    for suffix in ("nominal", "plus20g_motorCG_probe"):
        assert cases[f"R1_{suffix}"]["total_with_growth_g"] - cases[f"C1_{suffix}"][
            "total_with_growth_g"
        ] == pytest.approx(extra_g)
    for case in cases.values():
        mass = case["total_with_growth_g"] / 1000
        assert case["severe_recovery_DF3_mean_N"] == pytest.approx(
            3 * mass * (20.4**2 / 0.6 + 9.80665)
        )
        assert all(x["worst_case_mass_kg"] == pytest.approx(mass) for x in case["guide_screens"])
    adverse = cases["R1_plus20g_motorCG_probe"]["guide_screens"][-1]
    assert 0 < adverse["formal_speed_margin_mps"] < 0.001
    assert adverse["planning_speed_margin_mps"] < 0
