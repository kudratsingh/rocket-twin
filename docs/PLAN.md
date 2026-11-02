# Plan — modular custom rocket and digital twin

Rebaselined by the owner, 2026-10-29. ADR-0006 supersedes the fixed F15, exact
three-second burn, universal average-TWR 3, 29 mm mount, 78 mm dimensions and PETG
body assumptions. Earlier results remain historical evidence, not active requirements.

## Core objectives

1. Build a substantial custom rocket that teaches mechanical design, materials,
   fabrication, assembly, propulsion integration, recovery and avionics.
2. Deliver the highest practical conventional performance within the current
   no-HPR-certification scope, with verified launch, structure and recovery limits.
3. Build a serious digital twin and controls platform: independent physics validation,
   traditional controllers, committed RL training, embedded deployment and eventual
   real-flight comparison. Fabrication and justified mechanical complexity are welcome.

Certified commercial motors and suitable purchased components complement custom
mechanical structures, interfaces and integration. Purchased tubing is an option,
not a mandate to minimize building. Performance means useful delivered impulse and
flight performance within verified launch, structural and recovery limits, not simply
maximum nominal motor designation or a heavier rocket approaching the mass cap.

## Preliminary physical platform

**Current delivery priority (ADR-0011):** bring one complete fixed-motor G80
package toward engineering acceptance first. G54 remains the committed upgrade
track and G12 the committed steering/PID/RL track. Record each configuration's
evidence separately; no G80 pass closes the other modes or aggregate WO-03.
The existing work-order sequence and full completion criteria remain unchanged.
Deliver the saved early frontend under ADR-0009 in parallel; missing analysis
overlays do not delay usable inspection, real experiments and replay.
The bounded G80 comparison now stops both specified capture envelopes before
CAD/FEA: rail bearing/pin engagement rejects B, while coupler fit/net section
rejects C under current provisional screens. The one subsequent S1 short-cassette study is also not admitted: its coupled
recovery-bearing, guide-mass and heel-length screens fail. IF-RECOVERY-001 needs
a dimensioned load-spreading saddle/strap endpoint and a complete full-growth
mass ledger; recovery demand must increase with that mass. No longer guide,
material limit or active vehicle change is adopted. See
[S1 decision](wo03-g80-short-subframe-decision.md). See [decision](wo03-g80-capture-decision.md) and
[current closure](wo03-g80-current-closure.md). Complete-package revalidation
remains mandatory; no completion gate is removed.

The next bounded IF-RECOVERY-001 saddle/strap study (S2) is also not admitted.
Its reduced diagnostic mass still misses the internal15.5m/s planning margin,
and actual foot/case/keeper/contact and conditional balance findings remain.
Formal15m/s, full50g, required opening cases and thermal/strength limits are
unchanged. A common positive carrier/fin-frame/body receiver and independent
motor thermal capture must be defined before another physical revision; no
isolated pin/saddle sweep or native refinement is admitted. See
[S2 decision](wo03-g80-saddle-study.md).

The owner's integrated aft admission decision now rejects the additive S2
receiver before detailed CAD: named stock977.490g with50g already exceeds the
source15m/s mass screen, before complete hardware and joint/thermal closure.
No credible complete arrangement is selected. The documented architecture
direction is a **single positive aft receiver replacing the wood frame and
duplicate carrier/collars**, with actual fin/body/harness joints and independent
motor capture. The gross replacement budget is198.333g at the separate15.5m/s
planning target,252.877g at formal15; no function may be removed for credit.
See [integrated decision and admission conditions](wo03-integrated-aft-proposal.md).
This is an interface requirement, not an adopted geometry or a changed WO gate.

