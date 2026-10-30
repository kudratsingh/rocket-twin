# WO-07 — RL ascent controller (PPO, domain randomised)

Branch: `wo-07-rl`. Tier: CPU `tiny`, then dev GPU (RTX 4090) for full runs.

## Deliverables

1. `src/rl/ppo.py`: PureJaxRL-style PPO over the vmapped WO-02 env; `src/rl/randomisation.py`:
   thrust scale ±15 % and timing, mass/CG offsets, servo lag/rate/deadband, IMU bias/noise,
   wind, loop jitter — ranges in `configs/rl.yaml`. `src/rl/policy.py`: MLP ≤ 3 layers,
   ≤ 64 units, float32, normalisation constants; `src/rl/export.py`: weights → C header
   (`firmware/include/policy.h`) with a reference forward pass and a test comparing Python and
   C outputs on 100 random observations.
2. Observation: estimated tilt (2), rates (3), body accel (3), time since ignition, gimbal
   state (2), reference error (2). Action: two gimbal angle commands. Reward: tilt error,
   rate penalty, gimbal effort, reference tracking, abort penalty.
3. `scripts/wo07_rl.py --preset {tiny,rl}`: `tiny` trains on CPU in < 2 min and improves over
   a random policy; `rl` runs the full configuration and writes a run record with cost.
4. `scripts/wo06_eval.py --controller rl`: same protocol as PID; frontend policy panel shows
   obs/action traces and the randomisation draw for a run.

## Benchmark

Committed PPO training and fair PID/RL evaluation use the same held-out cells and
three seeds per configuration. Report tilt RMS, apogee σ, failures, aborts and gimbal
effort, including confidence/variation. Beating PID without extra aborts is the
improvement target; negative comparisons remain valid research results and do not
remove RL from the project. Exported C policy matches Python to 1e-5; size, loop
budget and bounded outputs pass; $/run logged. A policy failing flight acceptance
is retained as a result and cannot be deployed.

## Notes

- Owner launches GPU runs. Expect minutes per run; if a run exceeds 30 min, re-price before
  run 2. Rough estimate: 3 seeds × 20 min × $0.89/h ≈ $1.
- Train on the estimator's output, not the true state — the firmware will not have the truth.
- Keep the policy size constraint from the first run; do not train a big policy "to see".

Train/evaluate finned and finless physical modes as explicit configurations;
report each separately. Preserve estimator observations, realistic sensor/actuator
constraints, domain randomisation, abort logic outside policy control, HIL, logging
and later system identification. Residual RL is an evidence-driven comparison,
not permission to skip the original finless objective or hide a failed policy.

## Improved-model research gate (ADR-0007)

Require the WO-06 gimbal/aero fidelity prerequisites before full training or a
PID/RL benchmark claim. Train with the same loaded, voltage-dependent actuator,
moving inertia and envelope-aware aerodynamic implementation used in experiments.
Randomize residual structural/mass, thermal derating, backlash/friction, voltage,
servo delay/load, aero coefficients/damping and sensor uncertainties with sourced
or explicitly bounded distributions. Evaluate against PID on identical held-out
conditions/seeds, including large-angle and out-of-domain/abort cases. Report
uncertainty, failures and negative results; preserve embedded policy constraints
and independent abort/recovery. Later measured calibration remains WO-09–12.

## Traceability and vibration-risk carry-through

Carry justified residual actuator, vibration/measurement, aero, joint and temperature uncertainties from WO-03/06 into RL training and held-out PID/RL evaluation. Preserve negative results and distinguish out-of-domain failures from qualified success.
