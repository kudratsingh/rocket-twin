# WO-02 — 6-DOF simulator (JAX) and validation against RocketPy

Branch: `wo-02-sim`. Tier: Mac CPU.

## Deliverables

1. `src/sim/`: `frames.py` (single definition), `dynamics.py` (rigid body, quaternion
   attitude, variable mass and inertia from WO-01, RK4 fixed step), `motor.py` (thrust-curve
   interpolation, propellant depletion, ignition delay, thrust-scale randomisation hook),
   `aero.py` (forces and moments from the WO-01 CP/drag model, angle of attack, damping),
   `tvc.py` (gimbal kinematics, thrust vector in body frame, moment about CG), `wind.py`
   (steady + gust + altitude profile), `sensors.py` (IMU accel/gyro with bias, noise, sample
   rate; barometer with noise and lag), `actuators.py` (servo: second-order lag, rate limit,
   deadband, latency, stall), `env.py` (reset/step/obs/reward/done for resolved physical modes and later the orbital vehicle; batched
   with `vmap`), `protocol.py` (eval cells, stub until WO-06), `telemetry.py` (Parquet writer).
2. Known-answer tests: a +δ gimbal deflection produces the expected sign and magnitude of pitch
   moment; zero wind + zero gimbal + fins → vertical flight; sensor noise statistics match spec.
3. `scripts/wo02_sim.py --preset {tiny,sim}`: runs actual performance and finned-trainer geometries unguided (gimbal locked
   where present), writes telemetry and `record.json`; `--compare rocketpy` runs the same case
   in RocketPy and prints apogee, time-to-apogee, max velocity deltas; `--batch N` times a
   vmapped rollout of N envs.
4. Derivation summary (10–20 lines) at the top of each physics module with its reference.

## Benchmark

Apogee and time-to-apogee within 5 % of RocketPy for each actual finned configuration and its distinct motor hypothesis; known-answer
tests pass; `vmap` over 4,096 envs steps on the Mac CPU; `tiny` < 2 min.

## Notes

- Validate the unguided case because RocketPy has no TVC; TVC correctness rests on the
  known-answer tests and later on flight logs.
- Build behind the interfaces in `docs/EXTENSIONS.md` (`AeroModel`, `EngineModel`,
  `Atmosphere`, `Gravity`, `Wind`) even though v1 implements the simple version of each;
  `propulsion.py` handles solid motors now and gets the liquid-engine model in WO-05b.
- `frames.py` defines both the flat-Earth NED path (`scale: model`) and the ECI path
  (`scale: full`, ADR-0005); only the NED path is exercised in this WO.
- No controller yet; `action` is a locked gimbal.

## ADR-0006 dependency clarification

Use the resolved `configs/platform.yaml` modes with their actual fins, moving
motor assembly, mass/inertia and source hashes. A motor substitution creates a
new complete experimental configuration. If the current sold variant/source
has not been reconciled, label the comparison a source-hypothesis case rather
than a prediction of purchased hardware. Do not import massless legacy stubs.

Validate usable guide travel, departure speed, crosswind response, acceleration,
altitude/site limits and recovery/deployment timing. A -10 delay is not selected
until the trajectory establishes suitability. Plugged G12ST-P requires independent
electronic recovery. Simulate through recovery, including long burns. Finless
known-answer tests do not establish stable flight or replace WO-06/07 closed-loop
validation and the later burnout-to-recovery gate.

## Completion evidence

Numerical benchmark met: final Mac CPU records and 65-test validation are linked in
[results](../results.md) and the [study report](../wo02-flight-study.md). Both actual
finned baselines plus three alternative hypotheses pass the 5% apogee/time gate;
4,096 CPU environments step through the same core; tiny completes below 120 s.
Full sensitivity cases include guide, wind, acceleration, recovery and source-mass
uncertainty. This closes WO-02 model validation, not motor procurement, measured
aerodynamics, structure/heat, control, HIL, finless transition or flight release.
