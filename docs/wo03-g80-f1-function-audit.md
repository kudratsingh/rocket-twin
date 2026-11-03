# Dedicated fixed G80 function audit — G80-F1 intake

**Inventory and architecture input only.** The owner has prioritized a simplified, dedicated fixed G80 construction over physical aft-module interchangeability. `G80-F1` here is a **provisional new study identity**, separate from the frozen earlier C1 mass/balance and C1 attachment records. No geometry, material, mass credit, active configuration, recovery load path, allowable, or launch baseline is selected by this note. The primary agent owns the construction and force decisions. This audit reads existing sources only; it ran no CAD, FEA, heat, simulator, flight, browser or GitHub action. The [A1 accounting and section map](wo03-a2-mass-allocation.md) and A1 failures remain historical evidence, not a G80-F1 design.

## Frozen A1 source and functional buckets

The [A1 resolved 90-row record](../runs/wo03-a1-bookkeeping-20261102-v1/record.json), SHA-256 `0810730990b5b7a6d8860ec6107c8358574d75be7d8f378e38677b1fa0114070`, is the complete **reference inventory**, not the mass of G80-F1. Its 90 rows total **1024.762435194 g** and point first moment **0.855746150448 kg·m**. Separate 50 g at z1227 mm brings the historical nominal to **1074.762435194 g** and **0.917096150448 kg·m**. The +20 g adverse aft/motor-CG probe is a separate case, not a physical accounting row or an assigned station. Full intrinsic inertia and a newly validated CP remain unavailable. These are all A1 values. The four mutually exclusive buckets below are functional *review labels*, not deletion instructions or a new vehicle mass calculation.

| Function bucket | Source rows | A1 booked mass (g) | Interpretation |
| --- | ---: | ---: | --- |
| Essential to a conventional fixed G80 function | 29 | 545.464691354 | Nose/body, guide interface, fin/can/root path, motor and retention/thermal functions. The specific A1 materials, layer stack and thrust seat are **not** therefore selected for G80-F1. |
| Useful instrumentation and recovery | 41 | 313.568121067 | Canopy, harness/attachments, independent recovery power and controller, sensed flight instrumentation and main avionics. Physical routing and exact installed hardware remain open. |
| Future interchangeability or A1 removable-joint implementation | 14 | 128.729622773 | Sleeve, collar, indexed stop, M5 joint, bond/process, module extraction slack/edge protection, index/lock allocation. A fixed construction may need different continuous tube, lap, supports and recovery paths; this entire number is **not** available as a saving. |
| Unresolved or potentially overlapping support reserves | 6 | 37.000000000 | Thermal, service, finish, chafe and guide-conversion allowances whose physical functions must be resolved before any row is replaced. They remain charged in A1. |
| **All A1 rows** | **90** | **1024.762435194** | No row omitted or credited. Separate 50/20 cases stay outside these buckets. |

The complete 90-row ID, source mass, station and function-class transcription is below. Every ID appears once. The [A1 decision](wo03-a1-connection-decision.md) and [ledger audit](wo03-a1-ledger-audit.md) explain the failed complete mass, bolt, paper/body, root and seat checks. A1 had **14.059073 m/s** nominal and **13.912018 m/s** adverse on the unchanged 1.5 m reference, both below formal 15 m/s; the new construction needs its own complete mass/CG, CP, drag and guide evaluation.

## Function changes worth considering, with no credit yet

