"""Independent solutions and opaque wall/gap energy balance, not rocket qualification."""

from pathlib import Path

import numpy as np

from src.analysis.thermal_radial import annular_wall, known_cases, opaque_gap_flux, wall_heat_rates


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


def test_actual_open_frame_is_not_an_opaque_full_length_tube() -> None:
    import yaml

    from src.analysis.thermal_topology import annular_intervals, run_thermal_topology
    from src.vehicle.schema import load_vehicle

    vehicle = load_vehicle("configs/vehicle/platform/performance.yaml")
    frame = next(part for part in vehicle.parts if part.id == "motor_mount")
    intervals = annular_intervals(frame)
    assert len(intervals) == 2
    assert abs(sum(b - a for a, b in intervals) - 0.006) < 1e-12
    midpoint = frame.position_m + frame.geometry["length_m"] / 2
    assert not any(a <= midpoint <= b for a, b in intervals)
    cfg = yaml.safe_load(Path("configs/engineering/wo03.yaml").read_text())
    study = yaml.safe_load(Path("configs/studies/wo03-thermal-topology.yaml").read_text())
    result = run_thermal_topology(vehicle, cfg, study, True, cells=4)
    assert result["energy_residual_j"] < 1e-6
    assert any(b["radial_sequence"] == ["motor_liner", "aft_shell"] for b in result["radial_bands"])
    assert result["thermal_acceptance_passed"] is False
