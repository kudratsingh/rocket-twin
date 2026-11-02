# C1: coupled aft mass and stability revision

**Selected direction for the next integration preflight:** a closed G11
receiver with counted local sockets/hardpoints and three swept, tapered fins,
without nose ballast or equipment relocation. Calculated full mass is
**1129.807g including the separate50g**, balance point879.798mm and aerodynamic
force location966.828mm. The loaded/burnout static margins are**1.319/1.546cal**
against1.0. The additional20g-aft plus motor-CG probe gives1.206cal loaded.

This is a credible **preliminary mass-and-balance direction**, not an accepted
structure, CAD assembly, aerodynamic performance optimization or flight package.
Socket/cap/body strength, local buckling, heat, finished harness, installed fins/
flutter, exact motor and launch equipment remain open. No active vehicle, saved
CAD or frontend geometry was changed. The previous S3 findings remain visible.

## Required balance point and comparison

Nose-to-aft station increases toward the tail. Centre of gravity is the
mass-weighted balance point. Centre of pressure is where the simplified
small-angle aerodynamic restoring force acts. Stability margin in calibres is
`(CP−CG)/body diameter`; one calibre is66mm here. Thus the required balance
point is `CG≤CP−66mm`, rather than a universal fixed CG station.

With the unchanged S3 fins, CP906.140mm requires **CG≤840.140mm**. S3's892.599mm
needs52.459mm forward shift, or0.062931kg·m of first-moment correction. C1's
new fin geometry recalculates CP to966.828mm, so the same1.0 requirement becomes
**CG≤900.828mm**. The selected879.798mm has21.030mm computed margin to that
limit; the combined illustrative sensitivity has13.563mm. The requirement has
not been reduced.

One independent **CP-only RocketPy1.13.0 check** reconstructs the source nose/
transitions and proposed fin surfaces. It returns966.827598mm, agreeing with
the shared calculation within3.33×10⁻¹⁶m under the existing comparison criterion.
This verifies numerical aerodynamic buildup at Mach0 for those assumptions;
it does not measure real CP or validate complete mass/CG/inertia, drag, large
angles, stability in flight or altitude. The [reference record](../runs/wo03-g80-mass-balance-revision-20261102-v2/cp-reference.json)
used one bounded20CPU/20wall-second case,1.189CPU/2.045wall including import.

All full masses below count50g once, at the unchanged1227mm aft allowance station.

| Arrangement | Full loaded mass | CG / CP from nose | Loaded margin | Severe mean opening screen | Disposition |
| --- | ---: | ---: | ---: | ---: | --- |
| Saved S3, not rerun |1199.622g |892.599 /906.140mm |0.205cal |2531.467N |Retain failed findings. |
| Lighter C1 receiver, old fins |1133.893g |880.303 /906.140mm |0.391cal |2392.764N |Lightening alone does not close balance. |
| Same, plus8g carrier and required nose slug |1193.674g |840.140 /906.140mm |1.000cal exactly |2518.916N |Needs51.781g slug; exceeds proposed cylinder capacity48.858g. Not selected. |
| **C1 receiver + swept/tapered fins** |**1129.807g** |**879.798 /966.828mm** |**1.319cal** |**2384.141N** |Selected preliminary mass/balance direction; no structural/launch adoption. |
| C1 +20g aft and motor-CG+12.8mm |1149.807g |887.264 /966.828mm |1.206cal |2426.345N |Illustrative sensitivity, not a validated uncertainty bound or manufacturer tolerance. |

The selected nominal mass before growth is1079.807g. Its complete replacement
assembly is424.286g,69.815g below S3's494.101g. Strictly below1500g remains the
physical project ceiling, not a target weight. Guide performance imposes a
different conditional limit; approximately1kg is not a universal rocket limit.

## What is lightened or combined, and which functions remain

The source is the saved complete S3 ledger. The original source frame bundle
was already removed once in S3; it is not removed again here. Source body,
avionics, recovery, liner/pads, finish,8g fin bonds, gap/locking/canopy allocations
and all unmodified S3 hardware/shield/service items remain counted.

