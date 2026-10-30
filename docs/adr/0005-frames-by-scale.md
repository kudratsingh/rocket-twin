# ADR-0005: Reference frames by vehicle scale

Status: accepted
Date: 2026-10-26
Work order: WO-02 / WO-05b

## Decision

The body frame is the same for every vehicle: x forward along the nose, z down, quaternion
scalar-first. The world frame depends on the spec's `scale`:

- `model` — flat Earth, local NED at the pad, constant gravity, atmosphere from a fixed
  sea-level-corrected table up to the vehicle's ceiling (a few hundred metres).
- `full` — Earth-centred inertial (ECI) integration with a rotating Earth for launch-site
  velocity and ground track; gravity inverse-square (J2 behind a flag); US Standard Atmosphere
  1976 to 150 km; local-vertical/local-horizontal frame derived for guidance and display.

Both are defined once in `src/sim/frames.py` with conversion helpers; `step()` selects by
`scale`, and the two paths share dynamics, propulsion, aero, sensors and actuators.

## Why

- A flat-Earth NED frame is exact enough for a 300 m model-rocket flight and keeps that path
  simple and fast for RL.
- An orbital ascent cannot be done in a flat frame: Earth rotation (~400 m/s at low latitude),
  curvature and gravity variation are first-order effects on reaching orbit.

## Alternatives considered

- ECI for everything — correct but burdens the model rocket with needless complexity and
  slows the RL rollouts.
- Flat Earth with corrections for the launcher — error-prone and fails for orbital insertion.

## What would reopen this

A need for high-latitude or inclined-orbit missions where J2 and launch-site latitude matter
beyond the flag (then full geopotential via the `Gravity` extension point).
