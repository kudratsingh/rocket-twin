"""Verified finite-overlap reduction and retained engineering evidence boundaries."""

import math

import pytest

from src.analysis.bonded_support import (
    annular_brace_sensitivity,
    bonded_path_hand_budget,
    overlap_beam_spring,
    overlap_known_case,
    peel_foundation_known_case,
)


def test_axial_known_case_and_eccentric_overlap() -> None:
    fixture = overlap_known_case(120)
    assert fixture["verified"]
    assert fixture["max_point_relative_error"] < 0.0001
    assert peel_foundation_known_case(120)["verified"]
    result = overlap_beam_spring(
        divisions=120,
        length_mm=150.0,
        overlap_mm=100.0,
        width_mm=2 * math.pi * 33,
        thickness_mm=(0.5, 0.2),
        young_mpa=(250.0, 250.0),
        adhesive_thickness_mm=0.1,
        adhesive_young_mpa=2.0,
        adhesive_poisson=0.3,
        force_n=60.0,
        outer_load_fraction=1.0,
        radius_mm=33.0,
        hoop_young_mpa=(250.0, 250.0),
    )
    # The outer sleeve is not axially fixed. All applied force must traverse its
    # finite adhesive overlap into the base, with normal/peel as well as shear.
    assert result["max_axial_displacement_mm"] > 0
    assert result["peak_tensile_peel_mpa"] > 0
    assert result["peak_abs_adhesive_shear_mpa"] > 0
    assert abs(result["axial_equilibrium_residual_n"]) < 1e-7
    assert result["external_work_nmm"] == pytest.approx(2 * result["strain_energy_nmm"], rel=1e-8)
    assert not result["contact_or_failure_model"]
    assert not result["measured_data_used"]
    assert not result["physical_qualification"]
    # No silent clipping of unsupported or invalid geometry.
    with pytest.raises(ValueError, match="overlap start"):
        overlap_beam_spring(
            divisions=119,
            length_mm=150.0,
            overlap_mm=100.0,
            width_mm=100.0,
            thickness_mm=(0.5, 0.2),
            young_mpa=(250.0, 250.0),
            adhesive_thickness_mm=0.1,
            adhesive_young_mpa=2.0,
            adhesive_poisson=0.3,
            force_n=60.0,
            outer_load_fraction=1.0,
        )


def test_ring_bond_body_and_joint_remain_serial() -> None:
    cfg = {
        "force_n": 60.0,
        "ring_bond_areas_mm2": [607.9, 607.9, 542.1, 542.1, 542.1],
        "ring_stations_mm": [0.0, 55.0, 110.0, 148.5, 187.0],
        "rail_area_mm2": 35.0,
        "rail_weak_i_mm4": 40.0,
        "paper_hot_mpa": 250.0,
        "plywood_hot_mpa": 1000.0,
        "adhesive_hot_mpa": 20.0,
        "bond_gap_mm": 0.5,
        "upper_wall_mm": 0.5,
        "aft_wall_mm": 0.5,
        "joint_stiffness_n_mm": 10.0,
    }
    soft = bonded_path_hand_budget(**cfg)
    cfg["joint_stiffness_n_mm"] = 1000.0
    cfg["rail_force_n"] = 120.0
    stiff = bonded_path_hand_budget(**cfg)
    assert soft["optimistic_serial_path_stiffness_n_mm"] < 10.0
    assert soft["optimistic_axial_shortening_mm"] > stiff["optimistic_axial_shortening_mm"]
    assert (
        soft["required_hot_bond_shear_mpa_if_one_smallest_ring"]
        > soft["required_hot_bond_shear_mpa_if_uniform_all_rings"]
    )
    assert soft["unbraced_full_length_euler_n"] < soft["ideally_braced_euler_n"]
    assert stiff["required_hot_bond_shear_mpa_if_uniform_all_rings"] == pytest.approx(
        2 * soft["required_hot_bond_shear_mpa_if_uniform_all_rings"]
    )
    assert soft["ring_bond_peel_strength_required_mpa"] is None
    assert not soft["numerical_assembly_acceptance"]
    ring = annular_brace_sensitivity(31.82, 24.8, 3.0, 1000.0, 26.8)
    assert ring["continuous_inner_band"]["radial_width_mm"] == pytest.approx(2.0)
    assert ring["continuous_inner_band"]["unperforated_section_inplane_i_mm4"] == pytest.approx(2.0)
    assert not ring["actual_assembled_support_stiffness_available"]