| S3 item/function | C1 construction/mass basis | Accounting and remaining issue |
| --- | --- | --- |
| Three constant-section channels,214.534g |Closed G11 body,R31.2–32,0.8mm wall,201.8mm long:59.299g gross |Continuous end-to-end force path; no fin-slot material-removal credit. Thin-shell buckling, laminate direction and actual openings are unverified. |
| Channel fin sides/floors and body support |Six100×12×2 side plates26.640g; three100×10.95×2 floors12.155g; six100×2×2 bridges4.440g; three100×10.95×0.9 pads5.469g |Local closed sockets retain tab, side-contact, axial-pin and body-transfer functions. Their supports/bonds/peel cannot be treated as rigid or proven. |
| End-channel cap anchors |Six integral hardpoints/transitions,25g geometry budget |Retains all six cap joints and load spreading. No secondary hot bond or raw-laminate value is credited as a qualified attachment. |
| Channel support for motor-front keys |Three carriers/transitions,12g |Retains three existing5mm pins/keys and forward thrust route. Existing key/cap/hot-bearing findings remain applicable until re-evaluated. |
| New joint/process work |8g additional process/hardware |Additional to retained source/S3 adhesives, fasteners, locks and wiring allowance. Not silently funded from growth. |
| Permanent aft cap with24mm bore |31.6mm bore, same64mm OD/6mm thickness:27.003g versus30.687g |Intended motor passage without removing recovery cap. Real radial passages, edge ligaments, harness and nozzle clearances require geometry checks. |
| One-piece floating annulus/prongs,6.196g |Three independent18.3×6.6×4 G11 arms,2.681g plus3g captive keepers |Arms are removed separately, then29mm motor passes the enlarged bore. Keeps independent retention and3.2mm float/hard-stop function; service/loaded clearance is not yet CAD-verified. |
| Rectangular fin panels |Swept/tapered panel mass110.328g versus114.414g |Only panel mass/first moment replaced. Original CAD residual17.210g and deeper-tab delta11.850g remain once. No free gusset or attachment credit. |

The new receiver components have gross dimensions or explicit local allowances;
the ledger is not measured mass, a reconciled CAD result or a conservative
bound. Full intrinsic inertia remains unavailable; no older tensor is attached
to the changed construction. The closed body changes support and heat paths,
so S3's channel Euler or contact result is not transferred as a C1 pass.

The proposed fins retain120mm root chord and6.35mm plywood thickness, with
90mm span,60mm tip chord and40mm sweep at1080mm. They replace the70mm-span,
120/120mm unswept panels. Panel area drops3.57%, while the modeled restoring
force moves aft. This explains the balance benefit without ballast; it does
not establish lower drag, better altitude or higher practical performance.

The same40kPa/5° screening method now gives per-fin factored force220.759N and
root moment8.830N·m, versus149.421N/5.230N·m before. These increases make the
installed root/socket and flutter work more demanding. The2mm local sides
require real closed-socket support and connection evidence; an ideal clamp,
isolated panel result or mass balance cannot qualify them. No detailed CAD or
stress mesh is admitted solely because the static margin is positive.

## Moving equipment and nose ballast

The source inventory places the main75g electrical group at mean328.8mm, on a
9.045g sled beginning240mm. Independent recovery has its own controller, cell,
switch, mounts and power. The bulkhead occupies225–230mm; a5mm whole-sled shift
is only an illustration retaining a5mm front service gap, not an established
mounting change. It gains merely0.000420kg·m. Even an unbuildable co-location
of all identified equipment/packaging at225mm gains about0.01428kg·m, only23%
of S3's0.06293kg·m deficit. No equipment, growth reserve or recovery power
location is moved in the selected case.

A larger relocation into the nose would need a new mount, wiring/separation,
sensor and packing arrangement. The hollow nose profile alone does not establish
an available electronics bay. It is not justified to move the controls sensor,
switches or separate recovery supply there merely to improve the mass model.

The ballast comparison explicitly adds an8g restraint/carrier at100mm and a
nonmetal slug at75mm before recomputing mass, guide speed and recovery. Its
required51.781g exceeds a24×45mm cylinder at the assumed upper density2400kg/m³
by2.923g. The nominal hollow-ogive radius clears a12mm-radius cylinder by
7.34–16.91mm at its axial ends52.5/97.5mm, but that is only a radial profile
check: packing, insertion, anchoring and opening loads remain unverified.
The selected C1 has **zero added ballast and zero ballast-carrier mass**.

## Guide departure and equipment dependency

