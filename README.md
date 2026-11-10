# rocket-twin

**Current full frontend revamp:** [Design workbench v2](docs/frontend-design-workbench-v2/README.md)
plans detailed component CAD/diagrams, a reusable parts bank, separate virtual
rocket drafts and complete alternative testing in ten phases with46 tasks. It
retains the current inspector/experiments/replay and all engineering/physical
gates. The first implementation is the current-source read-only parts bank;
full draft building and candidate simulation follow their data prerequisites.


A custom rocket and its digital twin: YAML vehicle specifications, parametric CAD,
a JAX flight simulator, and a web workbench for inspecting designs and replaying
experiments. The project connects mechanical design, materials and recovery
engineering with committed PID-to-reinforcement-learning control development.

The current priority is a conventional fixed-motor **G80** engineering package.
A **G54** performance upgrade and **G12 thrust-vector-control** trainer remain
separate tracks. Custom construction and practical performance are core goals;
certified commercial motors and suitable purchased parts complement the build.

**Repository:** public by owner confirmation (November 4, 2026). The next G80 engineering milestone is [VP1 material and attachment validation](docs/validation/rp1-vp1/package-summary.md). Physical interchangeability with G12 is optional; the first G80 remains a dedicated conventional build.

The current RP1 preview includes its own source-derived 3D inspection model,
linked Engineering drawings and recorded findings. Archived supported vehicles
can run local CPU experiments and replay/compare saved telemetry. Live browser
checks and actual screenshots are recorded in
[the release handoff](docs/frontend-release-20261107.md). Desktop layout and
explicit Side fitting pass measured thresholds; the full native-rate 60 fps
benchmark remains failed. Bounded live browser checks are recorded. The latest experiment comparison retains RP1 as the working design; metadata downloaded and whole Design was restored in the subsequent authorized check. Broader unexecuted branches remain explicit. This is a preliminary inspection/experiment preview,
not engineering, prototype-build or flight approval.

## Parts bank · first v2 slice

Select current G80 RP1/AD1 v2 and open **Parts bank** in the header. Browse55 source
definitions and55 installed occurrences, search/filter and inspect dimensions,
material, mass basis, source-budget cost, geometry and identity findings.
**Inspect installed part** returns to that exact part and its existing CAD/evidence.
The catalog is read-only; Add/Replace/Connect arrive with the separate-draft builder.
Existing GLBs are installed inspection references, not reusable local product CAD.
P61/P62 actual Chrome observations cover the source-snapshot/search/selection flow,
visible warnings and scroll reset. New API routes have in-process test evidence;
the current host used the explicitly labeled prepared snapshot after404.
[Details and limits](docs/studies/frontend-parts-bank-20261109/integration.md).

**Template recipes** now names five source groups and their features. Two nominal
local CAD cases (motor tube cut and plain aft ring) have independent 3D previews
and matching millimetre STEP downloads. The other groups preserve their exact
source and local-template limits. Parameter selection highlights related feature
rows; installed inspection returns to the existing stable part. No template adds
mass, adopts hardware or changes RP1. `make part-template-cad` verifies/copies the
completed local cache; a missing fresh-clone cache remains explicitly unavailable.
[Current paths and evidence](docs/studies/frontend-autonomous-20261109/integration.md).

**Saved drafts** provides a separate local source fork with label/notes saves,
immutable history and explicit stale-save recovery. It preserves the original 55
source accounting records. Closing/reopening the Parts bank preserves unsaved
text for the same loaded source; a page reload does not. Add/Replace/Connect,
blank drafts and candidate simulation remain later steps. The owner restarted the normal-host preview. Actual browser fork/save/reload,
read-only history and stale-write recovery pass their bounded checks, with
independent persisted-byte readback. **Download saved review JSON** exports the
shown saved revision, excluding unsaved edits and geometry assets. The actual
772,101-byte download was read back and verified. It is a structured review copy,
not byte-exact backup, import/restore artifact or simulation configuration. [Practical steps](docs/studies/frontend-draft-foundation-20261109/frontend.md).

**Unsaved source planning intents** is an explicit preview inside a current saved
draft. Prepare it, select an original occurrence, mark an exclusion intent, then
restore it. The source model and55-row ledger stay intact; the tool explains the
unresolved function and grants no mass credit, physical removal or candidate pass.
P85/P86 observed this path and independently retained all saved bytes. Intents are
not saved and reset when the parent revision/page changes. [Scope](docs/studies/frontend-draft-composition-20261109/integration.md).

For ongoing local API development, `make preview-dev` starts the same localhost
ports with source-only Python reload; normal `make preview` remains available.
The owner has started this mode and the new API path works. No listener was started
from the restricted agent runtime, and source reload cycling itself remains untested.

Engineering's **Physics & control system map** links selectable blocks to actual
source contracts, units and frames. It separates the current fixed/unguided G80
from the committed future G12 estimator/guidance/PID/RL/actuator loop, with missing
RP1 flight inputs, wiring and physical evidence explicit. **Download source SVG**
exports the current graph, full flow key and selected block with source labels.
The actual download and offline rendering pass; standalone Chrome reopening
remains unexecuted. [Export evidence](docs/studies/frontend-system-map-20261109/export.md).

