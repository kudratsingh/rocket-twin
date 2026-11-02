"""Read saved C2 evidence only; never import its timed execution script."""

import hashlib
import json
import math
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/wo03-c2-sandwich-socket-20261102-v2"
CFG_PATH = ROOT / "configs/studies/wo03-c2-sandwich-socket.yaml"


@pytest.fixture(scope="module")
def evidence():
    config = yaml.safe_load(CFG_PATH.read_text())
    return (
        json.loads((RUN / "record.json").read_text()),
        config,
        json.loads((ROOT / config["source_c1"]).read_text()),
    )


def test_frozen_inputs_execution_copies_and_failed_context_are_preserved(evidence):
    record, config, _ = evidence
    for relative, expected in record["input_sha256"].items():
        assert len(expected) == 64
        assert all(char in "0123456789abcdef" for char in expected)
        path = ROOT / relative
        # Source-only archived generators preserve this historical CAD identity;
        # generated mesh/binary bulk is not required by a fresh checkout.
        if relative.startswith("build/"):
            manifest = json.loads((RUN / "source-dependencies/manifest.json").read_text())
            archived = ROOT / manifest[relative]["archive_path"]
            assert hashlib.sha256(archived.read_bytes()).hexdigest() == expected
            if not path.exists():
                continue
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, relative
    assert (
        hashlib.sha256((ROOT / config["source_c1"]).read_bytes()).hexdigest()
        == config["source_sha256"]
    )
    assert (RUN / "executed-config.yaml").read_bytes() == CFG_PATH.read_bytes()
    assert (
        hashlib.sha256((RUN / "executed-script.py").read_bytes()).hexdigest()
        == record["input_sha256"]["scripts/wo03_c2_sandwich_socket.py"]
    )
    failed_run = ROOT / "runs/wo03-c2-sandwich-socket-20261102-v1"
    failure = json.loads((failed_run / "failure.json").read_text())
    assert failure["automatic_retry"] is False
    assert "stale CAD properties" in failure["error"]
    assert not (failed_run / "record.json").exists()
    assert (failed_run / "executed-config.yaml").read_bytes() == (
        RUN / "executed-config.yaml"
    ).read_bytes()
    assert record["resources"]["native_CAD_heat_flight_executed"] is False
    assert record["resources"]["threads"] == 1
    assert record["resources"]["cpu_limit_s"] == 10
    assert record["resources"]["wall_limit_s"] == 15
    assert config["budget"]["construction_candidates"] == 1
    for key in ("cpu", "wall"):
        assert 0 < record["resources"][f"{key}_s"] < record["resources"][f"{key}_limit_s"]
        assert record["resources"][f"{key}_limit_s"] <= config["budget"][f"{key}_s"]


def test_complete_replacement_ledger_retains_separate_growth_and_adverse_case(evidence):
    record, config, c1 = evidence
    rows = record["replacement_ledger"]
    assert len({row["id"] for row in rows}) == len(rows)
    assert all(
        row["function"] and row["basis"] and math.isfinite(row["station_mm"]) for row in rows
    )
    removed = -math.fsum(row["mass_delta_g"] for row in rows if row["mass_delta_g"] < 0)
    added = math.fsum(row["mass_delta_g"] for row in rows if row["mass_delta_g"] > 0)
    assert removed == pytest.approx(196.0917215174014)
    assert added == pytest.approx(250.02120951844594)
    assert added - removed == pytest.approx(record["net_added_mass_g"])
    assert record["net_added_mass_g"] == pytest.approx(53.92948800104456)
    assert config["criteria"]["separate_growth_g"] == 50
    assert config["criteria"]["extra_aft_g"] == 20
    assert config["criteria"]["extra_aft_station_mm"] == 1227
    assert config["criteria"]["motor_cg_probe_mm"] == 12.8
    cases = record["cases"]
    assert [case["id"] for case in cases] == ["nominal", "additional20g_motorCG_probe"]
    signed_moment_g_mm = math.fsum(row["mass_delta_g"] * row["station_mm"] for row in rows)
    for case, source in zip(cases, c1["mass_scenario_results"][2:4], strict=True):
        assert case["separate_full_growth_g"] == 50
        assert case["nominal_plus_optional20g_g"] + 50 == pytest.approx(case["total_g"])
        assert case["total_g"] == pytest.approx(
            source["loaded_mass_kg"] * 1000 + record["net_added_mass_g"]
        )
        assert case["total_g"] * case["cg_mm"] == pytest.approx(
            source["loaded_first_moment_kg_m"] * 1e6 + signed_moment_g_mm
        )
        assert case["cp_mm"] == source["cp_mm"]
        assert case["full_intrinsic_inertia"] is None
        assert "signed_ledger_axial_point_contribution_kg_m2" in case
        assert all(
            guide["worst_case_mass_kg"] == pytest.approx(case["total_g"] / 1000)
            for guide in case["guides"]
        )
    assert cases[1]["total_g"] - cases[0]["total_g"] == pytest.approx(20)
    assert cases[1]["cg_mm"] > cases[0]["cg_mm"]
    # The same severe opening case scales with each complete mass, without
    # recalculating trajectories or importing any simulator.
    assert cases[0]["severe_recovery_DF3_mean_N"] / cases[0]["total_g"] == pytest.approx(
        cases[1]["severe_recovery_DF3_mean_N"] / cases[1]["total_g"]
    )