| Candidate function change | Exact A1 charged IDs and mass (g) | Required replacement before any credit |
| --- | --- | --- |
| Remove the physical *modular service split* by using a dedicated fixed body/joint | `A1_G11_sleeve` 43.519855; `A1_integral_stop` 1.955371; `A1_integral_keys` 0.414400; `A1_outer_G11_load_collar` 23.852228; `A1_three_curved_inner_doublers` 8.325000; `A1_three_M5_complete_sets` 20.616715; fitted spacers 0.075933; upper bond/process 16.861305; collar bond 1.372625; doubler process 3; joint process 3; `S3_index_marks_service_locks` 2; A1 service slack 1.736191; edge protection 2. **Together: 128.729623 booked.** | A named continuous body/support, actual motor/fin thrust and torsion transfer, recovery attachment, assembly access, heat protection and any permanent lap/bond/fasteners. The 43.5 g sleeve and 16.9 g upper bond do real structural work in A1; a fixed airframe cannot simply delete them. The A1 collar/M5/paper route failed; dropping it does not establish a new path. |
| Replace complex sandwich fins with simpler solid plywood TTW fins | Nine `A_fin_*` panel, core, dense root, skin and bond rows total **108.085600**; `A_root_and_ring_bonds` 20.000000, toe/heel stops 12.708945 and rings 24.806317 are **separate** functions. | Full three-fin stock and through-wall tabs, root contact/adhesive/fillets, ring/tube load transfer, fin axial/radial capture, stiffness, flutter and hot/wet strength. The 3–4 mm suggestion has no current installed-root validation; 6.35 mm was the saved solid plywood study thickness. |
| Simplify the aft recovery and motor-support arrangement | `A_fore_recovery_cap` 30.687077, `A_integral_fore_cuff` 14.553114, `A_three_integral_recovery_saddles` 3.985833, `A_cap_cuff_bond` 5, `A1_routed_three_bridles` 15.056089, `S3_connector` 12, backbone extra 9.842520. **Together: 91.124633 booked.** | Direct, independent canopy/cord, nose, forward body/avionics, aft body/fin/motor retention and thermal paths with actual loops, terminations and protection. A motor-tube or TTW-fin anchor is a *possible topology*, not a rated eye or proven transfer into the shell/fin stock. The 12 g connector is a recovery candidate; a dedicated design might use a different continuous tether, but its replacement mass and installation must be stated. |
| Resolve reserves without hiding hardware | `A_body_and_retainer_service_hardware` 6, `A_finish_and_locks` 8, `A_added_thermal_isolation` 6, `S3_additional_thermal_protection` 6, `S3_future_rail_button_conversion_extra` 5, `A_harness_chafe_stitch_reserve` 6. **Together: 37 g booked.** | Identify real installed hardware/process, exact thermal layers, guide choice and protection. Some functions may coincide in a new design but none is duplicate by arithmetic alone. Source `rail_guides` 0.622999 g is separate from the 5 g future-button reserve and remains in the 90-row ledger. |

The fixed-motor core should keep the full **128.2 g motor** once, a physical thrust/reverse-retention chain, liner/shield/pads or verified replacements, three passive fins with sound root transfer, a positively retained nose/recovery package, guide attachment, and independent recovery power/control. The main `flight_computer`, IMU, high-g accelerometer and barometer are useful recorded-flight/controls instrumentation; the source avionics sled is only 9.044606 g, so simplification should be driven by packaging and access rather than assuming its removal saves a large amount. The independent EasyMini assembly and cell/switch/wiring are separate from the main flight-computer battery; no shared-power credit is assumed. See [common upper](../configs/vehicle/platform/common-upper.yaml) and the [recovery package](wo03-recovery-package.md).

## Existing lightweight source starting points, not an adopted hybrid

