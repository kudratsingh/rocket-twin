# rocket-twin — agent brief

A substantial custom modular rocket build and its digital twin: a parts model you can inspect
down to each component, a validated 6-DOF physics simulator, a web frontend that shows the
vehicle in 3D and replays experiments, classical and RL flight controllers trained in that
simulator, and finally the same rocket built, printed and flown with the trained controller on
a DIY flight computer. The owner is Kudrat Singh. You (the coding agent) write all the code.
The owner launches every paid run and does every physical build, test and flight.

Read in this order before any work: this file → `docs/PLAN.md` → `docs/ENVIRONMENT.md` →
`docs/UI.md` (before any frontend WO) → the current work order in `docs/work-orders/`.

## Core objectives and active architecture

The current delivery priority is one complete fixed-motor G80 engineering
package first, while the G54 performance upgrade and G12 PID/RL tracks remain
committed. ADR-0011 records this priority without changing aggregate WO-03
completion or the existing gates. Substantial custom construction, maximum
practical performance and serious PID-to-RL development remain three core goals.

The owner rebaselined WO-01 on 2026-10-29. Custom mechanical design, materials,
fabrication, assembly, propulsion integration, recovery and avionics are core
learning goals. Maximum practical performance within the no-high-power-certification
scope and serious digital-twin/control research are both core outcomes. Fabrication
effort and worthwhile mechanical complexity are acceptable; ease of assembly alone
must not select the design. Use certified commercial motors and appropriate purchased
components, with meaningful custom structures, mechanisms and integration.

The physical platform has three explicit configurations: conventional fixed-motor
finned performance, finned TVC trainer, and eventual finless TVC. For the first G80, ADR-0013 makes physical interchangeability optional: use a
dedicated fixed conventional airframe when that removes duplicated structure.
Do not include future gimbal/servo hardware. Share software, instrumentation,
specification methods and frontend; G54/G12 own physical checks. Other tracks
may share upper hardware where justified; aft modules and motors may differ.
`configs/platform.yaml` identifies the active modes and common YAML assembly. Every
resolved mode owns its actual parts, mass/CG/inertia, fins, aerodynamics and evidence.
Never remove fins with an aerodynamic flag while retaining their mass or reuse a
performance trajectory as validation of the TVC mode. The old
`configs/vehicle/tvc-ascent-v1.yaml` and thinner proposal remain historical references.

RL training, embedded policy deployment and eventual real-flight comparison are
committed milestones. Preserve the PID baseline, realistic sensors/actuators,
domain randomisation, small Cortex-M7 policy, abort logic, HIL, logging and system
identification. Report negative results; RL superiority is a hypothesis, not a
condition for honestly completing the comparison or a reason to drop RL.

One resolved YAML specification drives each configuration's CAD, mass model, BOM,
learn content, JAX physics and frontend. Independent RocketPy comparisons remain.
`orbital-launcher-v1` stays digital only: a two-stage liquid reusable launcher,
shared physics/frontend, PPO landing versus G-FOLD, ECI frames and extension interfaces.
Hobby solid motors cannot throttle; physical propulsive landing remains out of scope.
See ADR-0006 and `docs/wo01-rebaseline.md` for the preliminary trade and gate rationale.

## Operating mode: fast

**Owner-authorized sequence exception (2026-10-30, ADR-0009):** while expanded
WO-03 remains open, implement a limited WO-04 read-only inspection/recorded-Analysis
preview and limited WO-05 real-simulator experiments/replay/comparison. Deliver
the usable inspection viewer first; Analysis must not delay it. Full work-order
completion and engineering, build, paid-run, firmware-review and flight-release
gates remain unchanged. This exception overrides only the start-order rule below.

