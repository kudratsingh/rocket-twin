"""Two selected architectures: frozen sources, complete ledger and held admission."""

import hashlib
import json
import math
from pathlib import Path

import pytest

from src.api.workbench import build_workbench

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/wo03-architecture-space-mass-20261102-v1"


def test_archived_inputs_and_two_choices_preserve_stopped_approaches():
    record = json.loads((RUN / "record.json").read_text())
    archives = json.loads(
        (
            ROOT / "runs/wo03-c2-sandwich-socket-20261102-v2/source-dependencies/manifest.json"
        ).read_text()
    )
    for relative, expected in record["input_sha256"].items():
        if relative == "web/public/engineering-workbench/g80-c1.json":
            data = (json.dumps(build_workbench(), indent=2, allow_nan=False) + "\n").encode()
        else:
            path = ROOT / relative
            if relative.startswith("build/"):
                path = ROOT / archives[relative]["archive_path"]
            data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected, relative
    assert [row["id"] for row in record["arrangements"]] == record["selected_before_execution"]
    assert len(record["arrangements"]) == 2
    assert record["resources"]["CAD_FEA_thermal_freeflight_executed"] is False
    for key in ("cpu", "wall"):
        assert 0 < record["resources"][key + "_s"] < record["resources"][key + "_limit_s"]
    assert (RUN / "executed-script.py").read_bytes() == (
        ROOT / "scripts/wo03_architecture_space_mass.py"
    ).read_bytes()
    assert (RUN / "executed-config.yaml").read_bytes() == (
        ROOT / "configs/studies/wo03-architecture-space-mass.yaml"
    ).read_bytes()


def test_all_removed_functions_are_counted_once_and_balance_uses_same_ledger():
    record = json.loads((RUN / "record.json").read_text())
    c1 = json.loads(
        (ROOT / "runs/wo03-g80-mass-balance-revision-20261102-v2/record.json").read_text()
    )
    base = build_workbench()
    parts = {row["id"]: row for row in base["parts"]}
    for arrangement in record["arrangements"]:
        rows = arrangement["replacement_ledger"]
        assert len({row["id"] for row in rows}) == len(rows)
        removed = arrangement["removed_part_ids"]
        assert len(removed) == len(set(removed))
        assert all(identifier in parts for identifier in removed)
        assert "motor" not in removed and "independent_recovery" not in removed
        assert "recovery_battery" not in removed and "parachute" not in removed
        assert arrangement["gross_removed_g"] == pytest.approx(
            math.fsum(parts[identifier]["mass_g"] for identifier in removed)
        )
        assert math.fsum(row["mass_delta_g"] for row in rows) == pytest.approx(
            arrangement["net_mass_delta_g"]
        )
        assert all(row["function"] and row["basis"] for row in rows)
        delta_first = math.fsum(row["mass_delta_g"] * row["station_mm"] for row in rows)
        for case, old in zip(arrangement["cases"], c1["mass_scenario_results"][2:4], strict=True):
            assert case["separate_growth_g"] == 50
            assert case["total_g"] == pytest.approx(case["subtotal_without_separate_growth_g"] + 50)
            assert case["total_g"] == pytest.approx(
                old["loaded_mass_kg"] * 1000 + arrangement["net_mass_delta_g"]
            )
            assert case["total_g"] * case["cg_mm"] == pytest.approx(
                old["loaded_first_moment_kg_m"] * 1e6 + delta_first
            )
            assert case["required_severe_recovery_DF3_mean_N"] == pytest.approx(
                max(1782.253, 3 * case["total_g"] / 1000 * (20.4**2 / 0.6 + 9.80665))
            )
            assert case["full_intrinsic_inertia"] is None
        assert arrangement["cases"][1]["total_g"] - arrangement["cases"][0][
            "total_g"
        ] == pytest.approx(20)


def test_protected_fore_route_and_finite_connection_evidence_do_not_imply_admission():
    record = json.loads((RUN / "record.json").read_text())
    for arrangement in record["arrangements"]:
        space = arrangement["space"]
        assert space["recovery_vs_retainer_axial_gap_mm"] == 179
        assert space["outer_can_harness_min_after0p7mm_loss_mm"] > 0.1
        assert space["fore_cuff_real_windows_required"] is True
        assert space["window_wall_angle_reserve_deg"] > 0
        assert space["cuff_body_differential150_45_min_gap_mm"] > 0.1
        demand = arrangement["section_demands"]
        assert demand["cuff_body_mean_shear_pa"] < 1e6
        assert demand["cuff_half_section_hot_axial_stress_pa"] < 25e6
        assert demand["eccentric_lap_normal_edge_demand_proxy_pa"] > 0
        assert demand["qualified_peel_allowable_pa"] is None
        assert demand["cap_actual_effective_width_mm"] is None
        assert demand["installed_tube_joint_motion_mm"] is None
        assert demand["installed_flutter"] is None
        assert arrangement["status"].startswith("not_admitted")
    a, b = record["arrangements"]
    force = 220.75869590217366
    assert a["section_demands"]["single_fin_outer_root_reaction_DF3_N"] + a["section_demands"][
        "A_inner_root_reaction_DF3_N"
    ] == pytest.approx(force)
    assert a["section_demands"]["A_mean_root_interface_demand_pa"] > 0
    assert b["section_demands"]["panel_play_ideal_tube_best_case_proxy_mm"] > 1


def test_baseline_fails_while_longer_guide_results_stay_conditional():
    record = json.loads((RUN / "record.json").read_text())
    assert record["baseline_usable_m"] == 1.5
    assert record["formal_mps"] == 15 and record["planning_mps"] == 15.5
    for arrangement in record["arrangements"]:
        for case in arrangement["cases"]:
            guides = {g["usable_m"]: g for g in case["guides"]}
            assert guides[1.5]["rail_exit_speed_mps"] < 15
            assert case["baseline_formal_headroom_g"] < 0
            assert case["baseline_planning_headroom_g"] < case["baseline_formal_headroom_g"]
            assert guides[1.8]["rail_exit_speed_mps"] > 15.5
            assert case["loaded_static_cal"] > 1
