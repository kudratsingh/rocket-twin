# G80 captive keeper: nominal study stopped at nut constraint

The first and only keeper geometry child stopped at its predefined nut-constraint
gate. The direct washer-to-bridge probes returned **54.538 mm² per axis**, but
a 5° nut-rotation probe produced only **0.008278 mm³** of keeper intersection
per nut, below this study's **0.05 mm³** discrimination threshold. The study
therefore cannot establish the proposed anti-rotation function. The small
positive intersection is not proof that the nut rotates freely, nor is this a
torque, strength or manufacturing-tolerance result. No retry was performed.

The [stop record](../build/wo03-g80-keeper-geometry-v1/progress.json),
[preflight and source hashes](../build/wo03-g80-keeper-geometry-v1/preflight.json)
and [execution status](../build/wo03-g80-keeper-geometry-v1/execution-status.json)
are local ignored build artifacts. The isolated study is defined by
[wo03-g80-keeper-geometry.yaml](../configs/studies/wo03-g80-keeper-geometry.yaml)
and [wo03_g80_keeper_geometry.py](../scripts/wo03_g80_keeper_geometry.py).
Nothing here changes the active configuration or regenerates a valid complete
vehicle.

## Inputs and checks reached

The source was the frozen 52-part G80 identity
`62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009`
and the previous nominal bridge/guide geometry. Before this first keeper child,
the primary chose **no M2 washers** and three **integral G11 annular pads** on
the keeper, nominal OD 4 mm, ID 2.2 mm and height 0.1 mm. The broad aft face
would be recessed from 4.1 mm stock; flatness, machining and pad compression
are not established. M2 screw heads and nuts bear directly on G11 in this
nominal model; bearing, preload and locking are unqualified. The nominal 10 mm
M2 screw gives 2.3 mm protrusion through the proposed 6.1 mm stack and 1.6 mm
nut; missing length tolerance precludes a minimum-protrusion claim.

The nominal preflight records the axial and radial envelopes of the M3 screw,
washer, nut, stepped keeper pocket, M2 screw, nut and pad. It checks the
specified 0.5 mm keeper front wall, 0.1 mm keeper/bridge gap and nominal pad
clearance to the ring boundaries and adjacent pocket. The 1.1 mm counterbore
depth is a proposed pocket dimension, not a washer tolerance: the M3 washer's
source thickness is consistently 0.7–0.9 mm. Its maximum OD is unavailable, so
these are not worst-case fit checks.

The child passed its flat blind-pocket/wall/bearing fixture and checked the
imported source solids before constructing the candidate. The fixture's
numerical values were not persisted after the later stop; passing is established
by the execution reaching the later gate. It constructed the separate keeper,
modified source rear-ring band, retained the source rails and bridge/guides, and
modeled the nominal M2/M3 envelopes. It then found no screened positive-volume
candidate/reference intersections above 0.05 mm³. Soft-stowage and distributed
budget shapes were excluded, and source/reference pairs were not rescored.
This nominal screen is not a tolerance or full-assembly validation.

The 0.5 mm forward dropout probe produced **3.203702 mm³** of keeper
intersection per nut. This demonstrates interference for that one imposed
translation in the nominal model; it does not prove robust retention under
other motion, wear, loads or manufacturing variation. A 5° imposed nut rotation
produced the small intersections stated above, causing the stop. Integral-pad
contact, screws, material surfaces and hardware were not physically validated.

## Work not reached and remaining decisions

The stop occurred before the pre-shell insertion and motor-service samples,
final individual mass report, and STEP export. Those outputs are **unavailable**,
not zero or passed. The exact rear-ring removal volume and new keeper mass were
not persisted at the stop; a net replacement mass, full vehicle mass, CG and
inertia cannot be claimed. The M2 screw/nut nominal average is 1.32 g for three
sets, while direct bearing and locking remain unqualified. The old unitemized
7 g M3 hardware budget cannot be assumed to be a precise removable set. Retain
the separate 4.620 g annular upper budget, 12 g finish and 50 g growth
allowance without double counting.

The single child ran with hard limits of 120 CPU s and 120 s wall; the observed
parent wall time was **5.404 s** and child CPU was **4.450 s**. OCCT pool one
and single-thread library settings were requested; OS affinity was not set.
Before/after hashes match for the inputs enumerated in the execution status.
The earlier retention attempts were a separate stopped packet; their outputs
remain unchanged. Ruff and Black passed for this new script.

The primary must decide whether a better-defined nut anti-rotation geometry,
a more discriminating probe or physical evidence is warranted. No new layout,
second keeper attempt, thermal/structural solver, flight simulation, purchase
or physical action was performed. Switch DC duty, material properties, keeper
and bridge strength, shell assembly and service, thermal effects and all
flight-release gates remain open.

[Published compact keeper evidence](../runs/wo03-g80-keeper-20261101T063807744500Z/record.json) retains the stop, source-identical continuation, source snapshots, fixture values and resource accounting; native geometry stays local. No full engineering or physical acceptance follows.
