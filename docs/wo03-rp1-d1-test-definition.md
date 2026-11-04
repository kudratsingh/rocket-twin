# D1 representative material and installed-root evidence definition

**Prepared plan only. No purchase, fabrication, specimen loading or supplier contact is authorized.** This defines the smallest staged evidence needed to choose ordinary plywood, FP1 or FR1 honestly; it is not a new admitted fin or permission to start detailed vehicle CAD/FEA. Use [D1's governing case and unknowns](wo03-rp1-load-attachment-decision.md) and the existing [AD1 cord/root article plan](wo03-rp1-representative-test-plan.md). Stop a stage if its inputs, fixture validity, process or uncertainty cannot support the next decision. No automatic testing of every material family is proposed.

## Documentation first

Reuse the [prepared material questions/register](wo03-rp1-joint-material-reconciliation.md) and existing cord questions, all UNSENT. Request exact product/lot, thickness and density tolerances, ply/layup direction, test method, E and shear G (direction identified), tension/compression/shear, conditioning and temperature retention. For carbon, distinguish laminate CLT/in-plane values from flexural/transverse values. For adhesive, request exact adherends, secondary surface preparation, cured film limits, cure, wet-out, peel/mixed-mode behavior and temperature/moisture dependence. Typical values or raw cord/fibre strength are not finished joint allowables. A supplier may have no such data; record unavailable rather than substitute an unrelated substrate.

If documentation suffices for a defensible conservative finite-root calculation, assess that before owner tests. Otherwise the owner would first review one selected material/process, safe fixture, conditioning, calibration and acceptance plan. Hardware is unpurchased; no owner measurement is requested now.

## Stage 1: actual-stock and process witnesses

Proposed plywood/control and bonded-strip dimensions are **150 ×25 mm**, cut with face-grain/span directions recorded. Record all veneer/skin thicknesses, moisture/conditioning, density/mass and cure. Use short/long fixture spans **60 and120 mm** to separate bending, transverse shear and fixture/indentation effects; reserve90 mm as a held-out check. These dimensions are a proposed method-development fixture, not a claim of ASTM conformity. Thin0.5 mm skin-only flexural fixtures require separate validity checks; do not force a thick-beam method onto them.

For a layered option only, prepare a process matrix using the exact5 mm ten-ply and0.5 mm cured-carbon products. Proposed FP1 receiving ranges4.8–5.2 and0.45–0.55 mm remain unverified. Target30 and50 µm secondary bond films only if wet-out, pressure, film measurement and surface condition demonstrate a repeatable non-starved joint. If the adhesive requires a larger film, stop the FP1 mass/stack assumption and define its explicit consequence before proceeding. Do not quietly assign a thicker film to the existing ledger.

Witness geometry for shear: **25 ×102 mm adherends,12.7 mm overlap**, with actual thickness/film/preparation. Witness for the skin termination:25 mm width, **45 mm bonded skin run +15 mm bare wood**, with the through-tab continuation **17.451 mm** where appropriate. Measure slip, peel/wood tear and skin/core separation under a representative bending/shear combination. A lap-shear mean does not establish termination peel. Determine replication, scatter and acceptance for the selected process in the owner-reviewed protocol; one good specimen is not an allowable. Maintain dry and applicable moisture/temperature conditions. The unchanged45°C substrate screen and existing hot/weak sensitivities remain in force; a resin's cure or Tg does not authorize hotter service.

## Stage 2: dimensioned finite installed-root article

Use an actual local article corresponding to vehicle axial stations **980–1220 mm** (240 mm long), nose datum0, positive axial coordinate aft. Use the selected supplier paper body's66.802 mm outer diameter and actual measured wall; do not treat the nominal bore as rigid. Motor tube OD31.369 / ID29.169 mm, z1055–1220; forward ring1060–1072.2 and aft ring1190–1196. The actual circular/slot contact and manufacturing tolerances must be documented, not inferred from these envelopes.

The fin retains the selected130 mm root /65 mm tip /60 mm span /45 mm sweep. Its tab runs **1080.2–1189.6**, radial depth17.451 mm, rounded inner flatR15.95. The **0.4 mm aft adhesive gap** and source-selected receiving process are present. The forward ring is **8.0 mm ahead of the tab start**, not a direct tab stop. Do not accidentally recreate the old front support in the fixture. Wood AD1, FP1 and FR1 have different thicknesses and slots; select only one defined arrangement after stage1 rather than combine them.

```text
nose datum → z980       1055 1060 1072.2 1080.2       1189.6 1190 1196 1220
actual paper body ───────────────────────────────────────────────────────
actual motor tube           ├───────────────────────────────────────────┤
forward ring                      [====]   tab==================. [aft]
recovery loop / knot                  loop [50×20×14 mm keep-out]
fin outside body                             integral panel, no rigid root clamp
body fixture contacts → outside the load region, with compliance measured
```

The recovery loop1072.2–1077 and knot envelope50×20×14 mm atz1077–1127, R16.5–30.5, sector60° must remain clear, including abrasion/heat sleeve and assembly tolerances. Fit a harmless motor-envelope mandrel only for fit/removal, not a live motor or an uncounted structural reinforcement. Reproduce aft fillets, ring bore/perimeter bonds, actual paper slot, finish and process masses. Demonstrate adhesive access and insertion sequence before cure. Use a fixture that loads the body as a body rather than clamping the fin root; measure fixture, body, ring and motor-tube motion independently so support compliance is not hidden.

## Loads, measurements and acceptance

The required **331.125 N and8.83 N·m are already factored once**. For a generalized root-input fixture, two forces at10 and40 mm outward from the body can reproduce that pair: **147.166667 N at10 mm and183.958333 N at40 mm**. Their sum and first moment match exactly. This is a root-input equivalence, **not the actual distributed pressure or a valid full-panel displacement test by itself**. A distributed-pressure/whiffletree fixture must reproduce the panel distribution or have independently justified fixture-to-pressure correction before comparing total fin-tip movement. A single8.83/0.06 tip force underloads root shear and is unacceptable.

Calibrate force and moment channels; use pure-force, pure-moment and combined cases to identify the reciprocal2×2 root compliance and its uncertainty. Reverse the fin-normal load; examine unequal fillet/contact engagement and root twist directions. Measure translation and rotation at the body-root cut, tab/motor tube, rings and remote paper body, plus outboard tip position and strain/slip where relevant. The proposed displacement-resolution goal is0.01 mm, subject to a demonstrated calibration/fixture uncertainty budget. Record force/moment balance, hysteresis, residual motion, cracking, local crushing, paper tear, adhesive peel and delamination. A balanced force calculation is not a capacity measurement.

For a validated panel model, combine its deformation with the measured **whole-root** response; do not add that response on top of FP1's fixed-cut tab and0.100 mm assumption. The nominal FP1 arithmetic leaves0.644264 mm for the whole root **before uncertainty**, but neither that budget nor a fitted spring is acceptance evidence. Total movement under the required matched load, including measurement/model uncertainty, must remain **≤1 mm**; retained material/adhesive screens must pass without damage/slip/separation. Fixture/material calibration uses separate data from the held-out evaluation. Define peak-versus-mean load, rate, replication and any sacrificial limit testing in the owner-reviewed protocol; D1 does not invent a proof factor on top of the already applied3.

After static evidence, installed vibration/ground modal measurements and a valid flutter assessment still need actual joint stiffness and material temperature bounds. A static proof or catalogue kit flight cannot qualify flutter, thermal, repeated loading, recovery or flight release.

## Small article parts and mass record

| Item | Definition / measurement | Decision resolved |
| --- | --- | --- |
| One selected fin plus integral tab | Actual minimum received stock; panel/tab mass and grain/layup | Directional panel/root stiffness, strength and process variation |
| Actual body240 mm / motor tube165 mm | Supplier stock, wall/OD/bore and deformation measured | Finite body/tube support and removal fit |
| Forward and aft rings | Source-defined notches/locations and actual stock | Ring/bore/perimeter route and true aft gap |
| Selected adhesive, fillets, edge/finish and recovery protection | Weigh before/after; include wet-out and waste installed on article | Finished joint mass, starvation/peel and clearance |
| Fixture, calibrated force/displacement channels, thermal/conditioning equipment | Separately designed/reviewed test equipment, not flight mass | Accuracy, safety and environmental validity |

No invented total test mass or cost is supplied while fixture and material choice are undecided. The article definition is ready for owner **review**, not physical execution. Stop if conditioned capacity, measurable compliance or repeatable film cannot be established. Report the specific evidence conflict before another fin variant. G80 construction remains the immediate goal; G54/G12 and their independent gates are unchanged.
