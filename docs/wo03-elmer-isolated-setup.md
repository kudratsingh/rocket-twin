# Elmer macOS arm64 distribution preflight

2026-10-31. Research only: **no trusted, verified, relocatable arm64 Elmer CLI
package has been identified for this machine**. No archive, dependency or solver
was downloaded, installed, built or run. Both prior 600 CPU-second packets are
closed; any subsequent execution requires a newly declared packet. No tool is
qualified for the actual baffle by this research.

## Distribution evidence

- The [official Elmer repository](https://github.com/ElmerCSC/elmerfem) links
  Windows/WSL/VM distributions and macOS source-build instructions. Its
  [26.2.1 release assets](https://github.com/ElmerCSC/elmerfem/releases/expanded_assets/release-26.2.1)
  identify no macOS arm64 CLI binary. Upstream [macOS CI and discussion](https://github.com/ElmerCSC/elmerfem/issues/503)
  provide evidence of native builds, not a verified downloadable, relocatable
  archive or full runtime dependency closure.
- A search of official conda-forge and Anaconda sources did not identify an
  Elmer FEM solver feedstock or osx-arm64 binary. The specific
  [elmerfem-feedstock URL](https://github.com/conda-forge/elmerfem-feedstock)
  returned 404 in the web reader; the Anaconda package API was inaccessible to
  it. This is not an exhaustive proof that no package under another name exists.
  No exact conda version, build, package hash, runtime dependencies or size can
  be responsibly specified; do not invent an `elmerfem` conda install command.
- [MacPorts' Elmer port](https://ports.macports.org/port/elmerfem/details/)
  identifies version **2024.11.29**, revision **1**, upstream source commit
  `394d98700a395d5fbcc4bc47a8f186252f41c13f`, and license GPL-2. Its
  [Portfile](https://github.com/macports/macports-ports/blob/master/science/elmerfem/Portfile)
  gives a source archive SHA-256 of
  `5bda90a60965bbe12621729548c07d8e046b90ac4c998c8fa3d6d60eb800b2d0`,
  size 70,567,034 bytes; **these are source-archive metadata, not binary
  identity**. The port health page reports arm64 platform file inventories,
  but the web reader could not inspect a corresponding binary archive, exact
  build, contents, hash, or the dependency closure. Such a build listing does
  not prove an accessible archive, relocatability or compatibility with this OS.
  The documented standard install is `sudo port install elmerfem` and is not
  an isolated prefix command; it must not be used for this preflight.

MacPorts' displayed direct library dependencies are OpenBLAS, SuiteSparse AMD,
CAMD, CCOLAMD, CHOLMOD, COLAMD and UMFPACK, libgcc, qt5-qtbase, qt5-qtscript,
qt5-qtsvg, qt5-qttools and qwt-qt5. It lists clang-18, CMake, gcc15 and
pkgconfig as build dependencies. These are port-level dependencies, not an
inspected CLI dynamic-library closure; transitive dependencies, variants,
MacPorts installation prefix and Mach-O load paths still require inspection.
Elmer's [license policy](https://github.com/ElmerCSC/elmerfem/blob/devel/license_texts/ElmerLicensePolicy.md)
distinguishes LGPL core libraries from GPL ElmerGrid and most solver modules;
verify component and dependency licenses for any actual redistribution.

## Feasible next step and stop conditions

The checked machine reports `arm64`, Darwin `27.2.0`, macOS `27.2`; `port`,
`conda`, `mamba`, and `micromamba` were not on the checked PATH. A credible
isolated plan needs an exact trusted binary and signed/hash-verifiable package
metadata, compatible platform/build, all transitive runtime archives and sizes,
and a method for handling any embedded `/opt/local` paths without modifying the
shared installation. The MacPorts archive listing was inaccessible to the web
reader; conda-forge package/API identity was not established. Consequently,
exact isolated-prefix installation commands, download size and completion within
a setup time cap are **unknown**, not demonstrated. A generic conda prefix flag
or an unchecked MacPorts archive extraction does not solve these missing facts.

If trustworthy metadata becomes available, first do a read-only package and
dependency inventory, verify architecture, signature/hash and executable paths,
calculate total download/extracted sizes, and establish that all install and
cache paths stay under `.cache/elmer-isolated-preflight/`. Only then propose a
specific prefix command and hard wall-time cap. Treat a missing binary, unresolved
load path or unavailable dependency as a stop, and do not fall back to a shared
install or source build. Capture exact identities and all changes. The research
above used no solver CPU time and establishes no known-case or actual-geometry
accuracy.
