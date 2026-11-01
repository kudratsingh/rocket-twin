# Elmer classic A comparison: complete, actual geometry unqualified

**Current decision:** all three classic A cases completed after one explicitly
recorded resource-launch replan. Their fields agree with the preserved Vec
fields within 5.4e-12 K, while both implementations fail the unchanged 1e-7 K
exact-field criterion with nonmonotone errors. Changing the procedure library
does not resolve the discrepancy. Native conductive-heat errors pass their
separate reference tolerance; Robin exchange and local/algebraic energy
accounting remain unavailable. Neither implementation is qualified for an
actual-baffle calculation. No further solver or grid attempt follows automatically.

The original nine-result Vec campaign and the failed pre-execution launcher
remain preserved. The sections below retain the chronological preparation and
stop decisions, followed by completed results. See also the independent
[local-error audit](wo03-elmer-local-error-audit.md) and updated
[method decision](wo03-elmer-campaign-decision.md).

## Historical preparation, before execution

A controlled comparison of the existing classic `HeatSolve` and `HeatSolveVec`
implementations was prepared for the three previously solved A known cases.
At this preparation stage no classic solver case had been executed or authorized;
the subsequent explicit authorization and results are recorded below.

The [prepare-only manifest](../build/wo03-elmer-classic-comparison-prepare-v3/manifest.json) verifies that each proposed SIF differs from its corresponding preserved source by exactly one byte-string replacement:

```text
Procedure = File "HeatSolveVec" "HeatSolver"
Procedure = File "HeatSolve" "HeatSolver"
```

The `HeatSolver` entry point, direct UMFPACK configuration, mesh, material, all boundary conditions, native quadrature and Float64 VTU output settings remain unchanged. The wrapper reverses the replacement and requires exact byte equality with the original SIF; it verifies the four original mesh files and the prepared copies by SHA-256. All three original SIFs have SHA-256 `f8ad391758a3787257a658fdd81a9e7d247a98f87f2e6d354a7661485fcd57f8`; their classic copies have SHA-256 `385a65fd2925d2487a9aa6013c6a6738a49bb9a9b3a1ec15787690c8cf750783`.

The original and proposed meshes are the same affine P2 boxes, dimensions 0.0002 × 0.001 × 0.187 m and conductivity 0.04 W/(m·K). Case A prescribes 573.15 K on one face and a 308.15 K bulk with `h=36030.6 W/(m²·K)` on the opposing face; the other faces are insulated. The existing analytic reference and existing Float64 VTU/flux readers are reused. The three already completed Vec fields were re-read from their pinned VTUs and exactly matched the original stored arrays:

| A level | Nodes | Saved Vec maximum nodal error |
| --- | ---: | ---: |
| 2 | 125 | 1.933576334e-5 K |
| 4 | 729 | 1.122233601e-4 K |
| 8 | 4,913 | 3.735985899e-5 K |

All three Vec errors exceed the unchanged **1e-7 K** exact-field threshold. The preflight also verified the source-input hashes, VTK 9.6.2 Float64 reading, and the pinned Elmer runtime artifacts. `ElmerSolver` SHA-256 is `006922a630d1daa404ff1191a39dc33a44aa4b6d0c5bac907f07861db4232d6e`; classic `HeatSolve.dylib` is `4c3089732c61dbc684ba5be8232539a4196155b2253e1d216fa7986812f3b812`, and `HeatSolveVec.dylib` is `61ae7dfbf04f1aa3b8cdec328c7a69f7df99fc9d5ccaf71800673c254c8eba42`. The final 39-source hash ledger includes the new wrapper/config and process supervisor. A strict SIF replacement/rejection check and Ruff/Black passed.

If separately declared by the primary, the proposed packet is **three serial classic A cases**, one per fixed 2/4/8 level, one worker requested, each limited to **120 CPU s and 120 s wall**, with at most **360 native CPU s** and a **600 CPU s** whole-packet ceiling. The wrapper gives the parent a separate 240 CPU s cap, so parent plus the three native-child maxima cannot exceed 600 CPU s. Invalid or changed inputs, solver failure/nonconvergence, malformed/nonfinite output or resource cap stop the packet. Finite field-error failures are recorded individually across these already declared levels; no subsequent grid, quadrature or method tuning follows automatically. A solver exit is not an accuracy pass.