- Build order is the work orders, WO-01 → WO-05, WO-05b, WO-06 → WO-12, in sequence. Do not skip ahead, do not gold-plate.
- Use work-order branches and focused PRs after substantial work items (`AGENTS.md`).
  Split large WOs into coherent PRs; do not add owner review for routine changes.
  Start the next WO only when the current one's completion
  benchmark (below) is met and recorded in `docs/STATUS.md`.
- **No independent review pass by default.** Self-check against the WO's benchmark, run the smoke
  tests, open the PR. The owner reviews only WO-10 (flight-computer firmware and abort logic),
  because a silent bug there destroys hardware or hurts someone.
- Minimal tests: one smoke test per module that proves it runs end to end on CPU with the `tiny`
  preset. No test-count targets, no coverage targets.
- Prefer vendoring: copy small pieces of upstream code into `src/` with a header naming the
  source repo, commit and license. Do not maintain forks.
- When blocked, write the blocker and your best-guess resolution into `docs/STATUS.md` and
  continue with the parts that are not blocked. Ask the owner only for decisions that spend
  money, touch hardware, or cannot be undone.

## Hard rules

1. **The spec is the source of truth.** Every part, mass, dimension, material and electrical
   value lives in `configs/vehicle/` YAML, including resolved common/mode assemblies (schema in `src/vehicle/schema.py`). CAD, mass
   properties, the sim, the BOM and the frontend are all derived from it. Never hand-edit a
   mesh, a mass number in the sim, or a value in the frontend.
2. **One physics core.** All flight physics lives in `src/sim/` (JAX, pure functions, ADR-0001).
   The frontend never computes physics; it replays telemetry the core produced. The RL rollout
   worker and the single-run experiment API call the same `step()`.
3. **Validate before trusting.** Mass/CG/CP are checked against RocketPy's own calculation for
   the same geometry (WO-01); the 6-DOF flight is checked against RocketPy on an unguided flight
   (WO-02); real flight logs are overlaid on sim predictions (WO-11). A number that has not
   been checked against a reference is labelled `unvalidated` in results.md.
4. **No paid runs without the owner's explicit, per-run approval.** This project barely needs a
   GPU (PPO on the batched JAX sim trains in minutes on an RTX 4090). You produce the config, a
   CPU `tiny` dry run and a cost line; the owner launches. Every run gets `runs/<id>/record.json`.
5. **Pin everything.** Versions in `docs/ENVIRONMENT.md`, `pyproject.toml`/`uv.lock` and
   `web/package-lock.json` are frozen. Upgrading a pin is its own work order with a reason.
6. **Stay inside the NAR Model Rocket Safety Code and FAA Class 1.** Loaded physical design including mass allowance < 1,500 g;
   total propellant ≤ 125 g; single motor ≤ 160 N·s and certified average thrust ≤ 80 N;
   no hybrids or spark-producing motors; certified commercial motors only, no metal nose,
   body or structural parts, electrical ignition with interlock. The spec schema enforces the
   mass and propellant limits as hard validation errors. An actively stabilised finless rocket
   flies only at a club launch with the Range Safety Officer's prior approval; the build pack
   (WO-09) includes the stability and abort documentation the RSO will ask for.
7. **Abort logic is not optional.** The flight computer must detect loss of control (tilt beyond
   a limit, rate beyond a limit, sensor dropout, servo fault) and go to a safe state (gimbal
   centred, independent recovery armed according to its qualified flight-state logic) before any policy, PID or RL, is
   allowed to command the gimbal. Abort thresholds live in the spec, not in firmware constants.
8. **The frontend uses source-owned design and CAD.** Under ADR-0017 the owner
   now authorizes source-constrained virtual assembly and separate draft specification
   editing through validated controls. Frozen sources stay unchanged. YAML/CadQuery
   and physical calculations remain in Python; there is no unrestricted browser CAD
   kernel or automatic engineering adoption. The web app inspects, composes drafts,
   requests backend experiments and replays. `docs/UI.md` is frozen
   before WO-04 starts; frontend PRs implement it, they do not redesign it. This is where agent
   tokens go if unchecked — when a UI WO exceeds one week of effort, split it in STATUS.md.
