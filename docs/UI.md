# Frontend specification — focused engineering workspaces

## Active owner-authorized frontend direction — 2026-11-03

The owner supplied `output/frontend-planning-kit-20261103/` and explicitly
requested implementation, beginning with usable inspection while replay/data
work proceeds independently. [The tracked43-task ledger](frontend-workbench-backlog.md)
records scope, dependencies and evidence. [ADR-0014](adr/0014-focused-engineering-workspaces.md)
supersedes the dense universal-shell layout below where they differ.

Use five focused, addressable workspaces: **Design, Engineering, Experiments,
Flight Replay, Analysis**. A dense Mission Control is optional. Preserve the
existing React/Three.js/Python/JAX architecture and all recorded source boundaries.
The first code increment makes the model dominant, adds explicit zoom/fit/focus,
collapsible secondary panels, one reachable scroll region, compact source status,
and Back/Forward-aware navigation. F1/F2/A1 drawings load independently of C1.
Current G80-F2 construction is a separately identified concept/local-joint snapshot;
archived detailed CAD is never relabelled as a complete F2 rocket.

Experiments and Replay use the same retained component/run state, with focused
presentation rather than two numerical implementations. Replay uses recorded
positions/quaternions; nose-up descent remains source behavior with its recovery
model limitation explained. No cosmetic attitude correction. Candidate full
inertia and compatible spatial analysis are unavailable where not recorded.
Source/scalar graphics must not invent stress, pressure or temperature fields.

The first code slice is not browser acceptance. Only the previously designated
frontend agent/window may verify after its runtime-ownership prerequisite is
resolved; no retry/bypass of the recorded automatic rejection. Keep pending
scroll/zoom/history/WebGL/run tests explicit. Full WO-03/04/05 completion,
physical-build, purchase, paid-run, firmware-review and flight gates remain.

The next inspection refinement adds an export-safe source legend, selected-part
annotation, linked hidden states, selection-only/context and local keyboard
navigation. See `wo04-inspection-refinement-20261103.md`. A read-only host
preflight is available; it neither starts a server nor resolves browser ownership.

## Preserved baseline and detailed requirements

A1 connection follow-up is a separate versioned early-workbench snapshot
(`view=a1`), with source-defined concept interface/root diagrams, historical
coupler failure, fit/mass/guide records and separate motor load cases. It does
not map concept geometry onto C1 or archived CAD, run physics in the browser or
clear full WO/release gates. Offline rendered images are separate from browser
verification. See [A1 walkthrough](wo04-a1-connection-walkthrough.md).

Single-page web app. Vite + React + TypeScript, react-three-fiber for 3D, uPlot for plots,
zustand for state, FastAPI backend at `/api`. Desktop-first; no mobile layout required.
Dark theme, one accent colour, system font. No design system library.

The owner authorized an early inspection/experiment subset on 2026-10-30
([ADR-0009](adr/0009-early-inspection-experiments.md)) while WO-03 remains open.
Keep the parts list left, rocket viewport center and inspector/summary right for
every configuration. Explain terms and units in plain language. A prominent
"Preliminary design — engineering acceptance remains open" status is always
visible. Candidate designs are a separate, explicitly unaccepted group.

