# A1 retained material occupancy — declared read-only audit

One1CPU/5wall-second annular interval audit, no design iteration, CAD, heat,
guide or structural solve. Source A1 seat and retained C1 liner/shield dimensions
are compared as concentric annuli. Preserve the result, refuse overwrite and
do not shorten the liner, shift the motor or rerun A1 automatically.

This source-layout check follows the completed A1 packet and has its own
identity. It closes no requirement. Original source/config/mass and failure
records remain unchanged. A positive material overlap is an additional failed
admission condition and must be exposed in the current report and snapshot.

Executed once: the seat spansz1193–1195,R14.6–17.2. The retained mica and foil
both spanz1072–1200, atR14.7–15.1 andR15.1–15.12 respectively. Thus the
declared materials intersect over2mm axially:74.895569mm³ mica and3.797557mm³
foil. These are analytic annular intersections, not a full CAD collision or
motion sweep. The seat cannot be admitted with the unchanged thermal barrier.
See [record](../runs/wo03-a1-occupancy-audit-20261102-v1/record.json).

The specific next motor-interface decision is to establish a current verified
thrust-ring/nozzle/liner termination and seat plane. Any relocation or shortened
barrier needs explicit geometry, complete mass/CG/guide and thermal revalidation;
it is not performed as an automatic correction to this failed A1 study.
