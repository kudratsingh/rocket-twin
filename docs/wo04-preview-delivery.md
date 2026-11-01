# Local inspection and experiment preview

This is the owner's early, read-only digital-twin preview. It uses the actual
resolved configurations, CAD exports and the existing Python/JAX simulator.
G80 is the current engineering priority; G54 is a conditional upgrade and G12
finned and eventual finless TVC remain committed trainer/control directions.
Rendering or running a prediction does not establish engineering acceptance,
physical qualification or flight authorization.

## Start and use

On this Mac, from the repository root, start the existing pinned environment in
a normal host terminal:

```zsh
make preview
```

Wait for the API and Vite servers, then open <http://127.0.0.1:5173>. Leave the
terminal running; Ctrl-C stops the launcher. If preparation is missing, the
existing pinned setup commands are `make setup-viewer` and `npm --prefix web ci`;
`make cad` generates the separately required local CAD exports. No installation
is performed by `make preview` itself. CAD generation does not close WO-03.

- In **Inspect**, choose a configuration at the top. Select a part in the tree
  to see its function, material, modeled mass, source and open evidence. Use
  Hide outer body, Isolate part and Show all to examine the assembly. The
  exploded slider separates parts; Fit rocket reframes the current view.
- In **Experiment**, choose a supported complete finned configuration, enter
  steady wind speed and direction and gust amplitude, then run on CPU. Finless
  unguided flight is unsupported. Select a saved run to replay it, use the time
  slider or event buttons, choose a telemetry channel for each graph, and use
  Compare beside another run to overlay compatible channels and see settings
  differences. These are preliminary unguided simulated predictions.
- **Analysis** shows recorded fields only when their design and geometry
  identities match. No current compatible fields are available; stale,
  superseded and failed results remain identified as such. Missing evidence
  does not prevent basic inspection or make a passing result.

Saved runs and their Parquet telemetry live locally under `runs/`; CAD exports
live under `build/`. They are not carried by a source-only checkout. The viewer
cannot replay an incompatible CAD revision as though it were current.

## Verification and current availability

On 2026-10-31, after the owner restarted `make preview`, the designated Chrome
window loaded all four configurations: G80 (42 parts), G54 (42), finned G12
(53) and finless G12 (51). The G80, G54 and finned G12 Body upper inspectors
each displayed function, cardboard, modeled 56.03 g mass and open/unvalidated
evidence; finless showed the same information before the restart. G80 and G12
finned 3D geometry was visible after restart; G54 and finless 3D were also
visually observed. In finless Inspect, Isolate changed 51 visible parts to 1,
Show all restored 51, and the exploded slider reached 100%; Fit rocket framed
the separated assembly. In G80, Hide outer body revealed internal components
and Show all restored the assembly. Screenshots were emitted by the computer-use
tool; no screenshot files were persisted.

The two locally saved G80 runs reloaded after restart: calm
`exp-c6af2dc4871942dc97632ae44d6613c9` and 1 m/s eastward wind
`exp-1f2178e749f049f18181e123078679bd`. Their comparison displayed the wind
setting differences; the apogee event set the shared cursor to 10.39 s. In an
earlier same-day check, play/pause advanced the cursor, raw and derived channel
pickers displayed source and units, and both tilt curves and a 3D replay were
visibly rendered. These are actual saved preliminary simulator results, not
physical flight data. Finless Run on CPU was disabled with an explicit
unsupported-unguided explanation. Analysis showed a CAD/configuration identity
mismatch, all 51 parts unavailable, and no overlay attached. The failed baffle
result remained visible in the summary.

The previous connection failure occurred during a configuration switch; after
restart it did not recur in these checks. Web typecheck, lint, production build
and seven frontend tests passed; API and experiment tests passed (13 tests),
including a bounded real JAX rollout in a temporary test directory. The build
reported a large-chunk warning and the API tests a Starlette/httpx deprecation
warning. No 60 fps benchmark or current compatible Analysis overlay was
established. See [the preview handoff](wo04-preview-handoff.md) and
[telemetry picker record](wo05-telemetry-picker-preview.md) for prior detail.

Full WO-03, WO-04 and WO-05 acceptance remain open. Structural, thermal,
tolerance/motion, physical tests, paid-run approval, WO-10 owner review and
flight-release gates are unchanged. PID and RL controls remain later work.

## Availability recheck — 2026-11-01

The designated Chrome agent refreshed the existing preview tab and observed
the42-part G80 inspector,739.46g nominal mass and rendered CAD rocket. An
actual screenshot was emitted through computer use; no image file was saved.
The current shell could not connect to or bind the preview ports, whereas
browser-to-host access worked. No owner restart was needed, and no frontend
code, geometry or simulator was changed by this availability check. The
earlier four-configuration, visibility, replay and comparison observations
remain dated as above; this was not a repeated full verification campaign.
