"""Known answers for the shared JAX core before any controller is added."""

from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from src.sim import actuators, dynamics, env, motor, quaternion, sensors, tvc
from src.sim.inputs import prepare
from src.vehicle.mass import mass_properties
from src.vehicle.motors import load_rasp
from src.vehicle.schema import load_vehicle

ROOT = Path("configs/vehicle/platform")


@pytest.mark.parametrize("name", ["performance.yaml", "tvc-finned.yaml", "tvc-finless.yaml"])
def test_depletion_mass_cg_tensor_and_source_impulse(name: str) -> None:
    v = load_vehicle(ROOT / name)
    p = prepare(v, {"sensor_noise": False})
    assert v.motor and v.motor.curve
    source = load_rasp(v.motor.curve)
    for t in [0, 0.123, 1.1, source.burn_time_s, source.burn_time_s + 1]:
        thrust, fraction, _ = motor.motor_values(jnp.array(t), p)
        assert float(thrust) == pytest.approx(source.thrust_n(t), abs=1e-8)
        assert float(fraction) == pytest.approx(source.burned_fraction(t), abs=1e-10)
        mass, cg, inertia, _ = motor.properties(jnp.array(t), p)
        own = mass_properties(v, float(fraction))
        assert float(mass) == pytest.approx(own.mass_kg)
        assert -float(cg[0]) == pytest.approx(own.cg_m)
        np.testing.assert_allclose(inertia, own.inertia_kg_m2, atol=1e-12)


def test_quaternion_and_tvc_known_answer() -> None:
    p = prepare(load_vehicle(ROOT / "tvc-finned.yaml"), {})
    state = env.reset(p, jax.random.PRNGKey(0))
    r = quaternion.rotation(state.rigid[6:10])
    np.testing.assert_allclose(r @ jnp.array([1.0, 0, 0]), [0, 0, -1], atol=1e-12)
    np.testing.assert_allclose(r.T @ r, np.eye(3), atol=1e-12)
    force, torque = tvc.thrust_force_moment(
        jnp.array(20.0), jnp.array([0.05, 0]), jnp.array([-0.5, 0, 0]), jnp.array(0.7)
    )
    assert float(force[2]) == pytest.approx(-20 * np.sin(0.05))
    assert float(torque[1]) == pytest.approx(-0.2 * 20 * np.sin(0.05))


def test_vacuum_free_fall_and_finite_4096_env_step() -> None:
    p = prepare(
        load_vehicle(ROOT / "performance.yaml"), {"sensor_noise": False, "recovery_enabled": False}
    )
    p = p._replace(aero=p.aero.at[0].set(0))
    state = env.reset(p, jax.random.PRNGKey(0))
    y = state.rigid.at[2].set(-100)
    out = dynamics.rk4(jnp.array(10.0), y, jnp.zeros(2), jnp.array(-1.0), p)
    dt = float(p.launch[3])
    assert float(out[2]) == pytest.approx(-100 + 9.80665 * dt**2 / 2, abs=1e-10)
    assert float(out[5]) == pytest.approx(9.80665 * dt, abs=1e-10)
    keys = jax.random.split(jax.random.PRNGKey(1), 4096)
    states = jax.vmap(env.reset, in_axes=(None, 0))(p, keys)
    new, obs, _ = jax.jit(jax.vmap(env.step, in_axes=(0, 0, None, 0)))(
        states, jnp.zeros((4096, 2)), p, keys
    )
    assert new.rigid.block_until_ready().shape == (4096, 13)
    assert np.isfinite(np.asarray(new.rigid)).all() and np.isfinite(np.asarray(obs)).all()


def test_servo_delay_limits_stall_and_sensor_noise() -> None:
    p = prepare(load_vehicle(ROOT / "tvc-finned.yaml"), {})
    state = env.reset(p, jax.random.PRNGKey(0))
    servo, queue = actuators.advance(state.servo, state.commands, jnp.ones(2), p)
    np.testing.assert_array_equal(servo, jnp.zeros(4))
    for _ in range(100):
        servo, queue = actuators.advance(servo, queue, jnp.ones(2), p)
    assert np.max(np.abs(servo[:2])) <= float(p.servo[0]) + 1e-10
    assert np.max(np.abs(servo[2:])) <= float(p.servo[1]) + 1e-10
    stalled, _ = actuators.advance(
        servo, queue, -jnp.ones(2), p._replace(servo=p.servo.at[6].set(1))
    )
    np.testing.assert_array_equal(stalled[:2], servo[:2])
    state = state._replace(sensor_bias=jnp.zeros(6))
    keys = jax.random.split(jax.random.PRNGKey(2), 10000)
    obs, _, _ = jax.jit(jax.vmap(sensors.observe, in_axes=(None, None, None, 0)))(
        state, jnp.zeros(3), p, keys
    )
    std = np.std(np.asarray(obs)[:, :6], axis=0)
    np.testing.assert_allclose(
        std, [float(p.sensors[0])] * 3 + [float(p.sensors[1])] * 3, rtol=0.05
    )


def test_guide_constraint_never_reengages_during_return() -> None:
    p = prepare(load_vehicle(ROOT / "performance.yaml"), {"recovery_enabled": False})
    state = env.reset(p, jax.random.PRNGKey(0))
    y = state.rigid.at[2].set(-0.5).at[5].set(5).at[11].set(0.1)
    free, _ = dynamics.derivative(jnp.array(20.0), y, jnp.zeros(2), jnp.array(-1.0), p, True)
    constrained, _ = dynamics.derivative(
        jnp.array(20.0), y, jnp.zeros(2), jnp.array(-1.0), p, False
    )
    assert float(jnp.linalg.norm(free[6:10])) > 0
    np.testing.assert_array_equal(constrained[6:10], np.zeros(4))
