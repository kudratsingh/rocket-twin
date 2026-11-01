# G80 guide-event timing audit — conditional bound not admitted

A read-only attempt to bound departure-speed clock error is preserved in
[the diagnostic packet](../runs/wo03-g80-guide-clock-bound-20261101-v1/record.json)
and [applicability assessment](../runs/wo03-g80-guide-clock-bound-20261101-v1/applicability-audit.json).
It runs no simulator or mesh and changes no physics. It does **not** establish
a conservative bound for the actual saved flight.

The trial arithmetic used the source curve's 102.2 N maximum, effective full
depletion mass, thrust scale and the 5 ms time step to form
`delta_v <= dt * (Fmax / mmin + g)` for a constrained, calm-air axial path.
Subtracting that allowance from the three calm-air recorded guide speeds gives
18.155, 15.761 and 17.385 m/s. Those values and their conditional flags are
retained as hypothetical arithmetic, not accepted crossing-speed certificates.

Source review identified an unmet precondition: `dynamics.derivative` tests
guide position at each internal Runge–Kutta stage. The final recorded step may
therefore include free-flight derivative stages before `env.step` stores the
persistent guide-exit event. The trial bound does not cover the resulting
rotational/aerodynamic coupling. Source files match the staged flight source,
but that does not repair the proof's applicability. No threshold was changed
and no run repeated to fill missing telemetry.

The original sampled guide checks retain their stated model/time-resolution
scope; this audit adds no acceptance closure or new failure claim about the
physical guide. The missing Stage3 trajectory and guide-row audit remain
unavailable. A later bound must cover the actual internal-stage release, or
use appropriately retained trajectory/event and refinement evidence.
