# Current G80 architecture decision

**Prefer A, the integrated through-body motor/fin can, for the next bounded
connection study. Neither arrangement is admitted to detailed vehicle CAD or
finite-element analysis.** A removes161.498 g from C1 and removes the C3
end-node/motor-arm mechanism from the proposed topology. It still fails the
unchanged1.5 m guide requirement, and actual hot joints, installed flexibility
and supplier fit remain unresolved. B is27.503 g heavier and its declared
movement screen is less promising. No third arrangement or local bracket
iteration follows this packet.

This decision preserves substantial custom body/fin/recovery construction,
maximum practical conventional performance and the committed G12 PID-to-RL
track. G80 is first; G54 and G12 do not inherit this study. Active vehicle
specifications and the1.5 m launch baseline are unchanged.

## Frozen choices and execution

The [A/B specification](../configs/studies/wo03-architecture-space-mass.yaml),
[executed record](../runs/wo03-architecture-space-mass-20261102-v1/record.json)
and exact executed config/script preserve both choices made before execution.
One20-CPU/30-wall-second, one-thread packet used **0.431 CPU /0.507 wall seconds**.
It read saved fin construction/panel evidence and guide-model mass roots, then
used the existing shared guide calculation for twelve mass/travel cases. It
executed no CAD, FEA, thermal solver or free flight. Stopped R1/C2/C3 outputs
remain untouched. Full inertia remains unavailable; no flight comparison was
fabricated from point-mass ledger entries.

The [source packet](wo03-architecture-source-packet.md) separates manufacturer
construction precedents from typical material data and usable joint allowables.
Its20-source budget was exhausted with16 readable and4 unavailable documents;
it obtained no finished hot root/eye/bend/pocket qualification data.

## Functions and protected space before supports

Both proposals replace duplicated paper aft body/inner receiver, local sockets,
old end blocks, cap hardware and front-key/motor-retention mechanism with named
new functions. The exact561.441 g removal ledger refers to real C1 component
IDs, not an arbitrary mass target. The motor, upper assembly, canopy,
independent recovery controller/cell/switch and retained primary backbone stay
counted. Every replacement skin/core/dense root, tube, ring, cap, cuff, bridle,
retainer, bond, pin/hardware and process allocation is counted.

Both reserve a15.8 mm radius body/liner passage from station1069 to1195 and a
23 mm radius threaded-retainer/service envelope from1195 to1227. The latter
is a planning reservation, **not a verified purchased-part drawing**. Forward
bridles run900–1016, leaving179 mm axially before the retainer reservation.
This avoids placing another fixed end support through removable motor hardware.

Three forward eyes pass through actual13×1.4 mm cap slots, loop over6 mm
radius rear-face saddles and return forward. Their two legs lie at local
tangential±6 mm, radial centre24 mm, with12.7 mm webbing width. They replace
the old aft-running loops; their cut length and full sewn lap are counted.
Changing the former9 mm bend to6 mm is **not a capacity improvement claim**:
finished hot seam/bend capacity remains unavailable. The entire primary
backbone/termination requirement retains the full recalculated opening case.

The cap/cuff is a proposed integral G11 component. Real clearance windows at
1010–1018 and60/180/300 degrees leave half the cuff circumference at that
section. Those windows are excluded from strength/bond area and remain real
thermal openings; no material-removal mass credit is taken. Supports do not
silently occupy the harness route. The [function allocation and concept
drawings](wo03-architecture-function-allocation.md) show the actual connections
and their incomplete evidence.

## Complete comparison

Every total includes the separate **50 g at1227 mm**. The adverse case adds a
further20 g there and the existing12.8 mm motor-CG probe. That probe is not a
supplier tolerance. The model CP is966.827598 mm; the external C1 fin planform
and66 mm diameter are retained for this early screen, not aerodynamic validation
of a fabricated assembly.

| Case | Subtotal + separate50 / total, g | Loaded / burnout CG, mm | Loaded stability, calibre | Departure1.5 /1.8 /1.971 m, m/s | Severe recovery mean, N |
| --- | --- | --- | ---: | --- | ---: |
| A nominal |918.309 +50 /968.309 |844.352 /824.229 |1.855688 |14.913561 /16.341300 /17.103243 |2043.345 |
| A +20g / motor-CG |938.309 +50 /988.309 |853.756 /833.838 |1.713205 |14.742991 /16.154914 /16.908448 |2085.549 |
| B nominal |945.812 +50 /995.812 |852.518 /833.534 |1.731968 |14.680247 /16.086389 /16.836835 |2101.383 |
| B +20g / motor-CG |965.812 +50 /1015.812 |861.506 /842.671 |1.595779 |14.516331 /15.907334 /16.649682 |2143.587 |

A removes561.441 g and adds399.943 g; net−161.498 g and first-moment
change−0.176408 kg·m. B adds427.446 g; net−133.994 g and first-moment
change−0.145054 kg·m. New mass and mass-times-position come from the **same
ledger**. Rotation resistance is not replaced by zero: full intrinsic tensors
are unavailable.

Saved1.5 m total-mass roots are958.397937 g for formal15 m/s and903.854132 g
for separate15.5 m/s planning. A nominal/adverse headroom is therefore
**−9.911 /−29.911 g formal** and **−64.455 /−84.455 g planning**. B formal
deficits are37.414/57.414 g. All longer-guide results remain conditional;
passing their arithmetic confirms no equipment, body, joint or flight gate.
See the [unsent ROC/MDARS confirmation sheet](wo03-launch-owner-confirmation-20261102.md).

