# Next installed-root case for the refrozen G12 proposal

**Proposed next case: one elastic G12 fin-root/foundation load-path calculation,
with a deliberately ideal forward shell restraint.** It can test how the actual
potted tab and curved feet transmit the existing 57.629 N historical sensitivity
into the frame and shell, and whether a *conditional* foundation-stiffness
screen fails. It cannot by itself qualify the installed joint, prove a same-copy
aerodynamic envelope or close flutter. This is a case specification; no new
analysis is executed or passed here.

## Exact source and previously established results

Use `build/wo03-refreeze-g12-root-v1/resolved-candidate.json`, whose canonical
spec identity is `4ff75b8f2c6ab47ddf90b546761d7fa6d4a72c3af9f382e6b3790cbeb19c1287`
and file SHA-256 `8528d3f550ab31f53e51dcd894ce4dced1f3e6acec26f322d6f047270de192af`.
Use its manifest/record and original layered-fin STEP `74a4a92b…` and rounded
frame STEP `d012f279…`, not a native homogeneous fin or a generic frame missing
its saddle additions. The output `assembly.step` is inspectable; its component
interfaces and materials must be rebuilt as named, nonoverlapping analysis
regions rather than meshing the display compound as one material. The old
`81529f6a…` hoop YAML still has 60 stale-cache errors; the refrozen source is
the already reconciled 77-part identity, not a new design or the 69df G54 copy.

The published records establish a common-coordinate 3-DOF contact equilibrium
for a **rigid root and rigid, or hypothesized rotational, foundation**. For
0.1 mm foot bond and ideal body/frame support, feet carry 54.386 N and
1.9395 N·m; tab carries 3.243 N and 0.0775 N·m, summing to 57.629 N and
2.0170 N·m at the body tangent. Their shares change substantially when support
rotation changes. The independent contact quadrature and wrench-transport
checks pass for that reduction. They do not compute the flexible frame/shell
reactions or measure actual hot normal/peel capacity. The isolated panel estimate
is 0.606381 mm, leaving 0.393619 mm of the 1 mm service deflection budget for
root and foundation; the ideal bond solution has already consumed 0.001056 mm of
that remainder. Previous regional FEA component changes of 10.411%/26.797% and
22.909%/14.406% remain failures of the strict 10% criterion. See
[contact audit](wo03-installed-fin-closure-audit.md),
[load routing](wo03-fin-load-routing.md), and [refreeze](wo03-refreeze-g12-root.md).

## Geometry and required material ownership

Use the first-fin local axes: X radial outward, Y tangential, Z longitudinal
nose-to-aft. The fin is at 0°, and the other two fins need not be loaded for
this single-fin sensitivity; retain the full circumferential frame and shell so
that load may travel around them. The fin root is z=1.055–1.175 m, its 100 mm
tab z=1.065–1.165 m, and the frame z=1.012–1.180 m. Shell starts at z=0.922 m
and ends at 1.175 m; the shell slot and frame channel start at z=1.065 m. The
root is at nominal radius 33 mm. The tab is 2.5 mm deep; its channel has roughly
0.2 mm end and 1.15 mm side potting, with cylindrical clipping of its sidewalls.
Both curved feet have actual area 355.097 mm² each. The actual finite
frame/shell radial gap is 0.5 mm, with explicitly charged epoxy backing pads and
tab-channel cutouts. Preserve their actual extents and overlaps; do not replace
these contacts with a full circumferential tie or infer bonding from minimum
distance alone. [Geometry and material accounting](wo03-trainer-fin-package.md)
describes the provenance.

Use a **rigid root/gusset kinematic applicator** with its exact tab and two
foot surfaces; omit elastic panel deflection from this case and account for it
separately using the existing 0.606381 mm estimate. This matches the earlier
contact model's rigid-root assumption while introducing flexible G11 frame,
rails/rings, kraft shell, potting, feet and frame/shell pads. Omitted root/wood
and gusset flexibility makes the case optimistic, not a lower bound unless
all material properties and interfaces are also bounded appropriately. Use
finite, compatible normal-and-shear adhesive interfaces on the recorded tab
faces, foot footprints and pads. Full bonding and complete wetting are a named
ideal hypothesis; model neither unilateral open contact nor friction as an
unearned additional load path. Exclude the rejected deep-tab/open-cheek family.

The source fin STEP contains multiple materials, including carbon skins, PVC,
wood, gussets and epoxy, inside one compound. `scripts/wo03_trainer_fin_root.py`
constructed labeled layers historically; ensure any future checkout contains a
published, hash-matching recipe and exact material-to-solid ownership, or stop
before meshing. The original installed-root driver was local-only and must not
be an undeclared dependency. The ignored build artifacts and study inputs are
also required; verify their hashes and availability rather than assuming a clean
checkout can recreate them. Ownership, gap thickness, watertight shared
interfaces, positive volumes/Jacobians, no artificial overlap and correct
length units are hard preflight gates. A mesh lacking the 0.1–1.15 mm interfaces
or disconnected from an actual support is invalid, not an acceptable coarse
refinement.

## Load and restraints

