# WO-03 isolated EasyMini recovery-package proposal

Historical proposal/study evidence: its original source snapshot and results are preserved. The active combined adoption and current acceptance status are recorded in [ADR-0008](adr/0008-integrated-wo03-corrections.md) and [the integration closure table](wo03-correction-closure.md). Proposal-only statements below describe that study, not the current vehicle.


**Status:** preliminary copied-assembly study only. The active vehicle/common-upper YAML remains unchanged; this package is not hardware-frozen, qualified, or flight-ready. The copy starts from the lightweight Altus Metrum EasyMini v3.0 plus 1S 120 mAh battery proposal.

## Source facts and modeled package

Altus Metrum publishes EasyMini's 1.5 × 0.8 in (38.1 × 20.32 mm) board footprint, 6.5 g mass, and 3.7–12 V supply range ([product page](https://altusmetrum.org/EasyMini/)). Its outline drawing places four holes 0.125 in (3.175 mm) from the edges in a 0.550 × 1.250 in (13.97 × 31.75 mm) rectangle and says the pattern accepts 4-40 or M3 hardware ([manufacturer outline PDF](https://altusmetrum.org/AltOS/doc/easymini-outline.pdf)). That footprint and pattern drive the copied CAD. The 6 mm board thickness is an estimated envelope that includes terminal projection; it is not a manufacturer dimension.

