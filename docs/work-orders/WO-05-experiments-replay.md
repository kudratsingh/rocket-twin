# WO-05 — Experiments, 3D replay, telemetry, compare

**Design workbench v2 — owner direction, November 9:** The full next revamp is
planned in [ten phases with46 tasks and36 acceptance scenarios](../frontend-design-workbench-v2/README.md). It adds
source-supported intricate component CAD, linked drawings/systems, a parts bank,
validated separate draft composition and complete alternative testing. ADR-0017
extends the viewer-only rule narrowly; all CAD/physical calculations stay in the
backend. Current RP1 is frozen, existing workflows/legacy evidence persist, and
WO-03/04/05 prerequisites and owner physical/purchase/paid-run/WO-10/flight gates
remain separate. Full model-detail completion cannot be claimed with undefined
critical hardware. Start the first source-linked parts-bank slice after P0 docs.


**Desktop capability checkpoint:** [Current walkthrough](../studies/frontend-desktop-detail-20261108/walkthrough.md)
records source-backed GLB/inspection STEP downloads, adjustable sections, nominal3D
dimensions, joint close-ups and manufacturer PCB mounting references. P34–37 native
checks verify scoped section/detail/export/board paths; original obstructions and
setup stops are retained. This is a usable inspection increment, not WO-03/04/05,
engineering, manufacturing or flight acceptance. Mobile/pixel polish stays secondary.

**Owner priority — desktop engineering capability (November 8):**
Prioritize fully functional, interactive desktop rocket inspection, source-backed
CAD and intricate components/connections, graphics, experiments and replay.
Mobile/compact-layout polish and exact-pixel viewport campaigns are secondary and
must not delay those capabilities. Preserve completed layout evidence and open
checks; deferral is not a pass. Continue from current RP1/AD1 v2, keeping historical
CAD/run identities separate. Model actual documented detail where available;
label envelopes, concepts and undefined hardware rather than inventing precision.
[Saved direction and next capability](../studies/frontend-desktop-detail-20261108/priority.md).
Existing engineering, purchase, physical/test and flight gates are unchanged.

**Recorded replay navigation (November8):** loaded-run playback now has
flow controls above the Canvas, camera status below and source-local sticky
Scene/Graphs/Events/Validity/Data & limits destinations. P17/P19/P20 verify scoped
current-window behavior; exact responsive/performance/data prerequisites remain
open. [Evidence](../studies/frontend-replay-section-navigation-20261108/integration.md).
No flight calculations, controller, physical source or approval changes.

**November8 release closure:** [Current frontend worklist](../frontend-release-worklist.md) records merged monitoring/Analysis guards and the integrated bounded drawing, event-linked recovery explanation, source-preserving saved comparisons/exports and full Analysis framing correction. P2 remains diagnostic-only, not a60fps pass; cancellation remains inconclusive. Exact responsive checks await supported owner manual sizing. Full milestone prerequisites and all engineering/build/flight gates stay open.

**November 7 preview closeout:** [Actual release evidence](../frontend-release-20261107.md)
records the source-derived RP1 inspection model, live interactions and measured
layout/Side fit. Single/batch experiments and recorded replay have actual local
browser evidence; the full native-rate 60 fps benchmark remains failed. Missing
spatial fields and unexecuted compound checks are not passes. Full WO prerequisites,
WO-03, engineering, physical-build, WO-10 and flight-release gates remain unchanged.


F2-C1 is an inspection-only connection proposal, not a supported experiment
configuration. Its recorded guide/static/burnout comparisons are exposed in
`docs/wo04-f2-c1-walkthrough-20261103.md` without creating new flight results.
Keep the existing simulator/replay paths and source identities unchanged;
unavailable physical inertia and installed evidence do not become substitute
zeros or inherited flight qualification. Full WO-05 acceptance remains open.

2026-11-03 frontend direction: execute the supplied43-task planning kit through
focused Design/Engineering/Experiments/Flight Replay/Analysis workspaces
(ADR-0014; `docs/frontend-workbench-backlog.md`). Astra MEDIUM owns complex
workspace code; Terra HIGH owns bounded camera/replay/bookkeeping slices;
primary owns shared integration and engineering acceptance. Preserve existing
features and exact source identities. Early preview remains authorized while
WO-03 stays open. Browser verification remains blocked by the original
designated-agent ownership prerequisite; source/build/offline checks do not
clear it or any physical/flight gate.

