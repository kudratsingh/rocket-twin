# WO-03 Robin gas-FEM coupling

**The Robin gas-FEM coupling passes its source-independent fixtures and preserves separate bulk states at shared material edges.** The actual coarse gas mesh has also passed a geometry/conductivity-pattern resource preflight. No actual Robin factorization, actual temperature solution or engineering acceptance is claimed: complete physical wall conditions and their mapping remain a separate gate.

Final fixture run **`wo03-robin-gas-20261031T051640941571Z`**, **4.96 s elapsed, one CPU, $0**, has unchanged inputs and twelve passing fixture solves. [Fixture record](../build/wo03-robin-gas/final/record.json), [ordering comparison](../build/wo03-robin-gas/ordering-final/ordering-comparison.json), [actual coarse preflight](../build/wo03-robin-gas/actual-coarse-preflight/preflight.json) and [shared-assembler regression](../build/wo03-robin-gas/gas-regression-current/record.json) retain raw matrices, signs, assumptions, memory data and source/artifact identities. The final regression was recaptured after primary-owned dependency metadata changed; earlier captures remain historical, with unchanged numerical C matrices.

```sh
.venv/bin/python scripts/wo03_robin_gas.py --preset tiny
.venv/bin/python scripts/wo03_robin_gas.py --compare-orderings --output build/wo03-robin-gas/ordering-final
.venv/bin/python -m pytest -q tests/test_robin_gas.py tests/test_gas_conduction.py tests/test_gas_radiation.py
.venv/bin/python -m ruff check src/analysis/robin_gas.py src/analysis/gas_conduction.py scripts/wo03_robin_gas.py tests/test_robin_gas.py
.venv/bin/python -m black --check src/analysis/robin_gas.py src/analysis/gas_conduction.py scripts/wo03_robin_gas.py tests/test_robin_gas.py
.venv/bin/python -m mypy src/analysis/robin_gas.py src/analysis/gas_conduction.py
```

The three Robin tests, three existing gas tests, Ruff, Black and strict typing pass. Primary-owned nonlinear coupling tests are also exercised for compatibility but are not edited or counted as this study's owned fixture suite. No CAD, active vehicle YAML, material allowable, dependency, Git or computer-use change is made.

## Shared assembly and physical boundary conditions

The primary explicitly authorized extracting a public helper from the previously frozen `gas_conduction.py`. `assemble_tetra_conductivity(points_m, tetrahedra, k, ...)` validates geometry and returns sparse conductivity `K`, gradients/volumes, exterior faces/opposite nodes, connectivity and memory diagnostics. It does not invent boundary temperatures or perform an auxiliary Dirichlet solve. Element temporaries are processed in chunks of 25,000; retained gradients, COO arrays and face topology still require memory proportional to mesh size.

The original grouped-Dirichlet API retains its 150,000-tetrahedron fixture cap. The shared helper defaults to that cap, with an explicit primary-authorized ceiling of 750,000 tetrahedra / 150,000 nodes for actual callers. Existing three tests and all four three-level gas fixtures pass after refactoring. Across all twelve comparisons, the raw legacy `C` matrices have **zero numerical difference** from the original record. The prior source file is preserved under `build/wo03-robin-gas/prior-source`; old records are historical, not relabeled with new hashes.

Each exterior triangular facet has exactly one explicit boundary condition. Shared edge/corner **nodes are retained**, and different material faces may connect to different bulk temperatures without imposing different fixed values on the shared node. For constant finite half-wall conductance `h=k_material/delta_halfwall`:

```text
R_triangle = h*A/12 * [[2,1,1],[1,2,1],[1,1,2]]
B_node,bulk += h*A/3
D_bulk     += h*A
A_system    = K_air + R
```

