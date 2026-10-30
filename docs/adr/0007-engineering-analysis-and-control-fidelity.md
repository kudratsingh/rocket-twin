# ADR-0007 — Engineering evidence before CAD acceptance and control claims

Status: accepted by owner instruction, 2026-10-29. Extends ADR-0006; preserves the
work-order sequence. Substantial custom construction, maximum practical conventional
performance, and committed PID-to-RL development remain equal project objectives.
G80 is the conventional reference, G54 a conditional performance upgrade, and G12
the controls motor hypothesis. No motor-source quarantine or launch gate is waived.

## Decision

WO-03 owns executed structural calculations, targeted FEA, bounded transient thermal
analysis, tolerances, assembly/access and combined-axis motion checks, in addition
to CAD, exports and mass reconciliation. A rendered solid or a matching mass cannot
complete WO-03. Analysis meshes are distinct from display STL/GLB meshes.

Use engineering calculations first. For critical/uncertain load paths, use pinned
Gmsh and CalculiX, verify the setup against known solutions, and refine at least
three meshes. Require <5% change in the decision displacement and <10% change in
regional stress between the final two meshes, or continue refinement/report the
conclusion as unresolved. Exclude boundary/load singularities only with a defined,
physical reporting region and an explanation; do not hide a governing joint stress.
Record solver versions, input hashes, units, equilibrium residuals and all failures.
An unresolved solver, strength, fit or thermal conclusion keeps its acceptance gate
open. Completing an analysis with a failure is valuable evidence, not design release.

Define thrust/acceleration, fin bending, guide reaction, gimbal/servo reaction,
modular-joint retention and recovery-opening load cases. Trace each through actual
parts and bonds/fasteners. Evaluate stress, deflection and relevant local/global
buckling. Document orientation/grain, temperature effects, estimated versus measured
properties, boundary conditions, uncertainty, justified factors and physical tests.

Thermal analysis covers G80, conditional G54, long G12 exposure and post-burn soak.
Use published case-temperature histories when available; otherwise explicitly
bounded external-case temperature scenarios, not invented measured motor data.
Include liner, contact/air gaps, radiation, shields, adhesives, printed mechanism,
structure and nearby electronics. Report histories, peaks, uncertainty and applicable
temperature-dependent limits; verify energy/time-step behavior. Use results to revise
spacing, shielding/materials. Define instrumented verification before physical use.

Dimensions, manufacturing tolerances, expansion assumptions and minimum clearances
live in the YAML specification. Check minimum/nominal/maximum fit, insertion and
removal paths, fastener/bond access, gimbal combined deflections and wiring/nozzle/
retention envelopes. Purchased geometry and articulated joints remain explicit
supplier-fit gates until their exact drawings are reconciled. Reconcile CAD mass,
CG and inertia, then repeat affected static and flight comparisons. Keep the complete
WO-02 evidence immutable as the pre-CAD numerical baseline.

WO-06 cannot claim the PID benchmark until the shared JAX model includes linkage
kinematics, moving motor mass/inertia, torque/speed under load and supply voltage,
friction/backlash, deadband, limits and latency, with sources, uncertainty and
validation cases. Aerodynamic force, moment and damping must cover the intended
Mach/Reynolds/angle-of-attack envelope, including large angles seen in the G12 study.
Out-of-domain operation is flagged and excluded from a validated success claim.
Targeted CFD or other higher-fidelity analysis is required when needed for a concrete
design decision. Feed coefficient tables into the shared core, never browser physics.

WO-07 uses those models, randomizes residual uncertainty and evaluates PID and RL
fairly on held-out conditions. Preserve negative comparisons, embedded constraints,
independent abort logic, HIL and eventual flight comparison. WO-09–12 carry measured
material/joint/temperature/actuator/aero calibration, uncertainty and held-out evidence.

## Tools and gates

Keep CadQuery/OpenCascade, Three.js and JAX. Proposed analysis pins: Gmsh 4.15.2 and
CalculiX 2.23; installation/execution must be verified before describing them as
available. CFD is a targeted later decision; no OpenFOAM installation or paid run is
implied. Manufacturer/solver sources belong beside the actual numerical inputs.

Routine focused PR/check/merge workflow continues. Purchases, owner-performed
fabrication/tests/flights, paid runs and WO-10 firmware/abort owner review remain.
No numerical result authorizes flight; exact hardware, California/club/RSO, recovery,
structural/thermal measurements and finless burnout transition remain release gates.

Sources: [Gmsh documentation](https://gmsh.info/doc/texinfo/gmsh.html),
[CalculiX](https://www.calculix.de/),
[CadQuery BRep concepts](https://cadquery.readthedocs.io/en/stable/primer.html).
