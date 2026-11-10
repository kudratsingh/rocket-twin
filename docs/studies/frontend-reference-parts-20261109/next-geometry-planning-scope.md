# Proposed next increment: unsaved local reference arrangement

**Proposal for primary admission, with no implementation or acceptance change.**
Add one separate, unsaved geometry preview in which the owner can explicitly
**Add reference instance**, select that planning instance and enter its local
X/Y/Z translation numerically. Bound the first packet to at most two planning
instances: one exact nominal tube and one exact nominal aft annulus, quantity one
each, both retaining their original orientation. This makes a useful two-piece
arrangement possible without changing dimensions, invoking CAD or pretending the
pieces have been joined.

Current source is sufficient for this narrow geometric display. It is
insufficient for an installed part, stock selection, mating/fit judgment,
replacement, resolved inventory, mass/CG/inertia result or experiment. The
proposal introduces no new vehicle and leaves source definitions, all current
readiness flags, saved metadata drafts, the 55-record RP1 ledger and physical
sources unchanged. Primary decides whether to admit this bounded scope; this
note supplies implementation input and adds no independent review gate.

## Relationship to the current plan

[ADR-0017](../../adr/0017-parts-bank-and-detailed-design-workbench.md) permits
validated separate draft part/placement authoring while preserving frozen sources
and backend ownership. Its distinction between definition, occurrence,
connection, representation, draft and resolved candidate is essential here.

The [current P5/P6 backlog](../../frontend-design-workbench-v2/backlog.json)
records FW2-024/025/028 as partial: metadata fork/save/history and source
exclude/restore intent exist, with full composition and resolution still open.
FW2-026/027/029 and FW2-030–033 remain planned. The matching
[acceptance matrix](../../frontend-design-workbench-v2/acceptance.csv) leaves
FW2-A19 partial and FW2-A20–24 planned.

This increment would supply a small geometry-planning portion of FW2-025's
explicit Add and placement interaction. It does not complete that task's hardware,
required systems, quantity/parameter breadth or undo contract. It does not satisfy
FW2-026 contact/connection, FW2-027 candidate resolution, FW2-028 composition
persistence, FW2-029 candidate comparison or any P6 calculation criterion.
Neither overlapping solids nor a visually coaxial arrangement changes those
statuses. Existing partial native datum evidence is not reused as acceptance of
new placement controls.

## Frozen input and its limits

Use exactly the definitions from
[reference-local-v1](../../../configs/parts-bank/reference-local-v1.yaml) and the
[source contract](source-contract.md), under catalog revision
`8f6b7bf2f0dcc8dfb2714ba7a28688c820869dc3045060aba6ea5901983b7748`:

| Definition                               | Definition revision                                                | Nominal radius/length inputs, mm |
| ---------------------------------------- | ------------------------------------------------------------------ | -------------------------------- |
| `reference-local-v1:motor-tube-nominal`  | `fd6c666dfed5d79ed44ed126b85d1de7dca87c1210165808b44f270e2ce2a42c` | Ro 15.6845; Ri 14.5845; L 165    |
| `reference-local-v1:aft-annulus-nominal` | `158150615a9c291ce12b3320d535c11151a564d7ad176dda9ca9693025a5d710` | Ro 32.2; Ri 15.95; L 6           |

The source already supplies exact asset identity, recorded nominal geometry,
front-center local frames, analytic datums and explicit geometry-only scope.
Render the existing verified GLBs and move independent display instances using
rigid group translations. Reuse the unchanged registered STEP/GLB bytes. Missing
cache or failed public-byte verification makes that display unavailable; there
is no regeneration, alternate cache, installed-mesh substitute or guessed guide.

The tube product/dimension conflict and incomplete installed annulus proposal
remain visible for every planning instance. Material qualification, stock
identity/tolerances, mass, procurement cost, inertia, thermal capability and
strength allowables stay null. Interfaces and physical connections remain null.
All current Add-instance API/Connect, candidate, simulation, engineering,
physical and flight readiness flags remain false. The new action means adding
an entry to a separate geometry plan; it does not rewrite the existing source
DTO's `add_instance_api=false` or its inspection result's
`instance_created=false` into an installed-part capability.

