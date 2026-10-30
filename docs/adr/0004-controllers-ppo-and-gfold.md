# ADR-0004: Controllers — PID baseline, PPO for RL, G-FOLD as the optimal reference

Status: accepted
Date: 2026-10-26
Work order: WO-06 / WO-07 / WO-08

## Decision

- Baseline and first-flight controller: PID on gimbal angles from estimated attitude and rates
  (LQR if PID cannot meet the WO-06 benchmark), gains tuned in sim, exported to firmware.
- RL: PPO (PureJaxRL-style, single file, vmapped envs) with domain randomisation. Policy is an
  MLP with ≤ 3 layers and ≤ 64 units, float32, exported as a C header. Observations and actions
  are normalised with constants baked into the header.
- Lander reference: G-FOLD via lossless convexification solved with cvxpy/Clarabel on the
  `orbital-launcher-v1` stage-1 landing cases (from end of entry burn); PPO landing compared
  against it on fuel and success under disturbances.

## Why

- PPO is the published recipe for TVC-landing sim studies and quadrotor sim-to-real, is
  stable with vmapped envs, and needs no replay buffer.
- The flight-computer constraint (rule 9) is a hard ceiling on policy size; PPO handles tiny
  networks well.
- G-FOLD is the method real landers use; it is the right yardstick for "did RL learn something
  the optimiser cannot do", and it is a few hundred lines in cvxpy.

## Alternatives considered

- SAC — off-policy, replay buffer, more memory, no benefit at this scale.
- Residual RL on top of PID — a good v2 for flight (policy only corrects PID), noted for WO-12
  if full RL does not transfer.
- MPC in flight — not feasible at the loop rate on a Cortex-M7 for v1.

## What would reopen this

PPO fails to beat PID after two full runs with the randomisation set (then residual RL);
G-FOLD infeasible for the lander cases (then successive convexification).

## Owner rebaseline — 2026-10-29

PID-to-RL training, embedded policy deployment and eventual real-flight comparison
are committed core outcomes, across separately modelled finned trainer and finless
configurations. A negative PID/RL comparison is a reportable result, not permission
to remove RL from the project. Keep realistic sensors/actuators, randomisation,
abort/HIL, logging and system identification. Performance improvement remains a
research target; release depends on validated performance and safety, not winning
a metric. G-FOLD and the digital orbital comparison remain in scope. Any residual
policy investigation supplements the documented PPO result rather than erasing it.
