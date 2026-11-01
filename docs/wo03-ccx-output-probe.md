# WO-03 CalculiX output probe

**Decision:** the installed CalculiX 2.23 diagnostic confirms float32 scalar
values in the preserved A-2 `.frd` `NT` and `RFL` records. That output cannot
resolve the unchanged `1e-7 K` field check. `RFL` is exposed and agrees with the
hot-set `.dat` result in this run, but it is documented as external concentrated
heat sources; this probe does not prove it is an integrated film-heat output.
The declared three-grid packet is **incomplete**: A-2 solved, then the initial
reader stopped on an incorrect framing assumption. Per the stop rule, A-4 and
A-8 were not run. No acceptance criterion was relaxed, and no solver
qualification or baffle result is claimed.

## Identity and exact inputs

The command used the existing installed executable `/opt/homebrew/bin/ccx`,
resolving to `/opt/homebrew/Cellar/calculix@2.23/2.23_1/bin/ccx`, version 2.23,
SHA-256 `2349c77ebd8302615828ac3911caac45fb0a39363914ee555db1c7e3a86250bf`.
All thread-related environment variables were set to `1`.

The unchanged A decks were copied from the prior thermal-comparison packet;
only this card pair was inserted before `*END STEP`:

```text
*NODE OUTPUT
NT,RFL
```

No node, element, material, boundary, or method record changed. Source decks
and hashes:

| Grid | Retained input | SHA-256 |
| --- | --- | --- |
| 2 | `build/wo03-ccx-thermal-comparison-v1/A-2/case.inp` | `863c865282a83f35fc0283f2f2fbf68a719dd8ef14b8078338b679512e41ac31` |
| 4 | `build/wo03-ccx-thermal-comparison-v1/A-4-field-width-fixed/case.inp` | `d5dbcfcbdc881c61f468d379d03a02f77310ce8f91148861a32e37d4eb0d68f9` |
| 8 | `build/wo03-ccx-thermal-comparison-v1/A-8/case.inp` | `7338ee4a466ca17f48222e5ee2313db72b9382ad8ff21f42eea53304c07a2162` |

All three source hashes were verified before execution and again after the
probe; they are unchanged. The runner records each output-deck hash separately.
The physical model is the retained A box, `0.2 × 1 × 187 mm`, conductivity
`0.04 W/(m K)`, fixed hot wall `573.15 K`, cold bulk `308.15 K`, and film
coefficient `36030.6 W/(m² K)`.

## A-2 execution and FRD evidence

| Item | Observed |
| --- | ---: |
| Return code / completion marker | `0` / present |
| Solver wall time | `0.0200 s` |
| Child CPU time | `0.012015 s` |
| Child peak RSS (single child; `RUSAGE_CHILDREN`) | `6,160,384 bytes` |
| Setup wall time through source preflight | `0.00659 s` |
| Packet wall time at parser stop | `0.02153 s` |
| Child CPU allowance used | `0.012015 / 600 s` |
| Per-case wall allowance used | `0.02153 / 120 s` |

The saved FRD contains the ASCII field headers `NDTEMP` / component `T` and
`RFL` / component `RFL`. For each field the read-only decoder consumed exactly
27 records, checked node IDs `1..27` in order, and checked the subsequent
structural markers. Each record decoded as a 4-byte node ID followed by a
4-byte IEEE float32 value on this little-endian Apple Silicon host. The NT
block is followed by the next ASCII `1PSTEP` header; the final RFL block is
followed by the ASCII `9999` footer. This is a source-based layout check against
the official upstream [`frdselect.c`](https://github.com/Dhondtguido/CalculiX/blob/master/src/frdselect.c#L804-L839),
which writes scalar binary values via a `float` cast and `sizeof(float)`. The
upstream source tree is DEVELOPMENT, not source-pinned to the installed 2.23
build; the captured headers, complete node-ID sequence, values, and framing
provide the direct evidence for this run.

For the exact A-2 analytic profile, the decoded NT values span
`309.6128540` to `573.1500244 K`; maximum absolute difference from the exact
field is `2.4414e-5 K`. The observed float32 spacing across this temperature
interval is `3.0518e-5` to `6.1035e-5 K`. Decoded NT differs from the existing
`.dat` printed values by at most `4.5996e-5 K`. Those differences confirm the
field representation is too coarse to support `1e-7 K` evidence. They do not
establish solver field error below the `.dat` rounding interval.

The RFL hot-node sum from FRD is `9.856288970 W`, versus the existing DAT
hot-set total `9.856289 W`; the maximum per-hot-node difference is
`2.2748e-7 W`. At the observed hot-node magnitudes, float32 spacing is about
`2.98e-8` to `2.38e-7 W`, far above `1e-10 W`. The manual's
[output-variable table](https://www.dhondt.de/ccx_2.23.pdf)
labels the FRD RFL quantity “total flux”; its `*NODE PRINT` section defines
RFL as external concentrated heat sources. These observations establish that
the RFL records were decoded consistently with the DAT hot-node values. They
do not establish total heat transfer integrated over the cold film surface,
local energy balance, or the `1e-10 W` balance criterion.

## Stop and retained evidence

The first runner attempt had an overly narrow parser assumption: it searched
for a single-space `-4 NDTEMP` header and required an ASCII `-3` terminator.
The actual FRD uses padded header fields and the binary writer has no per-field
ASCII `-3` terminator. The solver itself completed A-2; the stop occurred in
post-solve parsing. The original incomplete `record.json` and as-run parser
remain preserved. A corrected decoder was run read-only on the saved A-2 files;
it did not invoke CalculiX. The parser correction diff and its hashes are also
retained.

The declared no-retry stop rule was applied after this parser-format failure:
A-4 and A-8 remain unrun. The final result is one-grid I/O evidence, not a
completed three-grid packet. See
[`build/wo03-ccx-output-probe-v1/record.json`](../build/wo03-ccx-output-probe-v1/record.json),
[`read-only-decode.json`](../build/wo03-ccx-output-probe-v1/read-only-decode.json),
and [`as-run-manifest.json`](../build/wo03-ccx-output-probe-v1/as-run-manifest.json)
for machine-readable resource, source, and format records.
The as-run and revised-parser identities are separately recorded in
[`runner-as-run.py`](../build/wo03-ccx-output-probe-v1/runner-as-run.py),
[`runner-parser-correction.diff`](../build/wo03-ccx-output-probe-v1/runner-parser-correction.diff),
and [`post-run-review-manifest.json`](../build/wo03-ccx-output-probe-v1/post-run-review-manifest.json).

The corrected runner is [wo03_ccx_output_probe.py](../scripts/wo03_ccx_output_probe.py);
the declared input manifest is [wo03-ccx-output-probe.yaml](../configs/studies/wo03-ccx-output-probe.yaml).
Its four independent format checks (including malformed-file cases) are in
[`test_ccx_output_probe.py`](../tests/test_ccx_output_probe.py). No later
solver run is authorized by this record.

A primary self-check exposed that whitespace-tolerant following markers could
hide a truncated record. The reader now requires the exact observed fixed-column
prefixes; independent IEEE-byte fixtures reject wrong IDs, infinity and
truncation. A read-only recheck of saved NT/RFL confirms 27 values per field.
The original parser failure remains preserved. These corrections and the
executed source snapshot are in the [published compact record](../runs/wo03-output-solid-map-20261101T011408613691Z/record.json). No additional solver call followed the stop.
