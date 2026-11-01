# G80 installed fin/root intake

**Finding:** the saved 52-part G80 package contains a custom plywood fin and
root construction, but the historical G80 panel and installed-root screens are
not an installed strength, stiffness, deflection or flutter qualification for
that exact candidate. They used a different resolved identity and fin shape
hash; the panel model was ideally clamped, and the root model did not solve the
connected fin, shell, frame and bond system. The current 6.35 mm plywood design
is retained. No layered G12 fin result is used here.

## Current G80 fin and nominal connection geometry

The active G80 source is `configs/vehicle/platform/performance.yaml`. Its saved
52-part candidate is identity
`62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009` in the
[integrated candidate manifest](../build/wo03-g80-integrated-candidate-v1/manifest.json).
The package-intake record lists the current active source's separate 42-part
resolved identity as `c18abfee2444307e46eaaca55197693a3d9353bd8d8d8ac42162ffd238ef1d5e`;
the 52-part copy is a proposal and is not the active configuration.
The exact saved `fin_set` STEP solid hash is
`6a890994308187c5dd42507e5e649ac81f98eb1a8670a2b1ee10c9cf912ecbee`. That
part's CAD mass is 131.624 g at the source plywood density of 715 kg/m³; the
separate 8 g `fin_bonds` part is still an estimate, not measured adhesive.

The current CAD generator is `fins` in [`src/cad/parts.py`](../src/cad/parts.py).
For this source it constructs three unswept rectangular fins at the aft shell:

| Feature | Current nominal specification |
|---|---|
| Fin set | 3 fins; 70 mm radial span; 120 mm root and tip chord; 0° sweep; 6.35 mm thickness; fin part station 1.080 m |
| Tab | 6.0 mm radial depth, fin thickness (6.35 mm) tangential width, 100 mm axial length, CAD offset 10 mm |
| Root gussets | Two triangular plywood gussets per fin, 12 mm radial span, 3 mm base, 1 mm inset; six gussets are fused into `fin_set` geometry |
| Aft shell slots | 7.3 mm width × 100 mm axial length; local start 168 mm; 0.5 mm nominal cardboard wall at 32.5 mm inner radius |
| Fixed plywood support | `motor_mount` length 190 mm; three 3 mm rings at local 0, 90 and 167 mm; rails 12 mm wide × 7 mm deep at radius 28.5 mm; fin channels at radius 30 mm with 6.4 mm nominal depth |

These are source CAD dimensions, not as-built tolerances or proved bond areas.
`fin_set` generation fuses tab and gusset solids into the modeled plywood
assembly; the CAD does not thereby prove the physical glue interfaces. In the
intended load path, fin panel load enters the root through the tab and gusset
bonds; the tab passes through the slotted aft shell into the fixed mount's fin
channel, while the gusset feet bear/bond at the shell. The resultant then needs
to pass through the mount rails/rings, shell and forward joint. Actual load
sharing among tab, two feet, shell and three rails/rings has not been resolved.

The 52-part integrated copy's `motor_mount` outer radius is **32.2 mm**; the
historical active source used **32.3 mm**. Its channel/ring/rail nominal
parameters are otherwise recorded in the resolved copy, but that 0.1 mm mount
change makes the old installed interface result non-transferable. The aft
shell's nominal 33.0/32.5 mm radii and 0.5 mm wall are in the saved resolved
copy. The integrated candidate therefore has a source-defined fin and support
geometry, but there is no executed installed-root report on its exact
`62e8de9e…` identity and `6a890994…` fin STEP hash.

The study's plywood directions are axis 1 span/face grain, axis 2 chordwise
in-plane transverse, axis 3 plate-normal. Its orthotropic engineering constants
are **estimates**: E1=E2=2.0 GPa, E3=0.5 GPa, G12=G13=G23=0.2 GPa, and
ν12=ν13=ν23=0.2; density is 715 kg/m³ within a cited 680–750 kg/m³ source range.
The strength screens use estimated directional bounds of 10 MPa in span and
chord and 2 MPa in in-plane shear. Hot sensitivity halves stiffness and strength.
These are not lot properties, coupon allowables or qualified bond/substrate
limits. The 6.05 mm panel thickness used for the minimum-dimension panel screen
comes from the 6.35 mm nominal source less the specified ±0.3 mm thickness
tolerance; it is a sensitivity/input assumption until an as-built part is
measured.

## Saved evidence and exact identity mismatch

