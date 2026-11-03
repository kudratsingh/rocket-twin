# A1 connection packet: independent A ledger and retained-upper audit

**Bookkeeping only, 2026-11-02.** This read-only audit uses the frozen A/B record and source part allocation. It selects no A1 geometry, hardware, mass or allowable and executes no CAD, FEA, thermal, guide or flight calculation. A remains a preferred bounded connection direction, not an admitted construction. The current G80 fixed-motor package is first; G54 and G12 require their own evidence. The full separate 50 g growth remains additional in every complete case.

## Source identities and accounting boundary

| Source | Role / frozen identity |
| --- | --- |
| [`runs/wo03-architecture-space-mass-20261102-v1/record.json`](../runs/wo03-architecture-space-mass-20261102-v1/record.json) | Executed A/B result, SHA-256 `7f4a0262a7ed5be0427bb7a1fe22c8870697014a6f2c807032091561511a82d2`; A `replacement_ledger` is the signed authoritative A delta. Its executed config and script are alongside the record. |
| [`configs/studies/wo03-architecture-space-mass.yaml`](../configs/studies/wo03-architecture-space-mass.yaml) | A/B study input; executed hash `336d79130931012710155ab8777cfe439afddf51f3b1c688637d41b8e90ce137`. Current file was not edited. |
| [`web/public/engineering-workbench/g80-c1.json`](../web/public/engineering-workbench/g80-c1.json) | Frozen 135-row C1 source allocation, mass and point-mass stations; executed hash `1481b5fb7f18b8fa39aea5aa2db0491d6828da28eccf3729f81abf550eaf288f`. These are not measured manufactured parts. |
| [`runs/wo03-g80-mass-balance-revision-20261102-v2/record.json`](../runs/wo03-g80-mass-balance-revision-20261102-v2/record.json) | C1 mass scenarios; executed hash `a22dc418ea4fdfb9d91f145180a0e1024f53d3b51b3d61d7d1c18b82fb960276`. |
| [`runs/wo03-c2-sandwich-socket-20261102-v2/record.json`](../runs/wo03-c2-sandwich-socket-20261102-v2/record.json) | Saved fin panel/core/skin mass basis only; executed hash `c67d16a49378e6b462bec66c689c414750cf5e9a61f4524785d0ffa198e2eac3`. C2 construction remains stopped. |
| [`configs/vehicle/platform/common-upper.yaml`](../configs/vehicle/platform/common-upper.yaml), [`configs/vehicle/platform/performance.yaml`](../configs/vehicle/platform/performance.yaml), [`src/cad/parts.py`](../src/cad/parts.py) | Source model for upper tube, coupler, stop/keys and aft hardware. Their current values below are model intent, not manufactured fit. |

The point-mass first moment uses nose-origin station `z` in mm: `M [kg·m] = mass [g] × z [mm] × 10^-6`. The source C1 subtotal is 1,079.806751 g and 0.932651621 kg·m. A removes 83 *identified* C1 rows, 561.440696 g and 0.617284717 kg·m; retains 52 rows, 518.366055 g and 0.315366904 kg·m; and adds 26 new rows, 399.942808 g and 0.440876825 kg·m. Thus the A subtotal is 918.308863 g and 0.756243729 kg·m. The **separate** 50 g at z1227 mm adds 0.061350000 kg·m, giving A nominal 968.308863 g and 0.817593729 kg·m. This agrees with the frozen A case at displayed precision. The specified adverse 20 g and motor-CG probe are separate case inputs, not part of this physical delta table. Full intrinsic inertia remains unavailable.

The full 109-line signed ledger below is transcribed from the immutable A `replacement_ledger`; its negative IDs correspond one-to-one to `removed_part_ids`. The source record retains the full function/basis text. No old C1 removal may be credited a second time in A1.

## Retained-upper source interface

