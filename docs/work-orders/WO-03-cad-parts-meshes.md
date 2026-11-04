# WO-03 — CAD, structural/thermal analysis and integration

**Current delivery: [VP1 owner-review validation package](../validation/rp1-vp1/package-summary.md).**
One first test lead is ordinary6mm02-20850 birch with WEST105/206/406 fillets;
this is not vehicle adoption. Four product drafts plus one supervised-lab RFQ
are complete and UNSENT. Recommended first authorization is inquiries only,
$0; no purchase, paid consultation, fabrication or loading. No email-sending
connector is available; owner-ready drafts/forms are supplied.

Room-pilot stock lists$236.75; conditional full stock reserve$269.49. Services,
fixtures, calibrated channels and delivery are unquoted, so the all-in total
is unavailable, never zero. A$5,000 planning reservation is an affordability
screen, not a price or spending permission. Method/replication/uncertainty and
stop conditions are in the [protocol](../validation/rp1-vp1/protocol.md). No full
root execution is admitted without the specified method, supported construction,
written quote and owner authorization. S0 closes after10businessdays, with one
follow-up; do not wait for supplier aerospace allowables.

D1's8.83N·m/331.125N once-factored load,1mm movement, estimated material screens,
50g growth,20g adverse/motor probe,55/68g harness cases,1.5m/15formal/15.5planning
and physical/thermal/recovery/flutter/WO10/flight gates remain unchanged.
Frozen AD1, unadopted FP1/FR1 and G54/G12 PID-to-RL stay separate. G80 first,
substantial custom construction and practical performance remain core goals.

Frontend [portable RP1 SVG exports and graph zoom](../wo04-rp1-export-20261104.md)
are merged inPR79 after required checks. Actual-source/code/SSR checks pass;
browser interaction remains unverified behind the unchanged ownership block.
Existing inspector, experiments and replay preserved; no browser workaround.

## Retained D1 and expanded acceptance criteria

**Current integrated decision: [RP1 D1 — load and attachment](../wo03-rp1-load-attachment-decision.md), ADR-0015.**
The owner assigns primary integration; the coordination question is closed.
Merged FR1 PR75 (solid carbon) and FP1 PR76 (carbon-faced plywood) are separate,
**unadopted** studies. Frozen AD1 v2 stays unchanged. FR1 fails evaluated finite
movement/body-bond screens; FP1's nominal0.961 mm includes an unverified0.100 mm
attachment input and fails material sensitivities. No installed fin pass.

Enforce8.83 N·m /331.125 N, factor3 already applied once. Current-planform
40 kPa/5° arithmetic gives2.905255 N·m but is not an adopted governing case.
Older70 mm-fin calm flights cannot establish current60 mm RP1 loads/inertia.
D1 reconciles the source, complete-root model and exact-once mass alternatives;
12/16 combined material diagnostics fail, none is a qualified property bound.
No new fin variant, vehicle change, stopped solver retry or detailed CAD/FEA
is admitted. Next: [bounded representative evidence definition](../wo03-rp1-d1-test-definition.md),
then source/whole-root evidence before one possible construction correction.
No purchase, supplier contact, physical test or owner hardware measurement.

[Accounting](../wo03-rp1-integrated-accounting.md) preserves full separate50 g,
20 g adverse/motor probe and55/68 g unverified harness cases. D1 adds0 g.
All FP1/FR1 cases miss15.5 planning; FP1 adverse68 g also misses15 formal on
reference1.5 m. Longer equipment remains unconfirmed. G80 custom building and
practical performance first; G54 upgrade and committed G12 PID-to-RL separate.
WO-03, thermal/recovery/installed flutter, physical and flight gates stay open.

[Separate frontend study comparison](wo04-rp1-studies-20261104.md) adds source-linked
selectable relationship graphics. Actual offline PNGs inspected; browser
interactions remain unverified behind the unchanged ownership prerequisite.
Preserve inspector/experiments/replay and exact configuration identities.

## Retained expanded completion criteria and earlier checkpoints

