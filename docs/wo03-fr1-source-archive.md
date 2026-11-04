# FR1 publication: historical schema provenance correction

The first PR75 hosted run41788449738 failed two historical C1/C2 provenance
tests after the new solid-carbon material tag changed `src/vehicle/schema.py`.
All new engineering data remained unchanged. Those tests compared frozen input
hashes to current code, preventing an otherwise valid schema evolution.

The original schema is now archived byte-for-byte at
`data/source-archives/schema-e11d777cce363e45.py.txt`, SHA256
`e11d777cce363e45fd07376b45db4bde640cea00fefda8377ced735250de5093`.
It was recovered by removing only the newly added tag from the maintained file
and verifying the exact original digest and pre-FR1 source. The `.txt` archive
is data: it is not imported or executed as a replacement current validator.

The two tests now verify exact current bytes when they match, or the explicit
source-path/hash archive when current code has evolved. Unknown drift, missing
archives and altered archive bytes still fail. No expected hash, old result,
force, material criterion or current nonmetallic validation was relaxed.
Separate tests reject tampered archives and an aluminum fin. This maintenance
fix does not establish any material or engineering acceptance.

The failed hosted run remains preserved. Replacement required checks must pass
at the new PR head before routine merge; no check is bypassed or deleted.
