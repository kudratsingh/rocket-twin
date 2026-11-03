# WO-03 recovery integration correction study

**Status:** isolated candidate, not adopted or released. No active vehicle configuration, CAD, mass cache, flight code or hardware was changed. The RUD M12/M16 industrial eye with structural-steel boss is rejected. This study now traces a light-material mechanical path from the recovery train through the upper G11 plate and across the detachable aft joint, and carries the EasyMini/1S wiring and service concept. The full path still fails important load-sharing, attachment and mass gates.

Reproduce the read-only calculation with:

```sh
.venv/bin/python scripts/wo03_recovery_correction_study.py --config configs/studies/wo03-recovery-correction.yaml --platform configs/platform.yaml
```

The ignored output is `build/wo03-recovery-correction/record.json`. It loads the four current platform assemblies through the standard vehicle loader and reconciled CAD mass data, hashes the active source/flight records before and after, and computes force screens using resolved part CG stations. This run does not simulate a deployment or qualify hardware.

## Independent recovery electronics and service geometry

The EasyMini v3 envelope is 38.1 × 20.32 mm. The Altus Metrum outline gives four 3.175 mm holes on a 13.97 × 31.75 mm pitch and allows 4-40 or M3 fasteners. A proposed 85 × 44 × 1.6 mm G10 plate is 10.56 g at the study density estimate; four M3 spacers/captured nuts have a 2 g allowance. The CAD/box positions are preliminary; screw-head, connector, sled-face, insertion and service clearances are still unverified.

Place the 30 × 15 × 4 mm, 3.6 g, 3.7 V nominal 120 mAh 1S cell at front station 0.333 m, body-Z center +12 mm. A 31.5 × 16.5 × 4.8 mm smooth G10 tray and 8 mm retaining band are proposed; keep pressure off the pouch and verify polarity/retention with the actual cell lot. The EasyMini uses JST-PH and its manual warns that other vendors may reverse polarity. The cell's pulse current, ESR and loaded voltage remain unknown.

The candidate switch is Schurter SWA1 0033.4518 with 0/1 markings, installed at 0.4843 m through a 15.875 mm external access port with a proposed 30 × 30 × 1.6 mm G11 doubler and 12.7 mm inner opening. Reserve a straight 6 mm coin or driver corridor 25 mm deep. The active body wall is 0.5 mm kraft; the panel hole effect, doubler bond, seal, anti-rotation and accidental-actuation guard have not been established. The manufacturer drawing is for the SWA1 family and the seller listing is a sibling 0033.4501 marked 110/220, so the exact 0/1 part, retention stack and DC contact rating must be confirmed. Its family 6.3 A / 250 V AC rating is not a 3.7 V DC rating.

Electrical path proposal: dedicated 1S positive → physical switch → EasyMini positive; dedicated negative returns directly to the EasyMini and stays isolated from the main flight-computer bus. Keep battery and output pairs twisted and separate. Placeholder service loop is 30 mm with 15 mm bend radius; 6 g is budgeted for leads/connectors/clamp. Verify strain relief, connector latch access, polarity, switch isolation and output compatibility on the bench. Output current and pulse duration remain null; no energy or firing capability is inferred from cell capacity.

Safe service sequence: keep both systems unarmed, switch OFF and disconnect/remove the recovery cell before carrier handling; separate the aft module and control/disconnect the output lead without pulling it; replace the cell with polarity and mechanical restraint verified; reconnect and secure the carrier; repack soft recovery from the nose toward the G11 plate; at every aft-joint exchange verify the four proposed removable links and all electrical connections. The panel tool corridor and the physical switch are still only envelopes, not verified access.

## Flight and recovery load basis

The latest current 27-case flight record is [`wo02-20261030T204849990760Z`](../runs/wo02-20261030T204849990760Z/record.json). It reports electronic apogee as the primary trigger and has no parachute inflation/drag transient. Its 12 s no-canopy motor-delay sensitivities give 22.393 m/s downward for G80 and 23.139 m/s downward for the G54 hypothesis. These are simulated no-canopy timing probes, not measured deployment speeds and not approved motor delays. Exact motor delay/charge behavior remains a hazard to bound.

The active engineering screen separately prescribes 5.0 m/s as an assumed nominal opening speed and 20.4 m/s as an off-nominal probe. Neither is emitted by the current canopy model. The prior 36.4 m/s G54 late-delay figure was from an earlier vehicle model and is retained only as historical context; it is superseded by the current 23.139 m/s probe. Independent apogee recovery remains the primary design path, but motor-delay behavior is not waived.