| Source ID | Source model and accounting | A1 consequence |
| --- | --- | --- |
| `body_upper` | Cardboard tube z140–918 mm, R32.5–33.0 mm; 56.032347 g, point-mass z529.073585 mm. Retained in A. | Any local body spreader, doubler, bond or new hole/fastener needs a positive row or an identified replacement. Do not remove the entire upper tube to claim a local change. |
| `interface_coupler` | Cardboard keyed tube z868–972 mm, R30.5–32.0 mm; 21.067330 g, z919.733683 mm. Upper overlap is z868–918 (50 mm). The source model gives slots at local z54–80, hence z922–948, widths 6/4/4 mm, depth 3 mm, at 0/120/240°. Retained in A. | A bore R32.2 mm begins at z922 and overlaps the coupler to z972. The audited ±0.1 mm per-radial-surface stack gives 0 mm minimum gap against required 0.1 mm. Coupler, keyed cuts, bond and actual manufactured bounds must be resolved explicitly. |
| `joint_stop` | ASA indexing kit, 1.319255 g at z923.410522 mm, nominal envelope z918–947 and R33.2 mm. CAD generator makes a **4 mm annular flange at z918–922** plus three separate 25 mm key boxes at z922–947, centered at radius 31.6 mm with 1 mm radial depth, widths 5.2/3.2/3.2 mm, at 0/120/240°. Retained in A. | Do not model the whole z918–947/R33.2 envelope as a solid ring. Key corners, slots, orientation, adhesive and the mating A can require an actual local fit check. The kit locates shells; source text expressly excludes structural axial retention. |
| `aft_interface_hardware` | Source performance-mode 6 g allocation at z941 mm, envelope z935–947; positive retention/indexing/removable fastener function, with no specific bolt geometry. Retained in A. | A1 bolts/locks cannot silently be added or credited against this row; specify whether hardware is distinct, replaces this allocation, or is still unresolved. Parent is the removed `aft_shell`, so the revised attachment identity also needs repair before a resolved assembly. |

The current A concept charges `A_loadbearing_outer_can` at R32.2–33.0, z922–1212 (87.913826 g) and `A_body_and_retainer_service_hardware` 6 g at z1140. These do not prove a coupler sleeve, keyed engagement, radial/bearing support, axial capture, upper-body spreader or bolt pattern. The cold-fit blocker in [`wo03-architecture-interface-audit.md`](wo03-architecture-interface-audit.md) remains. Source tolerance fields are estimates, not measured stack bounds. Thermal, moisture, insertion and service fit are unknown.

The frozen A/B packet also reserves the **motor/liner radius R15.8 mm over z1069–1195** and an independently removable **retainer/service radius R23 mm over z1195–1227**. Both are concept envelopes; the exact current G80 and Estes retainer dimensions are unverified. Three recovery-leg axes are 60/180/300° at radial centre 24 mm, tangential offsets ±6 mm, 12.7 mm radial web width and 0.55 mm tangential thickness over z900–1016. The stated 0.5 mm motion, 0.2 mm manufacturing and 0.1 mm required gap stay separate. Actual cuff windows over z1010–1018 span ±30° about those axes and must remain open. A1 sleeve, bolts, adhesive, spreaders and service tools must not occupy these reservations without a checked compatible route. The source A mass gives no machining credit for the windows or fin slots.

## Coverage and double-count traps for A1

