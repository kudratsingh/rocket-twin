# G80 package closure — isolated integrated candidate, acceptance open

The latest isolated candidate is the **72-part retention/recovery integration**,
identity `90b2a9ad780fc81d11171363432c46088531817ddb6570fe9f800429bde2bdfc`,
at its real staged CAD revision. It has not replaced the active 42-part design
or preview. The frozen 52-part studies below retain their own identities and
must not supply strength, fit or recovery acceptance for changed parts.

| Issue / previous finding | Implemented in the isolated 72-part candidate | Criterion / new result | Evidence | Remaining design and physical verification |
| --- | --- | --- | --- | --- |
| Keeper/bridge absent from complete vehicle mass | Separate modified mount, guides, keeper, bridge and itemized M3/M2 hardware; remove old 7 g lump once, retain distinct 1 g estimated locking/materials reserve | Loaded 772.982 g; full 50 g allowance gives 822.982 g. Full tensor and lateral/axial CG reconciled; 21 affected physical solids match pinned source STEP | [Integrated staged report](wo03-g80-staged-retention-results.md), compact source/mass ledger | Supplier tolerances, actual locking method, glue/grade/properties and measured masses; reserve is not selected locking hardware. |
| New mass invalidated old static and ascent predictions | Run same resolved candidate through static model, JAX and RocketPy | Growth loaded/burnout margin 1.1663/1.5483 cal ≥1; growth CG 829.167 mm. Nominal apogee 620.610 m vs RocketPy 620.650 m; apogee/time errors 0.00650%/0.01711% <5% | [Four-case results](wo03-g80-staged-retention-results.md) | Exact motor CG/source and as-built aerodynamics. Exploratory +12.8 mm motor-CG shift still gives 1.1360 cal; this is not a measured tolerance. |
| Changed-package guide and full descent unavailable | Four finite 180 s flights, including full-growth low/high thrust and 3 m/s east wind | Guide speeds 18.772/16.848/19.700/18.770 m/s ≥15 on assumed 1.5 m guide; all reach modeled ground. Total ground speeds 6.071/6.281/6.279/6.731 m/s exceed separate impact diagnostic | [Saved flight/landing evidence](wo03-g80-staged-retention-results.md) | Existing 6 m/s vertical-descent target remains distinct from total speed. Canopy sizing/drag, opening, packing/extraction, anchor and local site/guide remain open; modeled descent/wind not independently validated. |
| Actual bridge load sharing not trustworthy | Preserve completed 3D result and bounded known-case diagnostics separately | Mesh/input guards pass but actual reaction balance fails by 104.697/22.093 N; no installed strength/stiffness credit | [Bridge failure](wo03-g80-final-coarse-diagnostic.md), [known cases](wo03-ccx-reaction-fixture.md) | Numerical cause unresolved, actual hot joint/bearing/peel and reverse retention acceptance open; later proof tests do not replace these design requirements. |
| Installed fin/root/flutter and thermal design unclosed | Preserve exact geometry/source identities and failed/unavailable states | No new installed-root/flutter or thermal pass; Elmer implementation switching does not resolve exact-field failures | [Fin intake](wo03-g80-installed-fin-intake.md), [thermal decision](wo03-elmer-campaign-decision.md) | Applicable installed analysis, qualified heat method/useful bounds, unchanged required cases/45°C screen, and owner coupon/hot-load/modal/temperature measurements. |
| Recovery packaging had excluded positive overlaps | Retain the complete package rather than silently deleting contact-envelope conflicts | Three earlier overlaps remain unresolved; supplier canopy/switch updates are studies only | [Integration report](wo03-g80-staged-retention-results.md) | Actual hardware envelopes, load path, arming/tool access, routing/strain relief and extraction must close before adoption. |

## Subsequent canopy screening, not adopted

The [five-case canopy study](wo03-g80-canopy-stage3-results.md) replaces the
35 g placeholder once with the supplier-listed 51.6 g Apogee 29095. It retains
the full 50 g allowance and separately evaluates another estimated 5 g of
line/connector allocation. Full-growth mass is 839.582 g, or 844.582 g with
that allocation; growth loaded margins are 1.361/1.419 calibres. Nominal
modeled apogee is 613.213 m. The 0.75 drag coefficient and old packed envelope
are explicitly unverified inputs, not supplier performance or packing evidence.

