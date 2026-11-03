# G80-F1 — dedicated conventional construction decision

Current: **preliminary construction direction; one correction cycle completed;
not admitted to detailed whole-vehicle CAD or manufacture**. ADR-0013 supersedes
mandatory G80/G12 mechanical interchangeability. G54 and G12/PID-to-RL remain
separate committed tracks. No owner physical/purchase/flight gate changed.

Use a continuous66.675mm OD/64.77mm ID kraft body, custom160mm ASA ogive,
three custom6.5mm TTW birch fins, fixed29mm paper mount and plywood rings.
The v2 body is1060mm; overall retainer-inclusive envelope1250mm. Integral fin
tabs meet the mount and fixed rings. No removable aft sleeve, collar, radial
bolts, G11 outer can or future gimbal/servo provisions. Instrumentation and
independent recovery power remain. This is our cut/printed/bonded design, not
a substituted kit. See the two current manufacturer-linked manuals in
[construction references](wo03-g80-fixed-construction-references.md), and
[recovery review](wo03-g80-f1-recovery-review.md).

The chosen single correction extends the body300mm, leaves instrumentation
forward and doubles the forward ring to13mm. It improves balance but does not
clear the1calibre gate. No third geometry revision was executed. Calculated
mass and guide screens are promising, not installed-strength evidence.
No detailed whole-vehicle CAD, FEA, full flight campaign or new thermal solver
ran for the stopped candidate. The local section/connection drawings expose
remaining details; they are concept graphics, not released build drawings.

Numerical results are in the v1/v2 run records. V1 is frozen; v2 has a separate
specification snapshot and executed script. A launcher mistake also repeated
v1 once after the YAML-edit command failed under system Python; its1.155s
output is preserved separately and is not a new concept or acceptance result.
The required correction ran once in0.856s after imports, under30CPU seconds.

## Physical route and remaining admission conflicts

Fin force → integral plywood tab → continuous tab/tube and slot fillets →
forward/aft rings plus continuous paper body. There is no ideal ground support.
The distributed panel calculation passes nominal strength only; total movement,
6.1mm minimum stock thickness and installed flutter remain open. Forward ring
1075–1088mm overlaps tab1080–1190mm; a notch/termination is required and has
**not** been credited as solid load-carrying material. No invented smooth CAD.

Parachute → shock harness →0.6m heat leader → closed M4 eye/nuts/14mm washers →
13mm forward ring → tube/ring/body bonds and fixed motor/fin structure. The nose
branch uses a separate eye and plywood plate within the printed shoulder.
Finished eye capacity, local ring/plate/body behavior, positive nose-plate
retention, peel, uneven loading and physical proof remain unestablished. The
historical severe ring strip calculation still fails. Replacing a screw eye
with stronger hardware alone would move that weak link into the ring/body.

Motor → current commercial rear shoulder/retainer → fixed motor tube/rings →
body. Reverse motor retention is independent of recovery. The old internal
seat/liner has been removed from this architecture; no motor is silently moved
within an inherited interface. Exact current78010 shoulder/nozzle and009750
retainer/tube dimensions are still unavailable. Thermal mass is reserved outside
the bore, with relief/termination undefined; it is not an accepted shield.
The45°C provisional substrate screen and required cases remain unchanged.

## Recovery assumptions decision

Retain5m/s,20.4m/s,0.3m and DF3 calculations, including the severe case in
acceptance until a mechanism-based revision is justified. The equation is
energy-equivalent mean force, not a demonstrated peak.20.4m/s came from an
older late-delay probe, not F1 telemetry.0.3m is assumed effective travel, not
measured cord extension. Inflation comparison uses published Knacke-style
Cx·q·CdS with Cx1.2–2 and DF3 once. It excludes line-stretch/snatch and cannot
replace the severe case by itself. We have **not** reduced the recovery criterion.

