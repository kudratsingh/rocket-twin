# Native Elmer quadrature correction (read-only audit)

**Scope:** source/runtime reconciliation only. No solver, mesh, CAD, or source
files were changed or rerun. This note supplements the frozen native comparison;
it does not revise its as-run records.

## Finding

The comparison report's “27-point Duffy” description matches the recorded
`HeatSolveVec` runtime diagnostic for A/2: `HeatSolver: Number of 1st
integration points: 27` in
`build/wo03-elmer-thermal-comparison-io-replan/A/2/solver.log` (line 160).
For a standard tetrahedron, the pinned source's 27-point selection is the
three-by-three-by-three tensor Gauss rule mapped to the simplex by the Duffy
transformation in `GaussPointsTetra` (`Integration.F90`, source lines 1871–1947;
`GaussPointsBrick` tensor-product construction lines 2478–2518). Thus the
actual reported count is not a four-point rule.

The old “tetra510 default 4” statement is incorrect. `elements.def` defines
the standard 10-node tetrahedron (code 510) with `Gauss Points 27 64` (lines
409–441): 27 points for the first rule, 64 for the second. `GaussPointsAdapt`
can route through an explicit integration rule, an explicit point count, or
relative order; absent those, it calls
`GaussPoints(Element, PReferenceElement=pRef)` (`SolverUtils.F90`, lines
11756–12121). `HeatSolveVec.LocalMatrixVec` calls `GaussPointsAdapt(Element)`
(`modules/HeatSolveVec.F90`, line 646). The recorded SIF has no integration
point/order settings. The no-options path uses the first element rule, so the
27-point runtime diagnostic agrees with the literal code 510 element default.
The 4-point `GaussPointsTetra(4)` coordinates and equal weights are a separate
degree-2-exact standard tetra rule, but they are not the code 510 default and
are not evidence that this A/2 bulk assembly used four points.

The quadrature moments were independently recomputed for the runtime-indicated
27-point standard-tetra rule using the source mapping and 3-point
Gauss–Legendre tensor values. For each monomial `u^a v^b w^c`, all
`a+b+c <= 2` were compared to the unit-simplex integral
`a! b! c! / (a+b+c+3)!`. The largest absolute difference was
`2.7755575615628914e-17` (the constant moment, numerical summation of 1/6);
all nonconstant moments differed by at most `6.94e-18`. This verifies the
degree-2 moment property of that mapping calculation, not general solver
accuracy or the cause of the observed A error.

The boundary calculation is a separate path: `HeatSolveVec.LocalMatrixBC`
calls `GaussPoints(Element)` (source line 1109), not `GaussPointsAdapt`.
Consequently the bulk 27-point diagnostic does not prove the surface rule.
Code 306's six-point triangle rule and its moments remain as separately
documented; no evidence in this audit changes the Robin-wall quadrature claim.

## Provenance and evidence limits

- Pinned Elmer source: release `26.2.1`, commit
  `a19504ac53ec222e3355e182b08f2ff280c2203a`, extracted under
  `.cache/elmer-evaluation/setup-v1/elmerfem/elmerfem-a19504ac53ec222e3355e182b08f2ff280c2203a`.
- `fem/src/Integration.F90` SHA-256:
  `822675e40b4bfceda85e5cec85ebdf3fc22545bddbc63dd87195708f5970ea95`.
- `fem/src/SolverUtils.F90` SHA-256:
  `f264e7e4f7e1720614571c2f82e50c245d62eb7e27b123f449a31b8eaa093d56`.
- `fem/src/modules/HeatSolveVec.F90` SHA-256:
  `f745a711669aa9f7aeeb44d2a3f16ec1ba312958ee93311901f7712f079ff1a6`.
- Runtime count is an existing recorded log observation, not a rerun. The
  moment result is a post-hoc calculation from the pinned source mapping and
  standard three-point Gauss–Legendre constants. It is not an independent
  readback of Elmer's in-memory quadrature arrays.
- Do not rewrite the frozen report or reinterpret raw outputs based on this
  correction. Primary owns any acceptance or postprocessing decision.
