# WO-03 selected-package closure progress

Updated 2026-10-30. G80 remains the conventional reference, G54 conditional and G12
the PID-to-RL trainer. Substantial custom construction and the work-order sequence
remain unchanged. **Expanded WO-03 acceptance is open.** PR #9 is merged at
`2c7fc132c377f8bac7b9bb4f7e880ba84605c6d8`; its active vehicle is the baseline.
The studies below are explicit copies, not a newly accepted integrated vehicle.

## Correction decisions and acceptance

| Requirement / issue | Correction and criterion | Executed result | Remaining design acceptance / later physical verification |
|---|---|---|---|
| Package A fits and buckling | Retain the less-thinned Package A section and add two brace rings; DF3 hot strength/Euler, actual attachment stiffness | Exact clipped rail integration replaces the optimistic rectangular weak-axis inertia. G54 internal-bracing eigenvalue factor 3.7439 exceeds 3; last mesh change 1.46%. | Frame-only buckling is narrower than the complete bonded body path. Bond, ring, shell and joint transfer remain open. Later hot-joint/assembled proof and imperfection/modal measurements remain WO-09. |
| Brace-ring load path | Trace actual five ring/adhesive/shell solids with material inertia, force balance and hot properties | The accelerating-frame model balances force; rigid-epoxy paper peak stress exceeds the provisional DF3 screen. Favorable carbon-strip results with ideal end restraints were rejected when the shell-only transfer failed. | A finite-stiffness shoulder/load-spreading correction is being evaluated. Neither convergence nor a mean-shear hand check closes peel, crushing or the joint. [Load-path study](wo03-bonded-support.md). |
| Thermal acceptance | Configuration-specific source/ambient/foil/contact/property matrix, unchanged 45°C substrate screen, burn plus 300 s post-burn | 420 rows executed. Combined 300°C case / ε=0.9 / 35°C is **required robustness**, with worst G54 shell 48.78°C. Separate 300°C and contaminated-foil G54 corners also fail. | Required failures remain open. A 25°C controlled-ignition proposal passes its 60 calculated corners with a minimum 2.61 K G54 margin, but no operating boundary is adopted. Physical case-history, foil/contact and hot-joint measurements remain later. [Matrix](wo03-thermal-acceptance.md). |
| G12 complete recovery budget | Preserve 5 m usable guide, 10 m/s conservative departure and full 50 g allowance | Current dedicated recovery 111.034 g; maximum 119.767 g, leaving only 8.734 g incremental. The 5 m equipment assumption is **unconfirmed**. | All new anchors, reinforcement and mounting consume the budget even if classified as shared structure. New main-pack/fin trades must pass their own checks and integrated revalidation. [Budget inputs](../configs/studies/wo03-recovery-mass-budget.yaml). |
| Lightweight anchor | Direct three-leg aft load path, rounded bridge contacts, independent branches for upper parts; DF3 applied once | Wider-port G11 prototype gives positive estimated section margins but a complete G12 increment about 52.17 g. It exceeds the first prospective construction-trade headroom by about 5.62 g. | Splice cut lengths/installed strength, gas/heat protection, peel, fit and proof remain open; no industrial eye/steel boss is reinstated. [Anchor study](wo03-recovery-anchor.md). |
| Recovery mounting/service | Thin supported G11 carrier with actual controller/cell/switch/hardware; no unexplained solid collisions; credible removal paths | The three-row carrier reduces incremental mounting mass to 4.765 g, but its first run still has five real nominal intersections and removal-path failures. | These are design failures, not owner tests. Correct fasteners, component clearance and the actual service sequence before adoption. [Packaging study](wo03-recovery-packaging.md). |
| G54 stability after corrections | At least 1.0 calibre with complete package/full growth | Braced/bonded candidate with unchanged 70 mm span fails at **0.997717**. Its 75/77 mm span copies give 1.235926/1.320292 before the final recovery/joint corrections. | Recompute final mass, CG, full inertia, motor-CG sensitivity and flight performance; do not carry prototype margins forward. |
| Fin/root, flutter, retention, motion and service | Existing expanded WO-03 criteria remain active | The fin runner now derives actual minimum thickness from the part tolerance; it no longer silently uses 6.05 mm for every candidate. | Installed attachment/root stiffness, flutter applicability, axial pin retention, tolerance-expanded motion/wiring and all remaining closure-table items remain open. |

The hot material values are estimates or source-typical data, not measured
allowables. Force-balance, mesh and known-case results verify specific numerical
methods and do not establish manufactured joint strength or motor history.

## Evidence and reproduction

- [Exact fit/section study](../runs/wo03-fit-structure-20261030T221226140993Z/record.json)
  and [support FEA](../runs/wo03-support-fea-20261030T225615144070Z/record.json).
- [420-row thermal record](../runs/wo03-thermal-matrix-20261030T230041977112Z/record.json)
  with [compact per-case results](../runs/wo03-thermal-matrix-20261030T230041977112Z/case-summary.json).
- [Bounded ignition-temperature record](../runs/wo03-thermal-ignition-bound-matrix-20261030T231809584945Z/record.json)
  and [per-case results](../runs/wo03-thermal-ignition-bound-matrix-20261030T231809584945Z/case-summary.json).
- [Exact guide-limited budget](../runs/wo03-recovery-budget-20261030T230910555661Z/record.json).

`make correction-package` rebuilds candidates with the normal CAD generators,
reconciles mass, and publishes hash-checked local aliases under
`build/wo03-correction-package/latest/`. `make thermal-matrix` first rebuilds that
package, then runs the matrix. `make recovery-budget` runs the unchanged
guide-departure calculation and the explicit construction trades. Timestamped
historical records keep their original identities; mutable aliases never replace
their hashes. Large offline mesh/temperature artifacts remain local, with hashes
and compact records committed.

The final adoption must regenerate CAD and Analysis identities and re-run
structure, heat, fit, static stability and actual flight/RocketPy comparisons on
one complete package. WO-04 remains gated. Purchases, physical work, paid runs,
WO-10 owner firmware/abort review and flight release remain outside these local
numerical acceptance decisions.
