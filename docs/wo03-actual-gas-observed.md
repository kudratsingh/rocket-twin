# WO-03 observed actual coarse gas diagnostic

The actual coarse factor and all ten field probes completed in **892.496 seconds**. All 94 response blocks and the unchanged matrix algebra checks returned, and the canonical cache is preserved. **The numerical field gate failed:** energy/form residuals exceed pinned absolute tolerances, and the hot-case field has large undershoots, including surface-group means below the minimum prescribed physical temperature. `numerical_checks_pass=false`; no ODE or thermal acceptance follows from this cache.

This is the primary-authorized **one observed repeat** of the original actual coarse gas factor. The elapsed cap is explicitly revised from 300 to **900 seconds**, with one CPU, to prioritize a completed actual-baffle diagnostic calculation. This is a compute-budget revision, not a temperature-limit or engineering-criterion change. The old 300-second failed attempt and its three source files remain intact. No automatic further attempt or budget increase is authorized.

The actual mesh, original optical facets, exact source-vertex permutation, material M/B/D arrays and physical boundary hypotheses are unchanged. The mesh has 80,186 nodes, 427,940 tetrahedra and 144,690 completely classified exterior facets: 141,699 Robin and 2,991 prescribed. All 353 material bulk IDs and the 16 integrated liner cells remain distinct. The source optical and gas vertices match bitwise in SI after the verified permutation; both matrix axes and each B vector use that permutation. No missing wall path is replaced, clipped or insulated.

Air conductivity is **0.04 W/(m K)** from source scenario index 3 for `combined_300C_eps09_at35C`. Material M/B/D values remain the supplied **nominal** operator. This run is not the high-material-conductivity corner or the low-air-conductivity case. The three physically distinct motor faces retain their original hypotheses in metadata; only this declared screening assigns faces 901, 902 and 903 to `screening_shared_required_hot_case_history_k`. All nine actual gas openings use `ambient_opening_gas_temperature_k`. Their radiative brightness identities remain independent and are not an input to this linear gas factor.

The frozen observed Robin module is SHA-256 `6a1756130bee8c0db5527d81e86480a41a398366c982784189c9c54dd552fc9f`. The prior executed module, SHA-256 `21c115c6ca170a4eecf1bcad222fcea94b61de5482a3eb91533b51eafff1825b`, remains in local `build/wo03-gas-progress/prior-source/`. The separately pinned equivalence run compares prior/default/observed paths across all 12 known fixture levels and gives exactly equal raw maps, group areas and reconstructed nodal fields. The difference is observation and checkpointing; the physical algebra, geometry, material data, ordering and raw numerical checks are unchanged. See [the instrumentation evidence](wo03-gas-progress.md).

The resource gates remain **100,000 free nodes, 1,536 MiB estimated LU, 128 MiB reduced maps, 750,000 tetrahedra and 150,000 nodes**. Ordering is `MMD_AT_PLUS_A`; RHS blocks are 16 columns. The estimated LU allowance is not an allocator-enforced total process RSS limit. Callback records expose measured process high-water RSS, actual returned L/U fill and phase/block timing. One BLAS/OpenMP thread is pinned. No native LU or full node-by-all-input response basis is exported.

The new wrapper reuses the unchanged original condition builder. Configuration pins the wrapper, original condition builder, checkpoint writer, observed module, shared assembler, equivalence record, original failed record, mesh/groups/sidecar/optical source, full wall operator/metadata/QA and engineering thermal sources. Start and completion hashes are recorded. Source files are not changed during the attempt.

`build/wo03-actual-gas-observed/coarse-nominal/progress.json` exposes the last phase, ordered IDs, resources and returned-block count. `checkpoints/manifest.json` retains the full phase history and atomic, hash-bound raw G/C and R/J blocks. Partial manifests remain explicitly incomplete and cannot feed an ODE. Only after every response block and the unchanged final algebra checks return can the checkpoint writer finalize and the wrapper publish canonical `gas-response.npz`/`gas-response.json`. The record's complete field checks and `numerical_checks_pass` are still required by the primary's diagnostic runner. The offline cache cannot reconstruct a new spatial field.

The wrapper executes the same uniform 300 K, 300°C motor/35°C ambient, and selected signed 1 W checks as the prior script while the native factor is alive. It reports raw surface/gas fields, energy/form balance, map-reconstruction differences and overshoots. These are numerical probes with prescribed bulk temperatures, not solid transient temperatures or thermal qualification. Small tetrahedra, nonmonotone FE responses, variable-chord quadrature accuracy, gas mesh convergence, local material gradients, physical histories and full uncertainty/acceptance remain separate findings. The primary owns the nonlinear/radiation/ODE calculation and resulting engineering decisions; this wrapper does not run it.

Run `.venv/bin/python scripts/wo03_actual_gas_observed.py` once in its fresh default output directory. A persistent attempt sentinel rejects another run there. Mapping-only verification uses `--validate-only` and performs no factor. The execution outcome below is populated only from the separately recorded actual child.

## Completed execution and failed numerical gate

Run `wo03-actual-gas-observed-20261031T055158050983Z` returned in **892.495840 s** parent elapsed / **891.891890 s** child elapsed, before its hard 900-second cap. It performed one factor attempt, no ordering change, no property substitution and no retry. Input hashes before/after agree. Status is `ONE_OBSERVED_ACTUAL_FACTOR_CHECKS_FAILED_NOT_ACCEPTED`.

