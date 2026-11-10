# Reference arrangement — browser client admission

The standalone client prepares and changes only an **unsaved geometry-reference
arrangement**. It does not open saved draft IDs, persist state, edit the source
vehicle or produce physical inventory, mass credit, results or an accepted
candidate. No shared UI, API factory or route mounting is changed by this lane.

## Callable UI seam

`web/src/parts-bank/referenceArrangementClient.ts` exports:

- `createReferenceArrangementClient(fetcher = fetch)`. Construction performs no
  I/O. `prepare(signal?)` explicitly sends one GET to
  `/api/reference-arrangement` and requires the exact recorded empty plan.
- `client.command(baseEnvelope, corecommand, signal?)`. One POST contains exactly
  `{instances: tinyRows, command: corecommand}`. Tiny rows carry only reference
  ID, definition revision and translation. The command type is the exact Python
  union, including the current `base_plan_revision` guard. No client source,
  full plan, asset path, scale, orientation or physical properties are submitted.
- `ArrangementEnvelope`, `ArrangementPlan`, `ArrangementInstance`,
  `ArrangementCatalog`, `ArrangementTranslation` and `ArrangementCoreCommand`
  types, plus `admitArrangementEnvelope(raw)` for explicit response admission.
- `parseTranslationText(raw: string): number`, which throws a safe
  `ReferenceArrangementServiceError` on invalid input. Error objects expose
  `status`, `code` and optional `currentPlanRevision` without raw server errors.

A command's successful return has the exact API envelope:
`{catalog, plan, action: 'preview_uninstalled_reference_arrangement',
persisted: false, source_vehicle_changed: false}`. A UI can obtain definitions
and separate cache status from `catalog.definitions` / `catalog.availability`,
and display occurrences from `plan.instances`. Resolve each occurrence's exact
reference ID to its admitted definition for the independent scene renderer.
Missing registered cache is still an admitted **unavailable** state, never a
substitute geometry or a public-URL access claim.

Caller example:

```ts
const client = createReferenceArrangementClient();
const empty = await client.prepare(signal);
const reference = empty.catalog.definitions[0];
const next = await client.command(
  empty,
  {
    type: "add-reference",
    reference_id: reference.id,
    definition_revision_sha256: reference.revision_sha256,
    base_plan_revision: empty.plan.revision_sha256,
  },
  signal,
);
```

For translation, submit the selected occurrence ID and three separately parsed
text coordinates. The parser accepts ordinary signed decimal/exponent spelling,
trims surrounding whitespace and normalizes integral values and negative zero.
It validates decimal digits **before** numeric conversion: a finer lexical
value cannot round into an accepted millimetre value. Blank input, nonfinite
values, booleans, hexadecimal text, values beyond ±500 mm and more than three
meaningful decimal places reject. Trailing decimal zeros do not add meaningful
precision. This is input granularity, never tolerance or fit precision; no value
is rounded or clamped.

## Source record and validation

Production imports only the compact tracked
[`admission.json`](admission.json), never a test fixture. The 5,931-byte record
contains schema/generator identities, actual generator hashes, the catalog
header without definitions/availability, the actual empty plan and the two exact
reference/definition/template/instance identity mappings. It embeds no geometry.
Its SHA-256 is
`379c8072af75534d741ed3e216bca1e48abb91c30f0b1fc3d48098622d17d321`.

The catalog header must equal this source record exactly. Each definition and
its separate availability pass the existing `admitReferencePartDetail` path,
including source geometry, local/viewer frames, registered asset identities,
unknowns and old false readiness gates. Both definitions must remain in source
order; foreign/extra catalog fields reject.

The plan header must exactly match the actual empty template after excluding
only instances and revision. This preserves source pins, frame, null physical
inventory and installed transform, explicit null `mass_credit_kg`, other null
checks/results, unchanged false readiness and limits. There may be at most two
unique source-ordered occurrences. Each has its exact recorded instance/reference
ID and definition revision, quantity one, fixed identity quaternion, unit scale,
null installed transform, false source/vehicle addition flags and bounded
three-coordinate translation. Unknown fields, flags, transforms or foreign
identities reject.

A command snapshots its admitted base before I/O. It derives the exact expected
instance transition from that snapshot, including default-origin addition,
unique-reference limits and selected-instance translation. A response must match
those expected rows. Changed rows must change the base content guard; a no-op
must retain it. Echoing the prior base, adding the wrong reference or changing a
second occurrence cannot replace the displayed result. The client never mutates
caller state on success or failure.

**Hash limit:** nonempty plan SHA-256 values are validated as opaque Python
identities, not recomputed in JavaScript. The empty hash is exactly recorded.
Semantic source/transition admission does not prove a nonempty hash's mathematical
correspondence to Python canonical bytes; the server reconstructs tiny state and
validates the submitted guard. No full source/plan hash algorithm, server-head
freshness assertion, persistence, cross-tab ordering or event history is implied.
The UI should apply results only to its still-current request/base and retain
previous state and unsaved text on errors. The client performs no autosave,
automatic prepare, retries, fallback, download or reset. Abort guards before and
after transport/JSON prevent an aborted result from being returned for display.

## Actual producer fixture and checks

[`web/tests/fixtures/reference-arrangement.json`](../../../web/tests/fixtures/reference-arrangement.json)
contains one catalog plus four actual Python plans: empty, tube at origin, both
references at origin and tube translated to `[12.125,-8,165.001]`. It is not a
runtime fallback. Generation copied only `reference_parts.SOURCE_PINS` into a
temporary directory, created the four known asset parent paths with no assets,
called the actual `reference_parts.build`, then `create_plan` / three explicit
`apply_command` calls. Every registered cache path remained absent. The result
was serialized as finite JSON and formatted; no owner draft, CAD kernel, physics,
server or network was used.

The fixture is 33,198 bytes, SHA-256
`b7aaa1ea524010a5c59da6a3189302bbc69904a8c3207f6e0f301b9f73092db0`.
Both record and fixture pin the actual arrangement module SHA
`bc77c597b0e58adf14846e1aa31d73c2b3fe9d08f09ac51e2b35049909502e14`
and the existing reference catalog generator's actual SHA. Node tests independently
verify these byte identities, record/fixture relationships and absence of a
production test-fixture import. No Python subprocess is required at test runtime.

Focused Node/Vite SSR checks execute **12 reported cases** (11 subtests plus the
parent): actual DTO admission; exact GET/POST bodies; decimal text rejection;
source/asset/frame/availability/gate tampering; fixed instance validation;
strict empty prepare; wrong-transition/base echo rejection; local invalid-input
no-I/O; in-flight base snapshot/no-op guards; safe HTTP/transport errors; and
abort branches. The first implementation's base-snapshot failure was corrected
by cloning the admitted base before the request. Two unused bindings were also
removed. TypeScript, scoped ESLint and Prettier checks pass after correction.

These are local mocked-transport and source/SSR checks, not live HTTP/browser,
rendering, camera, physical fit or engineering acceptance. Primary owns mounting,
UI integration, designated-browser evidence and publication. Frozen RP1/AD1/D1,
all55 source records, saved drafts, installed source readiness and the five
UNSENT inquiries are unchanged.
