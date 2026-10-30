# WO-03 independent recovery power study

**Status:** bounded packaging/electrical proposal; not a selected or released design.
The active common upper still has a generic 20 × 20 × 10 mm, estimated 8 g
recovery-electronics box at front station 0.38 m and a net from the main battery.
These study options replace that placeholder only in
`configs/studies/wo03-recovery-power.yaml`. They do not change active vehicle specs,
authorize hardware, specify a deployment charge, or close WO-09/10 tests.

## Existing packaging and placement screen

The common upper gives a 66 mm body OD, a 210 mm avionics sled span from x=0.24 to
0.45 m, and 48 mm sled width. In the CAD generator, each part's `position_m` is its
**front** station; its axial bbox is `[position_m, position_m + bbox_m[0]]`. Thus the
installed primary 2S battery occupies x=0.245–0.300 m, flight computer 0.245–0.306 m,
IMU 0.315–0.335 m, barometer 0.318–0.333 m, high-g accelerometer 0.345–0.3706 m,
generic recovery box 0.380–0.400 m, microSD 0.405–0.425 m, pyro MOSFET 0.430–0.450 m,
and existing arming switch 0.435–0.447 m.

The lightweight option is EasyMini with the Altus Metrum 120 mAh 1S LiPo explicitly
supported by its manual; the RRC3+ alternative uses a Duracell MN1604 9 V source within
its 3.5–10 V range and optimized nominal voltage. A separate switch is reserved for
each option. Candidate front stations are: EasyMini battery 0.333 m and controller
0.380 m; RRC3+ battery 0.372 m and controller 0.380 m; separate switch station 0.415 m.
Proposed body lateral offsets are `[body-y, body-z]`; CAD maps these to
`[CAD-x, CAD-y] = [body-y, -body-z]` while longitudinal station is CAD z. This mapping
is explicit in the YAML. These are hypothetical AABB layouts, not finalized sled faces.

The EasyMini battery occupies x=0.333–0.363 m and its controller x=0.380–0.4181 m, a
17 mm axial gap. Battery overlaps the existing high-g accelerometer axially from
0.345–0.363 m; EasyMini overlaps the microSD axially from 0.405–0.4181 m. Their
proposed body-z offsets separate these simple boxes in the study, with no AABB
intersections against other extant named avionics boxes, except the replaced recovery
box. The battery/controller radial corner bounds are 15.88 / 19.38 mm in the 26 mm
radius bay.

The RRC3+ battery occupies x=0.372–0.4205 m and its board x=0.380–0.445 m. The battery
clears the high-g accelerometer axially by 1.4 mm but overlaps the microSD axially;
the RRC3+ board also overlaps the microSD, pyro MOSFET and existing arming switch
axially. Their proposed body-z offsets separate the boxes in the nominal AABB screen.
The RRC3+ board corner reaches 25.43 mm radius in the specified 26 mm bay; its battery
corner reaches 20.20 mm.

All these separation results depend on hypothetical offsets and simple boxes. The CAD
does not include a modeled recovery sled face, actual switch or battery terminals,
standoffs, connectors, wire exits, restraints or tolerances for this study. No installed
CAD fit or service access is claimed. The 17 mm axial gap in the EasyMini option does
not establish a safe wire route or repack/retention clearance.

| Bounded option | Published controller/battery data | Approximate added mass including explicit allowances | Layout note |
|---|---|---:|---|
| Altus Metrum EasyMini + 120 mAh 1S LiPo | EasyMini: dual-deploy, 38.1 × 20.3 mm board, 6.5 g, 3.7–12 V. Pack: 3.7 V, 120 mAh, ~30 × 15 × 4 mm, 3.6 g, seller-listed matching JST. | 25.8 g | 17 mm nominal axial gap between the pack and controller boxes; axial overlaps with high-g accel and microSD are separated only by hypothetical lateral offsets. |
| Missile Works RRC3+ + Duracell MN1604 | RRC3+: 65 × 25.5 mm board, ~14 g, 3.5–10 V; at 9 V, 6 mA quiescent, 35 mA during buzzer/LED, drogue/main outputs 2 A for 1 s and auxiliary 4 A for 1 s. MN1604: 9 V, typical 46 g, 22.8 cm³. | 80.2 g | RRC3+ board spans x=0.380–0.445 m and overlaps existing parts axially; nominal proposed body-z split avoids their simple box extents. RRC3+ additionally requires 4-40 mounting/standoffs and a sealed barometric bay with static ports. |