The [connected S3 layout](wo03-g80-connected-receiver.md) now defines actual
end faces, cap joints, motor keys, fin pins and strap/service openings, but its
constant-section construction fails coupled admission:1199.622g with50g,
0.205cal loaded stability, inadequate planning guide margin and independent
motor-removal/cap/body/contact issues. Keep the connection layout and replace
heavy construction with counted, locally verified load paths before CAD/FEA.
The parallel [launch/motor comparison](wo03-launch-guide-motor-trade.md) and
[ADR-0012](adr/0012-conditional-launch-guide-options.md) retain the1.5m baseline
while proposing a confirmed supported1.8m usable G80 setup as a planning option.
This increases the conditional gross planning budget to357.990g; it clears no
structural, thermal, stability, recovery, equipment or exact-motor gate.
Approximately1kg is not a universal limit. Guide buttons/attachments, actual
club/rail/start/release geometry, wind and exact California motor evidence remain
dependencies; G54 and G12/PID-to-RL tracks stay separate.

`configs/platform.yaml` identifies three resolved mode specs sharing a common upper
assembly. The WO-03 integrated design is 66 mm diameter with a 1,200 mm tube/case
envelope and 1,212 mm overall retention/hardware envelope. The original 800 mm
recommendation is preserved in the WO-01/02 records. Equipment remains forward in
the extended shared upper. Custom printed nose/sled, kraft tubes, aircraft-plywood
fins with gussets, machined G11 hot/load-transfer parts, mica/foil thermal protection
and positively retained interchangeable aft modules remain substantial fabrication
and integration work. These are unmeasured design estimates, not accepted hardware.
See [adopted corrections and closure](wo03-correction-closure.md), the generated
[mass/CG/inertia report](wo03-integrated-vehicle.md) and
[ADR-0008](adr/0008-integrated-wo03-corrections.md).

| Configuration | Purpose | Preliminary motor/configuration |
|---|---|---|
| `modular-performance-v1` | Passively stable performance flights, fixed mount, custom fins | AeroTech G80-10T single-use SKU 78010; exact flight delay pending trajectory analysis |
| `modular-tvc-finned-v1` | Passively stable trainer, PID then RL | Reformulated AeroTech G12ST-P DMS SKU 071200, two-axis custom gimbal, independent electronic recovery |
| `modular-tvc-finless-v1` | Original active-only objective after qualification | Same G12ST-P family and upper assembly; actual fins/bonds absent; separate negative-static-margin model and recovery-transition gate |

These are preliminary engineering recommendations, not flight-qualified hardware
or purchase authorization. Full trade, estimated masses/costs, curve differences,
fabrication plan and remaining evidence are in [WO-01 rebaseline](wo01-rebaseline.md).
The CTI G54 is the committed conditional performance-upgrade track; G33 remains
a comparison option. Exact hardware, stock and California classification still
need to be established. G25W's source quarantine
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
fins/gussets/centering frames, G11 recovery/thrust plates and hot gimbal/cassette,
printed nose/sled/servo supports, mica/foil protection, positive motor retention,
wiring/power/recovery integration and a TVC guide/test fixture. The trainer's current
screen requires 5 m usable guide travel while retaining its 10 m/s departure gate;
the actual equipment and club acceptance are unresolved launch dependencies.
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

## WO-02 numerical evidence

The actual G80 performance and finned-G12 trajectory comparisons, three complete
alternative motor configurations and uncertainty/recovery study now pass the
numerical benchmark on Mac CPU. [Results](results.md), [study](wo02-flight-study.md).
G54 is the conditional near-160 N s upgrade lead; fixed G12 has higher calm altitude
but guide/wind/thermal/recovery penalties. No hardware freeze or sequence revision.
Use these calculated loads/trajectory limits in WO-03 and the later PID/RL,
sensor, independent recovery and flight-release gates.

## Engineering evidence expansion (ADR-0007)

The owner's 2026-10-30 sequence exception in [ADR-0009](adr/0009-early-inspection-experiments.md)
allows limited WO-04 inspection/recorded Analysis and WO-05 experiments/replay
alongside open WO-03. The first deliverable is a usable local inspector of actual
CAD/resolved designs. Real backend/JAX runs, synchronized replay/graphs and two-run
comparison follow without implying engineering or flight acceptance. The full
work-order prerequisites and every physical/paid/firmware/flight gate remain.

