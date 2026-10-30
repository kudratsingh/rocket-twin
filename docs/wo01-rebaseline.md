# WO-01 rebaseline: custom modular rocket and serious control research

Owner direction: 2026-10-29. Active decision: ADR-0006. All work here is reversible
local planning, design and computation; no procurement, physical work or flight.

The recommendation is a **66 mm hybrid custom platform with interchangeable aft
assemblies**: conventional finned performance, a finned PID-to-RL TVC trainer,
and eventual finless TVC. The custom-build and maximum-practical-performance goals
are retained alongside committed embedded RL, independent validation and real logs.
The result is not selected merely because it is easy to assemble.

## Bounded architecture trade

| Architecture | Performance and learning benefits | Main penalty | Decision |
|---|---|---|---|
| One finless long-burn vehicle | Direct active-control challenge and one build | Carries gimbal mass on every flight; weak connection to highest passive performance; burnout authority/recovery difficult | Retain as a configuration, not the sole platform |
| Two unrelated passive/TVC rockets | Independent optimization; simplest validation boundaries | Duplicate avionics/recovery and build effort; less interface engineering reuse | Fallback if modular joint proves too heavy or unreliable |
| Common upper, distinct aft modules | Custom joints, mechanisms, structures, propulsion integration and shared avionics/recovery; different motors and actual mode models | Joint mass, tolerances, connectors and configuration management | Recommended preliminary architecture |

Shared nose/upper tube/sled/recovery attach to an indexed aft interface at station
520 mm. A 100 mm coupler has nominal 50 mm overlap into each shell, a positive
axial stop, anti-rotation keys and removable retention. The shell, coupler and
load-transfer hardware are separate counted parts. These are interface design
inputs; CAD must establish clearances, joints and load capacity. No fit is claimed.

`configs/vehicle/platform/common-upper.yaml` contains the shared parts; each mode
adds its own actual aft parts and propulsion. `configs/platform.yaml` names all
three. The loader emits complete resolved vehicles; each run stores the resolved
spec, inventory preview, all input hashes and code hash. Fins are physical
trapezoidal plate sets with radial inertia, not massless aerodynamic switches.
Servo offsets enter the full inertia tensor. Most component shapes remain envelope
approximations pending CAD; mass distributions and thrust-axis alignment are unmeasured.

## Materials and fabrication trade

For equal **66 mm OD and 660 mm total straight tube length**, shell-only masses
below exclude all joints, finishes, local reinforcements, fittings and nose. They
are comparisons, not equivalent-strength designs. Bulk estimates use
`pi*(R_outer²-R_inner²)*L*density`; printed voids and laminate quality are not inferred.

| Method | Tube-only mass estimate | Strength and thermal trade | Manufacturing, cost and learning |
|---|---:|---|---|
| Purchased thin kraft, cut/sealed/custom reinforced | About 55 g from the cited tube mass; specified upper + aft = 55.15 g | Good geometric stiffness per mass; moisture, crushing and bond loads govern; combustible, protect from ejection/case/plume | Tube stock roughly $10–20 allowance; teaches cutting, joint design, bonding, sealing and integration; recommended starting substrate |
| Custom mandrel-rolled kraft | Initial 55–85 g target, unverified | Seam, adhesive, wall variation and buckling require coupons; no assumed parity with wound stock | Roughly $10–25 materials plus mandrel/jig; more fabrication learning; alternate structure requiring separate mass/dimension revision |
| Printed PETG, 1.2 mm uniform shell | 205 g at 1,270 kg/m³ | Layer direction, ovalization, creep and case heat matter; reducing wall does not establish strength | Roughly $10–20 shell consumables; printing/section joining valuable, but sacrifices about 150 g versus tube before joints; not default |
| Printed PETG, 1.6 mm uniform shell | 271 g | More wall material does not remove anisotropy or heat/creep tests | More print time/material; preserves old study as historical evidence, not active baseline |
| Printed ASA, 1.2 mm uniform shell | 173 g at 1,070 kg/m³ | Better published outdoor/heat suitability than PETG, still directional and grade/process dependent; bulk HDT is not a flight service limit | Roughly $10–25 shell consumables, enclosure/ventilation and shrinkage management; use locally for nose, sled and gimbal instead of entire tube |
| Custom glass/epoxy, 0.6 mm trial laminate | 151 g at estimated 1,850 kg/m³ | Fiber orientation, resin fraction, cure and delamination govern; resin sets thermal limit; Class-1 material suitability also requires review | Roughly $30–70 consumables before mandrel/tools; strong fabrication-learning option, heavier/riskier initial process than kraft; coupon study before adoption |
| Plywood fins/bulkheads plus printed mechanisms | Included part by part below | Grain, root bending, bonded load path and flutter govern fins; isolate polymer mechanisms from case heat | Cutting/drilling/filleting, jigs, nested-ring design, tolerances and actuator integration give substantial custom work |

