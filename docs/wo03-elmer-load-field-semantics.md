# Elmer StressSolve displacement-load field semantics

Read-only source audit of the pinned Elmer source snapshot at
`.cache/elmer-evaluation/setup-v1/elmerfem/elmerfem-a19504ac53ec222e3355e182b08f2ff280c2203a`
(source commit `a19504ac53ec222e3355e182b08f2ff280c2203a`). This note distinguishes
what the source computes from what is inferred for a linear static case. It does
not qualify a bridge or assign acceptance thresholds.

## Source facts

- `StressSolver` assembles bulk terms, finishes bulk assembly, assembles boundary
  terms, finishes boundary assembly, and enforces Dirichlet conditions before
  calling `DefaultSolve` (`fem/src/modules/StressSolve.F90:697-758`). Bulk
  assembly accumulates element force vectors into the global RHS (`fem/src/DefUtils.F90:5527-5549`).
- In the normal bulk-save path, `DefaultFinishBulkAssembly` calls `CopyBulkMatrix`
  to retain `BulkValues` and `BulkRHS` before boundary assembly
  (`fem/src/DefUtils.F90:7299-7325`). `DefaultFinishBoundaryAssembly` calls
  `SetNodalLoads` after the boundary-element assembly and before later contacts/limiters and
  Dirichlet enforcement; `SetPointLoads` adds a
  `Target Nodes` load directly to the ordinary `A%rhs`; it does not add it to
  `BulkRHS` (`fem/src/DefUtils.F90:7384-7397`,
  `fem/src/SolverUtils.F90:8254-8277, 8337-8365`).
- `SetNodalLoads` skips a boundary condition with `Target Nodes` in the earlier
  boundary-tag loop, then handles it in the point-load loop. `Displacement 3 Load`
  maps to the component load name `Displacement 3 Load`; `SetPointLoads` adds the
  supplied values to the selected DOF entries of `b` (`fem/src/SolverUtils.F90:8151-8179, 8254-8277, 8337-8365`).
- `DefaultDirichletBCs` runs after the assembly steps above
  (`fem/src/modules/StressSolve.F90:742-747`). Enforcement zeroes constrained
  matrix rows and replaces their RHS with the prescribed diagonal times the
  Dirichlet value (`fem/src/SolverUtils.F90:9060-9081`). The retained bulk
  snapshot is therefore distinct from the Dirichlet-modified solve matrix.
- After solving, `SolveLinearSystem` selects `BulkMatrix` for `Aaid` when that
  optional matrix is supplied; for the displacement-load variable it calls
  `CalculateLoads(..., UseBulkValues=.TRUE., ...)`
  (`fem/src/SolverUtils.F90:15620-15639`). With `UseBulkValues=.TRUE.`,
  `CalculateLoads` temporarily uses `BulkValues` and `BulkRHS`, computes the
  matrix-vector product, and subtracts that RHS (`fem/src/SolverUtils.F90:14468-14479,
  14481-14490, 14538-14551`); it copies the resulting vector into the named
  loads variable and restores the original matrix-values pointer afterward
  (`fem/src/SolverUtils.F90:14585-14596, 14763-14765`). Thus the saved field is
  **bulk-operator times the solved displacement minus the saved bulk RHS**
  (`K_bulk u - f_bulk`), not raw `K u` and not `K u -` the complete
  applied-load vector.
- A separate `Calculate Residual` call uses the full matrix (`UseBulkValues=.FALSE.`)
  and full RHS, which is a different quantity from `Displacement Loads`
  (`fem/src/SolverUtils.F90:15659-15669`).

## Inference for linear static `TargetNodes` / `Displacement 3 Load`

For the fixture's bulk snapshot and direct target-node force path, equilibrium
implies `K_bulk u - f_bulk = f_target + f_other_boundary + r_support`, with
signs following the solver's assembled RHS convention. The field therefore
contains the target point load and support reaction; the calculation does not
subtract them. At an unconstrained, un-loaded node with no other non-bulk force,
the field is expected to be zero up to solve and output precision. At a loaded
free target node, it is expected to reproduce the applied target nodal force;
the full equilibrium residual after subtracting that force is expected to be
zero there. At fixed nodes it can represent support reaction, but it is not a
support-only reaction field. Body-force terms included in the
bulk assembly are removed through `BulkRHS`; boundary-force contributions
assembled outside that bulk snapshot remain in the result.

The existing known-answer support sums agree with this interpretation: the
uniform surface-traction EQUAL axial support reaction was approximately
`-150.00000000001793 N` and the separately tested direct-nodal SINGLE approximately `-149.99999999990467 N`, against
`+150.0000000000001 N` input; both documented force residuals satisfy the
unchanged `1e-5 N` fixture gate. They also passed their all-node displacement
checks. These observations establish this mapping and force balance for those
fixtures, not for arbitrary mixed loads or the actual bridge
(`docs/wo03-elmer-structural-fixture.md:5-14`,
`docs/wo03-elmer-nodal-fixture.md:3-5`).

## Remaining limit

No source-only result or fixture establishes an independent support-reaction
decomposition when target nodal, distributed boundary, and body loads coexist;
the field algebraically combines non-bulk loads and reactions. The direct-nodal known case
tests target-node loads without that mixed-load decomposition. The actual
bridge still needs its own equilibrated load-vector/force/moment interpretation
and reciprocity evidence, plus the separate required mesh-convergence and
engineering acceptance. This note makes no strength, stiffness, or installed
load-path claim.
