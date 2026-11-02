# WO-03 closure plan — fixed scope, bounded attempts

Owner direction, 2026-10-31. This plan changes neither expanded WO-03 acceptance
nor the active vehicle. G80 remains the reference, G54 conditional and G12 the
PID-to-RL trainer. The original frontend/browser pause was superseded by the
owner's limited preview resumption; its scope and verification are recorded in
`docs/STATUS.md`. Physical, paid-run, WO-10 owner-review and flight-release gates
remain.

Computing budgets below are **CPU execution allowances, not delivery dates**.
No paid compute is authorized. Known-case agreement, actual numerical accuracy,
design acceptance and owner qualification remain separate.

**Current C1 attachment checkpoint (2026-11-02):**
[C1 source identity](wo03-c1-attachment-source-lock.md) is frozen at1079.807g
nominal + separate50g =1129.807g. The one [R1 installed-fin reinforcement
preflight](wo03-c1-fin-attachment.md) is stopped before CAD/native analysis:
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

Next packet is a construction preflight only; no automatic second R1/native
trial or thermal-method restart is admitted by the failed result. Existing
known-case, installed/refinement and physical-test gates remain distinct.

## Current three deliverables — 2026-11-01

The original thermal campaign below is historical and closed as unqualified;
its failed/stopped records and required acceptance cases remain in force.
Current delivery priority follows ADR-0011, without changing WO-03 completion.

| Concrete deliverable | Pass/fail criterion | Computing effort and stop decision |
| --- | --- | --- |
| G80 positive retention correction after coarse diagnostics | Known-case and actual coarse force/reciprocity checks now pass; the current bond-only path remains adverse under provisional hot screens. Compare source-pinned rail-aligned capture versus a continuous G11 frame with complete load paths, fit and exact-once mass; no adoption without applicable strength/convergence/thermal/recovery evidence. | Input preparation only until primary admission. Proposed actual diagnostic: two serial120 CPU/120 wall-second cases,60 CPU setup+120 parent reserve=420 CPU seconds; one CPU requested,2 GiB per root process. Stop first invalid mapping, numerical failure or cap; diagnose once from saved data before a new declared attempt. No automatic backend switching or rerun. |
| Complete recovery backbone/attachments and installed fin load paths | Same candidate geometry; branches positively retain nose, payload and aft mass. Show finite joints, heat/contact assumptions, packing/extraction/service and itemized mass; retain existing recovery loads, design factors,1 mm fin-tip motion and flutter/convergence criteria. A straight tether route or isolated fin panel is insufficient. | Start with source/CAD hand calculations and one bounded layout. Any native targeted analysis requires its own declared≤10 CPU-minute packet,≤120 seconds per child and applicable known-case checks. If a joint, route or mass trade fails, preserve it and choose one correction addressing the actual failure; do not claim later proof tests close a current design failure. |
| Integrated G80 closure and usable preview handoff | One identity for all adopted parts/mass/CG/full inertia and applicable static/flight/engineering evidence; full50 g growth. Preview preserves active designs and labels the separate72-part snapshot, incompatible analysis and unsupported simulation honestly. Thermal remains open until a justified applicable method/bound passes required cases and45 °C screen. | Reuse current valid records. Run affected checks after an integrated change, not every documentation edit. Existing simulator comparison effort is separately recorded; no new thermal compute is admitted here. Stop acceptance at any design failure or missing compatible result. Host restart/browser check is distinct from automated API/build checks. |

See the [structural decision](wo03-structural-solver-decision.md),
[G80 closure table](wo03-g80-current-closure.md) and
[decision-driving inputs](wo03-g80-decision-inputs.md).

## Historical thermal-first deliverables