For each completed level the wrapper would compare the full nodal field to the same analytic reference and the saved Vec field. It retains the original **1e-7 K** field tolerance and native conductive-heat comparison **1e-10 W plus 1 ppm** of reference heat. Printed native conductive heat is an indicator; Robin exchange, algebraic/global and local energy balances, and the original raw-C convergence check remain unavailable unless independently verified. No actual baffle, curved gap, transient or radiation case is included, and no engineering acceptance follows.

Three no-solver preparation passes were retained as v1/v2/v3 while the source/tool ledger and packet guard were completed; the final v3 wrapper SHA-256 is `25bce81edb7de24c49d2ba103b6f4a413926932beeaaca4653d745662d990cde`. Their measured child CPU totals were **1.266343 + 1.193090 + 1.230996 = 3.690429 s**, and wall durations **1.651 / 1.388 / 1.464 s**; the final child peak RSS was **208,306,176 bytes**. Those measurements do not claim to include every interactive inspection or simultaneous memory. Setup was bounded below the requested 30 CPU s / 60 s per preparation; no Elmer solve occurred.

## Authorized packet stopped before the first solver

The primary subsequently selected the three-level classic packet with a corrected budget: **30 CPU s setup reservation + 60 CPU s parent hard cap + three 120 CPU s native caps = 450 CPU s** reserved under the 600 CPU s ceiling. This supersedes the earlier proposed 240 CPU s parent cap above. The v3 manifest and its wrapper/config snapshots were preserved. A fresh [v4 prepare-only manifest](../build/wo03-elmer-classic-comparison-prepare-v4/manifest.json) verified all 39 input/tool hashes; its SIF, mesh and Vec-level records were identical to v3 and each SIF still had only the declared procedure-library replacement. The v4 no-solver preparation used **1.268165 CPU s** and **1.644115 s wall**; the four measured preparation passes total **4.958594 CPU s**. The 30 s setup reservation is conservative, not a claim that the full amount was measured.

The authorized execution then **stopped before invoking `ElmerSolver` at A2**. A Unix child inherits its parent's hard CPU limit: the child launcher inherited the new 60 s hard limit and raised `ValueError: not allowed to raise maximum limit` when it tried to set its own hard limit to 120 s. The [stopped record](../build/wo03-elmer-classic-comparison-prepare-v4/record.json), [launcher log](../build/wo03-elmer-classic-comparison-prepare-v4/A/2/solver.log), original Vec campaign and all v3/v4 inputs are preserved. Sources and tool hashes remained unchanged. This is a resource-control failure, **not** a thermal accuracy result or evidence that classic `HeatSolve` ran. No classic A2/A4/A8 field or heat result existed at that stop; the separately authorized replan below produced them.

The failed launcher used **0.023370 CPU s**, the supervising parent used **0.032825 CPU s**, and its elapsed wall was **0.059175 s**; these are separate measured values. The predeclared stop rule was followed: no retry, later level, altered cap or alternative method was run. A future separately selected approach could use a child CPU cap no greater than its inherited 60 s limit, or redesign supervision so independently bounded sibling processes can retain 120 s each. Either requires an explicit new packet decision; neither changes the existing Vec failures, unavailable balances, original criteria or actual-baffle qualification status.

The original stopped record's `solver_invoked: true` flag was set **before** launching the Python limit wrapper. It therefore marks an attempted solver launch, not an observed `ElmerSolver` execution. The launcher traceback proves the limit-setting call failed before `os.execv`; a separate [stop interpretation](../build/wo03-elmer-classic-comparison-prepare-v4/stop-interpretation.json) records this distinction without altering the original record.

## One inherited-cap replan: three classic cases completed

The primary authorized one resource-launch-only replan after the preserved v4 launcher failure. The child CPU hard cap was changed to **60 s**, no greater than its inherited 60 s parent hard cap; per-case wall remained 120 s. The conservative allocation was **30 s setup + 60 s parent + three × 60 s native = 270 CPU s**, under the unchanged 600 s packet ceiling. A tiny owned-child test first inherited and explicitly set `(60, 60)`, then successfully executed a separate Python process that reported those same limits. This was a control test, not an Elmer run. Its parent used 0.061762 CPU s and child 0.040688 CPU s.

