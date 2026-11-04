# RP1 AD1: finished attachment definition and test decision

**Decision: retain balanced RP1 v2 as the preferred research direction. AD1 v2
defines one sacrificial attachment experiment; it is not an adopted vehicle or
a release to manufacture the flight rocket.** The exact cord products and a
repeatable proposed termination are now specified. Finished strength remains
unavailable, and the changed fin's optimistic screen fails before joint
flexibility is added. Do not perform detailed analysis of that unchanged fin.

Final identity: `G80-F2-RP1-AD1-definition-v2`,
[specification](../configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml),
[definition](../configs/studies/rp1-attachment-definition-v2.yaml),
[record](../runs/wo03-rp1-attachment-definition-20261103-v2/record.json).
[Drawings and complete ledger](../output/rp1-attachment-definition/index.html)
are dimensioned concepts, not whole-vehicle CAD. All stations below are mm aft
from the nose tip; the first of three fins defines angle0, then120/240degrees.
F2, F2-C1, RP1 v1, balanced RP1 v2 and AD1 v1 remain frozen historical sources.

## 1. Exact products, finished ends and available evidence

| Item | Definition and installed quantity | Physical mass / capacity status |
| --- | --- | --- |
| Apogee30327 | Buy minimum10ft; cut **6.5ft /1981.2mm** for the leader, leave3.5ft uninstalled. Nominal advertised diameter0.137in; proposed incoming maximum3.8mm is not a supplier tolerance. | **16.25g installed budget**, scaled from the frozen2g-per-foot interpretation plus25percent. Listing does not explicitly confirm the per-foot basis. Neither finished mass nor a finished knot rating is established. |
| LOC NW-12, variant39778657730751 | **Uncut12ft /3.6576m nominal,3/8in tubular nylon with both original factory-sewn loops**; listed$12.39 and availableflagtrue on2026-11-03. Loop-bearing length, thread/stitches and tolerances unknown. | **55g budget**, not a product measurement.1020lb tensile label has no examined raw-versus-sewn test scope. Commerce `weight:68` is inconsistent metadata, used only as a hypothetical sensitivity, not a physical bound. |
| Proposed proximal end | Figure-eight-on-a-bight eye, reeved round the motor tube as a choker. Locate knot between fins at60deg. No epoxy/CA on working rope or knot. | A **design choice for representative tests**, not an exact-product manufacturer-approved or qualified termination. No knot-efficiency percentage credited. |
| Proposed accessible end | Figure-eight-on-a-bight eye; loop-to-loop hitch to the intact proximal factory nylon loop. Distal nylon loop stays intact. | No supplied strength, bend, cyclic seating or unequal leg-load characterization. No metal connector removal credit taken. |

The [bounded documentation packet](wo03-rp1-cord-documentation.md) distinguishes
manufacturer storefront data, kit procedures and actual strength evidence.
Apogee's1500lb class Mega Mako procedure demonstrates another knotted wrap,
but different cut-part IDs and epoxy-coated terminations do not qualify ours.
Raw Kevlar label1500lb≈6.67kN and nylon label1020lb≈4.54kN are **not allowable
finished loads**; do not compare them to demand as a passing factor of safety.
The [supplier questions](wo03-f2-recovery-supplier-questions.md) remain UNSENT.
Hardware is unpurchased; there is nothing for the owner to measure now.

Reserve **300mm of raw leader at each end** for knot, eye and tail, including
minimum100mm tails and a distal40mm minimum clear bearing-length eye. These
are manufacturing reservations, not validated knot-consumption formulae. Tube
wrap centreline consumes110.487mm at the3.8mm cord envelope; the guarded route
from1072.2 to the160mm mouth plus20mm detour consumes932.2mm. Remaining reach
is **338.513mm outside the mouth**, versus the provisional300mm service target.
The frozen6ft allocation would give186.113mm with these same reservations and
would fail that target. The extra half-foot is counted, not free spare length.
If dressing either knot consumes more, tails may not be shortened to force a
pass: stop the dry-fit article and record the measured conflict.

## 2. Connection, protection and service

The tube is1055–1220, nominalOD31.369mm. The forward ring is1060–1072.2,
OD64.4/bore31.9/thickness12.2mm, from two6mm plies and0.2mm glue. At60deg,
one4.5mm-wide by5mm-radial U-notch has proposed±0.05mm cut control and2mm
rounded entrance/exit edges sealed within the existing1g finish allocation.
The radius is build intent; no exact-cord minimum bend diameter was found.
The width-only minimum bare-cord clearance is0.300mm **per flank**, using
maximum3.8mm cord and provisional0.05mm environmental closure. It is not
a checked curved passage, compressibility, moisture or moving-rope result.

