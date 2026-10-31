# WO-03 thermal model correction record

**Status: scoped numerical correction evidence; engineering acceptance remains open.** The earlier single-point thermal pass is superseded as acceptance evidence. Its temperatures remain a historical result of the band model and are retained below for traceability. This report does not change requirements, active configuration, or WO-03 acceptance.

## What changed

The earlier `neutral-coaxial-material-shield-v3` model already solved radial gas conduction and radiation on common unknown gap surfaces behind solid half-wall resistances through `opaque_gap_flux`. Its required combined contaminated-foil point reported 44.3728°C at `motor_mount` and 44.7490°C at `aft_shell`, just under the unchanged 45°C paper/wood screen. Its deficiencies were missing finite ring/end radiation and erroneous parallel gas paths through occupied glue areas; the old result is not acceptance evidence for those corrected effects.

The corrected finite-transient runner introduces finite ring/end radiation and a new properly coupled common-surface exchange for the fixed G54 coaxial proxy. However, this 30-row proxy does **not** yet retain the actual 1.418% slot air/radiation path: the surface adapter treats slotted regions 2/3/4 as full-annular proxy exclusions. The separate CAD occupancy evidence below identifies open areas for a next actual-CAD correction; those open paths are not implemented in the current proxy. Direct/lumped contacts, case-cylinder exchange once, and shell external convection/radiation remain as recorded. See the finite transient record and the [method/rejected baffle report](wo03-finite-thermal.md).

| Evidence | Prior band model | Corrected common-surface proxy, combined 300°C / emissivity 0.9 / 35°C, high-k/low-cp |
| --- | ---: | ---: |
| Missing-end reservoirs set to ambient | Historical single-point: mount 44.3728°C; aft shell 44.7490°C | Mount 46.0580°C; aft shell 43.5252°C |
| Missing-end reservoirs set to case temperature | Not reported as a matching prior comparison | Mount 51.9741°C; aft shell 50.0834°C |
| 45°C substrate screen | Unchanged | Unchanged; mount fails both stated end-reservoir assumptions in this corner |

Temperatures above are **part averages** (the liner also has its separately reported radial field). The missing-end choices are explicit cold/hot assumptions, not measured bounds on the exact nozzle or end hardware. Neither is a demonstrated physical boundary condition. The corrected comparison is therefore a sensitivity demonstration, not a selected worst case or qualification result.

## Executed scope and results

Record: [`wo03-finite-transient-20261031T033109134738Z`](../runs/wo03-finite-transient-20261031T033109134738Z/record.json). It contains **5 cases × 3 coherent material-property corners × 2 end-reservoir modes = 30 rows**. All recorded source hashes are unchanged for this run (`inputs_unchanged: true`); candidate identity is `7aecfec03d1197a71be48a466b0530accf46b17a642382ef7ef484af6e6af531`, CAD revision hash `b3440d2b97dcaf525fc1f40c5cf224dda6d9e02fa7bedcb43d58f822a0793108`.

| Prescribed proxy case | Highest liner part-average | Worst 45°C substrate part-average (margin to 45°C) | Rows meeting all configured screen limits |
| --- | ---: | ---: | ---: |
| Lower case 15°C / 120°C, emissivity 0.1 | 96.770°C | Mount 15.866°C (+29.134 K) | 6/6 |
| Upper hot soak 250°C / emissivity 0.3 / 35°C ambient | 230.630°C | Mount 47.462°C (−2.462 K) | 5/6 |
| Case 300°C / emissivity 0.3 / 35°C ambient | 276.752°C | Mount 51.190°C (−6.190 K) | 2/6 |
| Contaminated 250°C / emissivity 0.9 / 35°C ambient | 230.462°C | Mount 48.052°C (−3.052 K) | 4/6 |
| Combined 300°C / emissivity 0.9 / 35°C ambient | 276.539°C | Mount 51.974°C (−6.974 K) | 2/6 |

The liner limit in these rows is 300°C. The screen also includes the unchanged 45°C paper/wood substrate limit; a liner peak below 300°C does not imply the mount or substrate passes. Across the full set, **19/30 rows pass all configured per-part screens**. Failures are preserved, including the required combined case failures; they are not averaged across assumptions. The `low_k_high_cp`, nominal, and `high_k_low_cp` factors are coherent sensitivity corners, not statistical confidence intervals or measured correlated material populations. The ambient/case end modes are each explicit, not a confidence range.

