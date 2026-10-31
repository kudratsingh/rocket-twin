# WO-03 independent thermal error isolation

The production stable Robin factor passes the independent affine mixed-boundary
answer at the actual 935:1 aspect ratio. The manufactured curved-boundary cases
show a different result: energy and local algebra close, errors decrease with
refinement and the existing 5% convergence check passes, **while a 0.26–0.29 K
undershoot of the true effective boundary minimum remains at the finest level**.
This packet does not qualify actual-baffle local accuracy or temperatures.

The executed record is `build/wo03-thermal-error-isolation-v1/record.json`.
All nine level results and their mesh, quadrature, wall-input, field and exact
reference arrays are archived beneath `A`, `B` and `B_strong`; no failed local
extremum check is clipped or removed. Execution took 2.303 s wall and 1.992 CPU s
including child imports. Each case child had a 120 s watchdog, with all three
children bounded below the 600 CPU s allowance. No corrective trial was needed.
The factor, tetrahedral assembler and original verification YAML were hash-pinned
and unchanged. There was no Gmsh call or actual geometry/mesh/factor/ray/ODE run.

Each box measures x=0.0002 m, y=0.001 m, z=0.187 m, with k=0.04 W/(m K).
Every Cartesian cell is partitioned into the same six Freudenthal tetrahedra.
Divisions 2/4/8 in **all three axes** give 27/125/729 nodes and 48/384/3072
tetrahedra; the element aspect ratio remains 935:1. There is no unrefined
transverse-direction claim. Every exterior triangle has its own group, preserving
the variable wall integrals without assigning material/temperature ownership to
shared edge nodes.

## Affine mixed-boundary answer

Case A prescribes 573.15 K on x=0, places a 308.15 K bulk behind a finite
h=36030.6 W/(m² K) Robin wall on x=Lx, and insulates the other four sides.
The independent continuum answer is

`q'' = (573.15-308.15)/(Lx/k + 1/h)` and `T(x)=573.15-q''x/k`.

It gives 52707.4296313 W/m², total heat 9.85628934105 W and cold surface
309.612851843 K. The expected reservoir heats are +9.85628934105 W into the cold
bulk and the opposite signed heat into the hot prescribed reservoir. Every
computed node was compared with this independent linear function.

| Divisions each axis | Maximum nodal error K | Maximum reservoir-heat error W | Absolute energy residual W |
| --- | ---: | ---: | ---: |
| 2 | 2.274e-13 | 3.197e-14 | 2.132e-14 |
| 4 | 7.390e-13 | 2.309e-13 | 2.309e-13 |
| 8 | 1.648e-12 | 1.368e-13 | 1.936e-13 |

All levels pass the unchanged source tolerances: 1e-7 K temperature, 1e-10 W plus
1e-6 relative reservoir heat, 1e-10 W total balance, and 1e-9 W K form balance.
The largest form-balance residual is 1.501e-11 W K. The raw-C medium/fine change
is 1.660e-14 relative. The exact solution is already represented by P1, so the
roundoff-sized nodal errors need not decrease monotonically; the archived generic
decrease flag is false for A and does not invalidate its exact checks.

## Manufactured spatial Robin input

Case B uses the independently specified harmonic solution

`u(x,z)=308.15+100*(z²-x²)/Lz²`,
`grad(u)=(-200*x/Lz²,0,200*z/Lz²)`, `Laplacian(u)=0`.

All six sides have h=30 W/(m² K) and the effective bulk is
`Tb=u+(k/h)*grad(u).n`, so outward conductive heat equals `h*(u-Tb)`.
The optional B_strong case changes only h to 36030.6 W/(m² K). The continuum
net boundary heat is zero. Its individual reference reservoir heats and energy
forms are independently integrated from u, rather than derived from the FE
field or reduced operator.

Only two bulk IDs are used: cold=300 K and hot=420 K, with spatial fraction
`f=(Tb-300)/120`. A positive Gauss-Legendre/Duffy 4x4 rule has normalized weights
summing to one and constructs

- `M=h*A*sum(w*N*N.T)`;
- `Bcold=h*A*sum(w*N*(1-f))`, `Bhot=h*A*sum(w*N*f)`;
- each D is the sum of its B vector.

The fraction stays in [0,1] without clipping, both in quadrature samples and at
independently calculated true effective-boundary extrema. The smallest normalized
quadrature weight is 0.00420073. Maximum M/B partition discrepancy is 1.214e-16
W/K. This quadrature integrates the polynomial wall inputs and independent heat
references to roundoff; there is no centroid substitution. The two artificial
300/420 K channels reproduce the effective boundary forcing, but their wider
temperature span must not hide a local violation of the narrower true envelope.

