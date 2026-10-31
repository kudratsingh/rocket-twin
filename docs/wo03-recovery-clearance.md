# WO-03 recovery cap clearance with original outward horns

**The new cap/window/hoop geometry clears the sampled mechanism while preserving the original actuation.** All 25 combined poses have no reported positive-volume intersection among the changed parts and the modeled rigid vehicle, before any endpoint-zone exclusions. Actual minimum rod/frame separation is **0.954 mm**, against the stated **0.893 mm** dimensional-plus-reserve bound. The copied frame is one valid connected solid, and its front 8 mm cap is unchanged by the rear-hoop correction.

**Whole-path engineering acceptance remains open.** The hoop repairs the thin-rim failure under an optimistic equal-two-route shear proxy; a one-route bound still fails. Annular bending, torsion, actual reaction sharing and manufactured laminate continuity remain unqualified. The three longitudinal rails still fail matched/single-leg recovery demand. The complete 8 g thermal mass sensitivity meets the guide screen only if the unadopted 2.111 g rail saving is credited.

## Scope, source identity and reproduction

Only the new clearance script, study YAML and this document change. The seven earlier owned recovery files remain unchanged, as verified by hashes around both executions. The original outward 6 mm horns, rods, actual shaft positions/axes, gimbal attachment points, motion limits and configured actuator ratio **0.16** are preserved. Neither the thrust stop nor the cassette, motor or liner is relieved.

The primary agent found that the previous canted-horn model inferred shaft Z from rod-tip Z. Consequently, those canted results cannot be treated as actual fixed-shaft physical clearances. This study uses the corrected source, which reads the real horn shaft and validates rod-tip matching. The recorded `src/cad/kinematics.py` SHA-256 is `c26c5587048c448dab2635d607fdbe75f3f8f7d3d8e144481ec90c6ca0758ade`. The original flat mechanism remains unchanged by that correction.

```sh
.venv/bin/python scripts/wo03_recovery_clearance.py --preset tiny
```

This defaults to the separate `build/wo03-recovery-clearance/hoop/` output. The final run is **`wo03-recovery-clearance-20261031T023059417207Z`**, **46.83 s CPU, $0**, with `inputs_unchanged=true` and `frozen_owned_files_unchanged=true`. Its resolved copy reloads through the schema; its STEP, source hashes, motion/section reports and full mass/guide hypotheses are identified in [`record.json`](../build/wo03-recovery-clearance/hoop/record.json).

Self-checks verify current source identities, frozen files, schema/mass reconciliation, all 25 reported poses, preserved open failure states and a valid one-solid STEP after reimport. STEP roundtrip mass differs by **0.123 mg / 0.000273%**, below the work order's 10% CAD/spec mass reconciliation threshold. Ruff and Black checks pass. These checks do not qualify the material or load path.

The executed thin-rim failure is preserved separately at [`build/wo03-recovery-clearance/record.json`](../build/wo03-recovery-clearance/record.json), run **`wo03-recovery-clearance-20261031T022104167187Z`**, 69.26 s CPU. Its record SHA-256 is `b61ac097255a538f3131d3a76cd63c16a19b8c0f5d4ff62dbb41ffd714844ecb`; its STEP, copied specification and exact script/config snapshots remain under that directory. The final trial verifies that the thin reference's CAD/vehicle source identities are unchanged before reusing its front-window derivation.

## Derived windows and preserved ports

The full cap remains at **1.012–1.020 m**, with nominal thickness 8 mm, minimum thickness 7.7 mm and radii 24–32 mm. Its three paired ports and rounded saddles rotate to **60°, 180° and 300°**, between the rails. Each local pair retains `(28, ±5) mm`, Ø3.7 mm nominal ports, the 10 mm nominal pitch and the original 3 mm-radius, 6 mm-long saddle.

The script constructs the actual rod/horn shapes at the full 5 × 5 pitch/yaw grid. Conservative capped mechanism envelopes include the existing linear dimensional bounds, a 0.05 mm hole-radius allowance and a 0.15 mm positive reserve. For the larger rod bound this is:

`sqrt(3) × (0.15 mm frame + 0.25 mm rod) + 0.05 mm + 0.15 mm = 0.89282 mm`.

