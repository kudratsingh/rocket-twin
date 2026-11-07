# rocket-twin

A custom rocket and its digital twin: YAML vehicle specifications, parametric CAD,
a JAX flight simulator, and a web workbench for inspecting designs and replaying
experiments. The project connects mechanical design, materials and recovery
engineering with a planned PID-to-reinforcement-learning control stack.

The current priority is a conventional fixed-motor **G80** engineering package.
A **G54** performance upgrade and **G12 thrust-vector-control** trainer remain
separate tracks. Custom construction and practical performance are core goals;
certified commercial motors and suitable purchased parts complement the build.

**Repository:** public by owner confirmation (November 4, 2026). The next G80 engineering milestone is [VP1 material and attachment validation](docs/validation/rp1-vp1/package-summary.md). Physical interchangeability with G12 is optional; the first G80 remains a dedicated conventional build.

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

VP1 starts with documentation and one proposed room-temperature test round using ordinary birch plywood and WEST 105/206/406. This selects a first material/process to investigate, not vehicle construction. The owner will supply actual send dates and replies for the five prepared inquiries. Each response window starts from its actual send date, with one day-5 follow-up and a day-10 close. No send date or reply has been recorded yet.

The next owner decision will include the lab's method, calibration and uncertainty, an itemized all-in quote, and what passing or failing would establish under the unchanged D1 criteria. Material stock subtotals are **not** the total test cost; fixtures, calibrated measurement, services and delivery remain unquoted. Purchases and testing require owner approval. Supplier/lab messages are never sent by the workbench.

The [recorded flight studies](docs/wo02-flight-study.md) compare unguided ascent
against RocketPy under matched assumptions. Passing numerical comparisons do not
establish physical flight accuracy. The [results log](docs/results.md) retains
run identities, assumptions, discrepancies and negative results.

The early workbench is implemented while full WO-04/05 acceptance remains open.
Source, test and offline-render checks are recorded separately from pending
browser interaction acceptance. See the [current project state](docs/CURRENT.md)
and [frontend handoff](docs/wo04-focused-preview-20261103.md). The separate
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
