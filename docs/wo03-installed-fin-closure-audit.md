# WO-03 installed fin/root closure audit

The existing layered fin remains a development candidate. This audit closes a
bounded calculation item: the potted tab and both curved gusset feet now share
one root displacement and balance the same applied force and moment. It does
not close installed stiffness, strength or flutter. The most urgent missing
evidence is the actual frame/ring/paper/body compliance and the hot normal/peel
capacity of its interfaces. A larger isolated-panel flutter ratio cannot fill
those gaps.

Run `.venv/bin/python scripts/wo03_installed_fin_closure_audit.py --output
build/wo03-installed-fin-closure-audit-v1/<new-directory>`. The script refuses to
overwrite a directory and enforces a 120 s child cap with one CPU worker and no
solver installation. It reads historical evidence and actual STEP hashes; it
creates no geometry, material change, active adoption or FEA. The completed
record is
[`completed-audit/record.json`](../build/wo03-installed-fin-closure-audit-v1/completed-audit/record.json),
with the quantitative
[`connection-table.csv`](../build/wo03-installed-fin-closure-audit-v1/completed-audit/connection-table.csv).
An earlier attempt correctly stopped when loading stale historical CAD caches;
its original log and completion record remain in the output root. The final
audit reuses the original recorded guide screens and does not bypass the cache
guard. The intermediate `attempt-02-recorded-guide-only` calculation is also
retained; the final run adds the current CAD/schema code hashes to its input
ledger.

## Exact evidence and configuration scope

The developed assembly is the existing reconciled 81.947891 g layered fin set
inside the existing hoop/recovery copy, not a newly proposed fin. Its source is
`build/wo03-recovery-clearance/hoop/resolved-candidate.yaml`, copy SHA-256
`81529f6a6f01516de59b99cb3acc85b353c5d01275ecbb23be967a71151db890`, with historical
resolved-spec SHA-256
`be92b38991ca506f9645b112d04e6631ccbc02cb6c2eec011fa661b833c6fa60`.

The actual layered material STEP is
`build/wo03-trainer-fin-root/pvc5-forward25-backed-reconciled/fin-layers.step`,
SHA-256 `74a4a92bc27034ca1d1a2bda893e3ce4fe7e37a70fc1e74c0ba92ca689534285`.
The actual hoop frame STEP is
`build/wo03-recovery-clearance/hoop/recovery-cap-frame.step`, SHA-256
`d012f27912f1c1c28c4d63bf9ef03c78c31c6abab61029d04e5e66c511221b54`.
These files still match their original records. The previous installed-root
record documents zero symmetric-difference volume between the imported layered
STEP and its density-weighted explicit material recipe. No native homogeneous
fin or new CAD cache substitutes for those materials here.

Current validation of this historical hoop YAML reports **60 stale-CAD-property
errors** following CAD code changes. Its old caches are historical. No new
candidate copy is claimed valid under current CAD code. A future geometry rerun
must recompute all relevant caches from the actual material/frame shapes.
This audit only reuses recorded physical dimensions and verified STEP file
identities for the stated contact reduction.

The active `configs/vehicle/platform/tvc-finned.yaml` loads under the current
schema at resolved identity
`869179bb8627a2605cdf6049579c9af0c2bbb6cb43694c57bdb2471febd80b89`.
It still has a 6.35 mm base panel at station 1.080 m. Its historical installed
report has identity
`9abb673ce19bed6cc6f892ea4035aadb29113f176ca6d8495b92bc641529b5f2`;
that report is neither the current active identity nor the layered candidate.
The active root ends at 1.200 m, while its shell/frame end at 1.175/1.180 m:
25 mm of foot and 10 mm of tab lack axial backing. The developed copy's
1.055–1.175 m root and 1.065–1.165 m tab correct axial coverage only.
Existing reports do not establish installed strength or dynamic acceptance for
either assembly. See [the original trainer study](wo03-trainer-fin-package.md)
and [the rejected capture study](wo03-installed-root.md).

## Existing load path and calculation

The physical path is carbon skins/solid wood root insert → potted tab in the
G11 channel **in parallel with** gusset face bonds/curved feet → kraft body,
explicit frame/shell gap pads, G11 rails/rings and remaining body. The modeled
tab retains both side faces and its inner end face; it is not a shear-only
connection. The end gap is 0.2 mm, side gaps 1.15 mm, and the sides stop at the
actual cylindrical channel clip. Each curved foot has 355.097 mm² area, versus
2,400 mm² per gusset-to-fin side face. These finite footprints replace the
historical triangular-area proxy.