For comparison, using the same project factor of 3 and 0.3 m constant-deceleration travel gives:

| Configuration / scenario | Velocity basis | Factored upper G11 plate demand | Factored load crossing 0.92 m aft joint |
|---|---|---:|---:|
| G54 nominal screen | Assumed 5.0 m/s opening speed | 134 N | 85 N |
| G54 configured probe | Configured 20.4 m/s screen, not current model output | 1,832 N | 1,161 N |
| G80 current 12 s motor-delay probe | Current flight record, no canopy | 2,003 N | 1,196 N |
| G54 current 12 s motor-delay probe | Current flight record, no canopy | 2,349 N | 1,489 N |

The formula is `(resolved vehicle mass + 50 g allowance) × (v²/(2 × travel) + g) × 3`; there is no opening-shock multiplier. The 50 g allowance is conservatively placed aft of the modular joint for joint-force calculation. The interface demand uses only resolved component CGs aft of 0.92 m plus that allowance, rather than applying the whole rocket mass to every wall or joint. These remain prescribed load screens; none is a measured parachute force.

Without bypass reinforcement, the 66 mm OD × 0.5 mm kraft shell area is 103.67 mm². At the 1,832 N configured screen, wall-only average axial stress is 17.67 MPa; at the current G54 12 s no-canopy probe it is 22.66 MPa, against the 2 MPa estimated kraft screen. This exposes a deficient wall-only path under those scenarios. The axial load crossing the modular joint is much lower than the full anchor demand because only mass aft of the joint contributes, but the present keys are indexing/torque features, not rated axial retention.

## Lightweight detachable bypass candidate

The candidate uses four 10 × 0.5 mm pultruded carbon strips, arranged at 90° intervals from the existing 5 mm G11 recovery plate region to four detachable branch connections at the aft joint. Each path has an upper and aft strip segment totalling approximately 0.975 m between the recovery plate and aft load interface; a Peguet link at the 0.92 m split lets the modules separate. The strips would run along the body wall; the tube-interior path, strip-to-G11 end transition, module separation, wire/electronics interference and soft-pack snag clearance need a full assembly check.

At the forward plate, the study envelope proposes two radiused 7 × 15 mm slots with centers 24 mm apart (±12 mm lateral), for a sewn Kevlar loop lark's-head around the intervening G11 bridge. Four G11 clamp tabs (10 × 60 × 1 mm) retain the pultruded strips without drilling through them. At the keyed joint, four matched upper/aft G11 cleat pairs (10 × 45 × 1 mm, within the 50 mm overlap) clamp the split strip ends; one 4 mm Peguet connector links each pair to keep the modules removable. Two M2.5 fasteners per clamp are placeholder hardware. Clamp preload, carbon crushing/slip, slot-edge bearing, tab pullout, bond peel, tab-to-kraft adhesion and the joint's structural retention are unproven. These dimensions are a concrete study envelope, not final drawings or a build release.

The Easy Composites pultrusion datasheet gives representative lengthways tensile strength 400–500 MPa, modulus 28–40 GPa and density 1.30–1.50 g/cm³, and lists 80 °C maximum service temperature. It expressly says values are typical, not specification limits. For screening, this study uses the low-end modulus 28 GPa and estimates a 200 MPa hot stress bound as half the low-end typical tensile strength; the supplier does not publish this hot strength. Four strips give 20 mm² section, 4.0 kN combined capacity at that estimated 200 MPa screen before any additional factor, and about 27.3 g dry mass at estimated 1.4 g/cm³.

A perfect-bond axial stiffness model with the current 0.5 GPa kraft modulus gives about 97.6% carbon / 2.4% paper load share. At the 2,349 N G54 current delay probe, this predicts roughly 2.29 kN in the four strips and 55 N in the wall branch. If all four strips share equally, each strip carries about 0.57 kN at approximately 108 MPa; if one strip takes the whole carbon branch, its stress is about 430 MPa, above the estimated 200 MPa hot screen. The load share is not demonstrated; a single branch must be sized or tested against the whole branch demand before claiming capacity.

The same no-sharing check applies at interfaces. The G54 probe gives 1,489 N crossing the joint: one link carrying the complete joint force has a Peguet 4 mm WLL ratio of 1.32; equal four-link sharing would be 372 N per link, but equal sharing is not credited as a pass. Average bond shear on a 10 × 60 mm G11 tab is 0.62 MPa if four tabs share equally and 2.48 MPa if one tab carries the entire joint load. The project's 1 MPa hot adhesive screen is not an allowable and omits peel, edge concentration, moisture, temperature aging and local shell damage. At the G54 12 s probe's 2,349 N plate force, two-slot average bearing is 33.6 MPa if equally shared and 67.1 MPa if one slot carries the full force; G11 slot bearing strength is unavailable.

