# Recorded telemetry picker — early preview increment

This is a limited WO-05 preview, not work-order acceptance. The experiment
uses the existing Python/JAX simulator and recorded telemetry. Engineering
acceptance, physical verification and flight release remain open.

## Scope

The Experiment replay offers four selectable graphs. The available names come
from the loaded, decimated telemetry response for the selected saved run and,
when present, its comparison. Existing familiar graph labels are retained;
other names use the exact recorded column name. The API describes known
columns with source (recorded Parquet or backend-derived display value), unit,
meaning and a versioned semantic identifier. Unknown columns have unknown units
and meaning; these are not inferred from their names. The graphs display only
recorded or backend-derived data and no new browser flight calculation.

Comparison is withheld when both values exist but the channel's semantic ID,
unit, source or simulation-code identity cannot be matched. Missing or invalid
samples are unavailable, not zero. Each run retains its own time samples. The
plots show decimated playback samples, not the full-resolution peak or a new
analysis. An existing backend's metadata absence also withholds comparison.
The endpoint rejects a recorded schema that collides with a derived display
column rather than overwriting it.

## Checks and pending browser observations

On 2026-10-31, `make check`, `npm --prefix web run build`, `npm --prefix web run
lint`, `npm --prefix web run format:check`, `npm --prefix web test` (7 tests),
and `.venv/bin/python -m pytest -q tests/test_experiments_api.py` (3 tests)
passed. Build reported the existing large-chunk warning; the API test emitted a
Starlette/httpx deprecation warning. Test fixtures for future/unknown columns
and mismatched metadata are synthetic and do not represent flight data.

After the host restart, the designated Chrome window loaded the current
metadata contract: the calm G80 run showed “Height above launch · backend-derived
· m”, and selecting `mass_kg` showed “mass kg · recorded-parquet · kg”. The
calm run `exp-c6af2dc4871942dc97632ae44d6613c9` and 1 m/s east-wind run
`exp-1f2178e749f049f18181e123078679bd` loaded together. Their wind differences
were shown; teal and gold tilt curves appeared. Clicking apogee set T+10.39 s,
and play/pause advanced the cursor to T+12.13 s. A screenshot of the picker
and curves and a separate replay screenshot were emitted through the computer
use tool; that tool did not persist screenshot files. Missing-channel and
incompatible-metadata behavior was tested using synthetic fixtures, not
observed against these two compatible live runs.

The accessibility tree reported the WebGL fallback text even while screenshots
showed actual rendered 3D rockets in both replay and Inspect. Therefore the
text alone was misleading; 3D rendering was visually observed and no GPU
settings were changed. In G80 Inspect, hiding the outer body revealed internal
components and reduced the visible count from 42 to 39; Show all restored 42.
Switching to the finless G12 displayed its finless 3D geometry, 51 parts, and
negative static margin warning. These observations do not establish a 60 fps
benchmark or engineering acceptance.

## Remaining full milestones

Saved-run selection and comparison now discard responses superseded by a newer
selection. Clearing a comparison or changing configuration also invalidates an
in-flight request for that view. This behavior has a frontend unit test; browser
verification of this later change remains unavailable pending resolution of the
designated window's runtime ownership.

Full WO-04 requires expanded WO-03 acceptance and compatible real static and
transient analysis fields, their identity, controls and validation evidence.
There are currently no compatible recorded fields; failed and superseded
thermal results remain unavailable. Full WO-05 still includes validated complete
configuration overrides, Arrow IPC, its other replay/event requirements, and
the 120-second, 1 kHz, 60 fps benchmark, plus compatible Analysis comparison.
This increment does not claim those checks. PID/RL and orbital capabilities
remain later work orders.
