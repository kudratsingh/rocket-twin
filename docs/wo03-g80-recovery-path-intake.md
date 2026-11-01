# WO-03 G80 recovery load-path intake

**Status:** read-only load-path audit of the staged candidate; no connection is qualified and no physical test or new analysis was run. The staged 72-part candidate has identity `90b2a9ad780fc81d11171363432c46088531817ddb6570fe9f800429bde2bdfc` and base 52-part identity `62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009`. The Stage 3 nominal is `f7b8af96f50ce96d6091f1da177198eb82a0797e42cb6874d98d5b5d7e6a8899`. The corrected +5 g sensitivity is `6b0577cef1256065f27dc79bb494a89e6c1f0c90703c9815f47c7ae7910d1dc4`; it is a separate 73-part sensitivity, not the nominal package. Its record states the correction changed allowance learn/build metadata only, with the sensitivity prepare arrays unchanged. Neither identity is an accepted configuration.

## Load-path trace

| Link | Candidate definition and saved basis | What is represented | Missing connection evidence |
|---|---|---|---|
| Canopy → shock cord | `parachute`: station 0.150 m, 55×40×40 mm envelope, 35 g in the staged 72-part file; Stage 3 nominal mass is 51.6 g. `shock_cord`: station 0.205 m, 14×40×15 mm envelope, 10 g. Both are soft envelopes with supplied/estimated mass. | Approximate placement and mass only. | No cord length, canopy attachment loop, knot/stitch, termination, canopy/cord connection, or opening-load rating is defined. The canopy estimate uses a 750 mm parachute with unvalidated Cd/packing. |
| Shock cord → anchor | `recovery_anchor`: station 0.215 m, length 15 mm, radius 4 mm, 4 g supplied/estimated. CAD generator `anchor` describes a 3 mm shank, forward eye and aft washer. | Nominal anchor envelope: eye annulus and washer geometry; its 15 mm span overlaps the bulkhead station. | No purchased manufacturer/part number, material/grade, thread/nut or captive lock, installation torque, washer purchase identity, or physical cord-to-eye endpoint. No anchor strength is credited. |
| Anchor → spreader | `recovery_bulkhead`: G11, station 0.225 m, 5 mm thick, radius 32.3 mm, 3.4 mm hole, mass 30.234 g. Its CAD generator makes the disk and anchor hole. | The anchor shank is geometrically intended to pass through the bulkhead hole; the anchor's generated washer is on the aft side. The recorded mass uses the CAD bulkhead shape and a configured G11 density basis. | No washer bearing/contact stress, bulkhead bending, hole bearing, or fastener preload is assessed. The record does not establish an as-built bolted joint. |
| Bulkhead → upper body tube | `body_upper`: cardboard, station 0.140 m, length 0.778 m (ends at 0.918 m), OD 66 mm, ID 65 mm, nominal wall 0.5 mm; mass 56.032 g. Bulkhead is parented to `body_upper` at station 0.225 m. | Nominal placement and individual BRep mass/geometry. | Parent/part hierarchy is not an adhesive joint. No annular bond line, fillet, edge capture, tube tear-out, bulkhead-to-tube shear transfer, surface preparation, or coupon data is defined. This is the first unclosed structural connection after the cord/eye termination: the bulkhead is not attached to the tube by a specified load-bearing joint. |
| Upper body → aft module | `interface_coupler`: station 0.868 m, length 104 mm, cardboard, OD 64 mm, ID 61 mm, 21.067 g; intended 50 mm overlap into each shell. `joint_stop`: station 0.918 m, 29 mm, ASA ring/key geometry, 1.319 g. | CAD envelope and keyed removable-module concept; coupler learn text says keys carry torque and the stop carries thrust. | No opening-load axial retention/pull rating, bond/joint test, tube bearing/tear-out evidence, or proof that recovery opening force reaches the aft module through this joint. The aft G80 retention bridge/keeper is a motor-retention design and is not credited as a recovery load path. |
| Nose attachment (separate) | `nose_cone`: station 0.000 m, length 140 mm, OD radius 33 mm, ASA; 30 mm shoulder, CAD shoulder OD 32.15 mm / ID 30.8 mm. `body_upper` begins at 0.140 m. | Nominal shoulder and body envelopes only. | No positive axial retainer, separation joint details, nose harness attachment, or test is specified. The candidate anchor sits at the bulkhead in the body tube; no nose connection is credited. Nose separation under ejection and tether motion remain unmodeled. |
| Recovery electronics and retained parts | Detail is below. | Component envelopes, masses, and preliminary mounting geometry. Some fasteners have handling/vibration language; the carrier package is a modeled proposal. | These are not the recovery tether. Their restraint under the opening deceleration is not analyzed, and their mount fasteners are not specified/tested for this load case. The separate `harness` at 0.335 m is a 12 g avionics-bay distributed budget; it is not the 10 g `shock_cord` and has no defined recovery connection. |

The staged YAML gives these electronics/restraint envelopes and mass bases (all dimensions are bounding boxes; no rated load is stated):