| Function | Already counted in A | What A1 must identify before a mass credit or acceptance claim |
| --- | --- | --- |
| Upper coupler, stop/key, positive retention | Retained `interface_coupler` 21.067330 g, `joint_stop` 1.319255 g, `aft_interface_hardware` 6 g; A can 87.913826 g and A body/retainer service hardware 6 g. | A selected sleeve/spreader/bolt/key modification gets a named positive mass and station. Credit only the exact old ID and portion it actually replaces. If old coupler/stop stays, it stays charged. Finite axial, torsional, bending and reverse-load paths remain unproved. |
| Body spreading and local reinforcement | Retained `body_upper` 56.032347 g; A `A_fore_recovery_cap` 30.687077 g, `A_integral_fore_cuff` 14.553114 g, `A_cap_cuff_bond` 5 g. | Those A parts are forward recovery/cuff functions at z1004–1050, not evidence for the retained-upper modular joint at z918–972. A new local spreader/bond/fastener must be charged and fit checked. |
| Fin roots, rings and bonds | A dense band/tabs, skins/core and their face/butt/edge bonds, `A_structural_motor_tube` 33.832502 g, two `A_centering_ring_*` 12.919957 g each, `A_root_and_ring_bonds` 20 g, `A_root_axial_pins_and_washers` 4 g. Old C1 fin/pin/socket/bond allocations were removed exactly once. | A1 root or ring redesign replaces its own named A row(s), with any new joint stock, process resin, axial capture and local fasteners charged. A 20 g allocation is neither measured bond mass nor qualified peel capacity. |
| Motor service, adapter and protection | Retained `motor` 128.2 g, `motor_liner` 10.065964 g, `motor_radiant_shield` 0.656220 g, `thrust_pads` and `aft_thrust_pads` 0.299329 g each, `S3_additional_thermal_protection` 6 g; A `A_independent_threaded_retainer` 20 g, `A_retainer_adapter_and_bond` 5 g, `A_added_thermal_isolation` 6 g, plus the 6 g A service-hardware allocation. | All bought-part geometry/mass and exact G80/retainer mating remain unknown. If a new tube/adapter changes motor shoulder or pad function, replace the exact affected row. Do not transfer old end-cap/motor-arm credits or omit service sweep, heatshield, liner or process mass. |
| Recovery and harness | Retained `S3_connector` 12 g at z900 (Wichard 21223 *candidate* recovery connector), `recovery_backbone_extra_mass` 9.842520 g, upper shock cord/anchor/protection/electronics/battery; A three forward eyes 15.044942 g, integral saddles 3.985833 g and chafe/stitch reserve 6 g. | The 12 g connector is a recovery item, not a modular sleeve. Local terminations, sewn/bend hot strength and routing remain unknown. New A1 joint hardware cannot take recovery mass credit without a real changed function. |
| Guide and finishes | Retained original `rail_guides` 0.622999 g **and** separate `S3_future_rail_button_conversion_extra` 5 g; retained `S3_index_marks_service_locks` 2 g and `S3_wire_strain_relief_clearance` 1 g; A `A_finish_and_locks` 8 g and root/ring/cuff bonds as above. | Actual guide/button equipment and mass remain unconfirmed. Avoid a second button reserve or deleting the old rod-lug mass without a selected installed replacement. A1 machining/sealant/adhesive/wire process rows must be distinguished from existing allowances. |

The retained `S3_connector` and `S3_future_rail_button_conversion_extra` are planning allocations, not evidence of selected physical geometry. The A retainer 20 g and adapter 5 g are estimates, not supplier mass or fit. The 50 g separate allowance is never a fund from which to erase known hardware.

## A1 delta-ledger contract for the connection study

1. Start with the immutable A case. Record source `record.json` SHA-256 above and a new packet ID. Preserve all 52 retained C1 IDs, all 26 A-added IDs, and the separate 50 g unless an exact `replaces_id`/`replaced_function` is stated. Never replay the 83 old C1 removals as A1 credits.
2. For each changed row, provide `{id, action: retain|replace|add, replaces_id, function, material_or_supplier, geometry_source, mass_g, station_mm, mass_basis, uncertainty_or_bound, mode_scope, fit_status}`. An `action: replace` records a **negative** line for the old complete identified row (or a justified fraction with its explicit function split) and a positive line for the new row. A simple addition has no negative credit. Keep mass and station on the same row; `first_moment_kg_m = mass_g × station_mm × 10^-6` with signed mass.
3. Name the actual upper/can connection chain and mating surfaces: coupler/keys/stop, A can sleeve/body spreader, load-bearing bonds, positive fasteners/retention, recovery body transfer and service access. Mark missing dimensions, purchased tolerances, hot/wet properties, bond thickness, fastener capture and resulting installed mass `unknown`; do not enter zero.
4. Sum `A1_subtotal = 918.308863 g + Σ(A1 signed mass deltas)`. Add 50 g at z1227 separately, and keep the additional 20 g/motor-CG adverse case separate. Recompute corresponding first moments from the same rows, then only perform later required static/guide/recovery checks within the primary packet's declared budget. The unchanged 1.5 m usable baseline, formal 15 m/s, separate 15.5 planning and full separate 50 g remain. Conditional longer-guide outputs cannot revise the baseline.
5. If a joint design cannot state a finite installed load path, complete mass/CG, cold/hot fit or protected-space clearance, stop at that missing fact. This audit provides no engineering selection, no hot allowable, and no permission for detailed CAD/FEA or changed active specifications.

