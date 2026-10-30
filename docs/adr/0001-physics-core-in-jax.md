# ADR-0001: Physics core in JAX, pure functions

Status: accepted
Date: 2026-10-26
Work order: WO-02

## Decision

The 6-DOF simulator is written once as pure JAX functions:
`step(state, action, params, key) -> (state, obs, info)`, fixed-step RK4 at the spec's
physics rate (default 1 kHz, control loop decimated from it). Single-run experiments call it
in a Python loop on the Mac CPU; RL vmaps the same function over thousands of environments on
a GPU. No second implementation exists anywhere (no NumPy twin, no TypeScript preview physics).

## Why

- One code path means the frontend replays exactly what RL trained on.
- `vmap` + `jit` gives thousands of parallel envs on one card with no custom CUDA.
- JAX runs on Apple Silicon CPU for the `tiny` and `sim` presets without extra setup.

## Alternatives considered

- MuJoCo (Warp or classic) — excellent rigid-body engine, but variable mass, thrust curves and
  Barrowman aero are all custom anyway; MuJoCo adds a dependency for no shared physics.
- NumPy core + separate JAX port for RL — two implementations, guaranteed drift.
- RocketPy as the sim — not batched, not differentiable, no TVC actuator loop; kept as the
  validation reference instead.

## What would reopen this

JAX install failure on the owner's Mac that cannot be fixed with a pinned wheel; or
`vmap` throughput under 50,000 env-steps/s on a 4090 after profiling.
