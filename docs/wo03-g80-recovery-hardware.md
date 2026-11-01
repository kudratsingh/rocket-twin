# G80 recovery controller and power interface proposal

**Recommendation for primary review:** retain the EasyMini v3.0 + Altus Metrum
1S 120 mAh cell pair and use C&K `T102SHZQE` as the next exact mechanical switch
candidate for primary review against the 1 A screening assumption. Its official
series datasheet rates Q-silver-contact non-TX01 models at 2 A / 28 VDC and defines
T102 as two-position OFF/ON; the table gives an SPST operating function, while family prose says SPDT. The selected S/H/Z/E suffixes specify actuator,
bushing, lug termination and epoxy seal; the mechanical figures below are the
series option drawing, not a separately published T102 assembly drawing.
This is a candidate recommendation only: the exact current pulse/load is not
established, the present SWA1 apertures do not provide a designed mount for this
4.95 mm threaded bushing, and the C&K switch mass is unpublished. The existing
Schurter SWA1 `0033.4518` remains a historical package input with no DC rating.

This is a bounded component/interface note, not a new packaging run. The existing
four-mode recovery packaging result remains the geometry source and reports
`+4.765 g` calculated mass, zero unexplained rigid intersections in the copies,
and `acceptance_passed=false`. It does not prove physical fit or electrical
operation. This work did not change active specs or CAD, rebuild the package,
purchase components, or perform physical work.

## Candidate component and interface table