This is a consistent boundary mass matrix, rather than a lumped corner assignment. It follows the Robin weak-form boundary term described in the [MFEM primary boundary-condition reference](https://mfem.org/fem_bc/) and its [boundary mass integrator](https://mfem.org/bilininteg/). Here `h` represents a finite conductive half-wall, not a new convection model.

Physical prescribed gas temperatures are separate conditions with exact elimination and exact reservoir reactions. A Robin face may share nodes with a prescribed face. If **different prescribed temperature IDs share a node**, the input fails instead of selecting an arbitrary corner priority. Two prescribed facets may share the same physical state ID. Insulated faces must be explicit; missing, duplicated, internal or unoriented boundary facets fail.

**Gas-opening physical temperature and radiative-reservoir brightness are independent inputs.** An opening can use ambient gas temperature while an exploratory black-reservoir brightness is hot. Motor case temperature is a prescribed physical surface state. This module receives physical state IDs/values and signed surface loads; it does not choose radiative brightness temperatures or copy them into gas boundary conditions.

## Callable interface, exact signs and linear response

```python
from src.analysis.robin_gas import BoundaryCondition, RobinGasMesh, factor_robin_gas

mesh = RobinGasMesh(points_m, tetrahedra, boundary_triangles,
                    boundary_group_ids, metadata)
factor = factor_robin_gas(mesh, conditions, conductivity_w_m_k=0.026)
answer = factor.evaluate(T_bulk, T_prescribed_physical, Q_surface_into_gas)
T_nodal = factor.reconstruct(T_bulk, T_prescribed_physical, Q_surface_into_gas)
```

Coordinates are metres, connectivity is zero-based integer, boundary facets point outward from gas, and original integer radiation group IDs are preserved. `conditions` is either a mapping from group ID to a homogeneous condition or an explicit row **per triangle**. The latter keeps separate component bulk IDs even where one radiation group spans disconnected components. It does not silently make those components one thermal state.

Scalar examples are:

```python
BoundaryCondition("robin", bulk_id="component_17", h_w_m2_k=4.0)
BoundaryCondition("dirichlet", temperature_id="physical_gas_ambient")
BoundaryCondition("insulated")
```

Let `theta=[T_bulk,T_prescribed]`, with returned ordered state IDs. `L` distributes a **total group load in watts** uniformly by area using `A_triangle/(3*A_group)` at each triangle node. Its transpose `S=L.T` produces the power-conjugate group area mean. Positive loads enter the same FEM surface/gas field that sets wall exchange. Reduced maps are:

| Returned map | Shape | Meaning |
|---|---|---|
| `reservoir_conductance_raw_w_k = C` | `(nr,nr)` | Passive physical-reservoir conductance |
| `mean_by_reservoir_temperature = G` | `(ng,nr)` | Mean surface temperature response to physical states |
| `mean_by_group_neumann_k_w = R` | `(ng,ng)` | Mean surface temperature response to total group loads |
| `reservoir_heat_by_group_neumann = J` | `(nr,ng)` | Heat entering physical reservoirs from surface loads |

```text
T_surface_area_mean = G @ theta + R @ Q_surface_into_gas
Q_into_reservoirs   = -C @ theta + J @ Q_surface_into_gas
Q_into_bulk        = B.T @ T_gas - D * T_bulk
```

Prescribed-reservoir heat is the negative summed exact reaction, including adjacent Robin terms and Neumann loads. Thus the steady signed balance is `sum(Q_into_bulk)+sum(Q_into_prescribed)=sum(Q_surface_into_gas)`. Raw `J≈G.T` is checked rather than forced, as are raw symmetry/PSD, constant-temperature partition, energy balance and reconstructed-map agreement. No matrix, response or coupling is clipped, regularized or symmetrically repaired.

The factor retains sparse LU, `A/B/D/L`, prescribed-node mapping and complete nodal reconstruction. It **does not store an N-node × all-input dense response basis**. Reduced columns are solved in blocks of sixteen; reconstruction uses the same sparse factor. Boundary quadrature temperature is obtained from `T_nodal[boundary_triangles]` and the quadrature barycentric weights. Delta-state/load reconstruction is also the exact linear response of this fixed-coefficient system.

For a declared groupwise-isothermal radiation projection `q(T_mean)`, the nonlinear mean residual is `T_mean-G@theta-R@q(T_mean)` with Jacobian `I-R@dq_dT`. This describes the interface only; the primary owns nonlinear radiation, physical capacity/contact terms and replacement of corresponding legacy air paths. Old air paths must not be retained in parallel without an explicit physical reason.

## Integrated radial cells and variable-h quadrature

For a constant-h triangle crossing liner radial cells, use exact parent-triangle basis integrals:

```python
BoundaryCondition("robin", h_w_m2_k=h,
                  bulk_basis_integrals_m2={
                      "liner_cell_0": [I0, I1, I2],
                      "liner_cell_1": [J0, J1, J2],
                  })
```

`R_triangle` remains the exact consistent full-triangle matrix; each cell receives `B_cell=h*[I0,I1,I2]` and `D_cell=h*sum(I)`. There is no centroid-cell selection. An independent test divides a triangle into two equal subtriangles and compares these exact integrals with degree-two quadrature, including energy/partition and separate bulk-state checks.

An explicitly integrated variable-h wall may instead supply:

```python
BoundaryCondition("robin",
    wall_matrix_w_k=M,                         # 3x3
    bulk_load_vectors_w_k={"component": b},    # three entries per bulk
    bulk_diagonal_w_k={"component": d})
```

This form omits scalar `h/bulk_id/basis` to prevent double counting. With positive quadrature weights, `M=sum(w*h*N*N.T)`, `b=sum(w*h*N)` and `d=sum(w*h)` have the correct passive form. The core checks finite nonnegative data, raw matrix symmetry, `M@1=sum(b)`, `d_i=sum(b_i)` and PSD of the **augmented local wall energy** `[[M,-B],[-B.T,diag(D)]]`. Invalid terms fail; they are not repaired. Exact zero-area cell contributions should be omitted explicitly, with their mapping provenance retained, rather than assigning a fictitious path.

Definitions, quadrature weights, physical half-wall paths, variation/projection tests and source hashes belong in mesh/mapping metadata. Numerical PSD and conservation do not validate a material path, unresolved internal gradients or quadrature accuracy. Variable-h quadrature refinement is separate from gas-mesh refinement.

Matrices and vectors are tied to the **exact triangle vertices/order** used for integration. The actual mesh exporter supplies one-to-one source triangle IDs plus gas-local→source-local vertex permutations. Both matrix indices and each B vector must be permuted consistently. Copying arrays by CAD face ID alone is invalid. No actual mapping transfer is performed here.

## Mean temperature is not mean fourth power

`evaluate` returns area-mean temperature, exact area mean of the **P1 interpolant's fourth power**, fourth power of the mean, reconstructed nodal extrema and raw response-basis ranges. It evaluates no emissivity, view factor or radiation law. For one linear triangle, the fourth-power mean is the sum of its fifteen degree-four nodal monomials divided by fifteen.

The insulated-divider fixture has 310 K and 290 K disconnected sides in a common reporting group: its mean is 300 K, but the mean fourth power differs from `300^4` by **54,010,000 K⁴**. The finite slab's longitudinal surfaces also have a nonzero mismatch. These are concrete reasons to label groupwise-isothermal radiation as a projection approximation. P1 nodal extrema are numerical-field extrema, not a bound on unresolved physical hot spots or a validation of the 215 actual mixed-component radiation groups.

## Three-level fixtures and regression

All four cases reuse the independently verified Gmsh meshes at 3.0 / 1.8 / 1.0 mm target sizes, with constant air conductivity 0.026 W/(m K). Fixture half-wall values are selected numerical constants, not qualified material properties.

- **Finite half-wall slab:** 20×12×8 mm air, 310/290 K bulks, hot/cold `h=4/2 W/(m² K)` and a +0.0002 W surface load. The independent series answer is `q_air=(Th-Tc+Qhot*Rhot)/(Rhot+L/(kA)+Rcold)` with finite surface temperature drops. Temperature error is at most **2.85e−12 K** and reservoir-heat error **3.60e−16 W**.
- **Insulated absent-air divider:** two disconnected volumes, each anchored to its own finite Robin bulk. Exact intercomponent heat is zero; temperature error is at most **3.81e−12 K** and reservoir-heat error **4.72e−16 W**. This does not remove conduction through an actual solid barrier.
- **Shared corners:** six different bulk states and finite face coefficients share all cube edges. Explicit uniform face loads `Q_g=h_g A_g(300-Tbulk_g)` give the exact constant 300 K surface field without corner priority. Temperature error is below **8.53e−13 K**, heat error below **1.11e−15 W**.
- **Prescribed plus Robin:** one physical gas boundary is prescribed at 300 K, neighboring Robin walls are connected to 300 K bulk, and +0.0003 W is applied at the prescribed face. Exact field is 300 K, and the prescribed reservoir absorbs the complete load. Heat error is below **2.16e−14 W**.

All three-level checks pass. Last-two C changes are approximately 9.44e−15 for the slab, **0.3684%** for shared corners and **1.8973%** for the prescribed case; the zero-divider uses absolute-error checks. The nonzero reduced-C changes reflect discretization of general boundary-state basis fields even where the manufactured operating field is exact.

Across all twelve operating cases: maximum signed heat-balance residual **2.16e−14 W**, boundary/element-plus-wall quadratic-form difference **6.46e−12 W K**, raw C asymmetry **4.34e−19 W/K**, and conjugacy error **2.78e−15**. The quadratic form is in W K, not stored energy or heat rate. These checks do not establish a discrete maximum principle.

Raw nonmonotonicity remains visible. Finest slab K contains **5,532** positive offdiagonals; its Robin A contains **5,538**. No condensed C positive offdiagonal appears in these fixtures, but this is not a guarantee for an actual many-surface matrix. The disconnected-domain response slightly exceeds one by about **9e−15**, retained as roundoff. Raw nodal response extrema and positive-Neumann minima are exported without clipping.

## Ordering and actual coarse resource gate

Three slab levels compare COLAMD and MMD_AT_PLUS_A in **separate fresh child processes**. MMD reduces L/U nonzeros from **7,004→6,094**, **53,190→41,424**, and **435,618→339,190** (13–22% reduction). At the finest fixture it is slower, roughly **0.085 versus 0.024 s**; fresh-process peak RSS is approximately **89.4 versus 85.2 MiB**. Lower fill does not guarantee lower total RSS. Raw C differences are at most **8.14e−19 W/K**, and mean/load-map differences at most **2.23e−11 K/W**. The API default remains COLAMD; **explicit MMD_AT_PLUS_A is recommended for the first memory-limited actual attempt**, subject to the primary's decision and observed fill.

The actual coarse preflight reads the accepted immutable mesh SHA-256 `aefc71e318393ae781fefb5e5d2195eb6383dc32214f292eb4445f1de86b4351`. It performs conductivity/geometry/topology and sparsity work **only**, without assigning missing material `h`, prescribed temperatures or Robin states:

| Actual coarse quantity | Result |
|---|---:|
| Nodes / tetrahedra / boundary facets | **80,186 / 427,940 / 144,690** |
| Surface groups / air components | **1,127 / 1** |
| K stored nonzeros | **1,241,556** |
| Preflight elapsed / process high-water RSS | **3.80 s / 596.6 MiB** |
| All-free 64-fill LU estimate | **1,222.25 MiB** |
| Minimum scaled determinant / volume | **2.00784e−12 / 1.13427e−18 m³** |
| K diagonal min / max / ratio | **3.07448e−5 / 542.706 W/K / 1.76520e7** |
| K raw positive offdiagonals | **314,962**, maximum **118.968 W/K** |
| K asymmetry / constant residual | **5.68e−14 / 1.15e−13 W/K** |

Affine quadratic-form residuals are at most **3.74e−10 relative**; the constant-mode assembled residual is **2.50e−13 W K**. Positive `k,V` give the element Gram PSD construction, but no global constrained-spectrum or actual response is claimed. Thin slivers, diagonal spread, raw nonmonotonicity and conditioning remain explicit concerns. **Actual solved-response overshoots are unavailable**, since no solve is performed.

The primary permits **one coarse attempt only after valid mesh and complete BC**, with explicit limits: 100,000 free nodes, estimated LU 1,536 MiB, reduced maps 128 MiB, 750,000 tetrahedra / 150,000 nodes, one CPU and a **300 s child-process cap**. The all-free sparsity estimate fits that gate. Map storage is `8*(nr+ng)^2` bytes, allowing up to 2,969 reservoir states at 1,127 surface groups; actual state count remains unspecified until complete BC. No hypothetical state assignment is used to claim map acceptance.

The module's default fixture guard remains 25,000 free nodes / 512 MiB estimated LU / 256 MiB maps. Estimates use a declared fill model, not a guaranteed RSS limit; assembly and native-factor allocations coexist. The eventual actual child must record native L/U fill, elapsed time, process peak RSS, energy/conditioning and raw response ranges, and stop if the explicit preflight rejects. Limits must not be repeatedly raised or geometry/properties altered to reduce DOFs. No all-three actual factorization campaign is authorized here.

Complete actual wall paths, local/quadrature accuracy, mesh convergence, physical capacities/contacts, legacy-path replacement and spatial radiosity remain primary-owned integration gates. Source-independent fixtures and a resource-compatible sparsity pattern do not close rocket temperature, engineering acceptance, physical testing, owner review or flight release.
