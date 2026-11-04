# First inspection slice — reachability and source identity, v3

2026-11-03. This continues the saved PR68/69 implementation and the
[previous refinement](wo04-inspection-refinement-20261103.md). The primary owns
integrated checks and publication. The local source snapshot has no Git metadata;
this note asserts no new commit, merge or running-host identity.

## What the owner can use

- Five addressable workspaces remain available: Design, Engineering, Experiments,
  Flight Replay and Analysis. Navigation remains outside the content scroll region.
- Design retains recorded 3D geometry, source-derived horizontal 2D envelopes,
  part search, shared selection/visibility, explicit zoom/fit/focus/reset, section,
  explode, source component details and SVG export. Fit and reset remain distinct.
- The 2D drawing and its details now use natural content height. The 3D viewer
  receives an explicit measurable height. Narrow layouts place parts/details below
  the visual without a fixed 2D container overlapping those panels. Desktop CSS
  reserves 64% of normal workspace width for the visual; actual rendered dimensions
  have not been measured in the browser.
- Find a component and Open component details reveal collapsed panels, leave
  focus view if necessary, scroll the target into view and move keyboard focus.
  Selection summary shows the source component's function, material, recorded-mesh
  availability and hidden state. It offers a direct selected-details action.
- A source with no recorded component meshes starts in 2D. Representation changes
  retain mounted children and shared selection. Missing component meshes are named
  explicitly; concept rows do not acquire a mapping to another assembly.
- `/` reveals collapsed part search. F/R from the parts tree or drawing controls
  target the active 2D focus/reset actions. Section/explode keys do not change the
  retained hidden 3D view. Input typing and browser Ctrl/Cmd shortcuts are excluded.
- Inspection rejects mismatched or ambiguous component identities before storing
  a response. Aborted source/mass responses cannot replace newer data. During a
  source change, the previous source's name, geometry maturity and fingerprints
  are not displayed as the requested design. A successfully loaded source can
  remain visible when only the configuration catalog is unavailable.
- Source & limitations now discloses the loaded document's full specification/CAD
  identities and actual per-component mesh coverage. Missing fingerprints remain
  unavailable. A successful export or simulation grants no physical qualification.

Terra HIGH's coordinated section-picking change preserves the existing camera,
selection and store contracts: part click/pointer-over ignores intersections on the
clipped side of the same world-space plane used for section rendering. Those hits
no longer stop propagation before a visible interior component can receive the
pick. Visible-side and boundary hits remain eligible. This is code behavior;
actual interior-part picking remains a browser check.

## Open the saved workflow

From the repository root in the existing Node 22 / Python 3.11 environment:

```sh
.venv/bin/python scripts/wo04_preview_preflight.py
make preview
```

The preflight is read-only. The launcher prepares existing source exports and
starts API/Vite at ports 8000/5173. No new server start or host reachability result
is asserted by this documentation increment. Earlier sandbox listener EPERM and
the separate designated-browser ownership prerequisite remain recorded blockers;
a sandbox probe cannot establish that the owner's host server is stopped.

| Workspace / source | Route |
| --- | --- |
| Recorded reference inspection | `http://127.0.0.1:5173/?workspace=design&design=modular-performance-v1` |
| Separate F2 construction | `http://127.0.0.1:5173/?workspace=engineering&view=g80-f2` |
| Separate unadopted F2-C1 connection proposal | `http://127.0.0.1:5173/?workspace=engineering&view=g80-f2-c1` |
| Preserved experiments | `http://127.0.0.1:5173/?workspace=experiments` |
| Preserved recorded replay | `http://127.0.0.1:5173/?workspace=replay` |
| Compatible recorded analysis | `http://127.0.0.1:5173/?workspace=analysis` |

The existing configuration selector and workspace/topic history remain in use.
This slice does not add a new persisted part-selection route contract. Experiments
and Replay retain their existing shared component/run state; no physics or saved
attitude was changed.

## Which source the saved image evidence represents

The existing [fin render record](../runs/wo04-focused-2d-refinement-20261103-v1/fin_set.json)
identifies the historical `modular-performance-v1` reference:

