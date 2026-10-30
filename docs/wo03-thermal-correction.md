# WO-03 aft thermal correction and operating-window screen

## Run and assumptions

Run `wo03-thermal-correction-20261030T223118695049Z` evaluates the 15°C/120°C lower history and the separate 35°C histories across all four modes, plus a combined 300°C/ε=0.9 sensitivity, conditional ambient probes, an ambient-bound search, CAD-mass sensitivities for two slotted glass-epoxy fin-can skin thicknesses, G54 connection-by-connection heat histories, and a CAD-reconciled Package A fixed-mount/bond sensitivity. The source snapshot remained unchanged (`inputs_unchanged: true`, 26 SHA256 inputs). Full case data and identities are in [record.json](../runs/wo03-thermal-correction-20261030T223118695049Z/record.json) and [candidate-results.json](../runs/wo03-thermal-correction-20261030T223118695049Z/candidate-results.json).

The 45°C aft-shell screen is unchanged. The original G54 35°C results remain visible and fail their two prior sensitivity cases: 46.33°C for a 300°C case peak with ε=0.3, and 47.10°C for a 250°C case peak with contaminated foil ε=0.9. The run also combines the 300°C peak, 120 s cooling time constant and ε=0.9 as a stronger sensitivity: G54 reaches 50.20°C at 35°C ambient. These are prescribed exploratory source histories, not measured motor-case temperatures.

| G54 ambient boundary | Case peak | Outer foil ε | Aft-shell peak | Margin to unchanged 45°C screen |
|---:|---:|---:|---:|---:|
| 35°C | 300°C | 0.3 | 46.33°C | −1.33 K |
| 35°C | 250°C | 0.9 | 47.10°C | −2.10 K |
| 35°C | 300°C | 0.9 | 50.20°C | −5.20 K |
| 32°C | 300°C | 0.3 | 43.48°C | +1.52 K |
| 32°C | 300°C | 0.9 | 47.39°C | −2.39 K |
| 30°C | 300°C | 0.3 | 41.58°C | +3.42 K |
| 30°C | 300°C | 0.9 | 45.52°C | −0.52 K |

The combined high-source/contaminated-surface case still fails at 30°C ambient. An 8-step search under that paired sensitivity estimates an ambient boundary of 29.41°C for zero margin and 26.21°C for a 3 K margin. Those temperatures are model boundaries, not validated weather limits. An operating restriction would need actual club/site conditions, sensor accuracy, prelaunch monitoring, and owner/RSO agreement; no restriction is adopted here. The original 35°C failures remain failures and are not reclassified as out-of-envelope passes.

## Slotted fin-can skin geometry and mass

The two CAD-mass candidates cover each mode's aft shell from 1.08 m to the lesser of 1.20 m or shell end. Thus the two performance modes use 120 mm of skin; the TVC modes end at the 1.175 m shell end, leaving the aft volume open. Both variants carry the three actual fin slots from 1.09 m to 1.19 m in the CAD shape.

| Mode | 0.25 mm skin: added mass range | CG shift range | 0.40 mm skin: added mass range | CG shift range |
|---|---:|---:|---:|---:|
| Performance | 9.11–10.54 g | 4.23–4.88 mm | 14.62–16.90 g | 6.73–7.76 mm |
| G54 performance | 9.11–10.54 g | 3.59–4.14 mm | 14.62–16.90 g | 5.72–6.60 mm |
| TVC finned | 7.16–8.28 g | 2.97–3.42 mm | 11.49–13.28 g | 4.73–5.46 mm |
| TVC finless | 7.16–8.28 g | 4.34–5.01 mm | 11.49–13.28 g | 6.92–7.98 mm |