## Smallest useful owner path

1. Explicitly open **Local reference arrangement — unsaved geometry only**.
   Prepare an empty plan from the exact current reference catalog. Show its source
   identity and that leaving the page or preparing afresh discards the plan.
2. Select either of the two source references. Show the fixed nominal dimensions
   and source limitations, then explicitly **Add reference instance** at the local
   preview origin. Never add automatically on selection or load. Once added,
   disable another copy of that definition and explain this packet's one-each cap.
3. Select a planning instance from a short keyboard-accessible list. Edit labelled
   **Local X / Y / Z translation (mm)** fields and press **Apply placement**.
   Keep invalid or unapplied numeric text distinct from the last admitted
   placement. No slider, drag authoring, snap, datum-mate, angle or dimension edit
   is needed for this packet.
4. Inspect both independent solids, select either instance/datums, explicitly Fit
   the arrangement and use the existing orbit/pan/zoom controls. Allow ordinary
   visual overlap without a pass/fail color or compatibility claim. The preview
   caption says no mating, tolerance, contact or collision check has run.
5. Explicit **Clear unsaved arrangement** returns to a newly prepared empty plan.
   This is a reset, with no undo/history/persistence claim. Returning to the main
   source Design preserves its existing selection and camera state.

The arrangement origin is an arbitrary local preview origin. Define its axes as
CAD X/Y/Z with the two references initially sharing the same front-center basis;
+Z runs aft. This is not a nose-tip station or an installed RP1 coordinate system.
For the first packet, permit finite translations in [-1000, 1000] mm per axis,
with strict backend validation. This proposed bound limits UI/render extent and
payloads; it is not a physical clearance, accepted placement range or tolerance.
Orientation is fixed to identity, scale is fixed to one and quantity is fixed to
one. A later need for rotation or duplicate quantities requires its own scope.

For a source-local CAD point `p` and planning translation `t`, display the point
as `viewer(p + t)`, using the existing exact mapping:

```text
viewer[X,Y,Z] = [cadX/1000, -cadZ/1000, cadY/1000]
```

Equivalently, translate the already metre-scaled local GLB/group by
`[tX/1000, -tZ/1000, tY/1000]`. Put that instance's datum overlay under the same
group transform. Directions only rotate axes; translation and the millimetre
scale do not modify their dimensionless values. Plane normals remain the
arbitrary positive-axis convention, never asserted kernel/outward normals.

## Minimum backend seam

Introduce an independent geometry-plan schema and pure functions, rather than
extending the frozen saved-metadata or exclusion-overlay contracts. Suggested
operations are `create_geometry_plan(verified_catalog)` and
`apply_geometry_command(plan, command)`. A later thin local API wrapper may expose
these stateless functions under a separate reference-preview namespace. Endpoint
names are for primary to decide; no existing draft UUID or owner library access
is needed.

A plan needs schema/kind, exact catalog and definition revisions, its own opaque
Python content revision, and at most two ordered planning entries. Each entry
has a distinct planning-instance ID, exact definition ID/revision, fixed
quantity/orientation/scale and three finite local translation values. Keep the
render list separate from `effective_inventory`, which stays null. A count of
two planning entries is never a 57-record RP1 accounting inventory. Preserve
source provenance/limitations by exact definition links and trusted server DTOs.

Only two commands are required:

| Command                   | Minimum validated inputs                                                                              | Result                                                                                 |
| ------------------------- | ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `add-reference-instance`  | Exact base plan/catalog revision and one allowlisted definition ID/revision                           | Add one quantity-one planning entry at [0,0,0]; reject a duplicate or third entry      |
| `set-reference-placement` | Exact base plan revision, known planning-instance ID and three bounded finite `translation_mm` values | Replace only that entry's planning translation; preserve all definition/asset identity |

