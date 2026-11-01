# WO-03 CalculiX backend and binary result-output assessment

## Decision

There is a plausible, still unverified native route to reduce force-output quantization: request `RF` using `*NODE OUTPUT`, which writes the mixed binary/ASCII FRD file. The documented `*STATIC` option supports `SOLVER=ITERATIVE CHOLESKY`; the installed Homebrew package is CalculiX 2.23_1, its pinned executable SHA-256 is `2349c77ebd8302615828ac3911caac45fb0a39363914ee555db1c7e3a86250bf`, and its binary contains the `ITERATIVECHOLESKY` and `SPOOLES` option strings. No run with either backend/output combination is authorized by this assessment.

The FRD precision is **not certified for the installed 2.23 binary**. Manual §7.98 documents the binary/ASCII FRD behavior but does not specify scalar/vector value widths. The official upstream GitHub `frdvector.c` currently writes vector values as C `float` (4 bytes) in its `output="bin"` branch, as text with `%12.5E` fields after float casts in its `output="asc"` branch, and as C `double` (8 bytes) in its third/other branch; each binary branch writes an integer node identifier before the vector components. The third branch is not `asc` and must not be described as the ordinary ASCII path. The manual documents no input or CLI switch that selects that third branch, and I found no documented selector for it. The repository page is `master`, not a source tag or commit verified to match the 2.23 source archive used for the local binary. It therefore does not prove that the installed writer takes any one of these paths or establish its full field framing. Coordinates are not used as evidence of RF value width.

## Precision implication

For a float32 FRD vector path, a conservative per-component encoding bound for normal values is `u × Σ|RF_i|`, with `u = 2^-24`; the serialized values would be summed in wider precision. Read-only arithmetic on the preserved B DAT support reactions gives an axial bound of `8.941e-6 N` in each step, just below the existing `1e-5 N` criterion. This makes binary FRD **plausible** for B, subject to verified route and end-to-end parsing; it is not a pass and does not account for any other uncertainty.

The same estimate on the preserved actual bridge's second-step support reactions is `1.5651e-5 N` axial, before transverse components. Thus float32 alone would not certify its unchanged `1e-5 N` reaction criterion. Independently, the actual bridge's observed force residual is `104.6968 N`, and its reciprocal-work discrepancy is `32.2291 N·mm`; a more precise output channel cannot cure either result. No precision or force threshold is changed here.

| Evidence case | Existing axial RF absolute sum | Float32 encoding bound | Existing strict limit | Implication |
| --- | ---: | ---: | ---: | --- |
| Known B, step 1 | 150 N | 8.941e-6 N | 1e-5 N | Quantization bound could fit narrowly if actual RF field encoding and parsing are verified. |
| Known B, step 2 | 150 N | 8.941e-6 N | 1e-5 N | Same as step 1; still unverified. |
| Actual bridge, step 2 | 262.574 N | 1.5651e-5 N | 1e-5 N | Float32 encoding alone exceeds the limit. |

The estimate uses the saved decimal reaction values as an upper bound on `Σ|RF_i|`; it does not claim to have decoded FRD. In the actual bridge, large cancelling nodal reactions make the total absolute sum substantially larger than the net 150 N applied force.

## Documented capability and local evidence

- CalculiX 2.23 manual §7.123 (`*STATIC`, p. 600) specifies the `SOLVER` selector and says the linear default is SPOOLES. The manual's solver discussion documents `ITERATIVE CHOLESKY` as incomplete-Cholesky preconditioning. The exact token spelling in the manual includes spaces: `SOLVER=ITERATIVE CHOLESKY`.
- Manual §7.98 (`*NODE OUTPUT`, pp. 566–567) says the keyword writes selected nodal fields to `.frd`; unlike `*NODE FILE`, its file is a mixture of binary and ASCII. It documents `RF` as an available nodal output key (also described under `*NODE FILE`). It does not specify numeric widths, byte order, records, or an output-precision switch.
- Manual §7.99 (`*NODE PRINT`, p. 567) describes DAT `RF` as external forces, normally reactions but including nodal concentrated and distributed loads where applicable. The documented binary route changes file encoding; it does not establish different RF physical semantics.
- Local read-only package metadata reports `freecad/freecad/calculix@2.23` version `2.23_1`, installed from the 2.23 source archive whose Homebrew recipe records SHA-256 `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`. `strings` on the pinned executable finds both solver option strings, but strings are capability evidence only; no input has been run to confirm acceptance of the keyword or convergence.
- The official upstream source repository's current [`frdvector.c`](https://github.com/Dhondtguido/CalculiX/blob/master/src/frdvector.c#L41-L55) shows the `output="bin"` vector path writing an `int` node identifier and three `float` values; the `output="asc"` branch uses textual `%12.5E` fields and float casts; the third branch writes the node ID plus three `double` values. No documented option was found to select that third branch. This source is **not pinned to, or demonstrated identical with, the 2.23 source archive**. The relevant 2.23 tagged-source function/format path and the installed FRD value encoding remain unresolved.

## Narrow future diagnostic, if separately declared

No backend or output rerun should start automatically from this assessment. A future known-answer packet would first need a primary decision on whether to test only the documented binary `*NODE OUTPUT` path or to stop until a matching 2.23 source proves a double-width selector. If binary is selected, the narrow candidate remains: same-physics B with SPOOLES, then B with `ITERATIVE CHOLESKY`, and only after both unchanged known-answer gates pass, the saved actual coarse deck with `ITERATIVE CHOLESKY`. Keep inputs and criteria unchanged, and stop on the first failure, malformed/unmapped FRD, or cap. This note itself authorizes no execution.

## Preserved reciprocity evidence

The compact projection and reproducible projection script are [record.json](../runs/wo03-g80-reciprocity-20261101-v1/record.json) and [proof.py](../runs/wo03-g80-reciprocity-20261101-v1/proof.py). The original 5 MB record and its hash are retained unchanged under `build/wo03-g80-bridge-reciprocity-audit-v1/record.json`. The compact record preserves source hashes, native step time/increment rows, load counts, work values and print bounds; it omits the 85,700 displacement rows, support RF arrays and 4,256 serialized load rows. Resource accounting for the audit is unavailable because no CPU or wall sample was recorded.

## Sources

- [CalculiX CrunchiX 2.23 User’s Manual](https://www.dhondt.de/ccx_2.23.pdf), §§7.97–7.99 and §7.123.
- [Official Dhondtguido/CalculiX source repository, `frdvector.c` on `master`](https://github.com/Dhondtguido/CalculiX/blob/master/src/frdvector.c#L41-L55). This is explicitly not treated as a verified 2.23 source snapshot.