Next decision: one mechanism-based deployment/anchor packet must establish an
applicable severe case and positive anchor/body path, while a declared
forward-mass placement correction must supply the missing stability margin.
No automatic new bracket/architecture or capped calculation repeat. A purely
algebraic35–50g nose-weight possibility must count actual hardware and packing;
it is not an executed passing design. Exact supplier fit remains a separate hold.

## Complete recorded budget and closure

All values below are model estimates. No current flight performance/altitude is
claimed for this stopped geometry. Full flight validation is deferred until
static/connection admission; no old C1 trajectory is reused. Model inertia
includes simplified envelopes, with integral-tab mass allocated separately;
physical full inertia/CAD reconciliation remains unavailable. Tensor values
in the record are diagnostic geometry estimates, not measured as-built inertia.

| Case | Parts plus separate50g, g | CG, mm | CP, mm | Loaded / burnout margin, cal |1.5m speed, m/s | Formal / planning headroom, g | Retained severe mean×DF3, N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nominal_full_growth | 817.506 | 810.611 | 860.125 | 0.743 / 1.171 | 16.388 | 140.847 / 86.302 | 1725.1 |
| adverse_20g_aft_motor_probe | 837.506 | 823.063 | 860.125 | 0.556 / 0.974 | 16.170 | 120.847 / 66.302 | 1767.3 |

Adverse adds20g at1250mm **in addition** to full50g and retains the12.8mm motor-CG
probe. On conditional1.8m travel speeds are17.951/17.714m/s; on1.971m they are
18.785/18.537. Neither equipment nor a longer baseline is adopted. Reference
1.5m calculated total-mass limits958.352g formal/903.808g planning depend on
this diameter, thrust curve,0.85 thrust,0.8Cd,0.5N friction,vertical travel and
fixed loaded mass. They are not universal rocket limits.

At1calibre the balance point must be no farther aft than793.450mm. Current
nominal810.611/adverse823.063mm fail. Holding all else fixed, a point ballast
at120mm would need36.827g in the adverse case merely to reach the boundary;
this is an algebraic planning quantity, **not an admitted revised design**.
Use actual forward equipment/anchor placement and useful margin in a separately
declared next packet rather than automatically adding ballast or rerunning v2.

| Item | Result | Acceptance / next evidence |
| --- | --- | --- |
| Exact-once estimated parts ledger |42 rows,767.506g;50g outside |Complete estimate; supplier/as-built uncertainties stay open |
| Guide requirement for candidate |16.388/16.170m/s |Passes15 formal and15.5 planning in saved guide model only |
| Static stability |.743/.556cal |Fails1.0; corrected placement needed |
| Fin panel strength |3.174MPa vs5MPa estimated hot |Nominal scalar screen passes, no installed qualification |
| Fin movement |.932mm distributed panel;3.056mm tip-load bound |Installed total1mm not proven; root stiffness must exceed2573Nm/rad in same model |
| Minimum6.1mm fin thickness |1.128mm panel estimate by thickness-cubed scaling |Fails1mm before root flexibility; stock selection/reinforcement decision needed |
| Forward recovery ring |Severe strip fails; separate inflation-only strip passes |No full path acceptance. Annular redistribution/contact/support not solved |
| Current motor/retainer |Supplier mating drawing missing |Exact bore/shoulder/lip/contact and service hold |
| Fin/ring occupancy |Forward tab overlaps ring8mm |Local tab/slot termination not defined; do not pretend solid contacts are buildable |
| Thermal |No compatible F1 temperature result |45°C screen/required matrix retained; no old failed overlay promoted |
| Recovery/electrical independence |Two distinct power nets in candidate |Logical separation only; proof/electrical/deployment tests later |
| Reference comparison |Both endpoint static RocketPy checks pass |Agreement under shared geometry, not strength/flight validation |

The single correction exhausted this packet. **No installed engineering requirement
closes.** The guide and nominal panel screens became calculable/passable; this
is narrower than accepting a complete vehicle. The next bounded deliverable is
a recovery/installed-root and forward-placement admission definition, not detailed
whole CAD of an unresolved joint. Retain the simple fixed architecture; do not
reintroduce the removed modular hardware.

