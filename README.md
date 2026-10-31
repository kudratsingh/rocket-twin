# rocket-twin

A substantial custom modular rocket build and a serious digital-twin/control project.
Two core outcomes: the highest practical performance within the no-high-power-
certification scope, and PID-to-RL training, embedded deployment and eventual real-flight
comparison. Custom mechanical design, materials, fabrication and integration are part
of the project, alongside certified commercial motors and appropriate purchased parts.

The current WO-03 design shares an upper airframe, avionics and recovery across
conventional performance, finned TVC training and eventual finless configurations.
Custom fabrication, maximum practical conventional performance and committed
PID-to-RL development remain equally important outcomes.

## Current integrated vehicle — WO-03 open

**Diameter: 66 mm. Overall length: approximately 1.21 m (1,212 mm).** A 400 mm
upper-body extension, stronger fins/supports, thermal protection and recovery
integration have increased length and mass. These figures supersede the original
800 mm platform and its earlier performance estimates.

| Configuration | Motor hypothesis | Nominal loaded mass | With 50 g allowance | Nominal calm-air altitude |
|---|---|---:|---:|---:|
| Conventional finned performance | AeroTech G80-10T SU family | 739 g | 789 g | 635 m / 2,084 ft |
| Conditional performance upgrade | CTI G54 / Pro29 source hypothesis | 818 g | 868 g | 756 m / 2,479 ft |
| Finned TVC trainer, gimbal locked | Reformulated G12ST-P DMS family | 780 g | 830 g | 531 m / 1,743 ft |
| Eventual finless TVC | G12ST-P, separate actual geometry | 646 g | 696 g | Not flight validated |

Altitude uses **nominal mass**; growth is evaluated in separate cases. These are
simulated source hypotheses, not flight measurements or purchase-ready motor
configurations. G54 predicts about 19% more nominal altitude than G80. Its defined
full-growth/depletion stability minimum is **1.046 calibre**, just above the 1.0
gate; an additional exploratory motor-CG sensitivity falls below 1.0. G54 remains
conditional on design robustness and exact source/hardware/CG evidence.

**G12 TVC currently requires 5 m usable launch-guide travel in the model. Its
availability and club acceptance are unconfirmed.** The lower-thrust, full-growth
screen retains its 10 m/s departure requirement. This guide assumption is not
confirmed launch equipment or authorization.

The integrated design uses light kraft tubes, custom keyed joints, rectangular
plywood fins and root gussets, machined G11 recovery/thrust/gimbal parts, mica/foil
thermal protection and a dedicated recovery-controller power package. All-printed,
rolled-paper and composite options remain available where justified by strength,
heat, mass, cost and learning. One shared YAML parts model drives CAD, mass/CG/full
inertia, JAX physics, BOM/learn metadata and future viewer inspection.

**WO-03 acceptance remains open.** Remaining items include installed fin/root and
flutter evidence, minimum clearances, G54 thermal/CG sensitivities, detailed motor
capture/fastener/pin evidence, recovery mounting/arming/routing and anchor capacity.
Nominal CAD/flight comparisons and standard thermal screens do not close these
design items or the separate physical qualification gates. See the
[correction/closure report](docs/wo03-correction-closure.md),
[full mass/CG/inertia report](docs/wo03-integrated-vehicle.md) and
[current status](docs/STATUS.md).

G80 remains the reference; G12 remains the PID-to-RL trainer; eventual finless
burnout/recovery transition requires its own validation. Certified commercial
motors and appropriate purchased components complement substantial custom
mechanical work. Exact motor/source/lot, California eligibility and club/RSO
acceptance remain launch prerequisites. G25W remains quarantined. Historical
threshold-only motor exclusions remain recorded and are reconsidered under the
rebaseline. The 1.5 kg loaded ceiling is a limit, not a target weight.