| Interface | Exact candidate and sourced facts | Interface to carry forward | Unknown / limit |
|---|---|---|---|
| Recovery controller | Altus Metrum EasyMini v3.0; 38.1 × 20.32 mm outline, 6.5 g, 3.7–12 V input. Manufacturer outline gives a 13.97 × 31.75 mm four-hole pattern for M3 or 4-40 fasteners. | Reuse current copy's board front station 0.380 m, board holes at 0.383175 and 0.414925 m, four nylon standoffs, and terminal access. Follow the outline's marked board orientation. | The 6 mm component envelope is a study estimate. Actual terminal, USB and sensor-aperture keepouts/orientation have not been fit-checked. [Product](https://altusmetrum.org/EasyMini/), [manufacturer outline](https://altusmetrum.org/AltOS/doc/easymini-outline.pdf). |
| Dedicated cell | Altus Metrum / Garbee and Garbee 1S LiPo, 120 mAh, nominal 3.7 V, seller dimensions about 30 × 15 × 4 mm, 3.6 g. Seller states it has no over-current protection board. | Reuse its tray at 0.333 m, 16 mm internal width, 0.5 mm nominal side clearance each side, 8 mm band, and 17 mm nominal axial gap to the board. A 30 mm lead-service loop and 15 mm bend radius are placeholders only. | Match actual JST polarity and plug orientation to the exact board revision before connection. Confirm cell dimensions, retention, lead route and sag using the authorized ground-test procedure. [Seller product](https://shop.gag.com/product/120mah-lipo-battery/). |
| Controller battery connector | EasyMini has a two-pin JST-PH input for a nominal 3.7 V 1S LiPo. Manual identifies pin 1 as positive and pin 2 negative for non-Altus cells, and warns that other hobby packs may reverse polarity or include protection that interrupts pyro current. | Route the cell's own two-pin JST lead to the EasyMini battery connector; unplug by connector housing during service. Keep lead pair twisted and strain relieved. Preserve a safe pull path when the carrier is removed. | Seller does not publish the exact connector view/polarity drawing for this cell revision. Inspect physical plug polarity and mating direction before use; actual connector dimensions and cable bends are absent from CAD. [EasyMini manual §§3.1–3.4, 4.2, 5](https://altusmetrum.org/AltOS/doc/easymini.html). |
| Primary switch candidate | C&K `T102SHZQE`: T102 = two-position OFF/ON (SPST operating function; see supplier discrepancy below); S actuator 0.370 in (9.40 mm); H threaded flat bushing 0.220 in (5.59 mm); Z solder lug; Q silver contacts; E epoxy seal. Official datasheet gives 2 A at 28 VDC for Q-contact non-TX01 models and 30,000 cycles for other models. | Wire common terminal 2 in the recovery battery-positive feed and terminal 1 as switched output for ON; verify whether any unused terminal is present on the exact supplied part and keep it isolated. Mount in a new 4.95 mm panel hole, with rear terminal clearance and deliberate access. The S/H/Z series option drawing gives about 8.13 × 5.08 mm body envelope and 4.06 mm SP lug span. | At 1 A / nominal 3.7 V, the documented DC current rating covers the screening assumption only. This does not prove pulse/load compatibility or recovery qualification. C&K does not publish mass or a panel-thickness limit in the reviewed sheet; carry a 2.0 g placeholder estimate and weigh the exact part later. Its bushing dimension comes from the series option drawing; confirm exact T102 suffix drawing before CAD. [C&K T-series datasheet](https://www.ckswitches.com/media/1391/ttoggle.pdf). |
| Alternate small switch | E-Switch `200MSP3T1B1M2QEH`: silver-contact SPDT On-Off-On, panel mount, official listing 3 A / 28 VDC, 4.95 mm cutout, 9.40 mm actuator height. | Could be wired as one selected ON throw and OFF for center plus the unused throw. | Not preferred: its On-Off-On throw behavior is less direct for a two-state ARM/OFF control, and its PC-pin terminals need a separate connector/strain-relief interface. The 200 series official page/sheet does not publish mass or a panel-thickness limit in reviewed evidence. [E-Switch 200 series product](https://www.e-switch.com/product/200-series-subminiature-toggle-switch/), [exact variant sheet](https://configured-product-images.s3.amazonaws.com/2D/specs/200MSP3T1B1M2QEH.pdf). |
| Static-pressure interface | EasyMini is a barometric dual-deploy controller. The common-upper engineering notes already require static ports away from stagnation/wake pressure. | Keep the EasyMini pressure aperture exposed to a vented, representative ambient-pressure volume; the cell tray, carrier, tape, wiring and G11 plate must not seal or shadow it. Retain the existing vehicle's independent pressure-sensor function separately. | The outline/manual consulted here do not specify an EasyMini sensor-aperture keepout or port dimensions. No pressure-port path or pressure-equalization test was executed. Resolve from the v3.0 PCB artwork and the finished avionics-bay port geometry before adoption. |

The candidate wire intent is the existing four-edge topology: dedicated cell
positive → recovery switch → EasyMini positive input; dedicated cell return →
EasyMini return; EasyMini outputs → its isolated output harness. Keep recovery
positive **and return** separate from main battery, flight-computer/servo grounds,
GPIO, USB/data, sensors and conductive chassis paths. This is netlist intent,
not a continuity, isolation, arming or fault test. No initiator, deployment charge
or load is specified here.

The new C&K suggestion is for the G80 study only. It does not replace the completed
four-mode package, alter its `+4.765 g` result, or make that mass delta a universal
G12 budget. The C&K's 2.0 g mass is only a planning placeholder, not supplier data;
the alternative switch would require its own later mass/property accounting.

The switch sits at 0.470 m, separate from the existing main-avionics switch at
0.435 m. A small exposed toggle can snag on handling, clothing or packed recovery
materials. If the primary accepts the candidate, recess or guard it without making
the deliberate arming operation inaccessible, label the two systems distinctly,
and verify the mechanical OFF state during the separate service/arming procedure.

## Which geometry this note refers to

- Active G80 source identity: `c18abfee2444307e46eaaca55197693a3d9353bd8d8d8ac42162ffd238ef1d5e`.
- Selected separate motor-mount proposal: outer radius 32.2 mm, candidate identity
  `0a1ad4c196e7bbd046704199e99bad1f6649bc237c3c07b0e4f26118d4572c4b`; it changes
  the 32.3 mm radius and remains a candidate, not an active-spec edit.
- Recovery packaging basis: `runs/wo03-recovery-packaging-20261031T003400482420Z/record.json`.
  Its G80 copy has calculated loaded mass 744.227 g and the stated `+4.765 g`
  recovery-package increment. Those numbers do not include an executed merge with
  the 32.2 mm mount proposal.

The packaging carrier is G11, 92 × 26 × 1 mm, front station 0.333 m, centered at
body lateral `[0, +10]` mm. Three two-fastener support rows are at 0.360, 0.390 and
0.421 m, with 8.5 mm nominal carrier-to-sled clearance. The existing study places
the battery at 0.333 m and controller at 0.380 m; this leaves 17 mm between their
nominal axial envelopes. It models no flexible connector or wire. The independent
switch is at station 0.470 m; the existing main-avionics switch is distinct. The
packaging candidate's service sequence removes the aft module and six carrier
fasteners before carrier withdrawal; that sequence has not been physically
demonstrated.

## Minimal closure path

1. Primary reviews `T102SHZQE` for the declared 1 A screening assumption. Preserve
   positive-line isolation and freeze the actual current/pulse/load before any
   hardware qualification. If the actual duty exceeds its rating, reassess.
2. Primary reviews the C&K candidate before any design change. If selected, make
   a separate copy with a 4.95 mm bushing hole and inspect its 5.59 mm bushing,
   wall/doubler stack, nut/lock hardware, solder-lug keepout, wiring and external
   access. Do not enlarge/rewrite the completed SWA1 package in place.
3. Inspect the exact EasyMini v3.0 artwork and physical cell/plug. Freeze board
   orientation, pressure-aperture keepout, cable twist/strain relief, battery
   polarity, and extraction route on the selected 32.2 mm G80 candidate.
4. Only later, under the project's electrical safety/WO-09/10 gate, test the exact
   isolated board-cell-switch assembly with a manufacturer-approved representative
   load and verify open/closed state, continuity, sag, disconnect and absence of
   cross-connection. No such test occurred here.

This note closes no recovery strength, bulkhead/anchor load path, deployment,
packaging, electrical fault-isolation, G80 mount, thermal, flutter or flight gate.
The previously rejected industrial lifting-eye/steel-boss recovery-anchor
alternatives remain rejected; this switch assessment does not reopen them.

## Primary selection and later integration

The primary selects C&K `T102SHZQE` for the **next mounting study**, subject to
its actual panel, retention, terminal and access checks. It has not replaced the
SWA1 envelope in the frozen [52-part combined candidate](wo03-g80-integrated-candidate.md).
The supplier table specifies T102 OFF-NONE-ON with OPEN / terminal 2–1
connection (SPST operating function), while the family ordering prose calls it
SPDT. Retain this discrepancy and verify the exact purchased part; do not infer
an energized unused throw. The official Q-contact 2 A / 28 VDC rating supports
only the stated 1 A screening comparison, not an unspecified deployment load,
battery pulse, service life or electrical qualification. The 2 g mass remains
an estimate. [Official T-series sheet](https://www.ckswitches.com/media/1391/ttoggle.pdf).
