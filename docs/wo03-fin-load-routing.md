# WO-03 fin-root load routing: G12 archived contact sensitivity

**The root moment is an axial-Z moment, not the radial-X rail-bending moment
used by the old surrogate.** The archived G12 contact calculation gives the
branch resultants below; this audit transports their forces and moments to
explicit body and rail reference points. It does not determine installed rail,
ring or shell reactions, stress, stiffness, strength or flutter acceptance.

**Identity matters.** The contact record belongs to the 70 mm-span layered-fin
G12 hoop/recovery copy (`81529f6a…`, historical resolved spec `be92b389…`),
not the 69df790… G54 baffle candidate, which has 75 mm-span homogeneous plywood
fins at a different station. The G12 copy has 60 stale CAD-property validation
errors under current code. Here the archived contact result, recorded geometry
and hash-verified original fin and frame STEP files are used as historical
as-run evidence; no current valid G12 copy or shared G54 traction is claimed.
The selected force is the prior 57.629073 N per-fin historical q × CN=2
sensitivity, not a validated same-candidate operating load envelope.

The `final-metadata-corrected/record.json` under
`build/wo03-fin-load-routing-v1/` records all source hashes, full hypothesis
wrenches and coordinates. The script
`scripts/wo03_fin_load_routing.py` refuses to overwrite its output. Its one
CPU, 120 s CPU limit run took under 120 CPU s; exact timing and peak RSS are in the record; it performed a small STEP section only, no FEA and no
new CAD generation. Earlier non-final outputs are preserved. Input files are hash-recorded; the historical copy and STEP hashes are
checked against the archived audit before use. The G54 geometry read is
only an identity comparison, not a load-transfer calculation.

## What is known at the interface

At the first fin, local X is outward radial, Y tangential and Z longitudinal.
The idealized load at the body-tangent reference point is
`[Fx,Fy,Fz,Mx,My,Mz] = [0,57.629,0,0,0,2.017]` in N and N·m, for the
archived three-DOF contact model. The 2.017 N·m is 57.629 N acting at half the
70 mm span, about Z. Three physical components, `Fz`, `Mx` and `My`, were not
solved by that model: the displayed zeros embed its planar, constant-along-chord
assumption and are not measured bounds on actual tractions.

The tab faces run from z=1.065 to 1.165 m and both curved feet from z=1.055 to
1.175 m. Both have midpoint z=1.115 m. Their area, curvature, side normals,
gaps and contact stiffness were resolved in the
[installed-root audit](wo03-installed-fin-closure-audit.md); that audit's
common-root forces are integrated from its contact tractions with rigid
adherends and the stated support hypotheses. The tab loads the G11 frame
through its potted side and end faces; the curved feet load the paper/body bond.
The later splitting of those loads between individual rails, rings and shell
is not known merely from this interface equilibrium.

For the 0.1 mm foot bond and ideal rigid body/frame support, the source gives:

| Interface receiving fin load | Tangential force N | Moment about body tangent Z, N·m | Moment about body axis Z, N·m |
| --- | ---: | ---: | ---: |
| Both curved feet → paper/body | +54.386 | +1.9395 | +3.7343 |
| Three-face tab → G11 frame | +3.243 | +0.0775 | +0.1845 |
| Total | +57.629 | +2.0170 | +3.9188 |

These are service resultants; do not multiply the source force or moment by
three again except for a clearly specified DF3 strength demand. Force balance
is checked on every archived 0.1 mm support hypothesis. The axis moment changes
because `M_B = M_A + (r_A-r_B) × F` and the tangent is 33 mm from the body
axis: `2.0170 + 0.033 × 57.629 = 3.9188 N·m`. The same force/moment pair
expressed at a different origin does not create extra loading. The negative
reaction on the fin is equal and opposite. This is a one-fin sensitivity, not
an equal-three-fin or simultaneous aerodynamic case.