Latest bounded follow-up: **RP1 AD1 v2**,
[attachment definition](../wo03-rp1-attachment-definition.md) and
[representative test plan](../wo03-rp1-representative-test-plan.md). Exact cords,
proposed finished ends, contacts, finite-support demands and full mass/guide
consequences are recorded. The changed fin's optimistic screen FAILS5MPa/1mm;
finished attachment and conditioned joints remain unknown. Do not restart
unchanged-fin detailed analysis, stopped solvers or silently transfer old support
results. A sacrificial test plan ready for owner review is not an authorization
to purchase/fabricate/load it or manufacture the flight vehicle. Aggregate
WO-03/physical/flight gates and independent G54/G12 PID-to-RL remain unchanged.

Current bounded recovery deliverable is RP1 in
`docs/wo03-f2-recovery-precedent-decision.md`. A motor-tube wrap/nylon topology is
recommended from manufacturer precedents. Its single balance correction passes
the formal1.5m departure screen under estimates, misses15.5planning and loses
the former front-tab ring support. Hold
adoption and expensive work pending the named mass/equipment/joint decisions.
This does not close structural/thermal/root/flutter or aggregate acceptance.
F2-C2 arithmetic was superseded before execution; stopped F2/C1 methods stay stopped.

F2-C1 connection packet is recorded in `docs/wo03-g80-f2-c1-decision.md` and `configs/engineering/g80-f2-c1-verification.yaml` (repository-relative). Seven proposed fits and coupled mass are calculated; installed recovery/motor/thermal/fin gates and3-grid accuracy remain open. Fine node-capped attempts stopped without resource increases; no full-WO or physical adoption. Source-linked frontend study is independent of the active design.

G80-F2 is the separate actual-stock construction follow-up to frozen F1. See `docs/wo03-g80-f2-decision.md` (relative to repository root). Only local joint CAD is executed; static/formal-guide passes do not close installed recovery/fin, thermal, exact motor fit, planning-speed or full WO-03 gates. Preserve G54 and G12/PID-to-RL separately.

Current delivery: dedicated fixed G80-F1 under[ADR-0013](../adr/0013-dedicated-conventional-g80.md)
and[bounded packet](../wo03-g80-fixed-packet.md). Physical interchangeability is
optional for first G80. Deliver one coherent specification/CAD/mass/construction
package after feasibility, with mechanism-based recovery review and explicit
prototype versus physical/flight gates. G54/G12 and aggregate criteria remain.

Latest local connection decision: [A1](../wo03-a1-connection-decision.md), separate
from frozen C1/A/B. Actual joint dimensions and complete mass are now recorded,
but baseline guide/bolt screens fail and installed/hot/source evidence is open.
No detailed whole-vehicle CAD/FEA or aggregate acceptance is admitted by it.

Branch: `wo-03-cad` (focused dependent PRs permitted). Tier: Mac CPU and ordinary
repository checks; paid compute requires separate approval. ADR-0007 expands this
work order without changing the full-milestone sequence. Full WO-04 completion
depends on the WO-03 criteria below. ADR-0009 separately permits the owner's limited
early inspection/experiment preview. The owner resumed its implementation and
designated-agent browser verification on2026-10-31 while engineering work
continues. G80 reference, G54 conditional, G12 controls.

ADR-0008 adopts the combined correction package into the active specifications.
Use [the integrated property report](../wo03-integrated-vehicle.md) and
[issue closure table](../wo03-correction-closure.md), including remaining design
failures. Proposal-only recovery, fin or motor-support passes are historical
inputs; acceptance applies to the complete resolved vehicle, wiring and allowance.
Known-case verification, nominal CAD motion, minimum-thickness analysis, installed
root evidence and later physical qualification are distinct evidence levels.

## Current executed checkpoint — G80 retention remains open