Opening demand keeps20.4 m/s,0.3 m stopping travel, gravity and DF3 exactly
once, with the prior1782.253 N study floor retained. These are prescribed
energy-equivalent means, not measured snatch peaks or justified equal sharing.

## What the connection calculations establish

| Check, worst mass case | A | B | Acceptance boundary |
| --- | ---: | ---: | --- |
| Window-reduced cuff axial stress, hot provisional |21.209 MPa |21.800 MPa |Below unchanged estimated25 MPa; scalar/directional installed qualification remains open |
| Effective cuff/body lap mean shear |0.387 MPa |0.397 MPa |Below unchanged1 MPa shear screen; no peel acceptance follows |
| Eccentric lap edge normal-demand proxy |0.0515 MPa |0.0530 MPa |Normal/peel allowable unavailable |
| Fore-cap effective circumferential width needed at25 MPa |111.229 mm |114.325 mm |Actual finite annular spreading is unknown; no rigid cap or equal loop sharing |
| Fin-root normal reaction |821.222 N outer /−600.464 N inner |2854.095 N positive half-depth contact |Factored source force/root moment transported through actual lever arms; no second DF3 |
| Root interface scalar demand |0.684 MPa over1200 mm² |8.155 MPa over350 mm² |A reaction includes normal/peel;1 MPa **shear** is not its allowable. B bearing capacity unknown |
| Panel + play + ideal-tube movement proxy |0.882 mm |1.226 mm |Not installed motion: intact tubes and rigid fore support deliberately overestimate stiffness; slots, finite rings/laps/coupler remain |
| Cuff/body cold / differential-hot minimum gap |0.200 /0.116775 mm |Same |Above0.1 under specified CTE/tolerance bounds; actual root moisture/hot fit and supplier envelope remain unavailable |
| Forward bridle / outer-can radial gap after0.7 mm losses |0.508 mm |Same |Concept reservation only, not CAD insertion/deployment proof |

A's motor-tube contribution is an **optimistic coextensive parallel-tube
reference**; the actual inner tube is shorter and transfers through finite
rings. It cannot clear the1 mm installed requirement. B credits no fin torsion
restraint from its removable motor cassette. These models must not be promoted
to measured stiffness or installed flutter results.

The only purchased-retainer hypothesis is [Estes009750](https://estesrockets.com/products/pro-series-ii-29-mm-motor-retainer-set),
whose manufacturer describes an ABS threaded retainer for most29 mm composite
motors. The20 g retainer and5 g adapter/bond are **allocations**; exact mass,
threads, mounting diameter, nozzle/shoulder geometry and hot450 N reverse-load
capacity were not supplied. Manufacturer topology does not qualify this exact
G80 fit. The [Ventris instructions](https://d37tikmwcb2tc.cloudfront.net/rocketry/file_attachment/Estes_009701.pdf)
provide a second construction precedent for fin/ring/motor-tube and epoxy
retainer integration, without our loads or temperature evidence.

Required300°C case/contaminated foil/35°C ambient, burn plus soak and45°C
substrate screening remain. New tubes, contacts, adhesives and cuff windows
change heat paths. Existing liner/shield mass remains counted; exact thrust-ring
and liner-end geometry and all new temperatures remain unresolved. No thermal
benefit is claimed.

## Retained-interface follow-up (no new construction case)

A separate [read-only interface audit](wo03-architecture-interface-audit.md)
finds a further concrete cold-fit failure:64.0mm retained model coupler in the
64.4mm proposed bore has0mm minimum radial gap under the declared±0.1mm per-
surface screening bounds, versus0.1mm required. Hot/moisture dimensions remain
unknown. The derived63.8mm maximum nominal coupler OD is a dimensional bound,
not an adopted part or another mass/strength case. This finding does not rewrite
the immutable A/B results or create a third arrangement.

## Admission decision and next bounded action

**No installed engineering requirement closes.** A is the coherent lower-mass
direction, not an accepted vehicle. B is stopped in this packet rather than
receiving automatic reinforcement. Before complete CAD admission, A needs:

1. A credible full-growth guide budget: at least29.911 g additional saving for
   the adverse formal1.5 m case, with useful margin, or an explicit baseline
   decision after real usable-guide evidence. Conditional1.8 m is not adopted.
2. A bounded fore-cap/root connection study establishing finite load spreading,
   peel/bearing demands and support flexibility with actual joints. The needed
   width/capacity figures above define the question; another isolated pad does not.
3. Exact G80/retainer mating and hot-fit data, and a source/test basis for the
   finished6 mm-bend bridle and hot joints. Later owner measurements cannot
   retrospectively waive a present failed calculation.

The specific architecture choice is whether a conventional G80 package can use
a confirmed supported guide with enough **usable travel**, while keeping a
structural motor/fin can, or must first earn another≈30 g vehicle-wide saving
for the existing1.5 m adverse case. Do not chase that deficit by thinning
unverified sockets or consuming the50 g allowance. Continue frontend/source/
test-plan work independently. All owner physical, purchasing, paid-run,
firmware-review and flight-release gates remain.