| Next deliverable | Pass/fail criterion | Computing budget | Decision on failure |
| --- | --- | --- | --- |
| 1. Error-isolation packet | Test the actual 935:1 long-gap aspect ratio with independently known steady conduction/finite-wall answers, mixed prescribed boundaries and spatially varying manufactured wall inputs. Check local extrema, reservoir heat and global/local balances at three refinements. Retain existing analytic-case tolerances; approximate cases must show decreasing error and meet the existing method convergence criterion. Identify which mechanisms the tests isolate and which remain unproved. | One CPU; ≤120 s per case; ≤10 CPU min total. Existing captured-field diagnosis and stable-ledger proof are inputs, not repeated full factors. | At most two corrective trials for one identified defect. If either trial repeats the same unexplained failure, stop that implementation family, preserve it and state a different mathematical/geometry treatment to test. A passing simple case cannot qualify the actual baffle. |
| 2. Actual-baffle thermal credibility packet | Exact candidate/material/opening/contact identity; valid mesh or justified reduced/bounded representation; admissible local temperatures; unchanged field/heat tolerances; important substrate/bond peaks and heat routes stable under spatial and temporal refinement. Apply the unchanged required-case matrix, including300°C/contaminated foil/35°C and45°C substrate screen. Part means and local coverage stay distinct. | Preflight first. Detailed route: ≤300 s per mesh, ≤900 s per complete factor, declared existing node/map/memory guards; no automatic increase. Permit one new actual trial only after deliverable1 and a feasible resource/geometry preflight. Alternative assessment: ≤10 CPU min of fixtures/counts before a detailed alternative run is proposed. | Current invalid/capped attempts already trigger replanning: no blind retry of the original PLC/native/midpoint constructions. Any repeated invalid cell/connectivity defect or cap stops that approach. Assess an alternative retaining actual openings/material paths, with validated accuracy or conservative conductance/radiation/temperature bounds. Bounds must cover property/contact/source uncertainty; if they straddle45°C, acceptance stays open. A trivial ambient-to-case bound is insufficient to choose the design. |
| 3. One complete-package closure report | Recovery/support and installed fin/root evidence belongs to the same resolved package as the thermal result. Count every part once; reconcile mass, CG and full inertia; pass applicable strength/stiffness/flutter/fit/motion, G54≥1 calibre with growth and G12≥10 m/s on the still-unconfirmed5 m guide with full50 g allowance; repeat affected JAX/RocketPy checks. Issue→correction→criterion→result→evidence→physical-verification table. | Existing regression campaign approximately20–40 CPU min, excluding separately declared targeted analyses. Independent structural audits: ≤120 s per child, ≤10 CPU min each; FEA retains existing known-case/convergence requirements. | Any design failure leaves the package unaccepted. Select a correction addressing the limiting load/heat/mass path; do not compose passes from incompatible prototypes, reduce the growth allowance, relax the departure screen or defer a design failure as a physical-test-only item. |

## G80-first execution priority (ADR-0011)

The declared external-tool campaign is closed with a scoped decision in
[wo03-elmer-campaign-decision.md](wo03-elmer-campaign-decision.md); do not restart
stopped custom methods or automatically add new verification packets. The first
complete mechanical/thermal/recovery package is now G80. Follow the dependency
order in [G80 intake](wo03-g80-package-intake.md): exact current fit and one
correction → actual joints/retention/installed fins and recovery → qualified heat
and same-candidate mass/CG/full-inertia/stability/guide/flight revalidation. Keep
all 50 g growth allowance. G54 and G12 remain independent committed tracks.
This priority does not change the completion thresholds or full work-order
sequence. The saved preview is delivered under its existing early exception.

## Inputs that could change decisions

- Exact motor external case-temperature histories, including ends and post-burn
  cooling, determine source heat exposure. Certification/thrust data does not
  supply these temperatures. Instrumented manufacturer information or later
  owner measurements would resolve them; current explicit bounds stay required.
- Foil emissivity/contamination and actual seams/openings can change radiation
  reaching rings and substrates. Preserve degraded-foil cases; measured surface
  condition/emissivity or calibrated hot-soak data is needed before narrowing them.
- Adhesive coverage, thickness, conductivity/contact quality and hot shear/peel
  affect both heat transfer and structural load paths. Sectioned coupons,
  temperature-dependent bond tests and assembled hot proof tests are needed.
- Minimum-direction plywood/carbon-sandwich properties, installed root stiffness,
  damping and body/joint capacity can control fin strength/flutter and recovery.
  Use source ranges until owner coupon, torsion/modal, joint and recovery tests
  establish as-built values. No supplier-typical value becomes a measured allowable.
- Motor mass/CG/envelope and actual guide length remain configuration-specific
  inputs. Supplier drawings and measured hardware/guide dimensions resolve them;
  the G54 motor-CG sensitivity and G12 departure budget remain visible.

Parallel audits must rank these by whether their credible interval crosses an
acceptance boundary. Input uncertainty is not resolved by numerical convergence.
Gas refinement also cannot conceal unresolved wall quadrature, local radiation
sampling or mean-temperature/fourth-power projection error. Those existing
common-surface checks remain part of the actual thermal credibility packet.
Report closed engineering subitems and complete-package results first; software
test counts support implementation verification only.


## Executed checkpoints

- Known-answer packet is complete: exact affine935:1 case passes; curved cases
  reveal local undershoots despite energy closure and coarse map convergence.
  These diagnostics do not qualify the actual solver. [Evidence](wo03-thermal-error-isolation.md).
- Both permitted fixture correction trials have been used and rejected as
  standalone treatments. Trial1 loses source accuracy; trial2 preserves source
  heat but has excessive temperature/reference-heat error. This branch is
  stopped; no third tweak or actual-geometry run follows. [Decision](wo03-thermal-method-decision.md).
- Support/recovery and installed-fin audits close exact geometry/force accounting
  and common-root equilibrium subitems. Actual joint capacities, foundation,
  flutter and the guide-compatible complete thermal/recovery package stay open.
  [Closure table](wo03-package-closure-progress.md).
