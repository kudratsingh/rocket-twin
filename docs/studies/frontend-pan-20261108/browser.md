# Move/Rotate and whole-rocket recovery — bounded browser check

The corrected current-window behavior was observed after one normal reload and one correction recheck: **Move translates the scene without changing the camera angles; Rotate changes the angles; Whole rocket returns from a bottom-part close-up to the full overview.** The initial Move failure remains recorded separately.

The sole verifier used the existing authorized Chrome window. This packet had a four-minute cap, with one attempt and one correction recheck. No DevTools, other window/runtime, viewport workaround, simulation, performance attempt or PCB-dialog retest occurred. No user-change guard occurred. Exact CSS viewport dimensions remain unmeasured.

## Initial failure and working close-up recovery

Fresh state showed Move view pressed and Rotate view unpressed. The first ordinary drag from native coordinates [2300,1100] to [2600,1250] changed the actual readout from 45°/54.7°/0° to −15°/24.7°/0°: it rotated despite the displayed Move mode. `before-move.jpg` and `after-move.jpg` preserve this failure. Explicit Rotate then changed the readout to −45°/8.7°/0°.

The source `aft_ring` was selected from the current RP1 summary. Frame selection produced a bottom-ring close-up and declared Aft ring as target. Whole rocket returned the complete rocket to a visible overview, 45°/54.7°/0°, Target: Assembly, while retaining the selected part. `bottom-framed.jpg` and `whole-after-bottom.jpg` preserve that path. This tests the default visible assembly; arbitrary hidden-set preservation was not separately exercised.

## Single changed-source recheck

The primary reported that the gesture binder now takes explicit drag mode and disposes/rebinds on mode changes. After that correction-ready signal, the verifier normally reloaded the same tab once. The original failure was not reclassified as a pass.

- Move was visibly pressed by default. The same ordinary drag translated the scene to the right and down while actual angles remained 45°/54.7°/0° (signed zero may appear). `corrected-after-move.jpg` shows the translated model. The immediate post-reload `corrected-before-move.jpg` was captured before the model finished appearing, so it is not used alone for an object-displacement measurement; the fully rendered Whole overview supplies the visible reference.
- Native wheel input of 0.2 API page zoomed the displaced view. `corrected-wheel-retains-pan.jpg` shows it remains displaced rather than returning to the assembly centre. This is an observed current-window result, not a physical wheel-notch sensitivity measurement or a numeric pan-distance assertion.
- Explicit Rotate became pressed. A real drag from [2300,1100] to [2450,1180] changed the actual angles from 45°/54.7°/0° to 15°/38.7°/0°. `corrected-rotate.jpg` preserves the actual rotated view.
- Whole rocket restored 45°/54.7°/0°, Target: Assembly, with the whole model visible. Move was then selected again. `final-whole-move.jpg` and `final.ax.txt` preserve that final state.

A native element ID expired when Whole rocket caused a render; the failed stale-ID click was not counted as an action. The verifier refreshed supported state before selecting the actual Move control. There was no second correction attempt.

## Final scope and state

Final state: RP1 AD1 v2 and specification `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`, selected `aft_ring` retained, full assembled rocket visible, Move pressed/Rotate unpressed, 45°/54.7°/0°, Assembly target, both panels open, Details visible and tools closed. No source or physical configuration was replaced.

Prescribed responsive sizes, pointer-device sensitivity/latency, right/middle/Shift-drag, arbitrary hidden visibility states and other camera paths remain unexecuted. No FPS or complete frontend/engineering acceptance is claimed. Screenshots are unchanged local-only native JPEGs including Chrome, with no inferred CSS viewport size.

The [session record](../../../runs/frontend-pan-20261108/record.json) contains the exact filesystem-backed capture duration. The [inventory](evidence.json) hashes the record after finalization and excludes itself. Earlier 13/29/9-artifact packets remain untouched.
