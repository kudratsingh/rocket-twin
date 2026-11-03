# G80-F2-C1 — recovery force mechanisms and evidence boundaries

**Keep the required severe case unchanged.** Canopy inflation and separated-section
line snatch are additional mechanism comparisons, not grounds to replace the
20.4 m/s / 0.3 m / DF3 requirement with a smaller force. This note clarifies their
inputs and meanings; the primary owns the same-configuration calculations and
engineering decision. It selects no hardware, coefficient, recovery timing or
new allowable, and makes no qualification claim.

The source packet was declared before browsing: **at most four unique primary
URLs and eight minutes**, counting failures. Research ran from 2026-11-03
10:24:00 to 10:25:24 UTC and closed at **three attempted URLs, two readable and
one failed**. Search discovery and repeats of the same URL do not add a unique
URL. No contact, purchase, simulation, solver, computer UI, hardware or Git
operation occurred. Only this new note was written; prior F1/F2 records and
specifications remain frozen.

## Required comparison and why it stays separate

The [F2 coupled record](wo03-g80-f2-coupled-accounting.md) retains

`F_required = DF × m × [v²/(2s) + g]`,

with `v = 20.4 m/s`, `s = 0.3 m`, `DF = 3` once and `g = 9.80665 m/s²`.
Its recorded complete masses, including the full separate 50 g, are
917.559981 g nominal and 937.559981 g adverse; the rounded context values are
917.56 / 937.56 g. Recorded whole-case demands are **1,936.253 / 1,978.458 N**.
These are existing F2 results, not new calculations in this note.

This is a prescribed, vertical whole-mass arrest model. With an upward tether
force, negligible body drag and a downward-travel arrest from `v` to zero over
`s`, work-energy gives the displacement-mean tension `m v²/(2s) + mg`.
Constant deceleration makes that tension constant in the idealization. Real
transient peak tension is not established by the prescribed travel or DF3.
The 0.3 m means stopping travel in this model; it is not measured nylon stretch,
canopy inflation distance or line payout. The requirement remains even if a
different mechanism model predicts less. A credible larger demand must also be
reported, with its own provenance and assumptions.

## Primary sources and what they establish

