# ADR-0003: Model-rocket class, long-burn 29 mm motor, Teensy 4.1 flight computer

Status: superseded in part by ADR-0006 (2026-10-29 owner rebaseline). Historical decisions below are preserved; fixed motor, wall, diameter and screening thresholds no longer govern. Teensy/Cortex-M7 and no-HPR objectives are retained.
Date: 2026-10-26
Work order: WO-01 / WO-09

## Decision

- Stay in the NAR model-rocket class (≤ 1,500 g, ≤ 125 g propellant, ≤ 320 N·s): no
  certification, no FAA waiver, launchable at any club model-rocket range with RSO approval.
- Default motor: Estes F15 (29 mm, ~3.4 s burn). TVC wants a long, flat thrust curve far more
  than peak thrust; a short-burn motor leaves no time to control. Candidates recorded with
  their certified curves in `configs/vehicle/motors/`; the choice is confirmed in WO-01 when
  the vehicle's thrust-to-weight at liftoff is ≥ 3 and burn time ≥ 3 s with the spec'd mass.
- Flight computer: DIY on a Teensy 4.1 (Cortex-M7 at 600 MHz with FPU, native microSD, enough
  headroom to run a small MLP at ≥ 200 Hz with logging). We need to run our own controller;
  commercial TVC kits do not document custom-firmware support.

## Why

- Model-rocket class keeps the regulatory burden to "follow the safety code and get the RSO's
  OK", which is what a first actively-stabilised vehicle should carry.
- The policy must execute on the vehicle; the computer has to be ours.

## Alternatives considered

- BPS.space Signal R2 kit — proven TVC mount and flight computer, but custom firmware support
  is undocumented and availability is intermittent; may still be borrowed for the TVC mount
  geometry if the owner buys one.
- ESP32-S3 / RP2040 — cheaper, but less headroom for a 500 Hz loop with logging and no native
  SD on most boards.
- G-class motors (Aerotech G8/G11 long-burn) — attractive burn times, but push mass and
  impulse toward the class limits; recorded as a v2 option.

## What would reopen this

Thrust-to-weight < 3 or burn < 3 s with the final spec mass; servo bandwidth too low for the
gimbal authority the sim says is needed (then a larger servo and heavier vehicle, re-run the
limit check).

## WO-01 update — 2026-10-29

The 529 g F15 reference gives average thrust / liftoff weight 2.772, below the
minimum 3. The owner retained the 1.6 mm body tubes and directed a stronger,
long-burning 29 mm motor study. The 1.2 mm proposal is retained for later review.

Study inputs and source disagreements are recorded in
`configs/studies/motor-selection.yaml` and `motor-source-evidence.yaml` in that
same directory. `make motor-study` reproduces static mass/CG/fit screening and
RocketPy comparison. G25 source variants are separate hypotheses; certification
or dimension conflicts prevent selection. F25W is an additional source candidate,
not a selected motor. Burn duration must remain at least 3 seconds.

A replacement must include assembled casing/closure mass, extra mount/retention
mass, exact geometry and a traceable curve/certificate before closing WO-01.
Nothing in this study authorizes procurement, a physical build or a flight.
