# WO-03 Elmer structural-module capability audit

**Historical source-only assessment.** The later isolated module build and two known-answer structural cases are recorded in the [current decision](wo03-structural-solver-decision.md). The original installed prefix remains unchanged; the table below describes the pre-build snapshot.

**Result: source capability exists; local build and reaction qualification remain unavailable.** The pinned Elmer source has a `StressSolve` module implementing the `StressSolver` linear elasticity procedure. The already configured setup-v1 build did not include or build that module: its CMake module allowlist contains only `HeatSolve`, `HeatSolveVec`, `FluxSolver`, `ResultOutputSolve`, and `SaveData`, and there is no `StressSolve` target or installed `StressSolve.dylib`. Adding the target requires a CMake reconfiguration or a separately generated build graph; neither was performed. A one-file module build looks plausible within 90 seconds by source/build shape, but the compiler time and runtime module loading were not measured. Do not treat this as available to a native case without a separate bounded declaration.

## Pinned source and build facts

The source archive is ElmerFEM commit `a19504ac53ec222e3355e182b08f2ff280c2203a`, SHA-256 `1451e82f05b9661d82e1ebbf6e90ac373fc1b19482eef3889334a6df5ff0144a`. The setup record identifies Elmer 26.2, CMake 3.31.8 and `/opt/homebrew/bin/gfortran`. CMake configured a Release build with one job, MPI and OpenMP off, and this `INCLUDE_ELMER_MODULES` allowlist:

```text
HeatSolve;HeatSolveVec;FluxSolver;ResultOutputSolve;SaveData
```

The source module CMake macro turns each selected module into a shared library linked to `elmersolver` and installs it under `share/elmersolver/lib`. `StressSolve.F90` is one module source file; the procedure entry is `StressSolve StressSolver`. Thus the prospective target name is `StressSolve`, and it would link against the already built `elmersolver` shared library. The current generated makefiles contain no `StressSolve` target; a `cmake --build ... --target StressSolve` cannot use this unchanged build graph.

The earlier package setup used 489.423 seconds of a 600-second setup cap, leaving 110.577 seconds. Its CMake configure step took 6.646 seconds wall and 4.397 seconds CPU; the full build took 150.761 seconds wall and 144.047 seconds CPU. The one-module incremental compile and load time are unknown. It is computationally plausible that an isolated one-source module build fits a 90-second case cap, but this cannot be promised from the saved full-build timing. The setup reservation is tight: a fresh configuration consumed 6.646 seconds, leaving little of the stated 10-second setup reserve for differences. Any attempt would need its own cap and a stop-before-prefix-mutation policy. The current target absence prevents calling the module build-ready.

## Structural outputs supported by the source

The SIF procedure name is `StressSolve StressSolver`; the `StressSolve` initialization sets a `Displacement` variable with one degree of freedom per model dimension. Internally the source declares displacement, stiffness, force and stress arrays as `REAL(KIND=dp)`. Stress computation is optional through solver parameters such as `Calculate Stresses`; this describes code paths, not a completed structural analysis.

The existing `ResultOutputSolve` module supports VTU point data. It emits `Float64` metadata and values when `Single Precision` is false; `Single Precision=True` selects `Float32`. A VTU request can therefore write the displacement field at double precision after `StressSolve` is available. No numeric rounding test was made for this new field or route.

The source also defines a generic `Calculate Loads` pathway. For an assembled solve it computes a residual from the matrix times the solution and subtracts the right-hand-side, then can store the nodal values under the solved variable’s `Loads` name. `Calculate Boundary Fluxes=True` enables per-boundary sums of these residual values in the simulation scalars; the output is labeled `Displacement <component> Flux over BC <id>`. The implementation can warn if boundary DOFs are shared and only handles nodal values for the stated boundary-sum path. These source names do not establish that the sum is a verified physical support-reaction result for a G80 model: boundary membership, sign, constraints, load terms, and force/moment balance still require a known-answer case. The source does not attach SI units; forces inherit the user’s consistent unit system.

`SaveScalars` is an existing module that writes scalar simulation results as ASCII. A possible SIF pattern would use the `StressSolve StressSolver` primary procedure, a `ResultOutputSolve ResultOutputSolver` field writer requesting `Displacement` (and stress when enabled), `Calculate Boundary Fluxes=True` on the structural solver, and `SaveData SaveScalars` for `res: Displacement ... Flux over BC ...`. This is a source-based candidate pattern only; it has not been checked against a structural SIF example, run, or compared to an analytical force-reaction answer. I did not find a local Elmer Models Manual to verify it independently.

## Feasibility and limits

| Question | Evidence | Status |
| --- | --- | --- |
| Does the pinned source have a structural elasticity solver? | `fem/src/modules/StressSolve.F90`; `MainUtils.F90` maps `stress analysis` to `StressSolve StressSolver`. | Source verified. |
| Does the current local build include it? | `CMakeCache.txt` allowlist has five thermal/output modules; generated targets and installed library omit `StressSolve`. | No. |
| Is Float64 displacement output available through existing code? | `ResultOutputSolve/VtuOutputSolver.F90` selects 64-bit metadata unless `Single Precision` is true. | Source path; not tested for StressSolve. |
| Is there native boundary load output? | `SolverUtils.F90` computes residual loads and per-BC sums; fields are named “Flux”. | Source pathway; reaction semantics and equilibrium unverified. |
| Can the target be loaded without changing the installed isolated prefix? | The prospective module is a shared library depending on `elmersolver`; current loader path and staged-library override were not verified. | Unknown. |
| Can it fit the remaining 90-second compile/load cap? | Single module source and prior configure timing; no incremental target timing. | Plausible, not established. |

This capability inspection does not qualify the solver, prove reaction semantics, change prior Elmer thermal results, authorize structural input generation, or authorize an Elmer build or solve. The next decision belongs to the primary agent.
