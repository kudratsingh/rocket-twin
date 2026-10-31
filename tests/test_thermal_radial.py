"""Independent solutions and opaque wall/gap energy balance, not rocket qualification."""

from pathlib import Path

import numpy as np
import pytest

from src.analysis.thermal_radial import (
    SIGMA,
    annular_wall,
    direct_contact_flux,
    known_cases,
    opaque_gap_flux,
    wall_heat_rates,
)


def test_known_heat_transfer_and_internal_conservation() -> None:
    assert known_cases()["passed"]
    wall = annular_wall(0.0147, 0.0151, 0.156, 0.2, 10, 8)
    assert abs(sum(wall.capacities_j_k) - 10) < 1e-12
    heat = wall_heat_rates(wall, np.linspace(500, 300, 8))
    assert abs(sum(heat)) < 1e-9
    assert heat[0] < 0 < heat[-1]


def test_half_walls_limit_exchange_and_reciprocity() -> None:
    geometry = (0.0151, 0.03, 0.1, 0.03, 0.9)
    q = opaque_gap_flux(500, 300, 2, 3, *geometry)
    reverse = opaque_gap_flux(300, 500, 3, 2, *geometry)
    assert 0 < q < 200 / 5
    assert abs(q + reverse) < 1e-9
    assert q < opaque_gap_flux(500, 300, 0, 0, *geometry)
    assert opaque_gap_flux(300, 300, 0, 0, *geometry) == 0


def test_distinct_surface_emissivities_match_reciprocal_cylindrical_radiation() -> None:
    inner_radius, outer_radius, length = 0.01, 0.02, 0.1
    eps_inner, eps_outer = 0.1, 0.9
    hot, cold = 500.0, 300.0
    geometry = (inner_radius, outer_radius, length, 0.0, 0.9)
    heat = opaque_gap_flux(
        hot,
        cold,
        0,
        0,
        *geometry,
        inner_surface_emissivity=eps_inner,
        outer_surface_emissivity=eps_outer,
    )
    expected = (
        SIGMA
        * (2 * np.pi * inner_radius * length)
        * (hot**4 - cold**4)
        / (1 / eps_inner + inner_radius / outer_radius * (1 / eps_outer - 1))
    )
    reverse = opaque_gap_flux(
        cold,
        hot,
        0,
        0,
        *geometry,
        inner_surface_emissivity=eps_inner,
        outer_surface_emissivity=eps_outer,
    )
    assert heat == pytest.approx(expected, rel=1e-12)
    assert heat == pytest.approx(-reverse, abs=1e-12)
    assert known_cases()["two_surface_emissivity_reciprocity_error_w"] < 1e-12


def test_direct_contact_uses_series_wall_and_interface_resistances_only() -> None:
    hot, cold = 500.0, 300.0
    resistance_hot_wall, resistance_cold_wall = 2.0, 3.0
    contact_conductance = 0.2
    heat = direct_contact_flux(
        hot,
        cold,
        resistance_hot_wall,
        resistance_cold_wall,
        contact_conductance,
    )
    expected = (hot - cold) / (resistance_hot_wall + 1 / contact_conductance + resistance_cold_wall)
    reverse = direct_contact_flux(
        cold,
        hot,
        resistance_cold_wall,
        resistance_hot_wall,
        contact_conductance,
    )
    assert heat == pytest.approx(expected)
    assert heat == pytest.approx(-reverse)
    assert known_cases()["direct_contact_reciprocity_error_w"] < 1e-12