9. **Controllers must fit the flight computer.** Any policy meant to fly (PID or RL) runs as
   plain C on a Cortex-M7 at the spec's loop rate: an MLP of ≤ 3 layers, ≤ 64 units, float32,
   no dependencies. Train with that constraint from WO-07, not after.
10. **Every part teaches.** Each part in the spec carries a `learn:` block (what it does, the
    physics or electrical reason it is shaped/rated the way it is, what fails if it is wrong).
    Each physics module starts with a short derivation summary and a reference. The frontend's
    part inspector shows the `learn:` text. Keep these short and correct; they are the owner's
    study material.
11. **Honest reporting.** Single-run numbers are labelled single-run. Sim numbers are never
    presented as flight numbers. Negative results and crashes go in `docs/results.md`.
12. **Secrets and large files stay out of git.** `.env`, `runs/`, `data/`, generated meshes
    (`build/`) are ignored; meshes are regenerated from the spec. Flight logs go to a private
    HF dataset or `data/` on the owner's machine.
13. **Mac is for the frontend, CAD and the flight computer; cloud is for RL.** The owner's
    machines are Apple Silicon Macs (zsh, Homebrew). CadQuery, the API and the web app run on
    the Mac. PPO at thousands of envs runs on a rented RTX 4090. Commands for the owner are
    written for macOS.
14. **Real science, cited.** Every physics equation in `src/` traces to a named reference
    (textbook chapter or paper) in the module's derivation summary. The orbital vehicle's
    numbers come from public engineering sources cited in the spec; any figure without a
    citation is labelled `estimate`. No proprietary data or orbital-vehicle branding. Name physical commercial motors and
    components where necessary for exact identification, purchasing evidence and attribution.
    Where the model simplifies (no slosh, no structural FEA, no thermal, no CFD), the
    `learn:` block or derivation summary says so and names the full treatment, so the owner
    always knows the edge of the model.
15. **Extension points stay open.** Deeper models plug in behind interfaces named in
    `docs/EXTENSIONS.md` (aero, propulsion, structures, thermal, GNC, environment). Do not
    hard-wire a simplification where that file names an interface.

## Build order and completion benchmarks

