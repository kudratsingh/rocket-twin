# Early preview handoff — ready for visual testing

This is an early local WO-04/05 preview while expanded WO-03 remains open. It
is not engineering acceptance, build approval or flight authorization. The
latest edits have non-browser checks and the current-revision browser checks
below. These are preview checks, not full work-order or engineering acceptance.

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

The designated Chrome window initially reached an older host API snapshot,
which rejected all configurations after source changes. The owner restarted
`make preview`; after one transient 502 and a retry, the app loaded current G80
resolved SHA-256 `c18abfee…` and CAD generator `1193713d…`. Host services were
reachable for the checks below. The app and its local runs are not hosted remotely.

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
Saved runs are local artifacts and must be retained on this Mac to load them. Browser replay and comparison checks for these runs are recorded below.

## Current browser observations — 2026-10-31

In the designated Chrome window containing the Atlas Fibre G11 PDF, all four
configurations rendered a complete centered vehicle with one parts tree and
42 / 42 / 53 / 51 parts respectively. G80 and G54 masses were 739.46 g and
817.99 g; finned and finless G12 were 780.15 g and 645.94 g, with the 50 g
allowance separate. Selecting finless Body upper highlighted the part and opened
its inspector; isolate, show all and hide outer body gave 1 / 51 / 48 visible
parts. Explode reached 100%; Fit rocket framed the separated assembly, and
reassembly/reset restored the normal view. Dragging rotated the G80 view,
scrolling zoomed it, and Reset view restored its fitted camera. The finless
experiment button was disabled with the unsupported-unguided explanation.

Both current-revision saved runs loaded and compared in the app. Play/Pause
advanced and stopped time, apogee jumped to 10.39 s, 4× speed and free/fit
trajectory camera controls responded, and the comparison scrubber reached
132.85 s (past G80 landing at 116.03 s). Clicking a plotted graph moved the
shared cursor to 65.51 s. Teal/gold curves, metre/foot and m/s/mph labels,
acceleration, tilt from vertical and horizontal-distance graphs were visible;
matching calm settings and configuration/input differences were shown. Those
two saved runs were generated and checked through the actual API beforehand.

A further browser-triggered G80 run changed steady wind to 1 m/s toward
90° with zero gust: `exp-1f2178e749f049f18181e123078679bd`. The app displayed
preparation progress, saved the complete result, loaded it, played/paused it,
jumped to apogee and compared it with calm G80
`exp-c6af2dc4871942dc97632ae44d6613c9`. The displayed differences identified
wind speed, direction and the two wind-vector case values. Both records have
identical input, resolved-specification, CAD and simulation-code hashes. The
wind run's preliminary modeled apogee was 634.91 m and horizontal landing
displacement was 108.00 m; these are simulated results, not flight evidence.

Analysis displayed an identity mismatch, neutral geometry and “no overlay
attached” for stale records. The historical thermal export was labeled both
incompatible and SUPERSEDED, and the Inspect summary explicitly listed the
replacement-baffle numerical result as FAILED. No current compatible analysis
field exists, so a compatible stress/temperature overlay was not visually
verified. The designated Chrome tab emitted actual app screenshots through the
computer-use tool for Inspect, Replay and Analysis; no screenshot files were
persisted by that API. After a CSS-only change, CG and CP labels appear on
opposite sides of the unchanged markers at the fitted view. All four configurations were checked;
G80 and finless camera reset were exercised. At 150% browser zoom the tree
wraps names and moves mass to a separate line, and footer text wraps. This
reduces visible rows but keeps the inspected text readable; the 150% check is
not a measured window-width or mobile-layout acceptance test. Browser zoom was
restored to 125%.

The saved preview exercises preliminary unguided simulation only; PID and RL
are later work. Comparison of complete configurations can change geometry,
mounting, mass and recovery as well as motor. Thermal band results are superseded
for acceptance; the baffle transient's failed numerical validation remains failed.
Finned stress/displacement is a single-fin calculated field, not installed-root
qualification. Full work-order benchmarks, physical tests, paid-run approval,
WO-10 owner review and release gates remain unchanged.
