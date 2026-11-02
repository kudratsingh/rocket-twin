# WO-03 recovery load assumptions and evidence classes

**Scope.** This note traces the existing recovery force screens and identifies which inputs are configured, ledger-derived, or physically unmeasured. It does not redefine a load case, adopt an opening-force model, or make an acceptance decision. Keep the existing **20.4 m/s, 0.3 m, DF3** case in force. Its archived844.582g full-candidate result is **1,782.253 N**; every changed complete mass must be recalculated with the same case, retaining that archived value as the study floor; do not replace it with the 0.6 m comparison or reduce the design demand to make a candidate pass.

## Source and classification table

| Input/result | Current record | Evidence class and limit |
|---|---|---|
| Velocity cases | `configs/engineering/wo03.yaml` specifies 5 m/s nominal-opening screen and 20.4 m/s archived late-G80-delay off-nominal probe. `docs/wo03-g80-recovery-path-intake.md` and `docs/wo03-recovery-correction.md` preserve the same distinction. | **Prescribed screens.** Neither is a measured parachute-opening speed. The 20.4 m/s case is not an approved motor-delay or operational limit. Separate current no-canopy flight timing probes are not deployment transients. |
| Stopping travel | The engineering config contains 0.3 m and 0.6 m constant-deceleration travel values. Existing intake tables evaluate both. The corrected branch screen and backbone trade use 0.3 m. | **Configured assumptions.** No measured line elongation, harness stroke, canopy inflation distance, or vehicle stopping travel establishes either value. The required severe screen remains 0.3 m. |
| Design factor and gravity | `design_factor: 3.0` in `configs/engineering/wo03.yaml`; gravity in the archived formula is 9.80665 m/s². | **Configured arithmetic inputs.** DF3 is applied once to the total inertia-plus-gravity load. Do not multiply the already-factored 1,782.253 N again. |
| Force equation | Intake and branch records use `F_screen = DF × m × (v²/(2s) + g)`. | **Mean energy-equivalent constant-deceleration model.** `v²/(2s)` follows from constant deceleration over an assumed travel. Adding gravity gives the idealized restraint force per unit mass while slowing a downward-moving vehicle. This is not a proven peak force, measured harness tension, or transient response. |
| Participating mass | Corrected 73-entry Stage 3 +5 g sensitivity `6b0577cef1256065f27dc79bb494a89e6c1f0c90703c9815f47c7ae7910d1dc4`, ledger record SHA-256 `940d9dd79a3e5b45bf856f280883117e0fa151b64f2c19a710f07e4e0495e317`; 73-part total 794.582 g. | **Modeled mass ledger, not a measured as-built mass.** The 5 g line/connector sensitivity is an estimated allocation, not a physical part. Full 50 g growth is separately added once and, for the branch screen, assigned aft at 1.212 m. Full loaded mass used for the whole-candidate case is 844.582 g; burnout is 782.082 g after removing only 62.5 g motor propellant. The total-mass screen assumes the whole corrected candidate participates in the same stopping event; actual branch restraint, slack, separation, and simultaneous force sharing are not measured. |
| Canopy, line, and branch mass | `docs/wo03-g80-recovery-branch-loads.md` separates 51.6 g canopy on the chute side; 25 g recovery-interface ownership uncertain; 157.466 g known forward body/payload; 457.846 g wholly-aft parts; and 69.652 g straddling/budget-unknown. | **Bookkeeping classes, not physical topology.** The 51.6 g canopy is included in the whole candidate but excluded from the known forward-body branch. The 25 g and 69.652 g ranges are alternative ownership allocations, not concurrent additive loads for a selected branch. They do not reduce the full backbone screen. |
| Nominal full-body result | At 5 m/s and 0.3 m, the corrected sensitivity gives 130.420 N loaded and 120.769 N motor-burnout. At 0.6 m: 77.634 N and 71.889 N. | **Derived screen only.** The 0.6 m row is a travel sensitivity, not a replacement case or evidence that actual cord/canopy travel is 0.6 m. |
| Severe full-body result | At 20.4 m/s and 0.3 m, the corrected sensitivity gives 1,782.253 N loaded and 1,650.364 N motor-burnout. At 0.6 m: 903.550 N and 836.687 N. | **Derived screen only.** Preserve 1,782.253 N as the existing full-loaded primary-backbone and termination screening demand. The smaller 0.6 m values cannot be used to lower it. Neither number is a measured transient or material allowable. |
| Aft branch values | At 20.4 m/s and 0.3 m, known wholly-aft mass plus full 50 g growth gives 1,071.67 N loaded / 939.78 N burnout. If both ambiguous groups are allocated aft, the separate upper bookkeeping case gives 1,271.40 N / 1,139.51 N. | **Freebody mass screens, not reduced backbone criteria or proven local loads.** They are not additive to one another or to the whole-vehicle load, and do not prove how much enters a chosen subframe. See branch table and mass allocations in `docs/wo03-g80-recovery-branch-loads.md`. |
| Canopy inflation and shock | Existing records explicitly leave opening shock/snatch, canopy inflation, distributed dynamics, asymmetry, branch stiffness, and actual force history unmodeled. The canopy area/drag and packing are preliminary hypotheses. | **Unavailable physical response.** No peak multiplier or measured peak is assigned here. DF3 does not convert the mean equation into an observed peak force. |

## Force table retained from the archived intake

These figures use the same corrected 73-part mass basis for direct comparison. Values are the recorded constant-deceleration screen after applying gravity and DF3 once.

| Speed | Assumed stopping travel | Burnout mass 782.082 g | Full loaded mass 844.582 g |
|---:|---:|---:|---:|
| 5 m/s | 0.3 m | 120.769 N | 130.420 N |
| 5 m/s | 0.6 m | 71.889 N | 77.634 N |
| 20.4 m/s | 0.3 m | 1,650.364 N | **1,782.253 N** |
| 20.4 m/s | 0.6 m | 836.687 N | 903.550 N |

The relationship is monotone in the assumed stopping travel because shortening travel raises the mean constant deceleration. This arithmetic does not establish that 0.3 m is the actual event stroke; it preserves the existing conservative screen and prevents a less severe sensitivity from displacing it.

## What the equation does and does not say

For a point-mass approximation moving downward at speed `v`, stopping over distance `s` with constant deceleration gives mean kinematic deceleration `a = v²/(2s)`. The idealized upward restraint force is then `m(a + g)`, multiplied by the project factor 3. This is an energy-equivalent average under those assumptions.

Actual recovery loading is time-dependent. Canopy inflation and line payout can create a snatch peak; elastic extension, slack, packing, reefing, canopy drag growth, canopy/line inertia, and timing of the different vehicle masses can change both the force history and which branches carry load. The present mass-times-deceleration result does not bound that peak. Conversely, the records do not supply evidence for inventing an additional opening-shock multiplier, so this audit adds none. DF3 remains exactly once on the existing screen, and physical evidence is still needed to relate it to a measured or modeled transient.

Gravity is included in the equation; it is not an extra factor to apply again. The branch figures scale assigned retained mass with the same acceleration for freebody context. They do not establish equal load sharing, force simultaneity, or branch stiffness. The entire primary backbone/termination demand remains1,782.253N for the archived844.582g full-loaded probe. For a changed candidate, recompute it from complete loaded mass plus the separate50g allowance using the same speed, travel and DF3. Retaining the load case does not mean freezing its force while increasing mass.

## Provenance and missing measurements

The principal source records are [recovery path intake](wo03-g80-recovery-path-intake.md), [corrected branch loads](wo03-g80-recovery-branch-loads.md), [recovery backbone trade](wo03-g80-recovery-backbone-trade.md), and [recovery correction study](wo03-recovery-correction.md). The engineering config hash recorded with the 73-part branch ledger is `f5bb3c0fdb6abf4adf8628c76316302192ad779343a3a8188e01f2928c5a1678`. The branch ledger records the corrected 6b identity and separate 50 g growth placement. The corrected metadata copy is SHA-256 `8dfac23cf7fb41d7a24736b264fcc6203896e0cf6526bcee33a2f71165c0e231`; Stage 3 sensitivity input arrays are SHA-256 `6962dda2e123ac3528f75136f62b065d742e917712fc2dcef2dfc0a40a675967`. These preserve provenance; none turns a model mass or case assumption into measured physical evidence.

Evidence that would resolve the model-to-event gap is:

- actual as-built loaded/burnout mass and mass ownership for the canopy, cord, protection, connectors, nose, payload, aft assembly, and growth allowance;
- the real recovery deployment speed basis for the chosen G80 configuration, including trigger, motor-delay/charge behavior, and measured or validated canopy inflation timeline;
- canopy opening force history and line tension/extension over time for the actual canopy, packing, deployment, and representative atmospheric condition;
- measured effective harness payout/stopping travel, slack, termination stiffness, and load distribution into body, nose, payload, fins, motor, and aft attachment;
- instrumented representative ground or flight measurements that distinguish peak tension from average stopping load, with synchronized speed, inflation, and line-extension data;
- proof and environmental evidence for the actual cord, sewn/knotted terminations, connectors, anchors, and attached structures at the resulting load history.

Until that evidence exists, the 5 m/s case remains the nominal prescribed screen and 20.4 m/s at 0.3 m remains the required severe prescribed screen. Neither one establishes actual opening loads, a safe delay, qualified hardware, or acceptance.