## Signed A replacement ledger (source record transcription)

Values below are ledger point masses. `moment` is signed kg·m at the row's nose-origin station; it is bookkeeping, not intrinsic inertia. Each removed row's `remove_` prefix identifies its frozen C1 source ID. Positive rows are the A additions, including named estimates and process allocations.

| Signed ledger ID | Mass delta (g) | Station (mm) | Moment delta (kg·m) |
| --- | ---: | ---: | ---: |
| `remove_C1_aft_cap_15p8_bore` | -27.003233 | 1214.800 | -0.032803527 |
| `remove_C1_captive_motor_keeper` | -3.000000 | 1205.000 | -0.003615000 |
| `remove_C1_closed_G11_body_annulus` | -59.299336 | 1110.900 | -0.065875632 |
| `remove_C1_fin_socket_floor_1` | -4.051500 | 1140.000 | -0.004618710 |
| `remove_C1_fin_socket_floor_2` | -4.051500 | 1140.000 | -0.004618710 |
| `remove_C1_fin_socket_floor_3` | -4.051500 | 1140.000 | -0.004618710 |
| `remove_C1_fin_socket_outer_bridge_1` | -0.740000 | 1140.000 | -0.000843600 |
| `remove_C1_fin_socket_outer_bridge_2` | -0.740000 | 1140.000 | -0.000843600 |
| `remove_C1_fin_socket_outer_bridge_3` | -0.740000 | 1140.000 | -0.000843600 |
| `remove_C1_fin_socket_outer_bridge_4` | -0.740000 | 1140.000 | -0.000843600 |
| `remove_C1_fin_socket_outer_bridge_5` | -0.740000 | 1140.000 | -0.000843600 |
| `remove_C1_fin_socket_outer_bridge_6` | -0.740000 | 1140.000 | -0.000843600 |
| `remove_C1_fin_socket_side_plate_1` | -4.440000 | 1140.000 | -0.005061600 |
| `remove_C1_fin_socket_side_plate_2` | -4.440000 | 1140.000 | -0.005061600 |
| `remove_C1_fin_socket_side_plate_3` | -4.440000 | 1140.000 | -0.005061600 |
| `remove_C1_fin_socket_side_plate_4` | -4.440000 | 1140.000 | -0.005061600 |
| `remove_C1_fin_socket_side_plate_5` | -4.440000 | 1140.000 | -0.005061600 |
| `remove_C1_fin_socket_side_plate_6` | -4.440000 | 1140.000 | -0.005061600 |
| `remove_C1_forward_motor_key_carrier_1` | -4.000000 | 1057.000 | -0.004228000 |
| `remove_C1_forward_motor_key_carrier_2` | -4.000000 | 1057.000 | -0.004228000 |
| `remove_C1_forward_motor_key_carrier_3` | -4.000000 | 1057.000 | -0.004228000 |
| `remove_C1_independent_motor_retainer_arm_1` | -0.893772 | 1205.000 | -0.001076995 |
| `remove_C1_independent_motor_retainer_arm_2` | -0.893772 | 1205.000 | -0.001076995 |
| `remove_C1_independent_motor_retainer_arm_3` | -0.893772 | 1205.000 | -0.001076995 |
| `remove_C1_integral_end_hardpoint_0_1` | -4.166667 | 1024.000 | -0.004266667 |
| `remove_C1_integral_end_hardpoint_0_2` | -4.166667 | 1024.000 | -0.004266667 |
| `remove_C1_integral_end_hardpoint_0_3` | -4.166667 | 1024.000 | -0.004266667 |
| `remove_C1_integral_end_hardpoint_1_1` | -4.166667 | 1203.800 | -0.005015833 |
| `remove_C1_integral_end_hardpoint_1_2` | -4.166667 | 1203.800 | -0.005015833 |
| `remove_C1_integral_end_hardpoint_1_3` | -4.166667 | 1203.800 | -0.005015833 |
| `remove_C1_radial_mount_pad_1` | -1.823175 | 1140.000 | -0.002078419 |
| `remove_C1_radial_mount_pad_2` | -1.823175 | 1140.000 | -0.002078419 |
| `remove_C1_radial_mount_pad_3` | -1.823175 | 1140.000 | -0.002078419 |
| `remove_C1_socket_joint_process_hardware` | -8.000000 | 1110.000 | -0.008880000 |
| `remove_S3_end_contact_shims` | -1.000000 | 1111.000 | -0.001111000 |
| `remove_S3_fin_channel_selected_shims` | -4.000000 | 1140.000 | -0.004560000 |
| `remove_S3_loop_keepers_chafe_and_stitching` | -6.000000 | 1095.000 | -0.006570000 |
| `remove_adhesive_finish` | -12.000000 | 360.000 | -0.004320000 |
| `remove_aft_cap_M3_complete_set_0` | -4.000000 | 1203.800 | -0.004815200 |
| `remove_aft_cap_M3_complete_set_1` | -4.000000 | 1203.800 | -0.004815200 |
| `remove_aft_cap_M3_complete_set_2` | -4.000000 | 1203.800 | -0.004815200 |
| `remove_aft_half_cylinder_saddle_lobe_0` | -2.989375 | 1221.620 | -0.003651879 |
| `remove_aft_half_cylinder_saddle_lobe_1` | -2.989375 | 1221.620 | -0.003651879 |
| `remove_aft_half_cylinder_saddle_lobe_2` | -2.989375 | 1221.620 | -0.003651879 |
| `remove_aft_shell` | -19.253745 | 1057.848 | -0.020367544 |
| `remove_c1_fin_panels` | -110.328075 | 1144.444 | -0.126264352 |
| `remove_fin_axial_retention_5mm_cross_pin_complete_set_0` | -6.500000 | 1180.000 | -0.007670000 |
| `remove_fin_axial_retention_5mm_cross_pin_complete_set_1` | -6.500000 | 1180.000 | -0.007670000 |
| `remove_fin_axial_retention_5mm_cross_pin_complete_set_2` | -6.500000 | 1180.000 | -0.007670000 |
| `remove_fin_bonds` | -8.000000 | 1110.000 | -0.008880000 |
| `remove_fin_source_cad_residual` | -17.209569 | 1140.000 | -0.019618909 |
| `remove_fin_tab_depth_delta_0` | -3.950017 | 1140.000 | -0.004503020 |
| `remove_fin_tab_depth_delta_1` | -3.950017 | 1140.000 | -0.004503020 |
| `remove_fin_tab_depth_delta_2` | -3.950017 | 1140.000 | -0.004503020 |
| `remove_fore_cap_M3_complete_set_0` | -4.000000 | 1024.000 | -0.004096000 |
| `remove_fore_cap_M3_complete_set_1` | -4.000000 | 1024.000 | -0.004096000 |
| `remove_fore_cap_M3_complete_set_2` | -4.000000 | 1024.000 | -0.004096000 |
| `remove_fore_half_cylinder_saddle_lobe_0` | -2.989375 | 1000.180 | -0.002989914 |
| `remove_fore_half_cylinder_saddle_lobe_1` | -2.989375 | 1000.180 | -0.002989914 |
| `remove_fore_half_cylinder_saddle_lobe_2` | -2.989375 | 1000.180 | -0.002989914 |
| `remove_fore_integral_G11_annular_cap` | -30.687077 | 1007.000 | -0.030901887 |
| `remove_fore_integral_body_skirt` | -9.336892 | 987.147 | -0.009216885 |
| `remove_fore_skirt_M2_spreader_fastener_assembly_budget` | -5.000000 | 987.147 | -0.004935735 |
| `remove_fore_skirt_to_paper_extra_epoxy_budget` | -4.500000 | 987.147 | -0.004442162 |
| `remove_incremental_mount_gap_epoxy_upper_budget` | -4.620026 | 1105.000 | -0.005105129 |
| `remove_motor_aft_hard_stop_spacer_0` | -0.234432 | 1211.000 | -0.000283897 |
| `remove_motor_aft_hard_stop_spacer_1` | -0.234432 | 1211.000 | -0.000283897 |
| `remove_motor_aft_hard_stop_spacer_2` | -0.234432 | 1211.000 | -0.000283897 |
| `remove_motor_front_annulus` | -6.656655 | 1066.000 | -0.007095994 |
| `remove_motor_front_key_5mm_cross_pin_complete_set_0` | -6.500000 | 1057.000 | -0.006870500 |
| `remove_motor_front_key_5mm_cross_pin_complete_set_1` | -6.500000 | 1057.000 | -0.006870500 |
| `remove_motor_front_key_5mm_cross_pin_complete_set_2` | -6.500000 | 1057.000 | -0.006870500 |
| `remove_motor_front_prong_0` | -0.879120 | 1066.000 | -0.000937142 |
| `remove_motor_front_prong_1` | -0.879120 | 1066.000 | -0.000937142 |
| `remove_motor_front_prong_2` | -0.879120 | 1066.000 | -0.000937142 |
| `remove_motor_front_stop_key_0` | -1.758240 | 1057.000 | -0.001858460 |
| `remove_motor_front_stop_key_1` | -1.758240 | 1057.000 | -0.001858460 |
| `remove_motor_front_stop_key_2` | -1.758240 | 1057.000 | -0.001858460 |
| `remove_motor_keeper_spring_locking_allocation` | -6.000000 | 1212.400 | -0.007274400 |
| `remove_raw_Bally_2745_loop_0` | -9.586357 | 1110.900 | -0.010649484 |
| `remove_raw_Bally_2745_loop_1` | -9.586357 | 1110.900 | -0.010649484 |
| `remove_raw_Bally_2745_loop_2` | -9.586357 | 1110.900 | -0.010649484 |
| `remove_retention_locking_materials_reserve` | -1.000000 | 1185.000 | -0.001185000 |
| `A_fin_dense_root_band` | +20.020000 | 1140.550 | +0.022833816 |
| `A_fin_dense_through_body_tabs` | +27.112800 | 1140.000 | +0.030908592 |
| `A_fin_PVC_core` | +12.480000 | 1145.100 | +0.014290844 |
| `A_fin_carbon_panel` | +35.964000 | 1144.444 | +0.041158800 |
| `A_fin_face_bond_panel` | +2.673000 | 1144.444 | +0.003059100 |
| `A_fin_carbon_tab` | +7.015200 | 1140.000 | +0.007997328 |
| `A_fin_face_bond_tab` | +0.521400 | 1140.000 | +0.000594396 |
| `A_fin_edge_finish` | +2.000000 | 1144.444 | +0.002288889 |
| `A_fin_root_band_core_butt_bonds` | +0.299200 | 1140.550 | +0.000341253 |
| `A_loadbearing_outer_can` | +87.913826 | 1067.000 | +0.093804053 |
| `A_structural_motor_tube` | +33.832502 | 1132.000 | +0.038298393 |
| `A_centering_ring_0` | +12.919957 | 1072.000 | +0.013850194 |
| `A_centering_ring_1` | +12.919957 | 1192.000 | +0.015400589 |
| `A_fore_recovery_cap` | +30.687077 | 1007.000 | +0.030901887 |
| `A_integral_fore_cuff` | +14.553114 | 1030.000 | +0.014989707 |
| `A_three_integral_recovery_saddles` | +3.985833 | 1012.546 | +0.004035841 |
| `A_three_forward_bridle_eyes` | +15.044942 | 960.000 | +0.014443145 |
| `A_independent_threaded_retainer` | +20.000000 | 1210.000 | +0.024200000 |
| `A_retainer_adapter_and_bond` | +5.000000 | 1198.000 | +0.005990000 |
| `A_root_and_ring_bonds` | +20.000000 | 1140.000 | +0.022800000 |
| `A_cap_cuff_bond` | +5.000000 | 1030.000 | +0.005150000 |
| `A_root_axial_pins_and_washers` | +4.000000 | 1140.000 | +0.004560000 |
| `A_harness_chafe_stitch_reserve` | +6.000000 | 1030.000 | +0.006180000 |
| `A_added_thermal_isolation` | +6.000000 | 1140.000 | +0.006840000 |
| `A_finish_and_locks` | +8.000000 | 1140.000 | +0.009120000 |
| `A_body_and_retainer_service_hardware` | +6.000000 | 1140.000 | +0.006840000 |

