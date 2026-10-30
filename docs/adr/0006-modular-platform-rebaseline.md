# ADR-0006: Modular custom performance and PID-to-RL platform

Status: accepted as a preliminary WO-01 architecture; hardware and flight release pending
Date: 2026-10-29
Authority: owner's explicit rebaseline and authorization for reversible local WO-01 changes
Supersedes: ADR-0003 motor/airframe/threshold assumptions; earlier fixed-baseline directions

## Decision

Custom building, maximum practical no-HPR-certification performance and embedded
RL flight comparison are core goals. Neither fabrication convenience nor a single
long-burn motor should determine both physical modes. Preserve the YAML/JAX core,
independent RocketPy validation, frontend, digital orbital launcher, G-FOLD and
extension interfaces. The work-order sequence is unchanged.

Use a modular physical platform with common upper airframe, avionics and recovery,
and separate fixed-motor performance and TVC aft assemblies. Model performance,
finned TVC training and eventual finless TVC as distinct resolved configurations.
Fin removal changes physical parts, radial inertia, aero, recovery-transition
requirements and validation evidence together. Shared parts come from one YAML.

Preliminary trade recommendation: 66 mm OD, 800 mm length; thin kraft body sections,
custom reinforced/keyed joints, cut plywood load-transfer parts/fins, printed ASA
nose/sled/gimbal and purchased certified motor/avionics/recovery components. Body
material, dimensions and bore are revisable engineering choices, not permanent
constraints. Printing the whole shell is not required for a substantial custom build.
Custom tube rolling and glass/epoxy fabrication remain worthwhile bounded alternatives.

Performance mode: AeroTech G80-10T single-use SKU 78010 family, fixed 29 mm mount.
TVC modes: reformulated AeroTech G12ST-P DMS SKU 071200 family, custom two-axis gimbal,
independent electronic recovery. The -10 delay is a studied SKU, not a validated
flight deployment setting. Final exact sold envelope/source/California evidence
must be reconciled before hardware and the associated flight-validation claims.
CTI G54 (159.1 N s) is reopened as a higher-impulse performance upgrade; G33 as a
higher-thrust TVC alternative, subject to stock/hardware/classification evidence.
No source quarantine is cured by changing a numerical requirement.

Replace the universal >=3 s and average TWR >=3 gate with mode-specific preliminary
screens: guide departure under lower-bound thrust and mass growth, passive margin
for finned modes, and contiguous useful powered control time for TVC. Average TWR
and source terminal duration remain reported diagnostics. The preliminary screen
uses constant worst-case loaded mass, estimated guide friction and drag; it is not
a free-flight, crosswind, aeroelastic, thermal or closed-loop control validation.

WO-01 validates the preliminary model and records uncertainty; it does not require
completed CAD, hardware, purchasing, flight-ready status or an arbitrary three
accepted alternatives. Later mechanical, flight, control and release gates remain
mandatory and configuration-specific. A source-consistent digital hypothesis can
pass WO-01 while its exact physical correspondence remains an explicit later gate.

## Why this architecture

One optimized passive rocket alone would lose the committed RL/control learning.
One finless long-burn rocket would force performance flights to carry gimbal/servo
mass and inherit the active-control/recovery risk. Two independent airframes reduce
interface risk but duplicate recovery/avionics and hide whether shared engineering
is possible. Modular aft assemblies retain substantial fabrication and integration
learning, isolate motor/control trades and reuse the expensive upper equipment.
The joint adds mass and tolerances; interchangeability must be demonstrated, not
assumed from equal diameters.

Paper/plywood/printed hybrid construction gives the current mass budget room for
robust joints, control hardware and independent recovery. All-printed shells are
heavier at the compared dimensions; printed layer anisotropy and heat response still
need tests. Composite layup teaches useful skills but does not automatically beat
the hybrid in specific performance, cost or Class-1 suitability. See the measured-
versus-estimated distinctions in `docs/wo01-rebaseline.md`.

## Consequences and explicit limitations

- Legacy F15/1.6 mm/1.2 mm specs, original source bytes and old rejection reasons stay
  reproducible. Their gates apply to those studies, not the active platform benchmark.
- F25's short burn is no longer a blanket performance rejection. It passes the new
  preliminary performance rail screen but its current source/variant and eventual
  flight configuration still need their own validation. G25W remains quarantined.
- G12ST has useful control duration at the new mass/guide assumptions despite mean
  TWR below 3. This requires explicit RSO review; it is not a claim that a club must
  accept the flight. A longer guide/test fixture is part of the trade and cost.
- Finless TVC has negative passive margin and loses thrust authority at burnout.
  Demonstrate a safe burnout/abort-to-recovery transition across the qualified
  velocity/wind envelope before release. Adding deployable fins, if needed, creates
  another actual configuration; it is not a hidden toggle.
- RL remains committed: PID baseline, realistic sensors/actuators, domain
  randomisation, embedded policy limits, abort/HIL, logs and system identification.
  Honest negative comparisons satisfy research reporting; no unsafe RL flight is
  required to claim a milestone. G-FOLD and the digital orbital work are preserved.
- No purchases, physical work or paid runs are authorized here. The owner separately
  authorized GitHub pushes and PRs; ordinary PRs require checks, not owner review
  (`AGENTS.md`).

## Reopen when

CAD/measurements exceed mass or clearance budgets; joint/fin/thermal tests fail;
exact motor classification/source is incompatible; club rejects the operating
concept; rail/control/recovery simulation fails; or the modular joint costs more
mass/complexity than its learning/reuse benefit. Revise the affected resolved specs
and their evidence together. Do not quietly change evaluation thresholds to pass.