Costs are planning allowances, not quotes. Tube mass/diameter reference:
[Apogee's own 66 mm tube listing](https://www.apogeerockets.com/Building_Supplies/Body_Tubes/56mm_to_98mm_4in_Tubes/66mm_X_18in_Slotted_Body_Tube_for_TARC).
[Prusa PETG guidance](https://help.prusa3d.com/article/petg_2059) and
[ASA guidance](https://help.prusa3d.com/article/asa_1809) support the qualitative
print/thermal trade; no bulk or printed coupon strength is assigned to this rocket.
The literature values are not substituted for measured layer/joint behavior.

## Motor trade under revised requirements

Published motor performance and the numerical source curve are distinct evidence.
No vendor summary is used to rewrite a curve. Recommendations below are preliminary
families/hardware configurations for design, not a fully verified purchasable flight
configuration. Exact recovery delay, lot, installed envelope and California/club
acceptance remain later gates.

| Candidate | Published impulse / burn | Revised role and remaining issues |
|---|---|---|
| AeroTech G80-10T SU, SKU 78010 | 136.6 N s / 1.7 s, 127.9 g, 62.5 g propellant, 77.6 N mean | Performance recommendation: strong rail departure without reusable case mass. Historical 2007 source models 128 mm / 128.2 g and about 133.2 N s; current product says 124 mm. Preserve source discrepancy; -10 is a study SKU, not a validated flight delay. Direct product pages checked currently say out of stock; category/aggregator stock claims are not accepted. |
| CTI 159G54-12A, Pro29-3G + standard closure | 159.1 N s / 2.97 s, 198.2 g manufacturer | Reopened maximum-impulse performance upgrade: old three-second rejection is superseded. +70 g motor mass and uncertain availability/classification reduce immediate practicality; curve says 96.8 g propWt versus manufacturer 86.5 g. Not yet a qualified substitution. |
| AeroTech G12ST-P DMS SKU 071200, reformulated 2021 | 143.97 N s / 12.7 s, about 150.3 g | TVC recommendation: long useful powered window, acceptable new guide screen. Plugged: independent electronic recovery essential. CAL FIRE model classification letter archived; live Wildman product offers Add to Cart. Curve mass 150 g and length 156 mm versus report 150.32 g / 155.98 mm and advertised 147 mm; actual envelope and heat exposure remain open. |
| CTI 143G33-9A Mellow, Pro29-3G + standard closure, no spacers | 143.1 N s / 4.38 s, 197 g | Higher-thrust TVC alternative; fewer useful control seconds but easier launch. No complete in-stock configuration verified; 89 g curve depletion versus 79.1 g certified propellant and factory bulletin/lot status unresolved. |
| AeroTech F25 molded source | 70.7668 N s / terminal time 2.69 s | Reopened as a lower-energy performance commissioning candidate: passes revised performance rail screen at about 15.8 m/s. Short burn alone no longer rejects it. Not chosen for long-control trainer: contiguous useful window about 1.8 s, below the justified 2 s screen. Sold-variant/source correspondence still required. |
| Estes F15 archived source | 49.61 N s / terminal 3.45 s | Useful historical and lower-power trade, not immutable default. New performance guide screen about 8.8 m/s and trainer about 9.3 m/s, below their respective targets; trainer useful window about 2.7 s is below the preferred 5 s. |
| AeroTech F22 2026 post-test | 55.08 N s / report 3.83 s | Reconsidered; new performance/trainer guide speeds roughly 7.1/8.3 m/s fail. Seven-second delay test failures remain separate from threshold changes; no selection. |
| AeroTech G25W-10A | Conflicting historical/current datasets | Source quarantine remains. Removing the old thresholds cannot reconcile RMS/DMS identity, propellant/header mass or full envelope. |
| CTI 150G50-15A, Pro38-1G | 150 N s / 2.87 s, 218 g | Reopened for performance, not rejected for <3 s. Versus G80, about +90 g motor plus provisional +30 g larger-mount mass for only +10% impulse. No demonstrated practical gain before trajectory/fit/classification work. Keep 38 mm aft-module study separate. |

Manufacturer sources: [G80-10T](https://aerotech-rocketry.com/products/product_bea030f5-871e-61ef-1279-45a2bbebbd87),
[CTI G54](https://pro38.com/products/p29-3g/159g54-12a/),
[CTI G33](https://pro38.com/products/p29-3g/143g33-9a/),
[G50](https://pro38.com/products/p38-1g/150g50-15a/).
Direct checks: [G80 Chris' Rocket Supplies](https://www.csrocketry.com/rocket-motors/aerotech-rocketry/motors/29mm/single-use/aerotech-g80-10t-blue-thunder-rocket-motor.html),
[G80 Wildman](https://wildmanrocketry.com/products/g80-10t),
[G12 Wildman](https://wildmanrocketry.com/products/g12st-p-29mm-dms).
Availability is time-dependent and must be refreshed before any procurement decision.

The 29 mm bore survives this trade because both preliminary families fit its nominal
class and existing source evidence, not because it is a constraint. The 66 mm diameter
provides a preliminary electronics/recovery/gimbal envelope. Custom 38 mm modules
remain possible if a quantified flight/payload benefit justifies their added mass,
clearance and fabrication work. Neither 160 N s nor 1.5 kg is an automatic optimum.

## Source model acceptance and uncertainty

The two new numerical files under `configs/studies/rebaseline/motors/` are **web
RASP transcriptions with whitespace normalized**, not claimed byte-identical API
downloads. Every header/sample is retained from the displayed source block; local
hashes guard subsequent changes. Sidecars distinguish the historical G80/G78 header,
current catalogue/SKU values, reformulated G12 test summary and actual assembled
hardware still to be measured. G80's conflicting 2013 G80NBT header (69 g propellant)
is not silently substituted. The original downloaded curves are untouched.

WO-01 can validate these explicitly labelled preliminary numerical hypotheses.
A matching curve/config/reference demonstrates arithmetic, not exact current
hardware certification. Reconcile/freeze the exact source and sold variant before
WO-02 claims a prediction of that physical motor; if unavailable, simulations are
labelled source-hypothesis cases. Freeze the actual certified/OSFM approved motor,
lot, full case/nozzle/retention envelope, mass/CG and delay before procurement and
flight release. General NAR/Tripoli limits do not establish California approval.

## Derived mass and cost budget

These are preliminary estimates from each resolved specification, not weighed parts.
The shared upper is **245.75 g**, including 35 g canopy allowance, 30 g battery,
independent recovery electronics, wiring, fasteners/anchors and adhesive/finish.
The physical aft budgets already include liner, mount, retention and interface
hardware. Another **50 g growth allowance** is reserved outside the physical parts;
for passive margin all 50 g is conservatively placed at the aft end. Motor dry
hardware is included once in loaded mass, never added a second time.

| Mode | Shared upper | Aft excluding motor | Complete motor hypothesis | Nominal loaded | With 50 g growth | Parts-cost preview including one motor |
|---|---:|---:|---:|---:|---:|---:|
| Performance | 245.75 g | 98.08 g | 128.20 g | **472.03 g** | **522.03 g** | **$392** |
| Finned TVC trainer | 245.75 g | 180.02 g | 150.00 g | **575.77 g** | **625.77 g** | **$455** |
| Finless TVC | 245.75 g | 136.40 g | 150.00 g | **532.15 g** | **582.15 g** | **$446** |

No duplication of the shared upper in procurement: common inventory ~$309;
performance-only parts/motor ~$83; trainer-only parts/motor ~$146. Both aft modules
and one motor of each type total about **$538**, with the finless mode obtained by
omitting the trainer's fins/bonds in a separately fabricated/qualified finless shell.
Add ~$20–40 for that alternate shell/interface and assembly consumables, ~$100–180
spares/contingency: **roughly $650–950 planning envelope** before tax/shipping and
club fees. Motor budgeting is ~$40–50/flight. No reload hardware is assumed free.
A guide/test fixture adds roughly $100–200 if not supplied by the club; new printer,
enclosure, tools and paid compute are separate. All prices are budget estimates.

Inventories are generated into each run as `*-inventory.json`, retaining `build`,
`learn`, full geometry, material and mass fields for every part. These are previews;
CAD generators/STEP and full purchasing BOM/assembly pack remain WO-03/09.

## Replaced thresholds and preliminary screening evidence

- **Guide departure:** performance 1.5 m usable rail / >=15 m/s; TVC 2.4 m usable
  guide / >=10 m/s. At screening winds 2/1 m/s respectively, the targets correspond
  to kinematic crosswind angles about 7.6/5.7 degrees. They are provisional targets
  for later small-angle/wind validation, not universal launch rules. Usable travel
  differs from nominal rail length; guide spacing/clearance require CAD and club checks.
- **Loads and margin:** both passive modes require >=1 calibre at both burn endpoints
  with all growth mass aft. Fins differ: performance 80 mm span, trainer 95 mm span,
  both three custom 2 mm plywood trapezoids. Fin strength/flutter is unverified.
  Finless records its negative margin and active-control/recovery risk explicitly.
- **Control opportunity:** lower-bound thrust >=1.2 times worst-case loaded weight
  for >=2 contiguous seconds after guide departure, preferred >=5 s. A provisional
  0.2 s settling time gives 10 minimum/25 preferred response intervals. Sensors,
  servo lag, torque/rate limits and aerodynamic moments must validate that premise
  in WO-02/06; duration alone cannot prove a controller is useful.
- **Recovery:** 6 m/s preliminary descent target at rho=1.1 kg/m³, Cd=0.75. Worst
  trainer requires about 0.413 m², or 725 mm equivalent circular diameter; budget
  a 750 mm canopy. Actual canopy Cd, density/landing conditions, packing and opening
  loads require measurement and simulations. Finless cannot rely on TVC after burnout.

The guide-only calculation uses constant loaded mass plus 50 g, thrust scaled to
85%, Cd upper estimate 0.8, air density 1.225 kg/m³ and 0.5 N guide friction. It
stops at guide departure. It does not predict free flight, altitude, crosswind
forces, actuator torque or stability under large disturbances. Useful control time
is a conservative constant-mass thrust-duration proxy, not a Monte-Carlo result.

Initial screens correctly failed the trainer's passive margin and short guide;
the hardware hypotheses were revised to larger actual trainer fins and longer
usable guidance. The canopy allowance was revised after descent sizing. Recorded
negative runs remain under `runs/wo01-platform-20261030T015149592090Z/` and
`runs/wo01-platform-20261030T015256135912Z/`; no threshold was reduced to hide them.
Latest verified numbers and final run identifiers are in results.md.

## Fabrication and remaining verification

1. WO-02: simulate actual fixed/finned-locked configurations independently in JAX
   and RocketPy; select recovery delays and assess rail exit, wind, altitude/site
   limits, acceleration, dynamic pressure, drag and descent/landing sensitivity.
   Compare G80 with reopened F25/G54/G50 cases before asserting maximum altitude.
2. WO-03: generate the cut/printed parts and purchased component envelopes; verify
   all joins, ring/pivot/retention/nozzle sweeps, wiring/service access and packing.
   Include every tab, fastener, liner, fillet and finish; update mass/inertia from CAD.
   Prototype plans include axial joint/buckling/bending and fin-root coupons. A
   provisional 120 N axial design load (roughly 1.15 times source G80 peak, rounded
   up) and factor-two strength target guide sizing, not certified load capacity.
   Recovery opening loads need their own dynamic design case rather than this factor.
3. WO-09 owner-authorized fabrication/tests: cut/roll/seal tubes, fabricate plywood
   parts and jigs, print/finish nose and mechanisms, bond and index joints, assemble
   positive motor retention and independent recovery. Weigh/measure each assembly,
   perform sacrificial coupon/joint tests, deployment tests and instrumented thermal
   checks. ASA bulk temperature data do not validate a gimbal near a hot case.
4. WO-06/07/10: realistic sensor/actuator and fault models; PID baseline, committed
   PPO training with domain randomisation, export checks and HIL. Compare PID/RL
   fairly and retain poor transfer/failed runs. Policy <=3 layers/64 units, float32
   C on Cortex-M7; independent abort/recovery remains outside learned authority.
5. WO-11/12: club/RSO approval, conventional performance flights first, trainer PID
   then qualified RL, and finless PID/RL progression only after its separate control,
   abort and burnout-to-recovery gates. Full flight logs, paired predictions and
   held-out system identification. A finless unstable coast is not accepted by a
   static benchmark; any recovery-transition redesign creates a new configuration.

The custom build and serious RL project both survive this plan. No paid run,
procurement, physical fabrication/test or launch occurs in WO-01. GitHub pushes
and PRs are authorized separately under `AGENTS.md`; routine owner review is not
a development gate.
