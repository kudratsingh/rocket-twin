# Elmer A affine mixed-wall error: source diagnostic

2026-10-31. Read-only review of the completed `build/wo03-elmer-thermal-comparison-io-replan`
packet and pinned Elmer 26.2.1 source. No input, source, build, or result was
modified; no run was made. This narrows the next known-answer diagnostic. It
does **not** identify a proven cause, qualify a solver, or authorize another
solver packet.

## Observed pattern

The packet used P2 tetrahedra, native Float64 VTU fields, `HeatSolveVec`,
UMFPACK, and an affine known case. The A maximum nodal errors at refinements
2/4/8 were `1.9336e-5`, `1.1222e-4`, and `3.7360e-5 K`; all fail the unchanged
`1e-7 K` criterion and are nonmonotone. The source packet metadata identifies
the output field as `float64`. A hot-plane Dirichlet value is reproduced to
about `2.3e-13 K`, while the largest error occurs away from that plane, so the
known error is not explained by VTU float32 rounding or the Dirichlet value
setter. The solver log shows Elmer 26.2, direct UMFPACK, and exit success, but
does not report a field-error estimate, matrix condition estimate, or a
residual that bounds temperature error. The configured `1e-12` linear
convergence tolerance is not itself evidence of a `1e-7 K` solution error.

In contrast, B_strong passes the field criterion with reported errors about
`6.0e-10`, `7.3e-10`, and `1.55e-9 K`, and native boundary heat is around
`1e-11 W`. That contrast is real evidence that this executable/source/output
path can return sub-`1e-7 K` field agreement on the tested B_strong inputs. It
does not explain A, nor prove its model setup or convergence behavior is
equivalent.

## What source evidence does and does not implicate

- A's SIF sets a constant 573.15 K hot plane and one constant Robin boundary
  (`h=36030.6 W/m²K`, `Tbulk=308.15 K`), with the other four side boundaries
  natural. `HeatSolveVec` processes Robin terms in `LocalMatrixBC`: it selects
  `GaussPoints(Element)`, reads the coefficient and ambient temperature at
  each point, and adds `h φᵢφⱼ` to the local matrix and `h Tbulk φᵢ` to the
  load (`fem/src/modules/HeatSolveVec.F90`, about lines 1107–1160 and
  1196–1203). The source handles mixed Robin and Dirichlet contributions in
  the same solve; the source-only review does not identify a specific missing
  mixed-boundary term.
- The generated boundary faces are quadratic triangle code 306 and volume
  cells are quadratic tetrahedron code 510. The tagged `elements.def` gives
  6 default face points for triangle306 and 27 default volume points for
  tetra510. The 4/11/1 definition belongs to the preceding element block, not
  code 510. The existing A/2 log confirms 27 first integration points. The
  packet's independent rule check measured maximum monomial
  moment errors of `5.0e-16` through triangle degree 4 and `2.8e-17` through
  tetra degree 2. For constant A Robin data, the affine-face Robin matrix
  integrand is a product of P2 shape functions (degree 4); the load integrand
  is degree 2. These facts do not point to an obvious default-rule order
  deficit for this affine constant-Robin case. They do not prove every
  implementation detail or explain the observed error.
- Classic `HeatSolver` uses a different Robin assembly route: it loads nodal
  arrays, forms nodal `h*Tbulk`, then integrates interpolants via
  `DiffuseConvectiveBoundary` (`fem/src/modules/HeatSolve.F90`, about
  1539–1548 and 1602–1605; `fem/src/DiffuseConvectiveAnisotropic.F90`,
  713–750). This is a concrete independent implementation path available in
  the same source tree. It is not yet compared with the A result.
- The preflight's separate default-three-point analytic-load quadrature
  calculation was explicitly annotated as an assembly-load estimate, not a
  solved-temperature error or reservoir-heat error. It cannot be used as the
  explanation for A's nodal error.

No evidence here distinguishes between an A-specific model/reference issue,
the Vec-vs-classic boundary assembly path, linear conditioning/error
amplification, or another implementation detail. These remain possible
questions, not conclusions.

## One discriminating follow-up

If the primary agent later declares another known-answer packet, compare **one
otherwise byte-identical A input** through classic `Procedure = File
"HeatSolve" "HeatSolver"`, keeping mesh, material, all six BCs, direct UMFPACK,
and Float64 output fixed. Use the same refinement(s) chosen by the primary's
packet budget, and compare the full nodal field to the same analytic A
reference—not just the hot-plane nodes or a scalar flux.

This single solver-path comparison isolates the two distinct Robin assembly
implementations while holding the physical conditions and direct solver
constant. Similar A errors on both paths would move the investigation toward
shared model/reference or matrix-sensitivity questions; materially different
errors would localize the discrepancy to solver-path assembly or its
interaction with the shared system. Neither outcome alone qualifies Elmer.
Do not change quadrature or tolerances as part of that diagnostic. No next
execution is authorized by this document.
