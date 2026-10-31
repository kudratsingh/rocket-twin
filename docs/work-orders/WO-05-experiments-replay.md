# WO-05 — Experiments, 3D replay, telemetry, compare

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