| Evidence | Identity and geometry | What it supports | What it does not support |
|---|---|---|---|
| Current 52-part candidate | Resolved SHA `62e8de9e…`; current fin STEP hash `6a890994…`; regenerated candidate mount radius 32.2 mm | Nominal package geometry, mass properties and other saved package screens for this candidate | No same-identity installed fin/root solve or updated root load transfer |
| Historical G80 fin/installed study | `runs/wo03-fin-installed-20261030T205715365284Z/record.json`; resolved SHA `c5eab65c97604f6bf6605bf2dff6369c48a62e3d04c808e7ba291489d762ab09`; source fin hash `e977795fc3c2776695911857df3812ff588c6944f91f760b997db1efd5bcf587`; source config then hashed to `2e87ef47…` | Historical panel/root calculations on that source, with its recorded load and idealizations | It is not the 52-part candidate: the resolved and fin-shape hashes differ, and mount/shell interfaces are not identity-matched to the 52-part package |
| Historical minimum-thickness panel run | `build/wo03-fin-acceptance-final/modular-performance-v1/wo03-fin-acceptance-20261030T204800907793Z/report.json`; 6.05 mm minimum, explicit orthotropic S6 shell, ideal clamp | Five panel mesh levels; 0.6612 mm hot/half-stiffness max displacement on its 49.807 N case; cold displacement change 0.0062% and first three frequency change 0.0035% between its two finest levels | Does not model the finite root joint; regional Syy and shear changes are 34.48% and 22.08%, over the strict 10% criterion. Overall panel acceptance remains false |
| Historical installed attachment screen | Same historical G80 installed record above; `acceptance: open`, `acceptance_passed: false` | A 1.2535 N/fin coincident q×estimated-CN history result and a separate 308.183 N/fin max-q×CN=2 sensitivity; simplified tab/gusset/shell/rail bounds | The coincident load is from the earlier configuration/flight identity. The max-q×CN=2 combination is explicitly not known to coincide and is not an operational maximum. Single-strip shell and single-rail results are not the assembled support solution. |

The historical G80 panel's static design case was 40 kPa at 5° and 49.807 N
per fin. Its attached load is an independent panel screen. The separate
historical coincident trajectory estimate was only 1.2535 N/fin, while the
uncoincident maximum-q × CN=2 sensitivity was 308.18 N/fin. These serve
different questions; neither is a verified current 52-part attached-root load.
Use neither as an exact current candidate force without deriving it from the
52-part flight identity and resolving the applicable operating envelope.

The existing 1 mm total fin-tip displacement limit and DF3 strength factor are
retained. The formal finite-element checks also require a known-answer method
case, force equilibrium, displacement convergence below 5%, and regional stress
convergence below 10%. The historical panel met its displacement and frequency
refinement checks but missed stress convergence in two components, so its
low absolute estimated stresses do not turn it into a passing finite-element
acceptance. The source-specific mounted root is an additional unclosed part of
the same 1 mm motion budget.

## Next bounded quantitative deliverable

Prepare one identity-matched installed-root response case for the saved 52-part
candidate: use its exact `fin_set`, `fin_bonds`, `aft_shell` and `motor_mount`
shape hashes; represent the finite slot/tab/channel and gusset-foot geometry;
apply plywood material axes at the actual fin orientation; and connect the tab,
feet, shell, rails/rings and body with explicit bond/contact properties or
documented conservative bounds. Record the actual connected reactions and
translational, bending and axial-root-torque stiffness at a stated root/tip
reference. Use a force/time history derived from this same candidate identity,
plus any separately approved off-nominal case; do not combine unrelated maxima.
The result should report joint and substrate demand separately from panel
stress, total tip motion against 1 mm, and the resulting installed-root inputs
needed by the existing flutter screen. This deliverable is a model-response
assessment, not flight qualification.

Before solving, require the exact candidate solid hashes and face map; measured
or justified tab/foot bond thickness, coverage and hot/cold directional
properties including normal/peel limits; plywood lot, grain direction,
thickness and temperature-dependent directional properties; shell and frame
material/support properties; and current same-identity per-fin forces and
moments. Include finite geometric tolerances/clearances where they control
contact. If a required capacity or support is unavailable, return a demand or
stiffness requirement with that capacity explicitly unresolved; do not turn it
into a pass. Stop before meshing for hash mismatch, missing load/moment basis,
unsupported bond/contact conditions, or stale geometry. Stop the acceptance
claim on failed known-case/equilibrium, a cap or invalid solve, displacement
convergence ≥5%, regional stress convergence ≥10%, or unavailable applicable
capacity/allowable. Installed flutter remains open until root torsion/stiffness,
damping and body/fin coupling are supported by an applicable dynamic method or
measurement.

The current work therefore retains the custom plywood fin and leaves its
installed strength, total motion, and flutter open. No G12 layered-fin,
G11-frame or G12 root result is transferable to this G80 geometry.