Peguet rates the MRSI04.0 4 mm stainless link at 13 g, 200 kg WLL (about 1,961 N) and 1,000 kg breaking load. Four links weigh 52 g. The 3/16 in Onebadhawk two-loop Kevlar harness page states 1,800 lb strength and standard 15 ft or 20 ft lengths but does not publish mass per length or loop capacity. The 0.8 m installed route is only a placeholder; the standard product is much longer and its cut-length, mass, packing and dynamic capacity remain unresolved.

| Estimated added part | Mass |
|---|---:|
| Four 0.975 m pultruded strips | 27.3 g |
| Four 4 mm links | 52 g |
| Twelve G11 tabs/clamps | 11 g |
| Small fastener allowance | 8 g |
| Adhesive and edge finish allowance | 5 g |
| Existing M3 eye removed | −4 g |
| **Net estimate before harness replacement mass** | **99.3 g** |

This is lighter than the rejected RUD steel-boss layouts, but it exceeds the 5–20 g increment target and omits the replacement harness mass delta. It is also not yet a complete rated load path: the actual G11 clamps and bonded tabs, four-way force distribution, aft joint load transfer and soft-pack clearance are not qualified. The candidate does not authorize hardware selection.

## Rejected industrial eye comparison

RUD RS-M12/M16 eyes were previously screened with steel tapped bosses/backers to meet manufacturer substrate engagement guidance. Their estimated system increments were 397 g and 583 g, respectively, and the steel structural boss violates the project's hard material scope. They are rejected and retained only as archived mass/WLL comparisons; neither is in the candidate path.

## Remaining gates

- Establish the actual design deployment-energy/load envelope, including canopy inflation and motor-delay contingencies; do not convert timing probes into opening-force measurements.
- Design and qualify the full branch path: harness sewn loop → two G11 slots/bridge → plate clamp → four carbon strips → G11 cleats → four detachable links → aft module retention. Check each branch for imbalance and every G11/adhesive/carbon contact for bearing, peel, slip, hot strength and fatigue.
- Confirm that the four links, G11 cleats and strips clear the inner tube, electronics, wires, recovery pack and removable joint motion; verify installation and extraction paths.
- Obtain mass and a compatible cut length for the selected harness; measure packed geometry and repack repeatability.
- Verify the EasyMini's exact mounting screw/head stack and board connector access, battery restraint and polarity, switch exact 0/1 part/stack/tool corridor, DC contacts, isolation and output pulse compatibility.
- Preserve current unverified ratings for M3 hardware, G11 plate, kraft shell, adhesives and the modular axial-retention interface; no structural pass is claimed.

## Sources

- [Altus Metrum EasyMini product page](https://altusmetrum.org/EasyMini/) and [owner's manual](https://altusmetrum.org/AltOS/doc/easymini.html) — 1S LiPo, nominal voltage, JST-PH polarity, ground-test requirements and voltage range.
- [EasyMini outline/drill drawing](https://altusmetrum.org/AltOS/doc/easymini-outline.pdf) — board outline, four-hole pattern and supported screw sizes.
- [Garbee and Garbee 120 mAh cell listing](https://shop.gag.com/product/120mah-lipo-battery/) — nominal voltage, capacity, dimensions and product mass claims.
- [Schurter SWA1 drawing](https://www.schurter.com/en/pdf/english/typ_swa1__frontpl_.pdf) and [Garbee and Garbee seller listing](https://shop.gag.com/product/rotary-switch/) — family actuation/dimensional basis; seller's marked variant differs from the proposed 0/1 part.
- [Peguet rigging Maillon Rapide](https://www.peguet.com/self-certified-maillon-rapide-quick-links/rigging-maillon-rapide) — manufacturer weight, WLL and breaking load.
- [Onebadhawk 3/16 in tubular Kevlar harness](https://onebadhawk.com/316-tubular-kevlar--2-loop.html) — manufacturer-stated strength and standard lengths; no linear mass listed.
- [Easy Composites carbon pultrusion data sheet](https://media.easycomposites.co.uk/datasheets/EC-TDS-Carbon-Fibre-Pultrusions.pdf) — typical axial properties, density, temperature rating and disclaimer.
- [RUD RS installation instructions](https://www.rud.com/fileadmin/rud.com/Produkte_PIM_Import/1-RS_EN_20240613_V04_FG.pdf) — basis for rejected steel-boss comparison.