G80-F1/ADR-0013: first conventional G80 may use a dedicated fixed physical
vehicle. Add its separately versioned source-linked construction/recovery/mass
snapshot; never substitute archived CAD or candidate inertia. F1 flight runs
require its own admitted geometry/mass/CP and motor identity. Preserve G54/G12,
PID/RL milestones and full completion prerequisites. The early preview exception
permits explanation graphics while WO03 stays open; no flight/build acceptance.


Branch: `wo-05-experiments`. Tier: Mac.

## Limited early-preview authorization

On 2026-10-30 the owner authorized real experiments, replay, understandable
synchronized graphs and two-run comparison alongside early inspection while
WO-03 remains open (ADR-0009). Use complete G80/G54/locked finned-G12 source
configurations, independent saved runs and the existing Python/JAX implementation.
Expose wind speed/direction and supported gust settings, progress, useful errors,
configuration/model hashes and recorded events. Reject unsupported finless
unguided runs; no active PID/RL controller is introduced.

Verify changing settings, executing two actual runs, replaying their recorded
position/orientation and comparing the results in the running local app. Keep
preliminary/unguided status, model-domain and engineering warnings explicit. This
subset does not waive the complete benchmark below, prerequisite acceptance,
Arrow/channel-picker/long-run performance deliverables or physical/flight gates.

## Deliverables

1. API: `POST /api/experiments` runs the sim (WO-02) in a background task with overrides from
   the UI form; `GET /api/runs*` and Arrow IPC telemetry endpoint; run list from `runs/`.
2. Frontend Experiment mode per `docs/UI.md`: setup form, run button with progress, 3D replay
   (pose from telemetry, trajectory line, wind arrow, gimbal visualised), camera modes, time
   scrub, play/pause/speed, telemetry strip with four uPlot panels and channel pickers, event
   markers, compare mode with two runs overlaid.
3. `src/sim/events.py`: ignition, liftoff, burnout, max-Q, apogee, deploy, abort detection
   written into `record.json` and shown as markers.

## Benchmark

From the UI: run the actual performance and locked-gimbal finned-trainer configurations, replay both, scrub to
burnout and see the CG marker and gimbal state; overlay altitude and tilt for both runs; run
list shows both with headline metrics. Replay stays smooth at 60 fps for a representative full-recovery flight of at least 120 s at
1 kHz telemetry (decimate for playback on the client).

## Notes

- If this exceeds one week, split: 05a (API runs + replay) and 05b (plots + compare).
- Telemetry channels are whatever `telemetry.py` writes; the channel picker reads the Parquet
  schema, so new channels from later WOs appear without UI changes.

Every override is validated into a complete configuration with geometry, mass,
aerodynamics and source hashes. Fins are actual parts, not an aero-only toggle.
Long-burn TVC replays include coast and recovery; changing motors requires its
mount, mass/CG and recovery changes. Label preliminary source cases as such.

## Recorded Analysis exploration (owner extension)

Extend the WO-04 Analysis view to browse and compare recorded load/thermal cases
and analysis runs on their matching actual geometry. Overlay stress, displacement,
temperature and applicable margins with consistent legends/units and part coverage;
link selected-part histories and exact transient time cursors. Reuse the WO-03
manifest and validation/provenance metadata. Keep calculated, estimated, measured
and unavailable data distinct, with assumptions and limits visible on selection.

Compare cases only with declared identity/registration compatibility. Different CAD
revisions use separately identified geometry; never silently attach or difference
incompatible fields. Flight replay and analysis clocks remain separate unless the
backend records a physical time mapping. Analysis computation stays offline/backend;
the frontend displays recorded fields and history/telemetry interpolation only.
Acceptance includes static and transient case comparison, missing/stale-result states,
selection-linked metadata and preserving all experiment/replay benchmarks.

## Traceability and vibration-risk carry-through

Preserve source-linked requirements/interfaces/FMEA and unresolved status while comparing/replaying recorded results. Never attach evidence to a different module/CAD identity or imply time coupling without a recorded mapping.

## Engineering-workbench increment (owner2026-11-02)

Implement WB-01–05 in `docs/UI.md` and the [A–L inventory](../wo04-engineering-view-inventory.md). First deliver linked C1 arrangement/internal sections, fin/recovery connections, actual load-path/free-body diagrams, C1/R1 mass/balance and conditional launch graphics. Later increments expose source-identified heat/netlist/compatible result fields and verification maps. No frontend physical calculations or invented analysis fields. Retain full benchmarks, earlier viewer/experiments/replay, exact identity/maturity, browser evidence boundaries and every engineering/build/flight gate.