The closed choker lies immediately aft of the ring,1072.2–1077.0. A
**50axial×20tangential×14radialmm knot reservation**, r16.5–30.5 and
z1077–1127, lies between fins. Its outer corner has only0.414mm nominal cold
clearance to the body; supplied stock ovality, swelling, actual dressed knot
and slack-rope movement remain unresolved. This box is not an actual knot CAD
or a proof that the cord cannot migrate into a fin. Inspect and photograph
both dressed topology and clearances before any closure of a test article.

The new80mm folded aramid sleeve ends **ahead of the ring:980–1060mm**.
Minimum internal flat width8mm,2g mass counted. Its exact textile/finish,
fold thickness and tie construction remain source/test dependencies. It may
slide for inspection while accessible; loose textile ties are included in that
budget, without assigning them structural capacity. It **must not occupy the
4.5mm notch**. AD1 v1's1032.2–1112.2 sleeve envelope is rejected for that
reason. The final correction reuses valid guide/fin arithmetic, moves only
the2g sleeve52.2mm forward and records the corresponding first-moment change.
No heat or abrasion pass follows: the bare rounded passage, sleeve ends,
mouth guard and knot need the unchanged required thermal/chafe verification.
The existing4g mouth guard,6g canopy blanket,4g anchor-lock process and1g
notch finish stay separately counted; none is a qualified structural anchor.

**Recovery force route:** canopy bridle → existing provisional distal
connector/swivel junction → distal sewn nylon loop → nylon → proximal sewn
loop/leader eye hitch → leader → choker/ring contact. From there force enters
the annulus locally and its inner/outer bonds, mount tube and continuous body;
actual partition depends on their stiffness and contact. The nose eye has a
separate branch at the distal junction, not an assumed equal half of the load.
The retained9g two-connector allocation and nose9g eye/washer geometry remain
unresolved products/capacities; AD1 does not claim a complete flight recovery
hardware selection. Tautening and snagged/slack branches may load one path first.
No half-force, uniform circumference pressure or equal bond sharing is credited.

Use the severe20.4m/s over0.3m energy/weight proxy withDF3 **once**. Final
nominal/adverse whole proxies are1972.104/2014.309N; the retained-body proxies
are1358.727/1400.931N. These are factored mean mechanism screens, not measured
inflation peaks or evidence that the nylon supplies0.3m stopping distance.
Preserve the separate snatch/inflation/normal-deployment review and all original
cases. An experiment may characterize the mechanism; it cannot silently lower it.

Assembly/inspection sequence:

1. Confirm labelled stock, mass, dimensions, ply direction, lot and conditioned
   bond process. Dry-cut the tube/rings, round/seal the notch and make witness
   marks. Document actual bore/bond thickness; generic catalogue nominal is
   not incoming acceptance.
2. Dress both leader eyes and tails on the actual tube, reeve the choker, verify
   passage/knot/fin envelopes and external reach. Fit the sleeve ahead of the
   ring, keeping adhesive off working fibers. Record this **before** any ring
   bond or inaccessible closure.
3. Bond forward ring to mount, install the assembly through body access, then
   integral fin/tab blanks and continuous root joints. The aft ring remains
   off until tab fillets, harness route and cure witnesses are inspected.
4. Install aft ring/bonds, inspect by aft opening and then body mouth; use a
   borescope where direct sight is lost. Motor bore and independent retainer
   remain unobstructed. Exact78010/12912/19002 seat/liner contact is still a
   separate supplier hold, not resolved by this leader geometry.
5. Bring the junction outside the mouth to separate/replace NW-12; inspect
   sewn ends, both eyes, tails, mouth guard and canopy pack. The permanently
   buried motor-tube choker **cannot be replaced without destructive access**
   in this architecture. Inspection access is limited; suspected hidden damage
   retires that assembly. Do not claim a fully replaceable anchor.

## 3. Changed fin support: executed failure, not transferred acceptance

Panel roots1075–1205; integral tabs1080.2–1189.6; aft ring1190–1196. The
forward ring is now ahead of the tabs. **There is no front tab end/side support
and no direct aft butt contact across the nominal0.4mm gap.** Loads follow the
integral wood tab, continuous tab/mount fillets, two external triangular
gussets and their curved body saddles, body slot edges and aft-end adhesive.
Fore and aft ring bonds support the tube/body with finite flexibility; neither
is an assumed perfect clamp. Reversing fin load exchanges tension/compression.

