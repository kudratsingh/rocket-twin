# Fin attachment inspector navigation contract

The focused fin/root/body/motor inspector is a Design overlay for current RP1/AD1 v2. `web/src/fin-attachment/finAttachmentState.ts` owns its pure local and route state. The state is source-bound to configuration `G80-F2-RP1-AD1-definition-v2`, specification SHA `811b3bed…1660`, and inspection geometry SHA `238d01e5…b608`. It admits only the nine current-source part IDs used by the close-up. It adds no vehicle part, physics, mass, material property, installed-joint pass, or manufacturing claim.

## State and links

`initialFinAttachmentState` starts assembled, with no selected piece/dimension, no isolation or hidden piece, both sidebars open and no saved inspector camera. `FinAttachmentState` carries those values, a section (`assembled`, `longitudinal`, `transverse`), and an optional finite camera snapshot (position, target, up, positive zoom). The camera is local/session state under `finAttachmentSessionKey(originPartId)`; the URL never encodes inferred or giant camera coordinates. `parseFinAttachmentCameraSnapshot` rejects nonfinite/degenerate values before reuse.

`finAttachmentHref(href, state, originPartId)` emits a Design link with exact `design`, `spec`, `part`, `finJoint=1`, `jointOrigin`, `jointGeometry`, `jointSection`, optional `jointPiece`/`jointDimension`, visibility arrays and sidebar flags. `parseFinAttachmentHref` rejects duplicated or conflicting source/query values, invalid sections, unknown parts/dimensions, duplicate or overlapping visible/hidden selections, and wrong RP1 identity. A route parser returns `null` on mismatch so the caller can show unavailable state rather than silently resetting to another design. Only recorded dimension IDs may be used when the final catalog is pinned.

`openFinDrawingHref(href, state, originPartId, 'root' | 'loadpath')` retains this inspector route and opens existing Engineering `rp1-connections`, `connection=fin-root`, with the requested drawing focus. `returnFinJointHref(href)` restores Design and the original `jointOrigin` part even if Engineering selected another RP1 graph part. The Engineering drawing itself remains the existing source-pinned root/load-path record; the inspector does not create a new drawing or strength result.

## Primary integration points

- The explicit **Inspect fin attachment** action should open the overlay and keep the main rocket pose as an actual camera snapshot. Existing `web/src/fin-attachment/mainCameraCheckpoint.ts` is a separate parent-owned main-scene capture. Closing the overlay or returning from Engineering should restore that captured main pose, not reconstruct it from a named view or display angle.
- `web/src/workbench/EngineeringWorkbench.tsx:68` already validates RP1 `design/spec/part/connection`, and its `rp1-connections` path begins near line 228. `web/src/workbench/workbenchRouting.ts:35` preserves unknown route parameters while changing Engineering topic. The parent should show a strict return action only when `parseFinAttachmentHref(currentHref)` succeeds.
- `web/src/workbench/Rp1ConnectionsView.tsx:386` currently uses `rp1ConnectionDesignHref`, which creates a fresh Design link and drops the joint state. Keep that general link for ordinary connection inspection, and add or replace the contextual return action with `returnFinJointHref(currentHref)` when the exact joint route is present.
- `web/src/workspaces/partLinks.ts:33` preserves unknown parameters on general part navigation. The parent should intentionally close or preserve the joint route when changing parts; a stale joint overlay must not auto-open for a foreign source.

## Checks and limits

Focused tests cover exact Design→Engineering→Design section/part/visibility round-trip, restoration of the original part after an Engineering selection, duplicate/stale/unknown-ID rejection, and finite camera validation without URL camera data. Source/type checks are not native verification. The designated browser owner still needs to observe actual overlay opening, section and dimension selection, selected camera return, root/load-path navigation, and restoration to the same RP1 part and main pose. Preserve failures if any; do not infer engineering or physical acceptance from route success.
