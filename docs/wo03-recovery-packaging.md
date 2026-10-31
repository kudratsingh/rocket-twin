# WO-03 independent recovery package candidate

**Status:** isolated copy only; not adopted, qualified, flight-ready or physically fitted. Run `wo03-recovery-packaging-20261030T234758724882Z` records `inputs_unchanged=true`, the four required independent recovery net edges in every copy, and `acceptance_passed=false`. The portable run record is `build/wo03-recovery-packaging/latest.json`; its four resolved copies and STEP/GLB exports are retained in the same ignored build tree.

Reproduce with:

```sh
XDG_CACHE_HOME=.cache .venv/bin/python scripts/wo03_recovery_packaging.py --config configs/platform.yaml --preset tiny
```

## Candidate layout

The copy replaces the existing ASA carrier and pins with a G11 plate 92 × 26 × 1 mm, beginning at station 0.333 m. It is centered at body +Z 8 mm (CAD Y −8 mm); board face stack positions are in `configs/studies/wo03-recovery-packaging.yaml`. The EasyMini is split into a 1.6 mm PCB envelope and an estimated 4.4 mm component keepout. Its published outline and four-hole locations are used, but actual component positions, relief adequacy and terminal/pressure-port clearances are not verified.

Four Ø5 mm nylon standoff envelopes span 6.4 mm between the PCB and carrier. Four nylon M3 screw/nut sets and six nylon M2.5 screw/nut envelopes are modeled with generic, estimated head and engagement dimensions. The cell remains a nominal 30 × 15 × 4 mm, 3.6 g 1S LiPo at station 0.333 m in a printed tray with an estimated woven retaining band. A 30 mm lead loop and 15 mm wire bend radius are placeholders; the connector and flexible wire have no CAD solid.

The carrier attaches at stations 0.360, 0.390 and 0.421 m, with two screws per row at x ±10.5 mm. The last row is centered within the existing 0.420 m crossbar. The plate ends at 0.425 m, leaving 4 mm aft of that row versus 35 mm for the earlier two-row layout. The third-row 4.6 mm head envelope has 0.6 mm nominal axial clearance to the EasyMini envelope end at 0.4181 m. A 6.5 mm carrier-to-sled face gap is represented by six 8 × 8 × 1 mm ASA pads. Local reinforcement, captive nut implementation and actual support contact are proposal geometry only.

An isolated 30 × 30 × 1.6 mm G11 switch doubler and radial panel opening are copied from the prior candidate. The nominal 6 mm × 25 mm tool corridor is only an envelope check, not installed switch access or a confirmed actuator interface. Exact switch variant and DC rating remain unconfirmed.

## Measured geometry screens and current failures

The 92 × 26 × 1 mm three-support beam screen uses estimated hot G11 modulus 5 GPa, assumed support conditions and point loads already including the project's factor. With I = 2.167 mm⁴, calculated deflection is 0.177 mm for the 3.4 N board load over a 30 mm span and 0.404 mm for the 7.6 N cell load at 12 mm overhang. These are simplified elastic calculations, not measured stiffness or allowable load. Hardware masses are CAD-envelope-derived with estimated material densities; package delta is +4.765 g in each copied mode, 2.153 g below the prior +6.918 g two-row candidate. This does not include weighing or resolve all omitted details.

| Mode | Loaded mass baseline → copy (g) | Burnout mass baseline → copy (g) | Loaded CG shift (mm) | Static margin with 50 g aft growth, loaded / burnout (cal) |
|---|---:|---:|---:|---:|
| Performance G80 | 739.462 → 744.227 | 676.962 → 681.727 | −2.415 | 1.351 / 1.764 |
| Performance G54 hypothesis | 817.991 → 822.756 | 721.191 → 725.956 | −2.308 | 1.080 / 1.594 |
| Finned TVC G12 | 780.147 → 784.912 | 698.147 → 702.912 | −2.339 | 1.254 / 1.746 |
| Finless TVC | 645.944 → 650.709 | 563.944 → 568.709 | −2.309 | −10.590 / −9.869 |

Copied CAD mass, CG and inertia are recomputed from the resolved copies; the complete state matrices are in `latest.json`. The finless static-margin values are not a valid acceptance measure. No flight result is implied.

The current exported solids do **not** fit without interference: five unallowed positive-volume intersections occur in each mode. They are microSD vs third-row sled fastener (2.454 mm³), regulator vs that fastener (2.454 mm³), EasyMini component keepout vs its screw heads (13.266 mm³), tray vs sled fasteners (0.096 mm³), and sled nuts vs sled fasteners (0.393 mm³). They are preserved as failures, not classified as acceptable contacts. The package is not fit for adoption until resolved and re-exported.

The modeled battery cell has 1.886 mm radial body clearance (1.386 mm after two 0.25 mm source-bound allowances) in its proposed lane; connector/lead protrusion is not modeled. The service sweep finds its radial lift and lateral move clear nominally, but flags the lift under expanded AABB bounds and collides with the interface coupler during aft extraction (at path fraction 0.870). The joint stop is also hit by expanded bounds near the exit. Battery replacement is therefore not demonstrated.

Carrier removal is nominal-BRep clear in three modes but the ±0.25 mm expanded-bound screen flags joint-stop proximity in all four. In the G54 hypothesis copy, a carrier fastener collides with the motor mount near the end of the modeled aft slide. This is an unresolved path failure. The simulation does not model disconnected leads, tool engagement, flex, or hands.

## Service sequence proposal

1. Put the independent recovery switch OFF, disconnect its 1S cell, and verify the system is unpowered before opening the bay. No arming or energetic-device procedure is specified here.
2. For controller/carrier service, disconnect the controller outputs and remove the six proposed carrier screws. Slide the assembly aft only after resolving the recorded interference and path failures; no present copy establishes successful extraction.
3. To replace the cell, release the estimated band, unplug by the connector housing, lift and move to the proposed body x +18.6 mm / body +Z 14 mm lane, then withdraw. The CAD sweep currently fails before extraction; this is a proposed direction, not a demonstrated service route. Confirm connector clearance, polarity, strain relief and cell restraint in a revised copy.
4. Repack the recovery bay from the nose toward the G11 bulkhead only after opening/retention and recovery routing are defined. No packed canopy, harness bend, volume, or fit is modeled or qualified.
5. Reassemble only with resolved fastener access and retention, then confirm switch OFF and electrical isolation. Switch actuator access is not represented by the clear geometric tool corridor.

## Evidence and remaining work

- The recovery copy netlist contains dedicated battery positive → switch → controller, a dedicated return, and controller output harness. It removes the shared main-battery edge. It has not been electrically tested.
- CAD-derived package mass/inertia changes are reported per mode. They are not measured hardware values.
- The required dimensional checks are controller component keepouts, connector and wire routing, carrier and cell removal, switch panel/actuator access, real fastener heads/thread engagement, and interference-free CAD after correction.
- The supporting parts still need detailed drawings, material/temperature allowables, attachment proof loads, vibration checks, and physical fit tests. Recovery attachment and deployment qualification remain separate gates.

Primary package facts: [EasyMini product/manual](https://altusmetrum.org/EasyMini/), [manufacturer outline drawing](https://altusmetrum.org/AltOS/doc/easymini-outline.pdf), and [120 mAh cell listing](https://shop.gag.com/product/120mah-lipo-battery/). Switch dimensions are based on the [Schurter SWA1 family drawing](https://www.schurter.com/en/pdf/english/typ_swa1__frontpl_.pdf); it does not establish the exact proposed variant's DC rating or installed interface.
