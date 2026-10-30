# WO-05 — Experiments, 3D replay, telemetry, compare

Branch: `wo-05-experiments`. Tier: Mac.

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