WO-01 and WO-02 numerical benchmarks remain the historical baseline. Current
integrated configurations are rechecked independently with RocketPy. Frontend,
PID/RL, firmware/HIL and owner-performed build/flights remain in sequence; every
record has `flight_ready: false`. RL is committed, with honest negative results.
The digital-only orbital launcher, PPO-versus-G-FOLD and extension interfaces remain.
Purchases, physical work, paid runs, WO-10 owner review and flight release remain gated.

## Run locally

The owner-authorized early inspection/experiment preview can run while expanded
WO-03 acceptance remains open:

```bash
make preview
```

Open **http://127.0.0.1:5173**. The launcher installs the exact web dependencies
on first use, starts the local Python API at port 8000 and Vite at port 5173, and
stops the launched API when you press Ctrl-C. Use Node 22 and the existing project
Python environment (`make setup-viewer` if needed). After installation the lockfile
is used by `npm ci`. See [web instructions](web/README.md) and
[ADR-0009](docs/adr/0009-early-inspection-experiments.md) for the limited scope.
Browser interaction and successful simulated flights do not approve construction
or flight; PID and reinforcement learning remain later work orders.

Use Python 3.11 and uv. On a fresh network-enabled machine:

```sh
make setup
make setup-sim
make check smoke tiny benchmark
```

The current workspace already has the environment. `make tiny` resolves all modes
and produces source/code hashes, parts budgets, CG/inertia/CP, guide/control-time
screens and inventory/spec previews in `runs/<id>/`. `make benchmark` adds real
RocketPy comparisons and exits nonzero if preliminary completion gates fail. Neither
command authorizes hardware or flight. `make flight-study` runs the full motor,
wind, uncertainty and recovery study; see [WO-02 findings](docs/wo02-flight-study.md). Full dependency locking is still pending;
WO-01's direct dependency pins and tested reference versions are recorded.

The active manifest is [configs/platform.yaml](configs/platform.yaml); mode YAML
and shared upper are under [configs/vehicle/platform](configs/vehicle/platform).

```sh
.venv/bin/python scripts/wo01_platform.py --preset sim --compare rocketpy --require-benchmark
```

## Evidence and project direction

- [Rebaseline trade, motors, mass/cost and verification](docs/wo01-rebaseline.md)
- [WO-01 deliverables and stage-appropriate benchmark](docs/work-orders/WO-01-vehicle-spec-mass-cp.md)
- [ADR-0006](docs/adr/0006-modular-platform-rebaseline.md), [plan](docs/PLAN.md), [status](docs/STATUS.md), [results](docs/results.md)
- [Environment](docs/ENVIRONMENT.md), [owner start guide](START_HERE.md), [agent workflow](AGENTS.md)

## Delivered-performance evidence

The current table above is the integrated WO-03 prediction, with G80 as reference
and G54 conditional. The current 27-case campaign includes motor alternatives,
growth, thrust/drag, wind and recovery timing. Five nominal RocketPy comparisons
meet the 5% benchmark; the largest current error is finned-G12 altitude 2.064% and
time-to-apogee 0.917%. Numerical agreement under assumptions is not measured flight
accuracy. G12 passive weathercock/post-burn motion remains a control/model risk.
The high-g measurement path is retained alongside the low-g IMU.
[Recorded results](docs/results.md) preserve the earlier estimates and comparison
records as historical evidence rather than current performance claims.

## Historical studies

Original 1.6 mm PETG/F15 and 1.2 mm proposals and downloaded curves remain unchanged.
Their original three-second/TWR-3 gates remain reproducible, rather than being rewritten
as new results. They are not the active platform benchmark:

```sh
.venv/bin/python scripts/wo01_vehicle.py --preset sim --compare rocketpy
make motor-study
make f22-study
make g-impulse-study
```

Source collectors (`make fetch-motors`, `make fetch-motor-study-sources`,
`make fetch-f22-sources`) require network access and retain unreviewed raw data under
ignored `data/`. They do not select or purchase motors. Current exact source/variant
verification is separate from a preliminary numerical-model pass.