Source record totals: 561.440696 g removed, 399.942808 g added, net -161.497888 g; signed first-moment change -0.176407891 kg·m.

## Subsequent A1 accounting export (2026-11-02)

After the bounded A1 connection packet was executed, [`wo03_a1_resolved_ledger.py`](../scripts/wo03_a1_resolved_ledger.py) replayed **only** its signed mass rows against the frozen A component set. The [A1 source record](../runs/wo03-a1-connections-20261102-v1/record.json) has SHA-256 `7cf1284d869e217d5bede026f54f798fb928d9aa1d47b343642c3d3c7777627c`. The [immutable bookkeeping export](../runs/wo03-a1-bookkeeping-20261102-v1/record.json), SHA-256 `0810730990b5b7a6d8860ec6107c8358574d75be7d8f378e38677b1fa0114070`, contains each remaining component's ID, nonnegative mass, station, function, mass basis, source IDs and point-mass first moment. Its exact executed script is archived beside it.

The resolution is 49 retained C1 rows + 21 unchanged A additions + 20 A1 additions = **90 unique nonnegative accounting rows**, including reserves and process allocations rather than 90 verified installed parts or CAD solids. A1 explicitly removes eight existing rows once: `interface_coupler`, `joint_stop`, `aft_interface_hardware`, `A_root_axial_pins_and_washers`, `A_three_forward_bridle_eyes`, `A_centering_ring_0`, `A_centering_ring_1` and `A_structural_motor_tube`. The source 6 g `aft_interface_hardware` allowance is therefore credited once against A1's explicit positive M5 hardware, while positive axial stops do not prove radial fin-root capture. The old 83 C1 removals are not replayed as new A1 credits. A1's signed delta from A is +106.453571902 g and +0.099502421158 kg·m.