A frame/body stiffness change strongly alters the branch loads. In the source's
paper-free-rotation/frame-rigid limiting hypothesis the foot carries +424.434 N
and the tab −366.805 N tangentially; their large opposing forces still sum to
57.629 N. At the tangent the foot carries approximately zero Z moment and the
tab carries 2.017 N·m. This is an idealized equilibrium sensitivity, not a
credible installed reaction forecast. It illustrates why one nominal branch
fraction cannot establish capacity.

## Actual rail geometry and reference-point transport

A 0.1 mm slice of the hash-verified historical hoop-frame STEP at z=1.130 m
contains three distinct rail cross-sections, each **15.8355 mm²**, matching the
previous archived BRep result. The rail nearest the first fin has centroid
`(X,Y,Z)=(30.3203, approximately 0, 1130.05) mm`. The extra 0.05 mm in Z is
the midpoint of the finite slice, not an added support station. Other rail
centroids and each branch wrench about each centroid are in the record. The
frame STEP is the archived geometry, not a regeneration from the stale alias.

For the rigid-support hypothesis, transporting the **whole tab branch** from
the tangent to that rail centroid gives approximately
`[Fx,Fy,Fz,Mx,My,Mz] = [0,3.243,0,+0.0488,0,+0.0862]` N/N·m. The
corresponding whole curved-foot branch, transported mathematically to the same
reference, is `[0,54.386,0,+0.8185,0,+2.0852]`; it enters the paper/body,
not that rail directly. These are **known planar contributions to wrenches about a point**, not loads assigned
to that rail. In particular, the displayed +0.0488 N·m is the contribution to
`Mx` from transporting the modeled planar force; an unknown physical `Mx`
contribution must be added and cannot be treated as zero. The section lies within the loaded root, so neither value is an
internal cut resultant: actual distributed contact and unknown reactions on
both sides of the cut must first be included. Likewise, body-axis total torque
is not automatically the torsion in any one rail.

For a longitudinal rail the `Mz` component about its own section centroid is
**torsion**; `Mx` and `My` are **transverse bending moments**, and `Fx/Fy`
are transverse shear. Axial `Fz` is unknown here. St Venant torsion would require
the actual noncircular section's torsion constant, a justified shear modulus,
warping/end-restraint assumptions, and a demonstrated load split. The polar area
moment is not a substitute for that torsion constant. No such stiffness or
capacity is assigned here. The previous radial-X section-modulus screen applies
the root Z moment to a different mode without a demonstrated transformation;
it remains an unverified surrogate, not an installed-rail pass or fail.

## Required closure

The archived 0.1 mm contact model leaves 0.392563 mm of the 1 mm tip-motion
budget for the common foundation. Even with uncoupled idealized response it
requires `57.629/Ky + 2.017 × 0.07/Ktheta ≤ 0.000392563 m`: the isolated
intercepts are **146.8 kN/m** translation or **359.7 N·m/rad** rotation, each
only if the other deformation is zero. They are not a simultaneously passing
pair. The full 6×6 compliance and ring/body load distribution are unavailable.
The source also requires 2.357 MPa factored foot normal capacity in its ideal
support case; no hot peel allowable is established by the existing shear estimate.

Closure requires an actual bonded/contact model or justified bounds for the
fin/tab/foot, paper, gap pads, rails, rings and their end restraint; compatible
hot directional shear/normal properties and interface capacities; spatially
resolved reactions and refinement; and installed static and dynamic root
verification. Physical follow-up includes sectioning/wetting inspection,
hot bond and substrate coupons, assembled joint proof and measured modal/root
compliance. These are not substituted for the still-missing analytical design
closure. No active configuration, mass, CAD, thermal case or release gate changed.

The known-case wrench translation `[0,4,0] N` through arm `[2,0,2] m`
independently gives `[-8,0,+8] N·m` and reverses exactly; the focused test also
checks the 33 mm transport and round trip. Ruff and the focused test pass. This
checks force/moment bookkeeping, not material behavior or installed structural
qualification.
