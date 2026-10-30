# ADR-0008 — Adopt the combined WO-03 correction package

Status: adopted as reversible preliminary design, 2026-10-30. Expanded WO-03
acceptance remains open. No WO-04 start or hardware/flight release.

The recovery-only G54 prototype gave 0.991 calibre and failed the active 1.0
requirement. Combining its package with stronger fins, thermal barriers and motor
supports also changed mass, CG and inertia; a first combined revision again failed
at 0.961 calibre. Individual proposal passes therefore cannot establish acceptance.

Adopt one source-driven integrated package: a 400 mm shared-upper extension with
equipment forward; 5 mm G11 recovery load spreader; dedicated EasyMini/1S recovery
power; 70 x 120 x 6.35 mm rectangular plywood fins with tabs and twin 12 x 3 mm root
gussets; revised clearances and keyed joints; wider fixed-frame rails; a G11 thrust
web with integral bond fingers; separate front/aft mica compression pads, sleeve and
foil; removable bolted aft retention; and a machined G11 TVC cassette and gimbal.
The TVC cassette's fore relief and shortened first rail provide rod clearance;
two forward rails carry thrust. The finless model has no fin or fin-bond mass.

The 1,212 mm overall envelope includes retention/head projections. The 50 g growth
allowance remains explicit and may be placed at the aftmost station. Do not reduce
the 1.0-calibre passive margin gate or round a failure into a pass. The G12 trainer
retains its 10 m/s lower-thrust/growth/friction departure screen and provisionally
requires 5 m usable travel. Actual guide availability remains unconfirmed.

Reconcile CAD volume, estimated density, supplied/estimated masses, full inertia
and configuration-specific aerodynamics before static/flight comparison. Evaluate
hot plate/bond/rail/pin and fin/root loads, radial/axial thermal paths, motion and
tolerances together. Keep the opaque-wall model, serial mica resistance and
separate surface emissivities. A stainless fastener is no longer assigned a
generic electronics temperature limit; its conditional grade/assembly screen and
unresolved property-class evidence remain visible.

The orthotropic strip validates the solver method. The installed fin uses its own
geometry, mesh, directional strength and root demands; an ideal clamp does not
qualify peel, body backing, root stiffness or flutter. Preserve low-stress component
convergence failures even when dominant stress/displacement converge. Separate
coincident flight loads from noncoincident max-q times broadside-CN sensitivities.

Mode netlists previously overrode the shared independent-recovery power definition.
All active alternatives now use the dedicated battery, arming switch, return and
output bundle. A resolved-network regression catches recurrence. Graph separation
does not qualify continuity, firing current, EMC or common-cause independence.

G80 remains the performance reference, G54 conditional and G12 the PID-to-RL
configuration. Custom fabrication, maximum practical performance, committed RL,
the shared JAX/YAML architecture, independent RocketPy and existing sequence remain.
See the [closure table](../wo03-correction-closure.md) for current calculated results,
unresolved design items and separate owner-performed WO-09–11 verification. Purchases,
physical work, paid runs, WO-10 owner review and flight release remain gated.
