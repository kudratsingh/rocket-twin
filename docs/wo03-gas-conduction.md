# WO-03 steady air-conduction FEM and boundary conductance

**The homogeneous-air Laplace implementation passes four independent fixtures at three mesh refinements.** This verifies the bounded numerical method and its signed boundary interface. It does not provide an actual rocket fluid Boolean, validated surface mapping, accepted conductance matrix or rocket temperature prediction. Those remain separate CAD and coupled-physics tasks.

The final campaign is **`wo03-gas-conduction-20261031T040029804771Z`**, **6.73 s elapsed on one CPU, $0**, with unchanged source inputs. Its record is [`build/wo03-gas-conduction/final/record.json`](../build/wo03-gas-conduction/final/record.json). Twelve Gmsh meshes contain at most **14,067 tetrahedra / 3,297 nodes**, below the 150,000-tetrahedron limit. Each complete three-level fixture takes under two seconds, within its enforced **180 s total** budget. Gmsh 4.15.2, SciPy 1.17.1 and NumPy 2.4.6 are checked against existing pins; no dependency is installed or changed.

```sh
.venv/bin/python scripts/wo03_gas_conduction.py --preset tiny
.venv/bin/python -m pytest -q tests/test_gas_conduction.py
.venv/bin/ruff check src/analysis/gas_conduction.py scripts/wo03_gas_conduction.py tests/test_gas_conduction.py
.venv/bin/python -m black --check src/analysis/gas_conduction.py scripts/wo03_gas_conduction.py tests/test_gas_conduction.py
.venv/bin/python -m mypy src/analysis/gas_conduction.py
```

The three tests, Ruff, Black and strict module typing pass. Tests cover exact affine-field energy, sparse interior elimination, an intentionally nonmonotone obtuse tetrahedron, and invalid boundary knowledge/ownership/inversion/disconnected-component gates. An initial campaign stopped on a NumPy-boolean JSON serialization error in the zero-heat fixture. Its stopped record is preserved at `build/wo03-gas-conduction/record.json`; the serialization correction did not alter mesh or heat equations. Use the **final** record and current interface below.

## Equations, signs and raw matrices

