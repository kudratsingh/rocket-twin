# WO-05 — Experiments, 3D replay, telemetry, compare

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
