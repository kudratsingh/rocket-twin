from __future__ import annotations

import math

import pytest

from src.analysis.fin_attachment import (
    analyze_fin_attachment,
    fin_flutter_domain_assessment,
    gusset_pair_rotational_stiffness_nm_rad,
    normal_force_coefficient_per_radian,
    root_flexibility_flutter_sensitivity,
)


def test_rectangular_panel_loads_and_root_attachment_screens() -> None:
    span, chord = 0.070, 0.120
    slope = normal_force_coefficient_per_radian(span, chord, chord)
    cn = slope * math.radians(5.0)
    result = analyze_fin_attachment(
        configuration_id="synthetic-G12-F",
        dynamic_pressure_pa=40_000.0,
        normal_coefficient=cn,
        span_m=span,
        root_chord_m=chord,
        tip_chord_m=chord,
        gusset_span_mm=12.0,
        tab_engagement_length_mm=100.0,
        tab_radial_width_mm=6.0,
        body_wall_thickness_mm=0.5,
        frame_rail_width_mm=12.0,
        frame_rail_radial_depth_mm=3.0,
        rails_sharing_one_fin=1,
        tab_slot_width_mm=7.3,
        ring_count=3,
        ring_thickness_mm=3.0,
        bond_shear_modulus_pa=0.77e9,
        bondline_thickness_mm=0.2,
    )
    loads = result["loads_per_fin"]
    assert loads["planform_area_m2"] == pytest.approx(0.0084)
    assert loads["root_moment_nm_uniform_load_arm_span_over_2"] == pytest.approx(
        loads["normal_force_n"] * span / 2
    )
    assert result["gusset_bonds"]["nominal_triangular_face_area_per_side_mm2"] == 720.0
    assert result["gusset_bonds"]["peel_margin"] is None
    assert result["gusset_bonds"]["peel_status"].startswith("unavailable")
    # At this load a bare 0.5 mm kraft wall is inadequate without G11 backing credit.
    assert result["tab_and_body"]["kraft_shell_bearing_status"] == "screen-fail"
    assert result["tab_and_body"]["tab_slot_nominal_fit"][
        "nominal_per_side_clearance_mm_if_centered"
    ] == pytest.approx(0.65)
    assert result["structural_frame"]["rail_normal_bending_margin"] < 0
    assert result["structural_frame"]["span_root_to_rail_bending_moment_routing_verified"] is False
    assert "surrogate" in result["structural_frame"]["rail_bending_quantity_status"]
    assert result["structural_frame"]["rail_normal_bending_axis"].startswith("radial X")
    assert result["structural_frame"]["rail_normal_section_modulus_mm3"] == pytest.approx(72.0)
    assert result["structural_frame"]["rail_crossload_section_modulus_mm3"] == pytest.approx(18.0)
    assert result["structural_frame"]["rail_crossload_bending_stress_pa_single_support_bound"] == (
        pytest.approx(
            4.0 * result["structural_frame"]["rail_normal_bending_stress_pa_single_support_bound"]
        )
    )
    assert result["root_rotational_flexibility"]["gusset_pair_rotational_stiffness_nm_rad"] > 0
    assert result["acceptance_passed"] is False


def test_tvc_tab_and_hot_bond_use_explicit_dimensions_and_bounds() -> None:
    slope = normal_force_coefficient_per_radian(0.070, 0.120, 0.120)
    result = analyze_fin_attachment(
        configuration_id="synthetic-G12-F-hot",
        dynamic_pressure_pa=40_000,
        normal_coefficient=slope * math.radians(5),
        span_m=0.070,
        root_chord_m=0.120,
        tip_chord_m=0.120,
        gusset_span_mm=12,
        tab_engagement_length_mm=100,
        tab_radial_width_mm=2.5,
        body_wall_thickness_mm=0.5,
        frame_rail_width_mm=12,
        frame_rail_radial_depth_mm=2,
        rails_sharing_one_fin=1,
        tab_slot_width_mm=7.3,
        temperature_strength_fraction=0.5,
        hot_bond_allowable_pa=1e6,
        bond_shear_modulus_pa=0.77e9,
        bondline_thickness_mm=0.2,
    )
    assert result["materials_and_criteria"]["temperature_strength_fraction"] == 0.5
    assert result["gusset_bonds"]["used_area_per_side_mm2"] == 720.0
    assert result["tab_and_body"]["nominal_tab_bond_area_mm2"] == 250.0
    assert result["body_shell_local_bending"]["status"] == "unavailable"


def test_rotational_spring_and_flutter_sensitivity_reduce_free_root_bound() -> None:
    stiff = gusset_pair_rotational_stiffness_nm_rad(720, 12, 0.77e9, 0.2)
    assert stiff > 0
    very_stiff = root_flexibility_flutter_sensitivity(350, 0.070, 100.0, 1e12)
    flexible = root_flexibility_flutter_sensitivity(350, 0.070, 100.0, 100.0)
    assert float(very_stiff["frequency_ratio"]) == pytest.approx(1.0, rel=1e-6)
    assert float(flexible["frequency_ratio"]) < 1.0
    assert str(flexible["status"]).startswith("sensitivity-only")


def test_rectangular_flutter_geometry_matches_panel_domain_but_gate_stays_open() -> None:
    result = fin_flutter_domain_assessment(
        span_m=0.070,
        sweep_m=0.0,
        root_chord_m=0.120,
        tip_chord_m=0.120,
        base_fin_thickness_m=0.00605,
        root_gusset_thickness_varies=True,
        root_attachment_stiffness_verified=False,
        flight_max_q_available=False,
    )
    assert result["base_plate_constant_thickness_ratio_domain"] is True
    assert result["geometric_domain_status"].startswith("base plate matches")
    assert result["one_panel_aspect_ratio_span_over_midchord"] == pytest.approx(0.5833333333)
    assert result["quantitative_flutter_acceptance"] == "open"