The true effective boundary ranges, obtained from quadratic extrema on each
rectangle including in-face stationary coordinates, are:

| Case | True effective boundary K | Exact solution K |
| --- | --- | --- |
| B, h=30 | 308.148360453–409.576024955 | 308.149885613–408.15 |
| B_strong | 308.149884343–408.151187345 | 308.149885613–408.15 |

| Case | Divisions | Max nodal error K | Max facet-mean error K | Area-weighted RMS mean error K | Volume-mean error K | Below true boundary minimum K |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B | 2 | 4.296417 | 4.243994 | 0.134104 | 0.001731 | 4.294778 |
| B | 4 | 1.055862 | 1.051082 | 0.031268 | 0.000885 | 1.054222 |
| B | 8 | 0.261557 | 0.259782 | 0.007716 | 0.000235 | 0.258653 |
| B_strong | 2 | 4.616905 | 4.272664 | 0.173272 | 0.065880 | 4.616789 |
| B_strong | 4 | 1.155561 | 1.060294 | 0.032527 | 0.021458 | 1.155445 |
| B_strong | 8 | 0.287913 | 0.265133 | 0.006766 | 0.005491 | 0.287798 |

Both approximate cases show decreasing nodal, facet-mean, volume-mean, individual
reservoir-heat and energy-form errors. Max nodal errors fall approximately fourfold
per refinement. The existing 5% raw-C criterion passes: medium/fine changes are
0.008643% and 0.008601%. A separately reported nested-node field change, normalized
by the independently specified 100 K solution excursion, is 0.795569% and 0.867648%,
also below 5%. That additional field comparison uses the same numerical percentage;
it does not create a rocket accuracy tolerance.

The finest individual reservoir-heat errors are 1.547e-6 W (B) and 0.00183343 W
(B_strong), approximately 5.8 ppm of their reference channel heat. They decrease,
but remain above the exact affine-case 1 ppm relative agreement threshold. The
non-exact P1 harmonic solutions are not required to pass the 1e-7 K affine patch
tolerance; neither their remaining heat error nor their local undershoots are
reported as exact agreement. These are approximate convergence results.

## What the balances do and do not isolate

All nine levels pass production algebra/partition, global energy and form checks
under the unchanged tolerances. Across the curved cases, maximum absolute stable
energy residual is 6.821e-13 W, form residual 8.731e-11 W K and free-node residual
1.168e-13 W. Independent direct facet-heat sums agree with the stable reservoir
ledger. The exact manufactured net-heat quadrature is zero to at worst 1.741e-13
W; its independent continuum energy-form balance is within 2.183e-11 W K.
These small balances coexist with the local errors in the table.

The structured diffusion K has no positive off-diagonal above its reported
tolerance. The consistent Robin mass adds positive off-diagonals to A: for B at
the coarse level, 80 exceed tolerance; for B_strong, 128 do. Thus a monotone
discrete maximum-principle matrix is not assured even on this regular mesh. The
affine case passes with the same strong Robin/aspect, while curved forcing shows
local undershoot. This supports coarse approximation/Robin mass projection as
one sufficient mechanism; it does not attribute every actual-baffle artifact to
that mechanism.

An independent one-dimensional limiting example explains the scale: the L2
projection of z² onto linear shape functions on an interval of length dz is
`dz*z-dz²/6`, so its lower endpoint undershoots by `dz²/6`. For the prescribed
100 K quadratic profile this gives 4.16667/1.04167/0.260417 K at 2/4/8 divisions,
comparable to the observed errors. Positive wall quadrature preserves energy and
does not make a coarse linear field pointwise exact. No mass lumping, clipping,
matrix alteration or artificial boundary-temperature change was tried.

The packet therefore separates: exact affine/finite-wall verification **passed**;
calculation completion **complete**; approximate structured convergence **shown**;
local effective-envelope admissibility **failed at every curved-case level**;
actual-baffle accuracy and temperature acceptance **unavailable**. Actual sliver
quality, facet/solid ownership, varying material halfwalls, openings, nonlinear
radiation and transient error remain separate unresolved questions. The actual
baffle cannot inherit these fixture passes or the 5% indicator as acceptance.

Reproduction uses `python scripts/wo03_thermal_error_isolation.py --output NEW_DIR`
in the pinned project environment. No ignored prior build inputs are required.
The two focused tests verify the six-tet mixed-boundary analytic solve, independent
finite-difference derivatives, positive normalized quadrature, exact triangle mass
and spatial B/D partitions. Both pass; Ruff, Black and strict mypy pass for the
new source. Only the four assigned files and ignored output records were written.
