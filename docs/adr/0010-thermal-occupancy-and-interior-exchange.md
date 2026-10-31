# ADR-0010 — Physical occupancy and interior thermal exchange

Status: accepted model/traceability decision; candidate engineering acceptance open.

The expanded WO-03 requirements remain unchanged. In particular, keep the 45°C
paper/wood screen and the required 300°C motor-case / degraded foil / 35°C ambient
case through burn and soak. G80 remains reference, G54 conditional and G12 controls.

The previous radial-band model already solved gas conduction and radiation behind
common half-wall surface resistances. Its finite-end/ring visibility was incomplete,
and some annular gas paths also occupied explicit adhesive or fin material. A new
finite radiation operator must preserve that physical surface coupling rather than
adding radiation at bulk material temperatures.

Decisions:

- Partition one physical interface into its actual glued, other-solid and open
  portions from CAD. Retain conduction through adhesive and actual contacts;
  retain air and visible-surface radiation through genuine openings. Nominal CAD
  wetting is not measured bond coverage. Unknown potting cannot block radiation.
- Solve radiation and gas at the same massless surface temperatures behind the
  material half walls. Direct/lumped contacts remain separate and are counted once.
  Verify derivatives, energy balance, independent known cases and refinements.
- The primary radiative control volume is inside the tube at its actual inner
  radius. Exterior shell convection/radiation remains a separate existing model.
  At holes or absent tube, the control boundary is an explicit unknown reservoir,
  never fabricated paper. Exact nozzle/plume surroundings remain input uncertainty.
- Preserve the exterior-domain fin/body tangent-contact topology failure. Choosing
  the interior control volume does not repair that installed-root design defect.
- Curved mica pads may explicitly opt into exact circular radial boundaries. The
  older chordal primitive remains available for historical source reproduction.
  Opt-in corrections are candidate geometry; regenerate all caches and masses.
  The active vehicle retains its default geometry. Cache regeneration must prove
  its geometry, masses, CG and full inertia unchanged.
- Each revised candidate and operator retains its own specification, CAD, mesh,
  source and case identities. Reusing a projected radiation matrix requires an
  explicit equality check of every projected patch and records both identities;
  it does not transfer actual-CAD validity or hide excluded slots/pads.

The fitting baffle and any new package remain unaccepted until compatible
structural, thermal, fit/assembly, mass/guide, stability and flight/reference checks
pass. Scoped proxy results and optical fit studies cannot close the required matrix.
Physical qualification, purchases, paid runs, WO-10 owner review and flight release
remain separate gates. See [thermal evidence](../wo03-thermal-model-corrections.md),
[occupancy table](../wo03-interface-occupancy.md) and
[baffle fit/assembly study](../wo03-baffle-fit.md).