| Function | Reusable source dimensions and evidence limit |
| --- | --- |
| Body and nose | The current shared upper has a 66 mm OD / 65 mm ID, 0.5 mm wall kraft tube at z140–918, 56.032347 g in A1, and an ASA ogive nose at z0–140 with 30 mm shoulder. The old `performance.yaml` aft shell is also a thin paper-body precedent; a dedicated continuous body stock/cut/join scheme, length, seam and attachments must be selected and weighed. A plain kraft tube alone has no proven recovery or fin-root capacity. |
| Fixed 29 mm motor support | [Performance spec](../configs/vehicle/platform/performance.yaml) has a plywood fixed `motor_mount` at z1010–1200, with three 3 mm rings at local z0/90/167, 12×7 mm rails, channels, a 29 mm-class commercial motor and TTW slots; [installed-fin intake](wo03-g80-installed-fin-intake.md) describes its source geometry and open root findings. This is an existing construction precedent, not a passed mount. A1 separately has a 33.295479 g G11 structural tube z1069–1193, R15.8–17.2, with ring centers z1072/1192 and 0.3 mm nominal adhesive gaps; its thrust seat overlaps retained mica/foil per the [A1 occupancy audit](wo03-a1-occupancy-audit.md). A conventional lighter **29 mm motor tube plus two or three centering rings** is a reasonable next source search and construction study, but no exact lighter tube supplier, mass, wall, heat capability or root joint was found in the active inventory. It needs positive thrust/reverse and recovery attachment before selection. |
| Plywood fins | The original fixed spec uses three **6.35 mm** aircraft-birch plywood rectangular TTW fins, 120 mm root and tip, 70 mm span, with six small gussets; its historical CAD-derived fin set is 131.624 g. The [swept C1 screen](wo03-g80-mass-balance-revision.md) used **120 mm root, 90 mm span, 60 mm tip, 40 mm sweep** at z1080 and retained 6.35 mm thickness, moving modeled CP aft at the cost of higher factored fin force/moment (220.759 N / 8.830 N·m). A 3–4 mm solid-plywood variant is a **new** thickness/root/flutter candidate, not a mass or strength transfer; [fin design inputs](../configs/studies/wo03-fin-design.yaml) themselves label thinner-property transfers unsupported. |
| Motor source | The active performance spec pins provisional AeroTech G80-10T SKU78010 to [`AeroTech_G80_2007_published.eng`](../configs/studies/rebaseline/motors/AeroTech_G80_2007_published.eng) and [sidecar](../configs/studies/rebaseline/motors/AeroTech_G80_2007_published.yaml): assembled source 128.2 g, 29×128 mm envelope, 62.5 g propellant, curve 133.243510 N·s over 1.8079 s, 73.700708 N average. The [exact-motor comparison](wo03-launch-guide-motor-trade.md) records a sold-product 127.9 g/124 mm casing claim and 136.6 N·s/77.6 N certificate summary. Casing length versus full envelope, current polymer case/nozzle, source curve, lot, delay and California status need exact reconciliation before hardware/thermal selection. Do not mix curve and catalog values or borrow G54/G12 mounts. |

## Required screens and starter budget boundaries

The [engineering input](../configs/engineering/wo03.yaml) at lines 149–164 defines DF3 and prescribed recovery speeds **5 m/s** (nominal screen) and **20.4 m/s** (archived late-G80-delay off-nominal probe), with **0.3 m** and 0.6 m assumed stopping distances. The [recovery-load assumptions](wo03-recovery-load-assumptions.md) at lines 3, 9–18, 24–29 explicitly retain the **20.4 m/s, 0.3 m, DF3** case, applying the factor once to `m × (v²/(2s) + 9.80665)` and retaining the older **1,782.253 N** result as a study floor. That force came from the older complete **844.582 g** loaded sensitivity, including 50 g growth; it is a **model result**, not a universal force independent of mass. For comparison, the later A1 executed complete cases give **2267.985132 N** nominal and **2310.189531 N** with adverse +20 g, already DF3 factored; those too are A1-specific model results. The 20.4 m/s input is **not** a measured opening speed or approved delay; 0.3 m is **not** measured payout; DF3 does not model peak snatch. A new complete G80-F1 mass and justified participating free bodies must eventually recalculate the same required case while preserving the documented floor and all physical uncertainty. Do not double factor or lower it using the 0.6 m sensitivity.

The [guide/motor trade](wo03-launch-guide-motor-trade.md) at lines 59–69 preserves **1.5 m usable guide**, formal **15 m/s**, separate **15.5 m/s planning**, full **50 g** growth, thrust×0.85, 0.5 N friction, Cd0.8 and a 66 mm reference diameter. Its G80 source-model ceilings at 1.5 m are **958.398 g total** for 15 m/s and **903.854 g total** for 15.5 m/s (lines 129–133), conditional on unchanged model inputs. These are complete loaded-mass roots, not allowable dry-structure weights or approximately 1 kg universal limits. A new aero envelope, guide/button geometry, exact motor, mass/CG, full inertia and static CP require same-identity reassessment. The strict physical class limit remains <1500 g, but a larger class budget clears no guide or other gate. No actual club equipment, usable travel or longer baseline is confirmed.