This treats each stated linear bound as an independent Cartesian-coordinate bound. It is an explicit geometric study assumption, not demonstrated production capability. The envelope uses that larger rod bound for both mechanisms, projects only the portion that could enter cap material, includes 0.03 mm projection reserve and rounds the diameter upward in 0.1 mm increments.

| Mechanism sector | Axial cylinder centers | Derived diameter |
|---|---|---:|
| First rod/horn | R26 mm at 0°, 8° and 16° | **7.9 mm** each |
| Second rod/horn | R26.2 mm at 90° | **7.5 mm** |

The example 6.4 mm holes were insufficient for these declared bounds. All window cylinders stop exactly at the back of the **front 8 mm cap**. They do not extend into the added hoop. They are native, spec-owned `machining_holes` in the copied frame parameters. The rounded saddle cylinders are recorded post-Boolean additions owned by this script; generic `local_shape` alone does not reproduce those additions.

The windows remove **1.79852 g** at the estimated 1,850 kg/m³ G11 density. They remove **zero volume** from all three protected local port/saddle strips. The existing minimum flat pair ligament remains **6.000 mm**, compared with the prior assumed `2 × 2.9 mm = 5.8 mm` cord-contact relation. The conservative nearest port/window ligament is **3.561 mm**. The port outer-edge ligament is 1.657 mm nominal, or 1.295 mm under the separate independent-feature dimensional bound; that edge geometry is not itself a qualified tear-out or laminate criterion.

With the new whole aft demand of 1,031.96 N already including DF3, the retained local proxies are **18.614 MPa** port bearing, **11.168 MPa** pair-web shear and **44.383 MPa** local unsupported bridge bending. They remain below the previous estimated 25/25/80 MPa screens. These are local comparisons, not installed rope/contact ratings or whole-cap strength.

## Preserved thin-rim failure and one rear-hoop correction

The thin windowed cap was one valid connected solid and cleared all sampled geometry. Its continuous outer rim was only **2.05 mm nominal / 1.70 mm dimensionally bounded minimum**. Even an equal split into two circumferential routes gave **39.17 MPa** against the existing 25 MPa estimate. That proxy required **2.664 mm** minimum rim, a **0.964 mm** deficit. The thin-rim structural finding is retained.

The single bounded correction adds a native per-ring G11 annulus at **1.020–1.025 m**, **Ri29.8 / Ro32 mm**, 5 mm nominal axial thickness, 4.7 mm minimum. The 25-pose conservative mechanism envelope behind the cap reaches R29.308 mm and requires a rounded-up R29.4 mm opening; selecting Ri29.8 leaves additional radial space. Its front-cap symmetric-difference volume against the thin trial is **zero**.

The ring is continuous with the frame BRep. It assumes an eventual continuous machined G11 stock route; there is no newly invented bond or ideal interface spring. One connected CAD solid does not establish stock availability, a fabrication route, favorable laminate directions or interlaminar strength. Port bores remain open through their overlapping portion of the rear hoop, and that material removal is charged. The link windows remain limited to the front cap.

Actual radial BRep sections are recorded through every window center, port-hole center and saddle group. The minimum sampled critical net section is **27.400 mm²**, with approximately **388.56 mm⁴** radial-axis bending inertia and **58.788 mm³** section modulus at the weakest nominal window sections. No global bending-moment demand or bending margin is invented from those section properties.

The conservative dimensionally bounded section combines:

- Front rim: `1.70 × 7.7 = 13.09 mm²`.
- Rear hoop: `1.90 × 4.7 = 8.93 mm²`.
- Combined window-region minimum: **22.02 mm²**. The port-region bound is larger, **36.116 mm²**.

At least 1.70 mm of shared radial material remains across the cap/hoop face under these dimensional bounds. The intended path is port/saddle → intact front web → continuous outer rim/rear hoop → existing three rails. Its actual load split, annular bending/torsion, transition stresses and material directions still require a connected structural model.

| Circumferential load assignment | Estimated net-section stress | Comparison with 25 MPa estimate |
|---|---:|---|
| Two routes share the single-leg demand equally | **23.432 MPa** | Passes this proxy |
| One route carries that demand | **46.865 MPa** | Fails |

The required area is 20.639 mm² per equally loaded route, or 41.278 mm² for one route. Geometry and net area do not demonstrate the equal split. The hoop therefore corrects the earlier optimistic net-section deficit without closing whole-cap engineering acceptance.

