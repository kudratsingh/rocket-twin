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

## Runtime and evidence status

Store/API/composition checks and Node/Vite source/SSR tests cover the implemented
contract. **The live browser fork/save/reload/history/conflict lifecycle remains
unverified.** The isolated startup attempt stopped at the first denied loopback
bind, without starting a server or touching the owner's services/data.

The normal-host preview needs its ordinary restart to load the new router before
live lifecycle verification can proceed. Until then a missing route reports the
restart requirement; it does not fall back to static mutable data. No restart,
server action or additional browser attempt is performed by this documentation.
See [backend behavior and startup status](backend.md) and
[bounded integration record](integration.md). FW2-024/FW2-A18 remain partial.

## Observed native limit

P76 first reached the loading panel and then a blank application. That failure
is retained. One scoped error boundary now protects the optional panel; its
escaped diagnostic/source-return fallback passes repository checks. P77's single
ordinary reload displayed the real library and explicit unavailable404/restart
explanation. No boundary fallback was triggered or tested, and no fork/save,
Return click or flight-computer observation occurred. The positive lifecycle
still requires the normal-host restart. See [actual browser record](browser-library.md).

P77 estimated record/inventory closeout was203.462seconds against180seconds,
an explicitly failed timing bound. Its limited native observations remain valid,
but there is no whole-packet, catch-path or lifecycle pass.
