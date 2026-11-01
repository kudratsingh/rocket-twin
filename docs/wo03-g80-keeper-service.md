# G80 keeper service: nominal geometry completed, qualification open

The unchanged proposed keeper/bridge geometry now has completed **nominal
pre-shell insertion, cap removal and motor removal samples**, with separate
STEP exports and component masses. It is not a regenerated complete vehicle,
a tolerance/strength pass or physical build authorization. The source working
vehicle and preview remain unchanged.

This continuation follows the preserved [stopped keeper trial](wo03-g80-keeper-geometry.md)
and [independent rotation bound](wo03-g80-nut-rotation-bound.md). The original
5° probe remains inconclusive at the unchanged 0.05 mm³ discrimination threshold.
That diagnostic was not a project requirement for zero angular play at 5°.
The separate fixed-axis nominal argument predicts a barrier before ±15°;
the reconstructed BReps give **1.406745 mm³** overlap at each ±15° probe and
**3.203702 mm³** at the 0.5 mm forward-dropout probe, at all three axes.
These are geometric observations, not torque capacity or a proof against
translation, tilt, wear or every possible escape path.

## Exact source and verification

The source is the 52-part proposal
`62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009`.
The continuation compared the exact geometry-construction source blocks to the
earlier executed recipe and reproduced its 5° and dropout results within the
declared numerical tolerance. No physical dimension or collision-volume
threshold changed. Three washer/bridge probes again give **54.538048 mm²**.

The independently calculated blind-wall fixture volume is
`pi*(4²−1.8²)*0.5 = 20.04336113 mm³`; the calculation gives the same value
to recorded precision, with zero bore intrusion. The known annular bearing
area is `pi*(4.5²−1.7²) = 54.53804847 mm²`, matching the recorded probe.
Fixture values are retained separately from the progress file.

The local [record](../build/wo03-g80-keeper-service-v1/record.json),
[fixture](../build/wo03-g80-keeper-service-v1/fixture.json),
[preflight](../build/wo03-g80-keeper-service-v1/preflight.json), and
[execution status](../build/wo03-g80-keeper-service-v1/execution-status.json)
identify inputs and limitations. The [partial study assembly](../build/wo03-g80-keeper-service-v1/study-assembly.step)
and its separate part STEPs are ignored generated artifacts, not new active
vehicle exports. Purchased fastener shapes remain simplified envelopes.

## Assembly and service coverage

| Check | Result | Coverage and limit |
| --- | --- | --- |
| Nominal part/reference solid intersections | No screened overlap above 0.05 mm³ | Actual study pairs only; no manufacturing minimum, flexible wiring or load qualification. |
| Pre-closed support/keeper into bare aft shell | No sampled blockers | 61 axial positions from −300 to 0 mm, 5 mm spacing. Fins, motor, liner and main cap screws are installed later. Their later installation/bond access is not established here. |
| Cap removal from aft, main screws removed | No sampled blockers | 10 positions from 5 to 50 mm against the fixed studied parts. Unthreading torque, tools and hand access are not modeled. |
| Motor removal from aft, cap/main screws removed | No sampled blockers | 29 positions from 5 to 145 mm against the keeper, bridge, mount, shell, liner and fins. Actual supplier case/nozzle features and intervening positions remain unverified. |
| Nuts remain behind bridge during cap service | Nominal rotation/dropout barriers observed | Fixed-axis probes and closed-form bound only. Pocket tolerances, keeper deformation, anti-rotation torque and M2 locking remain open. |

Sampled positions are not continuous swept-volume proofs. The shell-blocked
radial nut-removal path from the earlier study remains blocked: this design
instead installs the captive nuts before the shell is bonded. Nut replacement
may require aft-module bench disassembly or replacement. No easier repair path
is claimed.

## Component accounting and structural consequence

| Component result | Calculated mass |
| --- | ---: |
| Actual old rear-ring material removed while retaining rail overlap once | 4.059293 g |
| Remaining plywood mount and guides | 40.448195 g |
| Separate 4 mm G11 keeper, including integral pads | 15.409675 g |
| G11 bridge after M2 holes | 10.176847 g |
| Three M2 screw/nut sets | 1.32 g supplier-listed nominal average |

The three proposed M3 stacks are separately 8.52 g supplier nominal. They are
not added as a second physical set to the old unitemized 7 g allowance. The
complete replacement ledger, locking provisions and adhesive allocation remain
unresolved, so **no full mass/CG/inertia or updated flight result is claimed**.
The full separate 50 g allowance, 12 g finish allocation and 4.620 g annular
upper budget remain explicit. Material densities and purchased masses are
estimates/listing values, not weighed hardware.

The keeper's integral G11 pads touch the bridge and the M2 closure can transfer
preload or operating reactions. Excluding keeper stiffness from a diagnostic
model does not establish zero real keeper load. Bridge bending, tab shear/peel,
rail/ring/body compliance, nut/washer bearing, fastener grade and preload, G11
directions/hot properties and thermal behavior remain open design items.

## Resource and stop record

One service child completed in **15.256 s wall / 13.979 s CPU**, below its
120 s wall and hard 120 CPU s limits. Including the prior keeper child gives
**18.428 s tracked child CPU**; this is not a claim that parent/setup CPU or
the earlier retention packet's missing CPU is zero. The geometry source and
inputs matched before/after. One OCCT worker and one-thread libraries were
requested, without an OS-affinity claim.

A source-comparison guard first stopped **before any child** because its text
search matched a preflight marker rather than the child construction block.
The guard was scoped to that child block and duplicate fixture-file output was
removed; the physical construction blocks still compare exactly. The stopped
guard source/log and the original geometry failures remain preserved. There
was one native continuation, no further native retry, and no FEA, heat, flight,
purchase or physical work in this packet.

[Published compact keeper evidence](../runs/wo03-g80-keeper-20261101T063807744500Z/record.json) retains the stop, source-identical continuation, source snapshots, fixture values and resource accounting; native geometry stays local. No full engineering or physical acceptance follows.
