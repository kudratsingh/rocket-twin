# Elmer 26.2.1 I/O and Robin boundary source audit

2026-10-31. Read-only audit of the owner-provided extracted source at
`.cache/elmer-evaluation/setup-v1/elmerfem/elmerfem-a19504ac53ec222e3355e182b08f2ff280c2203a`
(commit `a19504ac53ec222e3355e182b08f2ff280c2203a`, tag `release-26.2.1`). No
solver or test was run. This establishes what this source implements, not
runtime correctness, current packet acceptance, or actual-geometry qualification.

## ResultOutputSolver VTU field precision

In `fem/src/modules/ResultOutputSolve/VtuOutputSolver.F90`, the output routine
reads `Single Precision` (around lines 378–389). True selects `PrecBits=32`
and `KIND(SingleWrk)`; false or absent selects `PrecBits=64` and
`KIND(DoubleWrk)`. The XML data-array `type` uses `PrecBits` (for example, the
nodal field writer around lines 1186–1196), and the buffer writer in
`fem/src/GeneralUtils.F90` (around lines 2688–2728 and 2739–2825) writes the
actual field values as single or double precision accordingly. Therefore the
tagged VTU writer has a real double-precision result path; it is not limited to
float32.

`Binary Output` defaults true when neither it nor `Ascii Output` is specified
(`VtuOutputSolver.F90`, about lines 353–359). For the clearest, auditable
settings, specify:

```sif
  Vtu Format = Logical True
  Binary Output = Logical True
  Single Precision = Logical False
```

This produces appended binary Float64 values. The source's ASCII writer
formats double values with `ES16.7E3` (`GeneralUtils.F90`, about lines
2770–2784); that has fewer printed digits than the binary Float64 path. No
field tolerance is relaxed here. A packet still has to parse and compare the
actual emitted files against the unchanged criteria.

## Spatial Robin function evaluation

This source provides two distinct HeatSolver paths, and they must not be
conflated.

### Classic `HeatSolver` path

The existing `fem/tests/ProfileBCTemperatureRobin/case.sif` (source lines
98–106) is a relevant input example: its `Temperature Profile` is a MATC
function of `Coordinate 1`, with constant `External Temperature` and constant
`Heat Transfer Coefficient`. This proves a spatial MATC boundary value is
accepted in the input language; it does not prove the Robin coefficient or
ambient temperature is evaluated continuously at quadrature points.

Classic `fem/src/modules/HeatSolve.F90` obtains nodal arrays for
`Heat Transfer Coefficient` and `External Temperature` (`AddHeatFluxBC`, about
lines 1539–1548) and combines them node by node as `LOAD(j) += h(j)*Tbulk(j)`.
`DiffuseConvectiveBoundary` in `fem/src/DiffuseConvectiveAnisotropic.F90`
(about lines 647–753) then integrates using the boundary basis, interpolating
the nodal coefficient and the already-multiplied nodal load. This does not
evaluate the analytic product `h(x)*Tbulk(x)` at every integration point. It is
a finite-element boundary approximation from nodal samples. A mesh refinement
study might quantify its error, but source inspection alone does not show that
it meets the unchanged A/B/Bstrong tolerances. Do not describe this classic
path as exact continuous quadratic Robin input.

### Vectorized `HeatSolverVec` path

The pinned source also implements a path that evaluates the Robin values at
each boundary quadrature point. In `HeatSolveVec.F90`, `LocalMatrixBC`
(approximately lines 1060–1080) initializes handles for both boundary
keywords. At each boundary integration point (around lines 1130–1160), it calls
`ListGetElementReal(HeatTrans_h, Basis, Element, ...)` and the corresponding
call for `External Temperature`; it then assembles the Robin matrix and load
using the evaluated coefficient `C` and `C*Text` (around lines 1178–1190).

`fem/src/Lists.F90` defines the relevant semantics. `ListInitElementKeyword`
(around lines 6162–6506) detects the optional `<keyword> At IP` flag. In
`ListGetElementReal` (around lines 6847 onward), ordinary variables are
evaluated at nodes and interpolated with the basis by default. When
`<keyword> At IP = Logical True` is set for a variable/scalar procedure, the
routine instead evaluates its dependencies at the quadrature point. For nodal
coordinate dependencies, it first interpolates coordinate values with the
boundary basis and then evaluates the MATC expression. Thus, for MATC functions
of position, the vectorized path can represent the continuous input at its
actual quadrature points; it does not use a centroid-patched constant.

Minimal boundary-condition pattern, based on this API and the source test's
MATC syntax (illustrative only; not run):

