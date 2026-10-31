"""The recovery audit must reject missing mass and never turn force balance into rating."""

from pathlib import Path

import pytest
import yaml

from scripts.wo03_recovery_budget_closure import (
    cut_plan,
    factored_acceleration,
    force_case,
    reverse_horns,
)
from src.vehicle.schema import load_vehicle


def test_recovery_cut_plan_counts_leader_join_and_positive_coupler_branch():
    cfg = yaml.safe_load(Path("configs/studies/wo03-recovery-budget-closure.yaml").read_text())
    plan = cut_plan(cfg)
    assert plan["end_count"] == 18
    assert plan["line_mass_g"] == pytest.approx(35.575)
    assert not plan["all_terminations_qualified"]
    cfg["cut_plan"][0]["standing_m"] = 0.1
    with pytest.raises(ValueError, match="shorter than axial"):
        cut_plan(cfg)


def test_recovery_force_balance_applies_growth_and_factor_once_without_rating():
    cfg = yaml.safe_load(Path("configs/studies/wo03-recovery-budget-closure.yaml").read_text())
    vehicle = load_vehicle("configs/vehicle/wo02/performance-g54.yaml")
    case = force_case(vehicle, cfg, 23.139, "timing_probe")
    assert case["force_balance_pass"]
    assert sum(row["growth_kg"] for row in case["branches"]) == pytest.approx(0.05)
    assert factored_acceleration(23.139, 0.3, 3) == pytest.approx(3 * (23.139**2 / 0.6 + 9.80665))
    assert case["fixed_rail_capacity_estimate_n"] == 660
    assert not case["fixed_all_transfer_through_rails_screen_pass"]
    assert not case["all_physical_branches_verified"]
    assert all(row["installed_capacity_n"] is None for row in case["branches"])


def test_inboard_rods_follow_the_rotated_horns_and_keep_gimbal_ends():
    vehicle = load_vehicle("configs/vehicle/platform/tvc-finned.yaml")
    before = vehicle.model_copy(deep=True)
    result = reverse_horns(vehicle)
    assert result["gimbal_rod_ends_unchanged"]
    assert result["rod_mass_estimate_8g_retained"]
    parts = {part.id: part for part in vehicle.parts}
    for horn, rod in zip(
        parts["servo_horns"].cad.parameters["segments_mm"],
        parts["gimbal_links"].cad.parameters["segments_mm"],
        strict=True,
    ):
        assert sum((a - b) ** 2 for a, b in zip(*horn, strict=True)) == pytest.approx(36)
        assert horn[1][:2] == rod[0][:2]
        assert parts["servo_horns"].position_m + horn[1][2] / 1000 == pytest.approx(
            parts["gimbal_links"].position_m + rod[0][2] / 1000
        )
    original_parts = {part.id: part for part in before.parts}
    assert parts["servo_pitch"] == original_parts["servo_pitch"]
    assert parts["servo_yaw"] == original_parts["servo_yaw"]