## Fabrication and purchasing definition

Custom: ogive/shoulder, stock-cut fins and integral tabs, rings/nose plate,
slotted tube and removable instrumentation carriers. Purchased: body/motor tube,
certified motor, retainer, chute, line/heat protection, closed eyes/connectors,
electronics/cells/switches and rail buttons. Two6.5mm forward-ring layers are
laminated with the counted adhesive. Face grain runs spanwise on fins; cut edges
sealed, bond surfaces prepared per selected epoxy, measured parts dry-fitted,
then internal mount/tab/ring fillets made while the aft opening is accessible.
No generic material strength is assigned to a finished eye or paper joint.

Provisional fits: nose shoulder OD64.0 in ID64.77 gives radial clearance.385mm;
±.1mm radial on each gives.185/.385/.585mm cold min/nom/max. Thermal/humidity
and measured tube ovality are not closed. Ring/body adhesive gap.205mm nominal;
mount/ring.200mm. These are bonded gaps, not free-motion clearances. Motor
historical29.000mm envelope versus28.956mm nominal mount ID would be a44µm
interference; current nominal1.125in motor may instead clear, but a catalog
nominal is not a controlled tolerance. This inconsistency **blocks exact fit**;
no bore enlargement or motor/source substitution has occurred.

Sequence after design holds close: cut/condition/measure stock; dry-fit mount,
fins and anchors; install/test accessible anchor nuts; stage internal bonds;
close aft ring only after fillet inspection; install verified retainer; fit
removable electronics and separate recovery supply; verify arming/connector
access; ground packing/extraction and proof tests; finally owner-authorized
prototype assembly. Service motor only from aft with cap removed; electronics
and recovery accessed from nose. These are preliminary instructions, not build
or pyrotechnic deployment authorization. Final controlled drawings, procurement
pack and qualified instructions remain WO09.

### Complete consumed-parts estimate

Costs are inherited/engineering allowances, not current supplier quotes or a
shopping cart. No purchase made. Subtotal333.95USD includes one34USD motor;
stock pack quantities, shipping, tax, tools, spares and physical tests excluded.

| Part ID / function | Estimated mass,g | CG station,mm | Cost allowance,USD |
| --- | ---: | ---: | ---: |
| nose | 38.000 | 100.177 | 5.00 |
| body | 145.926 | 690.000 | 14.00 |
| fin_set | 77.220 | 1145.556 | 9.00 |
| fin_tabs | 26.093 | 1135.000 | 0.00 |
| motor_tube | 9.627 | 1137.500 | 4.00 |
| forward_ring | 21.929 | 1081.500 | 4.00 |
| aft_ring | 10.965 | 1193.250 | 2.00 |
| fin_internal_bonds | 14.000 | 1135.000 | 3.00 |
| ring_bonds | 9.000 | 1135.500 | 2.00 |
| outer_fin_fillets | 10.000 | 1140.000 | 2.00 |
| motor | 128.200 | 1156.000 | 34.00 |
| motor_retainer | 22.000 | 1227.500 | 18.00 |
| retainer_adhesive | 2.000 | 1212.500 | 1.00 |
| mount_external_shield | 9.872 | 1130.000 | 5.00 |
| body_recovery_eye | 9.000 | 1069.000 | 4.00 |
| nose_anchor_plate | 12.873 | 181.250 | 2.00 |
| nose_recovery_eye | 9.000 | 180.000 | 4.00 |
| heat_leader | 8.000 | 1035.000 | 5.00 |
| shock_cord | 18.000 | 290.000 | 8.00 |
| recovery_connectors | 9.000 | 262.500 | 8.00 |
| parachute | 35.000 | 242.500 | 30.00 |
| recovery_protection | 6.000 | 285.000 | 8.00 |
| flight_computer | 12.000 | 400.500 | 32.00 |
| imu | 2.000 | 450.000 | 18.00 |
| baro | 1.000 | 472.500 | 15.00 |
| high_g_accel | 1.000 | 497.800 | 24.95 |
| micro_sd | 3.000 | 515.000 | 10.00 |
| battery | 30.000 | 392.500 | 18.00 |
| independent_recovery | 6.500 | 579.050 | 0.00 |
| recovery_battery | 3.600 | 620.000 | 0.00 |
| recovery_power_switch | 3.700 | 619.288 | 0.00 |
| avionics_sled | 11.000 | 370.000 | 5.00 |
| logger_power_switch | 3.000 | 435.000 | 3.00 |
| logger_regulator | 4.000 | 450.000 | 4.00 |
| recovery_carrier | 8.000 | 570.000 | 4.00 |
| electrical_harness | 9.000 | 440.000 | 5.00 |
| recovery_harness_wiring | 5.000 | 600.000 | 4.00 |
| recovery_output_mount | 6.000 | 710.000 | 5.00 |
| rail_buttons | 5.000 | 470.000 | 6.00 |
| rail_backers | 4.000 | 470.000 | 1.00 |
| finish | 12.000 | 470.000 | 5.00 |
| service_allowance | 6.000 | 470.000 | 2.00 |