| WO | Name | Done when |
|---|---|---|
| 01 | Vehicle spec + parts tree + mass/CG/CP | All three modular mode specs resolve consistently; source-traceable preliminary motor hypotheses, part/build/cost inventories, mass allowance and mode-specific rail/static/control-time screens; static mass/CG/CP/margin within 3 % / 0.1 cal of RocketPy; `make benchmark` passes on CPU. Flight/build/control release gates remain later WOs |
| 02 | 6-DOF sim core (JAX) + validation | Unguided flight (fins on, gimbal locked) matches RocketPy apogee and time-to-apogee within 5 %; `vmap` over 4,096 envs steps on CPU; TVC, wind, sensor and servo models present with tests |
| 03 | CAD + engineering integration | All configuration CAD/exports and mass reconciliation; executed structural calculations and targeted verified/converged FEA, bounded transient thermal/soak analysis, spec-owned tolerance and combined-motion/access checks; quantitative margins and required physical tests; affected static/flight comparisons pass (ADR-0007, WO-03 criteria) |
| 04 | API + frontend v1 | FastAPI serves the tree, mass properties and meshes; web app shows the assembled rocket and an exploded view, a part inspector with specs + `learn:` text, a CG/CP/margin panel drawn on the model, the mass budget and recorded Analysis overlays/legends/case-time controls with per-part evidence (docs/UI.md) |
| 05 | Experiments + replay | From the UI: pick a vehicle, override parameters (motor, wind, mass shift), run the sim, replay the flight in 3D with a time scrub, plot any telemetry channel, compare two runs side by side; runs stored as Parquet |
| 05b | Orbital vehicle pack | `orbital-launcher-v1` spec (40–60 parts, every `learn:` written, every figure cited); CAD for tanks, engines, octaweb, interstage, fairing, grid fins, legs; sim extended (standard atmosphere to 150 km, Isp vs pressure, staging, spherical Earth frame, engine-out); scripted mission (pitch-over, gravity turn, MECO, separation, fairing jettison, SECO, boostback/entry/landing burns); stage 2 reaches orbital velocity with the spec'd payload and stage 1 lands nominally, within 10 % of cited class figures; scale switch and mission timeline in the frontend |
| 06 | Avionics model + PID baseline | Servo, IMU, baro and loop-timing models calibrated to datasheet values; attitude estimator; PID gimbal controller holds tilt ≤ 5° at burnout under 3 m/s steady wind + gusts in ≥ 95 % of 1,000 Monte-Carlo runs; visible in the frontend |
| 07 | RL ascent controller | PPO on the batched sim with domain randomisation (thrust ±15 %, mass/CG, servo lag, wind); policy fits rule 9; fair multi-seed PID/RL comparison on tilt RMS, dispersion and failures; improvement is a target, negative results retained; embedded export verified and RL vs PID visible in frontend |
| 08 | Lander + G-FOLD (digital milestone) | `orbital-launcher-v1` stage 1 lands with PPO from entry-burn end; G-FOLD (lossless convexification) solution computed for the same cases; fuel use and success rate compared under disturbances the optimiser does not model; `docs/blog-draft.md` written |
| 09 | Build pack | STL set + print settings, BOM with prices and links, wiring diagram generated from the spec's netlist, assembly order, RSO stability/abort document, `firmware/` stub with the policy exported as a C header |
| 10 | Flight computer firmware + HIL (owner reviews) | Teensy firmware: sensor read, estimator, PID and MLP controllers, SD logging, abort logic, recovery trigger; hardware-in-the-loop test against the sim over serial at the spec loop rate with ≤ 2 ms jitter; every abort condition verified on the bench |
| 11 | Ground tests + first flights | Bench tilt test and servo/TVC range test pass; owner flies PID first, then RL; flight logs import into the frontend and overlay on the sim prediction |
| 12 | System ID + retrain + writeup | Servo, thrust and aero parameters fitted from logs; controller retrained; before/after tracking error on real flights; README with sim table, flight table, cost, hardware list, reproduce commands |

A sim-only milestone (WO-01–08) is shippable on its own if hardware is late or flights are
weathered out.

## What each WO teaches (owner's study map; details in `docs/learn/README.md`)

| WO | Subjects |
|---|---|
| 01 | Static stability (CG/CP), Barrowman method, solid motors, thrust curves, impulse, materials and mass budgets, electrical ratings of avionics parts |
| 02 | Rigid-body dynamics with variable mass, quaternions and frames, drag and Mach effects, TVC moments, wind models, sensor and servo physics |
| 03 | Mechanical design, mechanisms (two-ring gimbal), tolerances, 3D-printing engineering, load paths, structural FEA, transient heat transfer and tolerance stacks |
| 04–05 | Nothing new in physics; the twin becomes usable |
| 05b | Liquid propulsion (Isp, mixture ratio, chamber pressure, nozzle expansion), tanks and pressurisation, staging and the rocket equation, standard atmosphere, gravity turns and orbital insertion, max-Q, entry and landing burns, grid fins and legs |
| 06 | Attitude estimation (complementary/Madgwick), PID and LQR, actuator limits, abort logic, Monte-Carlo evaluation |
| 07 | PPO, domain randomisation, sim-to-real, policy compression for embedded targets |
| 08 | Optimal control, convex optimisation, lossless convexification (G-FOLD) |
| 09 | BOM engineering, wiring and power design, LiPo safety, range safety and regulations |
| 10 | Embedded real-time firmware, sensor drivers, fixed-rate loops, hardware-in-the-loop testing |
| 11–12 | Flight test practice, system identification, closing the sim-to-real gap |

