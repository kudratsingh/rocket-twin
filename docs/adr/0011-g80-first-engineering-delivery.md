# ADR-0011 — G80-first engineering delivery, with separate mode evidence

Date: 2026-11-01 UTC (2026-10-31 Pacific)
Status: accepted — explicit owner direction

## Decision

Within open WO-03, prioritize one complete conventional fixed-motor **G80**
engineering package. Carry its structures/joints, thermal protection, fits,
retention, installed fins/flutter and recovery through the same resolved
configuration, mass/balance/full-inertia model and affected flight comparisons.
Preserve the full separate 50 g growth allowance.

The three committed goals are substantial custom construction, maximum practical
conventional performance within the no-high-power-certification scope, and
serious PID-to-reinforcement-learning development. G54 remains the committed
performance-upgrade track with its conditional motor/design gates. G12 remains
the controls track, including the eventual finless objective. Neither is canceled
or given a pass by G80 evidence. Share the upper assembly where mechanically
sensible; do not force a TVC-specific correction into the fixed mount.

This changes **delivery priority**, not formal WO-03 completion. Record partial
requirements and configuration readiness explicitly. A G80-specific pass cannot
set aggregate WO-03 complete or clear G54/G12 findings. Existing full WO-04/05
prerequisites remain; ADR-0009 continues to authorize the usable early preview.
Any later formal staged-completion revision requires an explicit plan/criterion
change rather than a silent reinterpretation of the benchmark.

## Execution

1. Close the declared small thermal-tool campaign with a scoped decision. Keep
   strict software checks and engineering decision accuracy separate; retain
   failed criteria. No new open-ended custom heat solver. Actual geometry needs
   its existing prerequisites and a separately declared budget.
2. Verify the exact current G80 findings before modifying a single candidate.
   Correct fit and load paths in dependency order; account for all new material
   and uncertainty. Revalidate affected geometry, loads, heat, mass properties,
   stability/guide and JAX/RocketPy comparisons after integration.
3. Deliver the saved inspector/real-simulator/replay preview using the current
   stack. Missing compatible engineering overlays do not delay basic delivery.
   Use the designated Chrome-window agent for browser checks and continue code
   work independently when the window or host service is unavailable.

Report usable outcomes or closed requirements, blockers, the next bounded
deliverable/stop condition and specific owner input. Test counts and PR checks
are supporting implementation evidence, not engineering acceptance.

## Gates and references

The repository stays private. Purchases, physical work, paid computation,
WO-10 owner review and flight release retain their existing gates. PID/RL,
HIL/logging/system identification, the shared YAML/JAX architecture, RocketPy,
the digital orbital launcher and G-FOLD comparison retain their work orders.

See [G80 intake](../wo03-g80-package-intake.md),
[thermal comparison](../wo03-elmer-thermal-comparison.md),
[preview delivery](../wo04-preview-delivery.md), and
[WO-03](../work-orders/WO-03-cad-parts-meshes.md).
