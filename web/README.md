# Rocket Twin inspection workspace

**Current full frontend revamp:** [Design workbench v2](../docs/frontend-design-workbench-v2/README.md)
plans detailed component CAD/diagrams, a reusable parts bank, separate virtual
rocket drafts and complete alternative testing in ten phases with46 tasks. It
retains the current inspector/experiments/replay and all engineering/physical
gates. The first implementation is the current-source read-only parts bank;
full draft building and candidate simulation follow their data prerequisites.


The November 7 preview has focused **Design, Engineering, Experiments,
Flight Replay and Analysis** workspaces. Start with `make preview` from the
repository root; it prepares RP1 display meshes and source snapshots, then starts
the Python API and Vite at `http://127.0.0.1:5173/`.

Current Design is frozen `G80-F2-RP1-AD1-definition-v2`: 26 source-derived
inspection meshes across 55 records, with simplified/missing geometry and
allowances labeled. Manufacturing CAD and full physical inertia remain
unavailable. Archived G80/G54/G12 geometry and matching saved runs are separate
sources; RP1 cannot run a flight through a borrowed model. Finless flight is
explicitly unsupported before its controller validation.

Mapped fin/recovery drawings, real single/batch CPU experiments, exact-time
replay, compatible comparisons, exports and current scalar Analysis findings
have native Chrome evidence. Desktop layouts/Side fits have actual pixel
measurements. The full native-rate 60 fps benchmark remains failed; wider
unexecuted/data-blocked branches stay explicit in the [current handoff](../docs/frontend-release-20261107.md).
The November8 continuation adds comparison-aware **Fit both trajectories**,
consistent CSV/metadata coverage rejection and usable visible focus restoration.
Their source checks/build pass; the new native Fit/focus branches remain pending
a stable designated-browser interval. See the [current completion packet](../docs/studies/frontend-completion-20261108/integration.md).
All supplier/lab drafts remain UNSENT. Engineering/build/flight gates stay open.

A new actual archived G80 Tiny run completed with wind1m/s and a45second partial
trajectory. The browser loaded it, compared it with a matching calm-air baseline,
jumped to apogee and exported the playback CSV. Landing is not recorded. The JSON
metadata export completed after explicit local-site authorization; no permission
prompt or setting change occurred on the actual completion path. [Run and export evidence](../docs/studies/frontend-desktop-experiment-20261108/integration.md).

## Parts bank · first v2 slice

Select current G80 RP1/AD1 v2 and open **Parts bank** in the header. Browse55 source
definitions and55 installed occurrences, search/filter and inspect dimensions,
material, mass basis, source-budget cost, geometry and identity findings.
**Inspect installed part** returns to that exact part and its existing CAD/evidence.
The catalog is read-only; Add/Replace/Connect arrive with the separate-draft builder.
Existing GLBs are installed inspection references, not reusable local product CAD.
P61/P62 actual Chrome observations cover the source-snapshot/search/selection flow,
visible warnings and scroll reset. New API routes have in-process test evidence;
the current host used the explicitly labeled prepared snapshot after404.
[Details and limits](../docs/studies/frontend-parts-bank-20261109/integration.md).

## Component structure close-ups

The current RP1 **Details → Inside the component** adds two source-based views:
actual manufacturer PCB pads/routes/holes with footprint and net selection, and
18 selectable fin/tab/gusset/tube/ring pieces from the existing mechanical model.
Body cutaways, illustrative separation and independent Fit/zoom make the
construction easier to inspect. Unknown package heights, adhesive geometry and
unqualified joints remain explicit. These are inspection references, not new
vehicle parts or engineering approval. [Open the views and source limits](../docs/studies/frontend-component-depth-20261108/integration.md).

## Desktop engineering inspection

PR116 is merged after both required checks. [Latest verified walkthrough](../docs/studies/frontend-desktop-evidence-closeout-20261108.md) includes actual ring-detail, source-drawing, keyboard, experiment and export evidence, plus the local screenshot/CAD packs. Full engineering and frontend benchmark gates remain open.

The four archived reference/controls configurations also have registered part
GLB/STEP/STL and whole-assembly GLB/STEP access. Use **Whole rocket assembly files**
without clearing a selected component. Legacy part STEP is local millimetres;
assembly STEP is placed geometry; STL has no encoded units and may follow print
packing. `make workbench-archived-cad` verifies/copies existing local files without
regenerating CAD. [Archive source and native evidence](../docs/studies/frontend-archive-downloads-20261108/integration.md).

