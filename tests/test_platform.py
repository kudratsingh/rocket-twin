"""Modular geometry, staged gates and launch/control screening regressions."""

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import yaml
from pydantic import ValidationError

from src.vehicle.aero import center_of_pressure
from src.vehicle.benchmark import evaluate_preliminary, screen_launch
from src.vehicle.geometry import shape_properties
from src.vehicle.mass import mass_properties
from src.vehicle.schema import Vehicle, load_vehicle

ROOT = Path("configs/vehicle/platform")


def test_rail_mass_budget_uses_same_solver_and_preserves_allowance() -> None:
    vehicle = load_vehicle(ROOT / "tvc-finned.yaml")
    nominal = mass_properties(vehicle).mass_kg
    actual = screen_launch(vehicle)
    study = screen_launch(vehicle, study_nominal_mass_kg=nominal)
    assert study == actual
    heavier = screen_launch(vehicle, study_nominal_mass_kg=nominal + 0.02)
    assert heavier["worst_case_mass_kg"] == pytest.approx(
        nominal + 0.02 + vehicle.design.mass_allowance_kg
    )
    assert heavier["rail_exit_speed_mps"] < actual["rail_exit_speed_mps"]
    assert mass_properties(vehicle).mass_kg == nominal
    with pytest.raises(ValueError, match="finite and positive"):
        screen_launch(vehicle, study_nominal_mass_kg=float("nan"))


def test_common_assembly_and_actual_mode_geometry() -> None:
    vehicles = [
        load_vehicle(ROOT / name)
        for name in ["performance.yaml", "tvc-finned.yaml", "tvc-finless.yaml"]
    ]
    ids = {p["id"] for p in yaml.safe_load((ROOT / "common-upper.yaml").read_text())["parts"]}
    common = [{p.id: p.model_dump() for p in v.parts if p.id in ids} for v in vehicles]
    assert common[0] == common[1] == common[2]
    assert [sum(p.type == "fin_set" for p in v.parts) for v in vehicles] == [1, 1, 0]
    assert vehicles[0].tvc is None and vehicles[1].tvc and vehicles[2].tvc
    assert center_of_pressure(vehicles[2]) < mass_properties(vehicles[2]).cg_m
    assert mass_properties(vehicles[1]).mass_kg > mass_properties(vehicles[2]).mass_kg
    # Fin removal changes mass, inertia and CP together; no aero-only switch.
    assert not np.allclose(
        mass_properties(vehicles[1]).inertia_kg_m2, mass_properties(vehicles[2]).inertia_kg_m2
    )


@pytest.mark.parametrize("name", ["performance.yaml", "tvc-finned.yaml", "tvc-finless.yaml"])
def test_preliminary_reference_and_mode_requirements(name: str) -> None:
    pytest.importorskip("rocketpy")
    vehicle = load_vehicle(ROOT / name)
    result = evaluate_preliminary(vehicle, compare=True)
    assert result["preliminary_design_benchmark_passed"], result["checks"]
    assert result["flight_ready"] is False
    if vehicle.design and vehicle.design.mode == "performance":
        assert vehicle.motor and vehicle.motor.burn_time_s < 3  # superseded universal gate
    else:
        assert result["average_TWR_diagnostic_only"] < 3  # time/rail gates apply instead
        assert vehicle.design
        interval = result["launch_screen"]["longest_useful_control_interval_s"]
        assert interval >= vehicle.design.minimum_control_time_s
        assert result["launch_screen"]["control_time_target_met"] == (
            interval >= vehicle.design.target_control_time_s
        )


def test_fin_plate_radial_inertia_against_rectangle() -> None:
    # Equally spaced rectangular plates: analytic mean radius squared catches
    # the old coaxial-box approximation omitting radial fin mass distribution.
    g = {
        "count": 3,
        "span_m": 0.1,
        "root_chord_m": 0.2,
        "tip_chord_m": 0.2,
        "sweep_m": 0,
        "thickness_m": 0.002,
        "radius_m": 0.03,
        "length_m": 0.2,
    }
    shape = shape_properties("fin_set", g)
    expected_axial = 0.03**2 + 0.03 * 0.1 + 0.1**2 / 3 + 0.002**2 / 12
    assert shape.cg_offset_m == pytest.approx(0.1)
    assert shape.volume_m3 == pytest.approx(3 * 0.1 * 0.2 * 0.002)
    assert shape.inertia_per_kg_m2[0, 0] == pytest.approx(expected_axial)
    assert shape.inertia_per_kg_m2[1, 1] == pytest.approx(0.2**2 / 12 + expected_axial / 2)


