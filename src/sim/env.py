"""One pure step function for single experiments and future batched PID/RL.

reset/step accept explicit parameters and random keys; no global simulator state.
RK4 handles mechanics, while actuator/sample/event updates use the physics clock.
Recovery triggers on descending flight after ascent, with separate lag/inflation.
An absent trigger or impact is recorded rather than silently filling event times.
WO-02 has locked-gimbal actions; controllers/reward protocols arrive in WO-06/07.
Reference: ADR-0001, Zipfel ch. 6, JAX jit/vmap/lax.scan documentation.
This observation API contains sensor outputs, not an oracle attitude controller.
"""

from functools import partial

import jax
import jax.numpy as jnp
from jax import Array

from src.sim import actuators, dynamics, sensors
from src.sim.types import Params, State

# Double precision for the independent physics benchmark; policy export stays float32.
jax.config.update("jax_enable_x64", True)  # type: ignore[no-untyped-call]  # JAX 0.4 setter lacks types.


def reset(p: Params, key: Array) -> State:
    direction = p.rail_direction
    # q taking body +x to the launch direction (shortest rotation).
    q = jnp.concatenate(
        (jnp.array([1 + direction[0]]), jnp.cross(jnp.array([1.0, 0, 0]), direction))
    )
    q = q / jnp.linalg.norm(q)
    rigid = jnp.concatenate((jnp.zeros(6), q, jnp.zeros(3)))
    bias = jax.random.normal(key, (6,)) * jnp.concatenate(
        (jnp.full(3, p.sensors[0] * p.sensors[9]), jnp.full(3, p.sensors[1] * p.sensors[9]))
    )
    return State(
        jnp.array(0.0),
        rigid,
        jnp.zeros(4),
        jnp.zeros((64, 2)),
        jnp.zeros((16, 6)),
        bias,
        jnp.zeros(10),
        jnp.array(0.0),
        jnp.array(-1.0),
        jnp.array(0.0),
        jnp.array(-1.0),
        jnp.array(False),
        jnp.array(False),
    )


def step(state: State, action: Array, p: Params, key: Array) -> tuple[State, Array, Array]:
    servo, queue = actuators.advance(state.servo, state.commands, action, p)
    rigid = dynamics.rk4(
        state.time, state.rigid, servo[:2], state.recovery_time, p, state.rail_exit_time >= 0
    )
    launched = state.launched | (-rigid[2] > 0.1)
    landed = state.landed | (launched & (rigid[2] >= 0) & (rigid[5] > 0))
    rigid = jnp.where(state.landed, state.rigid, rigid)
    rigid = rigid.at[:6].set(
        jnp.where(landed, jnp.concatenate((rigid[:2], jnp.zeros(4))), rigid[:6])
    )
    t = state.time + p.launch[3]
    exit_now = (state.rail_exit_time < 0) & (jnp.dot(rigid[:3], p.rail_direction) >= p.launch[0])
    exit_time = jnp.where(exit_now, t, state.rail_exit_time)
    exit_speed = jnp.where(exit_now, jnp.linalg.norm(rigid[3:6]), state.rail_exit_speed)
    apex = (state.recovery_time < 0) & launched & (rigid[5] > 0) & (state.rigid[5] <= 0)
    recovery_time = jnp.where(apex, t, state.recovery_time)
    new = state._replace(
        time=t,
        rigid=rigid,
        servo=servo,
        commands=queue,
        launched=launched,
        landed=landed,
        rail_exit_time=exit_time,
        rail_exit_speed=exit_speed,
        recovery_time=recovery_time,
    )
    _, info = dynamics.derivative(t, rigid, servo[:2], recovery_time, p, exit_time >= 0)
    obs, imu_queue, baro = sensors.observe(new, info[-3:], p, key)
    return new._replace(observation=obs, imu_queue=imu_queue, baro_filtered=baro), obs, info


@partial(jax.jit, static_argnames=("steps",))
def rollout(p: Params, key: Array, steps: int) -> tuple[State, Array]:
    def advance(s: State, i: Array) -> tuple[State, Array]:
        def active(current: State) -> tuple[State, Array, Array]:
            return step(current, jnp.zeros(2), p, jax.random.fold_in(key, i))

        def absorbed(current: State) -> tuple[State, Array, Array]:
            return (
                current._replace(time=current.time + p.launch[3]),
                current.observation,
                jnp.zeros(9),
            )

        s, _, info = jax.lax.cond(s.landed, absorbed, active, s)
        row = jnp.concatenate(
            (jnp.array([s.time]), s.rigid, info, s.servo[:2], jnp.array([s.landed.astype(float)]))
        )
        return s, row

    return jax.lax.scan(advance, reset(p, key), jnp.arange(steps))
