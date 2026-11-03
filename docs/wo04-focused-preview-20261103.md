# Focused frontend preview — 2026-11-03

This is the first implementation slice from the owner's43-task planning kit,
tracked in `frontend-workbench-backlog.json`. Astra MEDIUM implemented the focused
shell, topic/source isolation and a separate source-dimensioned2D slice; Terra
HIGH implemented camera controls, replay validity and conservative bookkeeping.
Primary owns shared integration, engineering interpretation and publication.

## Usable code and source identities

- Design: recorded CAD configuration selector, existing selected-part inspector,
  hide/isolate/explode/section, explicit zoom/fit/reset/focus, collapsible parts
  and details, and focus view. Desktop CSS reserves64% for the visual; this is
  a layout rule, not a measured viewport/performance result.
- Engineering: default current G80-F2 stock construction; independent F1/A1
  topics and preserved historical C1 arrangement/forces/mass/comparison/recovery/
  thermal/electrical/assembly/verification topics. Requested construction data
  loads independently of the C1 endpoint; missing-source errors do not silently
  select a prepared result. Exact missing-route404 permits a labeled fallback.
- Experiments: supported complete reference configurations and existing steady/
  gust input controls, Python/JAX run execution, saved results and comparison.
  F2 is not offered as a full flight configuration: admitted full inertia and
  installed engineering evidence remain unavailable.
- Flight Replay: the same retained experiment component/run state, focused on
  saved runs, transport, recorded trajectory/quaternion, graphs and comparison.
  Missing event/controller/completion evidence stays unavailable. No active
  steering controller was introduced; PID and RL remain committed later work.
- Analysis: preserves existing compatible-record selection/identity checks.
  No new accepted F2 stress or temperature overlay exists. Failed ring/baffle
  fields cannot color current geometry.

Workspace navigation uses addressable links and Back/Forward-aware URL state;
legacy Engineering view links remain supported. Detailed status is in contextual
source disclosures. Unknown workspace/topic yields a visible recovery notice.
Keyboard inspection shortcuts are restricted to Design/Analysis, and Escape
exits focus view before clearing selection. These are implemented/code-checked
behaviors; their actual browser interaction remains pending.

## Replay finding

[The saved-record audit](frontend-replay-record-audit.md) independently inspected
four raw samples of the existing historical G80 run. At11.150s it points4.076°
from up while descending5.456m/s. Landing is recorded at116.029s. This establishes
a recorded-model behavior, not correct suspended-body dynamics or a renderer
pass. The exact current/saved flight-source digest matches within its defined
scope. The browser never rotates the saved attitude to match velocity.

## Startup and locations

From the repository root, use Node22 and the existing pinned environment:

```sh
make preview
```

This prepares source graphics without simulations/CAD, starts the Python API
on8000 and Vite on5173. Each optional snapshot preparation now fails independently;
a failed generated export is removed rather than retained as current.

- `http://127.0.0.1:5173/?workspace=design`
- `http://127.0.0.1:5173/?workspace=engineering&view=g80-f2`
- `http://127.0.0.1:5173/?workspace=experiments`
- `http://127.0.0.1:5173/?workspace=replay`
- `http://127.0.0.1:5173/?workspace=analysis`

F2 offline SVG/PNG drawings: `output/engineering-g80-f2/index.html`. Their compact
render record is versioned under `runs/wo04-g80-f2-walkthrough-20261103-v1/`.
The additional2D source drawing is
`output/focused-design-2d/g80-reference-source-dimensions.png` (SVG beside it).
It represents `modular-performance-v1`, not F2. The first render exposed clipped
nose-datum text; one corrected rerender took0.876s. Its header, source hashes,
units, selected fin role and origin label were inspected in the actual PNG.
The32.564s initial and final records are under
`runs/wo04-focused-2d-20261103-v1/`. These are actual offline artifact images,
not app/browser screenshots. The local
jointSTEP files under `build/wo03-g80-f2-local-cad-v2/` cover joints only, not a
complete manufacture-ready assembly.

## Current launcher outcome

A fresh `make preview` attempt prepared all five source exports successfully.
The Vite listener then failed with `listen EPERM: operation not permitted
127.0.0.1:5173` in this sandbox, and the launcher exited2 with API cleanup.
Read probes of5173/8000 could not connect; no running host preview is confirmed.
The normal-terminal command above remains the owner startup path. No new
port/runtime/permission bypass was attempted. This OS listener failure is
separate from the earlier computer-use ownership rejection.

## Verification and remaining gate

Source, SSR, camera mathematics, tests and production package build are recorded
separately from browser observation. Vite reports the existing large-bundle
warning; no frame-rate, loading-time or WebGL performance benchmark is claimed.
The detailed viewport/zoom/scroll/focus/history/run matrix remains pending.

Automatic approval review previously rejected the computer-use documentation/
runtime ownership action because the designated frontend-agent ownership
prerequisite was unsatisfied. That recorded blocker remains unresolved; no new
agent, alternate window, headless/CDP route or retry was used. Only the designated
agent in the permitted Chrome window may complete visual/interactions after
supported ownership is established. Missing browser evidence does not invalidate
the offline drawings and does not become visual acceptance.

Expanded WO-03, full WO-04/05, prototype-build, purchase, paid-compute,
WO-10 firmware owner review and flight-release gates remain unchanged.
