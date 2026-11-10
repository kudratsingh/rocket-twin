# Bounded geometry-reference arrangement packet

**Primary-admitted scope under ADR-0017; strict code contract still required.**
Deliver one separate, unsaved local arrangement of at most one exact nominal tube
reference and one exact nominal aft-annulus reference. The owner explicitly adds
each reference and applies numeric local translation. This is a geometry-planning
increment, with no installed vehicle, physical connection or resolved inventory.
This document records the bounded packet; it does not implement or accept it.

The earlier [scope proposal](../frontend-reference-parts-20261109/next-geometry-planning-scope.md)
is preserved. This admitted packet narrows translation to **±500 mm per axis**
and input granularity to **at most three decimal places in millimetres**. These
are application/input limits only, never manufacturing tolerances or accepted
physical placement ranges. Primary chooses the new independent namespace/API.
Code work starts only after the actual strict backend/frontend contract exists.

## Frozen inputs

Use the current [reference-local-v1 source contract](../frontend-reference-parts-20261109/source-contract.md)
and exact nominal definitions under catalog revision
`8f6b7bf2f0dcc8dfb2714ba7a28688c820869dc3045060aba6ea5901983b7748`:

| Reference ID                             | Definition revision                                                | Exact nominal geometry, mm                             |
| ---------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------ |
| `reference-local-v1:motor-tube-nominal`  | `fd6c666dfed5d79ed44ed126b85d1de7dca87c1210165808b44f270e2ce2a42c` | Outer radius 15.6845; inner radius 14.5845; length 165 |
| `reference-local-v1:aft-annulus-nominal` | `158150615a9c291ce12b3320d535c11151a564d7ad176dda9ca9693025a5d710` | Outer radius 32.2; inner radius 15.95; thickness 6     |

Keep the source config, producer, registered STEP/GLB bytes, local frames,
analytic datum IDs, unknown properties and all old reference readiness flags
unchanged. Reuse the existing asset-byte verification and GLB viewer, extending
only display-instance matrices and necessary arrangement controls. There is no
CAD generation, kernel/solver execution, alternate geometry source or altered
nominal dimension. Source product conflicts and incomplete installed construction
remain visible.

Each planning entry has its own instance identity linked to the exact definition
revision. Quantity is one, scale is one and orientation is fixed to identity.
Only translation is editable. The plan contains at most two entries and no
second copy of either definition. Planning-entry counts are separate from the
unchanged 55-record RP1 ledger; they do not imply 56/57 effective inventory rows.

## Owner path and useful preview

1. Explicitly open the separate **Unsaved local reference arrangement** and
   prepare its empty state. Display exact source identity and the reset-on-leave
   scope. Do not access saved owner UUIDs, metadata history or the draft store.
2. Select one of the two references and press **Add reference**. Add its planning
   entry at [0,0,0]. Loading, selecting or opening a source never adds it
   automatically. Disable duplicate Add with a clear one-per-definition reason.
3. Select a planning entry from a short keyboard-accessible list. Enter labelled
   **Local X / Y / Z translation (mm)** values and press **Apply translation**.
   Each value must be finite, within [-500,500] mm inclusive and have no more than
   three decimal places. The strict contract must specify text/JSON admission
   without rounding invalid input into a valid value. Retain unapplied/invalid
   input separately from the last admitted plan.
4. Inspect the two independent verified solids and use orbit/pan/zoom. Existing
   analytic datums remain in the separate per-reference inspector; this packet
   adds no arrangement datum selection. Fit is explicit. A numeric placement
   update does not reset the camera. Solids may visually overlap; no fit,
   collision, contact, retention, tolerance or compatibility pass follows.
5. **Clear arrangement** explicitly obtains a fresh empty state. It provides no
   saved history, undo or persistence claim. Leaving the arrangement preserves
   the existing source Design scene, selection and camera.

Keep the layout small: source selector/Add, instance selector, three numeric
fields/Apply, Clear, source/limit status and a dominant useful preview. Deeper
provenance may be collapsed while critical geometry-only and unavailable-state
notices remain reachable. No drag authoring, rotation, scaling, dimension edit,
snap, Connect or automatic mate action belongs in this packet.

## Local frame and display matrices

Use an arbitrary arrangement-local front-center origin in CAD coordinates:
X = body +y, Y = body −z and +Z aft. Both references begin in this common local
basis. It is not the installed RP1 nose-tip/station frame, and the source DTO's
`installed_transform` remains null.

The existing verified GLB is already expressed in metres with this mapping:

```text
viewer[X,Y,Z] = [cadX/1000, -cadZ/1000, cadY/1000]
```

For a planning translation `[tX,tY,tZ]` in millimetres, apply only the display-group
translation `[tX/1000,-tZ/1000,tY/1000]`. The same group transform must carry that
instance's analytic datum overlay. Preserve original asset vertices and normals.
Direction vectors receive the axis rotation without millimetre scaling or
translation. Both datum-plane normals remain arbitrary positive-local-axis
conventions, never asserted kernel/outward face normals.

