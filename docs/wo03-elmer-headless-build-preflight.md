# Elmer serial/headless source-build preflight

2026-10-31. This is a bounded, primary-source build-feasibility assessment.
No source or build tool was downloaded, no build/install was attempted, and no
Elmer executable or thermal case was run. This does not qualify Elmer or close
any WO-03 gate. The prior [distribution preflight](wo03-elmer-isolated-setup.md)
found no verified relocatable macOS arm64 CLI distribution; this document
examines an isolated source build only.

## Pinned official source and available build switches

The current upstream release is Elmer FEM **26.2.1**, official tag
`release-26.2.1`, release commit prefix `a19504a` (29 April 2026). Zenodo's
official deposit associates that tag with `ElmerCSC/elmerfem-release-26.2.1.zip`,
72.4 MB, MD5 `43810fb941baded3c06ed61019efa7a0`, DOI
`10.5281/zenodo.19888172`. The release archive is identified, but
its bytes have not been verified locally; the MD5 is the depositor's listed hash,
not a strong SHA-256 identity. The GitHub release page separately identifies the tag
and abbreviated commit. [Release page](https://github.com/ElmerCSC/elmerfem/releases),
[Zenodo record](https://zenodo.org/records/19888172), [tagged CMakeLists.txt](https://raw.githubusercontent.com/ElmerCSC/elmerfem/release-26.2.1/CMakeLists.txt).

The tagged root `CMakeLists.txt` sets `WITH_MPI=TRUE` by default, so a serial
build must explicitly pass `-DWITH_MPI=OFF`. `WITH_OpenMP` defaults off;
explicit `-DWITH_OpenMP=OFF` keeps the requested serial configuration clear.
The same file defaults `WITH_ELMERGUI`, `WITH_ELMERPOST`, `WITH_ElmerIce`,
`WITH_XIOS`, `WITH_NETCDF`, `WITH_Mumps`, `WITH_Hypre`, `WITH_CHOLMOD`,
`WITH_Trilinos`, `WITH_FETI4I`, `WITH_CONTRIB`, `WITH_LUA`, `WITH_MMG`,
`WITH_PARMMG`, `WITH_ROCALUTION`, and `WITH_Zoltan` off. ElmerGUI is included
only when `WITH_ELMERGUI` is true; Elmer/Ice explicitly errors without MPI if
enabled. The CMake root also defines `INCLUDE_ELMER_MODULES`, whose empty
default means compile all solver modules. These are real options in this
release, unlike inferred or invented flags.

The tagged macOS instructions explicitly warn they may be out of date. They
describe GCC+CMake, show an MPI-off command but turn OpenMP on, and show GUI
requiring Qt4 and Qwt. They do not document a minimal headless profile or
isolated dependency workflow. [Tagged macOS instructions](https://raw.githubusercontent.com/ElmerCSC/elmerfem/release-26.2.1/compilation_instructions/macOS.md).

Potential command shape for a future, separately declared setup attempt (not
executed or proven sufficient):

```sh
cmake -S "$SOURCE" -B "$BUILD" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DUSE_MACOS_PACKAGE_MANAGER=OFF \
  -DWITH_MPI=OFF -DWITH_OpenMP=OFF \
  -DWITH_ELMERGUI=OFF -DWITH_ELMERPOST=OFF -DWITH_ElmerIce=OFF \
  -DWITH_XIOS=OFF -DWITH_NETCDF=OFF -DWITH_Mumps=OFF -DWITH_Hypre=OFF \
  -DWITH_CHOLMOD=OFF -DWITH_Trilinos=OFF -DWITH_FETI4I=OFF \
  -DWITH_CONTRIB=OFF -DWITH_LUA=OFF -DWITH_MMG=OFF -DWITH_PARMMG=OFF \
  -DWITH_ROCALUTION=OFF -DWITH_Zoltan=OFF
cmake --build "$BUILD" --parallel 1
cmake --install "$BUILD"
```

`USE_MACOS_PACKAGE_MANAGER=OFF` matters: in the tagged CMake root, leaving it
on makes configuration on Darwin search Homebrew/MacPorts and issue a fatal
error if neither is detected. `WITH_UMFPACK` defaults on; the root uses bundled
UMFPACK unless `EXTERNAL_UMFPACK` is set. `fem/src/CMakeLists.txt` shows the
serial `ElmerSolver` executable linking `elmersolver`, and the solver library
links Elmer's MATC/FHUTI/Arpack components, UMFPACK, BLAS and LAPACK. The
source also has an in-tree `ElmerGrid` target linking bundled METIS and `libm`.
Thus Qt, MPI, and external SuiteSparse are not intrinsically needed by the
shown configuration. However the actual compiler/linker/runtime closure for
this machine is **not established**: no CMake configure was run, BLAS/LAPACK
discovery was not tested, and the final Mach-O dependency graph/rpaths were
not inspected. Accelerate exists locally, but its selection and compatibility
with this GCC Fortran toolchain are unverified. The CMake root contains only
commented hints around Accelerate, not a verified configuration recipe.

## Isolated CMake and 600-second setup constraint

No `cmake` executable was found on the checked PATH. A local read-only check
found Apple clang 21.0.0 targeting arm64, Homebrew GNU Fortran 16.2.0, the
Command Line Tools SDK, and `/System/Library/Frameworks/Accelerate.framework`.
The official CMake download page offers a macOS universal binary archive, so a
future task-scoped cache could unpack a versioned CMake archive without
changing Homebrew/project dependencies. For a reproducible attempt, pin one
exact CMake release, stage archive and official SHA-256 file together in the
private cache, verify hash before unpacking, and add its `bin` directory only
to that command's `PATH`. Official CMake downloads: [cmake.org](https://cmake.org/download/)
and its linked [release/hash assets](https://github.com/Kitware/CMake/releases).

The one permitted read-only network preflight to the official CMake GitHub
release archive failed with DNS resolution error `Could not resolve host:
github.com`. The earlier Elmer distribution preflight also recorded GitHub
DNS failure. No retries or host workarounds were made. Therefore neither the
official source nor an isolated CMake archive is presently available from the
checked network path. Do not start the setup timer with repeated network
attempts.

The tagged source archive alone is 72.4 MB. No upstream evidence located in
this bounded review gives a one-CPU macOS build duration. Configuration plus
compiling the broad default module set and libraries is not responsibly
estimable as fitting within the **600-second total setup cap**; one-CPU
completion is uncertain and may exceed it. It is plausible to reduce compile
work by using the documented source selection variable
`INCLUDE_ELMER_MODULES`, but the exact module list and its transitive
dependencies for HeatSolver plus required infrastructure were not traced, so
do not apply an unverified reduced build. Current outcome: an isolated serial
build is technically plausible from the tagged source, but is **not feasible
to initiate now** due unavailable CMake/source retrieval, and ≤600 s completion
is unproven. If the primary later considers one setup packet, it should have
one source/CMake acquisition-and-verify window and a hard 600 s total wall/CPU
guard with no fallback install or repeated download attempts.

## Solver/output fit remains unverified

Elmer's existing [Models Manual](https://www.nic.funet.fi/index/elmer/doc/ElmerModelsManual.pdf)
documents spatially/time-varying prescribed heat flux and Robin heat transfer,
and idealized/diffuse-gray radiation (see the heat-equation chapter, pp. 9–22
as previously located in the WO-03 literature review). This makes the model
class relevant to the continuum problem; it does not prove the exact
continuously varying quadratic `Tbulk` and film function can be represented
with the intended interpolation/input syntax or that contact/gap geometry is
correct. Piecewise-constant boundary values are numerical approximations to
the same continuum problem only when their input error is quantified and
controlled; no such bound is established here.

Upstream release notes document VTU result output and report single-precision
support for ElmerGrid's `sbin` mesh format, but that mesh feature does not
establish result-field precision. The reviewed source/manual evidence did not
settle the tagged ResultOutputSolver's default scalar precision or confirm the
exact `Single Precision` option behavior for this tagged build. Consequently
VTU is a documented output format, but its precision is **unresolved here**;
do not use it as proof of the known-case field tolerance. A future declared
solver packet would need a tiny file-level precision diagnostic plus the
unchanged known-answer criteria before treating output as adequate. The thermal
boundary models and radiation are documented capabilities only, not executed
or qualified behavior.

## Decision table

| Candidate path | Officially documented | Local availability | Same physical model? | Current status |
|---|---|---|---|---|
| Elmer 26.2.1 serial CLI source build | Exact tag; root CMake switches for MPI, OpenMP, GUI and optional packages; bundled UMFPACK/METIS targets; macOS GCC+CMake instructions | gfortran/clang/SDK/Accelerate present; no CMake; one official archive request failed DNS | Potentially; exact continuous Robin input and radiation/gap representation still need a controlled case | No build. Retrieval unavailable; dependency closure and ≤600 s not demonstrated |
| Elmer VTU output for precision-limited known answer | VTU output exists; tagged precision contract not established in this review | No binary | Output format could carry required values only if exact writer precision passes unchanged tolerances | Unresolved; requires file-level precision check |
| Spatially varying Robin/radiation models | Elmer Models Manual documents spatial/time-dependent Robin/flux and idealized/diffuse-gray radiation | No binary | Model class appears relevant; exact quadratic ambient/film specification and geometry/contact remain unverified | Literature capability only; no execution or qualification |

This assessment gives the primary agent a bounded basis to decide whether to
declare one future setup attempt. It does not itself authorize or initiate that
attempt, change solver selection, or relax any acceptance criterion.

## Later exact retrieval identity

The primary verified annotated tag object `38fbce9fa264cb4b6f740cc045f1e8fbb876e06e`
peels to full commit `a19504ac53ec222e3355e182b08f2ff280c2203a` through the
[official tag API](https://api.github.com/repos/ElmerCSC/elmerfem/git/tags/38fbce9fa264cb4b6f740cc045f1e8fbb876e06e).
CMake 3.31.8 universal archive has an official release SHA-256, recorded in the
[download-only handoff](wo03-elmer-download-handoff.md). Neither archive has been
retrieved by the agent, and no setup/build/solver attempt has begun.
