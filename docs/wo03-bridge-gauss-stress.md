# Saved bridge fields: material-local Gauss stress diagnostic

Both retained coarse Elmer displacement fields now have an executed, material-local
stress diagnostic. The procedure differentiates each original quadratic element's
own displacement interpolation and applies that element's original material law.
It does not project stress across the G11/epoxy interfaces. **No strength,
convergence, installed-joint or WO-03 acceptance follows.** The reported local
peaks and substantial normal traction make a shear-only joint screen insufficient.
No native solver, CAD generation, mesh generation, active configuration change,
GitHub action or computer use was performed by this bounded task.

The exact archived inputs are the source deck and metadata in
`build/wo03-g80-bridge-area-budget-coarse-v1/bridge_1p5mm/`, the EQUAL mapped
`equal-readonly-displacements.npz` identified by its recovery record, and the
SINGLE `field_t0001.vtu` identified by its recovery record. SINGLE has no separate
mapped NPZ; the primary explicitly admitted its preserved VTU for bounded read-only
mapping. Generated diagnostic records and complete Gauss samples are under
`build/wo03-bridge-gauss-stress-v1/` and remain ignored.

## Load and material basis, before interpretation

The active performance CAD field calls the quantity
`reverse_retention_design_load_n: 150`. The source hand-check context in
[the motor-support report](wo03-motor-support.md) assumes 150 N reverse force,
50 N per fastener; it does not derive that demand from a measured flight event.
[The bridge structural preflight](wo03-g80-bridge-structural-preflight.md) explicitly
calls 150 N a **service** resultant and requires DF3 on output demands once.
Its study YAML separately records `reverse_service_load_n: 150` and
`design_factor: 3`; `configs/engineering/wo03.yaml` also sets DF3. The active
CAD name's word “design” is ambiguous relative to that documented service-load
interpretation. This report preserves the declared service case and reports only
**raw 150 N stresses**, without multiplying by three or calculating margins.
A later acceptance package must resolve the load basis and apply its declared
factor exactly once. The separate recovery demands, including already factored
recovery screens, are not the bridge's 150 N case and were not reused here.

The actual deck contains G11 E=10,000 MPa and six separately assigned epoxy
films E=100 MPa; every region uses ν=0.3. Deck material sections and element-set
ownership were checked against the saved metadata. These are the original
isotropic numerical hypotheses. The existing 25 MPa G11 hot screen and 1 MPa
adhesive hot shear screen are estimates; G11's 50 MPa cold/25 MPa hot strengths
and 10 GPa modulus are explicitly estimated in the engineering YAML. None is a
laminate-direction, bearing, pull-through, interlaminar, hot mixed-mode bond or
peel allowable. No other material's allowable is borrowed. This report does not
compare normal/peel to an invented capacity or treat von Mises as a laminate
failure criterion.

## Method and verification

For each original C3D10 element, with Jacobian convention
`J[i,j] = dx_i/dξ_j`, the physical shape derivatives are
`dN/dx = (dN/dξ) inverse(J)`. The source deck coordinates are in mm and the saved
Elmer U is in metres: U is explicitly multiplied by 1000 before differentiation,
so strain is dimensionless and stress is MPa. The equations are

`ε = (grad(U) + grad(U)ᵀ)/2`,
`σ = λ tr(ε) I + 2μ ε`,
`μ = E/[2(1+ν)]`, `λ = Eν/[(1+ν)(1−2ν)]`, and
`σ_vm = sqrt(3/2 dev(σ):dev(σ))`.