The next source-checked inspection increment gives dual-function RP1 parts
separate fin-root and recovery routes, with exact part/revision links back to
Design. Unmapped connections remain unavailable.
[Connection navigation](../docs/studies/frontend-rp1-evidence-routing-20261108/integration.md)
· [Future detail evidence](../docs/studies/frontend-desktop-detail-20261108/measurement-unlocks.md).
The source-bound round trip and explicit selection clear were subsequently verified in the browser; original failures remain recorded.

Detailed desktop inspection, CAD/connection understanding, graphics, experiments
and replay take priority over mobile layout polish. Current source-based tools
include interior/joint isolation, adjustable section planes, recorded3D dimensions,
and selected-part/assembly GLB plus inspection STEP/provenance downloads.
[Walkthrough](../docs/studies/frontend-desktop-detail-20261108/walkthrough.md)
· [Local portable file pack](../output/rp1-desktop-inspection-pack/index.html).
The STEP files reconstruct26 represented records/36solids with nominal and envelope
status retained;29 records still have no solid. Manufacturing details, qualified
connections and RP1 full flight inertia remain unavailable. Historical models/runs
are not substituted. All supplier/lab inquiries remain UNSENT.

Optional completed local CAD preparation is `make workbench-rp1-step`; it verifies
and copies existing registered files and never regenerates CAD. Start the app with
`make preview`, then open http://127.0.0.1:5173/. Actual native feature observations
and remaining source/engineering limits are linked in the walkthrough.

Read-only local inspection of the actual resolved vehicle specifications and
CAD-derived part meshes. This is a limited early WO-04 increment authorized while
WO-03 engineering acceptance remains open. A rendered model is not hardware or
flight qualification.

Use Node 22 LTS. Start the API from the repository root:

```zsh
uv run scripts/wo04_api.py --host 127.0.0.1 --port 8000
```

In another terminal:

```zsh
cd web
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to the local API on port 8000.
Generated meshes stay in ignored `build/`; the frontend does not bundle or alter
them. Missing or incompatible source/CAD records are visible errors.

```zsh
npm run typecheck
npm run lint
npm test
npm run build
npm run format:check
```

The initial dependencies are pinned exactly in `package.json`; the install lock
records their transitive dependencies. Do not upgrade pins as part of UI edits.

The top bar selects current RP1 or separate archived G80 reference, conditional G54 upgrade, G12 finned trainer
or eventual G12 finless concept. Candidate studies have a separate catalog section
and are not represented as adopted designs. The preliminary engineering banner
stays visible in every mode.

Inspect controls:

- **Move view** is the default: left-drag moves the rocket across the view without changing its angle. Choose **Rotate view** to turn it with left-drag. Scroll or use **Zoom in/out** to change viewing distance. **Whole rocket** restores the overview and frames the loaded assembly; **Fit assembly** retains the current angles. **Frame selected** focuses a component with geometry. Missing geometry remains unavailable.
- Click a tree row or mesh to select it; hover links the tree and geometry.
  **Escape** or the inspector’s close button returns to the vehicle summary.
- Eye buttons hide individual parts. **Isolate selected**, **Show all**,
  **Hide outer body** and **Hide nose** change display visibility only.
- The exploded slider or **E** spreads the existing placed CAD geometry for
  inspection; it does not edit the design or represent an assembly instruction.
- **Section** or **S** clips the display through its longitudinal axis.
- Archived models can request burn-state mass from the backend. RP1 instead selects a saved estimated case with its separate 50 g growth allowance already included; no burn/inertia model is inferred. CG means centre of gravity (balance point); CP means centre of pressure (aerodynamic force point). Markers are hidden in exploded views.
- **Terms & units** provides the plain-English key to the abbreviations used
  in the specification and engineering evidence.

Code ownership and data flow:

| File                                 | Responsibility                                                                              |
| ------------------------------------ | ------------------------------------------------------------------------------------------- |
| `src/App.tsx`                        | Catalog/configuration fetch, mode layout and backend burn-state requests                    |
| `src/components/PartsTree.tsx`       | Searchable hierarchy, selection and individual visibility                                   |
| `src/components/Viewer.tsx`          | Placed per-part GLB rendering, camera, display explosion and markers                        |
| `src/components/InspectionPanel.tsx` | Part function/spec/build/learn/evidence, requirements/FMEA, vehicle summary and mass budget |
| `src/components/ThrustCurve.tsx`     | uPlot display of the source motor curve served by the API                                   |
| `src/experiments/Experiment.tsx`     | Separately bounded CPU experiment and recorded replay increment                             |
| `src/store.ts`                       | Ephemeral viewer state using Zustand                                                        |
| `src/types.ts`, `src/api.ts`         | API contracts and HTTP errors                                                               |
| `src/styles.css`                     | Desktop dark theme and three-column inspection layout                                       |

The GLBs already contain their physical assembly placement, in metres. Their
display frame is `X = body+y`, `Y = airframe.length_m - station_m`, `Z = body-z`.
The viewer does not apply the YAML part station a second time. It computes only
camera/display transforms; mass, CG, CP, static margin and all flight/engineering
results come from the backend or recorded artifacts.

Current RP1 has recorded scalar findings only; compatible spatial stress, displacement
and temperature overlays are unavailable. The following display capabilities require
compatible source results and do not imply RP1 coverage.

Analysis reuses the same three-column assembly layout. It lists compatible and
incompatible historical runs, then selects an exact load/thermal case and field.
Compatible thermal results color each covered physical part uniformly and are
labeled as part means; they do not imply a resolved surface temperature gradient.
The time slider selects exact solver samples, and sample playback advances eight
recorded samples per second. The selected part's history shares that cursor.
Recorded analysis time remains separate from flight-replay time.

Supported static finite-element fields draw the recorded six-node triangular
shell midsurface using its explicit affine registration, alongside ghosted CAD.
Node colors interpolate for display; element colors retain discontinuities.
These fields cover one fin instance only, and are not copied to the other fins.
Stress component diagnostics are not presented as orthotropic strength criteria.
Displacement magnitude alone does not create a deformed shape or an amplified
physical displacement.

Fixed display color limits remain constant across cases and time by default.
Auto-range changes display scaling only. Reported raw peaks, screening limits,
assumptions, uncertainty, numerical checks and required physical tests remain
separate from that display. Neutral grey means unavailable coverage, never zero
or a passing result. Unsupported, missing or mismatched fields show a reason.
The viewer checks configuration, resolved-specification, CAD and part fingerprints
before attaching a field; the backend also validates artifacts and hashes.

`src/analysis/` contains the recorded-result viewer and evidence/history panels.
`npm test` smoke-checks the identity and missing-data boundary. Expanded WO-04/05
acceptance remains separate from these early inspection/analysis increments.

Exact replay time can be entered in seconds and applied with Enter or **Go to
exact time**. Invalid/out-of-window entries leave the cursor unchanged. The slider
and nearest sampled graph readout retain their stated precision. Recovery attitude
is approximate and is never cosmetically aligned with the velocity.

**Camera → Framing area guide** shows the display-only safe rectangle. Use an
explicit **Fit assembly** after changing a manual viewing state/viewport when a
new fit is wanted. Optional part labels can be turned off for unobstructed close-ups.
A child-workspace rendering failure keeps navigation available and offers a
context-preserving reload. The `__previewFault` rendering fixture is development
only; it never starts a simulation or changes saved records.

**Scene + telemetry:** the Replay centre places the rocket, camera/playback/exact-time
controls and four linked plots together when the centre is wide enough; smaller
centres stack, with normal scrolling. Telemetry means the recorded flight values.
Channel source/drawing details, comparison alignment/range, events, recovery
limitations, diagnostics and exports remain available. An event-aligned clock is
labelled **Time from burnout** (or the selected event); **T+** means absolute
time since ignition. The new layout does not change recorded data or the recovery model.
Native current-window evidence and remaining limitations are in the
[layout report](../docs/studies/frontend-replay-layout-20261108/browser.md).

**Comparison camera:** visible buttons select Auto A→B, A only, B only, fixed pad
or free orbit. Auto uses A's recorded position while available, then B's; explicit
A/B holds with a reason if that run lacks a position. The scene label identifies
what the camera follows. A valid position marker can be followed when attitude
is unavailable; no body attitude is invented. These choices move the view, not
the rocket or controller. **Fit A trajectory** fits A only; combined fitting is
unavailable. See the [camera integration](../docs/studies/frontend-replay-follow-20261108/integration.md).

The optional development URL flag `verifyViewport=1` shows **read-only browser-size
information**. Its reference sizes are not resize controls or normal app settings.
You do not need to match them to inspect the rocket. The helper cannot set Chrome
bounds/page zoom, and matching a reference does not pass layout checks. Use Chrome's
upper-right menu for page zoom; Rocket Zoom in/out controls the3D camera.

## Reach replay sections

On a loaded saved run, **Replay sections** jumps directly to Scene, Graphs, Events,
Validity or Data & limits. The last opens recorded playback diagnostics; it does
not run a benchmark. Visible playback controls are above the Canvas and camera
tracking below. **Fit both trajectories** frames recorded positions from both
loaded runs; without B, **Fit A trajectory** remains. These actions change the
view only. [Source/native evidence and remaining checks](../docs/studies/frontend-replay-section-navigation-20261108/integration.md).