The air domain solves **`div(k grad T) = 0`**, with positive, spatially constant conductivity and no internal source. On linear four-node tetrahedra, shape gradients are constant. Each element contributes **`K_e = k V B Bᵀ`**, where row `i` of `B` is `grad N_i`. Assembly sums these contributions into sparse `K`. This is the diffusion weak form documented by [MFEM's primary integrator reference](https://mfem.org/bilininteg/); mesh/node extraction uses the [Gmsh reference API](https://gmsh.info/doc/texinfo/).

Let `A` map each explicitly owned boundary node to its isothermal group. Free nodes include the volume interior and nodes on declared insulated boundaries. The harmonic basis has `H_B=A` and **`H_I = -K_II⁻¹ K_IB A`**. One SciPy sparse LU factorization supplies one solve per boundary group. The returned raw boundary matrix is **`C = Aᵀ K_B* H`**. It is not averaged with its transpose, clipped or adjusted to force zero row sums.

The signs are explicit:

- **`C @ T`** is heat from each isothermal reservoir **into the gas**, in watts.
- **`-C @ T`** is net heat **inward into each solid/reservoir boundary from the gas**, in watts.
- `net_inward_matrix_w_k` is the raw signed matrix `-C`.
- An offdiagonal pair conductance is `G_ij = -C_ij`; a negative value is reported rather than converted into a positive resistor.

For example, a slab with hot/cold groups gives `C = [[G,-G],[-G,G]]`. At 310/290 K the hot boundary receives negative net-inward heat and the cold boundary receives positive net-inward heat.

The Dirichlet quadratic form **`Tᵀ C T = Σ_e k V_e |grad T|²`** has units **W K**. It is not stored thermal energy in joules, heat rate in watts or entropy production. The record checks that form independently against element gradients, and separately checks signed heat-rate conservation `Σ(C@T)=0`. Positive `k,V` make the assembled element Gram sum PSD; the condensed matrix's symmetric part is used only to diagnose eigenvalues. That symmetric part never replaces raw `C`.

## Approved mesh and boundary interface

```python
from pathlib import Path
from src.analysis.gas_conduction import load_gas_mesh, group_conductance

mesh = load_gas_mesh(Path("mesh.npz"), Path("groups.json"))
result = group_conductance(mesh, conductivity_w_m_k=0.026)
group_ids = result.group_ids
C_raw = result.matrix_w_k
net_inward_matrix = result.net_inward_matrix_w_k
rates = result.evaluate([310.0, 290.0])  # exactly this ordered group list
```

The conductivity in this demonstration is an **estimate**, not a selected hot-air property. The general in-memory input is `GasMesh(points_m, tetrahedra, boundary_groups, metadata)`:

| Input | Contract |
|---|---|
| `points_m` | Finite float array `[N,3]`, SI metres |
| `tetrahedra` | Integer array `[M,4]`, zero-based node IDs, positive Jacobians |
| `boundary_groups` | Ordered mapping from stable group ID to a nonempty, disjoint set of exterior node IDs |
| `metadata` | Explicit boundary classification plus caller-owned STEP/spec/face/mesh provenance |

The non-pickled NPZ contains `points_m` and `tetrahedra`. JSON contains `boundary_groups` and `metadata`; node IDs are zero-based indices into that exact NPZ. A fixture example is in each `final/<fixture>/level-*/groups.json`. All fixtures round-trip through this same public loader before solving.

**`metadata["unlisted_exterior_faces"] = "insulated"` is mandatory.** It declares natural zero-flux conditions on the remaining exterior faces. Missing physical classification fails; a CAD exporter must not substitute that declaration for an unknown wall, aperture or reservoir. Each fixture additionally records all hot/cold/insulated physical face tags. Hot/cold faces are disjoint; shared edges with insulated faces retain explicit Dirichlet ownership. Shared nodes between two temperature groups are rejected until the exporter resolves ownership explicitly. Fully group-owned exterior triangle areas are reported, and point-constraint algebra tests are identified as such rather than passed off as physical surfaces.

The solver rejects orphan nodes, duplicate vertices/tetrahedra, nonmanifold faces, interior Dirichlet labels, nonpositive/numerically degenerate Jacobians and disconnected air components without a defined-temperature group. It does not flip inverted elements or repair geometry. Global tetrahedron intersection and actual CAD solid/void occupancy checks remain the exporter's responsibility. Hashes cover mesh arrays and ordered group ownership; source metadata and artifact file hashes are retained separately.

No radiation code or CAD source is changed. A future actual STEP/face adapter must supply the air void, its holes/end bypasses and complete physical surface labels, then produce these arrays. The present implementation does not infer an actual 1.418% slot geometry or replace it with a fully open annular radial gap.

## Independent exact cases and three refinements

The planar fixtures use length 20 mm, width 12 mm and height 8 mm; all use `k=0.026 W/(m K)` and 310/290 K reservoirs. Analytic heat follows [the DOE Fourier-law and cylindrical-resistance reference](https://www.energy.gov/documents/doe-hdbk-1012-92vol2). Gmsh target sizes are **3.0 / 1.8 / 1.0 mm**; raw mesh counts and errors are retained.

1. **Slab:** insulated lateral faces, complete end reservoirs. Exact `G=kA/L=0.0001248 W/K`; exact heat is **0.002496 W** and temperature is linear.
2. **Concentric cylinder:** `ri=5 mm`, `ro=10 mm`, length 12 mm, inner hot/outer cold, insulated ends. Exact `G=2πkL/ln(ro/ri)` and logarithmic temperature; expected heat is **0.05656385457 W**. Linear tetrahedra approximate the curved boundary, so geometric and solution discretization errors both appear.
3. **Insulated divider:** two disconnected air volumes separated by an absent-air 1 mm slab, each connected to only its own reservoir. Exact transfer is **zero** and each volume has constant temperature. The excluded divider is explicitly insulated. Opacity alone does not remove solid conduction; any real divider's conduction belongs to the caller's solid model.
4. **Longitudinal obstruction:** a 4×4 mm opaque/insulated obstruction occupies the entire 20 mm length, leaving `A_open=80 mm²`. Exact `G=kA_open/L=0.000104 W/K`; exact heat is **0.002080 W**. This tests excluded volume and partly blocked passage connectivity. It is not an exact answer for a short transverse aperture, spreading around shield ends or actual slots.

| Fixture | Tetrahedra at 3.0 / 1.8 / 1.0 mm | Raw relative heat error at those levels | Finest temperature error |
|---|---|---|---:|
| Slab | 509 / 2,128 / 9,524 | −2.85e−14 / +7.16e−14 / −8.13e−14 | 9.10e−13 K |
| Cylinder | 721 / 2,740 / 14,067 | **+2.8613% / +1.0321% / +0.3686%** | **0.2351 K** |
| Insulated divider | 655 / 2,256 / 9,382 | Relative error undefined for zero exact heat | 1.88e−12 K |
| Longitudinal obstruction | 684 / 2,114 / 8,646 | +4.38e−15 / +5.61e−14 / +2.56e−13 | 1.54e−12 K |

Divider hot-boundary raw heats are **−2.734e−17 / +2.235e−16 / +4.992e−17 W**, preserved with relative error `null`. Tiny signed diagonal entries in its raw matrix are also preserved. The last two cylinder conductances differ by **0.6610%**; the other connected exact-affine cases differ at floating-point precision. The final-level cylinder error passes the declared 3% known-heat, 0.5 K field and 5% successive-conductance criteria. Coarse cylinder field errors of **1.566 / 0.760 K** remain visible; they do not receive the finest field check's pass.

## Conservation, PSD and nonmonotonicity findings

Across all twelve solves:

- Maximum signed heat-balance residual: **8.05e−16 W**.
- Maximum raw `C` asymmetry: **1.30e−18 W/K**.
- Maximum raw row-sum residual: **1.73e−18 W/K**.
- Minimum symmetric-part eigenvalue: **−6.51e−19 W/K**, retained as floating-point residual against the declared scaled algebra tolerance.
- Maximum difference between boundary and element quadratic forms: **2.45e−13 W K**.

All algebra/conservation checks pass within their recorded tolerance. No matrix balancing, reciprocity adjustment, row correction or negative-value clipping is performed.

**The raw unstructured `K` matrices are not monotone resistor graphs.** Finest slab/cylinder/divider/obstruction cases contain **5,532 / 8,588 / 5,380 / 4,924** positive offdiagonal entries above the declared reporting tolerance. Their largest positive entries are approximately **2.77e−5 / 3.01e−5 / 2.61e−5 / 2.72e−5 W/K**. Counts, maxima and raw samples are recorded. Two-reservoir condensed matrices have no significant positive offdiagonal here; that does not prove a future many-surface CAD matrix will be monotone. The deliberate obtuse-tetrahedron test produces a negative pair conductance and asserts it remains present.

Symmetry, PSD and conservation are necessary algebra checks, but do not establish a discrete maximum principle or permit silently rebuilding a negative pair as a positive resistor. The primary agent retains the decision about any nonmonotone actual matrix, mesh revision and coupled temperature use.

These fixtures assume stationary homogeneous air, isothermal groups and a steady gas field. They omit gas heat capacity, temperature-dependent conductivity, pressure variation, buoyancy/advection, solid conduction, radiation and moving geometry. Actual CAD boundary coverage, local narrow-slot resolution, gas/solid time-scale suitability and the coupled G80/G54/G12 temperature/soak matrix remain open. No active design, material limit, recovery/guide criterion, physical test, paid-run, owner review or flight-release gate is changed.
