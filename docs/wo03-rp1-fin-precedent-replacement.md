# RP1 fin precedents and a lightweight replacement screen

2026-11-03. Owner-requested research and bounded analytical preflight against frozen **G80-F2-RP1-AD1 v2**. This packet is independent of ongoing frontend work. No active vehicle, frozen failure, material limit, launch reference or physical-release gate is changed.

**Decision:** retain the conventional through-the-wall attachment topology. FP1, a carbon-faced plywood replacement, passes the declared nominal component calculations and saves **4.670 g**, but **is not admitted as an installed replacement**. Higher wood stiffness and lower carbon/shear stiffness expose failures; conditioned material bounds and the complete attachment are unverified. No examined kit manual provides those missing capacities. This is a useful lightweight test candidate, not a build authorization or a claim that the request's complete installed-pass objective has been achieved.

## What the comparable rockets actually establish

Here, through-the-wall means an integral fin tab passes through a body slot and reaches the motor tube. An epoxy fillet is the rounded adhesive joint along the fin/body intersection. The fin therefore transfers load through several bonds instead of relying on the outer paper surface alone.

| Manufacturer precedent | Exact G80 evidence | Construction relevant to this project | Evidence boundary |
| --- | --- | --- | --- |
| [Madcow 2.6-inch DX3 instructions](https://madcowrocketry.com/content/pdf/dx3.pdf), historical K-126 | G80T-7 explicitly listed | Three 1/8-inch plywood fins; tang bonded to motor tube, root to body, adhesive on tang sides and exterior fillets; centering rings clear of slots | Material grade, load, installed stiffness and hot strength unavailable; 15 oz is not explicitly loaded mass |
| [LOC Hi-Tech instructions](https://cdn.shopify.com/s/files/1/0568/7489/3503/files/PK-56_HiTech_Build_Instructions.pdf?v=1639515959), 2021 | G80-7 with MMA-2 adapter | Three-ring motor mount; fins between middle/aft rings, root bonds and exterior fillets | Examined manual does not establish fin thickness/material or a quantified ring/tab connection |
| [Madcow Solar Express instructions](https://www.madcowrocketry.com/content/pdf/solarexpress.pdf), historical K-111 | G80T-7 explicitly listed | Similar plywood/tang/motor-tube/body method | Same manufacturer's topology, not independent instrumented qualification |
| [AeroTech Initiator product](https://aerotech-rocketry.com/products/product_6884e3bb-9375-a3f8-ab43-42d8a31ec4ee) | G80-10T listed | Molded polymer fins with proprietary Fin-Lok mount | Different construction; capacity does not transfer to a plywood joint |
| [LOC Graduator instructions](https://cdn.shopify.com/s/files/1/0568/7489/3503/files/PK-16-Graduator.pdf?v=1623763227) | D–G range, no exact G80 established in examined instruction | Through-wall tabs; optional ring positioning at tabs | Supplementary construction precedent only |

These are documented commercial design precedents. They are not independent flight-test records for our geometry. In particular, copying a kit's 3.175 mm thickness does not demonstrate compliance with this project's much larger retained load and 1 mm movement screen. The complete source inventory and revision differences are in `docs/studies/rp1-fin-precedent-replacement/kit-precedents.json`.

## Frozen source, requirements and load audit

Source: `configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml`, SHA256 `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`.

- Three fins, root chord 130 mm, tip chord 65 mm, exposed span 60 mm, sweep 45 mm; planform and stations unchanged.
- Retain **8.83 N m factored root moment**, already including the factor of three once. A moment is the turning load at the fin attachment. The consistent distributed resultant for the current trapezoid is **331.125 N per fin**.
- Retain the estimated hot plywood modulus **1 GPa**, bending stress screen **5 MPa**, mean adhesive shear screen **1 MPa**, and complete-tip movement limit **1 mm**. GPa describes stiffness; MPa describes force per area. These remain estimates, not measured material allowables.
- Keep the 1.5 m usable-guide reference, formal 15 m/s departure requirement, separate 15.5 m/s planning target, full separate 50 g growth allowance, and adverse extra 20 g aft plus recorded motor-balance probe.

The 8.83 N m load was inherited from the earlier 90 mm-span fin. Direct calculation of the saved 40 kPa/5-degree sensitivity for the present smaller fin gives approximately 2.905 N m; the existing strip producer rescales it by **3.0393**, despite describing the difference as rounding. This packet **does not substitute the lower load**. It preserves the larger demand explicitly, avoids applying the design factor twice, and records the provenance issue for a later requirements decision. Aerodynamic load-case qualification remains open.

## Bounded comparison and proposed FP1 construction

The two screened construction families were redistribution of the existing wood braces and carbon-faced plywood. This was algebra and numerical integration, with no native solver, whole-vehicle CAD, new flight campaign or repetition of stopped finite-element attempts.

Keeping the brace wood volume constant while changing brace height from 15 to 60 mm never passed the ideal-root movement screen: the best sampled result was approximately **1.238 mm**. The existing brace arrangement gives **1.805 mm** and **7.301 MPa**, already failing with an ideal rigid attachment. Attachment flexibility cannot rescue that failure.

FP1 proposes:

1. Nominal **5 mm ten-ply Finnish birch** external fin and integral tab, with unchanged outer shape. Proposed receiving thickness window is 4.8–5.2 mm; density budget is at most 750 kg/m3. These are selection requirements, not supplier guarantees.
2. Nominal **0.5 mm cured balanced 0/90 carbon/epoxy faces on both sides**, covering the inner 45 mm of the exposed span and the complete tab. Orient a principal reinforcement direction along the span. Proposed incoming thickness is 0.45–0.55 mm per face.
3. Thin, controlled secondary epoxy bonds, 0.03–0.05 mm per face. These are process targets needing a demonstrated adhesive, preparation and clamping method. The model assumes full bond with no slip.
4. Replace the six wooden braces and their dedicated 4 g adhesive/finish increment. Retain the existing 14 g internal-bond and 10 g external-fillet allocations, ring bonds, root/end fills, slot fill and global finish. Carbon faces are a proposed replacement for brace stiffness; this function is not yet demonstrated in the installed assembly.
5. Keep the forward ring, Kevlar route, motor retention and aft service arrangement unchanged. There is **no new claimed direct tab-to-ring bearing**: the aft tab ends 0.4 mm ahead of the ring and its connection remains adhesive.

The maximum proposed stack is **6.4 mm**. Against the existing proposed minimum slot and closure allowances, the scalar remaining gap is approximately 0.15 mm per flank; this is conditional arithmetic, not manufactured fit. The carbon termination, corner radii, surface preparation, root fillet geometry and harness clearances need local details before manufacture. A sharp face termination is not accepted by this mean-stress calculation.

### Material leads and missing properties

[Aircraft Spruce](https://www.aircraftspruce.com/catalog/wppages/finnishbirch.php) lists nominal 5 mm ten-ply Finnish birch, part 02-20750. Its listing does not supply the required directional, conditioned stiffness/strength bounds or the proposed receiving tolerances.

[Carbon Composite AG CP005](https://www.carbon-composite.com/en/Carbon-Plate-0.5mm/CP005-2) describes balanced 0/90 cured sheet with characteristic flexural modulus 60 GPa, flexural strength 850 MPa and density 1.56 g/cm3. Those characteristic values do not establish a hot/wet lower bound or thickness guarantee. The FP1 screen's **45 GPa and 150 MPa** are explicitly provisional test requirements, not supplier-certified reductions. Glass-transition temperature is not a guarantee of unchanged stiffness or joint strength below that temperature.

The material inventory rejects several tempting substitutions: Easy Composites' thin-sheet flexural values are marked TBC; its XC130 300 g UD product links properties from a different twill coupon; room-temperature G10/G11 properties lack matching conditioned stiffness and direction. Tensile modulus is not silently substituted for missing flexural evidence. No exact adhesive is selected. The complete inventory is in `docs/studies/rp1-fin-precedent-replacement/material-sources.json`.

## Calculation, results and the reason admission stays open

The layered section uses the sum of each material's stiffness times its second moment of area, with a symmetric neutral axis and perfect bonding. Panel bending, core shear, and **finite tab bending/translation/shear under both moment and force** are included separately. The tab is not declared rigid. The motor-side boundary is still assumed fixed; the remaining tube/body/ring/fillet flexibility is unavailable.

The beam relations follow [University of Illinois composite-beam bending](https://mechref.engr.illinois.edu/sol/bending.html); the transverse-shear term follows [TU Delft's Timoshenko beam treatment](https://interactivetextbooks.citg.tudelft.nl/computational-modelling/structural_linear/timoshenko_md.html). This is a preliminary beam/laminated-section approximation, not an orthotropic plate solution or a proved bound on the complete joint.

| Declared nominal calculation | Demand | Provisional screen | Result at this point |
| --- | ---: | ---: | --- |
| Maximum wood bending stress, including tab base | 1.435 MPa | 5 MPa retained | Pass |
| Maximum carbon bending stress | 58.587 MPa | 150 MPa unverified | Pass |
| Wood-core shear | 0.757 MPa | 1 MPa unverified | Pass |
| Mean skin-bond shear | 0.551 MPa | 1 MPa estimated | Pass; no peel/free-edge capacity established |
| Panel bending | 0.253 mm | Part of 1 mm total | Included |
| Panel core shear | 0.103 mm | Part of total | Included |
| Finite-tab displacement contribution | 0.506 mm | Part of total | Included |
| Additional installed attachment allocation | 0.100 mm | **Unverified allocation** | Not a measured/modelled displacement |
| Total including that allocation | **0.961 mm** | 1 mm | **Conditional nominal pass only** |

The component subtotal leaves **0.1388 mm** for all further attachment motion, before any unmodelled plate, local contact or bond effects. The tab model's fixed motor-side boundary and skin termination need substantiation. Mean shear cannot establish resistance to peeling or layers separating.

The sensitivity results prevent an installed-pass claim:

| Diagnostic change, other inputs held fixed | Result | Decision |
| --- | --- | --- |
| Wood stiffness 8 GPa, retained 5 MPa stress screen | 7.124 MPa wood stress, despite lower movement | Fails: stiffer wood attracts more stress |
| Carbon stiffness 30 GPa | About 1.275 mm total | Fails movement |
| Wood shear stiffness 0.1 GPa | About 1.130 mm total | Fails movement |
| Additional attachment movement 0.25 mm | About 1.111 mm total | Fails movement |

These diagnostic inputs are not established property bounds. They demonstrate which evidence is needed; the nominal point does not establish robustness. A bounded thinner-core/thicker-face correction also exposed the same stress/mass trade. No further construction variant or expensive analysis is automatically authorized by this packet. The working recommendation is **FP1 for material/attachment validation**, with adoption held.

Three integration resolutions (400/1600/6400) give stable arithmetic at the declared nominal point. This checks quadrature accuracy only. It does not validate beam assumptions, full composite action, property values, thermal response or installed strength.

## Complete fin and vehicle budgets

All three fins, tabs and specified bond/finish additions are counted once. Maximum proposed incoming thickness/density is used for mass while minimum dimensions are used for nominal stiffness. This does not imply the bounds are available from a supplier.

| Fin allocation | Existing AD1 | FP1 estimate |
| --- | ---: | ---: |
| Wood external panels | 78.832 g | 68.445 g |
| Wood tabs | 25.918 g | 22.337 g |
| Wooden braces | 26.277 g | Removed conditionally |
| Brace-only bond/finish | 4.000 g | Removed conditionally |
| Carbon faces, panels + tabs | — | 35.177 g |
| New face bonds, including 50% process increment | — | 3.598 g |
| Face-end finish allocation | — | 0.800 g |
| Retained internal bonds + outer fillets | 24.000 g | 24.000 g |
| **Complete fin group** | **159.026 g** | **154.356 g** |

New adhesive and face-end allocations need manufacturing validation. Existing ring/fill/global-finish masses remain elsewhere in both vehicles; they are not free mass credits. Purchase cost is unavailable. Zero-cost placeholders exist only inside the temporary mass-helper copy and must never be used as a quoted bill of materials.

| Vehicle case, full separate 50 g included | Loaded mass | Loaded stability | Departure, saved 1.5 m guide model | Formal mass headroom | Planning mass headroom |
| --- | ---: | ---: | ---: | ---: | ---: |
| FP1, estimated 55 g nylon, nominal | 929.879 g | 1.461 calibres | 15.256 m/s | +28.465 g | -26.080 g |
| Same, extra 20 g aft + motor-balance probe | 949.879 g | 1.281 calibres | 15.075 m/s | +8.465 g | -46.080 g |
| 68 g nylon metadata probe, adverse | 962.879 g | 1.369 calibres | **14.960 m/s** | **-4.535 g** | -59.080 g |

A calibre is one body diameter between the balance point and the calculated aerodynamic-force location. Unchanged fin shape leaves the model's force location unchanged. The 68 g case is neither a measurement nor an upper bound. The proposed weight saving does not resolve uncertain finished harness mass or the separate planning-speed shortfall. Launch equipment is unconfirmed; no longer baseline is adopted. No new altitude, full inertia, flutter or flight claim is made.

## Next bounded deliverable and stop conditions

Before detailed installed analysis or adoption, resolve these together:

1. Establish actual stock thickness/density and conditioned directional stiffness, wood stress/strain capacity, core shear, and carbon compression/tension properties. In particular, establish the wood's upper stiffness alongside its strength; a lower stiffness floor alone is insufficient for layered stress sharing.
2. Identify the adhesive and preparation/press process. Define a representative fin/root article with actual motor tube, body slot, fillets and face terminations; calculate or measure total motion at the retained combined force/moment. Test design is documentation only here: no physical work, loading or purchase is authorized by this report.
3. Substantiate skin bond shear **and peel/delamination**, root bond loads, tube/body deformation, aft-end bond and recovery-route clearance. Demonstrate the complete attachment fits the available movement budget; do not assign a convenient spring stiffness without evidence.
4. Weigh a finished fin and identified recovery harness, then repeat the complete nominal/adverse mass, balance and departure calculations. Reject the candidate if needed correction consumes formal mass headroom, fails retained stress/movement criteria, or requires a changed load/material/guide/allowance to appear to pass.
5. Keep exact motor fit, thermal layout, installed flutter and recovery strength as separate open requirements. No numerical refinement, product precedent or passing CI closes those gates or WO-03.

No supplier message is sent and no owner action is required to read this packet. Material/process evidence or later owner-authorized samples are the first external needs.

## Reproduce and inspect

```bash
.venv/bin/python scripts/wo03_rp1_fin_precedent_replacement.py --out output/rp1-fin-screen-new-identity
.venv/bin/python -m pytest -q tests/test_rp1_fin_precedent_replacement.py
```

The producer refuses an existing output identity and a changed source hash. The study YAML includes frozen guide-model limits so reproduction does not depend on ignored local run directories. `docs/studies/rp1-fin-precedent-replacement/screen-record.json` preserves the published point calculations and diagnostic failures. Local drawings are under `output/fin-precedent-replacement-20261103/drawings/`; they are explanatory concepts, not CAD, browser acceptance or manufacturing drawings. No browser/computer-use operation was attempted.

Local validation: lint, formatting and strict type checks pass; all five new tests pass. The complete local suite reports **421 passed, three subtests passed, two failed**. Both failures are historical source-hash assertions caused by a local `src/vehicle/schema.py` variation: an extra `carbon_epoxy` allowlist line, SHA256 `9b801a824ae617fbd9f70d2b54c81045e54e38f42eb97d041d13482917bb42ee`, versus committed main's `e11d777cce363e45fd07376b45db4bde640cea00fefda8377ced735250de5093`. That shared-file variation is not required by FP1 and is excluded from this packet; historical expected hashes are preserved. Published calculations use the committed schema imported separately, with other helper and motor-curve identities recorded. Hosted checks apply to the focused PR's exact head; a local suite pass is not claimed.