Source stock choice is a departure from the LOC1/8in fins:6.5mm was selected for
our40kPa/5deg hot panel screen, not because kit fins were inadequate. Its minimum
stock stiffness finding remains open. Longer body is our balance correction;
kit catalogue weights were never substituted for the ledger. Independent
barometric recovery plus low/high-g logging adds real mass and learning value;
future G12 servo/regulator/gimbal stock does not. Fixed fins/mount lose aft
interchangeability and internal repair access; staged bonding/inspection is
therefore essential. G54/G12 cannot inherit F1 acceptance.

### Owner-only measurements and tests, planning only

- Identify exact motor lot and chosen retainer/mount; record OD at multiple
  stations, rear shoulder/contact plane, forward end/nozzle projection, bore,
  lip and cap engagement. Seek current supplier drawing first; no trimming.
- Condition and measure selected tube/ply stock; weigh all finished parts and
  adhesive/finish. Establish grain/hot/wet behavior and fit after conditioning.
- Test representative fin/tab/ring/body joint under both signs of load. Record
  force vs displacement, root rotation, onset of peel/crushing and residual set;
  compare with108.95N/2.905Nm factored panel and1mm total criterion. Installed
  modal/tap test and justified flutter screen remain later physical correlation.
- Test finished harness ends/eye/washer/ring/body and nose plate separately then
  assembled. Record extension, capacity and failure mode at relevant temperature.
  Deployment test measures section separation speed, slack, line-stretch and
  canopy inflation force/time; distinguish normal from deliberately faulted cases.
- Instrument motor mount/body/adhesive/electronics during owner-authorized ground
  thermal validation with suitable isolation; record burn and post-burn soak.
  No stopped custom thermal campaign restart is proposed.
- Independent recovery power/arming, connector strain relief, packing/extraction
  and inert service trial before any later live deployment procedure or flight.

No owner action is necessary to inspect this packet. Essential hardware inputs
are exact supplier dimensions and measured properties at the later authorized
prototype/ground-test stage; no club contact, purchase or physical work occurred.

## Stock-supply hold

The separately bounded [official supplier amendment](wo03-g80-f1-supply-holds.md)
found no exact one-piece1060mm blank. LOC lists762mm with different65.024mmID /
66.802mmOD, and Balsa Machining general34in stock is863.6mm. Thus the current
body is a design-intent envelope, not a sourced cut length. A permanent bonded
splice from actual stock is a specific possible next architecture/interface
revision; it must count its sleeve/bond mass and revalidate fits/balance, rather
than silently treating a short tube as long. No such revision ran in this packet.
