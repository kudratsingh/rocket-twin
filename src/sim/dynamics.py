"""6-DOF rigid-body RK4 in world NED, body-x noseward, quaternion attitude.

m*vdot=R*(F_thrust+F_aero)+m*g; I*wdot=tau-w cross Iw-Idot*w.
Mass, CG and inertia follow exact source impulse with uniform propellant depletion.
Guide motion constrains translation to the launch direction and locks attitude;
friction is an explicit uncertainty, zero in the independent reference benchmark.
After release, all six degrees of freedom evolve. Aerodynamic surface velocity
includes angular rate. Recovery is a separate drag system after an apogee trigger.
No aerodynamic/structural flight qualification follows from numerical agreement.
Detailed exhaust mass-flux terms, gimbal multibody inertia and parachute attitude
are approximations, recorded in the validation report.
References: Zipfel ch. 4–6; Goldstein ch. 5; US Standard Atmosphere 1976.
"""

import jax.numpy as jnp
from jax import Array

from src.sim import aero, environment, motor, quaternion, tvc
from src.sim.frames import STANDARD_GRAVITY_M_S2 as G
from src.sim.types import Params


def derivative(
    t: Array, y: Array, angles: Array, recovery_time: Array, p: Params
) -> tuple[Array, Array]:
    position, velocity, q, omega = y[:3], y[3:6], y[6:10], y[10:13]
    rotation = quaternion.rotation(q)
    mass, cg, inertia, idot = motor.properties(t, p)
    thrust, _, _ = motor.motor_values(t, p)
    burn_end = p.motor[4] + p.motor[0] * p.motor[3]
    rho, sound, _ = environment.atmosphere(-position[2] + p.launch[2])
    relative = velocity - environment.wind(t, -position[2], p)
    force, torque, mach, alpha = aero.forces(
        rotation.T @ relative, omega, cg, rho, sound, (t < burn_end).astype(float), p
    )
    tf, tm = tvc.thrust_force_moment(thrust, angles, cg, p.pivot_station)
    acceleration = rotation @ (force + tf) / mass + jnp.array([0, 0, G])
    opening = jnp.clip((t - recovery_time - p.recovery[1]) / jnp.maximum(p.recovery[2], 1e-3), 0, 1)
    opening = jnp.where((recovery_time >= 0) & (p.recovery[3] > 0), opening, 0)
    acceleration -= (
        0.5 * rho * p.recovery[0] * opening * jnp.linalg.norm(relative) * relative / mass
    )
    angular = jnp.linalg.solve(
        inertia, torque + tm - jnp.cross(omega, inertia @ omega) - idot @ omega
    )
    # Recovery attitude dynamics are not meaningful in this simple canopy model.
    angular = jnp.where(opening > 0.1, -5 * omega, angular)
    on_rail = jnp.dot(position, p.rail_direction) < p.launch[0]
    along = jnp.dot(acceleration, p.rail_direction) - p.launch[1] / mass
    at_rest = (jnp.dot(position, p.rail_direction) <= 0) & (
        jnp.dot(velocity, p.rail_direction) <= 0
    )
    along = jnp.where(at_rest, jnp.maximum(along, 0), along)
    acceleration = jnp.where(on_rail, p.rail_direction * along, acceleration)
    angular = jnp.where(on_rail, jnp.zeros(3), angular)
    qdot = 0.5 * quaternion.multiply(q, jnp.concatenate((jnp.array([0.0]), omega)))
    qdot = jnp.where(on_rail, jnp.zeros(4), qdot)
    result = jnp.concatenate((velocity, acceleration, qdot, angular))
    specific = rotation.T @ (acceleration - jnp.array([0, 0, G]))
    info = jnp.concatenate(
        (
            jnp.array([mass, -cg[0], thrust, mach, alpha, 0.5 * rho * jnp.dot(relative, relative)]),
            specific,
        )
    )
    return result, info


def rk4(t: Array, y: Array, angles: Array, recovery_time: Array, p: Params) -> Array:
    dt = p.launch[3]
    k1, _ = derivative(t, y, angles, recovery_time, p)
    k2, _ = derivative(t + dt / 2, y + dt * k1 / 2, angles, recovery_time, p)
    k3, _ = derivative(t + dt / 2, y + dt * k2 / 2, angles, recovery_time, p)
    k4, _ = derivative(t + dt, y + dt * k3, angles, recovery_time, p)
    out = y + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
    return out.at[6:10].set(out[6:10] / jnp.maximum(jnp.linalg.norm(out[6:10]), 1e-12))