Nominal filled bond gaps are **0.312mm radial** at the64.4mm ring/65.024mm
body bore and **0.2655mm radial** at the31.9mm ring/31.369mm mount. The tab's
inner flat is15.95mm from axis: its gap to the curved mount grows from0.2655mm
at centre to about0.536mm at the edges of minimum5.8mm stock. These are bonded
regions, not simultaneous air-gap paths or direct wood contact. Actual stock
and adhesive thickness/coverage ranges are not established. The nominal0.4mm
aft tab/ring gap also needs a qualified filled bond, without a fictitious stop.
Each external wedge underside must be fitted to the body's33.401mm outer
radius; a flat unmodified wedge is not a curved saddle. A0.2mm target bond film
there is a proposed process dimension, not a qualified tolerance/allowable.
Existing14g internal,10g outer and4g extra-root adhesive allocations remain
counted reserves; material removed while fitting wedges earns no mass credit.

Declared per-fin demand is8.83N·m, already factored3 at40kPa and5deg incidence;
the associated pressure-resultant screen is331.125N. It remains a conservative
load hypothesis, not a new validated flight envelope. Include torsion/in-plane
and guide/recovery combined cases before installed acceptance; those are not
represented by the one transverse strip calculation.

| Contact/demand calculation | Result | Interpretation |
| --- | ---: | --- |
|15mm force couple for8.83N·m |588.667N | Demand scale; not asserted reaction partition |
|130×15mm gusset/fin face |0.302MPa mean | Edge peaks/wood direction/peel unknown |
|130×6mm gusset/body base |0.755MPa mean normal | **No normal/peel allowable available**; shear1MPa cannot qualify it |
|109.4×5.8mm tab flat, if whole couple enters it |0.928MPa mean | Curved tube/gap/fillets and load direction control; mean shear alone insufficient |
|17.451×5.8mm aft end, if whole331N enters it |3.271MPa mean | Adhesive tension and finite gap, not a compressive stop |
| Forward ring outer full-route envelope |0.568MPa mean shear | Below estimated1MPa shear only; peel/paper/local ring bending unresolved |
| Forward ring inner full-route envelope |1.200MPa mean shear | Exceeds1MPa if that full path is required; partition unverified |
| Paper full-route axial envelope |7.610MPa | Above2MPa provisional paper screen; not an established exact load distribution |

These separate conservative paths are not summed as independent simultaneous
loads and not used to invent an equal split. They expose where joint/property
information is needed. Cord contact pressure, ring annular bending/notch tear,
tube ovalization and interlaminar peel remain unavailable.

The tapered Euler–Bernoulli strip uses **minimum5.8mm stock**, estimated hot
E1GPa/5MPa, spanwise face grain, and an optimistic fully bonded triangular
gusset thickness profile. It gives **7.301MPa maximum and1.805416mm tip
movement**, failing5MPa/1mm. Bare panel is12.115MPa/3.988mm. Numerical
divisions100/400/1600 give1.806792/1.805497/1.805416mm; last change0.00449percent.
The independent uniform-beam integral differs from its closed form by
0.0000391percent. Those establish quadrature consistency only. A finite
root spring K200/500/1000/3000N·m/rad gives4.454/2.865/2.335/1.982mm; no
positive root stiffness can bring this optimistic panel below1mm. Actual ply
orthotropy, gusset orientation, bond slip, body compliance and installed
flutter remain unverified. No stopped mesh campaign was repeated.

One minor dimensional correction is admitted **only to the test definition**:
external slots6.8±0.05mm instead of6.5±0.1. With6.2mm maximum ply and0.05mm
closure, minimum per-flank gap improves0.075→0.250mm against0.1mm. It adds
0.15g epoxy versus an estimated0.125g minimum extra fill; zero paper removal
credit. Moisture/thermal bounds and supplied tolerances remain conditional.
This corrects a cut-width screen, not installed fin strength or motion.

## 4. Complete coupled budget, not separate promising corrections

The55-row ledger counts all prior hardware, adhesives, finish, shields,
electronics and recovery once. Added1.25g leader,2g sleeve and0.15g slot fill
total **+3.400g** versus balancedv2; no removal credit. Physical ledger is
884.549g; full50g growth is added at the1250mm tail separately. Adverse adds
20g there plus12.8mm motor-CG probe. Full rotational inertia stays unavailable;
no full flight or altitude comparison was run. External geometry/CP hypothesis
is unchanged; static RocketPy compares only the no-growth endpoints.

