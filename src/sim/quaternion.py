"""Scalar-first quaternion algebra, body to world (the conventions in frames.py).

qdot = 0.5*q ⊗ [0,omega_body]; R maps body vectors into NED world vectors.
The initial launch attitude is constructed on the host, not guessed in the core.
Each accepted integration step normalizes q to suppress numerical norm drift.
Reference: Zipfel, Modeling and Simulation of Aerospace Vehicle Dynamics, ch. 4.
No Euler-angle integration and no duplicated NED/ECI definition are introduced.
"""

import jax.numpy as jnp
from jax import Array


def multiply(a: Array, b: Array) -> Array:
    return jnp.concatenate(
        (
            jnp.array([a[0] * b[0] - jnp.dot(a[1:], b[1:])]),
            a[0] * b[1:] + b[0] * a[1:] + jnp.cross(a[1:], b[1:]),
        )
    )


def rotation(q: Array) -> Array:
    q = q / jnp.maximum(jnp.linalg.norm(q), 1e-12)
    w, x, y, z = q
    return jnp.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )
