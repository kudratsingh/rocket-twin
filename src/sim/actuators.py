"""Second-order servo with transport delay, speed/position limits and deadband.

angle_ddot=wn^2*(command-angle)-2*zeta*wn*angle_dot, integrated semi-implicitly.
A fixed buffer implements latency at the physics timestep; commands are held by
control-loop decimation in the experiment driver. Stall freezes the mechanism.
Rate is derived from the YAML seconds-per-60-degrees value, not an ideal actuator.
Torque/current under thrust load and backlash are unmeasured WO-03/06/09 gates.
The current model must not be used to certify servo load capability.
Reference: Ogata, Modern Control Engineering, second-order systems and delay.
"""

import jax.numpy as jnp
from jax import Array

from src.sim.types import Params


def advance(servo: Array, queue: Array, command: Array, p: Params) -> tuple[Array, Array]:
    limit, rate, wn, zeta, latency, deadband, stall = p.servo
    dt = p.launch[3]
    queue = jnp.concatenate((jnp.clip(command, -limit, limit)[None, :], queue[:-1]), axis=0)
    delayed = queue[jnp.clip(jnp.rint(latency / dt).astype(int), 0, queue.shape[0] - 1)]
    error = delayed - servo[:2]
    error = jnp.where(jnp.abs(error) < deadband, 0, error)
    velocity = jnp.clip(servo[2:] + dt * (wn**2 * error - 2 * zeta * wn * servo[2:]), -rate, rate)
    angle = jnp.clip(servo[:2] + dt * velocity, -limit, limit)
    velocity = jnp.where(jnp.abs(angle) >= limit, 0, velocity)
    out = jnp.concatenate((angle, velocity))
    return jnp.where(stall > 0, jnp.concatenate((servo[:2], jnp.zeros(2))), out), queue
