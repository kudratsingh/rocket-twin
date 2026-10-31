# WO-03 stable gas heat evaluation

The cancellation-resistant heat ledger is now implemented and verified for future gas solves. **No actual factorization, PDE solve, ODE or mesh change was performed.** The existing actual coarse fields and their failed record remain unchanged. Their 181.615 K nodal minimum and 305.217 K minimum group mean are still unresolved spatial failures; passing this ledger check does not qualify those temperatures.

The prior observed module was preserved byte-for-byte at `build/wo03-stable-gas-ledger/prior-source/robin_gas.py`, SHA-256 `6a1756130bee8c0db5527d81e86480a41a398366c982784189c9c54dd552fc9f`. The old actual scripts/configurations/records, wall operators, checkpoint writer and shared tetra assembler were not edited. Old configurations still pin their executed module identity and reject silent replay with this changed implementation.

## Implemented numerical correction

The solve is unchanged: the same A/B/D/L/E arrays, material wall terms, conductivity, boundary conditions, native factor options, ordering and RHS vectors produce the same nodal fields. `_solve`, `reconstruct`, `integrated_wall_terms` and `triangle_robin_matrix` retain their original algebra. No matrix is clipped, symmetrized, regularized or altered to enforce monotonicity.

Heat into each finite-wall bulk now accumulates local `b_fi dot (Tnodes_f - Tbulk_i)` before global summation, rather than subtracting the large assembled terms `B.T@T` and `D*Tbulk`. Prescribed-reservoir heat includes **all fixed-node reactions**, evaluated from local element-gradient and wall temperature differences, less the same normalized surface Neumann loads. Local element terms are processed in 25,000-tetrahedron chunks. There is no full node-by-all-input response basis or native LU export. A lazily constructed wall-geometry cache is proportional to facets/paths; transient reaction arrays cover only the current RHS block.

These are the same partition-of-unity weak-form integrals evaluated before absolute-temperature cancellation. Validated source wall-row and B/D partition roundoff defects remain reported. The stored A/B/D/L and source wall arrays are retained untouched; their finite-arithmetic defects are not introduced as an artificial uniform-temperature heat source. The prior assembled reaction expression remains available as `_raw_reservoir_heat` and is reported alongside stable results during evaluation.

Air energy uses local nodal temperature differences. Boundary work uses the same temperature reference in both surface and reservoir terms: `q @ (L.T @ (T - Tref)) - (Treservoir - Tref) @ Qstable`. Differences are formed **before** area averaging. The prior raw/unshifted work and form discrepancy are exported separately. This avoids a residual multiplied by a large absolute reference temperature; it changes neither temperature fields nor prescribed source states. The reference convention and the difference between absolute-mean-then-subtract and mean-of-differences are visible in the result.

`evaluate(...)` still reconstructs through the unchanged native factor, then evaluates the ledger. The new `evaluate_saved_field(field, bulk, prescribed, loads)` performs the same postprocessing on an explicitly supplied finite field **without a solve**. It does not establish that a supplied field solves those boundary data; raw and stable free-node residuals are separately reported. The caller retains source/field identity responsibility. The bounded runner supplies the exact recorded actual field and hashes all its inputs.

Result keys retain the stable primary heat/form values and add raw assembled bulk/prescribed heat, raw heat balance, raw legacy form discrepancy, raw-versus-stable heat difference, stable free residual, reference temperature and source partition diagnostics. Native condensation now obtains C/J from the stable reactions. G/R remain temperature maps from the same solves. C/J are therefore **not claimed bit-identical to the prior assembled ledger**; their observed differences are recorded. The progress callback still receives independent copied blocks and plain metadata. The optional observer changes no numerical value in the new implementation.

## Executed fixture and observation equivalence

Each evidence child uses one CPU and a hard **120-second** cap. Only source-independent small fixtures are factored; the runner rejects actual-sized fixture inputs. The known analytic campaign retains its existing fixture definitions, three refinements, conductivity, thresholds and method caps.

`build/wo03-stable-gas-ledger/verified/fixture-equivalence/record.json` records `wo03-stable-ledger-fixture-equivalence-20261031T064824877581Z`, elapsed **2.283 s**, SHA-256 `0cd0d21fc089670443fa6113e90f8c3da8d3db1a7b8355e9fb7ddcb0483c903b`. Across all **12 fixture levels**:

- Prior 6a versus new A/B/D/L/E arrays, native L/U factors and permutations are **exactly equal**.
- Reconstructed fields, G/R and surface areas are **exactly equal**.
- Maximum intended prior/new C difference is **5.660e-17 W/K**; maximum J difference is **1.776e-15**. These are separately reported rounding-scale reaction changes.
- New default versus new observed fields and **all** G/R/C/J/area arrays are **exactly equal**. This is an independent observation-purity check, not a claim of prior/new C/J equality.

`build/wo03-stable-gas-ledger/verified/known-cases/record.json` records `wo03-stable-ledger-known-cases-20261031T064829572654Z`, elapsed **4.406 s**, SHA-256 `e0f8290426808e4078455243527d388c26b292fa83682d029190cd7af24b485f`. All twelve levels pass the unchanged independent half-wall series resistance, insulated divider, shared-corner and prescribed-reaction benchmarks. Maximum temperature error remains **3.809e-12 K**; maximum stable heat residual is **7.707e-16 W**, and reference-form discrepancy **8.692e-15 W K**.

The focused **15 tests pass**, including existing gas/Robin/coupling/observation tests plus exact-uniform heat, saved-field no-solve evaluation, A/B/D/L immutability, mixed-bulk offset invariance and the all-prescribed/no-Robin case. Offsetting a fixed mixed-bulk example by 1e9 K preserves its difference heat/form results exactly; this is a numerical invariance test, not a material-temperature scenario. Scoped Ruff/Black and strict mypy for the changed module pass.

## Read-only actual-field replay

The replay has **no native LU** and never calls `reconstruct` or `_solve`. It rebuilds only the pinned operator/geometry data needed to evaluate the ten already saved nodal fields. Its source binding explicitly uses the archived 6a module identity for the original artifacts and the new module identity for postprocessing; no executed record is relabelled. The old C/J cache remains an old-heat-ledger reference and is not recondensed, replaced or exported as a new stable operator.

`build/wo03-stable-gas-ledger/verified/actual-field-replay/record.json` records `wo03-stable-ledger-actual-field-replay-20261031T064845023504Z`, elapsed **15.179 s**, SHA-256 `3bd7a2fff5e02d976e9b78bb7f137221de9d1c5908d9e26cb31d58f2417adfff`. All original fields and means are unchanged. Under the original **1 µW / 1 mW K** criteria:

- Maximum stable heat residual across all ten fields is **1.027e-7 W (0.103 µW)**.
- Maximum reference-form discrepancy is **1.455e-10 W K**.
- Stable heat results agree with the preceding read-only local ledger audit within **1.11e-16 W**.
- Original raw heat/form discrepancies remain separately exported, and the original actual record stays **`numerical_checks_pass=false`**.

This establishes the evaluation correction on completed data. It does not fix the coarse discretization's nodal/group undershoots, certify a refined solve, or authorize use of the failed operator as actual-temperature acceptance. The primary retains the investigation, future refined-mesh solve, spatial reliability gate and all thermal/physical decisions.

Run `.venv/bin/python scripts/wo03_stable_gas_ledger.py --output <fresh-local-folder>` for the separately capped fixture/equivalence and completed-field evidence. It does not provide an actual solve or ODE mode. Generated bulk evidence remains local.
