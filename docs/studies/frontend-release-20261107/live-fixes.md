# Live inspection corrections — November 7, 2026

The owner restarted `make preview` in the normal host Terminal. Sole verifier
`/root/browser_access_sol` observed the exact RP1 inspection digest
`238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`
in the live API, matching its frozen specification and record, with canonical
resolved/CAD identities still null. All 26 mesh records loaded. No engineering
or build/flight criterion changes; the five inquiry drafts remain UNSENT.

| Observed finding | Correction | Actual recheck and limit |
| --- | --- | --- |
| React synchronous-unmount console errors at CG/CP `Html` labels | Replace static inspection labels with owned text nodes projected by the existing Three camera; keep React StrictMode and dependency pins | Reload, clear console display, clear selection and fit assembly; then section/hide/restore. Verifier reported zero new console messages in that flow. Remaining workspaces still need their checks. |
| Selected-part summary covered framing status and missing-solid warning | Move framing and geometry status to a stacked Scene tools readout; keep source-maturity banner on canvas | Verifier opened Scene tools and observed both readouts separately and legibly at 1440 × 900. Smaller sizes pending. |
| Orientation caption overlapped overall length at lower left | Clear inherited `left` when right-aligning the orientation caption | Verifier observed orientation at right, separate from the overall length caption. |
| RP1 summary claimed live burn-state requests | Explicit saved estimated case language; no compatible burn-state model for RP1 | Code correction; remaining summary browser recheck pending. |
| Header Parts appeared to open Details under emulation | No application correction: native accessibility-index click coordinates were offset in the DevTools responsive viewport | Actual visible button coordinates selected Parts and Details correctly. Record the interaction-method limitation, not an application pass from the misdirected click. |

`SceneLabel` uses text-only DOM nodes, camera/world transforms and explicit node
ownership. It does not start a separate React DOM root, infer geometry, calculate
physics or add a renderer. Three focused checks cover perspective/orthographic
projection, parent motion, invalid anchors and repeated setup/cleanup without
removing sibling nodes. All 157 web tests, TypeScript, lint and production build
passed locally. Local SSR fixtures emit a sandbox WebSocket `EPERM` warning in
some existing tests; the test processes completed successfully. These checks are
not browser interaction evidence.

The pinned Fiber/Three combination constructs deprecated `THREE.Clock`; this is
separate upstream compatibility debt. No warning is suppressed, dependency
upgraded or project clock contract replaced in this packet.

## Actual images

- `runs/frontend-browser-20261107/rp1-baro-framed-1440x900.png`: real close-up,
  simplified barometer envelope selected, before bottom-message correction;
  SHA-256 `543119eaae2e37adffc897083ba1a38b6a4b1ca0a6e35dc4e3bc67a912d31411`.
- `runs/frontend-browser-20261107/rp1-assembly-fixed-labels-1440x900.png`: rendered
  assembly and projected saved-estimate CG/CP labels, before orientation correction;
  SHA-256 `3d793b264a565684ab64185eaee31d161c169603fb6c907d3119012d3dfc3929`.
- `runs/frontend-browser-20261107/rp1-restored-tools-1440x900.png`: after section,
  outer-body hiding and restore; selected part retained, Scene tools readouts
  separate and orientation corrected; SHA-256
  `f5fc5d6034176f329281708c9ba007926988a7993154221918bd226c4274751e`.

Images are genuine native Chrome captures, excluded as generated bulk files.
The browser protocol and compound acceptance rows remain open until their full
applicable paths are observed; these individual rechecks do not blanket-pass
layout, replay, experiments, Analysis or engineering acceptance.
