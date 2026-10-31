# Early inspection and experiment preview

Owner-authorized limited WO-04/05 work under ADR-0009; expanded WO-03 remains open.
This app displays preliminary designs and simulated, unguided flights. It does not
approve fabrication or launch. PID and reinforcement learning remain WO-06/07.

## Start locally

```zsh
cd /Users/kudratsingh/Machine-Learning-Projects/rocket-twin
make preview
```

Open <http://127.0.0.1:5173>. The launcher starts the Python API on port 8000 and
Vite on port 5173; Ctrl-C stops the launcher. Python dependencies are pinned in
`requirements-wo04.txt`, Node in `docs/ENVIRONMENT.md`, and web dependencies in
`web/package-lock.json`. Use `make setup-viewer` for the Python viewer dependencies.
If locked web packages are absent, install them explicitly with `npm --prefix web ci`; the launcher does not install dependencies. CAD must
already be exported with `make cad`; the API never runs CAD or engineering solvers.

The owner started the host services because agent shell binding/network access is
restricted. New backend source needs a service restart. After the Analysis discovery
refresh is loaded, newly registered offline fields appear without later restarts.

## Executed browser checks

Checks used only the owner's designated Chrome window containing the Atlas Fibre
G11 PDF; Rocket Twin is a separate tab in that same window.

| Action | Observed result |
|---|---|
| Switch G80 → G54 → finned G12 → finless G12 | One parts list and one viewer after every switch; 42 / 42 / 53 / 51 source-linked parts |
| Check masses against resolved backend documents | G80 739.46 g; G54 817.99 g; finned G12 780.15 g; finless G12 645.94 g, before the separate 50 g allowance |
| Select a component | Selected motor mount highlights and opens its inspector with material, function, dimensions and estimated mass |
| Isolate / show all / hide outer body | Finless visibility changes to 1 / 51 / 48 parts respectively |
| Explode and reset | Display-only separation reaches 100%; configuration reset restores its visibility/layout |
| Run G80 in calm air from the browser | Real Python/shared JAX execution saves a complete run; replay, event buttons and graphs load |
| Play/pause and select maximum height | Time advances, pauses, and jumps to the recorded maximum-height event |
| Run conditional G54, 3 m/s wind toward 90°, zero gust | Complete second run, correct settings and matching CAD load |
| Compare G80 and G54 saved runs | Shared replay/graph time, separate teal/gold trajectories and overlaid graphs; both settings displayed |

The switching defect was duplicate React sibling keys retaining earlier parts
panels. Unique component keys correct the cause. A separate narrow-desktop layout
correction removes the fixed 1,120 px minimum; its final browser check remains pending.

## Recorded experiment evidence

Both runs use the existing 1 ms shared simulator, seed zero, 850 m assumed site
elevation, simulated sensor noise and locked gimbal, with recovery recorded before
the 360 s horizon. They do not include the separate 50 g growth allowance.

| Run | Settings | Maximum height | Maximum speed | Guide departure speed | Horizontal landing displacement |
|---|---|---:|---:|---:|---:|
| `exp-173525a242be493e8e3268471b8e16aa` | G80, calm | 635.19 m | 149.57 m/s | 19.08 m/s | 1.88 m |
| `exp-da02d58e35af404faf2802bea54c942b` | Conditional G54, 3 m/s eastward wind | 752.54 m | 141.08 m/s | 19.97 m/s | 350.39 m |

These differently configured runs verify the comparison workflow; they cannot isolate
the motor's performance effect. The run records retain resolved/specification hashes,
CAD revision, input hashes, model hash, settings, events and limitations alongside
full Parquet telemetry. Both use CAD revision
`671116b6a3e90d111b37d7e6dcab7cb17a20821eb6ff6b52475dcb5a27bbf80f`.
Replay uses recorded north/east/down position and quaternions, with a tested transform
to the CAD/display axes. No browser flight integration.

## Current-revision browser continuation — 2026-10-31

After the owner restarted the host services, the current CAD identity and the
two newer saved runs were checked in the designated Chrome window. A subsequent
browser-triggered G80 experiment at 1 m/s wind toward 90° and zero gust,
`exp-1f2178e749f049f18181e123078679bd`, completed, loaded, replayed and was
compared with the current calm G80 run. The CG/CP labels were separated by a
CSS-only change; marker positions and backend values remain unchanged. See the
[current handoff](wo04-preview-handoff.md) for exact observed actions, run IDs,
layout limitations and the still-unavailable compatible analysis overlays. The
older browser evidence below remains historical.

## Current identity update — 2026-10-31

The seven exports described below and the two browser-tested runs above use an
older source/CAD identity. A current in-process API check finds zero compatible
recorded Analysis manifests in all four configurations; the earlier runs also
cannot attach to current CAD. They remain historical observations, not current
visual verification. New compatible evidence is required; no failed or
superseded thermal model should be rerun merely to populate the viewer. See
[the current handoff](wo04-preview-handoff.md).

## Analysis and remaining gates (earlier snapshot)

Seven fresh exact-identity exports are registered locally: four part-mean transient
thermal records and three single-fin nominal structural records. They are calculated,
unmeasured evidence. Stress and displacement cover one analyzed fin instance;
other parts remain unavailable. Temperature is uniform per part, not a resolved
through-wall field. Displacement magnitude does not establish installed-root strength
or imply that a deformed shape was calculated for the full rocket. Incompatible
historical analyses cannot attach. Browser acceptance of the refreshed overlays
remains pending until the running backend loads the discovery refresh.

The preview is not full WO-04/05 completion. Remaining work includes final Analysis
browser checks, arbitrary telemetry selection, the full performance benchmarks,
later parameter overrides, and prerequisite WO-03 engineering acceptance.
Finless unguided runs are rejected; static finless inspection remains available.
G54 exact motor/source/hardware and thermal/CG dependencies remain conditional.
The G12 5 m usable guide assumption is unconfirmed. Recovery, drag, wind, actuator and
high-angle behavior remain bounded models, not flight evidence. Physical tests,
paid-run authorization, WO-10 owner review and flight-release gates remain intact.
