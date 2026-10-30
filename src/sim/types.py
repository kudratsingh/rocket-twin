"""Fixed-shape JAX pytrees for one shared experiment/RL physics path.

State uses world NED position/velocity, scalar-first body-to-world quaternion,
and body angular rates; axial stations increase aft in the source specification.
Parameters carry numerical hypotheses, never motor names or hidden geometry toggles.
Array shapes are fixed across motor/configuration variants for jit/vmap reuse.
References: Zipfel, Modeling and Simulation of Aerospace Vehicle Dynamics, ch. 4–6;
JAX pytree documentation. Host-side source and configuration validation is separate.
No policy or estimator is implemented in WO-02.
"""

from typing import NamedTuple

from jax import Array


class Params(NamedTuple):
    times: Array
    thrust: Array
    impulse: Array
    motor: Array  # burn_s, prop_kg, thrust_scale, time_scale, ignition_s
    mass0: Array
    moment0: Array
    inertia_origin: Array
    prop_origin_inertia: Array
    prop_position: Array
    aero: Array  # area, diameter, base_cd, drag_scale
    mach: Array
    cd: Array
    surfaces: Array  # [slope, station] padded rows
    launch: Array  # usable rail, friction, site elevation, dt
    rail_direction: Array
    wind: Array  # north, east, gust_sigma, period, power exponent
    recovery: Array  # cd_area, trigger lag, inflation_s, enabled
    servo: Array  # max_angle, rate, omega_n, zeta, latency, deadband, stall
    sensors: Array  # accel_noise, gyro_noise, baro_noise, baro_tau, imu_hz, baro_hz, latency
    pivot_station: Array


class State(NamedTuple):
    time: Array
    rigid: Array  # NED position 3, velocity 3, quaternion 4, omega 3
    servo: Array  # angle 2, rate 2
    commands: Array  # 64 x 2 latency buffer
    imu_queue: Array  # 16 x 9 latency buffer
    sensor_bias: Array
    observation: (
        Array  # body specific force 3, gyro 3, baro height, time, gimbal 2, high-g specific force 3
    )
    baro_filtered: Array
    rail_exit_time: Array  # -1 until departure
    rail_exit_speed: Array
    recovery_time: Array  # -1 until apogee trigger
    launched: Array
    landed: Array
