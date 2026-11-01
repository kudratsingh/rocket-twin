# G80 package closure — current proposal, acceptance open

The selected mount and recovery packaging now form **one 52-part proposal**,
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
[this unexecuted keeper plan](wo03-g80-captive-retention-plan.md) distinguishes
pre-shell nut installation from routine aft cap/motor service. Its new G11 ring,
closure hardware, mass and thermal/structural effects still require evaluation.
No result is transferred to the active design or treated as a retention pass.
