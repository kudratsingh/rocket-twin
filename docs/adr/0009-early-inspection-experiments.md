# ADR-0009: Early design inspection and experiment preview

Date: 2026-10-30. Status: accepted by explicit owner instruction.

Expanded WO-03 remains open. The owner needs to inspect and understand the current
rocket rather than wait for all structural, thermal, recovery and fit corrections.
The owner explicitly authorized limited WO-04 and WO-05 implementation in parallel.

Deliver a running read-only inspection app first: actual CAD-derived geometry,
configuration selection, linked part selection, visibility/isolation, exploded
view, understandable part information and current backend-derived vehicle values.
Show preliminary status and unresolved findings. Explain abbreviations, units and
why each quantity matters. Active designs and candidate studies remain distinct.
Add compatible recorded stress, displacement and thermal displays as a second
increment; missing or incompatible data is unavailable, never a zero/pass.

The early experiment subset runs supported complete configurations through the
existing Python/JAX simulator, with steady-wind controls and supported gusts,
separate saved runs, progress/errors, exact configuration/model identity, actual
position/orientation replay, synchronized graphs and two-run comparison. No
browser flight physics, arbitrary motor swaps or active PID/RL controller is
introduced. Unsupported finless unguided simulations are rejected explicitly.

This exception permits starting these subsets; it does not accept WO-03 or mark
full WO-04/05 complete. Their remaining prerequisites and benchmarks still apply.
Engineering acceptance, owner physical work, purchases, paid runs, WO-10 firmware/
abort review and flight release retain their existing gates. Continue focused PRs
and merge only after required checks pass. No routine owner PR review is added.
