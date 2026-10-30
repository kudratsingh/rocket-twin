# WO-03 — CAD, structural/thermal analysis and integration

Branch: `wo-03-cad` (focused dependent PRs permitted). Tier: Mac CPU and ordinary
repository checks; paid compute requires separate approval. ADR-0007 expands this
work order without changing the sequence. WO-04 starts after all WO-03 criteria
below are met and recorded. G80 reference, G54 conditional, G12 controls.

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
