# WO-03 wall treatment trial 1: vertex quadrature

**Rejected as a standalone correction by the primary.** This one fixture-only
trial removes the structured boxes' global effective-boundary undershoot, but
changes the manufactured spatial source integration and substantially worsens
continuum heat and mean accuracy. No second execution or actual-mesh treatment
was made. This is corrective trial 1 of the maximum two authorized trials.

Evidence: `build/wo03-robin-lumped-trial-v1/record.json`, with all nine level
records and raw input/matrix/field arrays beneath `A`, `B`, `B_strong`. Execution
was 2.524 s wall / 2.210 CPU s on one CPU, with a 120 s child cap per case and
600 CPU s total allowance. All frozen source/config hashes remain unchanged.
Ruff, Black, strict mypy and the independent vertex partition/energy fixture pass.

The meshes, k=0.04 W/(m K), box dimensions 0.0002×0.001×0.187 m, prescribed/Robin
cases, analytic solutions, tolerances and 2/4/8 divisions in every axis are those
of [the frozen isolation study](wo03-thermal-error-isolation.md). Source mesh
arrays are bitwise identical to the prior arrays. The volume K is bitwise equal
to replay of the unchanged assembler on those same arrays. Raw K/A/B/D and wall
terms were checksum-verified unchanged after construction/solution; no saved
actual matrix was loaded, clipped, altered or repaired.

The separately declared discretization is triangle vertex quadrature:
`M=hA/3 I`, `Bcold=hA/3*(1-f_vertex)`, `Bhot=hA/3*f_vertex`, with each
`D=sum(B)`. Here f is the original analytic effective-bulk fraction evaluated
directly at the three vertices with the triangle's outward normal. Fractions
stay in [0,1] without clipping. Partition and positive wall energy are retained.
This quadrature integrates affine functions exactly; the quadratic boundary
source is changed. This distinction is the decisive outcome of the trial.

Case A still passes the unchanged exact linear/series-heat checks: maximum nodal
error 1.592e-12 K and reservoir-heat error 3.357e-13 W over all three levels.
There are no global effective-boundary violations in any case/level. The following
curved-case results are not accepted merely because the node values improve.

| Case | Divisions | Max nodal error K | Max boundary-quadrature point error K | Volume-mean error K | Continuum net/source defect W |
| --- | ---: | ---: | ---: | ---: | ---: |
| B, h=30 | 2 | 1.392e-4 | 6.184760 | 4.166661 | 0.05609999 |
| B | 4 | 7.119e-5 | 1.546211 | 1.041665 | 0.01402500 |
| B | 8 | 3.433e-5 | 0.386562 | 0.260416 | 0.00350625 |
| B_strong, h=36030.6 | 2 | 5.113e-7 | 6.184687 | 4.166662 | 67.377209 |
| B_strong | 4 | 2.616e-7 | 1.546172 | 1.041665 | 16.844302 |
| B_strong | 8 | 1.306e-7 | 0.386543 | 0.260416 | 4.211076 |

The continuum net heat in this table is independently integrated with the frozen
accurate Gauss/Duffy rule on the **numerical P1 field and original analytic
effective bulk**; its exact reference is zero. It matches the nodal source
integration defect to at most 1.238e-13 W (B) or 5.116e-13 W (B_strong). The
strong case therefore fails the unchanged 1e-10 W physical zero-net-heat check by
4.211 W even at the finest level. Error decreases roughly fourfold, but no
threshold is relaxed and no continuum/source agreement is claimed.

| Finest result | Original consistent | Vertex trial 1 |
| --- | ---: | ---: |
| B nodal error K | 0.261557 | 0.00003433 |
| B volume-mean error K | 0.000235 | 0.260416 |
| B reservoir-heat error W | 0.000001547 | 0.00280461 |
| B_strong nodal error K | 0.287913 | 0.0000001306 |
| B_strong volume-mean error K | 0.005491 | 0.260416 |
| B_strong reservoir-heat error W | 0.00183343 | 3.368418 |

All changed-discretization energy ledgers close: maximum discrete energy residual
5.684e-13 W, form residual 4.366e-11 W K and free-node residual 3.266e-13 W.
That is conservation of the vertex-quadrature problem, not conservation under
the original accurately integrated spatial source. The existing medium/fine C
criterion passes at about 3.1573% for both curved cases, but that indicator does
not establish the required local/source/heat accuracy. All false physical heat
and exact-reference checks remain in the archive.

The fixture K has no positive off-diagonal above its reported tolerance; the
lumped A likewise has none. This explains why the diagonal wall can improve
fixture bounds. The actual old gas K already has positive off-diagonals and an
interior overshoot with **no wall term** at that node
([existing diagnosis](wo03-gas-field-diagnostic.md)); this trial cannot correct
or uniquely explain that separate failure. No actual operator qualification or
temperature acceptance follows from the fixture result.

Real material chord maps have varying/possibly discontinuous h and parallel bulk
paths. Their interface endpoints and jumps are not the smooth analytic f used
here. Side-local values, facet subdivisions and common power-conjugate surface
registration would have to be defined; no global edge-node material priority or
unjustified averaging is authorized. That interface/jump treatment remains open.
The primary selected a separately sourced final trial preserving the original
accurate B/D while changing only M; it does not change this rejected record.