The renderer may clone source scene/object state as needed for independent
planning instances, but must not mutate or reparent loader-owned/shared source
objects unexpectedly. Parent integration owns verified asset loading, resource
lifetime, error containment and camera controls. Fit may use display bounds;
those bounds do not become physical/fit checks. No second source of dimensions
or material properties is introduced.

## Required strict contract before code admission

Primary chooses an independent namespace and local API; existing source-read,
saved-metadata and exclusion-intent contracts remain frozen. The actual contract
must define these minimum elements before implementation:

- A versioned geometry-only plan schema, exact catalog/definition identities,
  distinct planning-instance IDs, fixed quantity/orientation/scale, bounded
  translations and an opaque backend-owned content revision.
- Explicit `add-reference` and `translate-reference` commands,
  their exact allowed fields and base-revision checks. Clear creates a fresh
  empty state. No arbitrary source/asset JSON, URLs, file paths, owner UUIDs,
  definition parameters or unsupported command fields are accepted.
- Trusted backend reconstruction/validation, duplicate/third-entry rejection,
  numeric granularity/bounds, finite-value enforcement and source/asset/frame
  validation. The backend owns hash computation. JavaScript sends compact
  identities/placements and treats Python revisions as opaque.
- A clear state-authority model. If stateless, a reconstructed-state hash checks
  that submitted state; it does not provide an authoritative server head or
  cross-tab saved-state history. Keep one pending command, bind responses to
  their requested local base and reject late mismatched responses.
- Stable safe errors and atomic return behavior: a rejected command changes
  nothing. No automatic retry, source migration, regeneration or fallback.
  Errors retain the admitted plan, current selection and unapplied text.
- Explicit unavailable/null effective inventory, mass, mass credit, CG, inertia,
  fit/physical checks and no connection result. Resolved candidate, simulation,
  engineering, physical and flight readiness remain false. Existing reference
  flags are not rewritten to imply installed Add/Connect capability.

Frontend state should distinguish the admitted plan, selected instance/datum,
numeric text, pending action and safe error. Selection identity includes the
planning instance and definition revision so both definitions' `axis` names
cannot alias. Abort on unmount and disable commands while pending. A changed
source requires explicit fresh preparation; no owner data is read or written.

## Implementation and evidence bounds

Allow **one implementation plus one focused correction**. Primary integrates
source/API/web checks once the bounded implementation is complete. Required
checks should establish the real path and controlling failure, without turning
this packet into an independent review gate or a broad repeat campaign.

The integrated source/API checks must cover empty state, the two Adds, unique
identity/cap rejection, valid translation and exact display mapping; invalid
numeric text/JSON, nonfinite/bound/granularity rejection; unknown fields and
unsupported commands; stale/hash/source/frame rejection; independent returned
state; and unchanged source/asset bytes and null/false gates. Use isolated test
inputs with no saved owner UUID/history or process/kernel/store work.

Web checks must cover strict tiny request/response admission, no automatic
mutation, selected-instance placement/datum coherence, retained text/error state,
abort/late response behavior and unchanged camera/source return semantics where
source-level evidence can establish them. No synthetic, SSR or recorded-readback
check establishes actual native interactions.

Native verification is a **later, fresh bounded packet** with its own explicit
feature/source freeze, cases, action/time limits and sole designated Chrome
owner. It should observe explicit Add, numeric Apply, two-piece visibility,
instance-scoped datum following, explicit Fit, Clear and source return as scoped
by primary. It is not a P87 retry; preserve P87's recorded partial outcome and
all earlier failures. No alternate port/server, browser transport or unsupported
runtime follows from a native block.

## Stop conditions and retained gates

Stop the affected path on source/frame/hash mismatch, missing or unverifiable
asset, invalid plan, an exceeded cap or unexplained failure. Preserve the
rejected state/evidence and use the single focused correction only where its
cause and scope are known. Otherwise report the controlling issue for primary
replanning; do not widen bounds, silently round inputs, borrow assets, regenerate
CAD or change readiness to continue.

There is no physical mating, accepted stock/product, vehicle/source edit,
effective inventory, mass credit, material/strength/fit/engineering/simulation
result, candidate adoption, saved owner history or CAD generation in this packet.
FW2-025 remains a bounded partial capability; interface graph, deterministic
candidate resolution, complete composition persistence and P6 checks remain
separate work. No task or acceptance status is promoted by this plan.

Frozen RP1/AD1/D1 and the 55-record ledger remain unchanged. Dedicated fixed G80
first, separate G54 upgrade/G12 PID-to-RL, five UNSENT inquiries and all purchase,
contact, paid-run, WO-10, engineering, physical/test and flight gates are retained.
Only this plan file is written in the preparation task.