The manual identifies the white two-pin JST-PH input for a 1S LiPo, recommends Altus Metrum batteries, says to twist the switch, battery and output-wire pairs, and requires an external power switch in-line with battery positive. It also says to ground-test the selected battery/load combination; the manual's generic 4–12 V prose differs from the product page's 3.7–12 V figure, so this proposal follows the specific 1S LiPo input documented elsewhere in the manual and still requires exact revision and load verification ([manual §§2.1, 3.1–3.4, 4.1–4.3](https://altusmetrum.org/AltOS/doc/easymini.html)).

| Item | Nominal mass | Geometry / basis |
|---|---:|---|
| EasyMini v3.0 | 6.5 g | Manufacturer footprint and hole pattern; 6 mm thickness is estimated |
| Dedicated 1S, 120 mAh LiPo | 3.6 g | Seller approximate 30 × 15 × 4 mm envelope; connector polarity/protection and pulse sag unverified ([seller listing](https://shop.gag.com/product/120mah-lipo-battery/)) |
| Separate positive-line rotary switch | 3.7 g | Seller-based estimate; 28.575 × 15.875 × 12.7 mm placeholder, no panel cutout or axis frozen ([seller listing](https://shop.gag.com/product/rotary-switch/)) |
| ASA carrier | 1.467 g | CadQuery block/rail volume × nominal 1,070 kg/m³; calculated, unmeasured printed mass |
| Nylon alignment-pin proxies | 0.25 g | Estimated cylindrical pins; head/thread/nut/preload not modeled |
| Unmodeled fasteners/restraint allowance | 6.283 g | Residual to keep carrier + pins + hardware at 8.0 g total; not a part geometry or verified retention design |
| Wiring/connector allowance | 4.0 g | Estimated mass; not a routed flexible-solid model |
| **Package total** | **25.8 g** | Increase of **17.8 g** versus replacing the old generic 8 g recovery-controller envelope |

The carrier uses the current `brackets` block generator for a battery support and two board rails. The four `pins` generator cylinders align to the published holes. They are not a completed retention mechanism: positive capture, pullout strength, anti-rotation, connector restraint and fastener material remain open. The 8 g combined carrier/restraint budget includes the CAD-derived carrier and pins; do not add another 8 g carrier allowance.

## Isolated electrical boundary

The copied netlist removes the existing shared-main-battery `RECOVERY_INDEPENDENT` feed. It adds only these functional edges:

- `RECOVERY_BAT_POS`: dedicated recovery battery → separate recovery power switch
- `RECOVERY_ARMED_POS`: switch → EasyMini
- `RECOVERY_RETURN`: dedicated battery return → EasyMini
- `RECOVERY_OUTPUT_BUNDLE`: EasyMini → its own unassigned output-harness envelope

No main-flight-computer battery rail, ground, GPIO, sensor, USB/data or shared arming-control edge is added to those nets. AWG 28/26 entries are placeholders, not selected wire or current ratings. The design does not model real leakage or common-cause paths through an actual switch, test equipment, USB cable, conductive structure or installed harness. It specifies no energetic device, initiator, charge, output current or firing connection. Isolation, battery sag and approved ground-load testing remain WO-09/10 work.

## Four copied-mode results

The generator copies the three active platform modes and the separate G54 performance hypothesis. It exports distinct assembly STEP/GLB and resolved-copy YAML under `build/wo03-recovery-package/<mode>/`. The latest reproducible record is [`runs/wo03-recovery-package-20261030T190729005110Z/record.json`](../runs/wo03-recovery-package-20261030T190729005110Z/record.json); the generated copies are ignored build outputs.

| Mode | Loaded mass baseline → package (g) | Burnout mass baseline → package (g) | CG shift, loaded / burnout (mm, forward negative) | 50 g aft-growth static margin baseline → package, loaded / burnout (cal) |
|---|---:|---:|---:|---:|
| Performance G80 | 460.59 → 478.39 | 398.09 → 415.89 | −3.47 / −2.31 | 1.185 → 1.248 / 1.649 → 1.703 |
| Performance G54 hypothesis | 534.36 → 552.16 | 437.56 → 455.36 | −3.74 / −2.82 | 0.928 → 0.991 / 1.449 → 1.506 |
| Finned TVC G12 | 549.71 → 567.51 | 467.71 → 485.51 | −3.73 / −3.01 | 1.234 → 1.296 / 1.681 → 1.738 |
| Finless TVC | 505.85 → 523.65 | 423.85 → 441.65 | −3.41 / −2.26 | −6.914 → −6.854 / −6.386 → −6.335* |

The complete baseline and package inertia matrices at loaded and burnout states are in the record. For compact comparison, diagonal inertia changes `(Ixx, Iyy, Izz)` in g·mm² were, loaded / burnout: G80 `(5.623, 180.965, 175.637) / (5.622, 81.523, 76.196)`; G54 `(5.623, 263.870, 258.542) / (5.623, 121.151, 115.823)`; finned TVC `(5.656, 276.286, 270.941) / (5.665, 147.628, 142.281)`; finless TVC `(5.653, 205.359, 200.006) / (5.661, 85.700, 80.342)`. Off-diagonal changes and all full matrices are retained in the JSON record.

Margins use the current calculated CP and place the full existing 50 g design growth allowance at the aft end for both end states. The G54 package improves its loaded value by about 0.063 cal, but **0.991 cal remains below the 1.0 cal screen**. Its copied WO-01 static-margin screen remains false; no requirement is waived. `*` Finless passive static margin is a CP diagnostic only and is not a valid controllability or stability pass for an actively controlled finless vehicle. All four copied WO-01 preliminary benchmark records remain false: `independent_static_reference` is false for all four, and G54 also fails `mode_static_margin_screen`. The package does not claim to fix those validation/design gaps.

Exact CAD checks found no BRep intersections between modeled rigid new envelopes (board with holes, battery, switch, carrier, and pins) and other rigid geometry in all four copied modes. Current generated solids validate. The output-harness and residual fastener/restraint budget are nonphysical distributed-budget representations excluded from rigid interference checks; therefore this result does not demonstrate wire or fastener fit. Purchased masses/envelopes are input estimates or sourced dimensions, not measured fit or proof of CAD mass accuracy.

## Access, physical fit and remaining work

Nominal stations use the project convention `position_m = front station`; axial bbox runs aft. Proposals: battery front 0.333 m at body offset `[0, +0.012]` m; EasyMini front 0.380 m at `[0, +0.0135]` m; switch front 0.415 m at `[0, −0.019]` m. At these positions the battery envelope spans 0.333–0.363 m and the board 0.380–0.4181 m. This gives a 17 mm nominal axial gap between those boxes. The switch and board overlap axially but use opposite hypothetical lateral offsets. These are coordinate screens, **not** actual face assignments or verified clearances.

Insertion/removal, tool access, body-wall switch hole, port exposure, battery restraint, terminal projection, board connector orientation, wiring route, pair twist, bend radius and strain relief were not fully CAD-checked. Current assembly CAD does not describe removable avionics-bay access faces, panel cuts, pressure-port paths, complete purchased terminal protrusions, or flexible harness geometry. No complete physical packing or insertion pass is claimed.

Before any adoption, WO-09/10 must establish the exact board and battery revisions, connector polarity and retention, switch panel geometry and safe unpowered state; manufacture and measure the carrier; check insertion/access and all clearances on complete CAD and hardware; and ground-test the exact dedicated battery, switch, controller and approved load. Root-level structural, thermal, fault-isolation, control, deployment, site and flight gates remain open. `flight_ready=false`.