def test_material_profiles_supply_foil_emissivity_and_new_thermal_screen_limits() -> None:
    import yaml

    cfg = yaml.safe_load(Path("configs/engineering/wo03.yaml").read_text())
    assert cfg["materials"]["mica"]["limit_c"] == 300
    assert cfg["materials"]["mica"]["conductivity_range_w_m_k"] == [0.2, 0.7]
    assert cfg["materials"]["mica"]["cp_range_j_kg_k"] == [700, 1100]
    assert cfg["materials"]["aluminum"]["surface_emissivity_by_scenario"] == [
        0.1,
        0.3,
        0.3,
        0.9,
    ]
    assert cfg["materials"]["G11"]["limit_c"] == 150
    assert cfg["materials"]["stainless_fastener"]["limit_c"] == 150
    assert cfg["materials"]["stainless_fastener"]["temperature_limit_sensitivity_c"] == [60, 150]
    assert cfg["materials"]["epoxy"]["limit_c"] == 65
    assert cfg["materials"]["epoxy"]["temperature_limit_sensitivity_c"] == [45, 65]
    assert cfg["materials"]["epoxy"]["hot_strength_reduction_fraction"] == 0.5
    assert cfg["materials"]["epoxy"]["substrate_properties_measured"] is False
    assert "96.1 C by DMA" in cfg["materials"]["epoxy"]["basis"]
    assert cfg["materials"]["epoxy"]["substrate_properties_measured"] is False
    assert "96.1 C by DMA and 98.9 C by DSC" in cfg["materials"]["epoxy"]["basis"]