The source-pinned coarse fields now pass force/reciprocal-work checks and the
stress recovery method passed known cases, but face-resultant bounds exceed the
estimated hot bond screen. The physical bridge is2 mm thick;1.5 mm names the
coarse mesh target. The two mesh-only pilots do not establish uniform regional
refinement, and no convergence pass follows. Evaluate a positive mechanical
reverse-load path with its complete mass/CG/fit/thermal/recovery consequences
before further automatic analysis of the unchanged bond-only candidate.
See [closure](../wo03-g80-current-closure.md),
[traction bounds](../wo03-g80-bridge-support-traction.md) and
[correction trade](../wo03-g80-retention-correction-trade.md).
The finite0.1 mm shear-layer verification, actual backing/contact, regional
convergence, hot directional/bond properties and all other criteria remain
applicable; the axial known case alone does not replace them.

The [bounded B/C comparison](../wo03-g80-capture-decision.md) now rejects both
specified envelopes at early screens; no CAD/FEA was admitted and no installed
requirement closes. The next finite direction is a short captured G11 aft
subframe linked to the protected aramid backbone. Endpoint/body/fin/motor
restraints, hot properties and complete mass/fit/load ledger must pass admission
before detailed work. This does not revise the work-order sequence or criteria.

The owner's subsequent bounded S1 admission is recorded in
[connections/margins](../wo03-g80-short-subframe-decision.md). It fails coupled
recovery bearing, full-growth guide mass and heel screw length; no CAD/FEA is
admitted. Revise IF-RECOVERY-001 with a real load-spreading endpoint and the
complete mass ledger, recalculate the same recovery cases at that mass, and
retain guide speed/thermal/structural criteria. This changes the next design
interface, not the formal work-order sequence or acceptance requirements.

The following bounded [S2 study](../wo03-g80-saddle-study.md) preserves the
required20.4m/s/.3m/DF3 case and recalculates it at full new mass. S2 is not
admitted; it misses the declared useful guide margin and lacks a positive
carrier/fin-frame/body receiver, qualified soft/contact capacity and motor
thermal clearance. The initial output stop and failed adjacent integration
check are preserved. No third concept or automatic refinement follows. The
next design must close those physical interfaces and coupled mass/balance
before detailed CAD; no work-order sequence or acceptance gate is removed.

The [subsequent integrated aft decision](../wo03-integrated-aft-proposal.md)
screens the receiver, fin/body capture and independent motor retention together.
The additive sketch exceeds the unchanged formal guide-model mass ceiling at
named stock alone and retains adverse/unresolved joints, hot contact and
partial stability. No complete arrangement is selected. Before another physical
iteration, define one positive common receiver replacing duplicated structure,
with dimensioned mating/retention, full hardware/heat/service mass, recalculated
opening demand and useful guide margin. No new CAD/FEA/thermal/flight campaign
is admitted here. S2 PR45 publication preserves its failed numerical checks.

The owner subsequently authorized one connected receiver and parallel bounded
Sol HIGH launch/motor comparison. [S3](../wo03-g80-connected-receiver.md) defines
continuous end-bearing/positive joints but fails mass/planning,1cal stability,
independent service and recovery/body/contact admission; no CAD/FEA/flight
follows automatically. [ADR-0012](../adr/0012-conditional-launch-guide-options.md)
keeps1.5m usable as baseline and records conditional longer-guide options.
Validate actual rod-lug/button compatibility, usable versus overall travel,
support/operating conditions and counted attachments before any baseline change.
Guide-model mass ceilings are configuration-specific, never universal≈1kg limits.
Preserve15m/s formal, separate15.5 planning and full separate50g, unchanged
thermal/structural criteria and independent G54/G12 evidence.

Owner-authorized [C1 mass/balance study](../wo03-g80-mass-balance-revision.md)
is the next pre-geometry checkpoint. Its calculated1.319cal loaded margin with
full50g addresses balance by a counted receiver plus changed fin planform,
not an unmodeled ballast/forward move. Existing cap/body/harness/contact and
new thin-body/socket/fin strength/flutter remain acceptance items. Recompute
mass/static/guide/recovery when those corrections change the ledger. Current
1.8m departure14.975m/s fails15; actual guide/button/support/site confirmation
is a dependency, not an assumption erased by numerical travel roots.