The v4 source/config snapshots and stopped record remain intact. All 39 pinned v4 source/tool entries were rechecked; only the wrapper/config changed for the declared resource caps and the distinction between *launch attempted* and *Elmer execution observed*. The [v5 prepare manifest](../build/wo03-elmer-classic-comparison-prepare-v5/manifest.json) has identical per-level SIF, mesh and saved Vec hashes to v4. The three authorized classic levels then completed exactly once; logs show the `HeatSolve HeatSolver` procedure and UMFPACK. The [execution record](../build/wo03-elmer-classic-comparison-prepare-v5/record.json) has SHA-256 `035bf9e2028d7581f2e2d2b0ffb4413c4705c55ee548377ca78217c21951503a`; source/tool before-and-after hashes match. No Vec run, changed physics, actual-baffle case or further tuning occurred.

| A level | Classic max nodal error (K) | Classic vs saved Vec max absolute field difference (K) | Exact-field 1e-7 K |
| --- | ---: | ---: | --- |
| 2 | 1.933576351e-5 | 7.39e-13 | Fail |
| 4 | 1.122233601e-4 | 2.50e-12 | Fail |
| 8 | 3.735985797e-5 | 5.34e-12 | Fail |

All outputs were Float64, read with VTK 9.6.2 and its thread caps set to one. The classic nodal temperature ranges were 309.612851205–573.1500000000001 K, 309.612847777–573.1500000000002 K, and 309.612845518–573.1500000000002 K, respectively; no field values were clipped. The exact-field errors are nonmonotone. Raw shared-node changes from level 2→4 and 4→8 were **1.86117083e-5 / 1.04307465e-4 K** for classic and **1.86117069e-5 / 1.04307467e-4 K** for Vec. These are measured field differences, not a passed convergence criterion. The conditional affine-P2 continuous-error bound straddles the boundary envelope at every level, so the continuous envelope status is unavailable rather than a pass or a demonstrated violation.

Classic native outward-conductive-heat reference errors were **1.010677e-6 / 2.846940e-6 / 2.956771e-6 W**, each below the unchanged **9.856389e-6 W** A reference tolerance (1e-10 W plus 1 ppm). Their sums over six outward conductive boundaries were **−2.032116e-6 / −3.387118e-6 / −4.225578e-6 W**. These are conductive-flux indicators, not independently verified Robin exchange, algebraic/global or local energy balances; those checks and raw-C convergence remain unavailable.

The packet parent used **1.212668 CPU s** and the three native children together **0.739856 CPU s**. The sampled child RSS maxima were approximately 9.85 / 9.78 / 46.33 MB; the separate parent peak was **208,846,848 bytes**. These are separate maxima, not simultaneous total memory. The five measured no-solver preparation passes used 6.247214 CPU s; adding the recorded earlier failed launcher/parent and smoke child/parent gives approximately **6.405859 CPU s** of tracked setup, with other interactive setup not separately measured and the 30 s reservation retained. One worker was requested and Elmer reported one thread per task; OS affinity was not established.

**Decision:** the classic and Vec runs are separate, successfully executed tool paths, but agree with each other to about 5.4e-12 K while both fail the A exact-field criterion. This comparison does not identify the underlying cause or qualify either implementation for the actual baffle. It supports no automatic additional solver, grid or quadrature attempt. The closed-form screens and the mechanical package retain their previously stated, separate evidence limits.

The classic solver logs contain repeated nonfatal `Requested property: [Density], not found` warnings: **48 / 384 / 3,072** such property lines for A2/A4/A8; the saved Vec logs contain none. The shared SIF is steady and specifies conductivity without a density, body-force, or flow input. In the pinned classic source, element assembly requests density and uses it in heat-capacity and potentially other source/flow paths. The present inspection did **not** prove every density-dependent path inactive or establish the warning's impact. This warning is part of the classic-run evidence and a further limit on interpretation; it is not a basis to change the original inputs, ignore the failed exact-field check, or infer a cause. No solver retry or input modification followed.

## Published compact evidence

[Decision packet](../runs/wo03-elmer-classic-decision-20261101T093000Z/record.json) retains the source-pinned stopped and completed records, native inputs, resource ledgers and read-only audit. Nodal arrays and generated meshes/fields remain local, with raw-file hashes retained.
