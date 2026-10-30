"""Quasi-steady subsonic aerodynamic forces from actual WO-01 surfaces.

Each surface sees v_rel + omega cross r; linear normal force opposes transverse
relative flow. Its lever arm supplies restoring and pitch/yaw damping moments.
This retains physical fin locations, unlike a global stability flag.
Axial drag uses the spec's Mach table and distinct powered/coast base drag.
Small-angle validity and Mach<=0.8 are reported by the host, not hidden by a pass.
No CFD, flutter, transonic extrapolation or measured derivative claim is made.
References: Barrowman 1967; Mandell et al., Topics in Advanced Model Rocketry.
Extension contract: AeroModel; replace calibrated surface derivatives here later.
"""

import jax.numpy as jnp
from jax import Array

from src.sim.types import Params


def forces(
    relative_body: Array,
    omega: Array,
    cg: Array,
    rho: Array,
    sound: Array,
    powered: Array,
    p: Params,
) -> tuple[Array, Array, Array, Array]:
    speed = jnp.linalg.norm(relative_body)
    mach = speed / sound
    cd = jnp.interp(mach, p.mach, p.cd) + (1 - powered) * p.aero[2]
    axial = -0.5 * rho * speed**2 * p.aero[0] * cd * p.aero[3] * jnp.sign(relative_body[0])
    arms = jnp.stack(
        (-p.surfaces[:, 1] - cg[0], jnp.zeros(p.surfaces.shape[0]), jnp.zeros(p.surfaces.shape[0])),
        axis=1,
    )
    local = relative_body + jnp.cross(omega, arms)
    normals = (
        -0.5
        * rho
        * p.aero[0]
        * p.surfaces[:, 0, None]
        * jnp.linalg.norm(local, axis=1)[:, None]
        * local
    )
    normals = normals.at[:, 0].set(0)
    force = jnp.array([axial, 0, 0]) + jnp.sum(normals, axis=0)
    torque = jnp.sum(jnp.cross(arms, normals), axis=0)
    alpha = jnp.arctan2(jnp.linalg.norm(relative_body[1:]), jnp.maximum(relative_body[0], 1e-9))
    return force, torque, mach, alpha
