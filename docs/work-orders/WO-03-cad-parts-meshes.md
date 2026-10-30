# WO-03 — CAD parts and meshes

Branch: `wo-03-cad`. Tier: Mac CPU.

## Deliverables

1. `src/cad/`: one CadQuery generator per part type in the schema (nose cone with ogive/conical
   option and shoulder, body tube sections with couplers, avionics bay with sled and sensor
   mounts, battery tray, motor mount tube and retention, two-axis TVC gimbal with servo horns
   and linkages at the spec'd ratio, servo mounts, parachute bay and bulkhead, launch-rail
   guide, physical plywood fin sets and keyed interchangeable aft interface). Commercial parts (servos, Teensy, sensors, battery) as
   bounding-box placeholders with correct mass and mounting holes.
2. `scripts/wo03_cad.py --vehicle modular-tvc-finned-v1`: exports STEP, STL (print orientation applied)
   and GLB (via trimesh, one file per part + assembly) into `build/<vehicle>/`; writes
   `build/<vehicle>/manifest.json` with CAD-derived volume × density per part.
3. `print:` settings per printable part in the spec (orientation, layer height, infill, walls,
   supports yes/no, material). Justify walls, grain/layer direction and joint sections
   against load/heat cases; a universal 1.2 mm wall is not a structural qualification.
4. Mass cross-check report: CAD mass vs spec mass per part, flagged beyond 10 %.

## Benchmark

Every part generates; assembly GLB renders without gaps at the interfaces; CAD mass within
10 % of spec mass for every part (spec updated where CAD is the better estimate, with a note);
`make cad` regenerates `build/` from scratch.

## Notes

- Keep printed parts within a 220 × 220 × 250 mm build volume and split long tubes with
  couplers; the spec owns the split points.
- Design the gimbal and indexed aft joint so the sim's `tvc.py` linkage ratio and max
  deflection are exactly what the geometry allows; record the measured range in the spec.
- Use the CadQuery LLM-skill guidance (idiomatic workplane/selector style), not OpenSCAD-style
  boolean soup.

## Modular custom-build deliverables

Generate every resolved mode, shared upper once plus actual aft assemblies. Include
cut and bonded parts, fasteners, liners, fillets, finish and purchased envelopes;
commercial mass comes from supplier/measurement rather than solid-box density.
Verify gimbal/nozzle/retention sweeps, servo offsets, tube crushing, joint retention,
packing and service access. Export volume/inertia and reconcile moving versus fixed
parts with the twin. Custom construction and learning are objectives, not penalties.

Plan joint/buckling/bending, fin-root, recovery-opening and thermal tests with
explicit load assumptions and margins. Actual fabrication and proof/temperature
measurements are owner-authorized WO-09/10 work. CAD fit or a wall-thickness check
alone does not release hardware. Re-run per-mode static/flight checks after changes.