Assign instance identity from the validated plan in Python; a deterministic
one-per-definition namespace is enough for this cap. Never accept a filesystem
path, arbitrary asset URL, complete client definition/source, replacement
hardware, caller-chosen UUID, orientation, scale or geometry parameters. Unknown
keys/types/IDs, duplicate entries, unsupported commands, malformed/nonfinite
numbers and stale source/revision identities fail without changing the plan.
Reset can call `create_geometry_plan` explicitly, so a third mutation command is
unnecessary.

If the API is stateless, accept only a bounded compact prior-entry list plus
opaque base hash and the new command. Reconstruct the prior plan from trusted
catalog definitions and validated placements, check its Python hash, then apply
one command. JavaScript must not hash full floating-point source DTOs. This
checks the submitted state's identity; it does **not** establish an authoritative
server head or cross-tab concurrency history. Do not advertise persistent stale-
write protection. Keep one pending command per UI plan and reject a late response
that no longer matches its requested local base. A changed catalog must stop the
plan until explicit fresh preparation; no automatic migration or retry.

The response can expose independent geometry-planning operations without changing
source readiness. It must retain unavailable/null mass, credit, CG, inertia,
physical/fit checks and effective inventory, with false resolved/simulation/
engineering/physical/flight gates and explicit no-connection blockers. No prior
RP1 result attaches to a placement, and no calculation is launched. P6
invalidation remains a future contract: there are no admitted plan results here
to relabel as current passes.

## Minimum frontend state and render seam

A standalone arrangement component owns `{plan, selectedInstanceId,
selectedDatumId, placementText, pending, error}`. Only explicit commands replace
its admitted plan; errors retain the current plan, selection and numeric input.
Abort on unmount, disable mutation while pending and label the page unsaved.
Parent source changes require explicit fresh preparation. No local-storage,
Saved drafts write, reviewJSON import, export or source replacement is needed.

Reuse `referencePartsClient` for live source detail and its existing strict
`admitReferenceDefinition` admission. Verify every rendered GLB with the current
asset-byte verifier, not availability alone. The arrangement renderer accepts
only an admitted plan and its matching verified local asset scenes. A rendering
entry becomes a distinct R3F group, with its own scene/object state and the
recorded definition link; do not mutate/reparent a loader-owned shared scene
object across instances or alter source materials. Parent integration owns
resource lifetime and a boundary for unavailable assets.

Use one separate arrangement Canvas and controls, or an existing local-preview
Canvas adapted by primary. Never insert it into the mounted source Design scene.
Numeric placement changes only the selected planning group; camera reset is
explicit through Fit. Source/datum selection stays scoped by
`{planning_instance_id, definition_revision, analytic_feature_id}` so both
instances' `axis` IDs cannot alias. All geometry is display-only; a scene bounds
calculation for Fit is not mass/fit/physical analysis.

## Bounded implementation evidence to request next

A single implementation packet plus one focused correction is enough to test:
trusted empty-plan creation; the two explicit Adds; duplicate/third/foreign
rejection; valid numeric placement; malformed/nonfinite/out-of-bound rejection;
opaque revision and stale catalog failures; independent return values; retained
unknowns/gates; no store/process/kernel calls; and unchanged registered asset
bytes. Frontend tests should cover exact tiny request shapes, instance-scoped
selection/transforms, safe errors/abort, retained numeric text and no automatic
mutation. Existing producer/definition byte pins must remain unchanged.

A separately bounded designated-window packet would then observe Add, numeric
Apply, two-piece visibility, one datum following its selected instance, explicit
Fit and clean source return. Current native evidence cannot supply that proof.
Any source/frame/asset mismatch stops the affected display without a new geometry
or server workaround. No solver/kernel/vehicle variant, source dimension change,
readiness promotion or physical action belongs in this packet.

No backlog, acceptance status, producer, code, saved draft or physical source was
changed while preparing this note. Frozen RP1/AD1/D1, dedicated fixed G80 first,
G54 upgrade/G12 PID-to-RL, all five UNSENT inquiries and existing engineering,
purchase, physical/test, paid-run, WO-10 and flight gates remain unchanged.
