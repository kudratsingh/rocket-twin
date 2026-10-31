# WO-03 explicit thermal acceptance matrix

## Decision and provenance

The explicit matrix is `wo03-thermal-matrix-20261030T230041977112Z`. The study record is [record.json](../runs/wo03-thermal-matrix-20261030T230041977112Z/record.json); its 420-row detail artifact is [matrix-results.json](../runs/wo03-thermal-matrix-20261030T230041977112Z/matrix-results.json). The record reports 28 source inputs unchanged. It carries the source candidate record `wo03-correction-package-20261030T224434934669Z`, exact hashes for all four resolved candidate YAMLs, current thermal/material/topology code, source vehicle files and motor curves. Every row retains the resolved candidate identity, thermal input corner, component peaks, declared-limit margins, CAD bond shape hashes, mass properties, prescribed histories, roles and evidence basis.

**Acceptance classification is OPEN.** The 45°C plywood/cardboard screen and original ambient/source cases are unchanged. The combined 300°C case / 120 s decay / ε=0.9 at 35°C is retained as a **required robustness case**. With no exact offered-motor case history and no measured correlation between foil aging/contamination and emissivity, the current evidence cannot justify excluding that physically possible combination. The 25°C rows are conditional operating-restriction probes only; they do not replace the 35°C cases or close this required robustness case. No candidate is newly adopted or flight ready.

The four evaluated resolved candidates are G80 (`G80-0.070`), conditional G54 (`G54-0.075`), finned G12 (`G12-F-0.070`) and finless G12 (`G12-L-0.070`). The Package A braced fixed-mount/bond geometry applies to G80 and G54. It is explicitly not applicable to the TVC cassette/rail mounts; the finned and finless candidates retain their own corrected support geometry and are evaluated without fabricated fixed-mount bond rings.

## Cases and roles

| Case | Boundary | Role/status in matrix |
|---|---|---|
| Lower reference | 15°C ambient, 120°C case peak, 30 s decay, configured ε=0.1 foil | Original lower-boundary reference; calculated screen only |
| Upper hot soak | 35°C, 250°C peak, 120 s decay, ε=0.3 foil | Required original 35°C case |
| High case | 35°C, 300°C peak, 120 s decay, ε=0.3 foil | Required original 35°C sensitivity |
| Contaminated foil | 35°C, 250°C peak, 120 s decay, ε=0.9 foil | Required original 35°C degradation sensitivity |
| Combined robustness | 35°C, 300°C peak, 120 s decay, ε=0.9 foil | Required robustness case pending stronger motor-history and foil-aging evidence |
| Conditional ambient probes | 25°C, each of the 250°C/ε=0.3, 300°C/ε=0.3 and 250°C/ε=0.9 histories | Operating-restriction proposal only; not an accepted ambient boundary |
| Conditional combined probe | 25°C, 300°C peak, 120 s decay, ε=0.9 foil | Operating-restriction robustness probe; not acceptance |

All prescribed motor-case histories remain exploratory exterior-temperature boundaries. They step to peak at ignition through source burnout, then decay exponentially; there is no internal propellant, combustion, case heat-capacity or plume model. The source basis is recorded in `configs/engineering/wo03.yaml`; the exact offered motor configuration, lot and measured exterior history are unavailable.

## Package A gap, adhesive and contact bounds

For the two fixed-mount candidates, the matrix rebuilds the mount and five tube bond-ring CAD solids at each radial-gap bound. Ring stations and widths stay tied to the resolved candidate; existing slot cuts are regenerated in the bond CAD solids. True CAD volume/centroid/inertia are recomputed for the modified mount and bonds. The three gap/conductivity combinations are low: 0.68 mm / 0.15 W/(m·K), nominal: 0.50 mm / 0.20 W/(m·K), and high: 0.32 mm / 0.25 W/(m·K). Adhesive density is 1200 kg/m³. Five-ring bond mass spans 1.09–2.31 g; the nominal 0.50 mm candidate is about 1.71 g. Fillets are excluded.

Each bond ring is a thermal node between `motor_mount` and `aft_shell`. The old broad direct mount-to-shell edge is removed for Package A candidates. Per-interface wetting/contact conductance is varied at 2, 10 and 50 W/K per ring, rather than using the previous 1,000,000 W/K ideal-wetted value. The CAD contact area is about 5.4–6.1×10⁻⁴ m² per ring (0.00283–0.00285 m² summed over five rings), so the tested interface range corresponds approximately to 3×10³–8×10⁴ W/(m²·K) per ring. These are estimated contact bounds, not measurements; actual bond-line wetting, voids, interfacial conductance and hot durability remain open.

Thermal material uncertainty uses three coherent sensitivity corners: conductivity ×0.7 / specific heat ×1.3, nominal, and conductivity ×1.3 / specific heat ×0.7. Explicit material-profile ranges are respected (for example the mica conductivity and heat-capacity ranges and G11 heat-capacity range). Adhesive conductivity is covered by the three gap/k candidates; adhesive heat capacity uses the same ±30% factors. These are sensitivity corners, not statistical confidence intervals, manufacturing tolerances, or measured correlations. Temperature-dependent degradation is unavailable. Foil ε uses each case's configured value and includes the ε=0.9 contaminated/aged sensitivity.

