# Separate two-reference arrangement display

This standalone display lane implements the geometry viewer from the
[bounded packet](plan.md). Primary owns the strict backend command/hash contract,
API/client, arrangement controls and integrated acceptance. The viewer accepts
already-admitted planning entries; it does not create, place, save or resolve
parts itself.

## Controlled component seam

Default `ReferenceArrangementScene` accepts:

```tsx
{
  instances: DisplayInstance[];
  selectedInstanceId: string | null;
  onSelect: (id: string | null) => void;
}
```

`DisplayInstance` is exported by `referenceArrangementDisplay.ts` and re-exported
from the scene module:

```tsx
{
  id: string;
  definition: ReferenceDefinition;
  translation_mm: [number, number, number];
}
```

Primary maps its admitted plan into this exact display projection. The parent
owns the keyboard instance list, Add/Apply/Clear actions and source API state.
Scene clicks select a known piece through `onSelect`; the scene does not select
on loading or change the parent's plan. A drag beyond two pointer pixels does
not select. Empty-canvas clicks do not clear selection. Parent selection may be
null; an unknown selection ID highlights nothing rather than choosing a piece.

Before loading any asset, `admitArrangementDisplay` checks the complete list:
maximum two entries, unique IDs, one of each exact frozen definition, exact
three-field display entries and three finite numeric translations. IDs are
bounded to 1–100 ASCII letters/digits/colon/underscore/hyphen. Positions must be
within ±500 mm per axis and already expressible with at most three decimals.
Strings, nonfinite values and implicit rounding are rejected. These are display
input limits, not accepted stock tolerances or physical placement bounds.
`admitReferenceDefinition` rejects foreign/revised source, frames, dimensions,
asset identities, fabricated feature data or changed null/false flags.

Display validation does not replace backend state/hash admission. It introduces
no new source definition or interpretation of current readiness. Frozen source
metadata, original unknowns and old source Add-instance/Connect flags stay
unchanged.

## Asset loading and lifetime

One Canvas displays both original GLBs. For each distinct planning entry,
`verifiedTemplateAsset` independently verifies its registered URL/byte count/SHA
before `GLTFLoader.parseAsync` loads the returned bytes. Separate parsing gives
each planning entry its own scene/object resources; no shared loader object is
reparented or mutated. There is no new mesh generation, source material edit,
CAD/kernel call, alternate asset, placeholder or substitute solid.

The instance/source identity keys the loader lifetime. Asset requests have
canonical instance ordering and fixed URL/hash/byte descriptors. Translation,
selection and input-array ordering do not reload scenes. New instance sets may
load/frame afresh. Cleanup aborts pending requests and disposes owned mesh
geometry/material resources; a parse completing after cancellation is disposed.
An error in either asset suppresses the combined preview with an explicit safe
unavailable message. Renderer failure has its own contained unavailable message.
There is no automatic retry or fall-through to borrowed geometry.

SSR renders an empty/loading/error state without a Canvas or asset request.
Actual mounted viewing loads the validated source assets. Browser rendering and
resource cleanup behavior have not been observed by this lane's Node tests.

## Coordinate frame and camera

The scene group is named `uninstalled-local-reference-arrangement`. It is a
separate local planning frame, never the current rocket scene or an asserted
installed transform. Each child uses its distinct planning-instance ID, fixed
identity rotation and unit scale.

For the already metre-scaled source GLB, only the planning group translation is
applied:

```text
translation_mm = [tX,tY,tZ]
viewer translation_m = [tX/1000,-tZ/1000,tY/1000]
```

This preserves the recorded front-center CAD frame and every source vertex.
The tube remains Ro/Ri/L = 15.6845/14.5845/165 mm; the annulus remains
32.2/15.95/6 mm. Their recorded viewer bounds are translated once, without an
extra axis rotation or scale. Exported helper functions provide admission,
translation, per-instance/combined display bounds and instance/source framing
identity. These bounds support selection and camera framing only; they provide
no contact, clearance, fit or physical result.

Normal-flow controls provide Rotate view, Pan view, Fit arrangement and zoom
buttons; wheel/pinch zoom remains available through the existing OrbitControls
pattern. Selection and translation preserve the camera. The framing identity
excludes both, and the Canvas receives a stable initial-camera object. Only an
initial/new instance set or explicit Fit frames current translated bounds;
explicit zoom changes distance around the current target. Fit accounts for the
horizontal and vertical perspective field of view. Pose changes can move pieces
out of view; the visible hint directs the owner to Fit explicitly.

The selected piece receives a source-bound box outline and a small planning-only
callout. Both ignore picking. They do not modify its source mesh/material and
are not added source parts. This lane does not add datum controls; a future
parent-owned overlay would need the same instance translation and scoped IDs.

## Scoped evidence and limits

Seven reported Node tests (one parent and six substantive subtests) pass through
Vite middleware/SSR without binding a listener. They reuse the unchanged actual
Python reference fixture at SHA256
`5db095fc80474ce25b1c0bb70087ca9c49abe4d696227a5b4810e4e6abfcd838`.
They cover actual two-definition admission and original null/false preservation;
translation and source-bound union bounds compared with independent Three
translation matrices; empty/cap/duplicate/granularity/bounds rejection;
source/frame/dimension/asset mismatch rejection; pose-independent framing
identity; and empty/loading/invalid SSR with no request or automatic selection.

The helper tests are **synthetic display checks using actual frozen metadata**,
not new CAD readback, actual native rendering, physical fit or physics proof.
Project TypeScript checking and scoped ESLint/Prettier pass. The existing Three
CommonJS deprecation appears during SSR without failing the tests. One focused
correction stabilizes camera configuration and source-keyed/canonical asset
lifetime across pose/selection/order updates and Clear/new instance sets.

Only the five assigned new display/test/doc files were written. No shared
viewer, producer, asset, source config, owner draft/history or API was edited.
No browser, server, network, CAD/kernel, solver or Git action occurred. Actual
asset-load/render/picking/camera/cleanup evidence belongs to primary integration
and the later fresh bounded designated-window packet. There is no P87 retry.

All effective inventory, mass, mass credit, CG/inertia, mating, material/strength,
engineering, simulation, physical and flight claims remain unavailable or false
under the unchanged source/plan contracts. Frozen RP1/AD1/D1 and its 55 records,
dedicated G80 first, separate G54/G12 PID-to-RL, five UNSENT inquiries and all
existing owner gates remain unchanged.
