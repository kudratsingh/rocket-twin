# WO-03 external thermal known-answer comparison

CalculiX completed three refinements of the straight affine finite-wall case and
three of an existing concentric-cylinder fixture. Both produce results consistent
with their references at printed precision, but the unchanged 1e-7 K and 1e-10 W
exact/balance checks cannot be established from the seven-significant-digit
output. B and B_strong were not executed; the actual baffle remains unqualified.

## Executed packet and identity

The raw inputs, solver logs, `.dat` files, input hashes, resource accounting and
machine-readable results are in `build/wo03-ccx-thermal-comparison-v1/`.
`/opt/homebrew/bin/ccx` resolves to
`/opt/homebrew/Cellar/calculix@2.23/2.23_1/bin/ccx`; `ccx -v` reported 2.23;
its SHA-256 is `2349c77ebd8302615828ac3911caac45fb0a39363914ee555db1c7e3a86250bf`.
The straight fixture source is `configs/studies/wo03-thermal-error-isolation.yaml`
SHA-256 `04bfb41d359a2f4513c531bf4cb9f7c131d7db4175215a3169c1b22879bc8589`.
The annular source is `configs/studies/wo03-gas-conduction.yaml`; all three
input mesh and boundary-group hashes are recorded. The annular input/reader
implementation used for execution is preserved and hashed in the packet;
`scripts/wo03_ccx_thermal_comparison.py` also contains the corresponding generator
and reader. Annular inputs depend on the existing ignored fixture meshes and are
not self-contained without those hash-matching files.

All solver calls requested one thread and the logs report one CPU for Spooles.
The whole packet consumed 0.305709 child CPU s; maximum recorded cumulative child
peak RSS was 16,269,312 bytes. Individual child wall and CPU values are in the
record. The inclusive setup elapsed wall time was not measured; it cannot be
verified against the ten-minute setup budget. Solver execution stayed within the
120-second per-case and 600-second total CPU allowances.

The first A/4 input exceeded CalculiX's 16-entry node-set limit. A single
syntax fix split set lines; the next A/4 input was rejected at a long numeric
coordinate. The primary agent explicitly replanned one further format-only fix
within the original budget, with no numerical method change and no more retry
cycles. The `.12g` coordinate representation then allowed A/4 and A/8 to run.
The maximum coordinate round-trip difference versus the original float arrays
was 2.78e-17 m for A/4 and A/8 and 4.99e-14 m across the annular levels. Failed
inputs and both correction records are retained.

## Straight box, prescribed hot surface and finite cold film

All use the same six-tetrahedra-per-cell subdivision, 0.0002 × 0.001 × 0.187 m,
k=0.04 W/(m K), hot 573.15 K, cold bulk 308.15 K, h=36030.6 W/(m² K), and
insulated other boundaries. Independent heat is 9.856289341054246 W. All 2/4/8
levels completed and the greatest printed nodal error was 4.816e-5 K. The A/2
printed hot heat was 9.856289 W; this is consistent with the unchanged 1e-10 W
plus 1 ppm heat criterion, but no separate cold-surface integral was computed.

For temperatures in this range the last printed digit is 0.0001 K; assuming
round-to-nearest, each displayed temperature represents an interval of ±0.00005 K.
The resulting bound on maximum absolute nodal error is at most 9.816e-5 K, not
1e-7 K. The exact-temperature criterion therefore remains **unavailable**, not
passed. Printed heat is likewise insufficient to establish 1e-10 W balance.
Per-surface heat, local residual and energy-form balance remain unavailable.

A later read-only surface audit, recorded in the
[integrated comparison](wo03-external-thermal-decision.md), bounds the cold-side
heat using printed field uncertainty. It supplies a surface-heat interval, not
a precise cold heat or a passed energy balance. No additional solve was run.

## Concentric cylinder: physically curved geometry

The pre-existing three Gmsh fixture meshes use inner/outer radii 0.005/0.010 m,
length 0.012 m, k=0.026 W/(m K), inner/outer temperatures 310/290 K and insulated
ends. The independent reference is `T(r)=290+20 ln(0.01/r)/ln(2)` and
`Q=2πkL×20/ln(2)=0.05656385457 W`. This is a physically curved annulus, with a
piecewise-linear mesh approximation of its circular boundary. It is **not** the
935:1 narrow gap or the finite-wall annulus, which remain untested.

| Level | Nodes | Printed max nodal error K | Hot heat W | Cold heat W |
| --- | ---: | ---: | ---: | ---: |
| 0 | 262 | 1.56610 | 0.05818231 | -0.05818231 |
| 1 | 786 | 0.75968 | 0.05714763 | -0.05714763 |
| 2 | 3297 | 0.23505 | 0.05677237 | -0.05677237 |

Printed field and heat errors decrease; finest heat error is approximately
0.369% and medium/fine heat change approximately 0.657%. Printed extrema are
290–310 K at each level; at displayed precision no envelope violation is seen,
but rounding limits a strict no-violation claim. The existing fixture's individual
3% heat and 0.5 K nodal criteria and 5% successive-conductance criterion are met
at the finest level with ample margin over print rounding. Printed hot and cold
rates cancel, but seven-digit output cannot establish the unchanged 1e-10 W
balance criterion. Local balance remains unavailable, so the complete fixture
verification is **not passed**.

## Spatial Robin and documented capability

CalculiX 2.23 [manual](https://www.dhondt.de/ccx_2.23.pdf), section 7.59,
specifies uniform *FILM and uses `FxNUy` with a supplied `film.f` for nonuniform
sink temperature and coefficient. B and B_strong require a continuously varying
effective sink; a matching linked user routine was not established and they
were not executed. Face-centroid constants would alter that boundary without a
quantified approximation error. The quadratic profile in B is in a straight
box; it is not curved geometry. The unchanged approximate-convergence and local
envelope criteria for B and B_strong therefore remain unavailable.

The [2.23 capability overview](https://www.dhondt.de/ov_calcu.htm) documents
steady/transient heat transfer and prescribed/cavity radiation; neither transient
nor radiation was tested here. CalculiX is GPL version 2 or later per the
[project site](https://www.calculix.de/). The local macOS binary was invoked with
`ccx -i case`; the upstream [download page](https://www.dhondt.de/) lists source,
Linux and Windows packages and an older macOS installation guide. No solver
source was vendored. These fixtures do not establish actual-baffle heat routes,
contact, radiation, transient response, design acceptance or flight readiness.
