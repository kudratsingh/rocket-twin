"""Resolve a complete vehicle into fixed-shape JAX parameters and provenance.

Only this host boundary reads YAML, source files and WO-01 part geometry.
Growth mass is an explicit point-mass sensitivity at a specified station, never
an unexplained scalar multiplier on nominal hardware. Source arrays are padded
with zeros after burnout; original breakpoints/impulse remain unchanged.
References: ADR-0002; Goldstein parallel-axis theorem; Barrowman 1967.
Unknown hardware properties remain estimates and are not inferred from a fit.
"""

import hashlib
from pathlib import Path
from typing import Any

import jax.numpy as jnp
import numpy as np
import yaml

from src.sim.types import Params
from src.vehicle.aero import normal_force_surfaces
from src.vehicle.mass import mass_properties
from src.vehicle.motors import load_rasp
from src.vehicle.schema import Vehicle


def prepare(vehicle: Vehicle, case: dict[str, Any]) -> Params:
    if not vehicle.motor or not vehicle.motor.curve or not vehicle.design:
        raise ValueError("flight requires a complete physical mode and source curve")
    model_path = Path(case.get("model_config", "configs/sim-model.yaml"))
    estimates = yaml.safe_load(model_path.read_text())
    actuator_model = estimates["servo"]
    sensor_model = estimates["sensors"]
    dt = float(case.get("dt_s", 0.005))
    if not 0.001 <= dt <= 0.01:
        raise ValueError("physics dt must be in [0.001, 0.01] seconds")
    curve_path = Path(vehicle.motor.curve)
    metadata = yaml.safe_load(curve_path.with_suffix(".yaml").read_text())
    if (
        metadata.get("review_status") != "preliminary_numerical_hypothesis"
        or metadata.get("sha256") != hashlib.sha256(curve_path.read_bytes()).hexdigest()
    ):
        raise ValueError(
            "flight requires a reviewed numerical source hypothesis; quarantined/tampered data refused"
        )
    curve = load_rasp(curve_path)
    for key in ("thrust_scale", "drag_scale", "time_scale"):
        if float(case.get(key, 1)) <= 0:
            raise ValueError("flight scales must be positive")
    if float(case.get("rail_friction_n", 0)) < 0:
        raise ValueError("guide friction must be nonnegative")
    if len(curve.samples) > 128:
        raise ValueError("curve exceeds fixed input size; increase bound explicitly")
    expected = [
        vehicle.motor.propellant_mass_kg + vehicle.motor.casing_mass_kg,
        vehicle.motor.propellant_mass_kg,
    ]
    if not np.allclose(expected, [curve.loaded_mass_kg, curve.propellant_mass_kg]):
        raise ValueError("configured motor masses disagree with source hypothesis")
    points = curve.samples
    times = np.concatenate((points[:, 0], curve.burn_time_s + np.arange(1, 129 - len(points))))
    forces = np.pad(points[:, 1], (0, 128 - len(points)))
    impulse = np.concatenate(([0.0], np.cumsum(np.diff(times) * (forces[1:] + forces[:-1]) / 2)))
    own = mass_properties(vehicle)
    cg = np.array([-own.cg_m, *own.cg_lateral_m])

    def cross(r: Any) -> Any:
        return np.dot(r, r) * np.eye(3) - np.outer(r, r)

    origin = own.inertia_kg_m2 + own.mass_kg * cross(cg)
    growth = float(case.get("added_mass_kg", 0))
    station = float(case.get("added_mass_station_m", vehicle.airframe["length_m"]))
    if growth < 0 or own.mass_kg + growth >= 1.5:
        raise ValueError("invalid growth mass or loaded scope cap")
    moment = own.mass_kg * cg + growth * np.array([-station, 0, 0])
    origin += growth * cross(np.array([-station, 0, 0]))
    part = next(p for p in vehicle.parts if p.type == "motor")
    if not np.allclose(
        [part.geometry["length_m"], 2 * part.geometry["radius_m"]],
        [curve.length_m, curve.diameter_m],
    ):
        raise ValueError("motor installed dimensions disagree with source hypothesis")
    prop_position = np.array([-part.cg_station_m, *part.cg_lateral_m])
    prop_inertia = part.inertia_per_kg_m2 + cross(prop_position)
    surfaces = np.array(normal_force_surfaces(vehicle))
    if len(surfaces) > 8:
        raise ValueError("surface count exceeds explicit bound")
    surfaces = np.pad(surfaces, ((0, 8 - len(surfaces)), (0, 0)))
    tilt = np.deg2rad(float(case.get("rail_tilt_deg", 0)))
    heading = np.deg2rad(float(case.get("heading_deg", 0)))
    direction = np.array(
        [np.sin(tilt) * np.cos(heading), np.sin(tilt) * np.sin(heading), -np.cos(tilt)]
    )
    servo = next((p for p in vehicle.parts if p.type == "servo"), None)
    actuator = [
        0,
        1,
        actuator_model["natural_frequency_rad_s"],
        actuator_model["damping_ratio"],
        actuator_model["latency_s"],
        0,
        0,
    ]
    if servo and servo.electrical and vehicle.tvc:
        assert servo.electrical.speed_s_per_60deg is not None
        assert servo.electrical.deadband_us is not None
        actuator = [
            vehicle.tvc.max_deflection_rad,
            np.pi / 3 / servo.electrical.speed_s_per_60deg * vehicle.tvc.linkage_ratio,
            actuator_model["natural_frequency_rad_s"],
            actuator_model["damping_ratio"],
            actuator_model["latency_s"],
            servo.electrical.deadband_us * np.pi / 2000 * vehicle.tvc.linkage_ratio,
            0,
        ]
    noise = bool(case.get("sensor_noise", True))
    model = vehicle.aero.cd_model
    if vehicle.recovery is None:
        raise ValueError("flight model requires explicit recovery parameters")
    recovery = vehicle.recovery
    depletion_mass = float(case.get("depletion_mass_kg", curve.propellant_mass_kg))
    if not 0 < depletion_mass < curve.loaded_mass_kg:
        raise ValueError("invalid propellant-depletion hypothesis")
    recovery_area = (
        np.pi
        * (float(case.get("canopy_diameter_m", recovery.canopy_diameter_m)) / 2) ** 2
        * float(case.get("canopy_cd", recovery.drag_coefficient))
    )
    if vehicle.avionics is None:
        raise ValueError("flight model requires sensor ratings")
    imu_rating = vehicle.avionics.sensors["imu"]
    if imu_rating.accel_range_g is None or imu_rating.gyro_range_dps is None:
        raise ValueError("IMU ranges are required")
    high_g = vehicle.avionics.sensors.get("high_g")
    values = {
        "times": times,
        "thrust": forces,
        "impulse": impulse,
        "motor": [
            curve.burn_time_s,
            depletion_mass,
            float(case.get("thrust_scale", 1)),
            float(case.get("time_scale", 1)),
            float(case.get("ignition_s", 0)),
        ],
        "mass0": own.mass_kg + growth,
        "moment0": moment,
        "inertia_origin": origin,
        "prop_origin_inertia": prop_inertia,
        "prop_position": prop_position,
        "aero": [
            np.pi * (vehicle.airframe["body_diameter_m"] / 2) ** 2,
            vehicle.airframe["body_diameter_m"],
            model.base_drag_cd,
            float(case.get("drag_scale", 1)),
        ],
        "mach": model.mach,
        "cd": model.cd,
        "surfaces": surfaces,
        "launch": [
            float(case.get("usable_rail_m", vehicle.design.rail_length_m)),
            float(case.get("rail_friction_n", 0)),
            float(case.get("elevation_m", 850)),
            dt,
        ],
        "rail_direction": direction,
        "wind": [
            float(case.get("wind_north_mps", 0)),
            float(case.get("wind_east_mps", 0)),
            float(case.get("gust_amplitude_mps", 0)),
            estimates["wind"]["gust_period_s"],
            float(case.get("wind_power_exponent", 0)),
        ],
        "recovery": [
            recovery_area,
            float(case.get("recovery_lag_s", recovery.trigger_lag_s)),
            float(case.get("inflation_s", recovery.inflation_s)),
            float(case.get("recovery_enabled", True)),
        ],
        "servo": actuator,
        "sensors": [
            sensor_model["accelerometer_noise_mps2"] * noise,
            sensor_model["gyro_noise_rad_s"] * noise,
            sensor_model["barometer_noise_m"] * noise,
            sensor_model["barometer_time_constant_s"],
            imu_rating.rate_hz,
            vehicle.avionics.sensors["baro"].rate_hz,
            sensor_model["imu_latency_s"],
            imu_rating.accel_range_g * 9.80665,
            np.deg2rad(imu_rating.gyro_range_dps),
            sensor_model["reset_bias_sigma_fraction"],
            (high_g.accel_range_g or 0) * 9.80665 if high_g else 0,
            high_g.rate_hz if high_g else 1,
            sensor_model.get("high_g_noise_mps2", 0.981) * noise,
            sensor_model.get("high_g_latency_s", 0.002),
        ],
        "pivot_station": vehicle.tvc.pivot_position_m if vehicle.tvc else part.cg_station_m,
    }
    if any(not np.isfinite(v).all() for v in map(np.asarray, values.values())):
        raise ValueError("nonfinite physical input")
    return Params(**{name: jnp.asarray(value, dtype=jnp.float64) for name, value in values.items()})


def source_hashes(vehicle: Vehicle) -> dict[str, str]:
    assert vehicle.motor and vehicle.motor.curve
    path = Path(vehicle.motor.curve)
    return {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (path, path.with_suffix(".yaml"), Path("configs/sim-model.yaml"))
    }
