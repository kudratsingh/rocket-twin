# WO-03 recovery integration screen

**Status:** preliminary calculated integration screen; acceptance remains open and this is not flight-ready evidence. Run `wo03-recovery-integration-20261030T204618137637Z` evaluated all four platform assemblies using the same read-only protocol. Its record is [`record.json`](../runs/wo03-recovery-integration-20261030T204618137637Z/record.json). Source hashes were unchanged; all vehicle loads passed the standard loader with reconciled CAD mass caches. No source configuration or cache was changed by the analysis.

## Soft recovery package and access

The modeled parachute, shock cord and protection envelopes span stations 0.150–0.219 m (69 mm axial), with a maximum AABB-corner radius of 29.364 mm (58.728 mm circumscribed diameter). Their component boxes total 101.2 cm³ and their estimated masses sum to 51 g. These figures describe nominal component envelopes, not packed fabric volume. No rho-based fabric or cord solid-volume lower bound is supported: the source gives estimated whole-component masses and no reliable fabric-only/cord-only mass or validated material density. No folding, compression or repeatable packing claim is made.

The nose shoulder bore is 61.6 mm ID, giving 1.436 mm nominal radial clearance to the package's circumscribed bound. The body bore is 65 mm ID, giving 3.136 mm. The package overlaps the 30 mm long shoulder zone axially by 20 mm, and ends 6 mm ahead of the bulkhead station. These are rectangular-envelope clearances only. Fabric deformation, neck passage, extraction force, knots, harness sweep and repacking are unverified.

The modeled recovery electronics/carrier/harness set sums to 25.8 g estimated. Nominal rigid BRep pair checks found zero intersections in every configuration. This excludes flexible wire, connector, strain-relief, switch access and assembly trajectories. The recovery output wire budget and flight harness budget overlap by 55 mm axially; their actual routed relationship is unknown. The output budget ends 10 mm ahead of the internal switch envelope. The switch is at station 0.470 m and has 5.936 mm nominal radial room to the body bore, but no sidewall opening, bushing, shaft projection, panel retention, arming hole or screwdriver access is modeled. That external control remains an open design item.

EasyMini's current geometry has four 3.2 mm mount holes on 13.97 by 31.75 mm pitches; the modeled alignment pins are 2.4 mm diameter, nominally leaving 0.4 mm radial clearance. This only checks the stated hole/pin dimensions, not board fit, screw heads, board retention or connector access. The battery note describes a dedicated 1S 120 mAh LiPo, but voltage and capacity are absent from the resolved electrical profile. Its connector, polarity protection, restraint, pulse current/ESR and compatibility remain unverified. The analysis's 1 A × 1 s × 6 V (6 J) output is a screening assumption, not a component rating or validated deployment pulse.

## Active electrical topology

The current resolved netlists in all four configurations contain the intended topology: `RECOVERY_BAT_POS` from `recovery_battery` to `recovery_power_switch`, `RECOVERY_ARMED_POS` from the switch to `independent_recovery`, `RECOVERY_RETURN` directly from the dedicated cell to the controller, and `RECOVERY_OUTPUT_BUNDLE` from the controller to its output harness. The analysis confirms these edges and confirms no shared nodes with the modeled main power / flight computer net graph. Root corrected mode-level overrides after an earlier screen found a direct-main-battery connection; the earlier screen record remains archived. This is a spec-topology result, not a physical continuity or switch-isolation test.

## Anchor demand screen

The active geometry has a 5 mm G11 recovery bulkhead with a 3.4 mm anchor bore, nominal 0.2 mm radial clearance to the 3 mm M3 shank, and an 8 mm OD washer (41.17 mm nominal annular bearing area). Demand calculations use configured 5.0 and 20.4 m/s velocities, 0.3 and 0.6 m stopping distances, the resolved vehicle mass plus its 50 g design allowance, and a factor of 3. They assume constant deceleration over the stopping distance plus gravity and include no opening-shock multiplier. The 20.4 m/s case is an off-nominal probe, not an approved deployment-delay case.

| Configuration | Effective mass (kg) | Factored nominal max at 5 m/s, 0.3 m (N) | Factored off-nominal max at 20.4 m/s, 0.3 m (N) | Gross M3 shank demand at off-nominal max (MPa) | Mean washer pressure at off-nominal max (MPa) |
|---|---:|---:|---:|---:|---:|
| Modular performance | 0.789 | 121.9 | 1665.9 | 235.7 | 40.4 |
| TVC finned | 0.830 | 128.2 | 1751.8 | 247.8 | 42.5 |
| TVC finless | 0.696 | 107.5 | 1468.6 | 207.8 | 35.7 |
| G54 performance hypothesis | 0.868 | 134.0 | 1831.7 | 259.1 | 44.5 |

These stress and pressure values are demands, not capacity comparisons. No verified rating is available here for the anchor eye, M3 hardware, washer, G11 bearing or plate bending, bulkhead-to-tube bond/retention, harness attachment, or dynamic opening shock. The joint has not passed a structural qualification screen.

## Service procedure outline

1. Keep both vehicle power systems unarmed. Turn the recovery switch OFF and disconnect/remove the dedicated recovery cell before carrier handling. The resolved YAML describes the isolated topology, but physical continuity and switch behavior still need verification.
2. Separate the aft module at its joint for avionics access. Control and disconnect the recovery output lead without pulling on the modeled wire budget; flex routing and strain relief are not defined.
3. Release carrier retention and move the carrier through the open aft end. Replace the cell with polarity and positive restraint verified, reconnect the EasyMini and harness, then secure the carrier. Fastener and connector access need a physical mockup.
4. Insert and repack the soft recovery components from the nose toward the aft bulkhead. Inspect the eye/washer seating and keep the nominal 61.6 mm shoulder passage clear. No packed volume or deployment behavior is inferred from the envelope check.
5. After an aft-module exchange, verify indexing, anchor/harness attachment and every electrical connection. Do not treat the rotary control as usable until its panel hole, bushing, shaft retention, arming opening and tool access have been designed and physically checked.

**Open acceptance evidence:** physically verify the corrected mode-specific power nets; establish a real switch installation/access; verify battery, controller, connector and output pulse ratings; demonstrate board/carrier retention and wire bend/strain relief; physically pack and extract the recovery train; define hardware/bond ratings and qualify the anchor/bulkhead/harness load path across the stated cases, including a justified opening-shock basis. None of these gates is closed by this report.
