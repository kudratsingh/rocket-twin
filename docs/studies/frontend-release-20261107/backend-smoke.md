# Actual-data in-process backend smoke — 2026-11-07

Result: **passed**. One serial GET-only TestClient(create_app(ROOT))
attempt; no socket, network, browser, installation, CAD/model solve or new run.
Declared limit:20 process CPU seconds /60 wall seconds, numerical and Arrow
parallelism1; CPU affinity is not asserted. Measured CPU
8.433 s / wall8.930 s.

- API requests completed: 36.
- RP1 source parts / validated GLBs: 55 /
  26; every served GLB hash is
  checked against its source-pinned URL, with GLB2 header/length/JSON validation.
- RP1 compatible analyses remain an empty list; no substitute field is attached.
- Exact conditional G54 run: `exp-ab60bd4ac5c2412a9dd85f712072bca2`. Matching archived configuration/resolved
  specification/CAD checks are required before telemetry checks.
- Native returned/raw rows: 132856 /
  132856; channels48.
- Native window: [0.001, 132.8560000002703] s;
  span132.8550000002703 s. Every interval
  is checked against1 ms within1 ns when this stage completes.
- Native response body: 113412840 bytes in
  process. This is not a socket/network transfer or browser load measurement.
- Default JSON and Arrow retain the event-preserving bounded profile.
- Raw owner record files checked: 383;
  all unchanged: True.
  Exact record/resolved/Parquet byte hashes unchanged:
  True.
- Peak RSS: 850132992 bytes, for
  this Python process including API/import/parsing costs. It is not browser
  memory, GPU usage, normal-host preview memory or a60 fps measurement.



The complete request status/timing/byte-digest evidence and before/after owner
file hashes are in [backend-smoke.json](backend-smoke.json). Bulk telemetry and
GLB payloads are neither printed nor stored by this smoke. No `/api/runs` list
or nonterminal/failed experiment endpoint is requested; raw record fingerprints
are computed directly without lifecycle normalization.

This establishes backend startup and actual saved-data endpoint behavior inside
TestClient. Normal-host preview serving, browser rendering/interactions,
full-rate playback/scrub/memory/FPS acceptance, engineering acceptance and every
physical/build/test/paid-run/WO-10/flight gate remain open. RP1 AD1 does not inherit
this separate archived G54 flight dataset. All five inquiries remain UNSENT.
