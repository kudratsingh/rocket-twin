# Unsaved reference arrangement — callable contract

This separate namespace admits up to two **geometry-only display occurrences**:
one exact nominal motor-tube reference and one exact plain aft-annulus reference.
It implements no installed vehicle occurrence, physical inventory, product/stock
adoption, mating, connection, collision check or engineering result. ADR-0017
permits this bounded planning prototype; frozen RP1/AD1/D1 and the source catalog
remain unchanged. This is not full Add/Replace/Connect or FW2-025 completion.

## Integration seam

`src.vehicle.reference_arrangement` exposes pure functions:

- `create_plan(catalog)` returns the empty `reference-arrangement-v1` plan.
- `reconstruct_plan(catalog, instances)` reconstructs a plan from a list of at
  most two tiny rows. Each row has exactly `reference_id`,
  `definition_revision_sha256` and `translation_mm`; no source JSON, custom
  instance ID, quantity, scale, orientation or physical properties are accepted.
- `admit_plan(catalog, plan)` verifies full canonical output against reconstructed
  state, including every derived field, source pin, false gate and content hash.
- `apply_command(catalog, plan, command)` admits the supplied plan and applies one
  explicit command guarded by its exact `base_plan_revision`.

A future stateless API should call `reference_parts.build(root)` itself and
reconstruct submitted tiny rows against that fresh server catalog. The caller
must retain the base content guard when reconstructing and applying a command.
Do not accept a client-authored catalog or full plan as an authoritative source.
These functions perform no filesystem access, persistence, random/time calls,
CAD/kernel execution or physics. No API, UI, store or factory is mounted here.

Exact command shapes:

```json
{"type":"add-reference","reference_id":"reference-local-v1:motor-tube-nominal","definition_revision_sha256":"fd6c666dfed5d79ed44ed126b85d1de7dca87c1210165808b44f270e2ce2a42c","base_plan_revision":"<current plan SHA-256>"}
```

```json
{"type":"translate-reference","instance_id":"reference-arrangement-v1:motor-tube-nominal","translation_mm":[0,0,12.125],"base_plan_revision":"<current plan SHA-256>"}
```

Adding sets translation to `[0,0,0]`. Adding the same reference again rejects;
there are only two admitted references and at most two occurrences. A third
reconstructed row rejects before assembly. Translation requires an existing
instance. Unknown commands, reference IDs, definition revisions, fields and bad
base hashes reject. Stale commands raise `ArrangementError` with
`code: stale_plan_revision`, `field: base_plan_revision` and `current_revision`.
Other errors carry a stable `code` and optional field, without exposing paths or
raw input. No exception is converted to a passing/empty arrangement.

## Identity and coordinate rules

The admitted catalog content revision is
`8f6b7bf2f0dcc8dfb2714ba7a28688c820869dc3045060aba6ea5901983b7748`.
Both full definition contents and their exact revisions are verified:

| Reference | Definition revision |
| --- | --- |
| `reference-local-v1:motor-tube-nominal` | `fd6c666dfed5d79ed44ed126b85d1de7dca87c1210165808b44f270e2ce2a42c` |
| `reference-local-v1:aft-annulus-nominal` | `158150615a9c291ce12b3320d535c11151a564d7ad176dda9ca9693025a5d710` |

Catalog source pins and both definition revisions remain on every plan. Instance
IDs replace the admitted reference's namespace with `reference-arrangement-v1`;
the exact allowlisted slugs make this deterministic and unambiguous. Instances
are always returned in source catalog order, regardless of command/input order.
Each fixes `quantity: 1`, identity `rotation_quaternion_xyzw: [0,0,0,1]`, unit
`scale: [1,1,1]`, `installed_transform: null`, `added_to_source: false` and
`added_to_vehicle: false`.

`translation_mm` is a three-number JSON list in an **uninstalled arrangement
frame**. Its axes remain parallel to each registered local CAD X/Y/Z, with +Z
along the nominal part length; the origin is an arrangement origin, not RP1's
installed frame. There is no automatic centering or installed transform. A later
viewer must apply translation in CAD millimetres before the existing mapping
`viewer[X,Y,Z]=[cadX/1000,-cadZ/1000,cadY/1000]`. The fixed quaternion and unit
scale cannot be edited in this slice.

Coordinates must be finite Python integers/floats, never booleans, and lie
within ±500 mm inclusive. `Decimal(str(value))` checks a maximum of three
meaningful decimal places without rounding or clamping. This is **input
granularity, not physical tolerance or fit precision**; registered nominal
geometry dimensions retain their original precision. Integral floats become
integers and negative zero becomes integer zero. JSON numeric trailing zero
spelling has no identity. Tuples, strings, null, nonfinite values and finer
coordinates reject.

The single `revision_sha256` hashes the complete canonical Python plan excluding
that revision field, using the existing sorted, finite JSON digest. Reconstructing
in a different order produces the same content identity. Translating to the
same normalized location is a fresh independent return with unchanged hash;
translating away and back restores the earlier content hash. There is no event
sequence, undo log or monotonic history. The hash is an opaque Python content
guard, not evidence of server persistence or authoritative cross-tab ordering;
a frontend must not rehash full source/plan JSON using JavaScript numeric rules.

## Availability, unknowns and limits

Catalog availability is validated separately from its immutable source content.
Hot and cold catalogs produce the same arrangement identity. The plan embeds no
assets or cache availability claims; the future API/UI must display availability
from its fresh server catalog separately. Missing registered bytes stay
unavailable, with no fallback or regeneration. A pure function cannot re-verify
bytes after its caller built the catalog. Corrupt source/asset bytes must still
be rejected by `reference_parts.build`; this module neither reads nor replaces
them. No public URL availability is inferred from local cache verification.

Every plan is `geometry_only_unsaved`. `physical_inventory`, installed transform,
total mass, explicit `mass_credit_kg`, CG, inertia, procurement cost and results
are null/unavailable, never
zero or pass. Resolved-candidate, simulation, engineering, physical, flight,
mating and Connect readiness all remain false. Old source definitions retain
`add_instance_api: false`: only this separate namespace creates arrangement
**display** occurrences. No source exclusion intents, 55-record accounting,
saved-draft metadata or physical inventory enter this namespace. The tube's
stock/motor identity conflict, unknown tolerances/materials and ring joint
limitations remain on the unchanged source definitions; positioning either
reference provides no qualification or capacity evidence.

## Executed checks and boundaries

`tests/test_reference_arrangement.py` uses actual pinned tracked sources copied
to temporary roots, with all four registered cache files absent. The actual
known source root is additionally compared in its existing hot-or-cold state;
no cache is required, copied, deleted, scanned for substitutes or generated.
Tests exercise two additions, bounded translation, source ordering, normalization,
no-op/restored hashes, independent returned objects, source preservation,
stale/duplicate/foreign/unsupported requests, malformed numeric input and
rehashed plan/catalog tampering. Calls also run with file reads forbidden after
catalog construction. No owner UUID, library, server or browser is accessed.

Focused pytest: **31 passed**. Scoped Ruff and Black pass; strict mypy
with `--follow-imports=silent` passes for the new module. These are local pure
source/code checks, not integrated API/browser/native rendering or geometry
placement acceptance. Primary owns later routing, UI/admission and publication.
No physical variant, CAD generation, simulation, supplier contact or purchase
was performed. All five inquiries remain UNSENT and engineering/physical/flight
gates remain open.
