# G80-F2 — supplier-stock construction follow-up

Selected for connection verification: **G80-F2 fixed-stock ballast v2**, keeping
60mm-span fins, compact forward instrumentation and17.816g captive washer ballast
plus7g retention hardware. F1 remains frozen. The65mm-span alternative is lighter
but leaves only0.059mm of minimum-thickness panel movement for root flexibility;
selected60mm fins leave0.401mm. This is a mechanics trade, not a blanket rejection
of ballast or a changed platform. No whole-vehicle/prototype/flight release.

Actual stock: two LOC BT-2.56 blanks, each762mm x66.802OD/65.024ID; upper298mm,
lower762mm. A permanent100mm split sleeve is formed from the second blank's
offcut to64.45OD, with50mm overlap each side,15mm internal seam patch and8g
adhesive. Sleeve nominal/final fitted dimensions are fabrication targets, not
supplier tolerances. Prepared incoming/conditioned radial fit.15/.287/.425mm
min/nom/max preserves.1mm minimum. No removable aft joint returns.

AeroTech12912 cut165mm plus19002 retainer are a manufacturer-matched candidate
family. Current78010 ring/nozzle/seat/retainer cap dimensions still missing;
29x128mm/128.2g historical curve remains the flight/guide hypothesis. Current
product nominal28.575mm case OD versus inferred29.169mm mount ID gives.297mm
nominal radial gap, not a tolerance proof. The historical29mm rounded envelope
would give.0845mm. Motor/retainer fit and procurement remain held, not trimmed.

Plywood is Aircraft Spruce02-20850 nominal6mm twelve-ply Finnish birch; full
69.75USD sheet charged once. Proposed incoming window5.8--6.2mm is an inspection
requirement, not a published tolerance. No Metsä strength is assigned to it.
Existing weak/hot estimates remain: E1GPa,5MPa strength; they need proof/calibration.
Forward ring two6mm plies+.2mm glue. Three6.5mm-wide blind notches7.4mm deep
leave4.8mm front web. Tabs start.2mm behind notch floor and end.2mm before aft
ring; flat inneredge leaves.2--.481mm epoxy gap to the motor tube. Local BRep
calculation removes2121mm³ tab/ring interference to zero; no whole CAD acceptance.

Recovery: parachute→cord→two0.3m heat-leader branches→two opposed closed eyes
atR23mm,30/210deg→forward ring→tab/tube/body joints.70/30 and full single-leg
loads remain checks, never assumed equal sharing. Each eye needs≥25mm usable
thread (12.2 ring+washers+nuts/projection requires19.4mm); proposed30mm thread
and45mm overall envelope. Exact finished hardware capacity/source remains held.
The simplified14mm strip still fails; it is a diagnostic, not a solved annular
plate or proof of installed failure. Actual support/annular behavior is a
separate bounded diagnostic and must not hide body, tab-bond or peel limits.

Nose branch: separate eye through12mm plywood annulus/45mm service aperture,
perimeter12mm lap into printed shoulder. Main logger/battery and independent
controller/cell move with the nose; no recovery wiring or battery is shared.
All part positions are explicit. Eight21-slice corner screens give≥1.114mm
radial nose-envelope clearance; connector projections, straps, holes and full
insertion motion are not proved by that sampled result. Nose carrier is removed
through the service opening after disconnecting accessible eye/outputs. Finished
nose-eye/plate/ASA bond and battery/ballast capture proof remain physical gates.

Recovery controller: Eggtimer Apogee one-channel kit, about5g,44.45x22.86mm,
1S only, integrated screw switch. Starter34USD is charged as15controller+19
cell/charger package allocation; no owner-stock evidence exists. Cell5g is an
unmeasured envelope allowance. Current EasyMini is out of stock, and $0 prior
rows did not establish ownership. Eggtimer live supply requires an owner-approved
inquiry/order; no contact/purchase occurred. Kit assembly and electrical/ground
qualification stay owner-performed. Other quoted component costs are marked
source prices or engineering allowances, not a reserved shopping cart.

Recovery packing is forward at280--360mm, above the458mm splice;50mm packed
canopy diameter/80mm length is157mL, an estimated stowage envelope. Cord and
blanket occupy the upper clear bore, not behind permanent electronics. All
instrumentation is retained with the nose so extraction does not pass a fixed
board/battery. The≥60.694mm centred sleeve bore is a conservative local limit;
actual packing, chafe, slack, ejection and extraction are later measured tests.

Keep historical20.4m/s/.3m/DF3 severe demand; no force revision was adopted.
Inflation and line-snatch mechanisms remain separate, with a defined test plan.
Temperature45°C substrate screen and required matrix unchanged; shield mass10g
is reserved, not an accepted continuous barrier. Fin contact windows and shield
ends/adhesive/solid paths must be represented in later thermal revalidation.
No custom thermal campaign restarted and no old result transferred to F2.


## Coupled results and admission