```sif
Boundary Condition 1
  Target Boundaries = <boundary-id>
  Heat Transfer Coefficient = Variable Coordinate 1
    Real MATC "h0 + h1*tx + h2*tx*tx"
  Heat Transfer Coefficient At IP = Logical True
  External Temperature = Variable Coordinate 1
    Real MATC "t0 + t1*tx + t2*tx*tx"
  External Temperature At IP = Logical True
End
```

Use the vectorized solver procedure, e.g. `Procedure = File "HeatSolveVec"
"HeatSolver"`, for these flags to be consumed by its element-value handles.
The pinned `fem/src/modules/CMakeLists.txt` discovers solver modules by source
basename; when `INCLUDE_ELMER_MODULES` is set, `cmake/Modules/AddModules.cmake`
uses it as an inclusion allowlist. A constrained build listing only
`HeatSolve`, `FluxSolver`, `ResultOutputSolve`, and `SaveData` will omit
`HeatSolveVec`; check or add `HeatSolveVec` in the build selection before
relying on the direct-at-IP path.
The ordinary `HeatSolver` path shown above uses nodal `GetReal` arrays and does
not consume these handles. The existing test `ProfileBCTemperatureRobin`
selects classic `HeatSolve`, and therefore is an input-syntax example only. The
source audit did not execute a quadratic Robin case, test boundary orientation,
inspect the run configuration's selected modules, or establish that
`HeatSolveVec` is present in the active binary. Confirm the actually built
module and the generated SIF before any packet relies on this route.

If `Heat Transfer Coefficient At IP` and `External Temperature At IP` are
absent, `ListGetElementReal`'s documented implementation path is nodal
evaluation followed by basis interpolation. This may be an appropriate
finite-element approximation, but it is not the exact continuously varying
quadratic input required for the strong case unless its input/interpolation
error is quantified and shown within tolerance.

## Source evidence and limits

| Behavior | Pinned-source location | Evidence status |
|---|---|---|
| VTU `Single Precision` selects 32 or 64-bit field output | `fem/src/modules/ResultOutputSolve/VtuOutputSolver.F90`, lines ~353–389, 1186–1204; `fem/src/GeneralUtils.F90`, `AscBinWriteInit` and `AscBinRealWrite` | Implemented path verified by read-only source inspection; no file emitted here |
| `Binary Output` default and settings | `VtuOutputSolver.F90`, lines ~353–359 | Implemented path; recommended config makes double path explicit |
| MATC spatial boundary syntax example | `fem/tests/ProfileBCTemperatureRobin/case.sif`, lines 98–106 | Input example exists, but that test uses the classic solver and constant Robin data |
| Classic HeatSolver Robin handling | `fem/src/modules/HeatSolve.F90`, lines ~1539–1548; `fem/src/DiffuseConvectiveAnisotropic.F90`, lines ~647–753 | Source shows nodal `h*Tbulk` assembly then boundary basis integration |
| Direct Gauss-point Robin evaluation | `fem/src/modules/HeatSolveVec.F90`, lines ~1060–1080 and ~1130–1190 | Source shows per-point evaluation/assembly |
| `At IP` switch and MATC/coordinate evaluation | `fem/src/Lists.F90`, `ListInitElementKeyword` around 6162–6506 and `ListGetElementReal` around 6847 onward | Source API; no task-specific quadratic run tested |

The minimal build/dependency list and runtime module availability remain matters
for the active setup packet. None of this document's source findings is a
known-answer pass or solver qualification.

## Native heat loads and boundary flux outputs

The pinned source has native scalar-output paths, but their meanings differ.
They are useful diagnostics once run, not a single interchangeable “film heat”
value.

### `Calculate Loads` and `Temperature Loads`

`MainUtils.F90` (around lines 2340–2380) creates `<Variable> Loads` when
`Calculate Loads = True`; for `Variable = Temperature`, the exact variable
name is **`Temperature Loads`**. `SolverUtils.F90` (around lines 15625–15638)
computes this from the assembled system. Its `CalculateLoads` path forms
`A*T - b` (lines around 14538–14551), so this is a nodal algebraic residual or
reaction load, with the sign of `A*T - b`, not an independent evaluation of
the Robin law.