The 45°C substrate screen is unchanged from the acceptance configuration. No proposed 25°C controlled ambient or ignition-temperature restriction replaces the required 35°C robustness case. The 30-row record explicitly says `full_existing_required_matrix_complete: false`, `engineering_acceptance_passed: false`, `active_adoption: false`, and `flight_ready: false`.

### CAD occupancy evidence for the next actual-geometry correction

Record: [`wo03-interface-occupancy-20261031T032856133441Z`](../runs/wo03-interface-occupancy-20261031T032856133441Z/record.json). Nominal actual-CAD interface occupancy partitions each 3 mm circumferential region; it does not claim wetting, tolerance, or optical visibility.

| Interface region(s) | Full cylinder area per ring | Adhesive | Fin | Open |
| --- | ---: | ---: | ---: | ---: |
| `mount_shell_bond_0–1` (each ring) | 606.201718 mm² | 606.201718 mm² | 0 | 0 |
| `mount_shell_bond_2–4` (each ring) | 606.201718 mm² | 540.359846 mm² | 57.243246 mm² | 8.598626 mm² |

This independent occupancy partition shows where the actual geometry has open area, but the current 30-row proxy does not use this partition to restore those slot paths: its adapter marks slotted regions 2/3/4 as full-annular proxy exclusions. The 8.598626 mm²/ring open area (1.418% of the full cylinder area) therefore remains unavailable as gas/radiation exchange in this proxy. Occupancy is nominal mid-radius evidence only; actual radial continuity, visibility, bond wetting and tolerance remain separate questions.

### Numerical checks

Each of the 30 row output JSON files carries two analytic-versus-independent central-difference ODE Jacobian checks (60 total). All **60/60 passed** the recorded 0.001 relative tolerance. Across those checks, maximum temperature-derivative relative Frobenius error was `6.78e-8`, maximum boundary-energy derivative relative norm error `3.64e-9`, and maximum absolute boundary-derivative difference `1.35e-8 W/K`. These verify the implemented derivatives at two recorded states per run; they do not verify the physical model or demonstrate spatial/temperature convergence.

The maximum absolute integrated energy residual across the 30 transient outputs was `1.38e-6 J`. That is a numerical ledger check for the modeled system, not evidence that omitted physics or boundaries are small. Each row records solver evaluations and a maximum integration step of 1 s under the run's recorded current configuration (the acceptance matrix historically allowed up to 2 s). No claimed refinement study follows from this step control.

## Geometry and related unresolved evidence

### Later regenerated-pad proxy and fitting-baffle identities

The later pre-baffle grid is
`runs/wo03-finite-transient-20261031T035356786167Z/record.json`, physical candidate
`e25026…` / CAD `1193713…`. Every projected coaxial patch was verified equal before
reusing the sampled `7aec…` view matrix, and both identities remain recorded.
This equality does not cover the actual sector/slot geometry. At the combined
high-k/low-cp corner, ambient-end means are **46.058694°C mount / 43.525445°C shell**;
case-temperature ends give **51.974698°C / 50.083576°C**. Required failures remain.
Recorded part-mean Analysis fields have been exported at this exact identity;
uncovered parts remain unavailable, and the fields are not registered on the
active vehicle or the different baffle candidate.

The fitting baffle is a further candidate `69df790…`, recorded in
`runs/wo03-baffle-fit-20261031T035358211715Z/record.json`. Its 32 new physical parts
clear nominal hardware; all 24 panels pass the declared baffle-first rigid
sequence over 588 sampled poses. G54 loaded mass is **846.009911 g**, a **−0.078409 g**
change from its source; full-growth/depletion minimum static margin is
**1.197510 calibre** with independent RocketPy endpoint comparison passing.
These are fit/static results. Its thermal, structural and flight acceptance
remains open. Do not combine the pre-baffle temperatures above with this new
mass and call it one validated vehicle. G12 receives no baffle mass or thermal
credit from this different fixed-motor configuration.

The old candidate CAD identity has approximately 1 µm chord overlaps. It cannot supply uniquely material-tagged actual-CAD radiation surfaces. The primary agent created an **opt-in circular-pad correction candidate** in [`wo03-circular-pad-candidate-20261031T034153884353Z`](../runs/wo03-circular-pad-candidate-20261031T034153884353Z/record.json). That candidate is separate from active configuration. A verified cache refresh found the active geometry, material/CAD parameters, mass, CG and full inertias unchanged exactly; only cache identities were refreshed. Actual ray analysis and the required transient matrix on the candidate geometry remain outstanding. The older proxy and current exact-pad replay keep separate physical identities. Neither replay supplies temperatures for the fitting-baffle geometry.