| Issue | Correction or disposition | Criterion / result | Evidence / remaining verification |
| --- | --- | --- | --- |
| Previous canopy misses vertical descent target in three cases | Screen larger supplier canopy and illustrative 20% lower drag-area sensitivity | All five sampled vertical speeds 5.049–5.849 m/s ≤6; all guide speeds ≥16.366 m/s vs15 | [Same-package results](wo03-g80-canopy-stage3-results.md); drag-area range is not a validated uncertainty bound. Actual drag, mass inclusion, packing/extraction and opening loads remain open. |
| Horizontal wind adds impact energy | Keep vertical target separate from total ground-speed diagnostic | Windy total speeds 6.027/6.553 m/s exceed6 while vertical speeds pass | No criterion is silently changed. Site wind, drift/landing loads and recovery dynamics remain unvalidated. |
| Extra 5 g part lacks build/cost metadata | Preserve failed as-run check, create explicitly unpriced metadata-only copy | All20 shared simulator-input arrays bitwise equal in four sensitivity cases, plus mass/CG/full-tensor equality | This is scoped input equivalence, not a rerun or retroactive claim that the original build/cost check passed; actual supplier cost and hardware remain unresolved. |
| Recovery force could pull the long body apart | Trace complete path and evaluate a plain upper-tube cut | Current off-nominal load cases exceed the estimated paper strength screen; a local spreader cannot bypass the serial tube cut | [Load-path intake](wo03-g80-recovery-path-intake.md), [axial screen](wo03-g80-recovery-axial-screen.md). Cord endpoints, continuous load path, nose/aft retention and component restraint need a correction, followed by analysis and owner proof/deployment tests. |
| Stage3 full trajectories not retained | Preserve metrics and source inputs; report coverage honestly | Last-prelanding samples available, complete trajectory replay and guide-row audit unavailable | No automatic repeat to fill missing output. Earlier Stage2 telemetry belongs to its different candidate. Future execution must retain required outputs. |

## Historical frozen 52-part proposal

The earlier selected mount and recovery packaging formed **one 52-part proposal**,
identity `62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009`.
It is available as separate STEP/GLB and normally validated specifications.
It has not replaced the working vehicle or frontend assets. G54 upgrade and
G12 PID/RL remain committed with their independent requirements and findings.

| Item / previous finding | Correction or disposition | Criterion / latest result | Evidence | Remaining verification |
| --- | --- | --- | --- | --- |
| Mount radial stack: 0.02093 mm, below 0.1 mm | Selected 32.2 mm mount, preserved channels and conservative extra adhesive budget | Cold 0.150 mm; in-domain 0.12102 mm, conditional pass. Out-of-domain hot sensitivity fails. | [Fit study](wo03-g80-fit-candidate.md); identical affected mount/shell geometry in integrated copy | Actual component temperatures/CTE, purchased motor dimensions, eccentricity and as-built fit. This does not close every interface. |
| Separate mass prototypes | Recovery packaging and mount combined, all 52 part masses counted | 748.569 g loaded + separate 50 g; growth CG 818.503 mm, margin 1.3278 cal ≥1 | [Reconciliation](wo03-g80-integrated-candidate.md) | Exact hardware, glue coverage, connectors/finish and measured properties; allowance is retained, not consumed silently. |
| Affected static/flight results absent | Run exact combined proposal through shared mass/JAX and RocketPy | Preliminary static reference passes; nominal apogee/time errors <0.01%, below 5%; conservative guide 16.955 m/s ≥15 | [Flight](wo03-g80-integrated-flight.md) and separate static-reference record | Unconfirmed actual guide/site, motor/mass/aero uncertainty and other winds; 45 s recovery incomplete. These are preliminary modeled checks. |
| Full-circle aft-ring bond proxy | Actual slotted surface measured | 541.114 vs former 606.956 mm²; corrected geometry, capacity/load sharing still open | [Load path](wo03-g80-mount-loadpath.md) | Finite wet bond, ring/rail/body stiffness, peel, bearing, reverse retention and hot properties. No full-joint pass. |
| Full thrust assigned to shell without acceleration balance | Accelerating cut equation and time-aligned modeled drag bounds | Earlier 43-part case forward shell-only sampled DF3 upper stress ≤1.643 MPa vs estimated 2 MPa; not transferred as a 52-part structural pass | [Cut analysis](wo03-g80-axial-cuts.md), [saved-flight bound](wo03-g80-axial-flight-bounds.md) | Repeat affected bound for complete candidate, local concentrations/buckling, actual connections, wind and material evidence. Aft parallel shell/motor/mount resultants remain unresolved. |
| Fused plywood mount hides manufactured joints | Select one G11 aft bridge / rail-tab and through-bolt capture proposal for bounded geometry checking; do not credit block-butt tensile glue | Proposed, **not implemented in the 52-part CAD**. Existing 20 mm screws do not span the proposed ≥30.9 mm stack; hardware/keeper mass remains unavailable | [Fabrication and retention definition](wo03-g80-mount-fabrication.md) | Explicit discrete joints, nut/washer ring relief, fastener engagement/access, bridge bending/tab bond, material directions, loads and full mass reconciliation. |
| Recovery packaging had no consistent combined CAD | Reconstruct existing carrier/cell/switch package under current CAD, with separate power topology | Nine volume-derived masses reconciled; no unexplained changed-interface overlaps, but three excluded positive overlaps remain **unresolved interface evidence** | [CAD package](wo03-g80-integrated-candidate.md) | Exact switch/body/doubler, fasteners, connectors, pressure ports, routing, packing/extraction, arming and tool access. Named exclusion is not fit approval. |
| Recovery anchor and opening path unqualified | Preserve required nominal/off-nominal load cases and reject industrial lifting hardware | Still open: harness → supporting structure → all retained components and tube/joints | [Recovery integration](wo03-recovery-integration.md), [G80 intake](wo03-g80-package-intake.md) | Actual load sharing, tear/bearing/bending/bond capacity and positive retention; later owner proof/deployment/electrical tests cannot substitute for unresolved design calculations. |
| SWA1 exact DC duty unavailable | Select DC-rated C&K T102SHZQE for the next mounting study only | Official silver-contact family rating supports the 1 A screening assumption; not in frozen 52-part CAD and not a qualified output circuit | [Hardware note](wo03-g80-recovery-hardware.md) | Panel/terminal/retention geometry, accidental actuation, exact mass and manufacturer-supported load/battery bench verification. |
| Isolated fin panel evidence treated as installed | Retain panel results with their scope | Installed attachment stiffness, strength and flutter remain open | [Original correction record](wo03-correction-closure.md) | Same-package finite tab/foot/frame/body loads, hot directional properties, applicable FEA convergence and installed dynamics. No G12 root evidence is borrowed. |
| Failed thermal operator and unqualified actual baffle | Close bounded existing-tool comparison, preserve failures | Elmer runs; A exact-field checks fail, general conservation/refinement and actual geometry unqualified. No thermal pass | [Closed decision](wo03-elmer-campaign-decision.md) | Applicable qualified method or useful conservative bounds, required matrix including 300°C/dirty foil/35°C, unchanged 45°C substrate screen, local/mean temperatures and soak. |

