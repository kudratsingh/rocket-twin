"""Independent actual-mode trajectory check; calm comparison is not wind validation."""

from pathlib import Path

import jax
import numpy as np
import pytest

from src.sim import env
from src.sim.inputs import prepare
from src.sim.reference import reference_flight
from src.vehicle.schema import load_vehicle


@pytest.mark.parametrize("name", ["performance.yaml", "tvc-finned.yaml"])
def test_actual_configuration_apogee_and_time_against_rocketpy(name: str) -> None:
    vehicle = load_vehicle(Path("configs/vehicle/platform") / name)
    case = {"dt_s": 0.005, "sensor_noise": False}
    p = prepare(vehicle, case)
    final, rows = env.rollout(p, jax.random.PRNGKey(0), steps=5000)
    data = np.asarray(rows)
    i = int(np.argmax(-data[:, 3]))
    reference = reference_flight(vehicle, case)
    assert abs(-data[i, 3] / reference["apogee_agl_m"] - 1) < 0.05
    assert abs(data[i, 0] / reference["apogee_time_s"] - 1) < 0.05
    assert float(final.rail_exit_time) > 0 and np.isfinite(data).all()
    # Real component placement permits lateral drift even in calm air.
    assert vehicle.recovery
    assert float(p.recovery[0]) == pytest.approx(
        np.pi * (vehicle.recovery.canopy_diameter_m / 2) ** 2 * vehicle.recovery.drag_coefficient
    )
