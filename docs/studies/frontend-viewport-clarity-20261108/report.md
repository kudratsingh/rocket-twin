# Viewport helper: information, not a resize control

The owner reported that Zoom had no percentages and choosing the pixel count did not change the window. The old helper used a Requested size selector that changed only its comparison target. It never resized Chrome. That affordance and the repeated manual pixel-matching request were confusing.

## Correction

The development-only helper now displays actual content width/height and device-pixel ratio. Reference sizes are static in a disclosure; there is no select/input pretending to resize the browser. Matching dimensions alone explicitly do not establish layout acceptance. It says the owner can use a comfortable window size, explains the three zoom scopes and retains a single Hide action. No resize/zoom protocol, new package, simulation, geometry or camera change.

Chrome page zoom belongs to its upper-right menu. On Mac, Command+0 resets page zoom to its default; this is not a guarantee that an independently configured default is100%. Official sources: [page zoom](https://support.google.com/chrome/answer/96810?co=GENIE.Platform%3DDesktop&hl=en), [Mac keyboard shortcuts](https://support.google.com/chrome/answer/157179?hl=en). Rocket Zoom in/out changes the3D camera; the previously observed macOS Window→Zoom changes window bounds without a page-zoom percentage.

## Evidence and scheduling

The updated SSR contract checks actual versus reference dimensions, no select/input, explicit non-resizing and no automatic acceptance. TypeScript verifies that the removed target/onTarget interface has no production callers. Native P13, after the owner's fresh Ready, completed33.601s inside90native/120overall: actual2240×1109CSS/DPR2; static reference sizes/cannot-resize wording/Hide observed; normal RP1 Design remained usable with its existing Custom30.3°/72.1°/0° Assembly camera.100% page zoom is owner-reported, not independently verified or inferred from DPR. [Native record](browser.md).

Do not ask the owner to match pixels as a prerequisite for ordinary inspection or unblocked development. Use supported available sizes and report them exactly. The prescribed1440×900,1280×720 and900×720 cases remain unchanged and pending; no fixture substitution, threshold relaxation or pass follows. A supported precise-size verification method is a separate coordinated prerequisite. Preserve the earlier measurements and rejected DevTools route; no alternate driver/window bypass.

The prior owner-action sheet and selector screenshots remain historical evidence. This note supersedes the request to manipulate that selector or pursue manual matching now. Source/code checks are separate from native observations; neither closes engineering/build/flight acceptance. RP1/AD1/D1, G54/G12 PID-to-RL and allfiveUNSENT inquiries are unchanged.