| Starter ledger account | Source A1 amount | G80-F1 status |
| --- | ---: | --- |
| All 90 identified source functions, including explicit process/reserves | 1024.762435194 g | Inventory to map, **not** candidate mass. Each selected new part needs new positive mass/station; a removed row needs exact `replaces_id` and a replaced function. |
| Full separate aft growth | +50 g at z1227 in A1 | Keep whole as a separate new-design allowance; later choose conservative placement on the complete new geometry. Do not spend it on known hardware. |
| Additional adverse mass/motor-CG probe | +20 g plus inherited motor-CG sensitivity | Keep separate from nominal and growth. Do not assign an invented physical station. |
| Fixed-G80 architecture replacements | Unknown | Body, fin, mount, recovery, avionics/guide and process selections are pending. **No new vehicle total or deletion credit is calculated here.** |

Next bounded deliverable: the primary selects one continuous fixed construction and explicit nose/upper/aft/motor recovery attachment topology. Only then write a signed exact-ID replacement ledger with stock dimensions, mass/station, process, unchanged full allowance and both mass cases; check complete body/fin/thermal/recovery paths and reference guide/static margins on that one identity. Stop before CAD/FEA or simulator acceptance if real stock, motor envelope, installed root, independent recovery path or complete mass cannot be defined. G54 and G12 remain separate committed configurations; this fixed G80 inventory does not close their shared interfaces or WO-03.

## Full A1 source row transcription

The following values are read from the immutable A1 bookkeeping JSON. The function bucket is this audit's classification; mass and station are the source's point-bookkeeping values. Long parts, distributed budgets and soft goods must not be split by point station to infer force sharing.

