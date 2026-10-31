# WO-03 independent recovery package candidate

**Status:** isolated-copy proposal only; not adopted, physically assembled, qualified or flight-ready. The current four-mode run is [`wo03-recovery-packaging-20261031T003400482420Z`](../runs/wo03-recovery-packaging-20261031T003400482420Z/record.json): `inputs_unchanged=true`, zero unexplained CAD intersections in each copy, and `acceptance_passed=false`. Stable output is `build/wo03-recovery-packaging/latest.json`, with each mode's resolved copy and STEP/GLB export beneath the ignored build directory.

Reproduce with:

```sh
XDG_CACHE_HOME=.cache .venv/bin/python scripts/wo03_recovery_packaging.py --config configs/platform.yaml --preset tiny
```

## Candidate package

The copy replaces the active ASA carrier/pins with a G11 plate 92 × 26 × 1 mm, front station 0.333 m, centered at body +Z 10 mm. The EasyMini has its published PCB outline and four-hole pattern at stations 0.383175/0.414925 m; the actual component envelope remains an estimate. The proposed PCB sits on four Ø5 mm nylon standoffs with a component-side Ø5.4 mm relief and through-bored fasteners. The M3 head envelopes are Ø5.2 mm, leaving nominal 0.1 mm radial clearance within those component reliefs. Board keepouts, head geometry, thread length, preload, nut capture and vibration fit remain unverified.

The 1S LiPo cell uses a nominal 30 × 15 × 4 mm, 3.6 g source listing. A printed tray provides 16 mm nominal internal width around the cell with 0.5 mm side clearance per side, plus a proposed 8 mm woven band. Lead length, JST-PH orientation, wire strain relief and actual flex path are not modeled. The cell touches the tray support face in the nominal CAD arrangement; manufactured tolerance and restraint need physical fit checks.

The carrier attaches to copy-only crossbar reinforcement at stations 0.360, 0.390 and 0.421 m, two nylon M2.5 fasteners per row. The first row is moved to x ±11.5 mm to clear the tray; other rows remain at x ±10.5 mm. The G11 plate ends at 0.425 m, leaving 4 mm aft of the third row. The carrier sits 8.5 mm from the sled face. Six 8 × 8 × 1 mm ASA pads are represented at the supports. Local support strength, captured fastener retention and actual access remain unverified.

The independent rotary-switch copy retains its G11 doubler and panel opening. Its nominal straight tool corridor is an envelope only; exact switch variant, actuation, fasteners, DC rating and physical tool access remain open.

## Fit, service path and mass screens

The latest CAD export reports **zero unexplained positive-volume intersections in all four copies**, including the five conflicts in the prior failed run (`wo03-recovery-packaging-20261030T234758724882Z`). Nut envelopes are now centered on their shank axes with clear modeled bores; board head reliefs and the tray/first-row fastener gap are represented explicitly. This is nominal geometry checking, not a production tolerance fit.

Carrier removal is modeled only after removing the complete aft module at the existing module joint, disconnecting controller outputs and removing the six carrier fasteners. The swept assembly then moves aft 585 mm through the retained coupler. The finite BRep sweep samples 293 poses at no more than 1.997 mm spacing against remaining non-ring components. The coaxial body, coupler and keyed joint-stop are handled with explicit radial containment checks using a conservative outer radial bound of 23.542 mm. The limiting bore is 30.5 mm at the coupler, leaving 6.958 mm nominal and 6.458 mm after 0.25 mm tolerance on both package and bore. The joint-stop keyed bore is estimated from its key radius less key depth. All these CAD checks pass.

This sequence assumes the aft module and its `aft_interface_hardware` can be accessed and removed as a unit; physical joint fasteners, wiring disconnect, motor handling, tool access and retention are not demonstrated. It also assumes no unmodeled flexible wire or recovery-harness path obstructs the operation. The model checks the retained coupler as an annular bore and keeps the joint-stop key envelope in the clearance bound.

After the carrier has been withdrawn, the copied cell is disconnected, its band released, and the cell lifted outward 8 mm from the tray. The sampled BRep path is clear with the two-sided ±0.25 mm bound; the cell fits within the retained carrier outline. The connector and wire are not modeled, so their service clearance is unresolved. The cell is not moved through the assembled coupler.

The plate beam screen assumes hot G11 modulus 5 GPa and the specified loads already include the project's factor. With I = 2.167 mm⁴, calculated deflection is 0.177 mm for a 3.4 N board load over 30 mm and 0.404 mm for a 7.6 N cell load at 12 mm overhang. These are simplified linear-elastic estimates, not measured stiffness or strength allowables.

| Mode | Loaded mass baseline → copy (g) | Burnout mass baseline → copy (g) | Loaded CG shift (mm) | Static margin with 50 g aft growth, loaded / burnout (cal) |
|---|---:|---:|---:|---:|
| Performance G80 | 739.462 → 744.227 | 676.962 → 681.727 | −2.421 | 1.352 / 1.765 |
| Performance G54 hypothesis | 817.991 → 822.756 | 721.191 → 725.956 | −2.314 | 1.081 / 1.594 |
| Finned TVC G12 | 780.147 → 784.912 | 698.147 → 702.912 | −2.345 | 1.254 / 1.746 |
| Finless TVC | 645.944 → 650.709 | 563.944 → 568.709 | −2.316 | −10.590 / −9.869 |

The modeled package increment remains **+4.765 g** across all four copies, 2.153 g below the prior two-row candidate's +6.918 g. Carrier, tray, reinforcement, fastener and nut masses derive from CAD volume with estimated densities; the remaining old 6.283 g allowance is explicitly retained as 3.139 g residual. These are calculated values, not weighed hardware. Full inertia matrices and per-part mass accounting are in `latest.json`. Finless static-margin values are not an acceptance measure.

## Proposed service sequence and open items

1. Put the recovery switch OFF, unplug its dedicated battery, and verify the electronics are unpowered.
2. Disconnect required wiring, support the aft assembly, and remove the aft-module joint hardware; withdraw the aft module as a complete unit. Its physical separation/access sequence is not verified.
3. Remove the six carrier fasteners and controller output connections, then draw the carrier aft through the coupler opening. The solid sweep passes only for the modeled rigid parts; cables, hands and tools are not represented.
4. On the withdrawn carrier, release the cell band, unplug the cell by its connector housing, and lift the cell outward from the tray. Confirm polarity, connector clearance, strain relief and retention against the real parts.
5. Reinstall in reverse order, verify fastener engagement and switch OFF state, then perform the separate electrical/ground checks required by WO-09/10. No physical assembly or ground test has occurred.
6. Recovery packing is not represented: no canopy volume, harness path, packing direction or bulkhead access is qualified.

Remaining gates include component/pressure-port and terminal keepouts, connector and cable service path, switch access and rating, material and temperature allowables, crossbar and G11 attachment strength, actual module-joint access, vibration retention, dimensional tolerances, measured mass properties, and physical fit/proof tests. Netlist topology remains a copy-only proposal, not an electrical test.

Primary package sources: [EasyMini product/manual](https://altusmetrum.org/EasyMini/), [manufacturer outline drawing](https://altusmetrum.org/AltOS/doc/easymini-outline.pdf), [120 mAh cell listing](https://shop.gag.com/product/120mah-lipo-battery/), and [Schurter SWA1 family drawing](https://www.schurter.com/en/pdf/english/typ_swa1__frontpl_.pdf). The drawing does not establish the proposed exact variant's DC rating or installed interface.
