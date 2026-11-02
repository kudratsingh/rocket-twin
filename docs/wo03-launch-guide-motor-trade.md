# Bounded launch-guide and exact-motor comparison

**Decision, 2026-11-01 local / 2026-11-02 UTC:** retain the G80 engineering
hypothesis first. A confirmed **1.8 m usable** guide is a practical conditional
fallback for modest mass growth, with 2.4 m usable considered only when actual
rail/support access is established. Do not adopt a longer guide as a substitute
for a complete light, strong aft receiver. G54 remains the conditional performance
upgrade; G33 is rejected for this package's guide departure, even at 3 m usable.
The baseline remains **1.5 m usable**;1.8 m requires confirmed equipment and
compatibility. No baseline, club, motor, physical connection or flight approval
changes here.

The controlling equipment finding is that the saved CAD's `rail_guides` are
**two cylindrical rod lugs, not 1010/1515 buttons**. A source-model usable distance
cannot be claimed from a purchased rail length. No complete new receiver mass
was available at this packet's cutoff: the only mass probes are failed S2 and
incomplete additive references. Neither is a selected complete candidate.

Reproduction: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
.venv/bin/python scripts/wo03_launch_guide_motor_trade.py` from repository root.
Inputs: [study YAML](../configs/studies/wo03-launch-guide-motor-trade.yaml).
Full outputs: [record](../runs/wo03-launch-guide-motor-trade-20261102-v1/record.json).
`runs/` is ignored local evidence; publication must preserve the small record and
input identities through the primary's approved Git workflow or evidence archive.

## Numerical scope and boundaries

The scope was declared to the primary before execution: 3 pinned motor hypotheses
× 4 usable distances = **12 unique combinations**, each with two mass-limit roots
(15 and 15.5 m/s) and two reference-mass probes. Limit: one CPU, 120 CPU seconds
per combination, 600 CPU seconds total, 900 seconds wall; no flight propagation,
CAD, FEA, heat solver, install or resource escalation. The final packet took
0.790 CPU / 0.812 wall seconds including imports/setup. A first successful packet,
one closure-binding lint correction and one formatting correction are preserved
as `initial-record.json` / `preformat-record.json`; all three executions use the
same 12 hypotheses. Cumulative numerical process effort was **2.420 CPU / 2.528
wall seconds**. Research, editing and tool orchestration are separate non-numerical
setup effort; this is not a 2.5-second end-to-end engineering task. Ruff and Black
checks pass. No solver failed or timed out; the initially missing `.venv/bin/black`
wrapper was resolved with the installed `.venv/bin/python -m black`.

The script imports the source-pinned staged `src/vehicle/benchmark.py`
(SHA-256 `5a0c22b90c3e205b90597caeb07b0ce6cbd10c4f1662eee841600aa16b59d46c`)
and calls its existing `screen_launch`, not a new simulator. Source73 is
`runs/wo03-g80-canopy-stage3-20261101-v1/sensitivity.yaml`, SHA-256
`6962dda2e123ac3528f75136f62b065d742e917712fc2dcef2dfc0a40a675967`.
The `767b45…35f57a` hash belongs to source72
`runs/wo03-g80-staged-retention-20261101-v1/resolved-candidate.yaml`,
not source73. The executed record already stores the correct source73 key/hash.
The record verified unchanged hashes of source, staged implementation, config,
script and all curves before/after execution. A subsequent metadata-only
correction clarified the G80 casing-versus-envelope wording in the maintained
study YAML; its exact executed bytes are preserved as
`runs/wo03-launch-guide-motor-trade-20261102-v1/executed-config.yaml`.
The [correction note](../runs/wo03-launch-guide-motor-trade-20261102-v1/metadata-correction.json)
records both hashes. Numerical outputs, executable script and the original
record remain unchanged; the12-combination campaign is closed.

Retained conservative inputs: fixed total loaded mass with **full separate50 g**,
thrust×0.85, vertical guide, 0.5 N friction, Cd0.8, 66 mm reference diameter,
air density1.225 kg/m³ and 1 ms integration. No mass-loss benefit or crosswind load
is credited. Formal15 m/s is unchanged; **15.5 m/s is a separate planning target**.
No apogee, maximum speed, delay selection, static stability, guide bending,
wind-qualified launch envelope or reference-flight acceptance is calculated.

Roots are guide-model total mass limits, calculated outside the physical-mass
ceiling when necessary to expose which constraint governs. Policy eligibility is
always capped at **strictly less than1500 g**, including growth. A mathematical
root above1500 g never becomes an eligible launch mass or target weight.
Root intervals are narrower than0.000227 g; this numerical precision greatly
exceeds the credibility of the unmeasured mechanical and motor inputs.

## Overall rail length versus safe usable travel

Source73 puts `rail_guides` at nose-to-aft station250 mm. Its CAD parameters
place two 12 mm-long tubes at local0/180 mm: global front edges250/430 mm,
centers256/436 mm, rear edges262/442 mm. Bore diameter3.4 mm, outer diameter6 mm,
radial center36 mm. The generator makes hollow axial tubes and feet. It provides
no rail-slot captive head, matched1010/1515 button neck/head, fastener or certified
button-bearing interface. A3.175 mm (1/8 inch) rod fits only nominally; straightness,
clearance, stiffness, lug joint strength and installed compatibility are unqualified.

Using the source aft hardware datum1212 mm and an explicitly **assumed100 mm**
aft-datum height above rail bottom, the upper/front guide leading edge starts
at100+(1212−250)=**1062 mm** above rail bottom. To preserve two-guide restraint,
this study conservatively ends useful guidance when that leading edge first
reaches the guide top. The lower guide remains engaged another180 mm; that
single-guide interval earns no safe-travel credit. Actual last engagement of a
12 mm lug could differ by12 mm, and future buttons have their own slot/head/end
geometry. An end cap, blast plate, stop, lug/button stand-off or occupied slot can
remove further travel. No actual pad offset or release geometry was measured.

For this stated placement/offset only,
`L_usable = L_clear_overall −1.062 m`; equivalently:

| Declared usable travel | Minimum unobstructed overall guide length | Evidence/access implication |
|---|---|---|
| 1.5 m reference | 2.562 m /8.41 ft | An8 ft overall rail is insufficient at source positions. |
| 1.8 m | 2.862 m /9.39 ft | A10 ft overall rail can geometrically supply this, if compatible and clear. |
| 2.4 m | 3.462 m /11.36 ft | Requires about12 ft clear overall, or a separately engineered placement. |
| 3.0 m | 4.062 m /13.33 ft | A10 or12 ft overall rail does not supply3 m usable here. |

For orientation only, 6/8/10/12 ft clear overall gives0.7668/1.3764/1.9860/
2.5956 m under that assumption. These are geometric conversions, **not extra
numerical departure cases**. No future aft-button-placement hypothesis is
screened or adopted. A button conversion needs its own dimensions, attachment,
stand-off/fin clearance, stiffness, service path and counted mass coordinated
with the complete receiver. Existing0.623 g printed lugs cannot be relabelled
as purchased buttons with zero mass consequence.

## Mass accounting and results

Source73 nominal794.581712 g minus the named139.060536 g source frame/carrier/
retention bundle **once**, plus separate50 g = **705.521176 g retained** with
G80 still included once. The named removed IDs and their actual individual
masses are in the record. This credit is conditional on replacing every removed
function. Retained fins, body, recovery, avionics, liner and shields are not free
mass and are not deleted here.

Swap only complete assembled motor mass: G54 adds70 g, G33 adds68.8 g to that
retained subtotal. Their whole replacement-assembly budgets include an explicit
**20 g incremental support/retention reserve**; it is a sensitivity, not a designed
or upper-bounded support. Deduct20 g from the gross CTI budgets below to obtain
the amount left for the common receiver after that reserve. Future button mass,
all fasteners, bonds, hot protection, body/fin/recovery joints, access and service
items must fit within the same complete budget. If actual support exceeds20 g,
the available receiver budget falls one-for-one.

| Motor hypothesis | Usable m | Raw maximum TOTAL launch g at15 /15.5 | Policy-capped complete replacement budget g at15 /15.5 | Departure m/s at S2-derived / additive-derived mass |
|---|---:|---:|---:|---:|
| G80 | 1.5 | 958.398 /903.854 | 252.877 /198.333 | 15.230 /14.835 |
| G80 | 1.8 | 1126.575 /1063.511 | 421.054 /357.990 | 16.688 /16.255 |
| G80 | 2.4 | 1446.649 /1368.353 | 741.128 /662.832 | 19.281 /18.784 |
| G80 | 3.0 | 1745.798 /1654.908 | <794.479 /<794.479 | 21.573 /21.019 |
| G54 | 1.5 | 1126.448 /1066.485 | 350.927 /290.964 | 15.889 /15.491 |
| G54 | 1.8 | 1288.140 /1222.719 | 512.619 /447.198 | 17.295 /16.852 |
| G54 | 2.4 | 1563.383 /1489.123 | <724.479 /713.602 | 19.712 /19.199 |
| G54 | 3.0 | 1798.770 /1717.000 | <724.479 /<724.479 | 21.779 /21.205 |
| G33 | 1.5 | 344.650 /323.450 | −429.672 /−450.871 | 7.975 /7.739 |
| G33 | 1.8 | 416.535 /391.324 | −357.786 /−382.997 | 8.772 /8.512 |
| G33 | 2.4 | 549.139 /518.225 | −225.182 /−256.096 | 10.187 /9.885 |
| G33 | 3.0 | 669.304 /633.490 | −105.017 /−140.831 | 11.434 /11.096 |

`<` means the strict1500 g physical ceiling governs. Negative budgets mean the
retained source subtotal already exceeds that guide-model limit before any
replacement assembly. They are not buildable negative masses. G33's extra
impulse relative to the conservative G80 source does not compensate for its
low early thrust. G54's source1.5 m advantage is conditional; at the incomplete
additive-derived full mass it misses15.5 by0.009 m/s and is not a rounding pass.

The two probes are deliberately labelled **incomplete, not admitted**:

| Motor | S2-derived full launch g | Additive-derived full launch g | Severe factored mean opening N, S2 /additive | Nominal factored mean opening N, S2 /additive |
|---|---:|---:|---:|---:|
| G80 | 932.677 | 977.490 | 1968.154 /2062.718 | 144.024 /150.944 |
| G54 | 1022.677 | 1067.490 | 2158.074 /2252.638 | 157.922 /164.842 |
| G33 | 1021.477 | 1066.290 | 2155.541 /2250.106 | 157.736 /164.656 |

Both CTI probes add the motor delta and separate20 g support sensitivity to the
same failed G80 reference. This is not a complete CTI vehicle design.
Opening uses unchanged `3*m*(v²/(2*0.3)+9.80665)`, with severe20.4 m/s and
nominal5 m/s. It recalculates at each corresponding full mass. It is a factored
work/mean-deceleration screen, **not a transient peak load**, strength allowance
or frozen1782 N. The record also gives opening screens at each policy-capped
mass ceiling; those values explain heavier-mass consequences, not desired loads.

## Exact motors, CG and integration consequences

| Hypothesis and exact commercial lead | Complete motor counted once; source dimensions | CG/support consequence and unresolved identity |
|---|---|---|
| AeroTech G80-10T SU SKU78010 | Pinned source128.2 g,29×128 mm; source133.243510 N s, terminal1.8079 s | Source midpoint1136 mm at fixed aft1200 mm. Sold product says127.9 g, casing124 mm,136.6 N s,77.6 N/1.7 s. The124 mm value is explicitly casing length and may coexist with a128 mm assembled envelope: datum/variant mapping is unverified, not a proven length contradiction. Historical G78 label, impulse/mass differences, current envelope/nozzle/CG and delay correspondence remain unresolved. No mass/curve values mixed. |
| CTI159G54-12A Red Lightning; Pro29-3G, standard rear closure, no spacers |198.2 g includes assembled hardware once;29×187 mm; source159.544346 N s, terminal3.026 s | Midpoint1106.5 mm,59 mm forward motor front versus source G80 (1013 vs1072 mm), motor moment change+73.6731 g·m at fixed aft plane.20 g support sensitivity has no verified CG/location. Header96.8 g depletion conflicts with86.5 g reported propellant;193/198.2 g catalog/manufacturer discrepancy remains. |
| CTI143G33-9A Mellow; same3G case/closure/no-spacer configuration |197 g assembled;29×187 mm; source143.298266 N s, terminal4.461 s | Same1106.5 mm midpoint/front shift; motor moment change+72.3453 g·m.20 g support sensitivity unlocated. Header89 g depletion conflicts with79.1 g reported propellant. Rejected guide performance, even before fit/heat acceptance. |

These are source-midpoint assumptions, not measured motor CGs or full-vehicle CGs.
The longer CTI motors reach the fore receiver/thermal region and need positive
thrust/reverse retention, actual case/closure/nozzle drawings, thermal clearances,
liner/shield extension, support mass and full new mass/CG/inertia/static stability.
The G80 support cannot be assumed to accept either CTI motor merely because both
say29 mm. Neither propellant discrepancy affects this fixed-loaded-mass guide
calculation, but both block using the data as a reconciled exact flight package.

Only G33 was added numerically because it has an existing pinned curve and a
specified complete hardware hypothesis. It is a useful negative comparison.
The second permitted extra lead is **metadata-only AeroTech G79W-14A SKU077914,
RMS-29/120**, not G79 SU, LMS or hobby29/40-120. The manufacturer currently lists
158 g,140 mm casing,115 N s,79 N average,59 g propellant and1.5 s at$34.99 with
Add to Cart. Its lower impulse and heavier motor do not establish improvement
over G80; early thrust and mounting might differ. No matching pinned exact curve,
complete hardware stock/cost/envelope or California acceptance was established,
so no invented curve or additional guide cases were run. Old catalog149 g/
108.6 N s and LMS125 g data are not substituted. [Manufacturer G79W-14A](https://aerotech-rocketry.com/products/product_68ec8c32-c7c1-b48f-bee3-dfd3d69ac87c).

G25W remains quarantined for the existing RMS/DMS/SU identity, dimensions, mass,
curve and certification discrepancies. The conventional three-second burn
preference is superseded by ADR-0006. G12 remains the committed controls/PID-to-RL
track, and larger diameters remain separate integration hypotheses; none is
quietly adopted or cleared by this comparison.

## Current eligibility, supply and equipment evidence

Public pages were read2026-11-01 local. Stock/cost is a dated observation, not a
reservation, shipment guarantee, purchase authorization or club acceptance.

General national model/no-HPR numerical screening uses certified single-motor
impulse≤160 N s, average thrust≤80 N, total propellant≤125 g, total mass≤1500 g,
commercial nonsparky nonhybrid propulsion and appropriate nonmetal airframe
construction. These numerical motor values support conditional no-HPR eligibility
for G80/G54/G33; an exact sold motor and complete construction must still match.
The [NAR boundary](https://nar.org/content.aspx?club_id=114127&module_id=667402&page_id=22)
is separate from FAA Class1, which also requires slow-burning propellant,
paper/wood/breakable plastic and no substantial metal, not merely a mass test.
Our project retains **strictly below1500 g**. Metal motor hardware and small
fasteners require appropriate interpretation with the actual configuration;
no FAA approval is inferred. [Official14 CFR101.22](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-F/part-101/subpart-C/section-101.22).

The current [NAR interactive certification list](https://www.nar.org/content.aspx?club_id=114127&module_id=670148&page_id=22),
updated2026-08-12, lists AeroTech G80T-7/10/13 at29×128 mm,136.6 N s and62.5 g,
separately from older G80 rows. This supports the family, not reconciliation of
all current SKU/source dimensions. The official [CAR certification page](https://www.canadianrocketry.org/en/certifications/motor-certifications)
links an Airtable index, whose motor rows were unavailable in the web extraction.
Current CTI exact-list status was therefore **not verified** here. Saved historical
CAR/report and manufacturer evidence remain; inaccessible current rows are not a
revocation claim or a current pass. Direct G33/G54 manufacturer pages timed out;
no repeated access campaign followed.

California exact classification remains independent. Official19 CCR1021 requires
SFM motor-type classification and a seal/registration number; OSFM identifies
itself as the state classification authority. No matching current G80/G54/G33
classification letter or actual packaging/seal was obtained in this bounded
packet. A catalog's “CSFM Approved” badge cannot establish model-vs-HPR exact
classification. The G80 manufacturer itself uses both model and high-power
language; the numerical national boundary does not resolve state classification.
[Official California regulation](https://govt.westlaw.com/calregs/Document/I1AEBEB775BE511EC98C8000D3A7C4BC3?needToInjectTerms=False&originationContext=document&transitionType=StatuteNavigator&viewType=FullText),
[OSFM authority](https://www.fire.ca.gov/osfm/what-we-do/fire-engineering-and-investigations/fireworks).

| Exact item | Dated direct observation | Practical consequence |
|---|---|---|
| G80-10T SKU78010 | Manufacturer$43.99, Add to Cart; Wildman$43.99 Sold Out | A direct purchase lead exists, not guaranteed California shipment or matched source hardware. [Manufacturer](https://aerotech-rocketry.com/products/product_bea030f5-871e-61ef-1279-45a2bbebbd87), [Wildman](https://wildmanrocketry.com/products/g80-10t). |
| G54-12A reload product1146 | Chris'$40.47, out of stock | No complete purchasable configuration verified; exact stock/lot/delay tool remains needed. [Direct vendor](https://www.csrocketry.com/rocket-motors/cesaroni/motors/pro-29/3g-reloads/cesaroni-g54-12a-red-lightning-rocket-motor.html). |
| G33-9A Mellow reload | Wildman$39.45 Sold Out | No ready fallback; saved ignition-pellet bulletin/lot applicability remains unresolved. [Direct vendor](https://wildmanrocketry.com/products/pr29-3g-my). |
| Pro29-3G case1104 and standard rear closure1237 | Chris'$44.66 and$33.50, both out of stock | Hardware is separate purchase but already included in assembled motor mass. G54 first-set listed subtotal$118.63 before tool/shipping/hazmat/tax; availability fails. [Case](https://www.csrocketry.com/rocket-motors/cesaroni/hardware/pro-29/3g-hardware/cesaroni-29-3-grain-case.html), [closure](https://www.csrocketry.com/rocket-motors/cesaroni/hardware/pro-29/6gxl-hardware/cesaroni-29mm-rear-closure.html). |

ROC/Lucerne remains an unconfirmed site. Its official page explicitly confirms
1010 and1515 rails and1/8,3/16,1/4 inch rods, encourages rails for G and above,
and requires every flight's RSO/FSR approval with stable-flight, safe-recovery
and OSFM motor evidence. **Rail length, support geometry and reservation are
not stated**, so ROC's listing establishes rail types, not1.8/2.4/3 m usable
access. High-power motors/users carry separate certification/California operator
requirements; actual model classification is essential. [ROC rules/equipment](https://rocstock.org/flying-with-roc-2/).

There is realistic longer-rail evidence nearby in California: the official
[MDARS equipment list](https://www.mojavedesertrocketry.org/club-equipment)
states approximately10 ft1515, and approximately10 ft1010 attached to1515,
for members. Under current forward guide positions10 ft corresponds to only
1.986 m usable with the assumed offset, sufficient geometrically for1.8 m but
not2.4 m. This is a credible access lead requiring owner choice, current event
confirmation, club approval and compatible actual buttons. It is not a booked
pad or permission to launch there.

An official club inventory elsewhere lists1.8/2.4/2.6/3.7 m1010 and3.7 m1515,
showing that those **overall** lengths are real equipment, not that California
clubs own them. [Victorian Rocketry inventory](https://victorianrocketry.org.au/public/pages/what-launch-rails-are-available).
Manufacturer80/20 sells1010 and1515 extrusion up to242 inches; that establishes
purchase feasibility only, not a stable rocket pad. Standard1010 hasI0.0442 in⁴,
standard1515 I0.2542 in⁴ with equal listed modulus10,000,000 psi: about5.75×
section bending stiffness at equal support/length. A longer unsupported rail
bends more; mounting height, clamps, backing, base/anchors, joint looseness,
straightness and wind matter. MDARS's1010-on1515 is explicit support evidence,
not qualification of a free-standing3–4 m1010 cantilever.
[Official1010](https://8020.net/1010.html), [official1515](https://8020.net/1515.html).

The [NAR model code](https://www.nar.org/ModelRocketSafetyCode) permits winds no
greater than20 mph (8.94 m/s) and safe weather; this is a code ceiling, not this
rocket's allowed wind. The source screen's2 m/s is a diagnostic assumption and
models no wind force. Club closures, pad deflection, recovery drift and the RSO
may impose lower limits. Long rails do not establish crosswind or lug/button
strength acceptance.

## Next bounded deliverable, stop condition and owner questions

Preferred next setup: finish the complete G80 receiver with full50 g counted,
retain the1.5 m reference until actual equipment is confirmed, and provisionally
plan around **1.8 m truly usable on a supported compatible rail** if the complete
mass needs that margin. At that usable distance the G80 planning ceiling is
1063.511 g, with357.990 g gross complete replacement assembly budget from the
source ledger; construction should seek lower mass and robust joints, not consume
the ceiling. Conditional fallback: a confirmed roughly12 ft clear supported rail
could provide2.4 m under current guide positions after a qualified button
conversion. G54's higher impulse remains a separate engineering upgrade once
matched motor evidence, stock, California classification and all integration
checks exist. It is not needed merely to hide an incomplete G80 mass ledger.

Stop here: no new placement, physical variant, simulation campaign, free flight,
CAD or solver run. The primary must first supply a complete preliminary candidate
ledger and select a guide/motor hypothesis; then one bounded same-configuration
package can check mass/CG/inertia, stability, actual release, joint/guide loads,
heat, fits and affected reference/flight comparisons. A guide pass alone clears
none of those gates or aggregate WO-03.

Required owner/club inputs, without sending messages on the owner's behalf:

1. Which club/site/date is intended—ROC/Lucerne, MDARS, or another confirmed site?
2. What actual clear rail length/profile, unobstructed slot, support/backing,
   clamps/base/anchors and loading arrangement will be available for this G rocket?
   Can a specific pad be confirmed ahead of time?
3. What aft datum/blast-deflector/stop offset is required, and what are upper-button
   initial height, end geometry and final reliable two-button restraint distance?
4. Will the club accept the specified button model, spacing, attachment/stand-off,
   rocket mass, departure calculation, wind limit and independent recovery package?
   What lower wind or pad-deflection limits apply?
5. For the exact proposed motor/lot/delay and hardware, can the supplier provide
   current certification, matching curve/mass/envelope and California **model**
   classification/seal? For CTI, resolve depletion and lot/bulletin applicability.
6. Can all required reload, case, closure and tool components actually be supplied
   together, with complete cost/shipping and California delivery conditions?

No message, purchase, reservation, paid run, browser/computer use or GitHub action
was performed by this bounded agent. The active vehicle and engineering findings
remain unchanged; `flight_ready` is false.