**Current C1 attachment checkpoint (2026-11-02):**
[C1 source identity](../wo03-c1-attachment-source-lock.md) is frozen at1079.807g
nominal + separate50g =1129.807g. The one [R1 installed-fin reinforcement
preflight](../wo03-c1-fin-attachment.md) is stopped before CAD/native analysis:
+70.111g, bridge mean hot shear4.756MPa>estimated1MPa, corrected ideal aggregate
movement1.039mm>1mm, adverse static margin0.991984cal<1.0. Nominal/adverse
masses1199.918/1219.918g miss conditional15.5m/s planning by47.602/67.602g.
Adverse formal speed15.000251870m/s on illustrative1.971m has only0.035501g
headroom and is not useful margin. C1 remains selected preliminary; no active
change or installed/thermal/flutter acceptance. The one next construction
preflight is a lightweight sandwich fin/dense captured root and mechanically
closed socket, with complete replacement mass and finite end/body connections.
Keep1.5m baseline, full50g,15m/s formal and separate15.5 planning unchanged;
all equipment remains unconfirmed. G54 and G12/PID-to-RL stay separate.

## Deliverables

**Delivery priority, ADR-0011:** execute these requirements first for one complete
conventional fixed-motor G80 candidate. Preserve G54's upgrade requirements and
G12's controls/finless track and evidence. Per-configuration progress is not
aggregate WO-03 completion; no formal completion criterion is removed or relaxed.
The owner-authorized saved frontend preview proceeds independently under ADR-0009.

1. Spec-driven CadQuery solids for every part in all three actual configurations;
   shared upper and distinct afts; separate G54 fit study and credible motor
   comparisons. Custom nose, reinforced/keyed modular joint, cut/printed structures,
   motor retention/liners, fin roots, bearing/pivot gimbal, servo mounts, horns,
   pushrods, stops, recovery and avionics mounts. Commercial/flexible items use
   supplier or estimated masses and explicit envelopes. Every part has build and
   learn content, source, cost and mass basis. Preserve the WO-02 configuration archive.
2. One-command STEP/STL/GLB regeneration, per-part and assembled files, manifest,
   print orientation/support settings and mass/centroid/inertia report. Printed
   parts fit 220 x 220 x 250 mm. CAD volume uses credible material density; purchased
   envelope volume must not masquerade as physical mass verification.
3. Structural case table and executed calculations for thrust/acceleration, fin
   bending, guide reactions, gimbal/servo reactions, modular retention and recovery
   opening. Trace loads through real joints and parts; evaluate stress, deflection,
   bearing/shear/bond loads and buckling where applicable. Record force balance,
   boundary conditions, grain/print orientation, temperature derating, property
   sources/ranges and justified design factors. Identify weak or unclosed load paths.
4. Targeted Gmsh/CalculiX FEA of critical/uncertain components. Pin tools, archive
   input/mesh identities, verify a known solution and equilibrium, and demonstrate
   at least three-level mesh refinement. Final displacement change <5% and regional
   stress change <10%, or refine/leave the conclusion unresolved. Define stress
   regions and singularity handling. Correlate with hand calculations; document
   material/connection idealizations and required coupon/joint/proof tests.
5. Executed bounded transient thermal models for G80, G54 and G12 through burn and
   post-burn heat soak. Model the case boundary, liner, gaps/contact/radiation,
   shields, structure, bonds, printed gimbal and nearby electronics. State published
   or explicitly assumed case-temperature bounds, property/temperature-limit
   sources, uncertainty and sensitivities. Produce temperature histories/peaks,
   energy/time-step checks and resulting design decisions. Define thermocouple,
   hot-soak, adhesive and electronics tests for the owner-performed stages.
   Partition partly bonded regions into geometry-derived adhesive, other-solid
   and genuinely open areas; do not apply full-area gas and glue through the same
   volume. Resolve visible ring/end, slot/notch/seam radiation and relevant gas
   leakage with compatible CAD, contacts and source uncertainty. Record a short
   connection table, before/after histories and part-average versus local coverage.
   Rejected or superseded thermal passes remain historical evidence. ADR-0010
   defines the interior control volume and common-surface exchange bookkeeping.