A separate G12 fore-shield record, [`wo03-tvc-fore-shield-20261031T025947335730Z`](../runs/wo03-tvc-fore-shield-20261031T025947335730Z/record.json), adds 0.753216 g but still reports 45.912899°C and fails the substrate screen. It is not accepted. The proposed R26 ring-baffle geometry is rejected for nominal interference with actual mount rails; its evidence and limits are in [the finite thermal report](wo03-finite-thermal.md). The fitting-baffle candidate passes only its stated nominal fit, sampled assembly and static comparisons; it has no accepted thermal result.

## Actual fitting-baffle material layout and visibility

The current actual-CAD occupancy record is
`runs/wo03-interface-occupancy-20261031T040905840132Z/record.json`, at
candidate `69df790…` / generator `1193713…`. It independently repeats the
nominal partition on the **fitting-baffle** source. This replaces transferring
occupancy by inference from its earlier parent.

| Affected physical region | Material and mechanism | Midradius area per ring | Radial thickness | Correction and remaining assumption |
| --- | --- | ---: | ---: | --- |
| Mount-to-shell rings 0/1 | Epoxy conduction and its two material contacts | 606.201718 mm² | 0.680 mm | No parallel gas volume. Retain epoxy and contact uncertainty; no claim of measured wetting. |
| Slotted rings 2/3/4: glued portion | Epoxy conduction and contacts | 540.359846 mm² | 0.680 mm | Only the actual glued portion receives this path. |
| Slotted rings 2/3/4: fin-occupied portion | Plywood conduction, directional properties and its contacts | 57.243246 mm² | 0.680 mm region | No gas through the occupied fin. Installed contact/bond quality remains uncertain. |
| Slotted rings 2/3/4: genuine opening | Gas conduction; radiation only where first-hit geometry permits | 8.598626 mm² | 0.680 mm nominal region | Preserve the actual three-dimensional opening; this midradius area alone is not a radiative view factor. |
| Baffle notches, seams and supports | Gas around finite solids; opaque first-hit radiation; solid support conduction | Actual placed STEP faces, not a full annulus | Spec-owned 20 µm foil, 1.2 mm seams and 0.6 mm support stacks | All features remain in the void Boolean and optical surface map. No thermally sealed notch is invented. |

The area figures partition one interface; they are not independent full-area
allocations. Volume and three probe-thickness checks close their nominal
partition. Bond coverage, thickness, wetting and contact quality remain bounded
inputs requiring later physical measurement.

The actual first-hit radiation study now preserves every source solid, finite
ring end, slot, notch and seam. Its three fitting-baffle levels use
93,502 / 123,724 / 144,690 boundary triangles and
150,000 / 450,000 / 1,150,000 rays; zero rays escape. Fine raw area-weighted
reciprocity error is 1.195%; the last global exchange-area change is 3.184%.
**Local view-factor convergence is not established.** These are visibility
calculations, not a temperature or baffle-cooling result.

Some longitudinal foil-to-ring direct paths fall by 51–67% at point estimates,
but seven of eight end comparisons have uncertainty intervals including no
change. New baffle faces see their adjacent ring with view factors around
0.964–0.978. An equal-radiosity exchange-area diagnostic therefore does not
show that total ring heating falls. Gas exchange and the solid support path
must be solved with those same surfaces. See [actual CAD radiation](wo03-cad-radiation.md).

The subsequent [count-weighted operator check](wo03-cad-radiosity.md) rejects
the old unweighted balancing at 26 small-surface entries outside conservative
sampling intervals. Its count-likelihood replacement respects those intervals,
closure and reciprocity, but does not close local optical convergence. No
transient may silently use the rejected operator.

A [geometry-only candidate preview](../build/wo03-fitting-baffle-preview/actual-baffle-layout.png)
has been regenerated from all hash-checked actual placed STL assets. Its
compatible Analysis manifest explicitly marks temperature and thermal margins
unavailable, with no values or invented time axis. It cannot inherit the
pre-baffle proxy's fields. This refresh is offline WO-03 work; frontend and
computer-use development remain paused.

The frozen [material connection map](wo03-surface-materials.md) uniquely owns
all 1,785 fluid faces. It deliberately leaves 897 irregular faces without an
accepted half-wall approximation. Missing paths are not insulation. An explicit
[local-material-chord screening approximation](wo03-surface-chords.md) now covers
all 144,690 boundary triangles, with 97,496 exact BRep queries in152.39s. Its
three-point path variation reaches21-fold, so geometric completion is not
quadrature convergence or a bound on internal gradients. The coarse gas mesh
is valid but refinement failed/capped. Neither establishes thermal acceptance. Motor end/nozzle temperatures
and external opening conditions remain separate source hypotheses.