| Selected case | Parts + separate50g,g | CG,mm | CP,mm | Loaded / burnout,cal |1.5m speed,m/s | Formal / planning headroom,g |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
|nominal_full_growth|917.560|773.559|859.442|1.286/1.704|15.370|40.784/-13.761|
|adverse_20g_aft_motor_probe|937.560|785.473|859.442|1.107/1.517|15.186|20.784/-33.761|

Both rows include50g all-growth-aft; adverse additionally20g and12.8mm motor-CG
probe. Actual parts867.560g,50 rows. Cost458.71USD includes full stock and recovery
starter allocation; known battery shipping adds10USD, other freight/tax/tools
unquoted. The original66.302g adverse planning budget is exceeded by33.761g;
no correction item or allowance is hidden. Formal1.5m still passes by20.784g
mass equivalent. Planning15.5m/s needs1.562667m usable for the adverse case;
this is not a confirmed rail or adopted baseline. Conditional1.8m gives
16.638m/s adverse. No full new flight campaign ran while connection acceptance
remains open. Static RocketPy endpoints agree; that validates the common static
calculation, not actual strength or flight readiness. Full physical inertia
remains unavailable; own-envelope tensors in records are diagnostic.

The65mm-span/no-ballast alternative is899.895/919.895g with1.324/1.150cal and
15.537/15.348m/s on1.5m. Its minimum5.8mm panel movement.941mm needs roughly
3987Nm/rad root stiffness for1mm total; selected60mm fins need roughly435Nm/rad.
Neither stiffness is measured. The selected ballast is17.816g source-defined
BelMetric WFE5X15SS washers plus7g capsule/bolt/attachment, not a free point mass.
It improves mechanical feasibility at the expense of guide/altitude potential.
No ballast/fin configuration has been flight-qualified.

## Ring calculation reliability and physical scope

The actual notched ring was exported from CadQuery and meshed with pinned
Gmsh4.15.2/CalculiX2.23. Three mesh sizes3/2/1.4mm completed, with finite body,
motor-tube and fin-tab support springs estimated from EA/L (not fixed axial
supports). A100N unit force uses70/30 and full single-eye cases, already-factored
recovery demands are scaled once. Washer/ring contact is tied and wood
isotropically estimated; this is a component diagnostic, not a dynamically
balanced deployed-vehicle model. It cannot establish installed capacity.

**Post-solve geometry audit found one inverted quadratic element in the2mm
mesh (min scaled Jacobian−.189). That result is invalid.** The coarse and fine
sampled minima are+.0346/+.1344, but two valid meshes do not supply the required
three-grid convergence evidence. The apparent middle-to-fine stress convergence
must not be used. Peak stress changes about27%; it is not converged. Force
balance is within1.4e-8 relative and a separate100N/mm spring known-answer fixture
returns exactly.02mm at2N; neither rescues invalid geometry. The packet stopped
without another mesh/solver attempt. The producer now checks quality before
solving; the executed prior producer and every failed/stopped record are retained.

