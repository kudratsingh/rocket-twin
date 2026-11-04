"""Known limits and mass-accounting checks for the unadopted fin screen."""

from __future__ import annotations

import copy

import pytest
import yaml

from scripts.wo03_rp1_attachment_definition import plate_displacement
from scripts.wo03_rp1_fin_precedent_replacement import (
    ROOT,
    STUDY,
    component_screen,
    diagnostic_sensitivities,
    replacement,
    section,
    sha,
)
from src.vehicle.mass import mass_properties
from src.vehicle.schema import load_vehicle


def test_layer_section_recovers_homogeneous_rectangular_beam() -> None:
    study = yaml.safe_load(STUDY.read_text())
    study["screening_inputs"]["carbon_E_Pa"] = 1e9
    study["geometry"]["bond_each_face_min_m"] = 0
    sec = section(study)
    height = sec["wood_m"] + 2 * sec["carbon_m"]
    assert sec["D_Nm"] == pytest.approx(1e9 * height**3 / 12, rel=1e-12)


def test_zero_skin_recovers_frozen_bare_panel_and_keeps_finite_root() -> None:
    study = yaml.safe_load(STUDY.read_text())
    study["geometry"]["carbon_each_face_min_m"] = 0
    study["geometry"]["plywood_thickness_min_m"] = 0.0058
    result = component_screen(study)
    expected = plate_displacement(1601, 0.0058, False)
    assert result["panel_bending_mm"] == pytest.approx(expected["deflection_m"] * 1000)
    assert result["finite_tab_translation_rotation_shear_mm"] > 0
    assert result["screen_total_tip_mm"] > result["panel_bending_mm"]
    assert result["installed_tip_movement_pass"] is None


def test_mass_replacement_reconciles_and_source_is_immutable() -> None:
    study = yaml.safe_load(STUDY.read_text())
    path = ROOT / study["source"]
    before = sha(path)
    source = load_vehicle(path)
    candidate, ledger = replacement(copy.deepcopy(study), source)
    delta = (mass_properties(candidate).mass_kg - mass_properties(source).mass_kg) * 1000
    assert delta == pytest.approx(ledger["net_change_g"], abs=1e-9)
    ids = {part.id for part in candidate.parts}
    for pid in study["mass_budget"]["retained_ids"]:
        assert pid in ids
    assert "root_gussets" not in ids
    assert "rp1_kevlar_wrap" in ids
    assert sha(path) == before


def test_refinement_and_material_degradation_are_visible() -> None:
    study = yaml.safe_load(STUDY.read_text())
    coarse, fine = (component_screen(study, n) for n in (1600, 6400))
    relative = abs(coarse["screen_total_tip_mm"] / fine["screen_total_tip_mm"] - 1)
    assert relative < 0.001
    soft = copy.deepcopy(study)
    soft["screening_inputs"]["carbon_E_Pa"] *= 0.5
    assert component_screen(soft)["screen_total_tip_mm"] > fine["screen_total_tip_mm"]
    assert fine["hot_wet_material_bounds_verified"] is False
    assert fine["installed_strength_pass"] is None


def test_stiffer_wood_can_fail_strength_without_failing_movement() -> None:
    study = yaml.safe_load(STUDY.read_text())
    study["screening_inputs"]["plywood_E_Pa"] = 8e9
    result = component_screen(study, 6400)
    assert result["screen_total_tip_mm"] < 1
    assert result["max_wood_bending_MPa"] > 5
    assert not result["conditional_numeric_pass"]
    rows = diagnostic_sensitivities(study)
    assert any(not row["result"]["conditional_numeric_pass"] for row in rows)