The independent common-surface gas/radiation fixture
`wo03-gas-radiation-20261031T051417456778Z` matches scalar parallel-plate
calorimetry over 6 / 48 / 384 tetrahedra: maximum heat error
3.86e-15 W, energy imbalance below 3e-15 W. A separate opening fixture holds
physical gas at 300 K while radiative brightness is 500 K. This verifies
coupling bookkeeping only. It does not supply rocket temperatures or qualify
local hot spots. [Coupling method](wo03-gas-radiation.md).

## Remaining acceptance work

This is not the full required matrix. The executed transient covers a fixed G54 coaxial proxy only. Required design closure still includes G80 and G12, all specified gap/contact variants, actual angular rails/slots/pads/end hardware, local hot spots and a new baffle design if retained. Actual material-tagged radiation has now been executed separately on the circular-pad and fitting-baffle geometries. Its local sampling uncertainty, gas coupling and the required transient matrix remain open. The motor case exterior history/bound, temperature-dependent material behavior and end boundary evidence also remain unresolved. These are **design acceptance items**, not silently deferred physical tests.

No result here closes structural or fit acceptance, and no purchasing, physical build/test, paid run, or flight-release gate is cleared. Exact-part thermocouple, bond/process and hot-soak measurements remain later owner-performed qualification after a design passes the required analytical gates.

## Reproduction

From the repository root, the corrected common-surface matrix is reproducible with:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python scripts/wo03_finite_transient.py --all-required
```

The related occupancy record is regenerated with:

```sh
.venv/bin/python scripts/wo03_interface_occupancy.py
```

This is the historically executed command under the run's recorded source snapshot. Since the CAD generator has changed since that snapshot, current-root execution may reject the old cached inputs; generate explicitly compatible current inputs before attempting a new run and do not assume this command reproduces the archived record as-is. The archived per-case JSON files and source hashes are the evidence for the values summarized here. The older band-model numbers are preserved in `runs/wo03-multilayer-shield-20261031T022026246942Z/thermal-results.json` solely as historical results, not current acceptance evidence.

## Correction closure for this increment

| Issue | Implemented correction / criterion | Current result | Evidence | Remaining verification |
| --- | --- | --- | --- | --- |
| Gas through adhesive-filled volume | Disjoint actual glue/fin/open occupancy; no duplicate material ownership | Nominal partition balances, real slots retained | Occupancy record040905; actual CAD boundary | Wetting/gap/contact ranges and physical bond inspection |
| Radiation through solid barriers or missing baffle notches | Opaque first-hit visibility using actual placed STEP | Zero escaped rays, all source faces retained; local ray uncertainty open | Actual CAD radiation / three optical levels | Thermal propagation and local sensitivity |
| Rail-colliding baffle | Notched/seamed20µm panels, indexed support stacks, baffle-first assembly | Nominal fit and588sampled assembly poses pass; thermal acceptance open | Fitting-baffle source035358 | Manufacturing/thermal tolerances, physical installation |
| Irregular material half walls | Exact normal-chord screening paths, explicit component/liner mappings | All141,699Robin facets covered; large local variation remains | Chord record051623, wall-energy QA | Solid-gradient and quadrature refinement; measured properties |
| Biased simple reciprocal fit | Count-likelihood fit, raw counts retained, simultaneous interval check | Old26-entry incompatibility rejected; replacement compatible | Radiosity record051129 | Local optical/temperature convergence |
| Gas discretization | Actual void tetrahedra, fixed source surface correspondence | Coarse passes; medium zero-volume and fine cap remain failures | Gas-mesh compact summary | Correct/validate mesh sequence and conditioning |
| Common-surface bookkeeping | Gas/radiation/halfwall solve and signed reservoir ledger | Independent scalar plate and separate opening-input checks pass | Coupling fixtures and tests | Corrected actual-candidate burn/soak matrix and energy/refinement |
| Compatible Analysis/preview | Exact revision geometry; unavailable temperature/margins | Consumer identity check passes; no stale fields transferred | Baffle preview record/Analysis manifest | Export compatible numeric histories only after actual solve |

The new geometry and screening package remains unaccepted. Part-average
calculations cannot establish missing local substrate temperatures. Actual
material/boundary/contact measurements stay in later owner-performed work;
open design/numerical findings above remain WO-03 acceptance items.
