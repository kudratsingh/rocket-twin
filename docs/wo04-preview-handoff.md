# Early preview handoff — ready for visual testing

This is an early local WO-04/05 preview while expanded WO-03 remains open. It
is not engineering acceptance, build approval or flight authorization. The
latest edits have non-browser checks; the existing visual observations in
[the earlier preview record](wo04-early-preview.md) predate these edits. Fresh
browser testing and screenshots remain pending at the owner's direction.

## Start on this Mac

From the repository root, with the existing pinned Python environment, Node 22,
locked web dependencies and exported CAD already present:

```zsh
make preview
```

When both servers report they are ready, open <http://127.0.0.1:5173>. It starts the
API at port 8000 and Vite at 5173; Ctrl-C stops the launcher. It does not install
packages. If dependencies are missing, the documented preparation commands are
`make setup-viewer` and `npm --prefix web ci` from the project root; those use
the existing pins. CAD exports are generated separately with `make cad`; this
can take time and does not close WO-03 acceptance.

On 2026-10-31 the agent attempted `make preview`: Vite failed with
`listen EPERM: operation not permitted 127.0.0.1:5173`, and the launcher
exited. A separate API attempt likewise failed to bind port 8000 with
`[Errno 1] ... operation not permitted`. Both HTTP connection checks failed.
There is no live agent-launched preview or running launcher session. Start
`make preview` in a normal host terminal outside the restricted agent sandbox;
wait for both services to start before opening the URL. Restart the API after
Python source changes.

The designated Chrome window was inspected afterward: its existing host Vite
server and API responded, but the API's older snapshot returned all four
configurations as unavailable with `Source specification/CAD changed after
snapshot; restart API with matching recorded artifacts`. The page remained on
“Loading resolved configuration.” Stop the old host launcher and restart
`make preview` in that host terminal before attempting the visual checklist.
The older browser page seen before reload was stale and is not current proof.

`build/`, `runs/`, `web/dist/` and `web/node_modules/` contain local generated
data and are not preview source publication payloads. Although most run files
are ignored, `.gitignore` explicitly permits `runs/*/record.json`; do not stage
these local run records as a substitute for their excluded Parquet telemetry. A fresh checkout needs compatible CAD exports;
recorded Analysis views also require independently retained, identity-compatible
analysis artifacts. The seven previously recorded local fields are no longer compatible with the
current source identities. An in-process API check returned zero compatible
analyses for all four configurations on 2026-10-31; their prior CAD/spec hashes
differ from the current ones. Do not relabel or silently attach those fields. `scripts/wo04_register_analysis.py` registers available
recorded manifests after checking identity and artifacts; it does not solve an
analysis or convert missing evidence into a result. Saved experiment runs likewise
remain local under `runs/` and are not included in a source PR. The two runs in
the earlier browser record use the older CAD revision and cannot be replayed
against current geometry. Two new current-revision local runs were generated
for testing as described below.

## Current-revision runs (non-browser, local only)

- G80: `exp-c6af2dc4871942dc97632ae44d6613c9`, apogee 635.19 m,
  landing at 116.03 s.
- Conditional G54: `exp-ab60bd4ac5c2412a9dd85f712072bca2`, apogee
  755.53 m, landing at 132.86 s.

Both used calm wind, zero gust, direction 0°, 1 ms simulation step, 850 m
assumed site elevation and the same model-code hash. Each finished within the
120-second wall limit, saved Parquet telemetry, and passed API checks of its
current resolved-specification and CAD identities, required pose/graph channels
and recorded events. Each telemetry response contains 3,009 playback samples.
Both used CAD generator SHA-256
`1193713d0f4a7ad8393a00a0a03e7aaa04e9aa9393d2034691ef7126ae3cdd3b`.
These are preliminary unguided simulations; configurations differ in more than
motor, and the data does not establish a real-flight performance difference.
Saved runs are local artifacts and must be retained on this Mac to load them. Browser playback has not been verified for these runs.

## Visual verification once resumed

- Cycle through G80, conditional G54, finned G12 and finless G12; confirm one
  centered complete rocket, correct part tree, selection/highlight, visibility,
  isolate, show all, exploded view and reset/fit. Inspect part and vehicle details.
- Run or load two supported complete flights with matching settings, then with
  differing wind; exercise progress, replay play/pause, speed, scrub, events,
  both camera modes, trajectory fit and synchronized metric/feet/mph graphs.
  Confirm the comparison identifies all recorded differences and continues to
  the longer flight's end. Finless flight must explain why it is blocked.
- Check compatible recorded fin fields and historical temperature data if present;
  confirm legends, selection, missing coverage, time control and the persistent
  SUPERSEDED warning on the old band-model thermal record. A FAILED numerical
  field must not color active geometry. If recorded data is absent or mismatched,
  the viewer should say unavailable/incompatible rather than inventing values.
- Test normal and narrow desktop layouts; capture actual app screenshots only
  when the owner resumes browser use. The current visual state has not been checked.

The saved preview exercises preliminary unguided simulation only; PID and RL
are later work. Comparison of complete configurations can change geometry,
mounting, mass and recovery as well as motor. Thermal band results are superseded
for acceptance; the baffle transient's failed numerical validation remains failed.
Finned stress/displacement is a single-fin calculated field, not installed-root
qualification. Full work-order benchmarks, physical tests, paid-run approval,
WO-10 owner review and release gates remain unchanged.
