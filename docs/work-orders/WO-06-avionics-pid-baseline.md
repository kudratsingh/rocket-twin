# WO-06 — Avionics model, attitude estimator, PID baseline

Branch: `wo-06-control`. Tier: Mac CPU.

## Deliverables

1. `src/avionics/estimator.py`: attitude from IMU (complementary or Madgwick; same algorithm
   the firmware will run), altitude/vertical speed from baro + accel; runs at the spec loop
   rate inside the sim's control decimation. `src/avionics/timing.py`: loop jitter and sensor
   latency models. `src/avionics/faults.py`: sensor dropout, servo stall, brownout injection.
2. `src/control/pid.py`: two-axis gimbal PID (or LQR) on estimated tilt and rates with
   feed-forward from the reference; anti-windup; gains in `configs/control/pid.yaml`.
   `src/control/abort.py`: the abort state machine from the spec thresholds (tilt, rate,
   sensor dropout, servo fault) → safe state. Both written so WO-10 can codegen them to C.
3. `src/sim/protocol.py` frozen: cells (nominal, wind, randomised), 1,000 episodes, 3 seeds,
   metrics (tilt RMS, max tilt, tilt at burnout, apogee σ, gimbal effort, aborts).
4. `scripts/wo06_eval.py --controller pid --preset sim`: Monte-Carlo over the protocol, writes
   the results table; frontend controller panel shows gains and live tilt/rate during replay.

## Benchmark

PID holds tilt ≤ 5° at burnout in ≥ 95 % of 1,000 wind-cell episodes and never triggers abort
in the nominal cell; abort engages correctly on every injected fault; results table filled for
PID, all cells, 3 seeds.

## Notes

- Servo lag, rate limit and latency must be on for the benchmark. A PID that only works with
  an ideal servo is not a baseline.
- Tune for the real servo's numbers from the spec; if the gimbal authority is insufficient,
  say so in STATUS with the numbers (it changes the servo choice in the BOM).

## Modular control scope

Evaluate finned trainer and finless separately, using the actual G12 moving group
and thrust history. The WO-01 useful-time proxy is not control validation. Quantify
settling time, thrust moment arm, torque/rate authority, fin restoring torque and
authority loss at burnout. Extend the fault protocol through independent recovery;
centring an unpowered gimbal cannot stabilize an unstable finless coast. Define the
verified wind envelope per configuration; preliminary launch-screen winds do not
claim the 3 m/s control target. Any unmet target is reported and blocks that release.

## Mandatory fidelity prerequisites (ADR-0007)

Before the PID benchmark, implement and validate in the shared JAX core:

- Exact linkage mapping and moving motor mass/CG/inertia; load-dependent servo
  torque/speed, supply-voltage effects, friction/backlash, deadband, position/rate
  limits and measured/estimated latency. Assess cross-axis, gyroscopic and other
  coupling where material. Record sources, uncertainty ranges and independent
  known cases; retain hooks for bench calibration.
- Aerodynamic force, moment and damping appropriate to the intended Mach, Reynolds
  number and angle-of-attack envelope. Explicitly cover the G12 large-angle cases
  from WO-02, flag out-of-domain operation and prevent unvalidated cells from
  counting as qualified successes. Use targeted CFD or other higher-fidelity
  analysis where needed for a design decision; import coefficient tables into
  the shared core used by experiments and RL.

Require expanded WO-03 structural/thermal/tolerance evidence for the exact control
configuration. Re-run applicable RocketPy comparisons with changed models and
retain the original WO-02 results. Passing the PID metric without these fidelity
checks does not complete this work order. Separate simulation acceptance from
owner measurements, HIL, WO-10 review and flight release.
