"""Mass accounting, bounds and three-second requirements for unselected studies."""

from pathlib import Path

import pytest

from src.vehicle.mass import mass_properties
from src.vehicle.schema import load_vehicle
from src.vehicle.selection import candidate_vehicle, evaluate_candidate

BASE = "configs/vehicle/tvc-ascent-v1.yaml"
NEW = "configs/vehicle/motors/AeroTech_G25_152mm.eng"


def test_study_accounts_for_casing_once_and_mount_reserve() -> None:
    baseline = load_vehicle(BASE)
    original = baseline.model_dump()
    candidate = candidate_vehicle(baseline, NEW, 0.020, True)
    props = mass_properties(candidate)
    # Original 529 g includes F15 103 g and original mount 16 g.
    # Replace the complete motor, then add only the incremental mount reserve.
    assert props.mass_kg == pytest.approx(0.529 - 0.103 + 0.170 + 0.020)
    assert mass_properties(candidate, 1).mass_kg == pytest.approx(props.mass_kg - 0.097)
    for old, new in zip(baseline.parts, candidate.parts, strict=False):
        if old.type == "body_tube":
            assert new.model_dump() == old.model_dump()
            assert new.geometry["wall_m"] == 0.0016
    assert baseline.model_dump() == original
    assert candidate.motor is not None
    assert candidate.motor.mount_position_m == pytest.approx(0.5476)


def test_long_motor_cannot_silently_overhang() -> None:
    baseline = load_vehicle(BASE)
    fixed = evaluate_candidate(baseline, NEW, 0, False, False)
    assert not fixed["axial_bounds_pass"]
    assert fixed["motor_aft_m"] == pytest.approx(0.7384)
    assert "reference_comparison" not in fixed
    shifted = evaluate_candidate(baseline, NEW, 0.02, True, False)
    assert shifted["axial_bounds_pass"]
    assert shifted["mean_thrust_to_liftoff_weight"] > 3
    assert not shifted["mechanical_fit_verified"]
    assert not shifted["selected"]


def test_high_thrust_short_burn_cannot_pass(tmp_path: Path) -> None:
    # Synthetic test fixture, never a real motor source.
    source = tmp_path / "synthetic.eng"
    source.write_text("; synthetic only\nTEST 29 114 P .06 .103 TEST\n1 60\n2 0\n")
    row = evaluate_candidate(load_vehicle(BASE), str(source), 0, False, False)
    assert row["mean_thrust_to_liftoff_weight"] > 3
    assert row["burn_time_s"] == 2
    assert not row["nominal_performance_pass"]


def test_summary_preserves_mass_conflicts_and_posttest_constraint() -> None:
    from src.vehicle.selection import screen_summary

    row = screen_summary(
        load_vehicle(BASE),
        {
            "assembled_mass_hypotheses_kg": [0.1329, 0.1356],
            "published_average_thrust_n": 19.6,
            "posttest_total_impulse_ns": 55.08,
        },
        0.020,
    )
    assert [s["liftoff_mass_kg"] for s in row["mass_scenarios"]] == pytest.approx([0.5789, 0.5816])
    assert row["summary_only_twr"] == pytest.approx(19.6 / (0.5816 * 9.80665))
    assert row["mass_scenarios"][-1][
        "max_burn_time_for_twr_3_at_posttest_impulse_s"
    ] == pytest.approx(55.08 / (3 * 0.5816 * 9.80665))
    assert not row["selection_eligible"]
    assert row["reference_comparison"] is None
