# WO-03 external heat solver: bounded literature and setup assessment

2026-10-31. This is a **documented-capability and local-inventory assessment**,
not an executed Elmer benchmark, a solver selection, or thermal acceptance. The
known-case failure and two used corrective trials remain as recorded in the
[closure plan](wo03-closure-plan.md) and [method decision](wo03-thermal-method-decision.md).
Elmer is a distinct external finite-element implementation to evaluate, not a
third correction to the stopped implementation. A successful fixture is not
evidence that the actual baffle, its mesh, or its temperature limits pass.

## What is documented

- The [Elmer Models Manual, heat equation, pp. 9–22](https://www.nic.funet.fi/index/elmer/doc/ElmerModelsManual.pdf)
  describes transient heat capacity and conduction, including anisotropic solid
  conductivity; prescribed temperature, prescribed flux, and Robin heat transfer
  conditions may vary with position and time. It describes idealized radiation
  and diffuse-gray radiation including mutual surface exchange. Radiation is
  nonlinear; use absolute temperature in fourth-power expressions. Surface
  orientation, opening visibility, temperatures and emissivity must be checked,
  not inferred from a successful solve.
- Upstream's [heat-equation UI definition](https://github.com/ElmerCSC/elmerfem/blob/devel/ElmerGUI/Application/edf/heatequation.xml)
  describes a `Heat Gap` model with radiation and/or convective transfer and a
  **special double boundary mesh**; it assumes direct diffusion across that gap
  is negligible. It is not evidence that this model represents the present
  conductive gas gap, actual openings, or partly bonded contacts. Explicit gas
  domains and solid/bond regions, or independently validated interface bounds,
  remain necessary. Do not double-count adhesive and gas area. Appropriate
  contact-resistance implementation and actual baffle meshing are unverified.
- [Upstream release notes](https://github.com/ElmerCSC/elmerfem/releases) describe
  both legacy and vectorized heat solvers, diffuse-gray radiation and radiosity;
  a release note is not proof any installed build has those features enabled.
  Confirm exact version, solver and options before deriving input syntax.
- Standard finite elements do not automatically preserve physical extrema on
  distorted or strongly anisotropic meshes. [Li and Huang's analysis](https://arxiv.org/abs/1209.5657)
  gives sufficient discrete-maximum-principle conditions involving element
  angles and time steps for a specific linear finite-element/theta-method
  setting; lumping removes one lower-time-step restriction in that analysis.
  These are **conditional results**, not an Elmer-specific guarantee. Check
  mesh angles/quality, extrema, independent field error and heat balance; do
  not clip unphysical values or treat conservative balance as proof of accuracy.

## NASA model-building implications

[NASA's Building Thermal Models](https://ntrs.nasa.gov/citations/20170010293)
distinguishes building, checking, executing and verifying; it calls for checking
material/optical assignments, thickness, connectivity, free edges and duplicate
nodes, and comparing local extrema to design limits. Correlation with measured
hardware is a separate later step. Its geometrical simplifications must preserve
important thermal paths. NASA's [Passive Thermal Control Engineering Guidebook,
section 4.2.4](https://ntrs.nasa.gov/api/citations/20230013900/downloads/NASA%20Thermal%20Control%20Engineering%20Guidebook%20v4.pdf?attachment=true)
explains that contact conductance depends strongly on actual interface conditions
and suggests bounding it when appropriate. Its generic metallic contact values
are not measured adhesive or baffle contact properties. Bound properties, contact,
source and degraded emissivity with defensible case-specific intervals, and retain
local peaks, openings, energy exchange and radiation sampling.

## Local inventory and possible isolated setup

Read-only checks on this arm64 Mac found `ccx` at `/opt/homebrew/bin/ccx` (version
2.23) and `gfortran` at `/opt/homebrew/bin/gfortran` (Homebrew GCC 15.1.0 and
16.2.0 listed). Neither `ElmerSolver` nor `ElmerGrid` was on PATH; standard
`/opt/homebrew/opt/elmer` and `/usr/local/opt/elmer` paths were absent. `cmake`
was not found on the checked PATH or in the checked Homebrew and `/usr/local/bin`
locations; another installation may exist outside those checks. This is not an
exhaustive filesystem search. Docker CLI exists, but daemon state,
images, architecture and available network were not checked. No Elmer download,
installation, build, invocation or thermal run was performed.

### Follow-up: bounded binary availability, 08:24 UTC

From 08:24:00 to 08:24:08 UTC (8 s wall time), checked the official
[26.2.1 release asset list](https://github.com/ElmerCSC/elmerfem/releases/expanded_assets/release-26.2.1)
and [26.1 asset list](https://github.com/ElmerCSC/elmerfem/releases/expanded_assets/release-26.1).
Neither lists a Darwin/arm64-named solver binary: each lists a generic release
archive plus GitHub-generated source archives. For traceability only, GitHub
publishes SHA-256 `729809851d07b0ee8d7aff636bc21745d65b35c94d90027f39958fb759ec1d31`
for `elmerfem-release-26.2.1.tar.gz`; **no bytes were downloaded or hashed locally**,
and this is not evidence of a relocatable Mac binary. An upstream
[Apple Silicon build discussion](https://github.com/ElmerCSC/elmerfem/issues/503)
and [macOS CI workflow](https://github.com/ElmerCSC/elmerfem/blob/devel/.github/workflows/build-macos-homebrew.yaml)
show source builds are possible, not a verified downloadable standalone solver.

Shell `curl -fsSL --max-time 15 https://api.github.com/repos/ElmerCSC/elmerfem/releases/latest`
failed immediately with exit 6, `Could not resolve host: api.github.com`. The
web reader could inspect release asset pages but could not access that API URL.
Therefore no trusted, accessible relocatable Mac solver was identified and no
binary setup, dependency check, solver invocation or model run was completed.
This is an availability result for the checked sources and network context, not
proof that no binary exists elsewhere. The 600 CPU s fixture budget is untouched.

The official [macOS source-build instructions](https://github.com/ElmerCSC/elmerfem/blob/devel/compilation_instructions/macOS.md)
call for GCC and CMake, and explicitly warn that they may be out of date; MPI,
GUI and their dependencies are optional for a serial CLI evaluation. The
[upstream license policy](https://github.com/ElmerCSC/elmerfem/blob/devel/license_texts/ElmerLicensePolicy.md)
distinguishes LGPL core libraries from GPL ElmerGrid and most solver modules;
the exact binary and dependency licenses need recording if redistributed.

Recommended next setup attempt: first check for an already available, trusted,
versioned arm64 CLI bundle or cached container image and its dependencies; if
available, stage it only inside `.cache/elmer-evaluation/`, capture origin,
version, hashes, architecture and dependency identities, and run in a bounded
process. Otherwise a serial source build into that same isolated prefix is a
candidate only if a usable CMake and pinned upstream source are already available.
Allow **at most 10 minutes wall time for the entire setup**, including dependency
and network preflight; stop and report unavailable if it cannot complete. No
system Homebrew install, environment pin or production dependency changes are
implied. A build within that time is **not established** on this machine. Avoid
assuming a particular binary, container or Homebrew formula exists or works.

## Proposed evaluation, subject to the existing budgets

If setup succeeds, record all commands, tool and build identity, input/mesh hashes,
elapsed and CPU time, status and outputs in the isolated evaluation directory.
Use one CPU and the closure plan's ≤120 s/case, ≤10 CPU min alternative-fixture
budget. Start with independent 935:1 affine and curved manufactured-wall cases,
mixed prescribed boundaries and finite-wall response at three refinements;
compare extrema, full field errors, source/reservoir heat and local/global
balances against independent references and unchanged tolerances. Add a small
transient and independently known radiation/contact fixture only if budget
remains; record both positive and negative outcomes. CalculiX 2.23 is the
only other candidate in this assessment, not an assumed independent solution
or demonstrated thermal capability. Its availability alone is not a validation.

No actual geometry run follows from these documents or from a simple fixture
pass. Only a passing known-case packet plus a separately feasible actual-geometry
or justified-bounds preflight can motivate the one permitted new actual trial,
under the closure plan's existing guards and case matrix. Otherwise the method,
credible temperatures and complete package remain unresolved; physical
qualification and flight release remain separate.