def test_long_burn_cannot_substitute_for_useful_control(tmp_path: Path) -> None:
    vehicle = load_vehicle(ROOT / "tvc-finless.yaml")
    source = tmp_path / "weak.eng"
    # Brief launch pulse followed by a long sustainer below weight.
    source.write_text("SYNTHETIC 29 156 P .082 .150 TEST\n.01 40\n.5 40\n.6 1\n12 1\n12.1 0\n")
    assert vehicle.motor is not None
    vehicle.motor.curve = str(source)
    result = screen_launch(vehicle)
    assert not result["control_time_screen_pass"]
    assert result["longest_useful_control_interval_s"] < 2
    with pytest.raises(ValueError):
        screen_launch(vehicle, dt=float("nan"))


def test_bad_modes_and_high_power_rejected() -> None:
    original = load_vehicle(ROOT / "tvc-finned.yaml").model_dump(by_alias=True)
    for defect in [
        "fins_double_counted",
        "finless_contains_fins",
        "high_thrust",
        "high_impulse",
        "growth_cap",
        "lower_declared_cap",
    ]:
        data = deepcopy(original)
        if defect == "fins_double_counted":
            data["aero"]["passive_stubs"]["enabled"] = True
        elif defect == "finless_contains_fins":
            data["design"]["mode"] = "tvc_finless"
        elif defect == "high_thrust":
            data["motor"]["qualification"]["certified_average_thrust_n"] = 80.1
        elif defect == "high_impulse":
            data["motor"]["qualification"]["certified_impulse_ns"] = 160.1
        elif defect == "lower_declared_cap":
            data["limits"]["max_liftoff_mass_kg"] = 0.5
        else:
            data["design"]["mass_allowance_kg"] = 1
        with pytest.raises(ValidationError):
            Vehicle.model_validate(data)


def test_curve_tamper_or_config_disagreement_fails(tmp_path: Path) -> None:
    vehicle = load_vehicle(ROOT / "performance.yaml")
    assert vehicle.motor and vehicle.motor.curve
    path = Path(vehicle.motor.curve)
    target = tmp_path / path.name
    target.write_bytes(path.read_bytes() + b"\n; tamper\n")
    target.with_suffix(".yaml").write_bytes(path.with_suffix(".yaml").read_bytes())
    vehicle.motor.curve = str(target)
    result = evaluate_preliminary(vehicle)
    assert not result["checks"]["source_traceable_and_config_consistent"]
    assert not result["preliminary_design_benchmark_passed"]


def test_offset_servo_pair_has_roll_inertia_and_cross_moment() -> None:
    vehicle = load_vehicle(ROOT / "tvc-finned.yaml")
    # Independent symmetric two-part fixture isolates the parallel-axis theorem
    # from the current CAD packaging, which intentionally has lateral CG offsets.
    servos = [p.model_copy(deep=True) for p in vehicle.parts if p.type == "servo"]
    for part, station, offset in zip(servos, [0.56, 0.60], [0.022, -0.022]):
        part.position_m = station
        part.lateral_offset_m = (offset, 0)
        part.cad_mass = None
        part.mass_kg = 0.014
    fixture = vehicle.model_copy(update={"parts": servos, "motor": None})
    actual = mass_properties(fixture)
    centered = fixture.model_copy(deep=True)
    for part in centered.parts:
        part.lateral_offset_m = (0, 0)
    difference = actual.inertia_kg_m2 - mass_properties(centered).inertia_kg_m2
    radial = 2 * 0.014 * 0.022**2
    cross = 0.014 * 0.022 * (0.56 - 0.60)
    assert actual.cg_lateral_m == pytest.approx((0, 0))
    assert difference == pytest.approx(
        np.array([[radial, cross, 0], [cross, 0, 0], [0, 0, radial]]), abs=1e-14
    )