| Source / exact access | Supported role | Limits |
| --- | --- | --- |
| [NASA SP-8066, *Deployable Aerodynamic Deceleration Systems*, June 1971](https://ntrs.nasa.gov/api/citations/19710021827/downloads/19710021827.pdf?attachment=true), §§4.6.2–4.6.3, printed pp. 59–60 (PDF pp. 65–66) | Treats opening and snatch separately. Opening-load factors require relevant empirical data. Snatch uses the velocity difference at line stretch and a spring/mass representation; neglect of drag is conditional. It warns that a simplified calculation can miss traveling stress-wave effects. | A spacecraft design guide, not an F2 canopy/harness test or a universal hobby opening coefficient. No NASA structural factor or numerical load is imported. |
| [Raiszadeh and Queen, AAS 04-271, *Mars Exploration Rover Terminal Descent Mission Modeling and Simulation*](https://ntrs.nasa.gov/api/citations/20040037788/downloads/20040037788.pdf), printed p. 4 (PDF p. 4), Figures 3–4 | Distinguishes an initial line-end inertial snatch peak from a later canopy-inflation opening peak. The authors explicitly identify their model's unusually high snatch response as an effect of the modeling assumption. | This is a description of a MER model and its limitations, not F2 force measurements. Its relative ejection velocity, inflation history, environment and peak ordering do not transfer. |
| [Earlier NASA flight-test PDF 19670022936](https://ntrs.nasa.gov/api/citations/19670022936/downloads/19670022936.pdf) | Attempted the existing F1 source lead. | Retrieval failed because its 19,972,247-byte content exceeded the web tool's size limit. No newly verified claim relies on its contents. |

The earlier [F1 recovery review](wo03-g80-f1-recovery-review.md) remains useful
for event decomposition and missing-input questions. Its other vehicle masses,
forces and source coefficients are not F2 evidence.

## Inflation is an aerodynamic event, not an assumed short stopping stroke

For a canopy moving relative to local air, define dynamic pressure as
`q(t) = ½ ρ(t) V_air(t)²`. A quasi-steady drag approximation is
`D_canopy(t) = q(t) [CdS](t)`. That is an aerodynamic force model, not a complete
riser-tension solution: canopy/line inertia, added-air effects, fabric motion,
vehicle deceleration and load-path dynamics can alter the force history.

A useful way to report an empirical opening comparison is
`F_open,peak = C_open × q_start × [CdS]_full`, where **here `C_open` is defined
as the ratio of peak force to that reference drag**. This definition supplies no
value or valid range. It requires compatible canopy type, area convention,
mass ratio, packing/deployment and flight-condition evidence. A coefficient
chosen only to obtain a passing force is unsupported. The historical F1
RocketPy/Knacke-style 1.2–2.0 sensitivity is not a NASA-validated F2 interval.

F2's **750 mm canopy diameter, Cd 0.75 and 0.3 s inflation time are estimates**.
The diameter must be identified as nominal laid-flat, projected or another
supplier convention before multiplying it into a drag area. Density, local
airspeed at filling, porosity, shape, lines and packing also need a basis.
A 0.3 s area ramp does not mean the whole rocket stops in 0.3 s or travels
0.3 m. Time, distance, force and velocity history cannot be interchanged without
solving the stated motion and identifying its end conditions.

The integral relations answer different questions: impulse determines momentum
change, while work determines kinetic-energy change. A time-mean force from
`Δp/Δt` and a displacement-mean force from `ΔE/s` need not coincide for a
nonconstant transient. Neither alone specifies its peak. A smooth simulator
area ramp is a model assumption, not a measured opening-load trace.

## Snatch depends on relative section motion and the arresting compliance

The following equations are **direct conservation-law derivations**, not a
formula claimed to have been validated by NASA for F2. Assume two freely moving
point masses `m1` and `m2`, collinear line engagement, and a short event in which
external differential work/impulse and rotation can be neglected. Define the
separation speed at engagement as `u = v2 − v1` along the taut-line direction.
Momentum conservation fixes the center-of-mass velocity; both masses share it
at the instant their relative motion is arrested. The part
of kinetic energy available to remove from their relative motion is

`E_relative = ½ μ u²`, with `μ = m1 m2 / (m1 + m2)`.

For an arrest extension `s_rel`, this energy audit requires
`∫ T(x) dx = E_relative`, so its displacement-mean tension is
`T_mean,x = E_relative / s_rel` under those assumptions. For an initially
unstretched, massless, undamped **linear** spring `T = kx`, the first maximum
extension obeys `½ k x_max² = E_relative`, yielding
`T_peak = |u| sqrt(k μ)`. For that specific triangular force-extension law the
peak is twice the displacement mean over `x_max`; **two is not a general
snatch multiplier**. The undamped spring then rebounds; that instant is not
permanent arrest. Nonlinear cord, knots, stitches, preload, damping,
distributed mass and rate effects need their own behavior.

If one end is an immovable anchor, the participating inertial mass becomes the
moving mass; formally `μ → m1` as the other mass tends to infinity. This is a
different boundary condition from two free rocket sections. For two freely
falling bodies, uniform gravity cancels in their relative equation; adding
`μg` automatically to a snatch-energy result is unjustified. For a supported
vertical arrest, gravity does work and must be included consistently. Canopy
drag, ejection forces and nonuniform external accelerations can invalidate the
short-event isolated-pair approximation.

**Whole-rocket airspeed is not automatically `u`.** Nose and body may share a
large airspeed while having little relative velocity. Ejection impulse and
differential drag can also create separation speed even near apogee. A canopy
pack/body snatch pair and a nose/body snatch pair are different systems; each
needs its actual engaged masses and velocity at its own line-take-up event.
The ledger's soft-goods grouping does not prove all its mass moves as one rigid
point. The existing 2 m elastic/nylon harness remains unselected: free length
does not establish elastic arrest travel, stiffness, damping or installed peak.

## What the primary must report alongside the unchanged requirement

| Reported case | Required inputs / output | Interpretation and stop |
| --- | --- | --- |
| Preserved severe whole-mass screen | Existing nominal/adverse complete masses; 20.4 m/s, 0.3 m, DF3 once; whole and explicit downstream branch cuts | Remains required. Do not remove full growth, count the whole force again on top of its branches, or divide it equally among eyes. |
| Inflation comparison | Actual or clearly hypothetical `CdS`, air density, airspeed at filling, area history and justified/explicitly unvalidated opening-factor sensitivity | Report an assumption-bound aerodynamic comparison. Actual inflation peak remains unavailable without applicable data. Do not multiply an opening coefficient into the existing arrest force or add reference drag twice. |
| Section-snatch comparison | Exact deployment sequence; free slack; engaged mass pair; relative speed; line angles; actual force-extension-rate behavior or clearly marked stiffness/stroke sensitivities | Report relative-energy and conditional force results separately. No finite peak follows from free line length alone; missing `u`, compliance or event mass means peak is unavailable. |
| Installed force path | Separate nose/body/canopy motions, eye branches, engagement order, washer/ring/tab/tube/body loads and thermal condition | Distinct event peaks can overlap; do not add unrelated maxima automatically or take the smallest as governing. A coupled history or a justified conservative envelope is needed. Hardware and installed capacity remain separate evidence. |

Report unfactored mechanism estimates and any factored demand in separate
columns, with DF3 applied once when the primary explicitly uses the project
factor. An empirical opening coefficient represents physical model response;
it is not itself permission to remove DF3, and it must not be confused with
another safety factor. Neither the reduced-mass derivation nor NASA precedent
changes the prescribed severe requirement.

The next evidence is a selected source-identified canopy/harness and a defined
event/measurement plan: synchronized relative motion and line tension, actual
slack and force-extension behavior, packing/engagement sequence and installed
load paths. This note authorizes no physical tests. Until those inputs and
compatible capacity evidence exist, report the relevant mechanism peak and
qualification **unavailable**, preserving any failed or held required case.