## Actual motion and dimensional clearance

All pairs containing the changed frame, junction, rods or horns are checked against every modeled rigid part through the nested motor/gimbal transforms. Raw reported intersections are retained separately from the existing 4 mm rod-end neighborhood policy. There are **no reported raw or nonjoint intersections** across all 25 poses at the existing 0.05 mm³ reporting threshold; no joint-zone exclusion was needed to obtain that result.

| Pair | Minimum actual BRep separation |
|---|---:|
| Rod / cap-frame | **0.954 mm** |
| Horn / cap-frame | **1.401 mm** |
| Rod / cassette | **1.756 mm** |
| Rod / motor | **2.618 mm** |
| Rod / coupler | **38.356 mm** |
| Rod / horn, including the mating neighborhoods | **0 mm** |

The rod/frame margin above the stated 0.89282 mm bound is **0.06073 mm**. The horn/frame separation exceeds its smaller 0.71962 mm bound. This is a finite-grid geometric result with an explicit dimensional sensitivity. It does not prove continuous motion, angular/axis/joint tolerances, hardware fit, flexible wiring or packing/service clearance. Zero separation at the articulated mating geometry is not joint qualification.

The maximum required servo angle is **18.672°**. The minimum sampled kinematic rate ratio is **0.24225**, above the unchanged configured 0.16. Actual horn length stays 6 mm to within `1.7 × 10⁻¹⁴ mm` numerical error, and the original phases/shaft axes and both original rod definitions are retained. Servo torque, speed under load, backlash, spline engagement and control authority remain later requirements.

## Full mass and unchanged guide hypotheses

The gross added hoop annulus is **3.951 g**. Its net increment over the thin trial is **3.082 g** after Boolean union with existing rails/saddles and the real port bores. Those overlaps are not counted twice. The resulting frame is **45.116 g**, versus 43.692 g in the prior recovery bill. Its total frame change is **+1.424 g** relative to that prior bill.

The full recovery increment becomes **67.506 g**, or **178.539 g** including the existing dedicated recovery allocation. This retains the same controller, isolated cell/switch, carrier, wiring/connectors, 18-end cord plan, protection, junction and attachment allowances. Adding frame material consumes recovery headroom even though the frame has other functions. No new saving from an unimplemented attachment or thermal component is credited.

The guide remains **5 m usable length, 10 m/s minimum departure, lower thrust, drag/friction assumptions and all 50 g growth**. Equipment availability is unconfirmed. The thermal entries are added-mass sensitivities, not compatible selected thermal hardware.

| Added thermal mass | Current rails: speed / mass margin | Prospective 2.111 g rail saving: speed / margin |
|---|---|---|
| 0 g | 10.14219 m/s / +7.239 g | 10.18390 m/s / +9.350 g |
| 8 g | **9.98513 m/s / −0.761 g, fail** | **10.02642 m/s / +1.350 g, arithmetic pass** |
| 12 g | 9.90717 m/s / −4.761 g, fail | 9.94827 m/s / −2.650 g, fail |
| 14 g | 9.86833 m/s / −6.761 g, fail | 9.90933 m/s / −4.650 g, fail |

Minimum speeds use the worse of the 1 ms and 0.5 ms integrations. The prospective rail saving has not been adopted or demonstrated compatible with this package. A changed thermal wall also changes the available bore and backing interfaces; a mass addition alone does not show fit.

## Remaining acceptance boundary

The actual slotted longitudinal rail area remains **15.836 mm²** each. Its estimated hot capacity is **395.89 N**, versus **784.95 N** from the existing unmeasured matched-leg bound and **1,031.96 N** from the single-leg bound. These required recovery cases still fail. No factor is applied twice, no opening requirement is relaxed, and no new rail/body attachment path is asserted.

The next engineering work is a separate actual cap/rim/rail/body load-sharing and material-direction model, plus compatible thermal, attachment and complete mass integration. The older required 0.3 m stopping-distance failure remains until supported snatch/energy rationale is reviewed. Owner material/fit/proof/deployment work, purchases, paid runs, WO-10 firmware/abort review and flight release retain their existing gates. All adoption and engineering/flight acceptance flags remain false.