def test_df3_is_applied_once_and_force_couple_transport_is_consistent(evidence):
    record, config, c1 = evidence
    load = record["load_case"]
    source = c1["mass_scenario_results"][2]["fin_load_screen"]
    assert load["DF_applied_once"] is True
    assert load["normal_DF3_N"] == pytest.approx(3 * source["normal_force_per_fin_unfactored_N"])
    assert load["root_DF3_Nm"] == pytest.approx(3 * source["root_moment_per_fin_unfactored_Nm"])
    root_radius = config["clearance"]["source_outer_body_radius_mm"] / 1000
    contact_start, depth = config["socket"]["contact_radius_depth_mm"]
    contact_radius = (contact_start + depth / 2) / 1000
    assert load["socket_center_DF3_Nm"] == pytest.approx(
        load["root_DF3_Nm"] + load["normal_DF3_N"] * (root_radius - contact_radius)
    )
    assert load["receiver_axis_DF3_Nm"] == pytest.approx(
        load["socket_center_DF3_Nm"] + load["normal_DF3_N"] * contact_radius
    )
    positive, negative = load["contact_N"]
    assert positive - negative == pytest.approx(load["normal_DF3_N"])
    assert (positive + negative) * depth / 4000 == pytest.approx(load["socket_center_DF3_Nm"])
    assert load["contact_area_each_mm2"] == pytest.approx(
        config["socket"]["axial_start_length_mm"][1] * depth / 2
    )


def test_failure_states_cannot_be_overridden_by_panel_or_formal_guide_results(evidence):
    record, config, _ = evidence
    assert record["status"] == "not_admitted_stop_before_CAD_FEA"
    panel = record["panel_and_finite_root"]
    joint = record["receiver_joint"]
    assert joint["mean_DF3_hot_bond_shear_pa"] > config["criteria"]["hot_bond_pa"]
    assert joint["hot1MPa_estimate_ratio"] < 1
    assert (
        panel["floor_pin_supported_point_load_stress_pa"] > config["criteria"]["G11_hot_bending_pa"]
    )
    limit_m = config["criteria"]["service_tip_mm"] / 1000
    assert panel["levels"][-1]["panel_total_m"] < limit_m
    assert panel["aggregate_service_motion_proxy_m"] > limit_m
    assert panel["bond_peel_and_face_compression_wrinkling_allowables"] is None
    assert joint["bearing_tearout_and_peel_capacity"] is None
    fit = record["fit"]
    assert fit["nominal_harness_link_min_mm"] == 0
    assert fit["after0p5mm_slack_and0p2mm_manufacturing_mm"] == pytest.approx(-0.7)
    assert fit["after0p5mm_slack_and0p2mm_manufacturing_mm"] < fit["minimum_required_mm"]
    assert "2D polygons only" in fit["scope"]
    for case in record["cases"]:
        guides = {item["usable_m"]: item for item in case["guides"]}
        assert set(guides) == {1.5, 1.8, 1.971}
        assert guides[1.5]["rail_screen_pass"] is False
        assert guides[1.8]["rail_screen_pass"] is False
        assert guides[1.971]["rail_screen_pass"] is True
        assert guides[1.971]["formal_margin_mps"] > 0
        assert guides[1.971]["planning_margin_mps"] < 0
        assert case["planning_1p971m_headroom_g"] < 0
    assert "No new solve" in record["thermal"]
    assert config["thermal"]["no_new_temperature_result"] is True
    assert "No installed dynamic/modal/flutter result" in record["flutter"]
    assert "No next candidate executed" in record["decision"]


def test_recorded_refinement_and_axis_radius_correction_do_not_qualify_installation(evidence):
    record, config, _ = evidence
    panel = record["panel_and_finite_root"]
    assert (
        [level["points"] for level in panel["levels"]]
        == config["budget"]["integration_points"]
        == [101, 401, 1601]
    )
    assert panel["existing_96point_method_error"] < 0.0001
    final, previous = panel["levels"][-1], panel["levels"][-2]
    change = max(
        abs(final[key] / previous[key] - 1)
        for key in ("panel_total_m", "cheek_and_finite_brace_tip_m")
    )
    assert change == pytest.approx(panel["final_relative_change"])
    assert change < 0.0001
    corrections = record["prior_receiver_radius_datum_correction"]
    for correction in corrections.values():
        assert correction["rocket_axis_to_fin_tip_m"] == pytest.approx(0.123)
        assert correction["axis_torque_DF3_Nm"] == record["load_case"]["receiver_axis_DF3_Nm"]
        assert correction["panel_socket_play_receiver_only_tip_m"] > 0.001
        assert "original_records_preserved_no_installed_acceptance" in correction["status"]
    assert corrections["R1"]["panel_socket_play_receiver_only_tip_m"] == pytest.approx(
        0.001054302383546538
    )
