# Saved source-fork review JSON — standalone builder

This bounded increment builds a **structured review copy of one already-saved
source-fork revision**. It is not a byte-exact store backup, import/restore
artifact, resolved candidate, simulation configuration or full FW2-028 delivery.
The frozen original and every engineering/physical/flight gate stay unchanged.

## Integration seam

`web/src/design-builder/draftRecordExport.ts` exports:

```ts
exportDraftReviewRecord(
  revision: DraftRevision,
  vehicle: InspectionDocument,
): Promise<{
  filename: string;
  text: string;
  bytes: Uint8Array<ArrayBuffer>;
  sha256: string;
}>;
```

Pass the selected **saved snapshot**, such as `editor.snapshot`, or a successfully
loaded historical revision. Do not overlay unsaved label/notes, pass the editor
object or implicitly save before export. The builder takes an independent JSON
snapshot and calls the existing strict `admitDraftRevision` before producing any
review record. Unsupported source, revision, inventory, readiness or metadata
fails visibly; no fallback or automatic repair is added.

The intended later button label is **Download saved review JSON**. The primary
owns that UI/download integration, any Blob/object-URL lifecycle and its actual
browser evidence. The UI should explain that unsaved text is excluded. This
builder never accesses a DOM, clicks a link, fetches assets, reads/writes files,
mutates the store or starts a download.

## Contents and deterministic identity

The document has `schema_version: 1`, format
`rp1-saved-source-fork-review-v1`, explicit review/serialization limits and the
complete admitted revision under `draft`. It retains all original metadata,
UUID, sequence, UTC timestamp, operation, saved revision hash, source snapshot
identity, parent revision reference, source specification, bank/inspection
snapshot, source references and all **55 original accounting occurrences**.
No source field is removed or replaced with zero: estimates, null physical
inertia, unavailable geometry, product conflicts, failed fin findings, saved mass
cases and open physical status remain at their original scope.

It contains one revision. Its `parent_revision_sha256` identifies lineage, but
ancestor revision contents are not fetched or embedded. Source CAD/mesh/image
references remain references; their binary asset bytes are not embedded. The
payload explicitly records source-fork-only/unresolved status, false resolved-
candidate/simulation/engineering/flight gates, no import/restore support and no
byte-exact backup claim. It cannot compose, adopt, resolve or simulate a vehicle.

Object keys are recursively ordered before two-space JSON serialization, with
one final newline and UTF-8 encoding. There is no newly generated timestamp or
export ID. The same semantic input produces the same text and bytes regardless
of incoming object-key insertion order. Non-JSON values, nonfinite numbers,
cycles and object accessor properties fail rather than being silently coerced.

The filename is exactly:

```text
rp1-draft-review-<server UUID>-r<sequence>-<saved revision hash first 12>.json
```

It contains no label, notes, source path or client filename. The hash fragment
in this filename identifies the **saved revision**, not the exported file.
`sha256` is calculated separately with Web Crypto over the actual returned
`bytes`, including indentation and final newline. It is not embedded as a
self-referential file hash.

## Serialization boundary

JSON parsing/stringification can change numeric lexical forms: Python `1.0` may
be exported as JavaScript `1`. The review preserves parsed semantic fields, not
the exact original source-file or store-file bytes. Deterministic key ordering
for this format does not establish equivalence to the server's Python canonical
encoding.

The preserved `draft.source_sha256` identifies the **original server canonical
snapshot**. It is not a digest of the reconstructed review's `draft.source` bytes.
The original metadata revision hash is checked by existing client admission;
the review's complete-source checks retain that admission scope. This increment
adds no full-source canonical hashing algorithm, no independent server-source
byte reconstruction and no restore/import verifier. Only the separately
returned `sha256` identifies the actual exported review bytes.

## Validation and limits

`web/tests/draft-record-export.test.mjs` reuses the frozen actual-store fixture
`rp1-draft-library.json`, SHA-256
`b2339838a42a6426d535a533df7c021211362e3dd4e643a933e5c4562d0cded0`.
It introduces no Python or web dependency. Six reported Node/Vite source-loader
tests pass, covering current and historical revisions, independently reparsed
field preservation, independent Node crypto checks of export bytes and saved
metadata identity, all 55 records/nulls/estimates, source pins, parent identity,
stable ordering, filename safety, guarded tampering/foreign/unavailable source,
unsaved-editor rejection and absence of fetch/download side effects.

Scoped ESLint/Prettier and web TypeScript checking pass. The returned byte array
owns an `ArrayBuffer`, making it directly usable as a later Blob part without a
shared-buffer cast. No existing client, fixture, backend, route, library control
or shared import was changed. No server, browser, Git/network, physical work or
owner draft mutation occurred.

This is source/structured-artifact evidence only. The normal-host lifecycle,
actual download/readback, browser messaging and integration remain unverified;
this packet starts no new native attempt. Primary integration/publication and
full FW2-028 remain separate. Five inquiries stay UNSENT and all owner gates
remain open.

## Integrated UI and actual readback

The primary added **Download saved review JSON** to the shown saved identity in
Parts bank → Saved drafts. The action validates the selected saved snapshot,
creates the Blob from returned UTF-8 bytes and requests one download; a revoked
object URL is cleaned after use. It reports requested filename/size/digest without
claiming browser completion. Unsaved edits are excluded and no save is implicit.

P82 reloaded2, inspected historical1, returned to2 and actually downloaded the
current2 record. Chrome showed754KB Done. Primary verified the fresh actual
772101-byte file and SHA-256
`3e8a7854563db8ec9564113759cea4824ad1936c96b894674f26bf2213d91588`,
parsed it, compared all semantic fields with actual saved2 and confirmed all55
records/no embedded assets/false gates/head unchanged. This supersedes the
standalone-only UI/native statements above. [Readback receipt](lifecycle-readback.json)
· [Native observations](browser-lifecycle.md).
