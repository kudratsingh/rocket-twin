# Elmer B stress-output preparation

**Prepared only; no solver was run.** The known B SINGLE nodal-load SIF is
byte-identical apart from `Calculate Stresses = Logical True`; its saved mesh
is copied byte-for-byte. Prepared SIF SHA-256 is
`6e25cf3e999af9959baa7475cbbbd0cfede7c15b18fec0b584f6b3126cfdd254`.
The prior successful direct-nodal B case and its source, module and solver
pins are recorded in the [preflight](../build/wo03-elmer-stress-fixture-v1/preflight.json).
No execution phase is implemented or enabled.

Pinned `StressSolve.F90` registers the six named stress components in order
`xx, yy, zz, xy, yz, xz` when requested. Its stress computation assembles and
solves a nodal projection; the intended output is therefore a recovered nodal
field, not independently validated integration-point stress. The SI inputs
imply pascals. Output array names, association, Float64 encoding and coverage
must be checked in the actual native output; the installed module has not yet
produced a stress output in this study. Unknown or ambiguous layout must stop,
not be guessed. No additional module build is implied by the source request.

The loaded 4 × 4 mm bar has analytic σzz = 9.375 MPa throughout both layers;
all other components and both unloaded bars have zero stress for ν = 0. The
existing [bridge structural preflight](wo03-g80-bridge-structural-preflight.md)
requires less than 2% stress error for its axial known case, less than 1%
displacement error and force residual below 1e-5 N. Applying the same 2% of
9.375 MPa as an absolute scale to every otherwise-zero component is an
explicit *proposed diagnostic*, not an already adopted zero-stress criterion.
The native U and force checks must remain unchanged. The synthetic tests check
named component placement and reject a missing field and wrong component;
they do not validate Elmer's actual VTU schema or stress calculation.

A future primary-admitted one-case packet proposes 120 CPU / 120 wall seconds
for the native case, 120 parent CPU seconds and a 60 CPU-second setup reserve
(300 CPU seconds planned, below 600), one requested CPU and a 2 GiB root-process
RSS guard. Stop on the first invalid input, tool, field, force, stress or resource
failure. The resource-control grace change and this numerical fixture cannot
retroactively repair the previous failed supervision or qualify the bridge.
Preparation and tests were brief, but aggregate setup CPU and wall were not
instrumented; they are unavailable rather than zero.

## Updated preparation for review

The primary extended the known-case gate before execution: maximum absolute
error across all six components and all 593 nodes must be less than 2% of the
9.375 MPa loaded axial reference. This is an additional full-tensor diagnostic;
the existing less-than-2% axial criterion remains separate and unchanged.
The v2 reader requires six canonically named Float64 **PointData scalar** arrays (case-insensitive only),
unique coordinates mapped to all 593 source nodes, and rejects missing,
duplicate, nonfinite, ambiguous or cell-associated components. This is a
source-backed expectation, not an observation of a native stress output. The
unchanged known-B reader retains the displacement and strict force checks.

The new launcher defaults to verification only and the configuration remains
disabled. It checks the v2 source/input ledger, prior fixture dependencies,
full installed prefix, and the separately pinned 50 ms supervisor helper;
it requests one worker and uses 120 CPU / 120 wall seconds for the child,
120 parent CPU seconds and a 2 GiB root-process RSS guard. The prior fixture
ledger's older supervisor hash is explicitly superseded only for this helper;
other dependencies must match. A v2 preparation initially stopped because its
parent directory did not exist; the directory was created and preparation
completed with no solver. Earlier setup usage remains unmeasured.

Three synthetic tests pass, including a 593-point VTU with named stress
scalars, lowercase names and rejection of missing or normalized duplicate fields; they do not prove the native output
schema. The launcher and ledger are ready for primary review; no case has been
admitted or run. The earlier statements that the launcher was not implemented
and that the full-tensor criterion was merely proposed describe the initial
preparation and are superseded by this section.

## Admitted known-case result

The single local B stress case completed under the supervised process and
passed the predeclared field, force and stress gates. Native PointData contained
Float64 scalar fields `stress_xx`, `stress_yy`, `stress_zz`, `stress_xy`,
`stress_yz`, and `stress_xz` at all 593 mapped nodes. Maximum σzz error was
`7.33379e-5 Pa`; maximum error across the complete tensor, normalized by
9.375 MPa, was `7.82271e-12`, below 0.02. Maximum displacement error was
`6.22462e-15 m`. The axial force residual was `9.53264e-11 N`, with a
`1.06581e-14 N` encoding bound, passing the unchanged 1e-5 N check. Stress is
a source-described nodal projection in SI pascals, not a verified local
integration-point or installed-joint stress.

The native child used 0.180223 CPU seconds and 0.222773 wall seconds; the
parent used 1.254062 CPU seconds and 226,541,568 bytes peak RSS. Root RSS was
sampled to 19,972,096 bytes; a sampled peak is not a guaranteed instantaneous
maximum. Inputs and prefix were unchanged and the exact disabled configuration
was restored. Earlier setup usage remains unavailable. The earlier bridge RSS
supervisor failure remains unchanged. This local known-case result does not
qualify actual bridge stresses, mesh convergence, material allowables or
installed strength; PR39 checks were pending at admission.