## Recorded assembly and service

Open **Engineering → RP1 assembly & service**, then choose one of seven concept
steps. Select a schematic group to read its source notes and open its exact part
in Design. The sequence explains loop/protection routing, inspection before aft
closure, motor access and the permanently buried recovery anchor. It preserves
failed/unknown joint findings and is not approved fabrication or service
instructions. P79 observed the final step and readable upper controls/diagram;
lower details and part-return interactions remain only partially verified.
[Source path and evidence](docs/studies/frontend-rp1-assembly-20261109/integration.md).

## Component structure close-ups

The current RP1 **Details → Inside the component** adds two source-based views:
actual manufacturer PCB pads/routes/holes with footprint and net selection, and
18 selectable fin/tab/gusset/tube/ring pieces from the existing mechanical model.
Body cutaways, illustrative separation and independent Fit/zoom make the
construction easier to inspect. Unknown package heights, adhesive geometry and
unqualified joints remain explicit. These are inspection references, not new
vehicle parts or engineering approval. [Open the views and source limits](docs/studies/frontend-component-depth-20261108/integration.md).

## Desktop engineering inspection

PR116 is merged after both required checks. [Latest verified walkthrough](docs/studies/frontend-desktop-evidence-closeout-20261108.md) includes actual ring-detail, source-drawing, keyboard, experiment and export evidence, plus the local screenshot/CAD packs. Full engineering and frontend benchmark gates remain open.

The four archived reference/controls configurations also have registered part
GLB/STEP/STL and whole-assembly GLB/STEP access. Use **Whole rocket assembly files**
without clearing a selected component. Legacy part STEP is local millimetres;
assembly STEP is placed geometry; STL has no encoded units and may follow print
packing. `make workbench-archived-cad` verifies/copies existing local files without
regenerating CAD. [Archive source and native evidence](docs/studies/frontend-archive-downloads-20261108/integration.md).

The next source-checked inspection increment gives dual-function RP1 parts
separate fin-root and recovery routes, with exact part/revision links back to
Design. Unmapped connections remain unavailable.
[Connection navigation](docs/studies/frontend-rp1-evidence-routing-20261108/integration.md)
· [Future detail evidence](docs/studies/frontend-desktop-detail-20261108/measurement-unlocks.md).
The source-bound round trip and explicit selection clear were subsequently verified in the browser; original failures remain recorded.

Detailed desktop inspection, CAD/connection understanding, graphics, experiments
and replay take priority over mobile layout polish. Current source-based tools
include interior/joint isolation, adjustable section planes, recorded3D dimensions,
and selected-part/assembly GLB plus inspection STEP/provenance downloads.
[Walkthrough](docs/studies/frontend-desktop-detail-20261108/walkthrough.md)
· [Local portable file pack](output/rp1-desktop-inspection-pack/index.html).
The STEP files reconstruct26 represented records/36solids with nominal and envelope
status retained;29 records still have no solid. Manufacturing details, qualified
connections and RP1 full flight inertia remain unavailable. Historical models/runs
are not substituted. All supplier/lab inquiries remain UNSENT.

Optional completed local CAD preparation is `make workbench-rp1-step`; it verifies
and copies existing registered files and never regenerates CAD. Start the app with
`make preview`, then open http://127.0.0.1:5173/. Actual native feature observations
and remaining source/engineering limits are linked in the walkthrough.

A new actual archived G80 Tiny run completed with wind1m/s and a45second partial
trajectory. The browser loaded it, compared it with a matching calm-air baseline,
jumped to apogee and exported the playback CSV. Landing is not recorded. The JSON
metadata export completed after explicit local-site authorization; no permission
prompt or setting change occurred on the actual completion path. [Run and export evidence](docs/studies/frontend-desktop-experiment-20261108/integration.md).

## What works today

- **Vehicle models:** typed YAML parts, geometry, mass, centre of gravity, full
  inertia, aerodynamic stability, motor curves, build inventories and per-part
  explanations. Each complete configuration has its own identity and evidence.
- **Flight simulation:** a shared JAX 6-DOF core with changing mass/inertia,
  quaternions, launch-guide constraints, aerodynamics, wind, TVC, sensor/servo
  models and simplified recovery. CPU experiments use this same core.
- **CAD and engineering tools:** CadQuery part generators and STEP/STL/GLB exports,
  plus structural, thermal, fit, recovery and mass-budget studies. Recorded
  failures and method limits stay visible alongside passing numerical checks.
- **Inspection workbench:** React/Three.js Design, Engineering, Experiments,
  Flight Replay and Analysis workspaces, backed by FastAPI. Inspect parts and
  source-linked drawings, run supported unguided CPU experiments, and replay
  recorded trajectories and telemetry.
- **Evidence-aware analysis:** geometry and result hashes are checked before
  overlays attach to a model. Missing or incompatible data is shown as
  unavailable. Candidate studies remain separate from reference assemblies.

## Current evidence