The unchanged transferred load is **57.629073 N per fin**, from the retained
historical maximum q × CN=2 sensitivity. The 70 mm span gives **2.017018 N·m**
root moment. CAD axes at the first fin are radial X, tangential Y and axial Z;
the resultants are `[F_X,F_Y,M_Z]=[0,57.629073,2.017018]`. In particular,
`r_X × F_Y` produces **M_Z**, not radial-X rail bending. The older attachment
screen applies the span-root moment to a longitudinal rail's radial-X bending
section modulus without an explicit frame/ring transformation. Its result is
a historical load-routing surrogate, not a demonstrated installed rail stress.
This audit does not change that frozen code. An actual connected model must
route both the distributed tangential load and axial moment through the full
frame/rings/body, using the appropriate torsion, bending and contact modes.
The per-fin local axes rotate with each fin. This single-root calculation does
not prove equal support sharing among all three fins or a simultaneous
multi-fin/frame load case.

At each adhesive patch, the existing finite-contact model uses
`K = integral(B.T D B dA)`, with
`B=[[1,0,-y],[0,1,x]]` at the body-tangent reference and
`D=(E*n*n.T + G*t*t.T)/bond_thickness`.
The common root DOFs are `[u_X,u_Y,theta_Z]`; the two branch stiffness matrices
are added before solving, rather than proportioning a result from separate
clamps. Hot adhesive E remains the existing **1 GPa estimate**, Poisson ratio
0.3. The wood insert and gussets are rigid in this reduction, as are support
translations. The actual flexible insert/gussets, frame, rings, paper, pads and
body are not silently credited as rigid installed structure.

The panel calculation retains 0.12 mm minimum skins, the assumed 4.7 mm minimum
core, 50% hot properties, DF3 for strength only, the 1 mm service deflection
screen and the unchanged 45°C substrate screen. It reproduces **0.606381 mm**
panel motion and leaves **0.393619 mm** for everything behind the panel.

## Quantified installed-path requirements

With ideal rigid paper/body and frame backing, the common-root results are:

| Curved-foot bond thickness | Foot share of root moment | Tab share | Foot normal / shear required, hot DF3 | Tab normal / shear required, hot DF3 | Added root motion at tip |
|---|---:|---:|---:|---:|---:|
| 0.1 mm | 96.157% | 3.843% | 2.357 / 0.512 MPa | 0.546 / 0.0365 MPa | 1.056 µm |
| 0.3 mm | 89.193% | 10.807% | 2.186 / 0.471 MPa | 1.518 / 0.102 MPa | 2.937 µm |

These are smooth finite-foundation traction demands, not resolved adhesive-edge
peaks. Hot normal/peel allowables for paper/adhesive, wood/potting and G11/potting
are unavailable. The 1 MPa hot shear estimate supplies no normal/peel pass.
Changing the foot thickness alters load sharing even though it does not alter
the isolated-foot traction under a fixed entire load. That is why the two
parallel interfaces must be solved together.

For an optimistic common foundation with uncoupled translation and rotation,
the remaining support must satisfy

`57.629073/K_Y + 2.017018*0.07/K_theta <= remaining support tip-motion budget`.

The two foot-thickness cases leave **0.392563 / 0.390683 mm**. Their intercepts
are **K_theta ≥359.665 / 361.396 N·m/rad if translation is zero**, or
**K_Y ≥146.802 / 147.509 kN/m if rotation is zero**. Neither pair of intercepts
can be used simultaneously as a passing pair: each alone consumes the full
budget. Finite wood/gusset compliance, support coupling or translation further
consumes that budget. All stiffnesses refer to the defined body-tangent
coordinates; a support rotation about the body center cannot be substituted
without translating the full force/displacement compliance matrix.

Separate rotational foundations expose sensitivity while keeping the same
geometry/properties. For 0.1 mm foot bonds, assigning both paper/body and frame
supports 35.870 N·m/rad (one tenth of the prior required total root K) gives
**2.578 mm** total panel/root motion and fails the 1 mm screen. Assigning each
358.700 N·m/rad gives **0.807 mm**, conditional on ideal zero translation and
rigid solid adherends. This is a hypothesis, not an installed pass. If the
paper/body can rotate freely while the frame is ideally rigid, the tab carries
all 2.017 N·m and its required hot normal/shear capacities rise to
**7.332 / 1.922 MPa**; the foot still transmits direct shear. The latter shear
demand exceeds the existing 1 MPa shear estimate (margin **−0.480**), even under
the ideal remaining restraints. A thick-foot version gives 8.962 / 1.432 MPa.
Thus a single nominal rigid-backing split cannot be treated as a bound on joint
strength. No actual support value is inferred from these endpoints.

