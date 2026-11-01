# G80 integrated mount and recovery candidate

**A complete proposed G80 geometry and mass package is available for inspection.**
It combines the selected 32.2 mm mount proposal and the existing recovery
packaging proposal; it is not adopted, structurally or thermally qualified, or
flight-ready. The resolved candidate identity is
`62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009`.

The separate local [resolved copy](../build/wo03-g80-integrated-candidate-v1/resolved-candidate.yaml),
[STEP assembly](../build/wo03-g80-integrated-candidate-v1/assembly.step),
[GLB assembly](../build/wo03-g80-integrated-candidate-v1/assembly.glb),
[execution record](../build/wo03-g80-integrated-candidate-v1/record.json) and
[mass reconciliation](../build/wo03-g80-integrated-candidate-v1/mass-reconciliation.json)
are generated local artifacts under ignored `build/`. They must be retained
separately from source. Active vehicle and preview assets were not changed.

## Composition and identity

The starting 43-part mount copy had resolved identity
`0a1ad4c196e7bbd046704199e99bad1f6649bc237c3c07b0e4f26118d4572c4b`.
The recovery geometry is reconstructed using the existing `copy_sources` and
`new_parts` implementation and the saved G80 recovery copy. A field-by-field
preflight compared the generated recovery rows with that saved copy after
normalizing schema defaults; it permitted only the selected mount difference,
the separate budget, CAD caches and the identified recovery-derived masses.
Other part fields and top-level fields, including the recovery netlist, had to
match. For the nine volume-derived recovery components, a post-export check
matched the retained masses to regenerated shape volumes and the study densities
exactly at the recorded floating-point precision; the separately specified board,
component, battery, switch, band and residual allowance masses retain their
original estimate bases. The historical recovery copy's caches are stale under the current CAD
generator, so changed-part properties were regenerated from actual shapes and
the complete candidate was revalidated normally before export. Original records
and geometry were not overwritten. Source hashes before and after execution
are recorded in `record.json`.

The full **4.620 g** added-annulus upper budget remains a separate
accounting component within the 52-part package. Its idealized representation is excluded from the rigid
collision screen. It is a conservative mass/inertia bound, not a measured glue
volume, wet area, adhesive coverage, bond stiffness or load path.

## Mass, stability and preliminary guide screen

The recovery package adds **4.765137 g** to the mount-only candidate. The sum of
all loaded part masses equals **748.569320 g**; the part-level mass, axial and
lateral CG and local inertia tensors are in the reconciliation file. Loaded and
burnout totals and complete vehicle tensors are in the execution record. With
the separate full **50 g** point allowance at the aft 1.212 m station:

| State | Mass | CG from nose | Static margin |
| --- | ---: | ---: | ---: |
| Loaded, no growth | 748.569 g | 792.220 mm | 1.726 cal |
| Loaded, 50 g aft growth | 798.569 g | 818.503 mm | 1.328 cal |
| Burnout, no growth | 686.069 g | 760.902 mm | 2.201 cal |
| Burnout, 50 g aft growth | 736.069 g | 791.544 mm | 1.736 cal |

CP is 906.140 mm in the existing preliminary model. Growth tensors are saved in
`mass-reconciliation.json`: the calculation applies the parallel-axis theorem
for a 50 g point mass at 1.212 m and zero lateral offset to each complete vehicle
tensor. This is one specified growth location, not a sweep of all possible
as-built changes.

The existing preliminary guide screen gives **16.60 m/s** under its 0.85 thrust,
constant loaded mass plus full allowance, vertical guide and modeled drag and
friction assumptions. It is not a new flight simulation, field guide-length
confirmation or measured result. The original CAD-only packet did not request an independent static reference,
so its recorded preliminary benchmark remains false. A subsequent separate
[static-reference record](../build/wo03-g80-integrated-candidate-v1/static-reference.json)
on this exact identity passes the independent preliminary static benchmark.
The later [same-package flight check](wo03-g80-integrated-flight.md) passes
nominal apogee/time agreement and the specified guide cases; the older mount-only
flight result is not transferred to this changed mass distribution.

## Nominal recovery-interface intersections

The screen used the reconstructed rigid solids and the existing explicit
recovery contact-pair exclusions, checking pairs involving changed recovery
parts. No unexplained positive-volume intersections above the existing
0.05 mm³ cutoff were found. Three named excluded pairs had positive overlaps:
body upper/switch **129.392 mm³**, avionics bay/sled fasteners **58.905 mm³**,
and switch/doubler **409.113 mm³**. These are modeled interface overlaps, not
proof of fit, contact load transfer or manufacture. Soft stowage and distributed
mass budgets were excluded. Wire and connector protrusions, tolerances, service
sweeps, switch duty, board pressure path and physical installation were not
verified by this check.

## Execution and remaining gates

One CPU was requested via the environment and an OCCT pool of one; OS affinity
was not set. One child completed within its 120 s wall cap, with 11.38 s wall
and 14.35 s process CPU reported; no retry or cap increase was used. The
configured total packet budget was 600 CPU s. Current source checksums and
candidate identity are retained in the execution record. Ruff and Black checks
passed for the new script.

Switch DC rating, exact connector polarity and pressure-port keepouts, carrier
and recovery load path, fin root/flutter, thermal qualification, tolerance and
physical tests remain open. No thermal or FEA solve, new flight/reference run,
physical work or release decision was performed here. The primary retains the
engineering adoption decision and the existing WO-03 and later release gates.

The [current G80 closure table](wo03-g80-current-closure.md) retains attachment, interface overlaps, thermal and recovery/fin limitations. The proposed C&K switch is later component research, not a replacement already present in this frozen geometry.

Published [same-package evidence](../runs/wo03-g80-integrated-package-20261101T053840103311Z/record.json) retains exact CAD/mass/static/flight compact records and their hashes. Generated geometry and full telemetry remain local. The 52-part identity is a proposal; working vehicle and release status remain unchanged.
