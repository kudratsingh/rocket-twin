# Plan — modular custom rocket and digital twin

Rebaselined by the owner, 2026-10-29. ADR-0006 supersedes the fixed F15, exact
three-second burn, universal average-TWR 3, 29 mm mount, 78 mm dimensions and PETG
body assumptions. Earlier results remain historical evidence, not active requirements.

## Core objectives

1. Build a substantial custom rocket that teaches mechanical design, materials,
   fabrication, assembly, propulsion integration, recovery and avionics, and delivers
   the highest practical performance within the current no-HPR-certification scope.
2. Build a serious digital twin and controls platform: independent physics validation,
   traditional controllers, committed RL training, embedded deployment and eventual
   real-flight comparison. Fabrication and justified mechanical complexity are welcome.

Certified commercial motors and suitable purchased components complement custom
mechanical structures, interfaces and integration. Purchased tubing is an option,
not a mandate to minimize building. Performance means useful delivered impulse and
flight performance within verified launch, structural and recovery limits, not simply
maximum nominal motor designation or a heavier rocket approaching the mass cap.

## Preliminary physical platform

`configs/platform.yaml` identifies three resolved mode specs sharing a common upper
assembly. Starting trade recommendation: 66 mm diameter, 800 mm overall length,
custom printed nose/sled, light kraft tubes with custom reinforced joints and cut
plywood load-transfer parts; positively retained interchangeable aft modules.

| Configuration | Purpose | Preliminary motor/configuration |
|---|---|---|
| `modular-performance-v1` | Passively stable performance flights, fixed mount, custom fins | AeroTech G80-10T single-use SKU 78010; exact flight delay pending trajectory analysis |
| `modular-tvc-finned-v1` | Passively stable trainer, PID then RL | Reformulated AeroTech G12ST-P DMS SKU 071200, two-axis custom gimbal, independent electronic recovery |
| `modular-tvc-finless-v1` | Original active-only objective after qualification | Same G12ST-P family and upper assembly; actual fins/bonds absent; separate negative-static-margin model and recovery-transition gate |

These are preliminary engineering recommendations, not flight-qualified hardware
or purchase authorization. Full trade, estimated masses/costs, curve differences,
fabrication plan and remaining evidence are in [WO-01 rebaseline](wo01-rebaseline.md).
A higher-impulse CTI G54/G33 configuration remains an upgrade trade if stock, exact
hardware and California classification can be established. G25W's source quarantine
remains; shorter burn alone no longer excludes F25/G40/G54 from performance mode.

Each mode has its own actual geometry, fin mass and inertia, motor, aerodynamic
model, launch/recovery plan, run identity and validation evidence. The shared upper
YAML is resolved into complete specs for CAD, calculations, BOM and frontend. Every
physical part and consumable appears with `learn`, mass provenance and build/cost
metadata. Interchangeability is a design hypothesis until tolerance and load tests.

## Requirements by stage

WO-01 freezes the preliminary model contract and justified screening requirements.
Rail exit is screened from the full thrust curve at lower-bound thrust and mass
allowance. Passive modes must have positive margin with allowance; TVC gets a useful
control-time proxy after rail exit rather than an exact universal burn duration.
Average TWR remains diagnostic. This does not replace later aerodynamic, structural,
thermal, recovery or controller validation. No apogee claim is made in WO-01.

The no-HPR scope requires a qualifying certified single commercial solid, nonsparky
motor, <=160 N s and <=80 N certified mean thrust, and the applicable propellant,
materials and loaded-mass constraints. California exact-motor approval and actual
club/RSO acceptance are independent gates before procurement/flight. ROC at Lucerne
is a candidate club, not a confirmed launch or approval. The 1.5 kg ceiling is not a
target weight; proposed configurations retain a 50 g growth allowance.

## Preserved digital architecture and milestones

One YAML-driven parts model, one JAX physics core, independently checked with RocketPy,
one viewer frontend, and swappable interfaces in EXTENSIONS.md. The digital orbital
launcher remains a two-stage, liquid, reusable model for trajectory, staging,
entry/landing and PPO versus G-FOLD; it is never built. No physical propulsive landing.

RL is committed. PID/LQR establishes the baseline; PPO uses estimator observations,
realistic sensors/actuators and domain randomisation; policies remain <=3 layers,
<=64 units, float32 C on Cortex-M7. Abort logic, HIL, flight logging, paired simulation
and system identification remain mandatory. Comparisons include failures and negative
results. Flight policy deployment occurs only after its applicable release gates.

## Work-order sequence and dependencies

| WOs | Scope retained and clarified |
|---|---|
| 01 | Modular specs, mass/CG/inertia/CP, materials/motor trade, preliminary rail/control-time screens and independent static benchmark |
| 02 | JAX 6-DOF; actual finned performance/trainer geometries; unguided locked-gimbal RocketPy comparisons; rail departure, recovery/delay, altitude, drag and wind envelopes |
| 03 | CAD of custom parts and purchased envelopes; modular interfaces, tolerances, finite-volume mass, load/thermal design and validation plans |
| 04–05 | Frontend, experiments and telemetry replay identified by resolved configuration and hashes |
| 05b | Digital orbital vehicle and shared physics extension |
| 06 | Estimation, measured-model hooks, PID/LQR, fault and abort evaluation |
| 07 | Committed PPO training, fair multi-seed PID/RL comparison and C export; negative results retained |
| 08 | Digital orbital landing PPO versus G-FOLD and writeup |
| 09–10 | Build pack, procurement review, owner build, component/structure/thermal tests, firmware and HIL |
| 11–12 | Conventional flights then qualified TVC PID/RL flights, finless progression when qualified, paired logs and system identification |

Sequence is unchanged. WO-01's rail-only arithmetic is a bounded design screen, not
an early implementation of WO-02. Physical measurements happen only after separate
owner authorization; their absence in WO-01 is explicit. In WO-03, geometry cannot
be accepted as hardware-ready until the later owner-performed tests are satisfied.
No sim success silently authorizes a flight or removes a failed safety gate.

## Fabrication and cost envelope

Custom work includes tube cutting/sealing, bonded and keyed couplers, plywood
bulkheads/fins/centering parts, printed nose/sled/gimbal/servo supports, positive
motor retention, wiring/power/recovery integration and a TVC guide/test fixture.
Compare all-printed PETG/ASA, hand-rolled kraft and glass/epoxy as documented trades;
material selection follows mass, loads, heat, fabrication learning and testability.

Preliminary shared platform with all aft assemblies, one motor per operating family,
and parts contingency: approximately $650–950 before new tools, shipping/tax and club
fees; guide/test fixture approximately $100–200 if the club cannot supply one. These
are estimates, not quotes. Recompute the derived inventories before procurement.
Consumable motors approximately $40–50 per flight plus delivery; reload hardware,
if later selected, is extra. Paid compute remains per-run owner approved; no paid run
is authorized by this rebaseline. Dependency pins are unchanged.

## Outside current authorization

Purchases, fabrication, physical tests, paid runs and flights. GitHub pushes and PRs
are authorized under `AGENTS.md`; routine PRs do not require owner review. No
custom propellant or motor modification. No HPR certification path. No physical
propulsive landing. No CAD editing in the frontend. Structural/thermal/advanced aero
extensions remain available through the existing interfaces instead of being implied
by a simple preliminary model.
