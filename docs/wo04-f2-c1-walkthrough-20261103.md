# F2-C1 connection walkthrough — early preview

Open `http://127.0.0.1:5173/?workspace=engineering&view=g80-f2-c1` after
`make preview` in a normal terminal at the repository root. The preparation
target is `make workbench-f2-c1`; it reads recorded evidence and writes
`web/public/engineering-workbench/f2-c1.json`. It does not run CAD, structural,
thermal or flight calculations. The API route is
`GET /api/engineering/workbench-g80-f2-c1`.

This is the separate **G80-F2-C1-fit-proposal-v2** study, with specification SHA
`f4f62b8c2051bc1f50bad5738ad8597d63671d953a1da2a70c18ec6f8bd75201`.
It is not historical C1, the archived 72-part model, or an adopted replacement
for frozen F2. Geometry is dimensioned concept/section graphics, not an accepted
whole-vehicle CAD assembly. No full physical inertia is available.

## What can be opened

| View | What it explains | Evidence boundary |
| --- | --- | --- |
| Clickable connection graph | Harness/eye/ring and motor/fin routes into body, motor tube and tabs; selecting a node lists its actual source parts | Arrows show force routes, not demonstrated capacity or equal sharing |
| Blind-notch longitudinal section | Front web, tab, filled bond and direction of recovery pull; dimensions use millimetres from the nose | A simplified local section shows why pull opens the floor gap; it is not mechanical capture |
| Fit table | Seven minimum/nominal/maximum stacks against the unchanged 0.1 mm criterion, including per-flank clearance | Proposed receiving/cut windows and environmental bounds remain unmeasured |
| Coupled case table | Frozen F2 versus proposal, nominal/adverse mass, loaded/burnout balance and stability, separate growth, guide and recovery proxy | Saved backend values; 1.8 m travel is conditional and not adopted |
| Numerical/status panels | Two completed grids, capped fine attempts, unavailable convergence and incompatible diagnostic field export | No installed strength acceptance or accepted spatial stress/temperature colouring |

The inspector uses 53 allocation rows, including process budgets. These are not
53 qualified manufactured parts. Source parameters retain their explicit SI
names; display dimensions and balance points use labelled millimetres, masses
use grams, and guide speeds use metres per second. A calibre is one body diameter.
The common-acceleration recovery proxy is distinct from a measured peak opening
force or a validated deployment simulation.

## Offline drawing pack and actual observations

`node scripts/wo04_export_f2_c1_drawings.mjs` exports the actual React/SVG graph
and section using the prepared snapshot and the existing native AppKit renderer.
Open `output/engineering-f2-c1/index.html` for the gallery, SVG originals, PNGs
and ZIP. The export record is
`runs/wo04-f2-c1-walkthrough-20261103-v1/record.json`; generated images remain
local bulk artifacts. Reproduction requires the prepared snapshot, web
dependencies and the existing Mac renderer; it does not open a browser.

The first graph image revealed poor generic port placement and unreadable edge
labels. That failed visual attempt is retained in the compact record and local
`first-render` directory. One correction used a vertical recovery route,
outside node ports, explicit arrowhead polygons and dark label backings. The
primary inspected the corrected **1200 × 1080** graph and **1200 × 430** section
at original resolution: labels, arrows, dimensions, source/status legend and
the recovery direction were readable; no observed clipping remained. Later
source-only refreshes preserved the visible SVG content. These are real offline
images, **not browser screenshots or interaction acceptance**.

## Verification and remaining limits

The local web suite passed 66 tests; TypeScript, ESLint, formatting and the
packaged build passed. The Python suite passed 403 tests plus three subtests
before the burnout metadata addition; focused evidence/API/field tests were
then repeated for that change. These support source routing, fail-closed
identity handling and preservation of earlier code. They do not qualify joints,
thermal performance, flutter, launch equipment or a live browser workflow.

Inspection refinement PR68 is merged after both required jobs passed at
`798d20ae722549f90648f5a2d709066156630c0b`. This connection-study increment is
published separately with the engineering evidence and its exact hosted head.

Vite binding `127.0.0.1:5173` remains denied by the sandbox (`listen EPERM`);
the URL is a startup target, not a verified running endpoint. The existing
designated-browser runtime-ownership action was rejected by automatic approval
review. No browser retry, alternate window, headless route or bypass was used.
Click selection, responsive layout, downloading SVGs, source fallback and the
preserved inspection/experiment/replay interactions remain on the original
designated-agent checklist. Only a plain API `404 Not Found` permits the prepared
fallback; missing/conflicting evidence otherwise stays unavailable.

Installed recovery anchor/bond strength, finished hardware, actual hot/wet fits,
motor/retainer contact, thermal matrix and fin/root/flutter evidence remain open.
G54 and G12 PID-to-RL need independent checks. This preview closes no build,
physical-test, firmware, paid-run or flight-release gate and does not complete
WO-03, full WO-04 or WO-05.