The resource preflight accepted 78,124 free / 2,062 prescribed nodes, 1,203,776 free-matrix nonzeros, **1,242,666,496 bytes (1,185.099 MiB)** estimated LU and **17,570,592 bytes (16.757 MiB)** reduced maps. Native `splu` returned in **513.450142 s** with **42,171,652 L/U nonzeros**. Measured process high-water RSS was **3,388,751,872 bytes (3,231.766 MiB)**. The actual process RSS includes assembly, native workspace, extracted L/U and response-block work; it is distinct from the preflight's LU-only estimate.

All 23 reservoir blocks and 71 surface-load blocks were retained. The checkpoint manifest is `complete_operator=true`, with the canonical ordered 1,127 surface groups, 353 component bulk states and two prescribed physical temperature identities. This identifies a complete returned linear operator, not successful physical/numerical temperature verification. All ten particular nodal and area-mean field probes were also saved; no spatial reconstruction is claimed for a new input from the reduced cache alone.

The checkpoint writer's `numerical_checks_pass=true` is scoped to its returned linear-map algebra/completeness validation. The authoritative actual-study `record.json` has **`numerical_checks_pass=false`** after the full field probes. The manifest flag must not substitute for that stronger gate.

The unchanged algebra checks pass: C symmetry discrepancy **8.193e-14 W/K**, maximum C row sum **5.749e-9 W/K**, mean-load symmetry discrepancy **3.695e-13 K/W**, power-conjugacy discrepancy **3.605e-12**, and uniform mean partition discrepancy **3.602e-12**. Minimum symmetric-part eigenvalues are **4.788e-11 W/K** for C and **−4.255e-14 K/W** for the mean-load map, under the existing roundoff criteria. No matrix was symmetrized or clipped; symmetric parts are used only for the existing eigenvalue diagnostics.

The field gate remains failed under its original limits:

| Probe | Returned result | Pinned check / finding |
|---|---|---|
| Uniform 300 K, unforced | Maximum temperature error **1.230e-8 K** | Temperature limit 1e-4 K passes |
| All ten probes | Absolute heat-balance residual **1.998e-6 to 3.958e-6 W** | All exceed the unchanged 1e-6 W absolute limit |
| Signed loads on groups 1 and 5 | Absolute energy-form discrepancy up to **1.187e-3 W K** | Four cases exceed the unchanged 1e-3 W K limit |
| Hot motor 573.15 K, other reservoirs 308.15 K | Nodal field **181.615257 to 602.731406 K** | 13,562 nodes below the prescribed interval; one above it |
| Same hot case, area means | **305.216634 to 573.150000 K** | Group 505 mean is **2.933366 K below** the prescribed minimum; the issue is not restricted to interior nodal extrema |

Raw response diagnostics also expose large nonmonotonicity: reservoir basis nodal coefficients span **−0.660723 to 1.456991**, positive-load nodal basis responses span **−117.491 to 863.623 K/W**, and minimum area-mean reservoir/load coefficients are **−0.297996** / **−19.025930 K/W**. C has **3,502** positive off-diagonal entries above its declared tolerance, with maximum **+0.009043585 W/K** (a negative pair-conductance interpretation). K has 300,310 and A 482,020 positive off-diagonal entries above that tolerance. These are raw findings, not repaired values. The minimum scaled tetrahedron determinant **2.008e-12**, minimum volume **1.134e-18 m³** and K/A diagonal ratio **1.765e7** remain conditioning/mesh concerns; this record does not isolate which discretization/conditioning mechanism produces the undershoots.

The prior 300-second failed run remains unchanged. This observed repeat establishes a completed but numerically unaccepted actual-CAD gas calculation. It does not justify an actual solid temperature, a required transient pass or feeding the cache to the current ODE gate. The primary may separately authorize bounded read-only verification of these complete returned maps/fields. No such follow-up, another factor or actual ODE was performed here.

## Preserved local artifacts

All artifacts are under `build/wo03-actual-gas-observed/coarse-nominal/` and remain local generated bulk data:

| Artifact | SHA-256 |
|---|---|
| `record.json` | `d4b4cffe6d296f2ae446ad389afd6513c2f5f2af28113b8345e5652754145fee` |
| `gas-response.npz` | `ed6a820d15d64224fd3201ef230f341da69304ae490559c4c79303a507f02ded` |
| `gas-response.json` | `7725547235cd8d07ea2461bb42539345362b8d77b12821088f50346291f33e04` |
| `checked-gas-surface-fields.npz` | `741fcec8ef7684d43bc1420fd41bc8ff6c30c35cd617d4d0dbd055ad4d12bea7` |
| `checkpoints/manifest.json` | `23b6fbfc9898735d9657c04d551b76d734057fe162f2b9c0779fe1665d685bc4` |

The complete raw block files, manifest history, worker log, attempt sentinel and failed field-check record are preserved. Scoped Ruff/Black pass for the new wrapper. The old three actual-factor files/record and frozen Robin/assembler/observer sources remain unchanged. No raw repair or relaxed numerical criterion is applied.
