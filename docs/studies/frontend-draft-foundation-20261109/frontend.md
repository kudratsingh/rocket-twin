# Saved drafts — metadata library

Open the current RP1 design, then **Parts bank → Saved drafts**. The library
supports the exact frozen `G80-F2-RP1-AD1-definition-v2` source, specification
SHA-256 `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`.
It creates separate local draft identities; selecting a draft does not replace
the rocket in Design.

## Use the library

1. Enter **New draft label** and optional **New draft notes**, then choose
   **Fork RP1 as separate draft**. Forking is explicit; opening the library only
   requests its saved list. A successful fork opens its new identity. Use
   **Refresh library from first page** to update the list, or **Next saved drafts
   page** when another page is available.
2. Open a saved draft by its label. Its UUID, current loaded revision, source
   snapshot hash and frozen specification are displayed. Edit **Draft label** or
   **Draft notes**, then choose **Save metadata revision**. The save uses the
   exact loaded base revision and appends immutable history.
3. Choose **Load parent saved revision** to inspect earlier saved metadata.
   History is read only and leaves the current editor, including unsaved text,
   intact. **Return to current metadata revision** closes the history view.
4. If another save has changed the head, the stale-save error preserves both
   unsaved fields and shows the newer revision. Saving is blocked until an
   explicit reload. **Reload latest and discard unsaved text** replaces the
   editor only after the latest snapshot is successfully loaded. There is no
   automatic retry, merge or overwrite.

While metadata is unsaved, opening another draft or forking is disabled. Save it
or use the explicit discard/reload action first. List refresh and history
inspection do not discard the editor. A failed request displays a recoverable
error; retry/reload actions are explicit. A missing or invalid response is not
shown as an invented empty library, and mutable drafts have no prepared-snapshot
fallback.

## Returning to the rocket

**Inspect frozen parent rocket**, source-part inspection links and **Return to
rocket** return to the existing source inspection path. After its first visit,
the Saved drafts pane stays mounted for the same loaded source when switching
Parts bank sections or closing/reopening the dialog. This preserves its loaded
snapshot, unsaved text and conflict state; closing the dialog does not save.
Changing the source or reloading the page resets this in-memory editor. Only
successfully saved revisions persist in the local library.

## What this increment preserves

Every admitted snapshot retains all **55 source accounting occurrences**, their
original definitions, quantities, estimates, conflicts and missingness. Geometry
children do not add mass charges. Labels and notes do not change the frozen
specification, saved runs, placement, geometry, mass, inertia, motor or evidence.
The library displays engineering acceptance open, simulation eligibility false
and flight readiness false.

This increment provides metadata authoring and history inspection. It does not
provide Add/Replace/Connect, blank rockets, parameter editing, undo/revert,
candidate resolution, CAD generation, checks or simulation admission. Existing
engineering, purchase, physical, paid-run, WO-10 and flight gates remain open;
all five inquiries remain UNSENT.

## Download the shown saved record

**Download saved review JSON** exports whichever saved current or historical
revision is shown in the identity panel. It never overlays unsaved editor text
or implicitly saves. The filename contains UUID, sequence and saved-revision hash
prefix. The UI reports the actual export-byte digest separately from the original
server source hash. The file includes one structured source-fork record, all55
source accounting occurrences and parent identity; no geometry asset bytes or
ancestor contents. It is not a byte-exact backup, import/restore file, candidate
or simulation configuration. [Format and limits](record-export.md).

## Runtime and observed evidence

The owner confirmed normal-host restart. P81 created exactly one clearly labelled
validation draft and saved its notes. P82 reloaded2, viewed historical1, returned
to2 and downloaded its reviewJSON. Primary actual-file readback verified772101
bytes/SHA3e8a7854…d91588 and semantic equality to saved2. P83 exercised a stale
Save against a deliberate competing update on this same test record: unsaved
text remained, then explicit reload loaded3. Three persisted revision digests,
unchanged55-record source and no rejected-write revision4 independently verify.
The numericHTTP409 code is API-contract evidence; the browser shows its conflict
behavior, without network-status instrumentation. No other draft was edited.

P81/P82/P83 native and evidence-closeout times met their respective bounds.
P76's blank-app failure, P77's closeout overrun and the unexecuted P80 parser
failure remain preserved in the linked record; later success does not erase them.
The boundary's exception catch path, modal persistence across every transition,
blank/composed drafts, undo/revert and full FW2-A18 remain open. See
[actual lifecycle observations](browser-lifecycle.md), [earlier failure](browser-library.md)
and [backend contract](backend.md). All physical/flight gates and five UNSENT
inquiries remain unchanged.
