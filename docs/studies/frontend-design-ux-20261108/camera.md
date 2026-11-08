# Design camera and display-transform source packet — 2026-11-08

The viewport now exposes Orbit / camera, an actual angle/target readout and a
compact gesture hint with Scene tools closed. Numeric fields provide keyboard
access to horizontal rotation, full nose-to-aft tilt including both poles, and
view roll. Fit assembly, Frame selection and Reset camera remain distinct.
This packet establishes source/math/SSR behavior; designated-browser interaction,
layout and clipping observations are separate acceptance evidence.

## Axes and actual camera state

CAD/inspection axes are unchanged: +Y points to the nose. Horizontal angle0°
places the camera on the +Z side of its pivot; +90° places it on +X. Horizontal
angles are unwrapped across360° turns. Tilt0° looks from the nose end;180° looks
from the motor end. Roll follows a right-hand rotation about the target-to-camera
axis. A stable horizontal-angle-defined up basis at either pole avoids an
undefined cross product. The actual camera quaternion/position are read back
into the visible fields after each operation. Manual orbit, pan, zoom, roll or
numeric angle application reports Custom; preset selection reports its shortcut
name. A readout cannot leave the previous preset marked active after manual
rotation.

The native canvas controller replaces the inspection OrbitControls wrapper to
support explicit roll and exact vehicle-axis poles without a world-up polar
clamp. It does not replace the renderer, GLB pipeline or replay camera. It uses:

- Left drag / one-finger drag: orbit, with continuous horizontal rotation.
- Right drag or Shift-drag: pan in the current rolled viewing plane.
- Alt-drag: roll about the viewing axis.
- Wheel or trackpad scrolling: zoom.
- Two-finger touch: pan and pinch zoom.
- Numeric angle fields, Apply camera angles, ordinary zoom controls and four
  keyboard pan buttons provide alternatives to dragging.

The controller listens only on the canvas, not global keyboard events. Pointer
capture is released on up/cancel/lost capture; unmount removes listeners and
restores the prior touch-action style. Angle form editing is independent of the
live readout and only Apply/Enter changes the pose. Empty/nonfinite angles and
tilt outside0–180° produce an error. No dependency or source configuration was
changed.

## Framing, targets and manual clipping

The existing `fitOrbitFrame` fixed-basis perspective fitter is retained unchanged.
Fit and Frame use the actual direction and up basis, including roll. Reset uses
the recorded Overview shortcut. The existing initial-fit and explicit-command
sequence remains bounded; panel changes and selection alone do not reset a
manually chosen angle. Manual poses and their pivot remain through canvas
resizing. Nonmanual fit intent may adjust distance after resizing while retaining
its chosen viewing basis.

The explicit target chooser recenters on loaded assembly or selected group/part
bounds without changing angle or distance. The actual named target is retained
in the readout. A later meshless selection cannot relabel or move the retained
geometry pivot. Group selection arrives through optional Viewer `selectionIds`
and `presentationGroupId`; a store group Frame command targets those loaded
members, while Fit assembly remains explicitly assembly-scoped. A selected pivot
follows its display translation on breakdown/restore while retaining its lateral
fit/pan offset and orientation.

Near/far planes are refreshed from current loaded conservative mesh bounds after
manual orbit, pan, numeric angles and zoom. Tests cover assembly and small-part
scales, close zoom and pullback. They establish valid perspective depth planes,
not that a camera moved inside a solid can see its hidden/behind-camera surfaces.
The source scene, material estimates and engineering readiness are unchanged.

## Source-pinned breakdown integration

`rp1BreakdownOffset` from the separate mapping lane supplies the final display
translation for source tuple inspection geometry
`238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`.
The same final vector is used by mesh drawing/picking and cached bounds used for
framing/pivots. `RecordedMeshBounds.displayOffset` is applied exactly once;
archived configurations retain their existing `explodeOffset × separation`
behavior. Zero RP1 separation returns source placement. No RP1 fallback based
on inferred geometry is introduced.

Transform updates refresh cached bounds without reloading source assets or
disposing their materials; materials are disposed only when their scene leaves.
Group selection highlights its supported solids without adding a label to every
member. Meshless Scene-tools Isolate is disabled; exit-isolate remains available.

Assembled / Breakdown / Section controls are beside the viewport. The caption
explicitly says the first half separates six functional groups and the second
half opens only the selected named group. With no group selected it says no
detailed group is chosen and directs selection in Parts. Display separation is
an illustration, not a physical assembly sequence, joint clearance or acceptance.

## Validation

The targeted camera/scene suite passes14 tests: existing fit/clipping/scene
regressions plus five new camera/transform/UI tests. Independent Three camera
projection checks rolled Fit/Frame corner coverage and positive near/far support;
angle tests cover multiple turns, both exact poles,15° roll and pan. Additional
bounds tests prove final RP1 translation is not multiplied again and zero returns
source bounds. SSR checks actual Custom readout, numeric labels, explicit target,
keyboard pan buttons and the visible gesture hint. Web TypeScript and lane
ESLint pass. No browser, simulation, CAD generation or source-identity mutation
was performed by this lane.

The sole authorized verifier must still observe full rotation, numeric
35°/25°/15°, actual Custom state after drag, precise end-on views, small-part and
group targets, close/pullback clipping, panel-width preservation, pointer/touch
behavior and breakdown picking/framing. Existing frontend and engineering/
physical/build/flight gates remain open. All five inquiry drafts remain UNSENT.

### Integrated visual correction

Actual native-window observations found overlap with representation tabs and selected-part actions. Assembly display modes were moved into the existing Scene tools drawer, with their explanation in a details disclosure. Camera/gesture controls remain visible with tools closed. The selected-part summary's owning stylesheet now keeps it above the camera readout. Native captures show both areas clear after correction; exact responsive sizes remain unverified because automatic approval review rejected DevTools opening. See the integrated report for the preserved failed observations.
