# G80-F2-C1 — bounded connection verification

Declared before numerical execution,2026-11-03. C1 here means F2 connection
packet1, not the historical C1 airframe. Frozen input is
`G80-F2-fixed-stock-ballast-v2`, spec SHA256
`7b188941de7fd4061800936c957b962d2165a5965c5cd9e46476d86242ed5a78`.
No active/shared vehicle, F1/F2 prior records, architecture or thresholds change.
G80 first; G54/G12 PID-to-RL remain separate committed tracks.

## Deliverables and admission boundaries

1. Supplier packet:12 uniqueURL/15min maximum, primary/manufacturer evidence only,
   exact78010/12912/19002 contact/removal and a light finished recovery attachment.
   Sol HIGH owns its two new source files. No contacting/buying/hardware work.
2. Physical connection/load audit: primary, oneCPU10CPU/20wall seconds of arithmetic;
   use all50 source rows, separate50g/+20g and saved motor-CG probe. Identify
   actual ring/tab/tube/body bond faces, load directions, fore/aft retained cuts,
   anchor/washer demands, uncertainty and mean/peak distinctions. Preserve
  20.4m/s,0.3m,DF3 once. Source missingness is unknown, not a pass or proof of
   hardware failure. No equal-sharing, perfectly rigid support or arbitrary force
   reduction. No new architecture/bracket sequence.
3. Local numerical method correction: reuse the exact recorded notched-ringSTEP,
   remove the thin tied steel volumes that produced the prior invalid middle
   mesh, and apply surface traction over the same provisional14OD/4.5ID contact
   footprints. No washer-contact stiffness or finished-anchor capacity is implied.
   Use the existing verified C3D10/SPRING1 exporter and saved known-answer evidence;
   one new single-element traction/axial known-answer fixture may exercise the new
   footprint/load integration with1% maximum displacement/stress error and1e-6
   resultant error. Three grids3.0/2.0/1.4mm, oneCPU,60CPU/120wall seconds per grid,
  180CPU/300wall aggregate. Check all sampled quadratic Jacobians positive and
   valid volume before solving. Require traction area within1% of analytic area,
   resultant1e-6, centroid0.05mm, force/moment/work balance1e-5 where evaluated,
   displacement last change<=5%, regional stress<=10%. A sharp peak that does not
   converge remains unavailable for strength. Reuse valid saved fixtures rather
   than recreate them. Stop the whole packet on the first invalid/timeout/failed
   known-answer case; no extra grid, solver, resource extension or blind retry.

The finite support springs remain an explicitly hypothetical component fixture;
actual global load allocation and joint compliance must be demonstrated separately.
Numerical method qualification is not installed recovery acceptance. Estimated
hot woodE1GPa/5MPa, paper500MPa/2MPa, hot bond1MPa and steel200MPa screens stay
unchanged. Isotropic vonMises output does not establish orthotropic wood capacity.
The45°C substrate screen/full required thermal matrix remains; no heat solver.

At most one fully counted local attachment correction may be screened after the
actual connection/material/occupancy basis is credible. If finished hardware,
actual support/load route or motor seat is unresolved, hold design adoption and
identify the exact missing input. No whole-vehicle CAD/FEA is admitted here.

## Coupled package and frontend

Any proposed correction counts all hardware, adhesive, shielding and service mass
once, re-evaluates nominal/adverse CG/stability/guide/recovery, and preserves1.5m,
formal15m/s/separate15.5 target. Current adverse formal headroom20.784g and planning
deficit33.761g are source-dependent. Longer equipment is unconfirmed. Reconcile
new geometry/spec identities before new fields; failed component diagnostics never
color the active assembly. No physical full-inertia/flight claim from envelopes.

Astra MEDIUM owns bounded design/workspace graphics refinement; Terra HIGH owns
read-only launch/preflight and interaction-checklist tooling. Primary owns shared
integration/engineering and offline rendering. Existing browser ownership
rejection is not retried/bypassed. FocusedPRs and required checks precede routine
merge; private repo and physical/purchase/paid/firmware/flight gates remain.

### Declared meshing and work-verification detail

Before execution: use straight-sided quadratic tetrahedra via Gmsh4.15.2
`Mesh.SecondOrderLinear=1`, not curved mid-edge nodes. Prove midpoint linearity
and positive corner determinants for every tetrahedron; this makes its Jacobian
constant throughout the element. Measure the polygonal CAD/footprint approximation
against exact volumes/areas. Use32/48/69 minimum circle nodes with3/2/1.4mm bulk
size, so curved-boundary approximation also refines. One geometric builder; no
post-failure strategy switch.100000nodes/grid is an additional pre-solve stop.
The [official manual](https://gmsh.info/doc/texinfo/) documents linear insertion;
the installed option was checked, not inferred from another release.

Use six-point quadratic-triangle surface integration; verify its nodal force and
first moment against an independently known flat triangle. Saved axial-bar and
SPRING1 fixtures are reused with hashes. Calculate continuum strain energy from
four C3D10 integration stresses and isotropic compliance, plus discrete spring
energy, and compare with half external work. Check reciprocal work between the
two unequal/single-eye cases. Report maximum and volume-weighted95th-percentile
principal/VM stress separately; regional convergence cannot qualify a sharp peak
or a finished orthotropic wood/bond/eye connection.

### One connected fit-definition proposal (declared before arithmetic)

The source's generic0.1mm linear tolerance does not say diameter versus radius;
ring/body and inner mount/end gaps are not automatically qualified by nominal
zero-intersection CAD. Screen one fit-to-measured-stock proposal only: forward/
aft ringOD64.4±0.05mm, bore31.90±0.05mm, nose annulusOD61.0±0.05mm;
notchwidth6.60±0.05mm; tab inner flat15.950±0.025mm, front1080.20±0.05mm,
end1189.60±0.05mm. Retain notchfloor1079.8 and aft-ringfront1190 with±0.05mm
proposed setup windows. BodyID64.9–65.15, plywood5.8–6.2 and mountOD31.25–31.45mm
are proposed incoming acceptance windows, not manufacturer tolerances. Nose
bore61.5–61.7mm and extra differential radial/axial±0.05mm remain unverified
conditioning bounds. Each clearance must still meet0.1mm. Before cutting, owner
measurement/conditioning must substantiate windows or the proposal stays unknown.

Count all additional filled adhesive volumes at1200kg/m3; retain the original
wood/tab mass allocations rather than earn removal credit before strength.
No anchor/hardware mass credit or ballast adjustment. Correct the stale13mm
ring learn text in this separately identified proposal only. Screen full mass,
CG, static margins, recovery and1.5/1.8m guide with the shared existing routines;
no full flight or accepted full inertia. This is a proposed fit correction, not
adoption: installed bonds/wood/eye/thermal/retention gates must also pass.