- Resolved specification: `c18abfee2444307e46eaaca55197693a3d9353bd8d8d8ac42162ffd238ef1d5e`
- Recorded CAD revision: `1193713d0f4a7ad8393a00a0a03e7aaa04e9aa9393d2034691ef7126ae3cdd3b`

These are copied identities from the saved evidence record, not a newly generated
source snapshot or a live-host verification. Its earlier PNG observations remain
attributed to that render. No new raster image was generated for this layout slice.
Current app identity must come from the fetched inspection document.

F2 construction and the F2-C1 fit proposal remain separate engineering graphics.
Neither is a complete recorded 3D CAD assembly. This frontend work changes no
engineering candidate, contact assumption, allocation, force, guide threshold,
source material or acceptance finding. Parallel engineering precedent work has
its own source and decision scope.

## Code evidence

The Astra source/workspace/2D command passed **15 focused tests**:

```sh
cd web
node --experimental-strip-types --test tests/inspection-workflow.test.mjs tests/workspace-chrome.test.mjs tests/workspace-navigation.test.mjs tests/design-presentation.test.mjs tests/orthographic-design.test.mjs
```

It covers requested-versus-loaded source identity, wrong/duplicate component
rejection, dimensions-only entry, reachable panel targets in server-rendered
markup, active-drawing shortcut mapping, source geometry/visibility rules,
navigation preservation and export-visible source/maturity content. SSR does not
execute pointer, keyboard, scrolling or download interactions.

Whole-web TypeScript, scoped ESLint/Prettier and `npm run build` passed during the
implementation packet. The build retained its greater-than-500-kB chunk warning;
no loading-time, WebGL or frame-rate result follows. Primary integrated checks
and publication are separate and will carry their own attribution.

Terra reported the following pre-freeze command passed **5/5 tests**:

```sh
cd web
node --experimental-strip-types --test tests/inspection-camera.test.mjs tests/inspection-state.test.mjs
```

Those checks cover orbit-preserving fit, finite end-on fit, section clipping-side
eligibility and existing inspection state behavior. Terra also reported passing
typecheck, lint and build before the code freeze, with the same large-chunk
warning. These results are separately attributed; they are not additional browser
observations or included in Astra's 15-test count. Relevant files are
`web/src/components/Viewer.tsx`, `inspectionCamera.ts` and
`web/tests/inspection-camera.test.mjs`; primary integration should include that
suite alongside the 15-test command above.

## Actual interaction evidence still required

Run the planning-kit matrix at 1280×800, 1440×900 and 1920×1080, each at
100/125/150% browser zoom, through the designated browser owner after supported
runtime access is resolved. Record exact build, route, source, viewport and result.

1. Reach the final expanded 2D detail and each inspector/tree footer; verify panel
   boundaries allow page scrolling, without overlap, clipping or a scroll trap.
2. Collapse both panels, use `/`, Find a component and selected-details actions;
   verify the reopened target and keyboard focus are visible. Enter/exit focus
   view and verify Escape ordering and selection/camera continuity.
3. Inspect a small internal component through tree, 2D and sectioned 3D; verify
   visible-side picking, hidden-part/layer explanations, reveal/focus, isolate,
   restored context and source correspondence. Section/explode remain display
   transformations, not clearance or assembly qualification.
4. Exercise explicit zoom/fit/reset/focus, orbit, pan, browser zoom and typing;
   confirm hidden representations receive no unintended camera commands.
5. Change source during loading and retry unavailable data. Compare displayed
   fingerprints/mesh coverage, preserved experiments/replay, deep links and
   Back/Forward. Verify actual SVG downloads carry the intended source/status.

No browser/computer/headless tool was used for this slice. Relevant backlog tasks
remain **partial**, with code evidence recorded, `browserObserved: false` and
`accepted: false`. Full first-slice acceptance, all 43 tasks, WO-03/04/05 and the
physical/build/paid-run/firmware-review/flight gates remain open.

Primary integration: the complete web suite passed71 tests; TypeScript, whole-web ESLint, formatting and production build passed. The existing large-chunk warning remains. These results are code checks; browser observations remain pending.
