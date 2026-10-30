# rocket-twin

A substantial custom modular rocket build and a serious digital-twin/control project.
Two core outcomes: the highest practical performance within the no-high-power-
certification scope, and PID-to-RL training, embedded deployment and eventual real-flight
comparison. Custom mechanical design, materials, fabrication and integration are part
of the project, alongside certified commercial motors and appropriate purchased parts.

The preliminary platform shares an upper airframe, avionics and recovery across
three explicit configurations with interchangeable aft assemblies:

| Mode | Preliminary propulsion | Nominal mass / with growth allowance |
|---|---|---:|
| Conventional finned performance, fixed motor | AeroTech G80-10T SU family | 472.0 / 522.0 g |
| Finned TVC trainer, PID then RL | Reformulated G12ST-P DMS family | 575.8 / 625.8 g |
| Eventual finless TVC | G12ST-P, separate actual geometry and validation | 532.2 / 582.2 g |

These are source-traceable numerical hypotheses, **not flight-qualified or fully
reconciled purchasing configurations**. The G80 source/current-product discrepancy,
G12 installed envelope, structural/thermal tests, independent recovery and launch
acceptance remain explicit gates. G25W remains quarantined. F25 and other motors
rejected only by the superseded three-second rule are reopened in the new trade.
The 1.5 kg loaded ceiling is a limit, not a target. No apogee optimum is claimed yet.

The recommended starting construction is a 66 mm × 800 mm hybrid of light kraft,
custom reinforced/keyed joints, cut plywood and printed ASA parts. All-printed,
rolled-paper and glass/epoxy options are compared on mass, strength, heat, cost and
learning. Shared YAML drives the parts model, future CAD/BOM, JAX physics and viewer.
Every part carries build/cost metadata and `learn` content. Full CAD and build pack
remain later work orders. Planning hardware envelope: roughly $650–950 before new
tools, shipping/tax and fees; a guide/test fixture may add $100–200.

WO-01 static and WO-02 numerical flight benchmarks pass on the Mac CPU. Actual
performance and finned-TVC flights are independently compared with RocketPy;
three alternative motor hypotheses and uncertainty/wind/recovery cases are recorded.
CAD, frontend, PID/RL, firmware and flights remain later work. Each run explicitly says `flight_ready: false`.
The digital-only orbital launcher, PPO-versus-G-FOLD comparison and extension
interfaces remain in the plan. RL is committed; honest negative comparisons count
as research evidence, while deployment still requires its acceptance gates.

## Run locally

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

## Delivered-performance findings

The G80 reference predicts ~698 m AGL; G54 ~842 m and G33 ~824 m. A distinct fixed
G12 model predicts ~1,023 m in calm air, but needs better conservative guide departure
and has strong wind sensitivity. The G12 TVC trainer predicts ~903 m calmly and
needs closed-loop control for its intended operating envelope. These are source
hypotheses, not flight claims. Keep G80 as the reference and G54 as the conditional
near-160 N s upgrade lead; hardware remains unfrozen. G80/G54 also exceed the
starting 16 g accelerometer range. [Recorded results](docs/results.md).

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