The valid fine-grid diagnostic still gives adverse ring/interface values when
scaled to the body recovery branch, but they remain **diagnostic**, not accepted
stress fields or proof that real hardware has failed. No stronger ring or rigid
support is adopted from them. Next numerical decision is a bounded pressure-
footprint model without tied thin washer solids, plus real support/load-path
validation; no automatic retry or whole-vehicle FEA is authorized by this packet.
See the [2.23 manual](https://www.dhondt.de/ccx_2.23.pdf) for the solver elements.

[Coupled accounting](wo03-g80-f2-coupled-accounting.md) explicitly reconciles nose,
body and soft goods. At the adverse severe mean proxy, nose409.288N +
body1408.793N + soft160.377N = whole1978.458N. No force was reduced arbitrarily
or divided equally among eyes. Single-body-eye eccentric moment32.402Nm and
70/30 moment12.961Nm remain checks. The report's *paper-only aft serial path*
is conditional: the actual parallel ring/tab/motor/body route has not been
established, so that proxy is not proof the real paper alone carries all aft
mass. A cut just forward of the anchor has a different retained fore-body load;
neither allocation may be silently substituted for the complete free-body model.
This missing installed load route remains the controlling structural admission
item, alongside exact eye/retainer dimensions, root stiffness/flutter and thermal.

## Complete parts and acquisition budget

$0 material rows are included in the two body blanks or full plywood sheet;
none means owner-owned electronics. Board15+cell/charger allocation19 =34USD
starter. Below are component acquisition allocations, not guaranteed checkout
quotes or finished weights. Tax, other shipping, tools and owner work are separate.

| Part | Mass,g | CG,mm | Acquisition allowance,USD |
| --- | ---: | ---: | ---: |
|nose|38.000|100.175|5.00|
|body|98.192|839.000|20.54|
|fin_set|78.832|1145.556|69.75|
|fin_tabs|25.918|1134.900|0.00|
|motor_tube|24.000|1137.500|7.49|
|forward_ring|20.265|1081.100|0.00|
|aft_ring|11.162|1193.000|0.00|
|fin_internal_bonds|14.000|1135.000|3.00|
|ring_bonds|10.000|1135.500|2.00|
|outer_fin_fillets|10.000|1140.000|2.00|
|motor|128.200|1156.000|43.99|
|motor_retainer|30.000|1227.500|23.99|
|retainer_adhesive|2.000|1212.500|1.00|
|mount_external_shield|10.000|1130.000|5.00|
|body_recovery_eye|18.000|1069.000|4.00|
|nose_anchor_plate|12.139|184.100|0.00|
|nose_recovery_eye|9.000|179.000|4.00|
|heat_leader|8.000|1035.000|5.00|
|shock_cord|18.000|390.000|8.00|
|recovery_connectors|9.000|362.500|8.00|
|parachute|35.000|320.000|30.00|
|recovery_protection|6.000|370.000|8.00|
|flight_computer|12.000|115.500|32.00|
|imu|2.000|123.000|18.00|
|baro|1.000|144.500|15.00|
|high_g_accel|1.000|97.800|24.95|
|micro_sd|3.000|155.000|10.00|
|battery|30.000|112.500|18.00|
|independent_recovery|5.000|192.225|15.00|
|recovery_battery|5.000|208.000|19.00|
|avionics_sled|11.000|127.000|5.00|
|logger_power_switch|3.000|156.000|3.00|
|logger_regulator|4.000|160.500|4.00|
|recovery_carrier|8.000|185.000|4.00|
|electrical_harness|11.000|130.000|5.00|
|recovery_harness_wiring|5.000|210.000|4.00|
|recovery_output_mount|6.000|245.000|5.00|
|rail_buttons|5.000|470.000|6.00|
|rail_backers|4.000|470.000|1.00|
|finish|12.000|470.000|5.00|
|service_allowance|6.000|470.000|2.00|
|upper_body|38.401|309.000|0.00|
|body_splice|12.426|458.000|0.00|
|splice_seam_patch|0.933|458.000|0.00|
|splice_adhesive|8.000|458.000|2.00|
|root_gussets|26.277|1140.000|0.00|
|root_extra_bond_finish|4.000|1140.000|2.00|
|nose_service_hardware|3.000|184.000|2.00|
|ballast_capsule|7.000|50.000|3.00|
|nose_ballast|17.816|55.000|3.00|

## Fabrication, service and owner-only verification plan

1. Confirm exact purchased stock/revision and condition paper/ply before measuring.
   Body receiving ID64.9--65.15mm and plywood5.8--6.2mm are proposed acceptance
   windows, not supplier guarantees; reject/refit/revalidate outside them.
2. Cut762+298mm body from two blanks. From the remaining offcut form100mm sleeve:
   remove about7.59mm axial strip for64.45OD and.2mm seam, form on a measured
   mandrel, apply15mm internal seam patch, then verify fitted conditioned clearance.
   Bond50mm overlap each side in an alignment jig; meter8g film/seam/fillet
   adhesive. Feather sleeve edges for line passage without crediting untested peel.
3. Cut fins/tabs and root wedges with spanwise face grain; cut matching blind ring
   notches after measuring thickness. Keep.2mm motor-tube and end gaps, nominal
   .25mm side gaps. Bond/fill these volumes; no parallel air route through glue.
   Dry-fit and inspect internal fillets before aft ring closes access. Record
   cure, adhesive lot, measured mass and bond preparation; no proof from appearance.
4. Install the two recovery eyes before closing the fixed bay; verify shank length,
   washers, nut engagement, locking, hardware/tool access and known branch routing.
   Actual eye ID/capacity remains unresolved, so this is not released fabrication.
5. Retain main battery/logger and independent Apogee/cell on removable nose carriers.
   Maintain positive straps, separate supply/output nets, barometric venting and
   screw-switch access. Check connector projection, polarity, wire bend/strain relief
   and complete insertion/removal with unarmed/disconnected electronics.
6. Capture the washer stack on the M5 bolt inside the closed capsule, secured to
   the nose carrier. Proof the complete52.367N severe ballast/capture demand and
   the full409.288N nose branch separately. Do not use ballast-only force for eye.
7. Repack inert recovery with the nose pod removed. Verify line slack, smooth splice
   passage, canopy extraction, both retained branches and arming/service access.
   Storyboard is not a simulated/qualified deployment. Independent recovery firing,
   actual ejection, relative separation speed, line stretch and opening peak require
   owner-performed ground tests under the existing gates.
8. Obtain actual motor/retainer drawings before final axial seat/nozzle/contact
   freeze. Motor slides out aft after cap removal; thermal sector/end design and
   hot/cold fits remain open. Instrument burn/post-burn temperatures later; no
   accepted45°C result or physical strength is claimed here.

Prototype definition status: local splice/root geometry and complete estimated
budget are inspectable; this is suitable for reviewing an inert fit/mockup plan,
**not a released complete prototype build**. Installed recovery path, exact
purchased envelopes, root/flutter and thermal acceptance remain open. Flight
readiness additionally requires later as-built proof, electronics/HIL, recovery
and owner launch release. G54 and G12/PID-to-RL retain their separate commitments.
The next specific decision is the recovery ring/tab/body route and validated
support representation, not a new platform or automatically thicker hardware.