The owner expanded WO-03 on 2026-10-29: executed structural calculations and
targeted verified/converged FEA; bounded transient thermal and post-burn soak
analysis for G80, conditional G54 and long G12; spec-owned tolerance stacks,
combined gimbal sweep and assembly/service access. CAD exports alone do not close
WO-03. Each analysis must report assumptions, uncertainty, margins/failures,
material/temperature sources and the physical measurements needed later. See the
expanded WO-03 acceptance criteria and ADR-0007. Analysis meshes and viewer meshes
serve different purposes. Keep CadQuery/OpenCascade, JAX and the existing web stack.

WO-06 PID acceptance now requires a source/uncertainty/validation-backed loaded
gimbal model (kinematics, moving inertia, voltage, friction/backlash, limits and
latency) and aerodynamic force/moment/damping validity over intended Mach, Reynolds
and angle-of-attack ranges, including the G12 large-angle cases. Use targeted CFD
where a concrete design decision needs it; feed tables into the one JAX core.
WO-07 trains and evaluates RL with those improved models and held-out uncertainty.
WO-09–12 measure and verify structures, heat, actuators and aero through owner tests,
HIL and flight logs. Preserve WO-02 as the baseline, re-run applicable comparisons
after model changes, and retain every original work-order position and release gate.

The owner also expanded the frozen frontend contract with an **Analysis** mode:
recorded stress, displacement, temperature and applicable margin fields on exact
configuration geometry; units/legends, case/time controls and part assumptions,
limits and validation status. WO-03 exports versioned fields and identity/registration
metadata, WO-04 implements the view/API, and WO-05 adds recorded case/run exploration.
Calculated, estimated, measured and unavailable data remain explicit. Analysis runs
backend/offline; the browser never becomes a physics or engineering solver.

WO-03 also owns stable-ID requirements/verification and interface tables, an initial
qualitative FMEA, and executed vibration/resonance/flutter screening (ADR-0007).
These artifacts link actual parts, datums, tolerances, identities, load/thermal
cases, evidence and later verification. Track site/equipment/supplier unknowns and
common-cause control/recovery failures. Screens include hot/softened structure,
attachment uncertainty and joint/gimbal/sensor/servo interactions; unresolved
critical conclusions keep WO-03 open. The frontend exposes recorded traceability;
WO-06–12 carry risks through modeling, fair PID/RL evaluation, owner acceptance,
HIL, operating procedures and held-out measurement/flight correlation.

The current WO-03 correction package prioritizes the complete bonded brace-ring/
body/joint path, the explicit configuration-specific thermal acceptance matrix and
the entire independent recovery package within the unchanged G12 guide/mass
criterion. [Closure progress](wo03-package-closure-progress.md) separates candidate
screens from the active integrated vehicle. Required thermal failures, joint
strength/stiffness, installed fin/root/flutter, retention and service-access items
remain completion gates. A lighter battery, panel or pressure bulkhead is an
explicit construction trade with its own verification, not an automatic budget
credit. Full WO-04 completion depends on one adopted package passing expanded
WO-03 acceptance and being recorded. The owner-authorized limited preview remains
a separate exception. The owner resumed preview implementation and designated
frontend-agent browser verification on2026-10-31 while WO-03 remains open.

The thermal-layout correction in [ADR-0010](adr/0010-thermal-occupancy-and-interior-exchange.md)
keeps the existing sequence and screens. It requires disjoint CAD-derived glue,
other-solid and open regions, geometry-compatible end/slot radiation and gas,
common-surface coupling, numerical refinements and exact candidate exports. Old
proxy passes are historical; full required-case and installed-design closure is
still WO-03 work. No candidate's fit result or temperature field releases hardware.