All scenarios use the existing source-pinned guide calculation, thrust×0.85,
0.5N friction, Cd0.8,1ms steps and full50g. The shared simulator was not replaced;
no new free-flight campaign was run. These are preliminary vertical-guide
screens without actual pad bending, gust, button friction or flight qualification.

| Scenario |1.5m usable reference |1.8m usable option |1.971m usable illustration |
| --- | ---: | ---: | ---: |
| Lighter receiver / old fins |13.635m/s |14.945m/s |15.644m/s |
| Selected C1 / clipped fins |13.663m/s |**14.975m/s: fails15** |15.676m/s |
| C1 +20g/motor-CG probe |13.526m/s |14.826m/s |15.519m/s |

The selected nominal case requires **1.805867m usable for15m/s**, or
**1.927373m for the separate15.5m/s target**. Under the explicit old-guide/start
loss1.077m these correspond to2.882867/3.004373m clear overall. Those are
calculated needs, not confirmed equipment. Seek an actually verified supported
arrangement with planning margin beyond the nominal1.93m result;2.0m usable
would be a useful planning aim, not a new formal requirement or a claim of access.

Nothing is confirmed at ROC or MDARS. The approximate10ft MDARS listing does
not prove unobstructed3.048m or1.971m usable travel. Actual buttons, start/stop,
release, support, fin clearance and wind limits can change the calculation.
Current CAD is rod lugs rather than1010/1515 buttons. The1.5m baseline remains
unchanged; **C1 fails it**. The previous conditional1.8m option also fails this
nominal C1 at14.975m/s; no rounding or tolerance credits turn it into a pass.
See the [short ROC/MDARS confirmation sheet](wo03-launch-equipment-confirmation.md).

The formal15m/s requirement and15.5 planning target remain separate. On the
illustrative1.971m case the additional20g probe has only0.019m/s planning margin.
That is not evidence of robust equipment access or complete uncertainty coverage.
Reusing the saved unchanged-guide-model mass roots at1.971m, nominal C1 has
90.147g formal /22.509g planning mass headroom. The additional20g/motor-CG
case has70.147g /2.509g respectively. These are conditional arithmetic margins,
not free allocations or measured mass tolerances. Necessary root reinforcement
can quickly consume the planning margin. With CP fixed, the latter case can
take only about47.8g more at the1227mm tail before reaching1cal; this is also
an edge calculation, not a design target or validation of unknown reinforcement.
If a club can only confirm1.5m usable, this design needs further mass/performance
work; the current calculations do not authorize a longer baseline.

## What this increment closes, and what stays open

The **specified mass-and-static-balance screen** now has a positive candidate:
1.319cal nominal and1.206cal in the stated additional sensitivity with full
growth. That closes the immediate calculation problem of how to obtain the
required balance without an uncounted nose weight. It does not close the full
WO-03 static/flight benchmark or any physical qualification.

The next bounded preflight must verify the real thin-body/socket/hardpoint
construction, changed fin loads, cap reaction signs/tension and actual independent
motor extraction. Preserve S3's adverse cap/barrel/contact/body results, the
required thermal matrix including300°C/contaminated foil/35°C and45°C substrate
screen, finished hot harness uncertainty, independent recovery integration and
installed deflection/flutter gates. Repeat complete mass/balance/guide calculations
if reinforcement, wall thickness, hardware or actual button mass changes. Stop
before detailed geometry if required reinforcement destroys those margins; do
not restore an assumed rigid support or remove a function for weight credit.

G80 remains first. G54 needs its own187mm motor envelope/support/retention,
source and California/stock evidence. G12's moving module and PID-to-RL work
remain committed and separate. No C1 result transfers to them. All physical,
purchase, paid-run, WO-10 review and flight-release gates remain unchanged.

[Specification](../configs/studies/wo03-g80-mass-balance-revision.yaml),
[saved v2 record](../runs/wo03-g80-mass-balance-revision-20261102-v2/record.json).
Four scenarios/three guide probes and two selected-case travel roots used one
CPU,0.605CPU/0.689wall seconds under the declared20CPU/30wall budget. An initial
configuration-key validation stop occurred before numerical work and is preserved
in v1; one explicit key-wiring correction left all candidate inputs unchanged.
No stopped S3, native analysis or12-combination motor campaign was rerun.