**Engineering acceptance is open (WO-03; November 6, 2026).** The latest
[RP1 load and attachment decision](docs/wo03-rp1-load-attachment-decision.md)
reconciles the carbon-faced plywood and solid-carbon fin studies. Neither is
adopted, and neither establishes an installed fin pass. Recovery joints,
conditioned material properties, thermal limits, exact motor fit and installed
flutter still need evidence. Older modular assemblies and their flight results
remain reference records, rather than validation of the latest RP1 geometry.

The current design under study is **G80 RP1 / AD1 v2**, presented from its frozen
55-part source definition, drawings and saved estimated cases. RP1 now has26 source-derived inspection meshes:10 ideal source-dimensioned parts
and16 simplified envelopes. All55records remain inspectable, including25mass
allowances without solids and4missing geometries. Complete manufacturing CAD
and full inertia remain unavailable. The archived G80 CAD assembly is a
separate inspection/replay reference. The [frontend revamp](docs/wo04-rp1-revamp-20261107.md)
implements adjacent collapsible left columns, a larger visual and a bottom tools
drawer; [the release candidate](docs/frontend-release-20261107.md) also implements
bounded experiments/batches, replay/export and recorded Analysis workflows.
Supported same-window native Chrome verification is available. Combined-release
acceptance is being checked in the permitted Chrome window after the owner restarted the normal-terminal preview.

VP1 remains a proposed evidence programme using ordinary birch plywood and WEST
105/206/406, not vehicle adoption. **The five inquiry drafts remain UNSENT under
the latest owner direction.** Frontend/design explanation continues from existing
repository evidence without waiting for replies. If outreach is later authorized,
response windows start from actual sends; no clock has started.

The next owner decision will include the lab's method, calibration and uncertainty, an itemized all-in quote, and what passing or failing would establish under the unchanged D1 criteria. Material stock subtotals are **not** the total test cost; fixtures, calibrated measurement, services and delivery remain unquoted. Purchases and testing require owner approval. Supplier/lab messages are never sent by the workbench.

The [recorded flight studies](docs/wo02-flight-study.md) compare unguided ascent
against RocketPy under matched assumptions. Passing numerical comparisons do not
establish physical flight accuracy. The [results log](docs/results.md) retains
run identities, assumptions, discrepancies and negative results.

The early workbench is implemented while full WO-04/05 acceptance remains open.
Source, test and offline-render checks are separate from the recorded browser outcomes and remaining compound acceptance gaps. See the [current project state](docs/CURRENT.md)
and [current frontend handoff](docs/frontend-release-20261107.md). The separate
[VP1 programme view](docs/wo04-vp1-validation-workbench-20261106.md) displays the frozen plan, conceptual parts, known/unquoted costs and five draft messages at
`/?workspace=engineering&view=rp1-validation`; it cannot authorize or execute tests.

**PID/RL training, embedded policy deployment, firmware/HIL and real flights are
later milestones.** The eventual finless vehicle needs its own active-control and
recovery validation. A digital-only orbital launcher and PPO-versus-G-FOLD study
also remain planned. No build or flight readiness is claimed.

## Run locally

Use **Python 3.11**, **uv**, and **Node 22.12+ within the Node 22 line**.
From a fresh checkout:

```bash
git clone https://github.com/kudratsingh/rocket-twin.git
cd rocket-twin
make setup
make setup-viewer
npm --prefix web ci
make preview
```

Open [the workbench](http://127.0.0.1:5173) or
[the local API reference](http://127.0.0.1:8000/docs). The launcher prepares
recorded engineering snapshots, starts FastAPI and Vite, and stops its API
process on Ctrl-C. It requires the Python environment and locked web dependencies
installed by the preceding commands.

Generated CAD meshes and full telemetry are excluded from Git. A fresh clone
contains source specifications, compact records and concept drawings; views that
need absent artifacts report them as unavailable. The
[web guide](web/README.md) explains the inspector, replay and compatibility rules;
the [environment guide](docs/ENVIRONMENT.md) records dependency pins and
regeneration commands. A complete Python dependency lock and fresh-machine
full-stack verification remain pending.

For the CPU model and reference checks:

```bash
make setup-sim
make check smoke
make tiny
make benchmark
```

`tiny` writes a new run with specification/source hashes and model outputs.
`benchmark` enforces preliminary static and unguided-flight comparisons against
RocketPy. These checks are distinct from the open engineering acceptance gates.

## Explore the project

| Area | Start here |
| --- | --- |
| Current design and open findings | [Current state](docs/CURRENT.md), [status history](docs/STATUS.md), [RP1 decision](docs/wo03-rp1-load-attachment-decision.md) |
| Vehicle specifications and calculations | [Platform manifest](configs/platform.yaml), [vehicle models](src/vehicle/), [CAD](src/cad/) |
| Physics and experiments | [JAX simulator](src/sim/), [experiment API](src/api/experiments.py), [flight-study method](docs/wo02-flight-study.md) |
| Inspection and recorded analysis | [Web app](web/), [API](src/api/), [RP1 study comparison](docs/wo04-rp1-studies-20261104.md) |
| Direction and validation | [Plan](docs/PLAN.md), [work orders](docs/work-orders/), [results](docs/results.md), [architecture decisions](docs/adr/) |