The calculation criterion for each row is that every part represented in the thermal network remains at or below its declared material screen. `PASS_SCREEN` means only that this particular calculation and input corner stayed within that screen. It does not infer hardware qualification, an exact motor history or local hotspot coverage. The overall acceptance status remains `OPEN` because the required robustness case is unsupported by motor-history/foil-aging evidence and fails in some bounded input corners.

## Calculated outcomes

For the original 35°C G54 cases, the bonded Package A candidate screens below 45°C in most, but not all, property/contact corners. Among 27 gap/contact/property combinations per required case, the G54 300°C/ε=0.3 case has 3 `FAIL_SCREEN` rows; its worst aft-shell result is 45.41°C (−0.41 K margin), at the low-conductance bond, 2 W/K interface and high-k/low-cp property corner. The G54 contaminated 250°C/ε=0.9 case has 6 failures among 27; the worst aft-shell result is 45.99°C (−0.99 K).

| Candidate | 35°C/250°C/ε=0.3: worst limited part | 35°C/300°C/ε=0.3 | 35°C/250°C/ε=0.9 | Combined 35°C required robustness |
|---|---:|---:|---:|---:|
| G80, bonded Package A | 41.83°C, +3.17 K | 43.51°C, +1.49 K | 44.29°C, +0.71 K | 46.73°C, −1.73 K |
| G54, bonded Package A | 43.32°C, +1.68 K | 45.41°C, −0.41 K | 45.99°C, −0.99 K | 48.78°C, −3.78 K |
| G12 finned, corrected TVC support | 42.24°C, +2.76 K | 43.93°C, +1.07 K | 44.04°C, +0.96 K | 46.30°C, −1.30 K |
| G12 finless, corrected TVC support | 42.48°C, +2.52 K | 44.24°C, +0.76 K | 44.44°C, +0.56 K | 46.82°C, −1.82 K |

Each listed value is the worst part temperature with a declared limit in that candidate's sampled uncertainty rows; margins use the unchanged part-specific limit. For G54, the original upper 250°C/ε=0.3 case passes every sampled row. The separate 300°C and contaminated-foil cases still have failures. G80 and the two TVC candidates pass every sampled row for the three original 35°C cases. All four candidates have combined 35°C failures in some sampled corners: 12/27 for G80, 22/27 for G54, 1/3 for finned G12 and 2/3 for finless G12. The combined case is therefore an active unresolved robustness failure, not silently downgraded to an optional sensitivity.

With a conditional 25°C ambient boundary, the combined case passes all tested rows: 27/27 each for G80 and G54 across the bond-gap, wetting/contact and property corners, and 3/3 for each TVC mode. Worst limited-part peaks are 37.19°C (G80), 39.34°C (G54), 36.77°C (finned G12) and 37.31°C (finless G12). The other 25°C source probes also pass their tested rows. This quantifies a possible operating-restriction benefit; it does not establish that 25°C ambient is available at the intended site, that a monitor/procedure can enforce it, or that the restriction should be adopted. The original 35°C failures remain in the matrix.

For reference, the nominal G54 bond/k case with nominal thermal properties and 10 W/K interface conductance gives 41.66°C for the original 35°C/250°C/ε=0.3 upper hot-soak, 43.32°C for 35°C/300°C/ε=0.3, 43.71°C for 35°C/250°C/ε=0.9, and 45.91°C for the combined 35°C case. The latter still exceeds the 45°C screen. Lower contact wetting and high-k/low-cp assumptions worsen the combined result further; stronger contact and low-k/high-cp assumptions improve it but do not demonstrate robust closure over the bounded cases.

## Conditional 25°C powered prelaunch warm-up

The follow-on warm-start matrix is `wo03-thermal-warm-matrix-20261030T231210015241Z`: [record.json](../runs/wo03-thermal-warm-matrix-20261030T231210015241Z/record.json) and [matrix-results.json](../runs/wo03-thermal-warm-matrix-20261030T231210015241Z/matrix-results.json). It reruns the 25°C combined 300°C/120 s/ε=0.9 proposal across the same full uncertainty set: 27 Package A gap/contact/property combinations each for G80 and G54, and all three material-property corners for each TVC candidate. All 60 rows screen within the unchanged part limits; overall acceptance remains `OPEN` and the 35°C required robustness failures remain unchanged.

The initial condition is a shaded/equilibrated vehicle at 25°C before arming. The model then runs 600 seconds before ignition with the case exterior and ordinary surroundings held at 25°C and the configured 1 W flight-computer heat source active. Thus all nodes start uniformly at ambient before the powered interval; ignition temperatures are calculated after the powered warm-up, rather than being initialized to 25°C at ignition. Solar heating is not modeled, so shade and the maximum-ambient sensor/monitoring condition are assumptions requiring an operating procedure.

