# RP1-first frontend release candidate — November 7, 2026

The frontend source implementation is integrated from main including PRs90/91.
Dedicated custom G80 engineering remains first; G54 and G12 PID-to-RL stay separate
committed tracks. No engineering, material, launch, prototype-build or flight
criterion is changed. All five supplier/lab inquiry drafts remain **UNSENT**.

**Release acceptance remains open.** The owner authorized the sole open Chrome
window and necessary tabs, resolving the previous project-level designation
question. Sole verifier `/root/browser_access_sol` made one supported inventory
call: Chrome was running, but it returned **“The browser access host is
unavailable”**, with no browser/tab exposed. There was no new automatic-review
rejection. No alternative browser, native-app, headless/CDP or repeated claim was
used. [Access evidence and full pending protocol](studies/frontend-release-20261107/browser-access.md).

## Start and inspect

In a normal host Terminal, stop an older preview with Ctrl-C, then:

```sh
cd /Users/kudratsingh/Machine-Learning-Projects/rocket-twin
make preview
```

The launcher explicitly generates the separate RP1 display assets, prepares
source snapshots, starts the Python API on8000 and Vite on5173. Requests never
run CAD. Normal-host listener/startup observation is still pending; sandbox tests
and the owner's opened page do not prove a particular backend revision.

- Design: `http://127.0.0.1:5173/?workspace=design&design=G80-F2-RP1-AD1-definition-v2`.
- Engineering: `http://127.0.0.1:5173/?workspace=engineering&view=rp1-connections`.
- Experiments: `http://127.0.0.1:5173/?workspace=experiments&design=G80-F2-RP1-AD1-definition-v2`.
  RP1 execution is unavailable. Explicitly choose an eligible complete archived
  configuration; this changes the experiment context, not the working Design.
- Replay: use the saved-run library, including diagnostic
  `exp-cf9e47a650074144856caf50775846d2`. URLs retain primary/comparison IDs and
  an independent `experiment` configuration. Source/CAD/frame checks precede load.
- Analysis: `http://127.0.0.1:5173/?workspace=analysis&design=G80-F2-RP1-AD1-definition-v2`.
  Recorded RP1 scalar findings are available; spatial overlays stay unavailable.

## RP1's own inspection geometry

[Geometry definition, verification and measurement list](studies/rp1-inspection-geometry-20261107/report.md)
and [all55 coverage rows](studies/rp1-inspection-geometry-20261107/coverage.md)
identify every stable source part:

| Source-record class | Count | Display behavior |
| --- | ---: | --- |
| Source-dimensioned ideal geometry |10| Separate selectable GLBs; dimensions remain estimates |
| Simplified nominal envelopes |16| Selectable, visibly labeled; purchased details/fit are not invented |
| Mass/process allowances |25| Selectable list/evidence records, no fake separate solid |
| Missing installed geometry |4| Explicit missing state, no substituted historical mesh |

The26 mesh-bearing records include bundled physical instances where the source
uses a set, for example three fin panels, integral tabs and six root wedges.
Source positions are global; the frontend must not translate them twice.
GLB units are metres; CAD uses millimetres. Nose tip is at viewerY=1.250m,
aft length datumY=0; X=body+y and Z=body-z. Bounds/scale, corrected6.8mm body
slots and109.4mm tabs have actual-mesh tests. Forward-notch roundovers and
finished joints are not modeled as qualified geometry.

Inspection identity `238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`
is separate from canonical CAD/resolved-flight identities, which remain null.
No mass or inertia is generated from these display solids. The3Dmass/CG/CP markers
use an explicitly selected saved estimated case (55/68g harness probes and full
50g growth already included), with nominal/adverse cases separately labeled.
They do not call or infer a canonical burn-state model. The exporter is
outside `src/cad` so archived CAD identity `1193713d…` remains unchanged.
The active specification, AD1/D1 records, FP1/FR1 status and original load gates
are frozen. A matching RP1 flight model is not created by a display mesh.

Missing geometry: shield sectors/terminations; actual dressed Kevlar wrap,
knots and moving route; rail buttons; rail backers. Later measurements of
stock/walls, motor/retainer seat, notch/knot passage and guide fittings can refine
these shapes. Hardware is unpurchased; the measurement list is planning only.
Dimensions cannot establish joint strength, hot behavior or flutter.

## Completed source workflows and evidence limits

| Workflow | Implemented and checked in repository | Still needs observation/evidence |
| --- | --- | --- |
| Design | Independent left panels, source-linked2D/3D, fit/focus, visibility/section/explode/restore,55part details and maturity | Actual layouts/picks/scroll/keyboard at1440×900,1280×720 and narrow viewport |
| Engineering | Fin/recovery source drawings, exact part/revision links, dimensions, failed/unknown findings and portable source exports | Browser round trip/history/download/error/readability |
| Single experiments | Complete supported configurations, seed/preset/wind/gust, effective request/model identity, idempotency, saved attempts/draft reuse/errors | Live Run button/progress/error recovery on normal host |
| Batches |2–4members, one serial CPU slot, declared steps/storage, failure retention, cooperative cancellation and interruption | Reload/member selection/cancel-before-termination in browser |
| Replay/comparison | Actual quaternion/position/CG interpolation, exact windows/events, event alignment, plot ranges/gaps, metric/familiar units, CSV/JSON/Arrow | Scrub/event/camera/unequal-window visual behavior and downloads |
| Analysis | RP1 failed component vs unknown installed evidence; exact field guards; recorded-case comparison/CSV with independent clocks and fixed legend | Browser missing-data behavior; a real compatible field pair for covered-data visual paths |
| Navigation | Design/evidence links and separate experimental context; saved primary/comparison routes; current source status | Back/Forward/reload and cross-workspace browser transitions |

