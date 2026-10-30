"""Two-axis thrust rotation at the specified gimbal pivot.

Angles rotate thrust about body +y then +z; +pitch gives negative body-z force.
With a pivot aft of CG, positive thrust-vector pitch gives negative pitch moment.
This sign is intentional, explicit and checked before any controller is written.
Fixed motors have zero permitted angle; motor hardware is included in mass once.
Small-angle gimbal moving-CG/inertia changes remain a later multibody extension.
Reference: rigid-body moment tau = r cross F, Goldstein, ch. 5.
No throttle is exposed for a commercial solid motor.
"""

import jax.numpy as jnp
from jax import Array


def thrust_force_moment(
    thrust: Array, angles: Array, cg: Array, pivot: Array
) -> tuple[Array, Array]:
    pitch, yaw = angles
    force = thrust * jnp.array(
        [jnp.cos(pitch) * jnp.cos(yaw), jnp.cos(pitch) * jnp.sin(yaw), -jnp.sin(pitch)]
    )
    arm = jnp.array([-pivot, 0, 0]) - cg
    return force, jnp.cross(arm, force)