Mass ranges use the configured density bracket 1600–1850 kg/m³ and CAD-integrated slot-cut volume; exact volume, inertia and shape hashes are recorded per row. The upper density matches generic G10/FR4 supplier data, while the low end is a process estimate for thin formed laminate. Supplier sheets are not evidence for this proposed layup: [Alro G10/FR4 TDS](https://www.alro.com/dataPDF/Plastics/TechnicalDataSheets/TDS_G10FR4.pdf) gives 1.85 specific gravity and 140°C maximum operating temperature; [Lork G10 data sheet](https://www.lorkindustrias.com/downloads/fichastecnicas/EPOXIGLASSG10DATASHEET.pdf) lists density 1.70–1.90 g/cm³ and 130°C service temperature. Neither establishes the proposed thin skin's through-thickness conductivity or specific heat. The requested 0.2–0.3 W/(m·K) and 1000–1200 J/(kg·K) remain study estimates pending an exact product/layup TDS and representative coupon measurements.

The 20 µm inboard foil from the prior bounded run reduced G54 peak from 46.33/47.10°C to 45.98/46.64°C in the 300°C/ε=0.3 and 250°C/ε=0.9 cases, respectively, but added 0.98 g and did not close either failure. Its archived record is `wo03-thermal-correction-20261030T214319909232Z`. The thermal solver does not simulate the new skin candidate: its radial barrier model would incorrectly turn the slotted skin into a continuous 360° opaque wall and seal the real fin openings. No skin thermal benefit or structural load-sharing benefit is claimed.

The skin CAD carries the actual slot interval 1.09–1.19 m. The CAD cutter's 6 mm dimension is radial depth; its 7.3 mm dimension is tangential slot width. Against the 6.35 mm fin root, the configured width gives 0.475 mm nominal clearance per flank, and the 6 mm radial cut passes through either skin thickness. These nominal dimensions do not verify angular alignment, assembly tolerance, adhesive squeeze-out or bond land. The TVC gimbal frame stays inside the shell's 32.5 mm inner radius. The thermal solver still cannot model the interrupted, slotted skin as a heat shield without falsely sealing the openings.

## Package A bonded mount sensitivity

The study copies the fixed G80 and conditional G54 vehicles, applies the two additional Package A mount rings, and recalculates mount mass properties from the CAD shape. It compares an open 0.5 mm radial gap against three slotted annular epoxy bridges. The bridge solids use the actual ring widths/stations and subtract the three fin-slot intersections; the CAD volume, multiplied by the configured 1200 kg/m³ density, yields about 1.1–2.3 g total adhesive across the tested gap bounds, with no fillet allowance. The rings keep their actual axial width in geometry; their radial conduction path is set separately to the 0.32, 0.50 or 0.68 mm gap. Per-ring ideal-wetted interface conductance is a declared 1,000,000 W/K modeling assumption. The package applies to discrete fixed mounts. The TVC modes use motor cassettes and rails, so Package A is recorded as not applicable rather than fabricating a fixed-mount change for them.

| Fixed-mount candidate | Gap / bond k | Added mass, G80 / G54 | G54 15°C/120°C | G54 35°C/250°C | G54 35°C/300°C | G54 35°C/250°C, ε=0.9 | G54 combined, 35°C | G54 combined, 25°C |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Open gap | 0.50 mm / — | 8.40 / 8.32 g | 15.41°C | 44.47°C | 46.91°C | 47.90°C | 51.20°C | 41.90°C |
| Bond, low bound | 0.68 mm / 0.15 W/(m·K) | 9.78 / 9.61 g | 15.35°C | 42.24°C | 44.09°C | 44.67°C | 47.15°C | 37.61°C |
| Bond, nominal | 0.50 mm / 0.20 W/(m·K) | 10.11 / 10.03 g | 15.32°C | 41.63°C | 43.27°C | 43.65°C | 45.83°C | 36.23°C |
| Bond, high bound | 0.32 mm / 0.25 W/(m·K) | 10.27 / 10.25 g | 15.31°C | 41.44°C | 43.00°C | 43.18°C | 45.19°C | 35.58°C |

These are aft-shell temperatures in °C. The 15°C/120°C row uses the declared lower case history, including its 30 s cooling constant. The next three columns preserve the original separate 35°C histories; the final two columns use the extra combined 300°C/120 s/ε=0.9 sensitivity at 35°C and a conditional 25°C ambient, respectively. G54 passes the unchanged 45°C shell screen on the bonded bounds for the two original separate failed cases (43.00–44.09°C for 300°C/ε=0.3; 43.18–44.67°C for 250°C/ε=0.9). Its combined 35°C result still fails at every tested bound, including the high-conductance case at 45.19°C. The combined 25°C probe is below 45°C in all four original vehicle configurations: 38.14°C G80, 40.83°C G54, 35.25°C TVC finned and 35.84°C TVC finless before candidate changes. This is a conditional model boundary, not an adopted weather restriction.

| G80 fixed-mount candidate | 15°C/120°C | 35°C/250°C | 35°C/300°C | 35°C/250°C, ε=0.9 | Combined, 35°C | Combined, 25°C |
|---|---:|---:|---:|---:|---:|---:|
| Open gap | 15.35°C | 42.57°C | 44.57°C | 45.81°C | 48.69°C | 39.25°C |
| Bond, low bound | 15.31°C | 40.84°C | 42.36°C | 43.13°C | 45.28°C | 35.64°C |
| Bond, nominal | 15.29°C | 40.42°C | 41.78°C | 42.32°C | 44.22°C | 34.54°C |
| Bond, high bound | 15.28°C | 40.34°C | 41.65°C | 42.00°C | 43.76°C | 34.08°C |

The bridge model treats each adhesive ring as a radial thermal pad with its computed CAD area and heat capacity. Adhesive conductivity, wetting/contact, bondline tolerance, fillets and mechanical load transfer are unverified. This thermal model does not establish bond shear/peel strength or durability; controlled bond-gap, coupon, proof, thermal-cycle and vibration tests remain required. Package A results are in-memory sensitivities and are not selected or adopted.

## Heat-flow explanation for mount/shell edge

The G54 heat-flow artifact samples the shared network rate calculation on each saved one-second solver state, then integrates forward and reverse energy on a refined dense-output grid with trapezoidal integration. Each radial-interface trace retains its axial segment. For the reference topology, the lumped `motor_mount -> aft_shell` contact carries net energy from shell to mount: −144 J in the 250°C/ε=0.3 upper hot-soak, −179 J in the 300°C/ε=0.3 case, −230 J in the 250°C/ε=0.9 contaminated case, and −285 J in the combined 300°C/ε=0.9 sensitivity. Positive direction in the trace is mount to shell; negative means the mount is cooling the shell. At the shell peak in those cases the broad edge removes about 1.33, 1.70, 1.93 and 2.44 W, respectively.

Removing that estimated lumped edge raised G54 shell peaks by 1.09°C, 1.37°C, 1.51°C and 1.88°C across those same cases. The direct radial-gap connection from mount to shell remains in the corrected topology and also flows toward the cooler mount near the shell peak, but it is much smaller (three axial segments each carry roughly 0.05–0.11 W in the reverse direction). The broad 0.2 W/K lumped contact is therefore an effective heat sink in this network, not a heat source. This explains the numerical increase after its removal; it does not validate the physical edge. The mount/shell radial clearance makes that broad contact geometry-inconsistent, and the solver contains estimated paths/properties rather than measured contact conductance. The heat traces show model causality, not a physical temperature prediction or a reason to restore the edge.

## Validation needs and status

Material properties/contact, external convection and emissivity remain estimates. Radially averaged node means omit local fin-root, slot-edge, bond, mount-plate and fastener hotspots; end-view-factor bypass and angularly interrupted barriers are unresolved. The combined 300°C/ε=0.9 case is a sensitivity, not an asserted operating case. The 45°C substrate screen is not relaxed.

Any later work would need an exact layup and resin system; measured density, conductivity, heat capacity and emissivity; a slot/root clearance and bond design; and instrumented heat-soak and vibration tests on representative assemblies. An ambient condition would need a calibrated site sensor and an explicit procedure that prevents launch outside the approved envelope. No physical test, material selection, active spec change or flight-ready conclusion is made.

All results retain `thermal_acceptance_passed: false` and `flight_ready: false`. No candidate is selected or adopted.
