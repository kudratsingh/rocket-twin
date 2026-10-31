# WO-03 — CAD, structural/thermal analysis and integration

Branch: `wo-03-cad` (focused dependent PRs permitted). Tier: Mac CPU and ordinary
repository checks; paid compute requires separate approval. ADR-0007 expands this
work order without changing the full-milestone sequence. Full WO-04 completion
depends on the WO-03 criteria below. ADR-0009 separately permits the owner's limited
early inspection/experiment preview; that preview is currently paused while
engineering work resumes. G80 reference, G54 conditional, G12 controls.

ADR-0008 adopts the combined correction package into the active specifications.
Use [the integrated property report](../wo03-integrated-vehicle.md) and
[issue closure table](../wo03-correction-closure.md), including remaining design
failures. Proposal-only recovery, fin or motor-support passes are historical
inputs; acceptance applies to the complete resolved vehicle, wiring and allowance.
Known-case verification, nominal CAD motion, minimum-thickness analysis, installed
root evidence and later physical qualification are distinct evidence levels.

## Deliverables

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
The owner's later preview resumption permits code/non-browser checks only;
computer use remains paused until testing is resumed.

Follow [the three-deliverable closure plan](../wo03-closure-plan.md) and
[thermal method decision](../wo03-thermal-method-decision.md). This records the
owner's2026-10-31 direction to isolate impossible temperatures on known cases,
verify actual geometry and refinements, stop repeated invalid/capped attempts,
and assess a justified bounded alternative before further expensive retries.
It adds no physical acceptance requirement or work-order scope. Complete-package,
recovery/support and installed-fin criteria above remain in force. Frontend and
browser work remain paused; the saved preview and all release gates are preserved.

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
