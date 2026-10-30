"""Sampled IMU/barometer observations with bias, noise, transport delay and lag.

Accelerometers measure body specific force R^T*(a-g), including rail reactions.
Gyros measure body rate; barometer observes height with a first-order pneumatic lag.
Noise is zero-mean Gaussian; biases are drawn once per reset. Sensor output is held
between sample instants, with deterministic PRNG keys supplied by the caller.
Rates/ranges come from the spec; noise/latency are labelled engineering estimates.
No truth attitude is included in the observation: WO-06 adds the estimator.
References: Titterton & Weston, Strapdown Inertial Navigation Technology, ch. 3;
ICM-42688/BMP390 datasheets are the later calibration sources.
"""

import jax
import jax.numpy as jnp
from jax import Array

from src.sim.types import Params, State


def observe(state: State, specific: Array, p: Params, key: Array) -> tuple[Array, Array, Array]:
    accel_noise, gyro_noise, baro_noise, tau, imu_hz, baro_hz, latency, accel_limit, gyro_limit = (
        p.sensors[:9]
    )
    dt = p.launch[3]
    queue = jnp.concatenate(
        (jnp.concatenate((specific, state.rigid[10:13], specific))[None, :], state.imu_queue[:-1]),
        axis=0,
    )
    delayed = queue[jnp.clip(jnp.rint(latency / dt).astype(int), 0, queue.shape[0] - 1)]
    noise = jax.random.normal(key, (10,))
    imu = (
        delayed[:6]
        + state.sensor_bias[:6]
        + jnp.concatenate((jnp.full(3, accel_noise), jnp.full(3, gyro_noise))) * noise[:6]
    )
    limits = jnp.concatenate((jnp.full(3, accel_limit), jnp.full(3, gyro_limit)))
    imu = jnp.clip(imu, -limits, limits)
    tick = jnp.rint(state.time / dt).astype(int)
    imu_period = jnp.maximum(1, jnp.rint(1 / (dt * imu_hz)).astype(int))
    baro_period = jnp.maximum(1, jnp.rint(1 / (dt * baro_hz)).astype(int))
    filtered = state.baro_filtered + (1 - jnp.exp(-dt / jnp.maximum(tau, dt))) * (
        -state.rigid[2] - state.baro_filtered
    )
    reading = jnp.where(tick % imu_period == 0, imu, state.observation[:6])
    baro = jnp.where(
        tick % baro_period == 0, filtered + baro_noise * noise[6], state.observation[6]
    )
    high_g = queue[jnp.clip(jnp.rint(p.sensors[13] / dt).astype(int), 0, queue.shape[0] - 1), 6:9]
    high_g = jnp.clip(
        high_g + state.sensor_bias[6:9] + p.sensors[12] * noise[7:10], -p.sensors[10], p.sensors[10]
    )
    high_period = jnp.maximum(1, jnp.rint(1 / (dt * p.sensors[11])).astype(int))
    high_g = jnp.where(tick % high_period == 0, high_g, state.observation[10:13])
    obs = jnp.concatenate((reading, jnp.array([baro, state.time]), state.servo[:2], high_g))
    return obs, queue, filtered
