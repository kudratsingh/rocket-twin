# Isolated Elmer setup — completed, not thermal qualification

The owner downloaded the two archives using the recorded download-only helper.
The agent verified their fingerprints, checked archive paths/size guards and
extracted them under `.cache/elmer-evaluation/setup-v1/`. The official CMake
3.31.8 archive SHA-256 is
`d1449f969c54d5c00886d5b643340d493dfb3c81cb39ee29b35453395c11ebf7`.
The commit-addressed Elmer archive SHA-256 is
`1451e82f05b9661d82e1ebbf6e90ac373fc1b19482eef3889334a6df5ff0144a`,
from official commit `a19504ac53ec222e3355e182b08f2ff280c2203a`.
The latter is an observed fingerprint, not an independently published checksum.

No global install or project pin changed. The local prefix is
`.cache/elmer-evaluation/setup-v1/prefix`. CMake used existing Apple clang,
Homebrew gfortran, SDK Accelerate BLAS/LAPACK and bundled UMFPACK/ARPACK/METIS.
MPI, OpenMP, GUI and other listed optional packages were disabled; compilation
used one build job and explicit one-thread library environment values.

The first selected modules were HeatSolve, FluxSolver, ResultOutputSolve and
SaveData. Source inspection identified the HeatSolveVec integration-point
boundary path, so one documented addendum added that module within the **same**
600-second inclusive ceiling, without a failed-build retry or source patch.
Release compilation used explicit O1 flags, not a project dependency upgrade.

| Stage | Wall s | Child CPU s |
| --- | ---: | ---: |
| CMake version | 1.217 | 0.0168 |
| Initial configure | 6.646 | 4.3970 |
| Initial build | 150.761 | 144.0466 |
| Initial local install | 0.413 | 0.1958 |
| Vector-module configure | 1.649 | 1.3954 |
| Vector-module build | 58.443 | 55.3707 |
| Updated local install | 0.255 | 0.1831 |

The final runtime/version/library check closed setup at **489.423 s including
107.013 s download**, below 600 s. Peak cumulative child RSS reached about
489.7 MB; this is a child maximum, not measured simultaneous total memory.
One build job was requested; no OS CPU-affinity claim is made. The runtime
reported one task/one thread and exited zero. Its version string is
`26.2-unknown`, because this archive build lacks Git metadata; source and binary
hashes, not that string alone, identify the evaluation.

For this local prefix, the non-simulation startup check is:

```sh
.cache/elmer-evaluation/setup-v1/prefix/bin/ElmerSolver --version
```

This prefix is an ignored local engineering artifact. Do not commit its binaries,
source tree or build bulk. Configuration commands, fingerprints, runtime linkage
and observed resources are retained with the compact published evidence. Release
redirect query credentials are redacted from publication; the helper now records
only resolved URL origins/paths. Original private acquisition data is preserved.

Successful build and startup do not establish physical or numerical accuracy.
The [completed known-answer campaign](wo03-elmer-thermal-comparison.md) has
failed/unavailable criteria; the [decision](wo03-elmer-campaign-decision.md)
keeps actual geometry unqualified. No baffle solve, rocket acceptance or flight
release follows from setup.

## Published compact evidence

[Setup record](../runs/wo03-elmer-local-setup-20261101T052500Z/record.json) retains sanitized acquisition, commands, runtime, source/binary identities and resource accounting. The original private redirect metadata and build bulk are excluded.
