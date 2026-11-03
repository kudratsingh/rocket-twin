# Focused preview: terminal preflight and pending browser checks

This is a preparation and evidence checklist, not a browser test result. The
previously designated frontend agent alone owns verification in the authorized
Chrome window after the supported runtime-ownership prerequisite is resolved.
The recorded automatic ownership rejection remains unresolved. Do not retry or
bypass it with a different agent, window, headless browser or CDP.

## Normal-terminal preparation

From this checkout's root, run:

```sh
.venv/bin/python scripts/wo04_preview_preflight.py
make preview
```

If the project environment is missing, use `python3 scripts/wo04_preview_preflight.py`
with a Python 3.10+ interpreter to diagnose it.

The first command only reads local files, versions, Git metadata and fixed
loopback HTTP endpoints. It neither installs, builds, generates snapshots,
starts or stops services, changes ports, nor runs simulations. Its output is
advisory and exits successfully even when a check reports an unavailable or
mismatched item; read the individual results. Node must be >=22.12.0 and <23;
project Python is expected to be 3.11. `node_modules` being present does not
verify installed dependency versions. A missing Git checkout means no commit or
clean-tree claim can be made from that directory.

`make preview` is a **separate state-changing startup command**: it prepares
five source snapshots and launches the API on 127.0.0.1:8000 and Vite on
127.0.0.1:5173. Run it only when that is intended; keep its terminal output.
Preflight before startup commonly reports endpoints unreachable. After startup,
run preflight in another normal terminal to report actual responses from that
process. A permission error, timeout or refusal is reported exactly; an
unreachable probe does not establish whether a listener exists elsewhere.
An HTTP response alone does not prove which frontend build is served. Do not
change ports or retry through another runtime as a workaround for an ownership
or sandbox restriction.

The F2 prepared export and live F2 response, when available, show source
identity, declared hashes and each listed local source's current hash. The
comparison is limited to those records; it does not prove completeness, a
running frontend's revision, CAD acceptance or physical readiness. A `404`
with exact `{"detail":"Not Found"}` is reported as a missing route; other
404s are source/resource missing, 409 is source error or mismatch, and other
errors stay explicit. A live F2 response is compared with the prepared identity
and source list. A missing route is not a source mismatch, and a source error
is not permission to claim a prepared fallback is valid.

A production build is a separate check (`npm --prefix web run build`); record
its result and warnings, without calling it browser acceptance. Use the detailed
matrix in [the acceptance plan](../output/frontend-planning-kit-20261103/07-acceptance-and-browser-tests.md).
Record exact checkout/commit or source hashes, build, URLs, configuration and
run identities, browser version, viewport CSS size, browser zoom, DPR, steps,
observations, failures and screenshots. Never mark an unattempted case as passed.

## Designated browser-agent checklist — all pending

Once ownership is supported and the intended host preview is running, use only
the authorized window and record actual observations:

1. Open Design with a real available catalog configuration. Confirm its source
   identity, maturity and CAD availability; distinguish F2 construction from
   archived geometry. Select a small part through the tree and 3D model; confirm
   the inspector corresponds to it. Record unavailable meshes and failures.
2. Hide, isolate and restore parts; use explode and section controls. Manually
   orbit, then use explicit zoom in/out, fit visible, fit entire rocket, focus
   selected and reset. Confirm fit preserves the chosen angle, focused geometry
   remains visible and delayed loads/resize do not cause unexpected jumps.
3. Check page, tree and inspector scrolling, focus view and keyboard navigation;
   make the final control reachable. Exercise Back/Forward, view resizing and
   the viewport/zoom matrix in the acceptance plan. Capture actual CSS dimensions.
4. Switch to the source-dimensioned 2D arrangement, select a corresponding part,
   pan/zoom and fit; export and inspect the download and source labels. Confirm
   the drawing identifies its own configuration rather than presenting it as F2.
5. In Experiments and Flight Replay select two **existing compatible saved runs**
   if available. Record both identities, input and model status; play/pause,
   scrub and compare synchronized channels and units. Check event labels,
   unavailable/missing samples and recovery-attitude limitations. If two runs
   are unavailable, report that case pending; do not fabricate data or silently
   substitute a different configuration. Starting a new experiment is a
   separate explicitly observed action, not part of this read-only preflight.
6. Record console/network errors, screenshot references and pass/fail/pending
   for each case. Repeat relevant cases after UI changes. Replay performance
   requires the full representative workload and host measurements described
   in the acceptance plan; a short sample or build output cannot substitute.

These observations do not close WO-03, WO-04/05, hardware or flight gates.