These are the small-strain, three-dimensional isotropic equations in Timoshenko
and Goodier, *Theory of Elasticity*, third edition, chapter 1. The retained
[official Elmer Stress.F90, pinned commit a19504a](https://github.com/ElmerCSC/elmerfem/blob/a19504ac53ec222e3355e182b08f2ff280c2203a/fem/src/Stress.F90#L1460)
forms the isotropic elastic matrix and computes the symmetric gradient in
`LocalStress` (lines 1460–1485); the pinned
[StressSolve module](https://github.com/ElmerCSC/elmerfem/blob/a19504ac53ec222e3355e182b08f2ff280c2203a/fem/src/modules/StressSolve.F90)
uses that routine. StressSolve source SHA256 is
`13631f3e0d98721a4af4c6730f940c125031280151640390648b3d4fe62e13e6`.
The von Mises invariant is reported as a scalar stress descriptor.

The postprocessor reuses the exact `EDGE`, `dlam` and `grads` statements extracted
from the hash-pinned existing `scripts/wo03_elmer_bridge_input.py`; it does not
execute that script's main. Gmsh was used only to query its original 11-point
Gauss4 reference rule, with no geometry or meshing calls. The recovered physical
points and signed determinant-times-weight values were compared with the original
metadata: maximum differences were 5.422e−10 mm and 2.076e−10 mm³. Jacobians
must be positive. Gauss4 has one negative weight: volume means are **signed
quadrature integrals divided by integrated volume**, not probability-weighted
averages. No percentile or absolute-weight substitution is used.

Before actual use, eight independent patch tests prescribed normal, simple-shear,
hydrostatic and nonsymmetric affine U=A·x on both a skew affine tetrahedron and a
valid curved ten-node tetrahedron whose midsides are not midpoints. They passed
the predeclared 1e−10 reference-scale algebra tolerance with ν=0.3, including the
hydrostatic zero-von-Mises check. The nonsymmetric test prevents an inverse/
transpose error from passing through a diagonal Jacobian accident.

The saved known B displacement field was then differentiated using the original
B deck. Its loaded axial reference is exactly 9.375 MPa, other stress components
zero, with unloaded bars zero. Maximum component errors, in order
xx/yy/zz/xy/yz/xz, were
`[5.598e-12, 5.168e-12, 6.831e-11, 3.489e-12, 1.258e-11, 1.476e-11] MPa`.
The largest error divided by 9.375 MPa is 7.286e−12, satisfying the unchanged
<2% axial known-stress gate and the separately primary-declared full-component
2% reference-scale diagnostic. A **separate native B nodal stress
crosscheck** gives 7.823e−12 normalized error. That homogeneous known case does
not validate globally projected mixed-material interface stress or a critical
bond peak. Actual bridge native nodal stresses were not substituted for the
material-local values.

Two data-admission mistakes stopped before actual stress evaluation: the EQUAL
archive uses compact Elmer IDs, rather than original deck IDs, and the reviewed
hash dictionary stores relative paths. They were corrected without changing a
numerical threshold or rerunning a solver. The original-to-compact map is checked
against sorted used original IDs and every original coordinate, then against the
reviewed map/mesh hashes. EQUAL U is mapped back to original IDs. SINGLE uses the
unchanged frozen `load_mesh`/`read_vtu` functions, verified VTU hash, mapped support
and load IDs, and the preserved strict force check. No original ledger was rewritten.

## Executed coarse results

All numbers below are raw service-load MPa. Each material row is its entire
original region, with eleven Gauss samples per element. These whole-material
means do not define the fixed washer/tab-root/edge regions needed for a later
mesh comparison. Each film integrates to about 9.93977689 mm³; G11 integrates to
5501.02316993 mm³. Full signed Cartesian components, locations of every minimum
and maximum, normals and film traction components are in each case JSON; raw
stress tensors/positions/weights are in each case NPZ.

| Region | Elements | EQUAL mean / max von Mises | SINGLE mean / max von Mises |
|---|---:|---:|---:|
| G11 | 20,409 | 6.474 / 85.246 | 7.671 / 257.346 |
| EPOXY_0 | 345 | 0.812 / 3.969 | 0.724 / 6.465 |
| EPOXY_1 | 352 | 0.803 / 3.917 | 2.801 / 8.776 |
| EPOXY_2 | 346 | 0.814 / 3.958 | 2.829 / 10.243 |
| EPOXY_3 | 346 | 0.803 / 3.924 | 0.735 / 6.524 |
| EPOXY_4 | 347 | 0.812 / 3.880 | 0.383 / 2.206 |
| EPOXY_5 | 350 | 0.804 / 3.944 | 0.382 / 2.220 |

Film normal comes from the saved bridge-interface and rail-back planes, oriented
from G11 toward rail; planarity and 0.1 mm separation are checked. Normal stress
is `n·σ·n`, tension positive. Total shear magnitude is
`norm(σ·n − (n·σ·n)n)`; it includes both in-plane directions.

| Film | EQUAL normal min / max | EQUAL mean / max shear | SINGLE normal min / max | SINGLE mean / max shear |
|---|---:|---:|---:|---:|
| 0 | −5.264 / 1.748 | 0.414 / 1.455 | −9.732 / 0.527 | 0.320 / 1.836 |
| 1 | −5.130 / 1.752 | 0.408 / 1.433 | −11.036 / 8.191 | 1.508 / 4.382 |
| 2 | −5.344 / 1.770 | 0.415 / 1.421 | −12.742 / 8.285 | 1.523 / 4.418 |
| 3 | −5.121 / 1.763 | 0.408 / 1.420 | −9.795 / 0.579 | 0.326 / 1.888 |
| 4 | −5.251 / 1.762 | 0.413 / 1.435 | −0.557 / 1.946 | 0.215 / 1.102 |
| 5 | −5.344 / 1.744 | 0.408 / 1.401 | −0.609 / 1.979 | 0.214 / 1.104 |

Both G11 von Mises maxima occur at original element 33204, Gauss index 1
(zero-based), position `[−5.5785704, 25.7195102, 172.3460194] mm`. This is a
sampled coarse-element peak, not a converged boundary maximum. SINGLE loads film
1/2 much more heavily than film 4/5 under the idealized rigid backing. The normal
stress is substantial and cannot be accepted using the estimated shear-only
screen. Neither these sampled peaks nor whole-film averages establish an actual
joint failure load, a lower bound, or an allowable.

## Resources, retained identity and stop condition

| Phase | Parent CPU s | Wall s | Peak process RSS bytes |
|---|---:|---:|---:|
| Final verification | 1.728 | 2.403 | 493,453,312 |
| EQUAL actual postprocess | 2.623 | 2.667 | 539,508,736 |
| SINGLE actual postprocess | 3.980 | 4.471 | 654,458,880 |

Each execution requested one CPU via environment limits and VTK one-thread
settings, with 30 s CPU limit and 30 s wall alarm. RSS is the process high-water
mark on macOS, not a machine-wide measurement. Synthetic pytest subprocess output
reports eight tests in 0.11 s. There was no native execution. Initial setup
inventory was bounded to approximately five minutes; later implementation and
formatting took additional agent time without expensive native work.

Every case JSON records before/after retained input hashes, unchanged=true,
source identities and resources. `artifact-manifest.json` hashes all retained
outputs. The exact executed source is preserved as `executed-postprocessor.py`
(SHA256 `cd1c887030511f56a0ac5e426a944c11f424bf61519847c1f95f3c31649f28ce`),
alongside `executed-verify.json`. Subsequent Black formatting and a source-citation
docstring correction were verified computational-AST identical; the actual fields
were not processed again. The current source hash is in the manifest. The current
code passes focused Black/Ruff checks and the eight patch tests. To run a future
bounded case with the formatted source, run `--phase verify` first; the script
rejects actual use unless verification matches its exact current hash.

The bounded diagnostic is complete and stops here. No refinement, new structural
solve, baffle attempt or heat-solver work is authorized by this result. The bridge
still lacks three-level displacement/regional-stress convergence, fixed physical
stress regions, realistic rail/keeper/contact/preload sensitivity, anisotropic hot
properties, actual adhesive mixed-mode criteria and physical tests. Preserve the
existing <5% displacement / <10% regional-stress convergence requirements and all
local edge peaks; do not tune them to these results. The next primary decision is
whether the large coarse local demands justify a source-preserving design replan
before a separately bounded convergence campaign. No owner input is required to
read these diagnostics; actual material/lot, fabrication and hot-joint testing
remain owner-dependent acceptance inputs.

The compact publication is
[`runs/wo03-bridge-gauss-stress-20261101-v1/`](../runs/wo03-bridge-gauss-stress-20261101-v1/README.md).
It preserves byte-identical numerical JSON records, exact executed worker and
read-only dependency/test sources, original dataset path/hash references and
future reproduction commands. It deliberately omits the NPZ all-Gauss arrays and
raw generated input meshes/fields. No numerical computation was rerun to prepare
that publication.
