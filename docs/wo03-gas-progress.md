# WO-03 gas factor observation and raw-block checkpoints

The optional progress callback now exposes where a gas factor spends time without changing its physical equations, raw matrices, ordering or numerical thresholds. It is verified on source-independent fixtures. **No further actual-mesh factor was attempted**, and the capped coarse attempt remains a failure with native LU phase unknown. Actual gas/solid transient and thermal acceptance remain open.

Before editing, the executed Robin module was copied byte-for-byte to `build/wo03-gas-progress/prior-source/robin_gas.py`, SHA-256 `21c115c6ca170a4eecf1bcad222fcea94b61de5482a3eb91533b51eafff1825b`; `source.json` records that identity. The old actual-factor script, configuration, report and execution records were not edited. Their pinned old module identity still means the new module cannot silently relabel or rerun the old study. A future actual attempt needs the primary's explicit source/configuration decision.

## Callable interface

`factor_robin_gas(..., progress_callback=callback)` adds one optional keyword, default `None`. The existing default ordering, 16-column RHS block size, conductivity/half-wall inputs, caps, checks, arithmetic and returned arrays remain unchanged. The callback has signature `callback(event: dict[str, Any]) -> None`. Its return value is unused. Any callback exception stops the factor with `GasProgressCallbackError`, preserving the original exception as its cause; missing checkpoints never become successful progress.

Each event carries a phase, monotonic `elapsed_s`, measured process high-water RSS in bytes, copied ordered-ID lists, copied plain resource counts and `complete_operator=false`. IDs/counts not yet established are empty; no face ownership or physical state is invented before validation. Later resource counts include node/element/face/state counts, matrix nnz, diagonal extrema, minimum tetrahedron quality/volume, free nodes, preflight memory estimates/limits, RHS block size and returned native L/U nonzero count. Memory figures retain their original meanings: an estimated LU allowance is not a hard process RSS allocation limit.

| Phase pair | Meaning |
|---|---|
| `assembly_begin` / `assembly_end` | Existing geometry validation and tetra conductivity assembly |
| `wall_build_begin` / `wall_build_end` | Complete exterior/physical-boundary validation and A/B/D/L construction |
| `preflight_begin` / `preflight_end` | Existing free-matrix/resource guards; a rejected end event has `accepted=false` before the original exception |
| `LU_begin` / `LU_end` | Existing native `splu` call with unchanged ordering; returned native time/fill is reported |
| `reservoir_block_begin` / `reservoir_block_end` | Ordered reservoir columns: component bulk states followed by prescribed physical states |
| `surface_block_begin` / `surface_block_end` | Ordered total surface-group Neumann columns |
| `final_checks_begin` / `final_checks_end` | Existing raw symmetry/PSD/conservation/conjugacy checks; end reports `algebra_checks_pass` |

Block events include zero-based half-open `column_start` and `column_stop`. End events include independent copies of the completed raw G/C or R/J column slices in `map_blocks`, with their canonical response names. They expose no live matrix view, native LU or full node-by-input response basis. Mutating an event's arrays, ID lists or counts is verified not to alter the factor. The complete nodal field remains reconstructable through the returned factor, with the existing physical and numerical limitations.

Observed elapsed time includes callback/checkpoint I/O. `native_LU_elapsed_s` still times the native call, with callback work outside that timer. Observation naturally changes wall time and RSS; those resource diagnostics are not claimed byte-identical. Raw numerical maps and reconstructed fields are.

## Atomic checkpoint observer

The new `scripts/wo03_gas_progress.py` provides `BlockCheckpoint(directory, source_binding, interrupt_after_blocks=0)`. The binding pins input hashes and explicit physical inputs, including conductivity, conditions, ordering and RHS block size. The supplied nested metadata is copied. Output must be fresh: there is no implicit resume, block reuse or checkpoint merge API.

At each returned block the observer writes the two raw reduced slices to a temporary NPZ and atomically renames it, then atomically updates `manifest.json` with the exact column range, shapes, SHA-256, source binding, ordered IDs and plain phase/resource history. Any interrupted or failed checkpoint retains `complete_operator=false`, `numerical_checks_pass=false`, and `partial_operator_usable_for_ODE=false`. An orphan temporary/block file cannot complete an operator. Arrays are neither padded nor clipped.

`finalize(returned_factor)` requires the final successful algebra event and a returned factor, matching ordered IDs, unchanged block hashes, exact equality with all returned raw map slices, and each column covered exactly once. Only then does it atomically export the complete five-array response NPZ/state JSON and mark the manifest complete. Complete fixture caches are verified against the existing hash-checking `RecordedGasResponse` reader. They still cannot reconstruct a new spatial field, and are not actual thermal evidence. No partial cache is passed to an ODE.

This is checkpointed evidence of returned map work, not a native restart design. If a future capped child is killed, the native factor is lost. Another native factor, any skipping/merging of prior blocks, or a larger elapsed/memory allowance requires a separate primary decision. No native LU bulk or full nodal response basis is exported.

## Executed verification

The fixture-only runner refuses meshes over 5,000 nodes or 20,000 tetrahedra before factorization; it exposes no actual-CAD solve mode. Run `.venv/bin/python scripts/wo03_gas_progress.py --output <fresh-local-folder>`. It uses the frozen source-independent fixture definitions and preserves the original 150,000-tetrahedron method cap. BLAS/OpenMP thread counts are one. Each known fixture remains bounded by 180 seconds across its three levels.

`build/wo03-gas-progress/final-fixtures/record.json` records run `wo03-gas-progress-20261031T053926281480Z`, elapsed **2.427215 s**, SHA-256 `65bfbb822594775470f127fe517e3a7ffb8292c76f1b385c4b085b35cd05466e`. Across **12 cases** (four fixtures × three refinements), the preserved prior module, new default call and observed/checkpointed call produced **exactly equal G/R/C/J, group areas and reconstructed nodal fields**, with every source identity unchanged. Thus no changed numerical value is hidden behind a tolerance comparison. The final runner also deliberately interrupts a known slab after one returned reservoir block: its persistent manifest remains incomplete, one raw block is retained, no final response cache exists, and the callback failure propagates explicitly.

The unchanged analytic Robin campaign was rerun at `build/wo03-gas-progress/known-Robin-regression/record.json`, run `wo03-robin-gas-20261031T053829517047Z`, SHA-256 `730063735f729bd20f1560ffaa2a5e7e7d55489e42b41e00e06bbf7303314917`. All 12 fixture levels pass. Maximum temperature error is **3.809e-12 K**, maximum absolute heat-balance residual **2.151e-14 W**, and maximum absolute energy-form discrepancy **6.451e-12 W K**. The separately identified legacy 12 raw conductance matrices still differ by exactly zero. Known cases include independent finite-half-wall series resistance, an absent-air insulated divider, different Robin materials sharing corners and exact prescribed reactions. These numerical fixtures do not qualify actual materials, local gradients, gas advection, opening histories or the actual mesh.

The focused **12 tests pass**: three new progress/checkpoint tests plus the existing gas, Robin and coupling checks. New checks exercise full 16-column plus tail blocks, deliberate mutation of copied observer data, exact default/observed fields, complete-cache reader compatibility, interrupted and corrupted checkpoint rejection, explicit observer failure and the original resource rejection before native LU. Scoped Ruff/Black and strict mypy for `src/analysis/robin_gas.py` pass. No actual probe success, actual ODE execution or temperature-limit pass is claimed.
