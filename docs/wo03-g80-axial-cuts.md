# G80 axial cuts: accelerating-vehicle demand and unresolved load sharing

For the selected 32.2 mm G80 candidate with the full 4.620 g incremental-annulus budget and **separate 50 g growth allowance**, the drag-free whole-vehicle axial resultant just ahead of the mount is bounded at **48.14–57.66 N**, rather than assuming the entire 117.53 N thrust is carried there. That cut crosses only the saved aft shell among the modeled structural parts. Its ideal uniformly distributed, factored axial stress is **1.404–1.681 MPa** against the existing estimated **2 MPa** paper screen. This is a conditional screen pass under the assumptions below, not a qualified joint or a result with aerodynamic drag included.

At the previously sampled **1178 mm** cut, the mount, motor, liner and fin assembly also cross the section. Under the declared uncertainty about where the equivalent propulsive force enters, the **total signed section resultant** is **−41.59 to +113.45 N**. The shell-only share cannot be derived from that interval: parallel parts can share force or carry opposing internal forces. The earlier 117.53 N shell-only check remains an intentionally strong sensitivity; neither it nor this global equilibrium proves the actual shell stress. A finite connection/load-sharing definition is still needed.

## Model and input identity

The [record](../build/wo03-g80-axial-cuts-v1/record.json) uses the exact 43-part candidate `0a1ad4c196e7bbd046704199e99bad1f6649bc237c3c07b0e4f26118d4572c4b` and the exact current 42-part baseline. Candidate loaded mass is **743.8042 g**, or **793.8042 g** with the complete 50 g allowance; baseline values are **739.4622 / 789.4622 g**. The candidate's upper annular adhesive budget represents a full nominal extra annulus, not established bond coverage. This is the loaded instant; it is not a depletion or trajectory campaign. The supplied **117.53 N** G80 source force already contains the source thrust multiplier, which is not applied again.

Every baseline part's stored STEP axial bounding extent was imported; the candidate mount uses its own saved STEP and the additional annular budget its declared tube bounds. The source center of mass of each part was checked inside its own extent. The record preserves every part's mass, interval and centroid, plus all source hashes before/after. Placeholder commercial, flexible and distributed-budget shapes remain estimates; bounds are conditional on those modeled extents and centroids representing the mass. Full 50 g growth is kept separate and may lie on either side of each cut.

For a part of mass `m` on `[a,b]` with known centroid `c`, the forward fraction at a cut `x` inside its extent is bounded using its support and first moment: lower `max(0,(x−c)/(x−a))`, upper `min(1,(b−c)/(b−x))`. Entirely forward and aft parts contribute all and none respectively. No part crossing a cut is silently concentrated at its centroid. These per-cut bounds can be loose and their independently extreme mass distributions need not describe one common manufactured vehicle across every cut.

Taking nose-forward compression as positive, a one-dimensional accelerating free body gives

```text
F_cut = m_forward * (T - D) / M + D_forward - T_forward
```

Here `D` and `D_forward` are the total and forward-body axial drag magnitudes, and `T_forward` is the equivalent forward-side propulsive force. Uniform gravitational acceleration cancels between whole-vehicle acceleration and the forward free body; this is not a claim that weight is zero. Numeric rows set **D = D_forward = 0** because the source gives no verified coincident drag magnitude or spatial partition. Drag-free values are therefore not all-flight or worst-case bounds. For an accelerating powered case with `0≤D_forward≤D≤T`, allowing an unconstrained drag partition can broaden the pre-thrust resultant up to T; it cannot establish the 2 MPa screen from the drag-free pass alone. Nonaxial aerodynamic loads, guide reactions, dynamic modes and separation are excluded.

The motor case spans approximately 1072–1200 mm; the mica pads end at 1072 mm and the plate is at 1060–1069 mm. The analysis places the **equivalent net propulsive force** anywhere in the deliberately broad **1069–1203 mm** pad-to-aft-retainer interval: zero ahead of a cut before it, full thrust ahead of a cut after it, and 0–117.53 N when the interval crosses the cut. This is a declared sensitivity to an unknown insertion location, not a source-verified thrust-pressure distribution. In particular, a cut through the propellant/motor also needs a proper momentum-flux and case-pressure representation; the equivalent-force model is not a rigorous bound on all possible internal motor loads.

