# Rocket Twin inspection workspace

Latest2026-11-03 preview uses focused **Design, Engineering, Experiments,
Flight Replay and Analysis** workspaces. Start with `make preview` from the
repository root. Engineering defaults to the separate G80-F2 construction
snapshot; the CAD selector contains recorded reference assemblies, not a
complete F2 vehicle. Design has explicit camera controls, collapsible panels
and linked2D source-dimension envelopes. Experiments/Replay retain real backend
runs, saved poses and source limitations. Missing spatial analysis stays
unavailable. See `docs/wo04-focused-preview-20261103.md` for source identities,
URLs, runtime blockers and unexecuted browser checks. Source/build verification
is not observed WebGL/interaction acceptance.

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

The top bar selects the G80 reference, conditional G54 upgrade, G12 finned trainer
or eventual G12 finless concept. Candidate studies have a separate catalog section
and are not represented as adopted designs. The preliminary engineering banner
stays visible in every mode.

Inspect controls:

- Drag to orbit, scroll to zoom, right-drag to pan. **Reset view**, **Fit rocket**
  or **R** fits the loaded geometry, including the full hardware envelope.
- Click a tree row or mesh to select it; hover links the tree and geometry.
  **Escape** or the inspector’s close button returns to the vehicle summary.
- Eye buttons hide individual parts. **Isolate selected**, **Show all**,
  **Hide outer body** and **Hide nose** change display visibility only.
- The exploded slider or **E** spreads the existing placed CAD geometry for
  inspection; it does not edit the design or represent an assembly instruction.
- **Section** or **S** clips the display through its longitudinal axis.
- The burn slider requests mass and balance-point values from the backend.
  CG means centre of gravity (balance point); CP means centre of pressure
  (aerodynamic force point). Markers are hidden in exploded views, where a
  physical balance-point overlay would be misleading.
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
