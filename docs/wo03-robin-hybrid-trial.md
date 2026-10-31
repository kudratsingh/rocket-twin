# WO-03 wall treatment trial 2: diagonal M with original accurate B/D

**The final authorized wall trial does not close the fixture accuracy problem.**
It preserves the original spatial source and continuum heat balance and removes
global envelope violations on these regular meshes. However, finest-level nodal
errors remain 8.194/9.020 K, facet-mean errors exceed 8 K and medium/fine field
changes exceed the unchanged 5% criterion. The two-trial wall-treatment family
is finished: no third trial, repeated execution, budget increase or tolerance
change is made. Actual-baffle accuracy/temperature acceptance remains unavailable.

The single execution is `build/wo03-robin-hybrid-trial-v1/record.json`: all nine
level cases completed in 2.534 s wall / 2.276 CPU s, one CPU, 120 s per-case child
cap and 600 CPU s total allowance. Every level's source wall/mesh arrays and raw
K/A/B/D/field arrays are retained. Frozen original and trial-1 files/records stay
unchanged. Ruff, Black and strict mypy pass for the new script.

The original 0.0002×0.001×0.187 m six-tet-per-cell boxes, k=0.04 W/(m K), all
three cases, 2/4/8 refinements in all axes, analytic answers and verification
tolerances are reused. The original consistent quadrature and its B/D are
reconstructed by the unchanged frozen fixture function; a separate bytewise
read-back audit verifies **every curved-case B/D against the archived original
arrays**, not merely against trial-1 values. No vertex/source resampling is used
for the hybrid forcing. See `archived-source-audit.json`.

The newly declared wall discretization is
`Mhybrid = diag(Moriginal @ ones)`, with original accurate B and D unchanged.
This is a fixture-only integration/stabilization choice, not an alteration of a
saved actual operator. For symmetric nonnegative M,
`diag(M*1)-M` is a graph Laplacian with quadratic form
`sum(i<j) Mij*(xi-xj)^2 >= 0`. Adding it preserves the original augmented wall
energy PSD. M/B/D constant-field partition is also retained. The unchanged
production normalizer verifies each replacement's partition, symmetry and PSD;
minimum augmented eigenvalue is -7.323e-17 W/K (roundoff), maximum partition
defect 1.110e-16 W/K. Raw constructed arrays are checksum-verified unchanged.

The effective forcing at each local surface node is
`sum_bulk(Bbulk_i*Tbulk)/Mhybrid_ii`. Its weights are nonnegative, sum to one
within roundoff and stay within the independently known true physical envelope.
The fixture volume K is bitwise equal to replay of the unchanged assembler on
the original identical mesh. Both K and hybrid A have no positive off-diagonal
above their reported tolerance. These are fixture properties, not evidence that
the actual unstructured volume operator has that sign structure.

Case A again passes all original exact-linear and series-heat checks: maximum
nodal error 1.592e-12 K and reservoir-heat error 3.357e-13 W. Roundoff-sized exact
errors need not decrease monotonically. Every case/level stays inside the true
global effective-boundary envelope. Those successes coexist with the following
curved-case errors.

| Case | Divisions | Max nodal error K | Max facet-mean error K | Boundary quadrature-point error K | Volume-mean error K | Reservoir-heat error W |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B, h=30 | 2 | 30.686546 | 30.075342 | 30.627810 | -0.000926 | 0.034718 |
| B | 4 | 16.138092 | 15.999290 | 16.110968 | 0.005424 | 0.011876 |
| B | 8 | 8.194088 | 8.161486 | 8.187691 | 0.003486 | 0.003421 |
| B_strong, h=36030.6 | 2 | 32.439974 | 29.956604 | 31.840826 | 0.130065 | 40.675425 |
| B_strong | 4 | 17.449881 | 16.048786 | 17.085127 | 0.141211 | 13.988313 |
| B_strong | 8 | 9.020249 | 8.297143 | 8.835474 | 0.080909 | 4.060264 |

Nodal and surface errors decrease but are much larger than the original
consistent method. Volume-mean error is not monotonically decreasing across all
levels; a small mean does not establish local accuracy. Source forcing change is
exactly zero for the archived B/D arrays. Independently integrated continuum net
heat is within 1.243e-13 W (B) and 7.473e-13 W (B_strong), passing the original
1e-10 W zero-net-heat tolerance. This fixes trial 1's changed-source defect, but
does not fix approximation error.

| Curved-case convergence | B | B_strong | Original criterion |
| --- | ---: | ---: | ---: |
| Medium/fine raw-C relative change | 3.1402% | 3.0706% | <5%, passes |
| Nested-node field change / independent 100 K excursion | 7.9440% | 8.4296% | <5%, **fails** |

All curved-case exact-reference reservoir-heat checks also fail the unchanged
1 ppm-plus-1e-10 W tolerance. They are reported as approximate errors rather than
forced through the exact affine patch threshold. No exact harmonic nodal/mean
agreement is claimed. The result fails the required combined convergence/heat
assessment even though each changed discrete problem's algebra/energy closes.

| Finest strong-Robin metric | Original consistent | Vertex trial 1 | Hybrid trial 2 |
| --- | ---: | ---: | ---: |
| Max nodal error K | 0.287913 | 0.000000131 | 9.020249 |
| Max facet-mean error K | 0.265133 | 0.260417 | 8.297143 |
| Volume-mean error K | 0.005491 | 0.260416 | 0.080909 |
| Reservoir-heat error W | 0.001833 | 3.368418 | 4.060264 |
| Continuum source/net-heat defect W | roundoff | 4.211076 | roundoff |
| True global envelope | fails | passes | passes |

The hybrid diagonal wall balances against accurately integrated, spatially
averaged forcing over the long original basis support. It can smooth the local
profile severely while retaining global bounds and heat balance. This inference
is supported by the fixture comparison, not a unique diagnosis of the actual
baffle. At most, these tests show why patch tests, global bounds, energy ledgers,
part means or a raw-C convergence number alone cannot establish local accuracy.

The old actual gas K has positive off-diagonals and an interior overshoot with
no wall contribution at the offending node
([existing diagnosis](wo03-gas-field-diagnostic.md)). Diagonalizing wall M cannot
remove that volume defect. No actual factor, mesh, rays, ODE, production-file edit
or adoption was attempted. Future method selection needs both justified volume
discretization/sign/accuracy and accurate local wall/source integration; it is a
different primary decision after this exhausted wall-only treatment family.

Real chord maps also contain varying halfwalls, parallel material/bulk routes,
openings and discontinuities. Their side-local limits, facet subdivision and
power-conjugate registration are unresolved. Neither fixture treatment licenses
edge-node material ownership, arbitrary jump averaging or transfer of old optical
quadrature. The primary retains route selection and integrated acceptance.