## Cut results

Values below are **drag-free total section resultants**, not automatically shell forces. Signs follow the convention above. `A` is the applicable nominal shell area where known, and the 2 MPa / DF3 uniform-shell comparison is explicitly conditional on the entire listed resultant being carried uniformly by the shell.

| Cut | Geometry at cut | Forward mass bound, kg | Total signed resultant, N | Uniform shell-only screen if assumed |
| --- | --- | ---: | ---: | --- |
| 1009 mm | Unbroken shell, just ahead of mount; no other modeled part crosses | 0.32514–0.38947 | +48.14 to +57.66 | **Conditional pass**: 1.404–1.681 MPa factored vs 2 MPa; area 102.887 mm². Drag, joint, local and thermal effects remain open. |
| 1011.5 mm | Forward mount ring and unbroken shell | 0.32514–0.41457 | +48.14 to +61.38 | Entire-resultant-to-shell hypothetical **passes** on the same area; actual shell share is unresolved because mount/budget also cross. |
| 1064.5 mm | Plate web, mount and unbroken shell | 0.32604–0.47115 | +48.27 to +69.76 | Entire-resultant-to-shell hypothetical **straddles** the 68.59 N threshold; real parallel-path force is unresolved. |
| 1070.5 mm | Compression pads, mount and shell | 0.35025–0.47790 | −65.67 to +70.76 | Insertion interval crosses the cut; entire-resultant-to-shell hypothetical **straddles** the 68.59 N magnitude threshold. Real transfer and momentum treatment are unresolved. |
| 1101.5 mm | Middle ring, motor, fins and slotted shell | 0.37305–0.66233 | −62.30 to +98.06 | Entire-resultant-to-shell hypothetical **straddles** the 61.28 N magnitude threshold; shell-only force is unknown. |
| 1178 mm | Last ring, motor, fins and slotted shell | 0.51288–0.76625 | −41.59 to +113.45 | Entire-resultant-to-shell hypothetical **straddles** the 61.28 N magnitude threshold; shell-only force is unknown. |

The unbroken annular shell area is `π(33²−32.5²) = 102.887 mm²`; the slotted **91.9144 mm²** section was measured from the same saved BRep in the [mount-load-path check](wo03-g80-mount-loadpath.md). Since all listed aft cuts have parallel crossing components, a force divided by shell area is a sensitivity only. A shell force can in principle exceed the net section resultant if another path carries an opposing force; no arbitrary 0–100% split is presumed.

## Validation and decision

The independent uniform-bar check uses a 2 kg bar with 10 N applied at its aft end: at one-quarter length, the exact 0.5 kg forward portion requires **2.5 N**; the first-moment-only fraction bounds contain its exact 0.25 fraction. Focused tests cover that check, outside cuts and rejection of an impossible centroid. The saved source hashes were unchanged. The one read-only STEP-import child used **3.065 CPU seconds**, **4.189 s wall**, and **493,633,536 bytes peak RSS**. OCCT pool size one and single-worker numerical libraries were requested; no OS-affinity claim is made. Black, Ruff and two focused tests pass. No CAD was regenerated and no FEA, thermal or flight solve was run.

The first practical consequence is to carry the **whole-vehicle accelerating free body** into the next G80 joint model, instead of treating the shell as a fixed support receiving full thrust at every station. The critical remaining dependency is the actual finite plate/finger, rail/ring, adhesive, shell and forward-joint load sharing, together with a justified motor pressure/propellant momentum treatment and aerodynamic force distribution. The 1009 mm conditional screen is useful but does not close local paper tear, peel, bond capacity, installed stiffness, thermal fit, recovery, flutter or flight acceptance.

## Published evidence

The [candidate-check packet](../runs/wo03-g80-candidate-checks-20261101T053200Z/record.json) retains the exact compact records and their source hashes, including the stopped fit input attempt. Generated CAD, resolved copies and full telemetry remain local; their hashes and reproduction sources are recorded. This is evidence for the separate candidate, not adoption or complete WO-03 acceptance.