6. Spec-owned tolerance and thermal-expansion stacks for couplers, indexing keys,
   motor/retention, bearings/pins, rods/servos and removable modules. Report minimum,
   nominal and maximum clearances against required minima. Check insertion/removal,
   fastening/bond access, wiring slack/bend and retention/nozzle keep-outs throughout
   combined two-axis motion. State sampling versus continuous bounds and unresolved
   purchased geometry. Never label a nominal pose or joint exclusion full validation.
7. CAD volume/CG/full inertia reconciled into the shared YAML and JAX/RocketPy
   adapters. Account for new structure, sensor, shielding, fasteners and harness.
   Resolve the high-g sensing requirement while retaining the low-g IMU. Re-run
   static and applicable flight/reference/uncertainty studies after design changes;
   retain the original WO-02 records and reasons for any changed result.

## Completion criteria

`make cad` regenerates every configuration and all exports; all parts are valid,
manufacturable-intent solids with declared mass bases; CAD custom-part mass agrees
with the adopted spec within 10%. This is unmeasured design reconciliation.

`make engineering` executes structural, thermal, tolerance/motion and required FEA
reports. Reports contain assumptions, margins, failures and limitations, versioned
inputs, source hashes and required physical verification. Known-case solver and
convergence checks pass. Critical numerical interferences, unclosed load paths or
unresolved strength/temperature conclusions are corrected or remain explicit open
WO-03 acceptance items; a report file alone cannot close them.

Affected static checks and JAX/RocketPy apogee/time benchmarks pass for actual
performance and locked finned-TVC configurations with their current mass properties.
Source hypotheses and uncertainty remain visible. Inspectable exports and concise
part-function/load-path documentation are available. Record evidence in STATUS and
results before advancing to WO-04. Actual strength, temperature, fit, recovery and
control qualification remain owner-performed WO-09–11 gates; flight_ready stays false.

## Bounded closure execution

The [external-tool comparison decision](../wo03-external-thermal-decision.md)
records the owner's research-first checkpoint: Elmer plus installed CalculiX,
two declared600-CPU-second packets,120s/case, separate600s setup caps, unchanged
accuracy requirements and explicit unavailable results. Neither tool qualifies
for the actual baffle yet. Publish this focused evidence before another selected
approach; no new production numerical method or physical acceptance follows.
The owner subsequently authorized the bounded frontend agent to verify the
preview in the designated Chrome window. Other agents must not use computer
tools concurrently; see `AGENTS.md`. Full milestone and release gates remain.

Follow [the three-deliverable closure plan](../wo03-closure-plan.md) and
[thermal method decision](../wo03-thermal-method-decision.md). This records the
owner's2026-10-31 direction to isolate impossible temperatures on known cases,
verify actual geometry and refinements, stop repeated invalid/capped attempts,
and assess a justified bounded alternative before further expensive retries.
It adds no physical acceptance requirement or work-order scope. Complete-package,
recovery/support and installed-fin criteria above remain in force. The separately
authorized preview and designated-agent browser checks proceed without changing
these requirements or release gates.

## Thermal numerical evidence: four separate gates

The owner explicitly reinforced these distinctions after the actual gas-mesh
and factor attempts. Every current report and closure table separates:

| Gate | Required evidence | Current examples and non-claims |
| --- | --- | --- |
| Mesh validity | Positive-volume cells, complete material/boundary ownership, geometry/barrier preservation, orientation and domain closure | The old coarse mesh passes its recorded geometric checks; its middle mesh is invalid. Neither establishes accurate temperatures; the subsequent complete coarse debug transient uses a failed field operator. |
| Calculation completion | A completed solver result with exact input/configuration/CAD/mesh identities and usable outputs | A runtime-capped fine mesh or coarse factor is incomplete. A cap alone establishes neither numerical success nor numerical failure. |
| Numerical accuracy | Applicable known cases, residual/heat-balance checks, and required time/spatial refinements supporting stable relevant temperatures/heat routes | Method fixtures cannot fill missing actual-solve energy or refinement evidence. Preserve invalid attempts and diagnose them or document a replacement method. |
| Temperature acceptance | Applicable unchanged required-case matrix and limits, with result resolution, uncertainty and margins explicit | The completed failed-operator debug run establishes no credible new-baffle temperature; 45°C substrate and combined300°C/contaminated-foil/35°C cases remain. A completed provisional coarse result alone cannot accept the design. |