The previous **8.459380 g open-cheek capture** remains rejected. Its optimistic
independent stiffness is only **40 N·m/rad** against required 358.700:
stiffness margin **−0.8885**. Its existing generic hot wood screening demand is
16.808 MPa against 5 MPa, margin **−0.7025**; that generic screen is not a
measured bearing allowable. Existing machining/interference findings remain.
The ideal cheek branch cannot supply more than 11.151% of the moment when the
whole root is just stiff enough. No new geometry or scaled cheek family is
introduced.

## Flutter relevance and retained failures

At the 1 mm static limit, the fixed-load-shape stiffness ratio to the isolated
panel is 0.606381. Its square root, **0.778705**, illustrates how a spring/mass
frequency could fall with root compliance under fixed mass and identical load
shape. It is not an installed eigenfrequency, a dynamic mode or a flutter speed.
The bending/rotation coordinates above also do not establish panel twisting
about its radial span. The existing layered torsion study still needs installed
root torsion **2.53–2.83 N·m/rad** in series to meet its **2.114 N·m/rad** static
divergence target. Its assumed intact caps, skin/cap shear and load eccentricity
remain unverified. Static divergence does not clear dynamic flutter.

The old active-panel NACA sensitivity remains historical and preliminary; it
cannot transfer its large homogeneous-panel speed ratios to this sandwich or
to an unmeasured root. The
[flutter source note](wo03-flutter-source-notes.md) documents its low-aspect-ratio,
joint, body-pitch and other mode limitations. Installed mode shapes, hot torsion,
root/airframe receptance, damping, excitation and body/fin/TVC coupling remain
required. The historical FEA regional stress failures remain **10.411% Syy /
26.797% shear** for 3.5→2.5 mm and **22.909% / 14.406%** for 2.5→2.0 mm, against
the unchanged strict 10% criterion. Contact quadrature convergence supplies no
replacement for those missing installed regional fields.

## G12 complete budget and stop decision

This audit adds **zero design mass**. It takes no new foil saving or unaccepted
rail saving. It reuses the conservative historical complete hoop/recovery mass
**781.641872 g**; the previously reconciled actual-shape value **781.572198 g**
is recorded but the 0.069674 g difference is not credited. The fin set is charged
once at 81.947891 g, and the separate 4.373453 g residual `fin_bonds` allowance
stays in the source. All original growth remains **50 g**, guide **5 m**,
minimum departure **10 m/s**, with the original lower thrust and two timestep
screens. The guide itself is still an unconfirmed equipment assumption.

| Historical complete-package hypothesis | Remaining guide mass headroom | Lower two-timestep exit speed | Result |
|---|---:|---:|---|
| Existing hoop/recovery copy, before new thermal/root mass | +7.239 g | 10.142195 m/s | Guide screen only passes |
| Same copy +8 g thermal hypothesis | −0.761 g | 9.985130 m/s | Fails |
| Same copy +rejected 8.459 g cheek capture | −1.220 g | 9.976158 m/s | Fails |
| Same copy +cheek +8 g thermal hypothesis | −9.220 g | 9.820699 m/s | Fails |

The 8 g item is a budget hypothesis, not an accepted G12 thermal/retention
package. The distinct G54 fitting baffle and eight-layer assembly supplies no
G12 mass credit. A complete compatible G12 solution and the installed joint
work still have to fit this budget. Shifting, omitting or reducing the 50 g
growth allowance is not part of this audit.

Two independent small fixtures pass: the full finite planar adhesive matrix
matches its analytic result to **1.91e−16 relative**, and two rotational branches
with series foundation springs reproduce the independent parallel/series formula
to **2.22e−16**. The actual contact calculations at 16/32/64 points converge by
less than **2e−16** in the final root-motion comparison; all branch forces and
moments balance within the recorded 1e−8 mixed-unit threshold. These establish
the bounded calculation's algebra and integration. They do not establish
material allowables or an installed continuum model. Ruff and Black pass for
the new script. No new expensive FEA is justified while these particular
load-routing and interface-property blockers remain unresolved.
