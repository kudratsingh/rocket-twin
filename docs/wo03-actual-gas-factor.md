# WO-03 one actual coarse nominal-wall gas factor

This study executes one resource-capped factorization of the actual coarse gas mesh with the complete, separately recorded material half-wall operator. The original gas and Robin method modules remain frozen. Its results are gas/surface numerical checks and reusable linear response maps; actual solid transient temperatures, radiation, the required thermal uncertainty matrix, installed material gradients and thermal acceptance remain open.

The mesh contains 80,186 vertices, 427,940 tetrahedra and all 144,690 exterior triangles. The sidecar maps every gas facet to exactly one source optical triangle and gives the local vertex permutation. The script verifies bitwise equality after the original millimetre-to-metre conversion, original CAD face IDs and radiation group IDs, then applies the permutation to both axes of each wall matrix and to each bulk-load vector. There are 141,699 finite Robin facets and 2,991 prescribed-temperature facets. No unclassified face becomes insulation.

The material operator retains all 353 component bulk IDs, including the 16 independently integrated liner cells. The specialized liner rows replace their deliberately unused scalar NaNs with their explicit integrated B/D arrays. An exactly zero cell intersection contributes zero; negative or nonzero terms are never discarded. The source three-point chord field remains a screening approximation with unresolved local gradient and quadrature variation, including a maximum sampled chord ratio of 21. No component-parent projection is applied here.

The selected source is `combined_300C_eps09_at35C`, scenario index 3 in the engineering thermal source, with air conductivity **0.04 W/(m K)**. Material wall M/B/D values use the supplied **nominal** conductivity operator. This is neither the low-air-conductivity operator nor the high-material-conductivity uncertainty corner. The acceptance label in the source file is separately preserved, including its spelling `combined_300C_eps0.9_at35C`.

The physical prescribed-temperature hypothesis is explicit:

| Original CAD face | Original physical temperature identity | This screening assignment |
|---|---|---|
| 901, motor fore end | `unresolved_motor_fore_end_surface_temperature_k` | `screening_shared_required_hot_case_history_k` |
| 902, motor cylindrical case | `prescribed_motor_case_surface_temperature_k` | `screening_shared_required_hot_case_history_k` |
| 903, motor aft/nozzle end | `unresolved_motor_aft_end_nozzle_surface_temperature_k` | `screening_shared_required_hot_case_history_k` |
| 1, 3, 5, 7, 9, 11, 13, 15, 802, actual gas openings | `ambient_opening_gas_temperature_k` | Same ambient physical gas identity |

The three motor histories are not established by this alias. It is a deliberately shared required-hot screening history that avoids assigning conflicting fixed temperatures at their common edge nodes. The original distinct hypotheses and their source metadata remain in the artifact. Physical opening gas temperature is independent of radial/fore/aft radiative brightness. This factor has no radiation brightness input.

The single child has a 300-second elapsed cap, one BLAS/OpenMP thread, at most 750,000 tetrahedra, 150,000 nodes and 100,000 free nodes, a conservative estimated-LU limit of 1,536 MiB and a reduced-map limit of 128 MiB. Ordering is explicitly `MMD_AT_PLUS_A`, selected after the separately recorded known-case comparisons. The LU allowance is an estimate before factorization, not an allocator-enforced process RSS limit. The final record reports actual native L/U nonzeros and process high-water RSS if the native call returns. The attempt sentinel prevents an automatic second attempt or a budget increase.

Raw reduced matrices follow the frozen Robin signs. For ordered reservoir temperatures theta (bulk states followed by prescribed physical states) and signed total group surface heat q, area-mean temperatures are `G @ theta + R @ q`; heat into each reservoir is `-C @ theta + J @ q`. Positive q enters the shared FEM surface/gas system. G/J are power-conjugate mean/load maps. Area-mean temperature is distinct from area-mean fourth power and local temperature; the explicit fields record that mismatch. Raw positive off-diagonal conductances, negative response entries, energy/form residuals and overshoots remain visible without clipping, symmetrization or corner priority.

The offline cache contains the exact array names consumed by `RecordedGasResponse`: `mean_by_reservoir_temperature`, `mean_by_group_neumann_k_w`, `reservoir_conductance_raw_w_k`, `reservoir_heat_by_group_neumann`, and `group_areas_m2`. Its JSON carries ordered `group_ids`, `bulk_ids`, `prescribed_ids`, diagnostics and exact input hashes. The cache supports repeated linear mean/heat responses; it cannot reconstruct a new spatial field. The separately saved check fields are the particular reconstructions executed while the native factor existed. Native LU storage is not exported or committed.