## Repository layout

```
CLAUDE.md                   this file
docs/PLAN.md                phases, scope, non-goals, budget
docs/ENVIRONMENT.md         pinned versions, GPU tier, install
docs/UI.md                  frozen frontend spec (screens, panels, interactions)
docs/EXTENSIONS.md          named interfaces where deeper models plug in later
docs/STATUS.md              running log: current WO, blockers, decisions, spend
docs/results.md             every number with run id + validation status
docs/learn/                 owner's study index (agent only links; owner writes)
docs/adr/                   decisions (template in 0000-template.md)
docs/work-orders/           WO-01 … WO-05, WO-05b, WO-06 … WO-12
configs/platform.yaml       active modular physical configuration manifest
configs/vehicle/platform/   common upper and complete performance/finned/finless modes
configs/vehicle/            historical tvc-ascent-v1.yaml, orbital-launcher-v1.yaml, motors/, engines/
configs/                    tiny.yaml, sim.yaml, rl.yaml, real.yaml
src/vehicle/                schema (pydantic), parts tree, stages, mass/CG/inertia, Barrowman CP
src/cad/                    CadQuery generators per part type, export STEP/STL/GLB
src/sim/                    JAX 6-DOF: dynamics, aero, propulsion (solid + liquid), tvc, wind,
                            atmosphere, gravity, staging events, sensors, actuators, env
src/avionics/               estimator (attitude from IMU+baro), loop timing, fault injection
src/control/                PID/LQR controllers, abort logic (shared with firmware via codegen)
src/rl/                     PPO (PureJaxRL-style), domain randomisation, policy export to C
src/gnc/                    G-FOLD (cvxpy), trajectory references
src/api/                    FastAPI: vehicles, mass props, meshes, runs, experiments
src/export/                 BOM, wiring SVG, build pack, RSO document
web/                        Vite + React + TypeScript + react-three-fiber frontend
firmware/                   Teensy 4.1 (PlatformIO): sensors, estimator, controllers, abort, logging
scripts/                    one entry point per WO step
tests/                      smoke tests only
runs/                       run records (ignored except record.json)
build/                      generated meshes (ignored)
```

## Conventions

- Python 3.11, `uv` for deps, `ruff` + `black`, strict `mypy` on `src/`.
- Web: Node 22 LTS, `npm`, TypeScript strict, ESLint + Prettier. No UI framework beyond what
  `docs/UI.md` names.
- Firmware: PlatformIO, Teensy 4.1 target, C++17, no dynamic allocation in the control loop.
- Conventional Commits. PR template: what, benchmark result, cost, what's next.
- Every Python script takes `--config` and `--preset {tiny,sim,rl,real}`; `tiny` runs on CPU
  in < 2 min. `make tiny` runs the whole pipeline on CPU.
- Units: SI everywhere internally (m, kg, N, s, rad). Convert only at the UI edge.
- Frames: body frame x forward (nose), z down. World frame per vehicle `scale`: flat-Earth NED
  for `model`, Earth-centred inertial + rotating Earth for `full` (ADR-0005). Quaternions
  scalar-first. State these once in `src/sim/frames.py` and import; never redefine.
- Logs: Parquet to `runs/<id>/telemetry.parquet`; `record.json` beside it.
- Cost line in every PR that touches a GPU: `estimated: <GPU> × <h> = $<x>`.

## Owner's standing notes to the agent

- Speed over polish. Fast iteration and completion is the priority; the owner studies the
  project on the side.
- Do not add process (extra reviews, extra docs, extra tests) that this file does not call for.
- If a WO looks like it will exceed one week of agent effort, split it and say so in STATUS.md.
  The frontend WOs (04, 05) and the orbital pack (05b) are the likeliest to need splitting.
- Re-price recurring costs when the project changes shape and say so before the next paid run.
