# WO-03 preliminary assembly and service notes

Status: preliminary design guidance from the resolved YAML, not a fabrication or
flight procedure. Dimensions are nominal spec envelopes. No measured fit, qualified
retention, recovery packing, connector routing, or service-time claim is made.

Regenerate station diagrams from the active platform manifest with:

```sh
uv run python scripts/wo03_service_diagrams.py --config configs/platform.yaml --preset tiny
```

Select another resolved platform mode with `--vehicle <resolved-id>`. The three
active assemblies have preliminary diagrams under `build/modular-performance-v1/service/`,
`build/modular-tvc-finned-v1/service/` and `build/modular-tvc-finless-v1/service/`.
Each directory contains `stations.svg` and `stations.png`; generated `build/` artifacts
are ignored. The PNG is rendered directly from the same resolved part stations and
envelopes as the SVG.

## Preliminary service sequence

1. Work with the vehicle unpowered. Disconnect/remove the battery first; inhibit the
   independent recovery circuit and physically disconnect any initiator leads. Verify
   both flight-control and recovery channels are unpowered before opening a module.
   The exact arming/interlock procedure and hardware are not yet defined or qualified.
2. Open the nose end to inspect the recovery bay. Remove the nose/shoulder using the
   as-yet-unverified retention method. Repack toward the nose only after a tested
   layout exists; neither the YAML's soft recovery envelope nor the drawing proves a
   real chute fits when folded. Preserve the separation path and do not route recovery
   harness across the electronics or motor service path.
3. For avionics service, open the adjacent upper/coupler modules and withdraw the
   removable sled along its rails. The battery's nominal envelope is 55 x 30 x 15 mm;
   sled, connector, restraint and hand/tool clearances remain to be checked together.
   Disconnect keyed, labeled plugs before withdrawing; provide strain relief at each
   fixed termination and enough documented service slack for the withdrawal path.
   Connector family, polarity keying, pinout, bend radius, slack length and strain-relief
   attachment are unresolved and belong in the WO-09 wiring/build pack.
4. Separate the upper body at the keyed modular interface to exchange the aft module.
   Confirm orientation/index marks and module identity before joining. The manifest
   gives a 66 mm outer diameter, separation station 0.52 m and nominal 50 mm overlap
   on each side. These are design inputs, not verified assembly clearances. Fastener
   access, insertion/removal force, adhesive/bond access, indexing tolerance and
   positive retention details remain open.
5. Service the motor from the aft end: remove its retention hardware, slide the motor
   aft out of the liner, inspect the liner/mount and reinstall only the exact selected
   motor configuration. Resolved finned-TVC spec envelopes show a 29 mm by 156 mm
   motor and 15.1 mm liner radius, with mount/liner starting at station 0.644 m.
   The 15.3 mm mount inner radius is only a nominal bound; closure, nozzle, lead and
   retention clearances and motor supplier drawing are not reconciled. Do not infer
   installed fit from these envelopes.
6. Before closing, check wire routing against coupler insertion and the complete
   gimbal sweep, verify every plug is seated and restrained, and confirm recovery
   wiring remains independent. Reinstall the modules in indexed orientation. Perform
   continuity/polarity checks only with initiators disconnected and per the later
   approved bench procedure. Any powered check, recovery test, proof load, or physical
   assembly is an owner-performed later-stage activity.

## Diagram interpretation and evidence boundary

The side-section station graphic is generated from `load_vehicle` resolving the
platform manifest and mode YAML. Positions and nominal envelope lengths come from
the resulting parts; annotations describe intended service directions, not a tested
packing or operation. Recovery soft envelope inputs are 0.15–0.205 m with a 55 x
40 x 40 mm bounding box inside the shoulder. This envelope is not a chute volume,
folding prescription, or physical qualification. The diagram deliberately does not
draw a packed parachute or invent attachment details. The actual cable path shown by
the CAD assemblies is likewise only CAD-visible; complete wire packing, bend radius,
strain relief and clearance through combined motion remain unverified.

The present nominal TVC design's sampled gimbal sweep passes 25 poses through
±4.9847 degrees. This is a nominal pose check, not a continuous swept-volume proof
and not a tolerance/wiring clearance finding. Full tolerance stack, supplier geometry,
connector routing and combined motion remain WO-03 closure items.

## Required drawing/template index for WO-09

The build pack should provide dimensioned, revision-controlled drawings for:

- Overall assembled vehicle and each of the three mode configurations, with datum,
  station reference, OD/ID, module boundaries, mass/CG and interface identification.
- Nose shoulder, upper tube cuts, keyed coupler, axial stop, key/index features and
  positive retention hardware, including tolerances and assembly/adhesive access.
- Recovery bulkhead and anchor geometry with actual purchased anchor/washer drawing,
  bond area, harness path and proof-load direction; no attachment is selected here.
- Avionics bay, sled rails/stops, electronics and battery mounting/restraint,
  connector locations, insertion path, service slack and clearance envelopes.
- Fixed aft and TVC aft interchange interfaces; motor mount/liner/retention and
  complete motor installed envelope based on selected supplier drawings; gimbal
  pivots, stops, servos, horns and pushrods in neutral and limit poses.
- Fin roots/slots and fin outlines for finned modes, plus any applicable alignment jig.

Provide 1:1 plywood cut/drill templates for the recovery bulkhead, motor centering or
retention pieces where plywood is actually adopted, fin alignment/build fixtures,
and all other plywood parts that emerge from the completed design. Each template
needs material thickness, grain direction, datum, hole/slot coordinates, kerf
allowance, revision and a scale-check bar; no unselected plywood geometry is presumed.

For every printed component include STL, material and machine profile, nozzle/line
width, layer height, walls/infill, supports, bed orientation, seam/support strategy,
critical-face post-processing, tolerance allowance and expected mass. The current
spec's generic `CAD Z on bed` orientation is a placeholder where no component-specific
orientation decision has been documented. Include supplier dimension drawings for
motors, closures, servos, bearings/pins, connectors, battery, recovery hardware and
any commercial electronics; reconcile drawing revision and measured received parts
before claiming fit.

## Open service/interface items

- Actual fastener sizes, tool access, torque/locking method, bond preparation and
  disassembly method at the nose, coupler, aft and recovery barrier.
- Selected motor and current supplier drawing; case/closure/nozzle/retention envelope.
- Recovery attachment, harness length/routing, folded canopy/line packing and safe
  deployment clearance.
- Connector part numbers, pinout/keying, wire gauge, strain relief, bend radius,
  slack/service loops, and wiring clearance over the full two-axis motion envelope.
- Sled/battery restraint, sliding stops, withdrawal direction and access with adjacent
  modules assembled.
- Tolerance/thermal stacks and measured fit; printed material orientation, bond and
  joint strength; repeated service wear and post-test inspection criteria.
- Independent recovery safe-state details and exact unpowered/arming verification.

Until these are resolved and checked against actual parts, the notes and diagram are
planning aids only. They do not close WO-03 mechanical integration or WO-09 build
acceptance and do not authorize physical use.
