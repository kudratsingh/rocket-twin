# WO-03 read-only completed-field heat ledger

The completed coarse field's **micro-watt heat-ledger failure is dominated by subtraction and assembled summation**, while its large spatial undershoots remain a separate unresolved failure. A local temperature-difference ledger gives about **0.10 µW** residual on all ten saved probes, below the unchanged 1 µW threshold. This read-only diagnostic does **not** change the actual record, solver, raw maps or fields, and does not relabel `numerical_checks_pass=false` as a pass.

The new script reads the immutable [observed-factor outputs](wo03-actual-gas-observed.md), their exact wall operator and mesh, and the recorded bulk/prescribed/Neumann states. It reassembles the pinned tetra conductivity and boundary matrices solely for reaction/energy postprocessing. It performs **no factorization, linear/PDE solve, ODE or new mesh**, and uses one CPU with a hard 120-second child cap. The actual audit completed in **7.458981 s**, with source identities unchanged and about 842 MiB process high-water RSS. All prescribed-node reactions are retained; no opening or motor reaction is dropped to make a balance close.

## Compared ledgers

For wall triangle f and bulk i, the raw assembled ledger is `B.T @ T - D * Tbulk`. The local-difference ledger accumulates `b_fi dot (Tnodes_f - Tbulk_i)` before summing into each bulk. The exact facewise counterpart of the raw expression additionally retains `(sum(b_fi)-d_fi)*Tbulk_i`; those source-partition defects are reported separately. These reordered calculations expose floating-point cancellation rather than silently replacing a matrix or discarding a term.

Prescribed heat is independently recomputed from **all** prescribed-node reactions `-E.T @ (A@T - B@Tbulk - L@q)`. That raw calculation reproduces every saved heat-balance residual to within **4.24e-22 W**. The audit then compares local wall reactions with the raw `K@T`, and with independent element Fourier reactions computed from local temperature differences and the existing gradients. No new field is solved. The two local prescribed-reaction routes agree to roundoff, so omission of prescribed heat is not responsible for the original discrepancy.

| Saved/diagnostic case | Original assembled residual | Local wall/element difference residual |
|---|---:|---:|
| Returned uniform 300 K | −2.954785 µW | +0.098043 µW |
| Returned hot case, 573.15 K motor / 308.15 K other reservoirs | −1.998102 µW | +0.102689 µW |
| All ten returned probes | −1.998 to −3.958 µW | +0.097895 to +0.102689 µW |
| Exact constant 300 K countercheck | −3.105790 µW | **Exactly 0 W**, including all individual local bulk and prescribed heats |

The maximum facewise wall-row partition defect and path `sum(b)-d` defect are only **5.684e-14 W/K**. In contrast, after global assembly the maximum `B` column-sum minus `D` discrepancy is **6.083e-9 W/K**. At a roughly 300 K absolute temperature, that multiplication/subtraction scale is micro-watts. Actual differences in individual bulk heats between the raw and local calculations reach about **2.1 µW**. Retaining the explicit source partition defects changes the hot local ledger by only about **0.245 nW**.

The raw `K@1` defect is also measured rather than assumed zero: maximum absolute **2.646e-13 W/K**, signed global sum **−2.315e-14 W/K**, and absolute row sum **1.267e-12 W/K**. Multiplication by 300 K places its aggregate scale far below the observed micro-watt effect. Replacing only raw air reactions with local-gradient reactions changes the local prescribed heat by about 1e-12 W or less; the dominant discrepancy is the bulk-wall cancellation/summation.

For the hot probe, the raw absolute reservoir-heat sum is about **1,922.84 W**, while its signed conservation discrepancy is micro-watts. That is a numerical scale comparison for this prescribed-field probe, not a measured power, motor history or solid transient result. Uniform heat should instead be exactly zero; the exact-constant countercheck exposes the raw absolute-temperature cancellation without requiring a large physical heat scale.

## Form balance and uniform-mode roundoff diagnostic

Using the same saved fields, local-difference air/wall energy and local reactions give maximum form discrepancy **3.164e-5 W K** over the ten probes, under the unchanged **1e-3 W K** limit. The original maximum was **1.187e-3 W K**. No original criterion is changed. Reference-shifted boundary work is exported separately; its difference from unshifted work follows `Treference * energy_residual`, up to reported arithmetic residuals. This helps distinguish an absolute-temperature ledger offset from a new physical energy source.

The returned uniform field differs from exact 300 K by up to **1.230e-8 K**. As an optional **roundoff diagnostic only**, the script evaluates `T_hot - (308.15/300)*(T_uniform - 300)` without replacing or exporting a repaired field/operator. Its largest change from the saved hot field is **1.263e-8 K**. The local hot balance becomes **4.846e-9 W**; its local form discrepancy becomes about **1.493e-6 W K**. The underlying hot nodal minimum remains **181.615257 K**, and the minimum area mean remains **305.216634 K**. The original raw matrices, field files, actual record and all source identities remain unchanged.

Those Kelvin-scale undershoots are not a micro-watt reporting effect. The original group mean is about **2.933 K below** the minimum 308.15 K source state, and the nodal field is over 126 K below it. Raw nonmonotone C/G/R responses and the lack of actual gas-mesh convergence remain. This audit neither repairs them nor establishes actual baffle temperatures or acceptance.

Adopting a cancellation-resistant wall heat ledger, element-difference reaction/energy postprocessor, reference-shifted work calculation, or a uniform-mode change to the solver would require a **fresh explicit implementation and equivalence/known-case evidence**. The audit is not that adoption. A solver change would also need appropriate completed-output verification; any new factor or PDE solve needs separate authorization. A spatial discretization correction would require its own mesh/method evidence. The current frozen actual record retains its original failed checks regardless of these diagnostic comparisons.

## Evidence and use

Run `.venv/bin/python scripts/wo03_gas_energy_diagnostic.py --output <fresh-local-folder>`. It rejects a pre-existing output folder, verifies pinned completed-input hashes, and writes only its new local ledger/record/log. It has no actual solve or transient mode.

The executed run is `wo03-gas-energy-diagnostic-20261031T062034608290Z`. Local outputs are `build/wo03-gas-energy-diagnostic/final/energy-ledger.json` and its wrapper `record.json`; the ledger includes each case's raw/local bulk and prescribed heat, raw/reference-shifted forms, free-node residuals, temperature extrema, source hashes and unchanged thresholds. All ten saved surface means reconstruct exactly from the original fields and area weights. The exact-uniform local heat countercheck is exactly zero. These are ledger reliability diagnostics, not an actual-temperature pass. The primary separately owns its explicitly investigative transient of the failed operator.