def test_actual_open_frame_is_not_an_opaque_full_length_tube() -> None:
    import yaml

    from src.analysis.thermal_topology import annular_intervals, run_thermal_topology
    from src.vehicle.schema import load_vehicle

    vehicle = load_vehicle("configs/vehicle/platform/performance.yaml")
    frame = next(part for part in vehicle.parts if part.id == "motor_mount")
    intervals = annular_intervals(frame)
    assert len(intervals) == 3
    assert abs(sum(b - a for a, b in intervals) - 0.009) < 1e-12
    midpoint = frame.position_m + frame.geometry["length_m"] / 2
    assert not any(a <= midpoint <= b for a, b in intervals)
    cfg = yaml.safe_load(Path("configs/engineering/wo03.yaml").read_text())
    study = yaml.safe_load(Path("configs/studies/wo03-thermal-topology.yaml").read_text())
    result = run_thermal_topology(vehicle, cfg, study, True, cells=4)
    assert result["energy_residual_j"] < 1e-6
    assert result["model"] == "neutral-coaxial-material-shield-v3"
    direct = [
        interface
        for interface in result["interfaces"]
        if interface["model"] == "direct_solid_contact"
    ]
    assert direct
    assert all(
        interface["source_surface_radius_m"] == interface["target_surface_radius_m"]
        for interface in direct
    )
    assert sum(interface["contact_conductance_w_k"] for interface in direct) == pytest.approx(
        study["direct_contact_conductance_w_k"][1]
    )
    assert any(
        band_interface["model"] == "direct_solid_contact"
        for band in result["radial_bands"]
        for band_interface in band["interfaces"]
    )
    foil_outer_interfaces = [
        interface
        for interface in result["interfaces"]
        if interface["source_part_id"] == "motor_radiant_shield"
    ]
    assert foil_outer_interfaces
    assert all(interface["source_surface_emissivity"] == 0.3 for interface in foil_outer_interfaces)
    assert any(
        band["radial_sequence"][:2] == ["motor_liner", "motor_radiant_shield"]
        for band in result["radial_bands"]
    )
    assert result["scenario_index"] == 1
    fin_bond_peak = next(row for row in result["peaks"] if row["part_id"] == "fin_bonds")
    assert [row["limit_c"] for row in fin_bond_peak["temperature_limit_sensitivity"]] == [45, 65]
    assert result["prescribed_case_peak_c"] == 250
    sensitivity = run_thermal_topology(vehicle, cfg, study, False, cells=4, scenario_index=2)
    assert sensitivity["case"] == "case-300c-sensitivity"
    assert sensitivity["prescribed_case_peak_c"] == 300
    contaminated = run_thermal_topology(vehicle, cfg, study, False, cells=4, scenario_index=3)
    assert contaminated["case"] == "contaminated-foil-eps0.9"
    assert contaminated["prescribed_case_peak_c"] == 250
    assert any(
        interface["source_part_id"] == "motor_radiant_shield"
        and interface["source_surface_emissivity"] == 0.9
        for interface in contaminated["interfaces"]
    )
    assert result["thermal_acceptance_passed"] is False
    assert {row["part_id"] for row in result["prescribed_case_contact_paths"]} == {
        "thrust_pads",
        "aft_thrust_pads",
    }
    aft_pads = next(row for row in result["pad_conduction"] if row["part_id"] == "aft_thrust_pads")
    assert aft_pads["area_m2"] == pytest.approx(4.7513e-5, rel=1e-4)
    assert aft_pads["thickness_m"] == pytest.approx(0.003)
    assert aft_pads["full_path_conductance_nominal_w_k"] == pytest.approx(
        0.45 * aft_pads["area_m2"] / 0.003
    )
    assert (
        aft_pads["effective_case_half_path_conductance_w_k"]
        < aft_pads["case_interface_conductance_w_k"]
    )
    # Exact 1-D series-resistance fixture: case contact + half pad + half pad +
    # retainer contact, using the recorded three-sector CAD area and k=0.45 W/mK.
    expected_half_edge_g = 0.013305510811344625
    assert aft_pads["effective_case_half_path_conductance_w_k"] == pytest.approx(
        expected_half_edge_g, rel=1e-12
    )
    assert aft_pads["effective_structural_half_path_conductance_w_k"] == pytest.approx(
        expected_half_edge_g, rel=1e-12
    )
    expected_serial_heat_w = 100.0 / (2.0 / expected_half_edge_g)
    assert expected_serial_heat_w == pytest.approx(0.6652755405672312, rel=1e-12)
    assert {
        "retention",
        "thrust_pads",
        "aft_thrust_pads",
        "aft_retainer",
        "retention_hardware",
    } <= set(result["case_coupled_part_ids"])

    tvc = load_vehicle("configs/vehicle/platform/tvc-finned.yaml")
    cassette = next(part for part in tvc.parts if part.id == "motor_mount")
    grip = annular_intervals(cassette)
    expected_grip_start = cassette.position_m + cassette.cad.parameters["grip_start_mm"] * 1e-3
    expected_grip_end = expected_grip_start + cassette.cad.parameters["grip_length_mm"] * 1e-3
    assert grip == pytest.approx([(expected_grip_start, expected_grip_end)])
    tvc_result = run_thermal_topology(tvc, cfg, study, True, cells=4)
    assert "retention" not in tvc_result["part_ids"]
    assert not tvc_result["excluded_overlapping_annular_barriers"]
    assert {row["part_id"] for row in tvc_result["prescribed_case_contact_paths"]} == {
        "thrust_pads",
        "aft_thrust_pads",
    }
    assert any(
        band["radial_sequence"]
        == [
            "motor_liner",
            "motor_radiant_shield",
            "motor_mount",
            "gimbal_inner",
            "tvc_gimbal",
            "gimbal_frame",
            "aft_shell",
        ]
        for band in tvc_result["radial_bands"]
    )
    assert {
        "motor_mount",
        "thrust_pads",
        "aft_thrust_pads",
        "aft_retainer",
        "retention_hardware",
        "cassette_mount_screws",
    } <= set(tvc_result["case_coupled_part_ids"])