Use explicit states such as invalid, incomplete, unestablished and unavailable;
do not turn missing data into a zero/pass or describe a time cap as a failed
physical temperature case. Part means and calculated local hot spots remain
distinct. Current working geometry and release gates remain unchanged while
these calculations are corrected.

## Analysis export deliverable and acceptance (owner extension)

Export versioned analysis manifests and field/history assets for the Analysis view
in `docs/UI.md`. Each artifact identifies exact configuration, resolved-spec hash,
CAD/generator revision, part IDs and mesh hashes, SI units/frame, case, quantity/
component/criterion and association (node/element/integration point/part/measured
point), time samples, coverage and original report. Record extrema, limits and margin
formula/threshold, assumptions, material/boundary uncertainty, validation/convergence
status and physical test requirements. Keep analysis meshes separate from display
meshes and export registration/mapping; preserve discontinuities and exclusions.

Calculated results, estimated inputs/proxies, located measured data and unavailable
coverage must be distinguishable in machine-readable metadata. Part-level thermal
or margin results are acceptable at their actual resolution; no fabricated spatial
stress field. Missing/stale/incompatible data must not become zero or a pass. Export
identity checks and a backend consumer smoke check are part of WO-03 acceptance.
All computation remains in the backend/offline pipeline. WO-04 consumes the exports;
WO-05 adds recorded case/run comparison and explicit transient/replay time mapping.

## Requirements, interfaces, FMEA and vibration/flutter acceptance

Maintain lightweight source-linked artifacts with stable IDs:

- Requirements/verification matrix: configurations (G80, conditional G54, finned
  G12, eventual finless), purpose/source, criterion or active-spec reference, related
  parts/interfaces, method, responsible WO, evidence and status. Cover scope/
  performance, guide, stability/control, mass/CG, loads/heat, recovery, sensors/power
  and operating conditions. Distinguish provisional assumptions and established
  requirements from measured evidence; track site, guide and supplier unknowns.
- Interface table: shared-upper/aft, motor/retention, gimbal/servos, avionics,
  recovery and electrical/software boundaries. Include datums/axes/units, dimensions/
  tolerances, load paths, retention, min/nominal/max clearance, connectors/power,
  configuration identity, indexing/keying/identification and unresolved dependencies.
- Initial FMEA: hardware/software/operating causes, local/system effects, justified
  qualitative severity/likelihood or uncertainty, detection, mitigation, residual
  risk, requirements/design links and later tests. Prioritize servo jam, brownout,
  sensor clipping/dropout, connectors, structures/heat, wrong-module pairing and
  recovery/common-cause failures. State abort limitations and finless burnout facts.

Execute structural-mode/resonance and fin-flutter screens with actual CAD/mass,
material ranges, attachment/damping assumptions and flight speed/load envelope.
Include temperature-dependent stiffness and joint/gimbal/propulsion/servo/sensor
interactions. Report calculated frequencies/modes, method/domain validity, flutter
results and uncertainty; verify against known cases and apply existing FEA mesh
convergence criteria. Identify design decisions and physical modal, torsion, loaded-
mechanism, vibration/aliasing and flight measurements required. Unresolved critical
issues remain acceptance items, not automatically deferred passes.

Generate the per-part engineering table from the shared specs with function,
material/method, mass provenance, dimensions/tolerances, load/thermal/vibration
cases, results/margins, evidence status and physical verification. Include preliminary
assembly/service diagrams and identify the later dimensioned drawings, plywood
cut/drill templates and print settings. Complete procurement/build pack remains WO-09.

## Current correction-package closure priorities

Retain the criteria above and close the selected package as one configuration,
using [the current closure table](../wo03-package-closure-progress.md):

