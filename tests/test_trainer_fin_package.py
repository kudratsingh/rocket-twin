"""Bounded layered-fin smoke: dimensions, explicit load transfer and no false pass."""

from pathlib import Path

import numpy as np
import pytest
import yaml

from scripts.wo03_trainer_fin_root import (
    composite_properties,
    curved_foot,
    layered_panel,
    layered_shapes,
    reconcile_root_adhesive_budget,
    root_support_extents,
    shifted_copy,
    torsion_targets,
)
from src.vehicle.schema import load_vehicle


@pytest.fixture(scope="module")
def cfg():
    return yaml.safe_load(Path("configs/studies/wo03-trainer-fin-package.yaml").read_text())[
        "root_closure"
    ]


def test_layered_panel_scales_with_load_and_keeps_missing_components_open(cfg):
    a = layered_panel(cfg, 57.63, 0.07, 0.12, 16)
    b = layered_panel(cfg, 115.26, 0.07, 0.12, 64)
    assert b["panel_only_tip_deflection_m"] == pytest.approx(
        2 * a["panel_only_tip_deflection_m"], rel=1e-12
    )
    assert a["minimum_skin_thickness_m"] == pytest.approx(0.00012)
    assert a["minimum_core_thickness_m"] == pytest.approx(0.0047)
    assert 0 < a["root_translation_and_rotation_compliance_budget_m"] < 0.001
    assert b["required_bending_root_rotation_stiffness_nm_rad_if_no_translation"] is None
    assert "chordwise normal" in a["stress_components_not_calculated"]
    assert not a["strength_acceptance_passed"]
    torsion = torsion_targets(cfg, a, 3430.301963243934, 0.07, 0.12)
    assert torsion["required_total_static_torsion_K_nm_rad"] > 0
    assert not torsion["NACA_TN4197_substitution_allowed"]
    assert not torsion["dynamic_flutter_acceptance_passed"]


def test_panel_unit_load_integral_matches_uniform_beam_reference(cfg):
    # All layers become one homogeneous rectangular beam when their E values
    # coincide and the face-bond thickness is zero. Independent uniform-load
    # cantilever and shear formulas verify the unit-load calculation.
    c = dict(cfg)
    c.update(
        skin_youngs_pa_typical=2e9,
        core_youngs_pa_typical=2e9,
        core_shear_pa_typical=0.2e9,
        face_bond_thickness_m=0.0,
    )
    f, length, width = 13.0, 0.07, 0.12
    row = layered_panel(c, f, length, width)
    tc = c["core_thickness_m"] - c["core_thickness_tolerance_m"]
    ts = c["skin_thickness_m"] - c["skin_thickness_tolerance_m"]
    ei = 1e9 * width * (tc + 2 * ts) ** 3 / 12
    expected_bending = f * length**3 / (8 * ei)
    expected_shear = f * length / (2 * 0.1e9 * width * tc)
    assert row["bending_tip_deflection_m"] == pytest.approx(expected_bending, rel=1e-12)
    assert row["core_shear_tip_deflection_m"] == pytest.approx(expected_shear, rel=1e-12)


def test_curved_foot_balances_force_and_moment_without_claiming_installed_stiffness(cfg):
    a = curved_foot(cfg, 57.63, 0.07, 0.12, 0.033, 0.00408, 0.0001)
    b = curved_foot(cfg, 57.63, 0.07, 0.12, 0.033, 0.00408, 0.0003)
    assert np.linalg.norm(a["force_and_moment_residual"]) < 1e-9
    assert b["added_tip_motion_from_rigid_root_m"] == pytest.approx(
        3 * a["added_tip_motion_from_rigid_root_m"], rel=1e-12
    )
    assert b["required_hot_normal_strength_DF3_pa"] == pytest.approx(
        a["required_hot_normal_strength_DF3_pa"]
    )
    assert a["fin_face_bond_area_per_side_m2"] == pytest.approx(0.0024)
    assert a["actual_foot_area_per_side_m2"] < a["fin_face_bond_area_per_side_m2"]
    assert a["installed_stiffness_lower_bound"] is None
    assert not a["peel_acceptance_passed"]


def test_shift_and_explicit_layer_mass_do_not_mutate_active_geometry(cfg):
    base = load_vehicle("configs/vehicle/platform/tvc-finned.yaml")
    v = shifted_copy(base, cfg)
    old, new = root_support_extents(base), root_support_extents(v)
    assert old["unsupported_foot_aft_length_m"] == pytest.approx(0.025)
    assert new["unsupported_foot_aft_length_m"] == pytest.approx(0, abs=1e-12)
    assert new["whole_tab_inside_frame_axial_extent"]
    assert new["shell_slot_front_station_m"] == pytest.approx(new["tab_stations_m"][0])
    assert new["frame_channel_front_station_m"] == pytest.approx(new["tab_stations_m"][0])
    layers = layered_shapes(v, cfg)
    props = composite_properties(layers)
    skins = [r for r in props["layers"] if r["name"].startswith("skin_")]
    assert sum(r["mass_kg"] for r in skins) == pytest.approx(2 * 3 * 0.07 * 0.12 * 0.35)
    assert all(r["valid_solid"] for r in props["layers"])
    # Every material owns its volume once; structural cap laps must not pass
    # through the plywood root gussets to obtain an artificially light mass.
    for i, (name, shape, _) in enumerate(layers):
        for other_name, other, _ in layers[i + 1 :]:
            assert shape.intersect(other).Volume() < 1e-5, (name, other_name)


def test_existing_root_bond_budget_allocates_once_and_keeps_new_bonds_additional(cfg):
    base = load_vehicle("configs/vehicle/platform/tvc-finned.yaml")
    v = shifted_copy(base, cfg)
    props = composite_properties(layered_shapes(v, cfg))
    original_fin_mass = next(p for p in v.parts if p.id == "fin_set").resolved_mass_kg
    ledger = reconcile_root_adhesive_budget(v, props["layers"], 0.00018, 0.001, cfg)
    residual = next(p for p in v.parts if p.id == "fin_bonds")
    assert ledger["overlap_removed_from_residual_budget_kg"] == pytest.approx(0.00362654720131877)
    assert residual.resolved_mass_kg == pytest.approx(0.00437345279868123)
    assert ledger["existing_root_interfaces_total_after_allocation_kg"] == pytest.approx(0.008)
    assert ledger["additional_new_construction_mass_kg"] == pytest.approx(
        {
            "skin_core_manufacturing_bonds": 0.006048,
            "structural_cap_bonds": 0.00018,
            "outer_tip_seal": 0.001,
            "new_frame_shell_gap_bonds": 0.00129037000775526,
        }
    )
    assert ledger["total_bond_and_seal_mass_after_reconciliation_kg"] == pytest.approx(
        0.0165183700077552
    )
    assert next(p for p in v.parts if p.id == "fin_set").resolved_mass_kg == original_fin_mass
    assert next(p for p in base.parts if p.id == "fin_bonds").resolved_mass_kg == 0.008
    # Re-running allocation on an already reconciled copy must fail; it must
    # never subtract the same explicit root interfaces twice.
    with pytest.raises(ValueError, match="unreconciled baseline allowance exactly once"):
        reconcile_root_adhesive_budget(v, props["layers"], 0.00018, 0.001, cfg)