def test_topology_exports_energy_balanced_connection_histories_and_pair_override() -> None:
    import copy

    import yaml

    from src.analysis.thermal_topology import run_thermal_topology
    from src.vehicle.schema import load_vehicle

    vehicle = load_vehicle("configs/vehicle/wo02/performance-g54.yaml")
    cfg = yaml.safe_load(Path("configs/engineering/wo03.yaml").read_text())
    study = yaml.safe_load(Path("configs/studies/wo03-thermal-topology.yaml").read_text())
    baseline = run_thermal_topology(
        vehicle, cfg, study, False, cells=4, scenario_index=2, heat_flow_step_s=1.0
    )
    refined = run_thermal_topology(
        vehicle, cfg, study, False, cells=4, scenario_index=2, heat_flow_step_s=0.05
    )
    shell_peak = next(row for row in baseline["peaks"] if row["part_id"] == "aft_shell")
    refined_shell_peak = next(row for row in refined["peaks"] if row["part_id"] == "aft_shell")
    assert shell_peak["peak_c"] == pytest.approx(46.331353, abs=1e-6)
    assert refined_shell_peak["peak_c"] == pytest.approx(shell_peak["peak_c"], abs=1e-12)
    assert baseline["energy_residual_j"] < 1e-6
    assert baseline["heat_flow"]["units"] == {
        "flux": "W",
        "energy": "J",
        "temperature": "K",
        "time": "s",
    }
    assert len(baseline["heat_flow"]["times_s"]) == len(baseline["times_s"])
    lumped = next(
        edge
        for edge in baseline["heat_flow"]["connections"]
        if edge["connection"] == "lumped_contact:motor_mount->aft_shell"
    )
    assert len(lumped["flux_w_by_time"]) == len(baseline["times_s"])
    assert lumped["net_energy_j"] < 0
    assert lumped["negative_energy_j"] > abs(lumped["net_energy_j"])
    assert (
        refined["heat_flow"]["maximum_abs_node_balance_residual_fine_j"]
        < baseline["heat_flow"]["maximum_abs_node_balance_residual_fine_j"]
    )
    assert refined["heat_flow"]["maximum_abs_node_balance_residual_fine_j"] < 5.0

    overridden = copy.deepcopy(study)
    overridden["contact_pair_conductance_w_k"] = {
        "motor_mount->aft_shell": [0.03, 0.03, 0.03, 0.03]
    }
    result = run_thermal_topology(
        vehicle, cfg, overridden, False, cells=4, scenario_index=2, heat_flow_step_s=1.0
    )
    paths = result["lumped_contact_paths"]
    pair = next(
        row
        for row in paths
        if row["source_part_id"] == "motor_mount" and row["target_part_id"] == "aft_shell"
    )
    unrelated = next(
        row
        for row in paths
        if row["source_part_id"] == "aft_shell" and row["target_part_id"] == "fin_bonds"
    )
    assert pair["pair_specific_override"] is True
    assert pair["base_conductance_w_k"] == pytest.approx(0.03)
    assert unrelated["pair_specific_override"] is False
    assert unrelated["base_conductance_w_k"] == pytest.approx(study["contact_conductance_w_k"][2])


def test_pad_conduction_uses_radial_bond_gap_separate_from_cad_ring_width() -> None:
    import copy

    import yaml

    from src.analysis.thermal_topology import run_thermal_topology
    from src.vehicle.schema import load_vehicle

    vehicle = load_vehicle("configs/vehicle/wo02/performance-g54.yaml")
    cfg = yaml.safe_load(Path("configs/engineering/wo03.yaml").read_text())
    study = yaml.safe_load(Path("configs/studies/wo03-thermal-topology.yaml").read_text())
    bond = copy.deepcopy(next(part for part in vehicle.parts if part.id == "aft_thrust_pads"))
    bond.id = "synthetic_cad_ring_bond"
    bond.parent = "motor_mount"
    vehicle.parts.append(bond)
    study["part_ids"].append(bond.id)
    study["pad_conduction_part_ids"] = [bond.id]
    study["pad_conduction_thickness_m"] = {bond.id: 0.0005}

    result = run_thermal_topology(
        vehicle, cfg, study, False, cells=4, scenario_index=2, heat_flow_step_s=1.0
    )
    row = next(part for part in result["pad_conduction"] if part["part_id"] == bond.id)
    assert bond.geometry["length_m"] == pytest.approx(0.003)
    assert row["thickness_m"] == pytest.approx(0.0005)
    assert row["area_m2"] == pytest.approx(bond.cad_mass.volume_m3 / 0.0005)
    expected = row["conductivity_nominal_w_m_k"] * row["area_m2"] / 0.0005
    assert row["full_path_conductance_nominal_w_k"] == pytest.approx(expected)