The next design correction must resolve an actual interface/load path on this
package and retain its mass consequences. Physical coupon, bond/hot-load,
mechanism, packing/deployment, electrical independence and integrated proof
measurements remain in WO-09–11. Purchases, physical work, paid runs, WO-10
owner review and flight release retain their gates. No G80 preliminary pass
completes WO-03 or closes G54/G12.

Published [same-package evidence](../runs/wo03-g80-integrated-package-20261101T053840103311Z/record.json) retains exact CAD/mass/static/flight compact records and their hashes. Generated geometry and full telemetry remain local. The 52-part identity is a proposal; working vehicle and release status remain unchanged.

## Subsequent retention geometry (not part of the frozen 52-part proposal)

[Two recorded geometry attempts](wo03-g80-retention-geometry.md) preserve the
initial 9 mm washer/ring conflict and a single input correction. The corrected
nominal screen has no positive-volume screened overlaps and has 54.538 mm²
washer/bridge probes, but washer OD tolerance, keeper/capture, rail-tab load
transfer and assembly remain open. Radial removal hits the installed shell;
[the keeper plan](wo03-g80-captive-retention-plan.md) distinguishes
pre-shell nut installation from routine aft cap/motor service. Its new G11 ring,
closure hardware, mass and thermal/structural effects still require evaluation.
No result is transferred to the active design or treated as a retention pass.

## Subsequent source-identical service and accounting

The [keeper service continuation](wo03-g80-keeper-service.md) now completes
nominal sampled pre-shell insertion, aft cap removal and motor removal. This
supersedes only the earlier unavailable service result, not tolerance, torque,
strength or full-path access conclusions. The [mass audit](wo03-g80-retention-mass-audit.md)
keeps all removed/replacement solids and the ambiguous old hardware lump
separate; no complete revised mass/CG/inertia or flight result is claimed.
The [bridge FEA record](wo03-g80-bridge-fea.md) preserves the coarse load-moment
stop before CCX. Structural acceptance remains open; known fixtures and a
geometry-only reconstruction do not establish installed strength.

## Frozen-package recovery horizon follow-up

The [180 s follow-up](wo03-g80-recovery-horizon.md) closes only the three
45 s trajectories' unavailable landing outputs: all now reach modeled ground.
The growth cases predict approximately 6.18 m/s against the preliminary 6 m/s
descent screen, leaving a recovery sizing/allowable-impact decision open.
This does not validate actual deployment, independent hardware, opening loads,
installed anchor strength or the later unintegrated keeper/bridge design.

## Actual bridge input gates pass; output validation fails

The [latest component campaign](wo03-g80-final-coarse-diagnostic.md) now fits
the unchanged mesh/resource/area guards and completes the two CCX load steps.
Its reaction imbalance fails decisively, so all raw displacement/stress/work
remains unvalidated; component and full-vehicle strength acceptance stay open.
The full3D route is stopped for this packet. A smaller known-case output
verification is required before any further numerical reliance; no criterion
or physical requirement is relaxed and no new vehicle geometry is adopted.

## Structural input/output path narrowed

The [structural solver decision](wo03-structural-solver-decision.md) closes the
specific small Elmer input/Float64-output/reaction verification obstacle for two
known load cases. It does not close the actual bridge's reaction or reciprocal-work
failure. CalculiX B1 precision remains insufficient and B2 displacement fails.
A bounded bridge input study is next; installed strength, hot load paths,
mesh convergence, fin/root/flutter and thermal acceptance remain open.