| Part ID | Station | Envelope or geometry | Mass and basis |
|---|---:|---|---:|
| `avionics_bay` | 0.240 m | 210 mm long, radius 26 mm; ASA sled | 9.045 g, CAD volume/density |
| `independent_recovery` | 0.380 m | 38.1×20.32×1.6 mm controller envelope | 3.000 g, supplied/estimated |
| `recovery_easymini_components` | 0.380 m | 38.1×20.32×4.4 mm board/components envelope | 3.500 g, supplied/estimated |
| `recovery_battery` | 0.333 m | 30×15×4 mm dedicated cell envelope | 3.600 g, supplied/estimated |
| `recovery_mount_carrier` | 0.333 m | 92×26×1 mm plate envelope | 4.297 g, supplied/estimated |
| `recovery_battery_tray` | 0.333 m | 31.5×17.5×4.8 mm ASA cradle envelope | 0.664 g, supplied/estimated |
| `recovery_battery_band` | 0.333 m | 8×0.3×0.8 mm nylon band envelope | 0.350 g, supplied/estimated |
| `recovery_fasteners` / `recovery_nuts` | 0.380 m | Four nylon M3×12 screw envelopes and four 5.5×2.4×5.5 mm square-nut envelopes | 0.683 g / 0.245 g, supplied/estimated |
| `recovery_sled_fasteners` / `recovery_sled_nuts` | 0.333 m | Six nylon M2.5×12 fastener envelopes and four 4.5×2×4.5 mm nut envelopes | 0.636 g / 0.194 g, supplied/estimated |

Their parent references attach to `avionics_bay`, the carrier, or one another, but those references do not define an opening-load path from each component through the sled into the cardboard tube. The battery band, flex leads, fastener preload, carrier restraint and board retention have no opening-shock verification.

The geometry and component hierarchy do not prove physical continuity across any of these connections. The staged record's `modified_mount.step` (`8f88eeeb…50a14`) and `bridge.step` (`f92832b8…6408ed`) are aft motor-retention parts, not the recovery anchor or bulkhead assembly. No identity-matched recovery-anchor/bulkhead/tube assembly STEP or load-bearing bond geometry was found in the inspected records. The latest package's calculated mass/CG does not establish attachment strength.

## Existing constant-deceleration demand only

I used the current configured values in `configs/engineering/wo03.yaml`: speeds 5 and 20.4 m/s, stopping distances 0.3 and 0.6 m, design factor 3. The existing basis is

`F_DF3 = 3 m (v² / (2 s) + 9.80665 m/s²)`.

The current corrected 6b full-growth sensitivity record has 0.8445817123 kg at full-loaded mass and 0.7820817123 kg at burnout. These include the full 50 g growth allowance and the separate +5 g canopy/line sensitivity component. The adjacent f7b nominal scenario is 0.7895817123 kg loaded and 0.7270817123 kg at burnout before the 50 g allowance; it is not used as the conservative bound below. Values are static constant-deceleration demands, rounded to 0.001 N.

| Speed | Travel | Corrected 6b burnout, 0.782082 kg | Corrected 6b full-loaded, 0.844582 kg |
|---:|---:|---:|---:|
| 5 m/s | 0.3 m | 120.769 N | 130.420 N |
| 5 m/s | 0.6 m | 71.889 N | 77.634 N |
| 20.4 m/s | 0.3 m | 1650.364 N | 1782.253 N |
| 20.4 m/s | 0.6 m | 836.687 N | 903.550 N |

These numbers include gravity and DF3 exactly as the configured screen does. No opening-shock multiplier, canopy snatch transient, distributed body dynamics, asymmetric loading, or safety factor beyond the named DF3 calculation is added. The 20.4 m/s value remains the archived late-G80-delay probe and is **not approved as a deployment-delay limit**. Do not treat these forces as material allowables or proof loads.

## Decision

The first unclosed structural connection downstream of the proposed line/eye is the G11 bulkhead-to-0.5 mm cardboard upper-body joint. The upstream cord-to-canopy and cord-to-eye endpoints are also only envelopes, so the complete load path is not yet physically defined.

One lightweight custom correction direction for later design review is to replace the generic purchased-eye assumption with a small, radiused G11 or plywood loop integrated into a local annular spreader bonded to the body tube, with the cord end specified as a real sewn/looped termination. This avoids the rejected industrial lifting-eye/steel-boss approach. It is only a candidate geometry direction: no adhesive, laminate, loop, or tube capacity is claimed. A later design would need an explicit cord termination and bonded load-transfer geometry, followed by coupon/joint proof evidence against a justified opening-load basis.

## Provenance and boundaries

The saved staged record and Stage 3 records are hashed in the prior machine-readable intake embedded as `prior_load_path_intake` in [the recovery-path record](../runs/wo03-g80-recovery-path-20261101-v1/record.json). Its input list covers the staged YAML/record/generator, the Stage 3 nominal/sensitivity specs and flight/static results, the engineering and retention study configs, the recovery screen, and the CAD/recovery integration source. The staged record reports `acceptance: false` and `flight_ready: false`; Stage 3 equivalence also reports acceptance false. No CAD, native solver, test, or browser work was performed for this intake. No G12 or prior motor/fin evidence was used as recovery strength evidence.
