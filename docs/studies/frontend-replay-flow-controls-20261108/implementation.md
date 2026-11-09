# Replay controls outside the canvas — 2026-11-08

## Trigger and scope

Primary's P16 review reports that the successful Fit both action leaves tall,
nearly overlapping recorded trajectories beneath the absolute top controls and
bottom tracking overlay in `runs/frontend-comparison-fit-native-20261108/fit-both.jpg`.
This packet removes those overlays from the actual canvas frame. It does not change
fit bounds, camera motion, geometry, poses, telemetry, clock or performance criteria.
The source worker did not operate a browser or independently verify the screenshot.

## Staged implementation

Candidate-only files, not yet applied to live source:

- `.cache/replay-flow-controls/Experiment.tsx`
- `.cache/replay-flow-controls/experiment.css`
- `.cache/replay-flow-controls/replay-flow-layout.test.mjs` (destination `web/tests/`)

The existing Play/Fit/diagnostics/time controls become a wrapping normal-flow row
immediately above `.exp-replay`. Camera tracking becomes a normal-flow block
immediately below it. The frame retains `ref={replayCanvasHost}` and contains only
the existing single `FlightScene`. Its unchanged height is
`clamp(300px, 36vh, 420px)`, with a 300 px minimum. Longer controls/status can increase
the surrounding flow height without reducing or obscuring that canvas frame.

No hooks, callbacks or data transformations are added. The remaining camera/time
controls, linked plots and disclosures retain their behavior. No generic canvas
selector or `!important` override is introduced. No physics, source adoption,
engineering acceptance or supplier inquiry status changes; inquiries stay UNSENT.

## Exact identity and preservation

Live baseline SHA-256, rechecked after candidate preparation:

- `Experiment.tsx`: `e1f83e3410d8a0975f3f3f05b71c189137dea27d5cc8ac3cbd16624526cc1c90`
- `experiment.css`: `bd0b0811ed20bf462c269f0a94ec287ce555820d1c4b8c58800e990d151340dd`

Frozen candidate SHA-256:

- `Experiment.tsx`: `c05595399fa11f5de4721f06da0b6783f7a80c31ab4d3e1bb013c0de92d32af7`
- `experiment.css`: `a775a0d8326c069fa67311addf5971a75d5e9082e35ea330845698c6f3e56f45`
- `replay-flow-layout.test.mjs`: `295a7fe5a1a40829c6f2c9bb23f17fcc15c122fe2245fd585e613ad61e4abda1`

A TypeScript AST/token comparison of baseline and candidate confirms identical
multisets of every arrow callback, call expression and variable declaration. All
function declarations except the two intended JSX-layout owners (`Experiment` and
`CameraTrackingReadout`) are token-identical, including `FlightScene` and
`ReplayCamera`. CSS before/after the bounded controls/readout rule block is byte-
identical, including canvas sizing and responsive layout rules.

## Checks and remaining observation

- Candidate TypeScript in-memory overlay: zero diagnostics; no live file swap.
- Candidate ESLint overlay: pass.
- Candidate TSX and CSS formatting: pass.
- New AST layout contract: pass against the staged candidate. It verifies one scene,
  a frame containing only `FlightScene`, preceding control/following status siblings,
  retained accessible labels, and unchanged run/time/mode/alignment prop bindings.

These are source checks, not computed-layout or browser acceptance. Primary must
coordinate live application and run integration checks. The designated verifier must
observe the actual fitted envelope without UI occlusion, reachable controls/status
at the current viewport and narrower widths, single-run/comparison behavior, and
unchanged time/channel/range state. No FPS or memory campaign is part of this packet.
