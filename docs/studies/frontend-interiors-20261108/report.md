# Easier interior inspection and source-supported detail

This follows the owner's request for easy drag/zoom, more useful internal geometry, accessible controls and alternative inspection. It continues from merged PR98–100 and frozen G80-F2-RP1-AD1-definition-v2. G80 custom construction remains first; G54 and G12 PID-to-RL stay separate committed tracks.

## What is usable

- A normal-flow inspection bar contains Inspect interior, direct Motor/Recovery/Avionics/Fins selection, source-detail coverage and Fin alternatives. Interior entry hides source-labelled outer shell/nose rather than relying only on transparency. Subsystem selection frames supported parts. Restore visibility returns the saved hidden/display set and fits the visible assembly, retaining the current camera basis.
- Direct manipulation distinguishes click jitter from actual orbit, normalizes wheel/pinch units and avoids conflicting hover/pick handling. Labelled Zoom, Fit, Frame and Reset remain visible. A diagnosed empty-selection fit bug is fixed: leaving a subsystem cannot retain an empty target and leave the restored body cropped.
- All26 core source primitives were missing normals. Private render geometry gains normals while preserving positions/indices/bounds and original source GLBs. Lighting, highlights and depth precision are improved. This is a rendering correction, not extra manufactured detail.
- Three optional source-supported detailed meshes refine the forward-ring passage/annulus and its recorded6mm /0.2mm /6mm stock/bond distinction, motor-tube bore/wall and aft-ring annulus. Their separate revision is `e4ff19fec90e36d2a97987387572749cf3e11449312d09b3cf7e1c8d15016238`. [The catalog](../frontend-design-ux-20261108/detail-catalog.json) audits all26 original assets; [the report](../frontend-design-ux-20261108/detail.md) identifies exact sources and missing features. Greater tessellation does not qualify a material or installed joint.
- Fin alternatives now include a separate rotatable one-fin construction schematic. AD1, carbon-faced plywood FP1 and solid-carbon FR1 use recorded planform/tab/thickness dimensions; FP1 can separate the core, adhesive and carbon faces for explanation. The proposed nominal film basis and exaggerated layer spacing are explicit. This preview does not replace the active vehicle or claim a complete replacement assembly/attachment.

## Geometry and evidence boundaries

The core inspection geometry remains `238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`; all55 stable part IDs and frozen AD1/D1 source records remain unchanged. Detail assets are optional, separately hashed and bound to the exact active source/core tuple. Their manifest and actual asset bytes are checked before use. Missing/incompatible detail leaves the core view available.

Twelve box envelopes have only12triangles each because the source supplies bounding dimensions. PCB components/ports, retainer cap/threads/seat, finished rope/knot topology and unspecified roundovers remain unavailable. Rendering polish does not manufacture those facts. Electronics stay visibly labelled envelopes. Finished FP1/FR1 CAD, installed strength, total attachment movement, heat and flutter acceptance remain open; no rejected construction is adopted.

## Preparation and verification

`make preview` explicitly prepares optional detail assets after the core display export. The fin-only schematic data is a tracked, reproducible export from `scripts/wo04_fin_visuals_export.py`; it carries source hashes and uses no browser physics. All computation/engineering findings remain backend/offline records.

Source checks: combined frontend tests, strict TypeScript, lint, formatting and production build; camera/gesture/normals/depth regressions; optional detail identity/actual-asset tests; interior visibility state tests; and recorded fin-export checks. Actual browser observations are recorded separately in this directory. The earlier exact responsive viewport matrix remains unavailable under the existing DevTools rejection; no workaround or inferred viewport measurement is used.

All five supplier/lab drafts remain UNSENT. No purchase, physical work, paid compute, material/load relaxation or engineering/build/flight acceptance follows from these changes.

## Recorded outcomes and limitations

Combined localfrontend202tests pass (four preserved/unpublished A2 cases;198 in this publication), typecheck/lint/format/build pass. Five Python source-detail/fin-export cases pass locally; the actual optional-asset test explicitly skips on hosts where optional local assets have not been prepared. No hosted actual-mesh validation is inferred from that skip.

The [integrated browser report](integrated-observation.md), [scoped results](integrated-results.csv) and [gallery](integrated-gallery.html) contain23 fresh captures and two AX records. The29-artifact inventory is hash-verified separately from the immutable13-artifact baseline. Current-window internal entry/subsystem framing, source-detail toggle, ring inspection, actual orbit/zoom, fin construction/layer switching and modalReturn/Escape were observed. The clipped return bug and corrected whole-assembly view are retained as separate evidence. No physical wheel-notch, quantitative FPS or prescribed viewport result is claimed. The final preview-first/collapsed metadata ordering and selected-label wording are source-only refinements after capture.

The final confirmed app is RP1 assembled,26/26 meshrecords visible, no individualpart inURL, Motor group highlight retained, interioroff, sourcedetailon, bothpanels/Parts open, tools/dialogclosed and Reset+Fit45/54.7/0 withAssemblytarget. No further owner coordination or backend restart is needed for this checkpoint. Unknown manufacturer/component geometry remains explicitly unavailable; all engineering/build/flight gates stay open.