def test_powered_prelaunch_soak_warms_from_ambient_and_preserves_zero_default() -> None:
    import copy

    import yaml

    from src.analysis.thermal_topology import run_thermal_topology
    from src.vehicle.schema import load_vehicle

    vehicle = load_vehicle("configs/vehicle/wo02/performance-g54.yaml")
    cfg = yaml.safe_load(Path("configs/engineering/wo03.yaml").read_text())
    cfg["thermal"]["ambient_c"][3] = 25.0
    cfg["thermal"]["external_case_peak_c"][3] = 300.0
    study = yaml.safe_load(Path("configs/studies/wo03-thermal-topology.yaml").read_text())

    default = run_thermal_topology(
        vehicle, cfg, study, False, cells=4, scenario_index=3, heat_flow_step_s=2.0
    )
    explicit_zero_study = copy.deepcopy(study)
    explicit_zero_study["prelaunch_powered_soak_s"] = 0.0
    explicit_zero = run_thermal_topology(
        vehicle,
        cfg,
        explicit_zero_study,
        False,
        cells=4,
        scenario_index=3,
        heat_flow_step_s=2.0,
    )
    assert explicit_zero["times_s"] == default["times_s"]
    assert explicit_zero["temperature_k"] == default["temperature_k"]

    warm_study = copy.deepcopy(study)
    warm_study["prelaunch_powered_soak_s"] = 600.0
    warmed = run_thermal_topology(
        vehicle,
        cfg,
        warm_study,
        False,
        cells=4,
        scenario_index=3,
        heat_flow_step_s=2.0,
    )
    warmup = warmed["prelaunch_energy_balance"]
    assert warmed["times_s"][0] == -600.0
    assert 0.0 in warmed["times_s"]
    assert warmed["times_s"][-1] == pytest.approx(vehicle.motor.burn_time_s + 300.0)
    assert warmup["start_temperature_c"] == pytest.approx(25.0)
    assert warmup["case_boundary_during_prelaunch_c"] == pytest.approx(25.0)
    assert warmup["electronics_power_w"] == pytest.approx(1.0)
    assert warmup["electronics_energy_input_j"] == pytest.approx(600.0)
    assert warmup["ignition_temperature_by_part_c"]["flight_computer"] > 25.0
    assert warmup["energy_balance_residual_j"] == pytest.approx(0.0, abs=1e-4)
    assert warmed["energy_residual_j"] < 1e-5
    assert warmed["thermal_acceptance_passed"] is False

    ignition_bound_study = copy.deepcopy(study)
    ignition_bound_study["initial_temperature_c"] = 30.0
    ignition_bound_study["initial_part_temperature_c"] = {
        "flight_computer": 40.0,
        "battery": 35.0,
        "servo_pitch": 40.0,
        "servo_yaw": 40.0,
        "servo_support": 35.0,
    }
    ignition_bound = run_thermal_topology(
        vehicle,
        cfg,
        ignition_bound_study,
        False,
        cells=4,
        scenario_index=3,
        heat_flow_step_s=2.0,
    )
    initial_parts = ignition_bound["initial_condition"]["initial_temperature_by_part_c"]
    assert initial_parts["motor_liner"] == pytest.approx(30.0)
    assert initial_parts["aft_shell"] == pytest.approx(30.0)
    assert initial_parts["flight_computer"] == pytest.approx(40.0)
    assert initial_parts["battery"] == pytest.approx(35.0)
    assert ignition_bound["initial_condition"]["requested_part_overrides_c"][
        "servo_pitch"
    ] == pytest.approx(40.0)
    assert ignition_bound["initial_condition"]["overrides_not_present_in_vehicle"] == [
        "servo_pitch",
        "servo_support",
        "servo_yaw",
    ]
    assert ignition_bound["prelaunch_powered_soak_s"] == 0.0
    assert ignition_bound["times_s"][0] == 0.0
    assert ignition_bound["energy_residual_j"] < 1e-5