| A1 source ID | Mass (g) | Point station (mm) | Point first moment (kg·m) | Function bucket |
| --- | ---: | ---: | ---: | --- |
| `A1_G11_sleeve` | 43.519855 | 902.000 | 0.039254908950 | interchange |
| `A1_additional_joint_process_mass_g` | 3.000000 | 952.000 | 0.002856000000 | interchange |
| `A1_centering_ring_0` | 12.403159 | 1072.000 | 0.013296186012 | fixed |
| `A1_centering_ring_1` | 12.403159 | 1192.000 | 0.014784565043 | fixed |
| `A1_collar_bond` | 1.372625 | 952.000 | 0.001306738678 | interchange |
| `A1_collar_doubler_bond_g` | 3.000000 | 952.000 | 0.002856000000 | interchange |
| `A1_extra_service_slack` | 1.736191 | 930.000 | 0.001614657879 | interchange |
| `A1_fitted_crush_spacers` | 0.075933 | 952.000 | 0.000072288292 | interchange |
| `A1_harness_edge_protection` | 2.000000 | 962.000 | 0.001924000000 | interchange |
| `A1_integral_keys` | 0.414400 | 932.000 | 0.000386220800 | interchange |
| `A1_integral_stop` | 1.955371 | 920.000 | 0.001798941550 | interchange |
| `A1_motor_thrust_seat` | 0.961063 | 1194.000 | 0.001147509769 | fixed |
| `A1_outer_G11_load_collar` | 23.852228 | 952.000 | 0.022707321116 | interchange |
| `A1_routed_three_bridles` | 15.056089 | 960.000 | 0.014453845755 | instrument/recovery |
| `A1_shortened_motor_tube` | 33.295479 | 1131.000 | 0.037657186284 | fixed |
| `A1_three_M5_complete_sets` | 20.616715 | 952.000 | 0.019627112657 | interchange |
| `A1_three_curved_inner_doublers` | 8.325000 | 952.000 | 0.007925400000 | interchange |
| `A1_three_fin_heel_stops` | 0.373792 | 1190.250 | 0.000444906523 | fixed |
| `A1_three_fin_toe_stops` | 12.335153 | 1081.750 | 0.013343551217 | fixed |
| `A1_upper_bond_and_process` | 16.861305 | 880.000 | 0.014837948191 | interchange |
| `A_added_thermal_isolation` | 6.000000 | 1140.000 | 0.006840000000 | unresolved reserve |
| `A_body_and_retainer_service_hardware` | 6.000000 | 1140.000 | 0.006840000000 | unresolved reserve |
| `A_cap_cuff_bond` | 5.000000 | 1030.000 | 0.005150000000 | instrument/recovery |
| `A_fin_PVC_core` | 12.480000 | 1145.100 | 0.014290844444 | fixed |
| `A_fin_carbon_panel` | 35.964000 | 1144.444 | 0.041158800000 | fixed |
| `A_fin_carbon_tab` | 7.015200 | 1140.000 | 0.007997328000 | fixed |
| `A_fin_dense_root_band` | 20.020000 | 1140.550 | 0.022833816296 | fixed |
| `A_fin_dense_through_body_tabs` | 27.112800 | 1140.000 | 0.030908592000 | fixed |
| `A_fin_edge_finish` | 2.000000 | 1144.444 | 0.002288888889 | fixed |
| `A_fin_face_bond_panel` | 2.673000 | 1144.444 | 0.003059100000 | fixed |
| `A_fin_face_bond_tab` | 0.521400 | 1140.000 | 0.000594396000 | fixed |
| `A_fin_root_band_core_butt_bonds` | 0.299200 | 1140.550 | 0.000341252639 | fixed |
| `A_finish_and_locks` | 8.000000 | 1140.000 | 0.009120000000 | unresolved reserve |
| `A_fore_recovery_cap` | 30.687077 | 1007.000 | 0.030901886580 | instrument/recovery |
| `A_harness_chafe_stitch_reserve` | 6.000000 | 1030.000 | 0.006180000000 | unresolved reserve |
| `A_independent_threaded_retainer` | 20.000000 | 1210.000 | 0.024200000000 | fixed |
| `A_integral_fore_cuff` | 14.553114 | 1030.000 | 0.014989707223 | instrument/recovery |
| `A_loadbearing_outer_can` | 87.913826 | 1067.000 | 0.093804052516 | fixed |
| `A_retainer_adapter_and_bond` | 5.000000 | 1198.000 | 0.005990000000 | fixed |
| `A_root_and_ring_bonds` | 20.000000 | 1140.000 | 0.022800000000 | fixed |
| `A_three_integral_recovery_saddles` | 3.985833 | 1012.546 | 0.004035841016 | instrument/recovery |
| `S3_additional_thermal_protection` | 6.000000 | 1140.000 | 0.006840000000 | unresolved reserve |
| `S3_connector` | 12.000000 | 900.000 | 0.010800000000 | instrument/recovery |
| `S3_future_rail_button_conversion_extra` | 5.000000 | 346.000 | 0.001730000000 | unresolved reserve |
| `S3_index_marks_service_locks` | 2.000000 | 1100.000 | 0.002200000000 | interchange |
| `S3_tail_fairing` | 2.500000 | 1213.500 | 0.003033750000 | fixed |
| `S3_wire_strain_relief_clearance` | 1.000000 | 1000.000 | 0.001000000000 | instrument/recovery |
| `aft_thrust_pads` | 0.299329 | 1201.500 | 0.000359644248 | fixed |
| `arming_switch` | 3.000000 | 441.000 | 0.001323000000 | instrument/recovery |
| `avionics_bay` | 9.044606 | 345.000 | 0.003120388964 | instrument/recovery |
| `baro` | 1.000000 | 325.500 | 0.000325500000 | instrument/recovery |
| `battery` | 30.000000 | 272.500 | 0.008175000000 | instrument/recovery |
| `body_upper` | 56.032347 | 529.074 | 0.029645234721 | fixed |
| `canopy_line_connector_sensitivity` | 5.000000 | 177.500 | 0.000887500000 | instrument/recovery |
| `flight_computer` | 12.000000 | 275.500 | 0.003306000000 | instrument/recovery |
| `harness` | 12.000000 | 385.000 | 0.004620000000 | instrument/recovery |
| `high_g_accel` | 1.000000 | 357.800 | 0.000357800000 | instrument/recovery |
| `imu` | 2.000000 | 325.000 | 0.000650000000 | instrument/recovery |
| `independent_recovery` | 3.000000 | 399.050 | 0.001197150000 | instrument/recovery |
| `micro_sd` | 3.000000 | 415.000 | 0.001245000000 | instrument/recovery |
| `motor` | 128.200000 | 1136.000 | 0.145635200000 | fixed |
| `motor_liner` | 10.065964 | 1136.000 | 0.011434935621 | fixed |
| `motor_radiant_shield` | 0.656218 | 1136.000 | 0.000745463516 | fixed |
| `nose_cone` | 33.017274 | 105.074 | 0.003469273144 | fixed |
| `parachute` | 51.600000 | 177.500 | 0.009159000000 | instrument/recovery |
| `pyro_mosfet` | 3.000000 | 440.000 | 0.001320000000 | instrument/recovery |
| `rail_guides` | 0.622999 | 346.000 | 0.000215557711 | fixed |
| `recovery_anchor` | 4.000000 | 221.159 | 0.000884635771 | instrument/recovery |
| `recovery_backbone_extra_mass` | 9.842520 | 947.500 | 0.009325787402 | instrument/recovery |
| `recovery_battery` | 3.600000 | 348.000 | 0.001252800000 | instrument/recovery |
| `recovery_battery_band` | 0.350000 | 337.000 | 0.000117950000 | instrument/recovery |
| `recovery_battery_tray` | 0.663667 | 348.215 | 0.000231099135 | instrument/recovery |
| `recovery_bulkhead` | 30.233745 | 227.500 | 0.006878177038 | instrument/recovery |
| `recovery_easymini_components` | 3.500000 | 399.050 | 0.001396675000 | instrument/recovery |
| `recovery_fasteners` | 0.683259 | 399.050 | 0.000272654385 | instrument/recovery |
| `recovery_mount_carrier` | 4.297337 | 378.542 | 0.001626722912 | instrument/recovery |
| `recovery_mount_hardware_allowance` | 3.139322 | 376.000 | 0.001180384973 | instrument/recovery |
| `recovery_nuts` | 0.245171 | 399.050 | 0.000097835508 | instrument/recovery |
| `recovery_output_harness` | 4.000000 | 420.000 | 0.001680000000 | instrument/recovery |
| `recovery_power_switch` | 3.700000 | 470.000 | 0.001739000000 | instrument/recovery |
| `recovery_protection` | 6.000000 | 210.000 | 0.001260000000 | instrument/recovery |
| `recovery_sled_fasteners` | 0.635786 | 390.333 | 0.000248168506 | instrument/recovery |
| `recovery_sled_nuts` | 0.194476 | 390.333 | 0.000075910544 | instrument/recovery |
| `recovery_sled_reinforcement` | 0.371349 | 390.333 | 0.000144949780 | instrument/recovery |
| `recovery_standoffs` | 0.106651 | 399.050 | 0.000042558997 | instrument/recovery |
| `recovery_switch_g11_doubler` | 2.078119 | 470.000 | 0.000976716154 | instrument/recovery |
| `regulator_5v` | 8.000000 | 417.500 | 0.003340000000 | instrument/recovery |
| `service_port_covers` | 1.000000 | 1118.500 | 0.001118500000 | fixed |
| `shock_cord` | 10.000000 | 212.000 | 0.002120000000 | instrument/recovery |
| `thrust_pads` | 0.299329 | 1070.500 | 0.000320432100 | fixed |
