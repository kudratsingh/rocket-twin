# Elmer known-answer comparison: completed fields, qualification open

2026-10-31 Pacific / 2026-11-01 UTC. **Elmer completed the nine logical field
results, but it has not qualified for the actual baffle.** The affine A field
misses the unchanged 1e-7 K nodal criterion at all three levels. B and B_strong
have no nodal effective-wall-envelope violations and pass a conditional
continuous P2 envelope bound, but raw-C, Robin reservoir heat, local/algebraic
balance and form balance remain unavailable. The recorded finite errors are not
monotone under refinement. No unavailable quantity is treated as zero or a pass.

## Identity, case and method

The completed record is
`build/wo03-elmer-thermal-comparison-io-replan/record.json`, SHA-256
`752366ff32bb495d2e0bf00598dc444fb515d97727dbdf2acfd682a5b04ea8be`.
It records unchanged input/tool hashes, the SIF and mesh identities, Float64
VTU fields, native output files, all nine results and resource accounting. The
executed revised harness is `scripts/wo03_elmer_thermal_comparison.py`,
SHA-256 `00a24c69fdfdfaa3401aebacd383265561ecf21284f13cbe1b386566f4188cfd`;
its study configuration SHA-256 is `49fa95a885b2490f08f4a02e8629146cac77178dad83432caff7aac9c4bf844e`.
The isolated Elmer executable reports `26.2-unknown` from the pinned 26.2.1
source archive; its recorded SHA-256 is `006922a630d1daa404ff1191a39dc33a44aa4b6d0c5bac907f07861db4232d6e`.
VTK 9.6.2 read all nine fields as Float64 and checked their coordinates and
node counts.

The preserved source box is 0.0002 × 0.001 × 0.187 m, k=0.04 W/(m K).
The original 2/4/8 tetrahedral subdivisions were enriched with shared edge
midpoints to straight native **510 quadratic tetrahedra** and **306 quadratic
boundary triangles**, retaining the geometry and source corner connectivity.
They have 125/729/4,913 nodes and 48/384/3,072 tetrahedra, respectively.
Native element node order, positive affine geometry and boundary ownership were
checked. The source's six-point triangular and 27-point tetrahedral rules
passed independent analytic moment checks for the polynomial degrees needed
here. This is a P2 comparison; it is not the same discrete method as the
prior P1 fixture.

A prescribes 573.15 K at x=0 and uses a 308.15 K bulk with h=36030.6 W/(m² K)
at x=Lx; its other sides are insulated. B and B_strong use h=30 and 36030.6
W/(m² K) on all six faces. Their continuous wall input is
`Tb=u+(k/h)∇u·n`, with `u=308.15+100(z²−x²)/0.187²`. The 300/420 K values
in the older study are reservoir-decomposition constants, not direct wall
temperatures. The Elmer SIF uses HeatSolveVec and MATC at integration points,
with Direct/UMFPACK and no input-constant approximation. No material, boundary,
solver or tolerance setting changed during the output-location replan.

A prior **unrun P1 preflight** independently found that Elmer's default
three-point 303 triangle rule does not exactly integrate the cubic `N_i Tb`
term. Its maximum assembled nodal input errors for B_strong at 2/4/8 were
0.0233949 / 0.00146218 / 9.13862e-5 W; these are input-quadrature differences,
not measured field or heat errors. The selected native P2 306 six-point rule
has the degree-four precision needed for the quadratic boundary expression;
no private element-definition or solver-source edit was used.

## Field results

| Case | Maximum absolute nodal error at 2 / 4 / 8 divisions, K | Existing 1e-7 K absolute-field comparison | Effective-wall envelope |
| --- | --- | --- | --- |
| A | 1.93358e-5 / 1.12223e-4 / 3.73599e-5 | All three fail | Continuous bound straddles; unavailable |
| B | 1.76266e-9 / 1.90469e-8 / 1.13586e-7 | 2 and 4 pass; 8 fails this additional strict diagnostic | No nodal violations; continuous bound certifies all three fixture levels |
| B_strong | 5.99925e-10 / 7.27027e-10 / 1.55393e-9 | All three pass this additional strict diagnostic | No nodal violations; continuous bound certifies all three fixture levels |

The error values do **not** decrease monotonically: A rises then falls; B and
B_strong increase across the three levels. Literal nonmonotonicity is reported,
not converted into a separate failure solely by assuming a roundoff floor.
For B and B_strong the 1e-7 K check is an additional strict field diagnostic;
the original P1 approximate-case comparison did not impose that affine-patch
threshold. P2 can represent the manufactured quadratic field, but that is not a
substitute for the original **<5% raw-C** convergence requirement. Raw-C is
unavailable, so neither approximate case has an aggregate pass. The reported
additional medium/fine nested-field changes are 9.738e-10 and 1.711e-11 of the
100 K excursion, respectively; they do not replace raw-C convergence.