| Resolved case/account | Mass (g) | Point-mass first moment (kg·m) |
| --- | ---: | ---: |
| 90 component and allocation rows | 1024.762435194 | 0.855746150448 |
| Separate full growth at z1227 mm | 50.000000000 | 0.061350000000 |
| Nominal total | **1074.762435194** | **0.917096150448** |
| Adverse extra aft case | +20.000000000 | Separate case input, with inherited motor-CG probe |
| Adverse total | **1094.762435194** | No physical-component moment inferred for motor-CG probe |

The nominal and adverse masses, nominal CG, A1 delta mass and first moment match the A1 executed record. The export used 0.001799 CPU seconds and 0.001816 wall seconds under declared 1 CPU / 5 wall second caps. It ran no guide, structural, thermal, CAD or flight calculation; full intrinsic inertia and a newly validated CP remain null. **A1 is not admitted** by this accounting export.

No accounting ID is missing or duplicated. Function scope remains open: the unchanged `A_body_and_retainer_service_hardware` 6 g and `A_finish_and_locks` 8 g are **conservative unresolved reserves** alongside explicit A1 M5 sets and A1 joint process/bond rows. Their physical realization or overlap has not been resolved, so both reserves remain counted and no credit is inferred. A1 toe/heel stops replace the old axial-pin allocation in the ledger, while actual radial capture, hot root/collar/upper-joint capacity, exact hardware and protected service paths remain engineering questions.

The maintained exporter subsequently received Black formatting only. Its exact
executed pre-format version and original record remain preserved;
`format-maintenance.json` records both hashes. No accounting or engineering
calculation was rerun for formatting.
