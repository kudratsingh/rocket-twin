# P8 Replay Scene + telemetry results

The functional packet completed in **452.815 active seconds** against 480. At **2240×1109 CSS pixels**, the actual scene, core time controls and four plots are simultaneously readable. Bounded saved-data time/cursor/channel controls, pair alignment/range and explicit state retention through one native tile/restore worked. The narrower centre stacks as intended, but lower-four-plot scroll reachability was not established by its one scroll capture. An aligned-clock HUD copy ambiguity is retained below. No Play or performance profile was started.

The base PR107 is merged at `e7a62a7baa619aa3b7940a80dce17e11607b536c`; this NEW layout was separately local/frozen at capture. Exact Experiment/CSS/App fingerprints are in [source-freeze.json](../../../runs/frontend-replay-layout-20261108/source-freeze.json). Tests/build and merged base are not browser/FPS acceptance for the local increment.

| Case | Actual observation | Outcome |
| --- | --- | --- |
| Single wide layout |Saved G80 `exp-cf9e47a650074144856caf50775846d2`, bounded 3009/116029 rows; scene/time/four plots readable together in fresh capture. |Passed current-window branch |
| Exact/cursor/channel |Exact 11.150 gives nearest 11.143 readouts; plot click jump 57.947 then Right →59.10757/shared readouts59.117. Offered `thrust_n` plot selected with N unit. |Passed |
| Existing compatible pair |A `exp-d0baf4168f7f41e687a1b5f12e14cc3e`, B `exp-d57656d638d5412d95b03198e9fb73d7`; live admitted 3004/9000 each. Burnout offsets1.8079 s; Zoom range9.446–31.943; exact aligned20. |Passed |
| Native resize/restore |Observed Window →Move & Resize →Left once and Fill once. App diagnostics measure 2240×1109→1120×1109→2240×1109 CSS, DPR2. |Passed sizing/explicit fields |
| State retention |Both actor IDs, time20, thrust_n, Camera: free, burnout alignment and range retained. |Passed explicit fields; numeric camera pose not measured |
| Stacked centre |At1120 viewport, canvas655.40625 CSS wide; telemetry below scene. The one scroll image still shows only top plots, so all lower plot reachability is not established. |Partial, no retry |
| Disclosures/warnings |Comparison controls, Source identity and sampling interpretation reached. Partial Tiny landing missing/attitude limits visible, no extrapolation/physics invented. |Passed reached branch |
| Clock HUD wording |HUD says T+20.000 while core field/plots say Aligned20 and validity requests21.808 after offset. |Copy ambiguity; no numeric clock failure inferred |
| Restore |Canonical RP1 Design, no run/compare/part, whole26/26, Assembly45°/54.7°/0°, Move on, Parts/both panels open, tools closed,Frame disabled. |Passed |

All three actual UI diagnostic downloads have **zero RAF intervals**, `unavailable_or_invalid` frame status and null profile. They were used only to read actual CSS/canvas/source state. They do not establish FPS, representative render performance, load/scrub thresholds, memory endurance or60 fps acceptance. Earlier failed/offscreen performance evidence remains unchanged. Each download was copied byte-identically with original filename/mtime/hash retained.

The wide canvas is754.7421875×397.234375 CSS pixels; tiled is655.40625×397.234375. The centre-container760 threshold differs from whole-viewport900. Actual1120 is not a substitute for required1280/900/1440. Native wide4480×2460/tiled2240×2460 JPEGs include Chrome; content dimensions come from the app, not raster inference. A parent submenu click dismissed the native menu; reopening and choosing the explicitly observed Left child performed the sole tile. There was no edge/keyboard toggle, alternative resize method or second tile attempt.

Free camera label persistence establishes the mode only. The packet did not inspect driver state or establish numeric orbit/pivot persistence. Exact aligned20 corresponds to absolute21.8079 s; nearest sample21.815 s remains separately labelled. The two Tiny seeds differ20261107/20261108; source compatibility does not make them an equal-seed experiment. Thrust0 N is an actual zero readout, not a missing-value substitution. Incomplete trajectories explicitly have no recorded landing.

The [session record](../../../runs/frontend-replay-layout-20261108/record.json) retains the actual sources/cases/limits and final state. All captures are fresh unchanged native JPEGs. CUA ended after final RP1 capture; no source/runtime changes were made by this agent. The prescribed-size matrix, numeric camera-pose retention, lower stacked plots reachability and performance/engineering/physical/flight gates remain open.