`Calculate Boundary Fluxes = True` asks generic solver support to sum these
nodal loads by boundary condition and reports simulation entries named
`res: Temperature Flux over BC <index>` (`SolverUtils.F90`, around lines
14599–14693). The code sums each nodal DOF once and warns if a DOF is shared by
multiple boundaries, because the load cannot then be uniquely attributed.
Absent any boundary-level `Calculate Boundary Flux = True` flag, it includes
all boundary conditions; if any such flag exists, only marked BCs are included
(around lines 14619–14630). The selected-boundary key is a logical on the BC.
This is a residual/reaction sum, not an integral of `h(x)(T-Tbulk)` or
`-k grad(T)·n`. It can serve as a boundary reaction/whole-system consistency
diagnostic, but it is not qualified as total Robin film heat. At natural Robin
DOFs the assembled equations already contain the Robin term, so the converged
algebraic residual is expected to be small; it does not separately expose the
film exchange.

`SaveScalars` can report the same nodal variable through `Operator = "boundary
sum"`. The mask is selected with `Mask Name <n> = "some key"` in the
SaveScalars solver and `some key = Logical True` on the desired BC. Its
`BoundaryStatistics` branch checks that mask, sums values over boundary DOFs,
and avoids duplicate hits. A same-source example is
`fem/tests/savescalars_flux/case.sif`, which saves `Temperature Loads` with the
`boundary sum` operator. The source test comment states that these nodal loads
are residual-based loads needed to cause the effect of the boundary
conditions.

Minimal documented-by-source pattern (not executed):

```sif
Solver 1
  Variable = String Temperature
  Calculate Loads = Logical True
  Calculate Boundary Fluxes = Logical True
End

Solver 2
  Equation = SaveScalars
  Procedure = File "SaveData" "SaveScalars"
  Variable 1 = String Temperature Loads
  Operator 1 = String "boundary sum"
  Mask Name 1 = String "film_boundary"
End

Boundary Condition 7
  film_boundary = Logical True
End
```

Here the sum is residual load at that BC's nodes. A shared geometric node
assigned to more than one BC still triggers the generic boundary flux
attribution limitation; a SaveScalars mask cannot make the underlying shared
nodal reaction physically unique.

### `SaveScalars` operator `diffusive flux`

The direct integration operator uses the selected scalar field's spatial
gradient at boundary quadrature points. For temperature, specify
`Coefficient 1 = "Heat Conductivity"` to multiply by the material conductivity;
without a coefficient, the integration tensor is identity and it integrates a
temperature gradient flux, not thermal power. The implementation in
`fem/src/modules/SaveData/SaveScalars.F90` (around lines 2631–2655 and
2756–2778) computes
`flux = n · (K ∇T)` and integrates it over each selected boundary. The
coefficient is read from the material on a selected adjacent parent body;
`Flux Integrate Body` can select which parent when the boundary has two. The
routine does **not** add the Fourier minus sign: conventional outward
conductive heat is `-n · (K ∇T)` for an outward normal. Thus negate the saved
integral if reporting that convention, and retain the orientation/sign in the
record. This is a gradient-based conduction measure, not an evaluation of the
Robin film law.

The operator's boundary mask is a logical BC key matching `Mask Name 1`; the
same loop also accepts `Flux Integrate = Logical True` on the BC. One source
example is `fem/tests/TwelveSolvers2D/case.sif`, which uses
`Variable = Temperature`, `Coefficient = Heat Conductivity`,
`Operator = diffusive flux`. `fem/tests/BoundaryFluxes/case.sif` explains that
`Calculate Boundary Fluxes` instead computes boundary loads from nodal loads
and notes the limitation when nodes are shared. `fem/tests/FluxIntegralBCTemperature/case.sif`
shows `Temperature Loads` with `boundary sum` for a case containing a Robin
boundary and a flux-integral constraint; this demonstrates API use, not that
the nodal load sum is the Robin film exchange.

### What this establishes for a future known case

- `Temperature Loads` and per-BC `Temperature Flux over BC <index>` are
  residual/reaction quantities. Their source convention is `A*T - b`; do not
  relabel them as the signed Robin-film integral.
- `SaveScalars` `diffusive flux` with `Coefficient = Heat Conductivity` gives
  an integrated conduction-gradient term on selected boundary elements. Its
  source formula is `n·(K∇T)`, requiring a sign conversion to report
  Fourier-outward heat. It can be compared with an independently calculated
  Robin exchange only after the selected surface, parent material, normal, and
  sign convention are pinned.
- A direct film integral `∫ h(x) (T(x)-Tbulk(x)) dA` is not named or
  automatically emitted by these mechanisms. It remains unavailable unless
  separately computed with validated field/BC evaluations. No energy balance
  result or local heat-transfer result is claimed by this source audit.

This is a source-verified minimal SIF pattern only. It has not been executed
with the setup-v1 binary or a known-answer case; any later actual execution
requires the primary agent's separately declared packet.
