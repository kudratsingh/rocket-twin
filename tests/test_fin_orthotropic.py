from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from src.analysis.fea import solver_path
from src.analysis.fin_fea import (
    _resolved_density,
    orthotropic_compliance,
    run_shell,
    shell_thickness_mm,
    uniform_load_beam_deflection_m,
)
from src.vehicle.schema import Part

CONSTANTS = {
    "E1_pa": 2.0e9,
    "E2_pa": 2.0e9,
    "E3_pa": 0.5e9,
    "nu12": 0.2,
    "nu13": 0.2,
    "nu23": 0.2,
    "G12_pa": 0.2e9,
    "G13_pa": 0.2e9,
    "G23_pa": 0.2e9,
}


def test_orthotropic_compliance_is_positive_definite_and_reciprocal() -> None:
    compliance = orthotropic_compliance(CONSTANTS)
    assert np.allclose(compliance, compliance.T)
    assert np.linalg.eigvalsh(compliance).min() > 0
    assert compliance[0, 1] == pytest.approx(-0.2 / 2.0e9)
    assert compliance[1, 0] == compliance[0, 1]


def test_invalid_orthotropic_compliance_is_rejected() -> None:
    invalid = {**CONSTANTS, "nu12": 1.1}
    with pytest.raises(ValueError, match="non-positive compliance"):
        orthotropic_compliance(invalid)


def test_shell_density_uses_resolved_material_or_explicit_override() -> None:
    part = type("MaterialPart", (), {"material": "plywood"})()
    assert _resolved_density(part, None) == 715.0
    assert _resolved_density(None, None) == 550.0
    assert _resolved_density(part, 600.0) == 600.0


def test_variable_ei_beam_fixture_and_constant_thickness_limit() -> None:
    force, span, chord, young, thickness = 1.0, 0.1, 0.01, 2.0e9, 0.001
    constant = uniform_load_beam_deflection_m(force, span, chord, young, lambda _x: thickness)
    inertia = chord * thickness**3 / 12
    assert constant == pytest.approx(force * span**3 / (8 * young * inertia), rel=1e-10)

    params = {
        "root_gusset_span_mm": 12.0,
        "root_gusset_base_mm": 3.0,
        "root_gusset_inset_mm": 1.0,
    }
    assert shell_thickness_mm(0.0, 6.05, params) == pytest.approx(6.05 + 6 * 12 / 13)
    assert shell_thickness_mm(12.0, 6.05, params) == pytest.approx(6.05)
    assert shell_thickness_mm(13.0, 6.05, params) == pytest.approx(6.05)
    variable = uniform_load_beam_deflection_m(
        force,
        span,
        chord,
        young,
        lambda x: shell_thickness_mm(x * 1000, 6.05, params) / 1000,
    )
    assert variable < uniform_load_beam_deflection_m(force, span, chord, young, lambda _x: 0.00605)


@pytest.mark.skipif(solver_path() is None, reason="CalculiX is optional for local tests")
def test_orthotropic_strip_matches_known_spanwise_e_deflection(tmp_path: Path) -> None:
    result = run_shell(
        tmp_path / "orthotropic-strip",
        None,
        size_mm=5.0,
        force_n=0.001,
        orthotropic=CONSTANTS,
    )
    assert result["material_model"] == "orthotropic engineering constants"
    assert result["density_kg_m3"] == 550.0
    assert result["compliance_positive_definite"] is True
    assert result["known_case_passed"] is True
    assert result["equilibrium_error_n"] < 1e-7
    assert abs(result["max_displacement_m"] / result["analytic_deflection_m"] - 1) < 0.05


@pytest.mark.skipif(solver_path() is None, reason="CalculiX is optional for local tests")
def test_gusset_profile_sections_and_root_refined_band(tmp_path: Path) -> None:
    part = SimpleNamespace(
        id="synthetic-gusset-strip",
        material="plywood",
        cad_mass=None,
        geometry={
            "span_m": 0.1,
            "root_chord_m": 0.01,
            "tip_chord_m": 0.01,
            "sweep_m": 0.0,
            "thickness_m": 0.001,
        },
        cad=SimpleNamespace(
            parameters={
                "root_gusset_span_mm": 12.0,
                "root_gusset_base_mm": 3.0,
                "root_gusset_inset_mm": 1.0,
            }
        ),
    )
    result = run_shell(tmp_path / "gusset-strip", cast(Part, part), size_mm=5.0, force_n=0.001)
    assert result["thickness_profile"]["section_count"] > 1
    assert result["thickness_profile"]["minimum_element_thickness_mm"] == pytest.approx(1.0)
    assert result["thickness_profile"]["maximum_element_thickness_mm"] > 6.0
    assert result["root_band_target_element_size_mm"] == 1.25
    assert result["root_band_element_count"] > 0
    assert result["regional_stress_by_actual_thickness_mm"]
    deck = (tmp_path / "gusset-strip" / "case.inp").read_text()
    assert "*SHELL SECTION,ELSET=TSEC_" in deck