First deliver working Inspect; compatible recorded Analysis is a second increment.
The limited Experiment preview also executes the shared Python/JAX simulator,
supports steady wind and existing gust settings, saves separate identified runs,
replays actual recorded poses and compares two runs with synchronized graphs.
Complete configurations replace arbitrary motor swaps. Preliminary unguided status,
incomplete trajectories and model-domain warnings remain visible. This start-order
exception does not waive full WO-04/05 completion or any physical/flight gate.

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│ Top bar: vehicle selector · run selector · [Inspect] [Analysis] [Experiment]     │
├────────────────────┬─────────────────────────────┬───────────────────┤
│ Left: parts tree   │ Centre: 3D viewport          │ Right: panel       │
│ (collapsible,      │ (orbit, exploded slider,     │ (changes with      │
│ click = select)    │ CG/CP markers, section cut)  │ selection/mode)    │
├────────────────────┴─────────────────────────────┴───────────────────┤
│ Bottom: telemetry strip (Experiment mode only) — time scrub + plots   │
└──────────────────────────────────────────────────────────────────────┘
```

## Mode: Inspect (WO-04)

- **Parts tree** (left): the spec's tree. Stages are top-level nodes when the vehicle has
  more than one. Click selects; hover highlights in 3D. Shows mass per part and subtotal per
  subtree (dry and wet for tanks).
- **3D viewport** (centre): GLB meshes from `/api/vehicles/{id}/meshes`. Controls: orbit, zoom,
  reset view; exploded-view slider (0–1, parts translate along the vehicle axis by their
  spec'd `explode_offset`); section-cut toggle (clip plane through the axis); markers for CG
  (filled) and CP (hollow) with a line between them; the burn slider moves CG as propellant
  depletes (per stage for the launcher). **Scale switch** follows the vehicle's `scale`:
  `model` shows a 1 m ground grid; `full` shows a 100 m grid, a human-figure silhouette for
  scale, and tank fill levels drawn inside the section cut.
- **Right panel — part inspector**: name, type, material, mass (spec and CAD-derived), key
  dimensions, electrical or propulsion ratings when present (engine: thrust SL/vac, Isp,
  throttle range, gimbal; tank: volume, propellant, fill, pressure), the `learn:` text with
  its citations, and links to the part's CadQuery file and spec lines.
- **Right panel — vehicle summary** (nothing selected): total mass, CG, CP, stability margin in
  calibres at liftoff and at burnout, NAR/Class-1 limit checks (green/red; model only), motor
  and thrust curve plot, mass budget table (part → mass → % of total). For `full`: per-stage
  wet/dry mass, propellant mass fraction, Δv per stage from the rocket equation, thrust-to-
  weight at liftoff, payload.

## Mode: Experiment (WO-05)

- **Right panel — experiment setup**: vehicle; preset (`sim`); overrides as a short form:
  motor (dropdown from `configs/vehicle/motors/`), wind (steady m/s + gust on/off), mass shift
  (g, position along axis), controller (none / PID / RL, from WO-06+), domain-randomisation
  seed. Button: Run. Runs execute on the API and return a run id; progress shown.
- **3D viewport**: replays the run: vehicle pose from telemetry, trajectory line, ground plane,
  wind vector arrow, gimbal angle visualised on the motor mount. Camera modes: follow, fixed
  pad, free. Time scrub shared with the plots. Play/pause, 0.25×–4× speed.
- **Telemetry strip** (bottom): up to four uPlot panels, channel picker per panel (any column of
  the telemetry Parquet), linked cursor with the 3D scrub, events marked. **Mission timeline**
  row above the plots lists the events with T+ times (model: ignition, liftoff, burnout, max-Q,
  apogee, deploy, abort; full: liftoff, pitch-over, max-Q, MECO, separation, SES, fairing,
  SECO, boostback, entry burn, landing burn, touchdown, engine-out).
- **Full-scale replay**: Earth-curvature-aware camera (downrange view in km, altitude in km),
  separate stage trajectories after separation, stage selector for which body the camera
  follows, ground track on a flat map inset.
- **Compare**: select a second run; 3D shows both trajectories, plots overlay both with the
  same channels. Used for PID vs RL (WO-07) and sim vs flight log (WO-11).
- **Run list**: all `runs/` with id, vehicle, controller, date, headline metrics; click to load.

## Later additions (named now so the layout leaves room)

- WO-05b: scale switch, mission timeline, stage selector, ground-track inset (listed above;
  the layout leaves room from WO-04).
- WO-06: controller panel — gains for PID, live tilt/rate readouts during replay.
- WO-07: policy panel — observation and action traces, randomisation values for the run.
- WO-08: lander mode — orbital stage 1 from entry-burn end, throttle and grid-fin traces, the
  G-FOLD reference trajectory drawn beside the RL trajectory.
- WO-09: build panel — BOM table, wiring diagram SVG, print list with status checkboxes.
- WO-11: flight log import — drag a flight log, it becomes a run with `source: flight`.

## API (FastAPI)

- `GET /api/vehicles` · `GET /api/vehicles/{id}` (spec as JSON) · `GET /api/vehicles/{id}/mass`
  (mass props vs burn fraction) · `GET /api/vehicles/{id}/meshes` (GLB per part, cached from
  `build/`).
- `POST /api/experiments` (vehicle, preset, overrides) → run id · `GET /api/runs` ·
  `GET /api/runs/{id}` (record.json) · `GET /api/runs/{id}/telemetry?channels=…` (Arrow IPC).
- `GET /api/motors` · `GET /api/motors/{id}/curve` · `GET /api/engines` ·
  `GET /api/engines/{id}` (thrust and Isp vs ambient pressure, throttle range).
- `GET /api/vehicles/{id}/mission` (scripted event list for `full` vehicles).

## Explicitly out of scope

Editing parts in the browser; user accounts; saving UI layouts; mobile; any physics in the
browser beyond interpolating telemetry for playback.

## WO-01 rebaseline contract clarification (ADR-0006)

The vehicle selector names separate performance, finned TVC and finless TVC models.
Load complete resolved specs and record hashes; physical fin removal changes mass,
inertia and aerodynamics together. Show `build` and mass provenance with `learn`.
Distinguish preliminary numerical checks from hardware/control/flight release;
negative finless margin and unresolved motor-source correspondence remain visible.
Motor overrides create validated configuration variants, including mount and
recovery changes. This clarifies data identity without redesigning the frozen UI.

## Mode: Analysis (owner-authorized specification extension, ADR-0007)

The top-bar modes are **Inspect / Analysis / Experiment**. Analysis reuses the parts
tree, viewport and inspector. Computation runs offline or in the backend; the
browser loads recorded results, interpolates display frames and explores them.
No browser stress, thermal, margin or flight solver is introduced.

- Select exact configuration, analysis run and load/thermal case, then quantity:
  stress (named component/invariant and criterion), displacement (component or
  magnitude), temperature, or applicable design margin. Render fields on the
  corresponding actual part geometry. An optional analysis-mesh outline makes the
  discretization inspectable. Display/deformed geometry stays separate from the
  original CAD; displacement amplification is explicit, defaults to 1 and changes
  visualization only. Never suggest an amplified shape is the actual displacement.
- Every overlay has a labeled color legend, units, min/max, scale limits and missing
  coverage. A fixed color range across compared cases/times is the default; an
  auto-range toggle is visible. Stress is Pa/MPa, displacement m/mm, temperature
  K/deg C, margin dimensionless with its formula and pass/fail threshold. Component,
  integration-point versus nodal data, averaging and excluded regions are explicit.
  For plywood/printed anisotropy, do not present von Mises alone as a valid strength
  criterion. A scalar part-level thermal or margin result uses a uniform tint and
  is labeled as such; it does not imply resolved spatial detail.
- For transient fields, show a time scrubber, play/pause, exact time and a per-part
  history plot. Static cases show their load state without a fictitious time axis.
  Time comes from the recorded analysis and remains distinct from flight-replay
  time unless a recorded mapping links them. Display interpolation is marked;
  reported peaks and margins use solver samples, never browser recomputation.
- Hover/select stays linked to the tree. Selecting a part exposes available results,
  peaks and locations, case loads/boundaries, material/orientation, assumptions,
  uncertainty, applicable temperature/strength/deflection limits, margin definition,
  solver/mesh versions, convergence/known-case status and required physical tests.
  Link the report and original result artifact. Unanalyzed parts remain selectable.
- Show provenance separately from validation. **Calculated** identifies model/solver
  output; **estimated** identifies assumptions/proxies; **measured** identifies
  instrument/log data with location, time and source; **unavailable** has a visible
  neutral/hatched state and reason. A measured point does not color an entire part
  as measured. Estimated material/boundary inputs remain visible beside calculated
  output. Neither a calculated field nor solver convergence implies physical
  validation. Show failures and unresolved conclusions prominently.
- Register fields using exact configuration, resolved-spec hash, CAD/generator
  identity, part IDs, analysis mesh hash, coordinate frame/units and mapping to the
  viewer mesh. Reject mismatched or stale overlays with an explanation; do not
  silently attach historical results to revised geometry or switch configurations.
  Invalid/missing data renders a visible status, never zeros or a green pass.

### Analysis API and export contract (WO-03 -> WO-04/05)

- `GET /api/vehicles/{id}/analyses` lists recorded compatible runs and incompatible
  historical runs with their reason; no analysis is launched by this request.
- `GET /api/analyses/{run_id}` returns the immutable manifest, cases, identity,
  quantities, times, part coverage, provenance/validation and artifact references.
- `GET /api/analyses/{run_id}/artifacts/{asset}` serves allowlisted field/mesh/history
  artifacts with hashes and cache headers. Validate identity before returning an
  attachable overlay. Configuration/run identifiers never become arbitrary paths.
- WO-03 exports versioned manifests and SI field/history artifacts. Store analysis
  nodes/connectivity and explicit CAD-to-display registration separately from GLB.
  Preserve raw values, locations, association (node/element/integration-point/part/
  measured point), timestamps, units, reported extrema and decision margins. Supply
  backend-generated display mappings where needed; retain discontinuities and
  excluded/singular regions. In the first version a part-level result is supported
  honestly, without inventing nodal FEA data.

WO-04 acceptance includes static and transient recorded overlays with real run
identity, part inspection, legends/time controls and unavailable-data behavior.
WO-05 extends Analysis to browse/compare recorded cases/runs and synchronized
history cursors; time coupling to flight replay requires explicit provenance.

### Linked verification context

Inspect and Analysis expose stable requirement/interface IDs, applicable mode,
criterion/source, verification method/WO, linked evidence and unresolved status.
Show relevant FMEA causes/mitigations/residual risks on part selection. Recorded
vibration modes/frequencies and flutter screening reports retain their validity/
attachment/temperature assumptions; a mode shape is a display field with explicit
normalization, not a measured displacement. Exact configuration/CAD identity checks
apply to these artifacts as to stress/temperature fields.

## Bounded inspection-visualization increment — owner direction 2026-11-02

The owner requested clearer frontend CAD/rocket visualization while the C1
engineering work continues. This limited WO-04 increment retains the existing
three-panel layout, renderer and source geometry. See
[scope, checks and pending visual observations](wo04-inspection-views.md).

Inspect adds overview/front/side/motor-end camera presets, focus on a selected
part (`F`), fit visible geometry, a transparent outer shell with internal-part
selection, a selected-part label, display wireframe and an orientation widget.
View controls are display-only; the renderer performs no flight or engineering
calculation. Analysis retains its recorded colors/opacity and excludes the new
ghost/wireframe/label styling. No incompatible analysis can attach.

The archived 72-part retention model remains separate from active designs and
from C1. C1 currently has numerical study evidence, not an exported complete CAD
assembly; neither the archived model nor an invented assembly is labeled C1.
The increment adds no engineering, build, flight or full-WO acceptance.

## Owner-authorized engineering workbench — 2026-11-02

The owner expands the early WO-04/05 preview from camera/inspection controls to
an explanatory engineering workbench. This explicitly updates the frozen UI
contract within ADR-0009; full milestone and physical-flight gates are unchanged.
Use [bounded tasks and A–L inventory](wo04-engineering-view-inventory.md) and
[first walkthrough](wo04-engineering-walkthrough.md). All diagrams/values derive
from versioned backend/offline sources, with configuration, frame, units and
maturity. C1 concept geometry never borrows the archived72-part CAD identity.

| Task | Deliverable / acceptance | State |
| --- | --- | --- |
| WB-01 | Linked C1 arrangement, side/front/aft projections, longitudinal and fin/recovery/receiver/motor sections; selection and source/maturity inspector; SVG exports with identity | Implemented code/API/SSR; browser unverified |
| WB-02 | Clickable motor/reverse/fin/guide/recovery paths and free-body diagrams; actual joint assumptions, failures and finite/unresolved supports | Implemented code/API/SSR; no invented clamps/sharing |
| WB-03 | C1/R1 mass distribution, separate50g/additional20g, loaded/burnout CG/CP/calibre, recorded guide samples and overall versus usable travel | Implemented code/API/SSR; conditional equipment |
| WB-04 | One source-identified heat topology and compatible recorded histories; electrical netlist and planned control blocks | Bounded subsequent export/graphics increments; no new solver/controller |
| WB-05 | Compatible stress/deformation/mode evidence, preliminary component sheets and visual verification/test map | Show missing fields now; real results/qualified WO09 build pack retain prerequisites |

Preserve actual CAD inspection, shared JAX experiments and recorded replay.
Selecting diagram components links all walkthrough graphics/inspector; link to
actual model only where its same identity exists. No current C1 full CAD, spatial
thermal/stress field or installed flutter pass exists. Illustrative assembly and
deployment sequences are not validated motion simulations. Static scalar failed
R1 findings must not be presented as fabricated spatial fields. No sensitivity
range automatically becomes a statistical confidence band.

Export read-only data with `make workbench`; `make preview` prepares it too. The
new API endpoint is `/api/engineering/workbench`. Only a404 missing-route response
may use the visibly labeled prepared offline export; incompatible/missing source
errors must remain errors. The first graphics are at
`http://127.0.0.1:5173/?workspace=engineering`, with `&view=forces`, `&view=mass`
or `&view=evidence`. No engineering calculation runs in TypeScript.


## Connections workbench delivery increment

The owner-authorized A–F extension adds source-linked comparison, recovery,
thermal-connection/history status, recorded electrical topology, assembly/service
storyboards and physical-requirement graphics to the existing Engineering tab.
Keep the first frozen C1 walkthrough unchanged; A/B concepts remain separate.
Use backend-recorded values, full identities and explicit unavailable inertia/
fields/pins; no browser physics. Export SVG and offline image artifacts with
source/status. Actual artifact image inspection is separate from designated-agent
browser interaction acceptance. See `docs/wo04-workbench-connections.md` and
`docs/CURRENT.md` for the implemented scope/remaining evidence; full WO criteria
and every existing release gate remain unchanged.