Apply the **service** force `F=[0,+57.629073,0] N` at a rigid-root reference
point 35 mm radially beyond the 33 mm body-tangent point, at z=1.115 m. Through
the rigid root this is equivalent at the tangent to
`[Fx,Fy,Fz,Mx,My,Mz]=[0,57.629073,0,0,0,2.017018]` in N and N·m. Its
body-axis moment is 3.918777 N·m. The prior load is a transferred historical
q × CN=2 sensitivity, **not** a current same-candidate operating envelope.
The three unmodeled physical components are unknown; zeros here define this
specific planar case only. Do not apply both the offset force and an extra
2.017 N·m couple or multiply the service case by DF3 twice.

For this one diagnostic case, fix all three translations on the shell's
forward end cross-section at z=0.922 m; do not separately ground a frame, ring,
rail, tab or foot. The frame must reach that restraint through the modeled
finite pad, shell and their proper connections. Free all other exterior faces
unless physically connected by the modeled interface. The rigid front section
is an explicitly optimistic, unmeasured support hypothesis; actual coupler,
upper body, motor, retainer and their load sharing are not represented. This
boundary choice defines a reproducible case, not a claim that the real vehicle
has a clamped forward joint. If a physically sound model cannot be constrained
without artificial support, report the unsupported mode and stop. The original
mechanism must not be moved or modified to make this model fit.

Use the historical estimated **hot** adhesive E=1 GPa and Poisson 0.3 for the
0.1 mm foot bond case; assign tab potting and pads their recorded finite
geometry and the same explicitly stated estimate only where that is the actual
source assumption. Apply the existing G11 hot E=5 GPa estimate, plus documented
cardboard, wood and laminate directional stiffness estimates from
`configs/engineering/wo03.yaml` and
`configs/studies/wo03-trainer-fin-package.yaml`; identify each adopted cold/hot
reduction, orientation and thickness. Where an essential directional or hot
constant has no defensible recorded value, leave it unavailable and stop before
calling the result representative. Do not supply a generic isotropic value as
measured G11 interlaminar, paper peel, adhesive peel or bond fatigue strength.
The retained 45°C substrate condition is a screen, not a proved temperature or
an adhesive allowable. No thermal result is imported as a structural pass.

## Execution and decision gates

1. Before this case, independently verify the solver and interface formulation
   on an analytical planar finite adhesive patch with coupled translation and
   rotation, including a nonzero force and moment and its reaction at a shifted
   reference. Reproduce the existing patch-matrix known answer to 1e-10 relative
   and check both force and moment equilibrium independently. If the selected
   solver cannot express these interfaces and output the required quantities,
   stop rather than silently alter the boundary condition.
2. Preflight counts, per-material mapping, disconnected parts, element quality,
   thin-gap resolution and predicted memory. Declare one CPU worker, at most
   120 seconds wall per mesh/solve child and at most 600 CPU seconds for the
   whole fixture-plus-case packet; three levels maximum. Measure actual CPU,
   wall, peak memory and thread behavior. No cap increase, repeated invalid
   mesh, silent fallback, or automatic retry. If resource bounds prevent three
   defensible meshes, report the case unresolved and replan.
3. For each of three refinements, archive exact resolved-copy, STEP, interface,
   solver, material, boundary and mesh hashes; named load, units, coordinate
   system, output associations and failure state. Calculate applied and support
   reaction six-component wrenches about the **same** reference. As a proposed
   bookkeeping tolerance use max absolute force residual ≤1e-8 N and moment
   residual ≤1e-8 N·m, plus independently reported relative residuals; insufficient
   printed precision means unavailable, never zero. Sum signed interface
   tractions on each side of the tab, foot and pad once; verify their action/
   reaction and the assembled resultant, with no double counting at shared nodes.
4. Report the common root's displacement and rotation, equivalent tip-motion
   contribution, tab/foot/pad forces and full wrench, and regional directional
   normal/shear/peel fields with actual material ownership. Refine fixed physical
   regions and interfaces, not just nodes selected by peak value. The final two
   levels must change displacement <5% and each required regional stress
   component <10%, per WO-03; report all three levels and all components. If an
   edge singularity prevents a converged peak, retain that failure and report
   separately defined finite-region quantities without claiming the peak passed.

The conditional 1 mm service screen can be **failed** if the modeled root and
foundation contribution plus the existing panel estimate exceeds 1 mm under
these explicit assumptions. A value below 1 mm is only a conditional numerical
result, not an installed stiffness pass: the fixed joint, rigid root, material
uncertainty and actual load envelope remain unqualified. Apply DF3 once to
service stresses only for comparison with explicitly identified material
screens; absent hot normal/peel allowables remain null, so strength acceptance
cannot be inferred from the shear estimate. A single planar case is not dynamic
flutter, full-axis load, tolerance, recovery, coupled thermal or complete-package
qualification.

## Motion and integration remain separate

The archived hoop study reported no changed-pair intersections above its
threshold at 25 sampled poses with the original flat outward horns and fixed
shafts; it did not qualify continuous motion or tolerance, joint, wiring and
loaded behavior. Earlier outward-arm/cap and flat inboard-arm interferences are
separate findings. Historical aft-canted 115° pose/clearance/rate outputs used
an inferred shaft and need revalidation after the fixed-shaft correction; do not
import their reported counts or rate as current. New refreeze property matching
has not re-executed motion and cannot resolve these issues. Root load-path
results must later be reconciled with an actual compatible fixed-shaft geometry,
thermal/recovery package and full growth budget before installed acceptance.