Mass totals add cited typical component masses and seller-listed switch mass (converted
from lb), **8 g carrier/restraint**, and **4 g wiring/service-connector allowances**.
The RRC3 option additionally includes the 9 V clip's seller-listed mass (converted from
lb). Allowances are not measured parts. EasyMini's 6 mm and RRC3+'s 6 mm thicknesses
are conservative study envelopes, not manufacturer dimensions. Battery retention,
wire lengths, strain relief, switch interface, connector dimensions, voltage sag and
built mass remain open.

## Electrical separation and safety boundary

Each study option gives recovery its own battery, switch and controller. Proposed
independent positive **and return** conductors stay within that recovery circuit. Do
not assume isolation if a shared ground, primary battery rail, charger, USB/data cable,
sensor, output, conductive mounting path, or harness connector can bridge the systems.
The exact fault-isolation topology must be resolved in the wiring diagram, then checked
for shorts/opens, inadvertent energization, continuity indication and arming states in
WO-09/10. The study does not specify any initiator, energetic charge, deployment
sequence, or pyrotechnic wiring.

For later service or wiring inspection, the assumed safe state is both the main
avionics pack and independent-recovery pack physically disconnected, with no energetic
load attached. An `OFF` switch position or software state alone is not treated as proof
of de-energization. The arming procedure and continuity check must be written and
independently verified in WO-09/10 before hardware work.

The EasyMini manual requires an external inline power switch and advises ground-testing
the selected battery against the chosen load; neither numeric EasyMini output-current
limits nor a guaranteed pulse load were located in the published product data used
here. RRC3 published output ratings do not demonstrate that a particular battery,
connector, wire or load combination is adequate. Duracell's typical internal impedance
and capacity curves do not provide a guaranteed pulse-voltage result for this assembly.
No output load or flight hardware is qualified by these values.

Both configs reserve a Schurter 0033.4501 rotary switch envelope. Seller data gives a
12.7 mm mounting hole and about 3.7 g. The existing common-upper arming switch is
already at x=0.435 m; a *separate* independent-recovery switch needs its own, safely
accessible wall location and power-only wiring. Its body may intrude into the sled
volume. Exact switch body clearance, panel-hole location, tool access, labeling,
connector retention, polarity keying, wire bend radius and strain relief are not
verified. The 4 g harness allowance is not a selected connector or wire gauge.

## Primary manufacturer/supplier references

- [Altus Metrum EasyMini specifications](https://altusmetrum.org/EasyMini/) — board size, weight, input-voltage range and dual-deploy capability.
- [EasyMini owner's manual](https://altusmetrum.org/AltOS/doc/easymini.html) — 1S LiPo support/recommendation, inline switch and ground-test notes; use exact model wiring instructions.
- [Altus Metrum 120 mAh battery](https://shop.gag.com/product/120mah-lipo-battery/) — nominal voltage/capacity, dimensions, mass, connector and protection-board statement.
- [Missile Works RRC3+ specifications](https://www.missileworks.com/rrc3) — board envelope/mass, power, current draw and output pulse ratings.
- [Missile Works RRC3+/RRC3 user manual](https://www.missileworks.com/downloads) — battery voltage/load testing, switch wiring, operating precautions, 4-40 mounting/standoffs and pressure-port requirements. The manufacturer download page links the primary manual.
- [Duracell MN1604 datasheet](https://www.duracell.com/wp-content/uploads/2020/02/9V-Duracell-Plus.pdf) — typical battery mass/volume, voltage, temperature range and load-dependence caveat.
- [Garbee and Garbee 9 V battery clip](https://shop.gag.com/product/9v-battery-clip/) — Keystone 233/Mouser 534-233 clip identity, wire lead length and seller mass.
- [Garbee and Garbee rotary switch](https://shop.gag.com/product/rotary-switch/) — Schurter 0033.4501 identity and seller dimensions/mass.

The figures above are manufacturer or supplier specifications, mostly typical values;
they are not test results for this vehicle. The layout positions, clearances, component
thickness envelopes and carrier/wire masses are study estimates. No availability or
purchase recommendation is implied.
