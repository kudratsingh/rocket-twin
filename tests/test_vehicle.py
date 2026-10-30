"""CPU smoke plus checks for mass accounting and rejected invalid assemblies."""

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import yaml
from pydantic import ValidationError

from src.vehicle.aero import center_of_pressure, drag_coefficient
from src.vehicle.mass import mass_properties
from src.vehicle.schema import Vehicle, load_vehicle

SPEC = Path("configs/vehicle/tvc-ascent-v1.yaml")


def test_vehicle_cpu_smoke() -> None:
    vehicle = load_vehicle(SPEC)
    start, end = mass_properties(vehicle), mass_properties(vehicle, 1)
    assert vehicle.motor is not None
    assert start.mass_kg - end.mass_kg == pytest.approx(vehicle.motor.propellant_mass_kg)
    # Independently remove propellant's first moment, catching double-counted motors.
    motor = next(p for p in vehicle.parts if p.type == "motor")
    expected = (
        start.mass_kg * start.cg_m - vehicle.motor.propellant_mass_kg * (motor.cg_station_m)
    ) / end.mass_kg
    assert end.cg_m == pytest.approx(expected)
    assert np.linalg.eigvalsh(start.inertia_kg_m2).min() > 0
    assert np.allclose(start.inertia_kg_m2, np.diag(np.diag(start.inertia_kg_m2)))
    assert center_of_pressure(vehicle) == pytest.approx(0.07323213814938)
    assert drag_coefficient(vehicle, 0.3) > drag_coefficient(vehicle, 0.3, powered=True)
    with pytest.raises(ValueError):
        mass_properties(vehicle, 1.1)
    with pytest.raises(ValueError):
        drag_coefficient(vehicle, 1.2)


@pytest.mark.parametrize(
    "defect",
    [
        "cycle",
        "duplicate",
        "net",
        "overweight",
        "propellant",
        "metal",
        "evidence",
        "bounds",
        "motor_mass",
        "limit",
        "nan_geometry",
        "negative_rate",
        "bad_drag_table",
        "duplicate_servo",
        "negative_rating",
    ],
)
def test_invalid_spec_is_rejected(defect: str) -> None:
    data = deepcopy(yaml.safe_load(SPEC.read_text()))
    if defect == "cycle":
        data["parts"][0]["parent"] = data["parts"][1]["id"]
    elif defect == "duplicate":
        data["parts"][1]["id"] = data["parts"][0]["id"]
    elif defect == "net":
        data["netlist"][0]["to"] = "missing_regulator"
    elif defect == "overweight":
        data["parts"][0]["mass_kg"] = 2
    elif defect == "propellant":
        data["motor"]["propellant_mass_kg"] = 0.126
    elif defect == "metal":
        data["parts"][0]["material"] = "aluminium"
    elif defect == "evidence":
        data["parts"][0]["estimate"] = False
    elif defect == "bounds":
        data["parts"][0]["position_m"] = 0.69
    elif defect == "motor_mass":
        data["motor"]["casing_mass_kg"] = 0.1
    elif defect == "nan_geometry":
        data["parts"][0]["geometry"]["radius_m"] = float("nan")
    elif defect == "negative_rate":
        data["avionics"]["loop_rate_hz"] = -1
    elif defect == "bad_drag_table":
        data["aero"]["cd_model"]["mach"] = [0, 0.3, 0.2, 0.8]
    elif defect == "duplicate_servo":
        data["tvc"]["servo_ids"] = ["servo_pitch", "servo_pitch"]
    elif defect == "negative_rating":
        data["parts"][3]["electrical"]["supply_v"] = -5
    else:
        data["limits"]["max_liftoff_mass_kg"] = 3
    with pytest.raises(ValidationError):
        Vehicle.model_validate(data)