| Final case | Total incl50g | CG / static margin |1.5m departure | Formal15 margin / mass headroom | Planning15.5 margin / mass headroom |
| --- | ---: | ---: | ---: | ---: | ---: |
|55g estimated main, nominal |934.549g |763.693mm /1.433cal |15.212909m/s |+0.212909m/s /+23.794g |−0.287091m/s /−30.750g |
|55g main, adverse |954.549g |775.602mm /1.255cal |15.033479m/s |+0.033479m/s /+3.794g |−0.466521m/s /−50.750g |
|68g metadata probe, nominal |947.549g |757.881mm /1.520cal |15.095650m/s |+0.095650m/s /+10.794g |−0.404350m/s /−43.750g |
|68g probe, adverse |967.549g |769.749mm /1.343cal |14.919669m/s |−0.080331m/s /−9.206g |−0.580331m/s /−63.750g |

CP859.442mm, diameter66.802mm; **CG** is balance point and **calibre** is one
body diameter separating it from the effective aerodynamic-force point **CP**.
55g-main burnout margins1.854/1.654cal; recorded aft-stowage sensitivity
1.315/1.140cal. Stowage locations are estimates, not measured motion bounds.
Conditional1.8m guide speeds16.668/16.472m/s are not adopted equipment.
Adverse formal maximum main mass is **58.794g** with other budgets fixed;
planning would require4.250g and is not credible for this main. A measured
finished mass or suitable actual launch-equipment decision matters materially.

Cost becomes **$476.69** before tax/shipping and test equipment: verified
NW-12 price lowers the former estimate7.61dollars; sleeve/fill add2.25dollars.
All remain budgeted acquisitions, not owner stock. Source-supported savings
already include removed ballast-only hardware and paired body eyes; do not
remove the retained nose/service hardware, double-credit paper cuts, or use the
lighter2017 **flat** nylon specification for today's **tubular**NW-12. Further
connector/adhesive savings lack complete functional/strength evidence and are
not credited. Strength, not a rounding-level mass change, controls next design.

## 5. Practical verification and admission

See the [dimensioned test plan](wo03-rp1-representative-test-plan.md). Product
drawings/reports can resolve mass units, sewn dimensions, rated scope, bend
limits and environmental data. They cannot establish our ring/body/root joint
capacity. The packet is **ready for owner review of a sacrificial soft-cord
coupon and local dry-fit article definition**. It is **not released for loading
or flight-vehicle manufacture**: textile/knot packing, fixture reactions and
conditioned bond details must first be recorded. Physical work remains owner
performed and separately authorized. The known fin failure need not prevent
an explicitly sacrificial recovery experiment, but prevents vehicle admission.

| Item | Closure / remaining gate |
| --- | --- |
| Exact nylon SKU and offered price | Documentation sub-item closed; physical stock/revision unknown |
| Raw cut/end topology and accounted route | Defined; finished length, seating/slip and mass unmeasured |
| Sleeve-through-notch conflict | Corrected inAD1v2 geometry; no thermal/chafe pass |
| Slot per-flank definition | Conditional dimensional screen passes; not whole-vehicle adoption |
| Changed fin panel/root | **Failed optimistic screen**; installed bonds/dynamics also open |
| Complete recovery connection | Demand/contacts defined; finished strength, paper, peel and partition open |
| Guide/static checks |55g-main formal/static hypothesis passes; planning misses and mass-sensitive |
| Physical/flight acceptance | Open; no engineering requirement closed merely by tests/PR checks |

The initial producer failed schema validation before numerical work because
the slot-fill envelope was incorrectly referenced at1140mm rather than having
its centre there. The archived successfulv1 corrected origin1075/CG1140.
The single subsequent geometry correction moved the sleeve; valid guide/strip
results were reused, not re-run. Initial1.233CPU/1.793wall seconds, correction
1.129CPU/1.319wall; thread settings1, actual CPU affinity unverified. Both are
within declared budgets. Stop conditions now apply: no automatic iteration,
FEA, custom thermal campaign, material-limit increase or recovery-case reduction.

**Next bounded engineering action:** one source-informed fin construction/
root definition addressing both the7.301MPa/1.805mm panel failure and finite
body joint, with complete mass/guide consequences **before** detailed analysis.
That requires a separately recorded scope; this packet does not start it.
The exact finished harness mass and representative hot/wet joint evidence
remain decision-driving. G54 and G12 PID-to-RL retain their separate gates.

Publication of the independent frontend increment is complete: PR72 merged
after both required jobs passed at`3a16cccea919fa83fc1695315af2f40b087d5fdb`.
The offline drawing pack was inspected, including a primary correction separating
parallel tube/ring and gusset/body force routes. Aggregate native rendering
106.955s stayed within120s; compact path-node secondary labels touch some box
bottoms and are not accepted manufacturing drawings. Browser acceptance stays open.