- Package A with two added brace rings must demonstrate its complete rail/ring/
  bond/body/upper-joint path, including hot properties, support stiffness, force
  balance, local bearing, bond peel and effective buckling lengths. Frame-only
  eigenvalues or perfectly restrained strip ends do not close the assembly.
- Apply the explicit configuration-specific thermal matrix in
  `configs/engineering/wo03-thermal-acceptance.yaml`. Keep the 45°C substrate
  screen unchanged. The combined 300°C case / contaminated foil / 35°C ambient
  is required robustness pending evidence; failed rows block acceptance unless
  a separate justified design or operating-boundary decision resolves them.
  Controlled-ambient and ignition-temperature proposals remain proposals until
  their enforceable limits, rationale and effects are recorded.
- Count the entire independent recovery system, reinforcement and mounting once.
  Preserve conservative G12 departure at 10 m/s on the assumed 5 m usable guide
  with the full 50 g allowance. Record total capacity and incremental headroom;
  revalidate explicit vehicle/construction trades if the package exceeds it.
  Actual 5 m guide availability is unresolved equipment evidence.

Adoption requires one reconciled mass/CG/full-inertia model, current CAD/Analysis
identities, and affected structural, thermal, fit, stability, flight and reference
comparisons. Installed fin/root/flutter, retention and service-access requirements
remain in scope. Distinguish design failures from owner-performed proof, electrical,
deployment and flight qualification. A partial candidate pass cannot close WO-03
or the prerequisites for full WO-04 completion.

## C2 next-correction checkpoint

**C2 bounded correction — rejected before detailed CAD/FEA (2026-11-02):**
The [complete sandwich/socket preflight](../wo03-c2-sandwich-socket.md) removes
196.092g and adds250.021g, net+53.929g. Full50g nominal/adverse totals are
1183.736/1203.736g, loaded margins1.139/1.034cal. Hypothetical1.971m speeds
15.263/15.116m/s pass formal15 only; planning15.5 and unchanged1.5m fail.
Receiver-pad hot mean shear3.828MPa>1, floor58.501MPa>25 and motion2.328mm>1
fail; actual nominal2D harness/link envelopes overlap. No installed engineering
requirement closes. Do not admit CAD/native analysis or another local glued pad.
The necessary interface change is continuous structural socket/receiver/end
moment transfer compatible with the recovery route. C1 stays preliminary; G54
and G12/PID-to-RL stay separate. Existing physical/paid/WO10/flight gates remain.
The saved axis-to-tip conversion now uses123mm: C1/R1 scalar aggregates
3.198/1.054mm; earlier3.179/1.039 proxies remain preserved as superseded.


## C3 continuous-connection admission stop

**C3 continuous-connection preflight — not admitted (2026-11-02):**
The [one bounded packet](../wo03-c3-continuous-connection.md) replaces local pad
transfer with integral channels and positive cap pockets as design intent.
Its aft central barrel node physically overlaps independent motor arms;
nominal harness gap0.647848mm becomes−0.052152mm after the existing bounds,
below0.1mm. Complete counted mass adds105.504g: nominal1235.311g and adverse
1255.311g each include full separate50g. Illustrative1.971m departure14.891938/
14.754038m/s fails formal15; adverse stability0.957949cal also fails.
No installed engineering requirement closes; no CAD/FEA/thermal/free-flight
run is admitted. Keep the59.299g body-support receiver counted until a defined
replacement earns its credit. Next interface must separate motor-retention
travel from end-fastener stock and combine body-support/torsion functions;
do not restart a local-pad or unchanged-channel variant. G80 stays first,
G54/G12 remain separate,1.5m baseline and all gates unchanged.



## Architecture-first A/B checkpoint

[Current decision](../wo03-architecture-decision.md) compares exactly two
complete function/space/mass arrangements with the same full-growth ledger,
source loads and guide model. A is preferred for joint-demand development;
neither is admitted to complete detailed CAD/FEA. The fore-cuff windows and
motor/recovery reservations are explicit; physical capacity, installed
stiffness/heat, supplier fit and the baseline guide budget remain open. This
checkpoint closes a bounded study, not an engineering requirement or WO-03.
Continue the authorized workbench/source/launch preparation in parallel.