[Experiment implementation and resource contract](studies/frontend-release-20261107/experiments.md)
records one local CPU worker, bounded batches and immutable terminal attempts.
Cancellation acknowledges a request; compiled JAX work may finish before a safe
boundary permits termination. There is no automatic retry or process-spanning
multiworker ownership promise. Worker-complete can still mean partial trajectory.

[Replay pose reference](studies/replay-pose-20261107/report.md) preserves the
T+11.150s diagnostic: approximately4.076° from upright while descending5.456m/s.
Recovery attitude remains approximate; no canopy, line or separated-body pose is
fabricated. Missing attitude with valid position gets a labeled marker. Each
comparison actor is absent outside its own recorded support.

[Data readiness](studies/frontend-release-20261107/data-readiness.md) establishes
that the archived G54 run `exp-ab60bd4ac5c2412a9dd85f712072bca2` supplies132856raw
rows over132.856s at the recorded1ms step with matching source/CAD/42part-shape
identities. Normal playback remains approximately3000native samples plus event
neighbours. The explicit full-rate benchmark mode admits at most150000rows and
64raw scalar channels before materialization; nine derived channels add at most
73returned channels. Actual browser60fps/load/scrub/memory acceptance has not
occurred. Instrumentation reports measurements only when that host supplies them.
The reserialized JSON byte count is not wire size or heap use.

All27 existing registered analysis manifests have valid payload hashes but
incompatible current geometry identities. They remain inspectable as incompatible
records, never accepted current overlays. RP1 scalar calculations are not fields:
7.301MPa/1.805mm belong to the saved optimistic failed component model, while
installed movement/peel and finished recovery capacity remain unavailable.
No new solver, repinning, pressure map, temperature map or CFD is introduced.
Comparison tables do not authorize geometry attachment or physical acceptance.

[Actual-data backend smoke](studies/frontend-release-20261107/backend-smoke.md)
completed36in-process GETs in8.433CPU/8.930wall seconds, under20/60limits:
all26RP1GLBs, actual saved G54 default/native/Arrow paths and empty RP1fieldcatalog.
All383owner-record hashes remained unchanged. Native132856×48data serialized to
113412840response bytes; normal/Arrow stayed at3009samples. This is not a host
listener, browser transfer, browser heap or FPS observation.

## Explicit release dispositions

- **RV-17 optional Mission Control:** deferred, outside this release. The five
  focused workspaces are the product entry points. RV-Q35 is not applicable.
- **RV-21 fidelity/controlled parametric editing:** deferred to its separately
  scoped work and dependent engineering gates. No in-place design/mesh mutation
  or silent reuse of old mass/inertia/aero/results is provided. PID and RL remain
  committed WO-06/07 milestones, not optional frontend features.
- **Schematic canopy/separated recovery animation:** omitted. There is no
  compatible separate-body evidence; the honest recorded one-body replay stays.
- **Unavailable fields/materials/guide hardware:** display supported missing states;
  do not manufacture engineering results to fill a panel. Full covered-field
  visual acceptance still needs a compatible dataset as well as browser access.

## Verification and remaining owner/runtime action

The21task ledger and37check matrix distinguish source checks from browser
observations. The original43FTtasks remain traceable. Source-verified tasks stay
partial until their applicable browser criteria are actually exercised. No image,
SSR test, passing CI or in-process API call is a browser acceptance substitute.

The owner/provider must make the supported **browser access host** available.
Ordinary documented setup is ChatGPT→Work→Plugins→Chrome and its extension
connection, if offered. If it is already connected, provider repair is needed;
no exposed command fixes this host. After a reported connection change, only the
named verifier may use the authorized current Chrome window. Primary/other agents
must abstain. No additional broad permission or supplier reply is needed.

Confirm normal-host `make preview`, then execute the linked protocol at the three
requested viewports. Record console/network errors, actual screenshots, full
scroll/selection/export states, timed long-run workload and compatible-data gaps.
Failures require fixes and affected rechecks on the combined release. Browser
acceptance, engineering acceptance, prototype-build authorization, firmware review
and flight release remain distinct.

Offline artifacts are separately useful: the actual-GLB contact sheet at
`output/frontend-release-20261107/rp1-inspection-contact-sheet.png`, its hash
manifest, source inspector HTML/SVG under `output/frontend-release-20261107/source-inspector/`,
and the RP1 connection pack at `output/rp1-connections-20261107/`. They preserve
source/configuration/status. None is a browser screenshot; static selection
buttons are inert. [Offline geometry QA](studies/frontend-release-20261107/offline-geometry.md).
