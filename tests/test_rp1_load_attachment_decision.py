"""Independent load accounting and finite-tab checks; no study/flight rerun."""

import copy
import hashlib
import json

import pytest
import yaml

from scripts.wo03_rp1_load_attachment_decision import (
    ROOT,
    STUDY,
    load_case,
    tab_compliance,
)
from scripts.wo04_rp1_studies_export import build


def test_force_moment_factor_and_planform_are_consistent():
    current = load_case(0.06, 0.13, 0.065)
    assert current["area_m2"] == pytest.approx(0.00585)
    assert current["centroid_m"] == pytest.approx(0.0266666666667)
    assert current["force_N"] == pytest.approx(108.94706343962352)
    assert current["moment_Nm"] == pytest.approx(2.9052550250566274)
    assert 8.83 / current["centroid_m"] == pytest.approx(331.125)
    assert load_case(0.09, 0.12, 0.06)["moment_Nm"] == pytest.approx(8.83034785883985)


def test_tab_matrix_recovers_independent_cantilever_work_and_reciprocity():
    study = yaml.safe_load((ROOT / STUDY).read_text())
    # Strip carbon and make core shear negligible: exact homogeneous beam case.
    study = copy.deepcopy(study)
    study["geometry"]["carbon_each_face_min_m"] = 0
    study["screening_inputs"]["plywood_G_Pa"] = 1e30
    answer = tab_compliance(study)
    h = study["geometry"]["tab_depth_m"]
    width = study["geometry"]["tab_chord_m"]
    t = study["geometry"]["plywood_thickness_min_m"]
    ei = study["screening_inputs"]["plywood_E_Pa"] * width * t**3 / 12
    c = answer["matrix_SI"]
    assert c[0][0] == pytest.approx(h**3 / (3 * ei))
    assert c[0][1] == c[1][0] == pytest.approx(h * h / (2 * ei))
    assert c[1][1] == pytest.approx(h / ei)
    assert c[0][0] * c[1][1] - c[0][1] ** 2 > 0


def test_record_does_not_turn_diagnostic_corners_or_budget_into_acceptance():
    record = json.loads((ROOT / "runs/wo03-rp1-d1-20261104-v1/record.json").read_text())
    assert len(record["material_corners"]) == 16
    assert record["all_diagnostic_corners_pass"] is False
    assert record["corners_are_verified_bounds"] is False
    assert record["installed_tip_movement"] is None
    assert record["new_construction_admitted"] is False
    assert record["FP1_panel_only_mm"] + record[
        "nominal_complete_root_ceiling_mm"
    ] == pytest.approx(1)
    # Whole-root ceiling replaces finite tab AND arbitrary reserve, not an extra spring.
    assert record["nominal_complete_root_ceiling_mm"] == pytest.approx(0.644264476804794)
    archive = ROOT / record["executed_source_archive"]
    assert (
        hashlib.sha256(archive.read_bytes()).hexdigest()
        == record["sources"]["scripts/wo03_rp1_load_attachment_decision.py"]
    )


def test_exported_studies_remain_distinct_and_reported_scope_is_preserved():
    value = build()
    fp, fr = value["studies"]
    assert fp["id"] != fr["id"]
    assert value["load_definition"]["required_moment_Nm"] == 8.83
    assert value["load_definition"]["proposal_adopted"] is False
    assert fp["displacement"]["attachment_budget_mm"] == pytest.approx(0.1)
    assert fp["displacement"]["reported_mm"] == pytest.approx(0.9612403332968898)
    assert fr["displacement"]["reported_mm"] > 1
    assert all(not x["installed_accepted"] for x in (fp, fr))