The continuous fixture certificate is a bound, not a hotspot sample. For
straight affine P2 tetrahedra and these exactly representable analytic fields,
the maximum continuous error is at most twice the maximum nodal error: the
sum of absolute quadratic shape functions is at most 2. B and B_strong's
resulting full temperature intervals lie inside their independently calculated
effective-wall envelopes. For A the interval straddles the hot endpoint, so no
continuous envelope conclusion is made. This bound does not transfer to curved
meshes, nonlinear fields or the actual baffle. Tiny A nodal excursions at the
prescribed hot wall occur at floating-point scale; the continuous A result is
still reported as unavailable, not a separate invented physical violation.

## Native conductive flux, not full energy closure

Elmer's per-boundary `SaveScalars` diffusive-flux outputs were read using their
native column names; the solver's `n·k∇T` sign was reversed for outward Fourier
conductive heat. Maximum absolute per-boundary errors against the independent
conductive-flux reference and the signed sums are:

| Case | Max boundary heat error at 2 / 4 / 8, W | Signed sum of outward conductive heats at 2 / 4 / 8, W |
| --- | --- | --- |
| A | 1.011e-6 / 2.847e-6 / 2.957e-6 | −2.032e-6 / −3.387e-6 / −4.226e-6 |
| B | 3.643e-12 / 5.056e-12 / 1.137e-11 | −6.747e-12 / 1.650e-11 / 3.103e-11 |
| B_strong | 1.735e-11 / 1.399e-11 / 1.024e-11 | −2.124e-11 / 2.506e-11 / 2.953e-11 |

For A the individual native-conduction comparison is within the existing
`1e-10 W + 1e-6 relative` heat tolerance on all levels; its signed conduction
sums exceed 1e-10 W. The B sums are below 1e-10 W. In every case the sum is a
**gradient-derived conduction indicator**, not the Robin film exchange, discrete
algebraic global balance, local conservation or energy-form balance. Those
quantities and the two-reservoir raw-C matrix remain unavailable. The solver's
`Temperature Loads`/boundary residuals are not relabeled as physical film
heat. These limits prevent a complete fixture pass even where the individual
field and conductive-flux checks are good.

## CalculiX and Elmer side by side

| Evidence | CalculiX 2.23 | Elmer 26.2 source build |
| --- | --- | --- |
| Straight finite-wall A | Three P1 levels completed; seven-digit printed temperatures cannot verify 1e-7 K. Separate binary probe found float32 output. | Three P2 levels completed with Float64 fields; all exceed 1e-7 K. Individual conduction heat agrees within A heat tolerance, but conduction sums exceed 1e-10 W. |
| Spatial Robin B/B_strong | Exact continuously varying sink unavailable without a suitable linked `film.f`; no solve. | Both run at three P2 levels, nodal and conditional continuous envelopes pass; B fine fails the additional strict field diagnostic, errors do not decrease monotonically, raw-C and physical balances unavailable. |
| Physically curved annulus | Three P1 levels; finest individual 0.5 K/3% heat and 5% successive-conductance checks meet their existing thresholds. Printed precision does not close balance or local verification. | Not executed. |
| Actual baffle / transient / radiation | Not qualified or accepted. | Not executed or qualified. |

The tools used different element order and only partially overlapping fixtures;
this is an evidence comparison, not a direct accuracy ranking. See
[CalculiX evidence](wo03-ccx-thermal-comparison.md) and
[Elmer tagged I/O](wo03-elmer-tagged-io.md).

## Execution history and bounds

The first packet's A/2 solve returned code zero, but its harness looked only in
the case root while Elmer wrote `mesh/field_t0001.vtu`; it stopped before
reading the field. The original record, inputs, log and output were preserved.
The primary authorized one **I/O-only** replan: accept exactly one VTU in the
case or mesh directory, verify the original input/output and tool hashes and
unchanged physical-function ASTs, reuse A/2 without invoking the solver, then
run the eight previously unexecuted levels. The original 0.369443 CPU seconds
and 0.721448 seconds of A case wall time were charged to the same original
budget. The A/2 field failure above was retained, not rerun or repaired.

The complete charged packet used **4.1685 CPU s**, including tracked old and
new parent/child time. Parent peak RSS was **201,113,600 bytes**; the cumulative
child peak was **47,955,968 bytes**. These are separate maxima, not a measured
simultaneous-memory sum. One CPU worker/thread was requested; VTK reported one
SMP thread and a global maximum of one, but no OS CPU-affinity claim is made.
There was no automatic numerical retry, tolerance relaxation, actual-geometry
solve, physically curved Elmer fixture, transient or radiation run.

Before either tool can support an actual-baffle attempt, an explicit decision
must resolve the observed A field error and balance limitations; verify native
Robin heat, local conservation and raw-C or provide a justified equivalent
bounded method; and cover physically curved geometry and the required transient,
radiative and actual material/contact paths. Those are numerical-method and
model evidence gaps, distinct from uncertain material properties and later
physical tests. No vehicle design or flight-release gate changed.

## Published compact evidence

[Campaign record](../runs/wo03-elmer-campaign-20261101T054800Z/record.json) is an explicitly labeled compact projection of the hashed raw record. It preserves all nine extrema/error/heat results and unavailable states; generated nodal arrays are omitted. The same packet retains the original stopped record, read-only A-2 recovery, original and completed harnesses, and corrected source-quadrature audit.
