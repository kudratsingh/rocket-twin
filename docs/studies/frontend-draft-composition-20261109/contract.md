# Source-fork planning overlay — pure exclusion/restore intent

This bounded P5 foundation records **planning intent only** over one verified
saved RP1 source fork. It does not remove a physical part, supply a replacement
function, earn mass credit, create a candidate or admit new engineering work.
The immutable base always retains all **55 original source accounting
occurrences**, including raw quantity, group count, placement, estimates,
unknown fields, conflicts, failed findings and source evidence.

FW2-025 remains incomplete. No API, store, UI, database, source YAML or existing
client/fixture is changed. Frozen AD1/D1, G54/G12 PID-to-RL, every physical gate
and the five UNSENT inquiries remain unchanged.

## Pure callable seam

`src.vehicle.draft_composition` exposes two functions:

```python
overlay = create_overlay(saved_revision)
next_overlay = apply_command(overlay, {
    "type": "exclude-source-occurrence",  # or restore-source-occurrence
    "occurrence_id": "fin_set",
    "base_overlay_revision": overlay["revision_sha256"],
})
```

`create_overlay` accepts the original Python saved-revision object from the
source-fork contract, including its complete source snapshot. It returns a new,
independent value with no exclusions. It verifies exact schema/UUID/sequence/
lineage/text/readiness and original metadata content hash, the complete server
canonical source hash, frozen RP1 source references, bank identity/revision and
55 unique definition/occurrence links. The two existing source-only/registered-
inspection snapshots remain the only admitted source identities. No new source
is generated, projected or resolved.

This function performs no store access: the caller must supply an actually saved
revision from its trusted workflow. Content hashes validate content/identity;
they do not authenticate a caller or prove possession of a local library record.
The structured review JSON export is not an import/restore input. Python source
canonicalization is the existing `parts_bank.digest` algorithm (sorted keys,
compact UTF-8 JSON, ensure_ascii=false, allow_nan=false), not a new cross-language
source hash algorithm.

`apply_command` first validates the entire submitted overlay and its hash against
a rebuilt expected intent preview, then validates the explicit command. The
only supported command fields are `type`, `occurrence_id` and
`base_overlay_revision`; no client paths, replacement quantities or metadata
updates are accepted. A command requires the exact current overlay hash and an
exact original occurrence ID. It always returns independently copied data and
never mutates its input or the source fork.

## Identity, reversal and errors

The overlay has a single `revision_sha256` covering every other overlay field,
including the unchanged saved base and derived preview/blockers. It is content
identity, not a new draft UUID, timestamp, mutation counter or history store.
Exclusion IDs are canonicalized in original source order, so equivalent intent
sets have the same hash regardless of command order.

- Excluding an included occurrence adds one exclusion intent and a visible
  unresolved-function blocker. Excluding it again fails `duplicate_exclusion`.
- Restoring an excluded occurrence removes that intent. Exclude then restore
  returns the original content/hash, while preserving independent object identity.
- Restoring an already-included occurrence is a **guarded no-op**: the current
  base hash is still required, the returned value is independent, and content/hash
  stay unchanged. A stale base fails even for this no-op.
- Duplicate/unknown intent IDs, malformed overlay/hash, altered derived preview
  or readiness, unknown command fields and unsupported schemas fail explicitly.

`CompositionError` carries stable `code`, optional `field` and optional
`current_revision`. A stale command returns `stale_overlay_revision` with the
current hash for explicit reload/reconciliation. Other relevant codes are
`invalid_saved_revision`, `source_unavailable`, `invalid_overlay`,
`invalid_command`, `unknown_occurrence`, `duplicate_exclusion`,
`unknown_command` and `unsupported_command`. Failed commands change nothing;
there is no retry or persistence side effect.

Known future commands `add`, `replace`, `connect`, `set-position`, `set-parameter`
and `resolve` return a specific missing-admission explanation. Add requires
reusable local definitions/frames/parameters/interfaces/counting; Replace needs
complete function/interface/hardware resolution; Connect needs actual named
features, transforms, retention/process/tolerance and evidence. Position and
parameter editing need backend generation/check invalidation. Resolution needs
an effective candidate and supported inputs. Other names are unknown commands.
Installed-reference assets never become reusable local parts through this seam.

## Preview and accounting boundary

`base` is the complete unchanged saved revision. `source_sha256` and
`source_revision_sha256` retain its exact source/metadata identity. No source
record is deleted or changed and no reduced "active mass" inventory is produced.

For each excluded intent, `preview.removed_functions` retains the source function,
original occurrence, provenance, unresolved issues, geometry scope, interface
missingness and physical-verification status. These explain what function would
be removed **if later implemented**, without pretending it has been replaced or
its evidence has disappeared. The preview explicitly states that the source
ledger remains intact; `effective_inventory` stays null.

`checks.status` is `unavailable`. Total mass, mass-removal credit, CG and inertia
stay **null**, never zero or pass. Resolve availability, resolved-candidate,
simulation eligibility, engineering acceptance and flight readiness stay literal
false, even with no exclusions or after restoring everything. Global blockers
retain source estimates/conflicts, failed fin findings, missing installed
geometry/inertia and physical gates; exclusions add their unresolved function
blockers. No CAD/physics/material calculation, mass sum, source adoption or
physical authority follows from any command.

## Verification and integration limits

Thirteen focused pytest cases pass using only a copied, SHA-verified
`b2339838a42a6426d535a533df7c021211362e3dd4e643a933e5c4562d0cded0`
actual-store test fixture in isolated temporary storage. They cover source and
all-55 preservation, three-fin group counting without mass credit, retained
conflicts/failures/null inertia, exclusion/restoration/no-op identities,
order-independent content hashes, stale/duplicate/unknown commands and IDs,
unsupported future-command reasons, malformed/tampered metadata/source/preview,
literal-false readiness and independent returns. A pure-operation test forbids
filesystem/store calls while applying the commands.

Black, Ruff and strict mypy on the new module pass. One scoped correction closes
Python's `0 == False` validation ambiguity by requiring literal readiness booleans
and checking the submitted overlay's canonical content hash before accepting its
derived preview. No owner UUID/library was opened and no owner data was written.

Primary review of this contract precedes any draft-command/preview integration.
There is no persistence protocol, command endpoint, native interaction evidence,
effective configuration, resolved accounting, CAD or simulation admission here.
The current review-JSON/native publication is independent of these three files.