| Candidate | Most restrictive part at ignition | Ignition screen margin | Worst post-burn combined peak | Minimum margin over tested corners |
|---|---:|---:|---:|---:|
| G80, bonded Package A | Aft shell 25.90°C | +19.10 K | Aft shell 37.81°C | +7.19 K |
| G54, bonded Package A | Aft shell 25.88°C | +19.12 K | Aft shell 39.95°C | +5.05 K |
| G12 finned, corrected TVC support | Aft shell 25.97°C | +19.03 K | Aft shell 37.35°C | +7.65 K |
| G12 finless, corrected TVC support | Aft shell 25.97°C | +19.03 K | Aft shell 37.89°C | +7.11 K |

The scenario-3 electronics load is the configured estimate 1 W, so 600 J is applied electrically before ignition. In the G54 low-conductance/high-k/low-cp corner, the modeled ignition shell mean is 25.88°C, flight-computer mean 29.43°C and battery mean 28.91°C. Its prelaunch stored energy is 216.36 J; the shared network reports 216.36 J net external energy and a 2.2×10⁻¹¹ J residual. Across the rows, the prelaunch energy balance closes to numerical precision; the full burn/300 s post-burn energy residual is below 1×10⁻⁹ J. These checks establish accounting consistency for the lumped model, not physical temperature accuracy.

This result shows the 25°C combined case remains under the present screens after the prescribed powered warm-up for these corners. It does not by itself adopt a provisional operating limit. The 35°C case remains required and failed in some corners; any proposed boundary needs site/ambient monitoring, a shade/prearm procedure, and later owner-performed instrumented burn/soak and hot-joint tests. No active thermal limit or vehicle boundary was changed.

## Conditional 25°C case with bounded ignition temperatures

The ignition-bound matrix is `wo03-thermal-ignition-bound-matrix-20261030T231809584945Z`: [record.json](../runs/wo03-thermal-ignition-bound-matrix-20261030T231809584945Z/record.json) and [matrix-results.json](../runs/wo03-thermal-ignition-bound-matrix-20261030T231809584945Z/matrix-results.json). It evaluates the combined 300°C/120 s/ε=0.9 boundary at 25°C ambient across the same 60 gap/contact/material uncertainty rows. The initial vehicle nodes are bounded to 30°C, except flight computer 40°C, battery 35°C, pitch/yaw servos 40°C and servo support 35°C. No powered prelaunch interval is applied. The configured motor-case history starts at 300°C at ignition. Components absent from a particular vehicle variant are recorded as absent; no thermal node is created for them.

| Candidate | Worst post-burn limited part/temperature | Minimum margin across its rows | Rows inside current limits |
|---|---:|---:|---:|
| G80, bonded Package A | Aft shell 40.27°C | +4.73 K | 27/27 |
| G54, bonded Package A | Aft shell 42.39°C | +2.61 K | 27/27 |
| G12 finned, corrected TVC support | Aft shell 39.85°C | +5.15 K | 3/3 |
| G12 finless, corrected TVC support | Aft shell 40.36°C | +4.64 K | 3/3 |

All 60 rows remain below the present component screens, but G54 does not retain the requested 3 K minimum margin: its worst margin is about 2.61 K. Therefore this sensitivity does not meet the full “all rows with at least 3 K margin” condition for a provisional 25°C envelope. The per-part initial bounds are a controlled/verified ignition-condition proposal, not a claim that ambient air or every component naturally equilibrates to those temperatures. No solar flux is calculated or measured. The proposal would require enforcing the ambient and component temperature bounds at ignition, with a shade/pre-arm procedure and WO09/WO11 instrumentation validation. This matrix does not adopt that envelope or change the unchanged 35°C cases and failures.

## Evidence still needed

The matrix does not establish local hot spots in bond rings, retention plates, fasteners, fin roots, foil seams, end faces or the TVC support. The radial thermal model uses lumped part means, simplified opaque annuli/gaps, estimated static-air transfer, approximate radiation, and axial support links. No result here is a physical temperature measurement or a material allowable.

Required evidence to close the thermal acceptance item:

- Exact motor exterior temperature history or a measured/conservatively bounded history for the offered motor configuration and lot.
- Foil emissivity measurements before/after exposure and an aging/contamination correlation that supports any exclusion of the combined case.
- Hot adhesive conductivity, heat capacity, gap, wetted area and interface conductance measurements on representative assemblies, including slot interruptions.
- Instrumented case, liner, support rings, front/aft pads, aft shell, fin root/bond, avionics, fasteners and gimbal measurements through burn and post-burn soak.
- Hot-joint strength and thermal-cycle evidence for the exact plywood/paper/adhesive, mica, foil, fastener and G11 grades and processes.

No boundary or temperature limit was relaxed, and no operating restriction or correction variant was selected. Matrix source and operating-proposal inputs are in [wo03-thermal-acceptance.yaml](../configs/engineering/wo03-thermal-acceptance.yaml); computed per-part evidence and row-level provenance are in the linked run artifact.