Run the mapping-only preflight with `.venv/bin/python scripts/wo03_actual_gas_factor.py --validate-only`. The actual study command is `.venv/bin/python scripts/wo03_actual_gas_factor.py`; it refuses a repeated attempt in the same output directory. Generated bulk arrays remain local under `build/wo03-actual-gas-factor/coarse-nominal/`. The immutable execution outcome and checks are recorded there in `record.json`; the results below are filled only from that executed artifact.

## Executed outcome: capped, no actual response cache

The sole attempt `wo03-actual-gas-factor-20261031T052709876340Z` reached the **300-second child cap**, with parent elapsed time 300.116906 s and measured child process high-water RSS **2,091,220,992 bytes (1,994.344 MiB)**. Status is `CHILD_CAP_OR_FAILURE_NO_RESULT`; the child was killed and reaped by the wrapper. Local compute cost is $0. No repeated factorization, larger time allowance, larger memory estimate, property substitution or mesh repair was executed.

The mapping-only check and the child both completed the exact correspondence and full physical classification above. Its final progress phase was `entering_ONE_factor_and_reduced_maps`. The frozen method returns only after assembly, native LU, all reduced blocks and algebra checks; therefore the native LU start/completion, actual L/U fill, reduced-block progress and numerical checks are **unknown** for this attempt. A zero-length worker log means no Python failure was reported before the cap; it does not establish native LU completion.

There is no `gas-response.npz`, `gas-response.json` or `checked-gas-surface-fields.npz` from this attempt. Uniform 300 K, the 300°C case/35°C ambient response, signed 1 W probes, actual-mesh symmetry/PSD/energy residuals, reconstructed overshoots and actual final diagonal-range reports remain **unavailable**, rather than zero or pass. The prior standalone K/pattern preflight is separately identified evidence, not a completed Robin factor: `build/wo03-robin-gas/actual-coarse-preflight/preflight.json` (SHA-256 `0b90edf78044652bb826f1bcc2d985071b88f90931f3e54464a7057fdf1d929b`). It reported minimum scaled determinant 2.00784e-12, minimum volume 1.13427e-18 m³ and K-diagonal ratio 1.765197e7. Those slivers remain an unresolved conditioning concern. No actual gas convergence claim follows from this coarse attempt.

The numerical fixture tests belong to the frozen gas/Robin foundation; they do not fill these missing actual results. The complete chord operator has its own approximation limits. All actual transient/coupled-temperature results, required material uncertainty corners, solid temperature limits and engineering acceptance remain open.

## Proposed phase/checkpoint correction, not executed

Before a primary-authorized repeat, add an optional observation callback to the frozen Robin function, with no equation, geometry, ordering, numerical-threshold, property, RHS block-size or budget change. The existing default path must remain behaviorally identical. The callback would atomically record monotonic elapsed time and RSS at:

1. Validated tetra assembly, including nnz, diagonal range, minimum element quality and volume.
2. Complete wall/exterior validation and A/B/D/L assembly.
3. Free-node/memory preflight, before calling native LU, including rejected estimates if applicable.
4. Native LU start and return, with actual elapsed time and L/U nonzero counts.
5. Start/return of each ordered 16-column reservoir or group-load response block.
6. Start/return of raw reduced symmetry/PSD/conservation diagnostics and final cache export.

On each returned response block, an observer may save only the raw reduced G/C or R/J slices plus their exact column range to a temporary file and rename it atomically. Each block manifest must pin all mesh/condition/operator/source hashes, air conductivity, nominal material selection, ordered IDs, ordering and array shapes, and include checksums and `complete_operator=false`. Store numerical diagnostic extrema and per-block timings alongside the slices. Do not retain the full node-by-all-input response basis, and include checkpoint I/O in the same elapsed/resource accounting. No native LU bulk export or commit is proposed.

Partial blocks are evidence of returned work, **not** a loadable `RecordedGasResponse`. An incomplete operator must not drive the nonlinear/transient runner or be padded with zeros. A later authorized repeat still needs a fresh native factor unless a separate restart method is explicitly designed; copying completed blocks into a future final operator would require an explicit provenance/residual-check plan and primary decision. This proposal does not silently turn the 300-second cap into multiple computation windows.

Before any actual repeat, rerun the existing gas/Robin fixture refinements and compare every raw matrix/field for an unobserved call against an observed/checkpointed call. Require equal source identities, complete column coverage, array equality where deterministic, unchanged conservation/PSD/overshoot results, callback-disabled backward compatibility and a deliberately interrupted known-case run that leaves only an explicitly incomplete manifest. Small fixtures can verify instrumentation equivalence, but cannot predict 80,186-node LU scaling. Primary approval is still required for the source change and any further bounded actual attempt.
