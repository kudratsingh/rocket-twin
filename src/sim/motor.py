"""Piecewise-linear commercial thrust, exact segment impulse and mass moments.

Thrust scale changes impulse; time scale changes burn duration and impulse.
Depletion follows normalized cumulative impulse, not elapsed burn time.
Uniform grain depletion inherits WO-01's unmeasured fixed-grain-CG assumption.
An analytic origin-inertia/parallel-axis update handles moving vehicle CG.
Idot is included in Euler's angular momentum equation; detailed exhaust flux,
grain regression and nozzle jet damping are not resolved in this first model.
References: Sutton & Biblarz, Rocket Propulsion Elements, ch. 4;
Goldstein, Classical Mechanics, ch. 5. All motor source identities remain on the host.
"""

import jax.numpy as jnp
from jax import Array

from src.sim.types import Params


def motor_values(t: Array, p: Params) -> tuple[Array, Array, Array]:
    burn, prop, scale, timing, ignition = p.motor
    u = jnp.clip((t - ignition) / timing, 0, burn)
    i = jnp.clip(jnp.searchsorted(p.times, u, side="right") - 1, 0, p.times.size - 2)
    a, b = p.times[i], p.times[i + 1]
    f0, f1 = p.thrust[i], p.thrust[i + 1]
    width = jnp.maximum(b - a, 1e-12)
    dt = u - a
    integral = p.impulse[i] + f0 * dt + 0.5 * (f1 - f0) / width * dt**2
    fraction = jnp.clip(integral / p.impulse[-1], 0, 1)
    active = (t >= ignition) & (t < ignition + burn * timing)
    thrust = jnp.where(active, (f0 + (f1 - f0) * dt / width) * scale, 0)
    mdot = jnp.where(active, -prop * (f0 + (f1 - f0) * dt / width) / p.impulse[-1] / timing, 0)
    return thrust, fraction, mdot


def cross_inertia(r: Array) -> Array:
    return jnp.dot(r, r) * jnp.eye(3) - jnp.outer(r, r)


def properties(t: Array, p: Params) -> tuple[Array, Array, Array, Array]:
    _, fraction, mdot = motor_values(t, p)
    removed = p.motor[1] * fraction
    mass = p.mass0 - removed
    cg = (p.moment0 - removed * p.prop_position) / mass
    cgdot = mdot * (p.prop_position - cg) / mass
    inertia = p.inertia_origin - removed * p.prop_origin_inertia - mass * cross_inertia(cg)
    derivative = mdot * (p.prop_origin_inertia - cross_inertia(cg)) - mass * (
        2 * jnp.dot(cg, cgdot) * jnp.eye(3) - jnp.outer(cg, cgdot) - jnp.outer(cgdot, cg)
    )
    return mass, cg, inertia, derivative
