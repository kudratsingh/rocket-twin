# Accessible grouped inspection controls

The owner screenshot identified a mixed, crowded source-control row and floating
camera controls near its right edge. The new layout reserves actual space above
the scene, uses labeled groups and wraps within available width. Existing source
identities, geometry, physics and control callbacks are unchanged.

- View:3D model /2D dimensions.
- Inspect: interior/restore visibility, internal assembly, section adjustment.
- Source: optional source detail and coverage; Alternatives stays separate.
- Mouse: Move view / Rotate view.
- Frame: Whole rocket, Fit assembly, Frame selection.
- Zoom: direct in/out buttons.
- Display: Scene tools entry and Restore assembly.
- Views: camera presets, exact angles / keyboard pan, framing guide and reset.

Display tools and Adjust section cut expose the existing Scene tools drawer,
including transparency, wireframe, balance markers, part labels, section-plane
settings, source dimension selection and display breakdown. Camera menu links
directly to exact camera angles and keyboard pan. The duplicate primary Reset
view button is removed; the existing Whole rocket and camera-menu reset remain.

Normal-flow groups replace the absolute controls that competed with the scene.
Source coverage is bounded to the viewport and scrolls. Source and Camera menus
close with Escape. Larger focusable targets, explicit group names and distinct
pressed/expanded states support keyboard and pointer use.

## Run and inspect

The existing preview is http://127.0.0.1:5173/ . When stopped, use `make preview`
from the repository root; no backend restart, setup or CAD regeneration is
required by this frontend-only increment.

## Evidence boundary

Local type/lint/build/format and grouped-control/source tests are supporting
evidence. [Native readiness](browser-readiness.md) and the designated browser
record are separate. [P69–P70 browser observations](browser.md) verify readable groups and model
visibility with the drawer open/closed and sidebars shown/hidden at the actual
authorized window size. Camera menu opens its complete exact-angle/pan form;
source coverage is bounded and scrolls. Display tools opens the drawer, Adjust
section cut opens the real plane settings, and section-off/Restore assembly plus
Move/Rotate state changes work through actual controls. Whole rocket, Zoom in
and Fit assembly were executed.

P69's native stepper setter did not confirm the requested45value (the retained
AX value was absent); Apply was not clicked. Numeric entry is unverified, not
a camera-math failure. P70's one drawer page-scroll skipped the middle section
fields in screenshots; AX lists the controls but full field pixel legibility is
partial. Optional preset/source-checkbox activation was unexecuted. No new
WebGL lifecycle-instrumentation or responsive matrix claim is made.

Actual captures: [whole model and groups](../../../output/frontend-control-layout-20261109/P70-final.jpg),
[camera form with tools open](../../../output/frontend-control-layout-20261109/P69-camera-form.jpg),
and [collapsed sidebars](../../../output/frontend-control-layout-20261109/P69-sidebars-collapsed.jpg).
Both native packets ended within their declared budgets (167.313/180 and
74.252/90 seconds). Browser ownership is idle; the permitted window is free. No viewport, zoom, FPS, mobile or physics claim
is inferred from CSS or static markup. Broader workbench acceptance and every
engineering/build/flight gate remain open.

## Supporting checks

349 local web cases pass, including four preserved/unpublished A2 cases
(345 in publication scope). New grouped-control tests and relevant existing
Design/interior cases pass10/10. Typecheck, lint, production build and formatting
pass. Required hosted results must be associated with the exact published head.
No generated CAD, native image/AX bulk, unrelated A2 changes or dependencies
are included in the focused publication.
