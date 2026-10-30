# WO-08 — Lander: PPO vs G-FOLD, digital milestone writeup

Branch: `wo-08-lander`. Tier: Mac CPU for G-FOLD; dev GPU for PPO.

## Deliverables

1. `src/gnc/gfold.py`: lossless-convexification landing guidance (cvxpy + Clarabel): minimum
   fuel to a target with thrust bounds, glide-slope and tilt constraints; time-of-flight line
   search. `src/gnc/reference.py`: converts a G-FOLD solution to a reference trajectory the
   sim can track with a simple tracking controller.
2. PPO landing policy for `orbital-launcher-v1` stage 1, episodes starting at the end of the
   WO-05b entry burn (reuse WO-07 PPO; new obs/action/reward for position, velocity, attitude,
   propellant; actions = centre-engine throttle, gimbal, grid-fin deflections).
3. Cells: nominal; disturbed (wind, thrust ±10 %, sensor noise, 100 ms actuator delay — the
   things G-FOLD's model omits). Metrics per PLAN.md.
4. Frontend lander mode: throttle trace, G-FOLD reference drawn beside the RL trajectory.
5. `docs/blog-draft.md`: "A digital twin of two rockets: PID vs RL ascent on a model rocket,
   ascent-to-orbit and RL vs G-FOLD landing on a full-scale launcher, on one GPU" — what was
   built, numbers, what cost what.

## Benchmark

G-FOLD solves all nominal cases; PPO lands ≥ 90 % nominal; disturbed-cell comparison table
filled for both with fuel and success; blog draft written with every number traceable to a
run id. This is the shippable sim-only milestone.

## Notes

- The lander is the orbital stage 1, digital only; do not let its needs leak into
  the modular physical TVC configurations. Initial conditions for the landing cases come from the WO-05b nominal
  mission's entry-burn end state, perturbed per the disturbed cell.
- Batch the GPU approvals: one message with all planned runs and costs.
