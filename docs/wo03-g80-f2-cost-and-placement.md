# G80-F2 cost and forward-placement preflight

**Review-only input for the primary's integrated F2 selection.** F1 v2 is frozen. This note reads the [F1 decision](wo03-g80-f1-decision.md), its [executed 42-row record](../runs/wo03-g80-f1-preflight-20261102-v2/record.json) (SHA-256 `9a112ccbdee8ab0e7e4106ee4f27779ccd542ec37655ca07f80cd6bacf0bdea6`) and [specification snapshot](../runs/wo03-g80-f1-preflight-20261102-v2/specification.yaml) (SHA-256 `3e2a328e3b9252650d8bb6e73a5d30e60c34686ef617d2bbfa2d86b1267dded7`). It selects no stock geometry, bought item, pack rearrangement, ballast, F2 ledger or new acceptance result. The primary will supply actual F2 stock/interface choices. No new geometry, solver, browser, purchase, or source-file edit was made.

## Frozen F1 accounts and the available budget

The 42 nonnegative F1 v2 rows sum **767.505913 g**, with the full separate **50 g** at the aft end giving **817.505913 g** nominal. The adverse case adds **20 g** aft and the saved **12.8 mm motor-CG probe**, giving **837.505913 g**. Both growth and adverse inputs remain separate in every F2 comparison. F1's adverse reference guide calculation has **66.302 g** planning mass headroom for 15.5 m/s on the unchanged 1.5 m usable guide, and 120.847 g formal headroom for 15 m/s. Those are conditional source-model headrooms, **not** a general material budget: every positive F2 stock, splice, anchorage, securing hardware, wiring, finish and process increment consumes the 66.302 g unless an exact replaced F1 function earns a signed credit. A shape, diameter, motor or drag change requires recomputing the guide model, so the old headroom cannot then be transferred directly. The strict separate <1500 g policy does not clear guide, static, recovery, fit, fin or thermal gates.

F1 adverse CG **823.063 mm**, CP **860.125 mm**, body diameter **66.675 mm** give a fixed-CP 1-calibre target **793.450 mm**, requiring about **24,801 g·mm** of forward first-moment change at the same 837.506 g mass. This is a *placement comparator*, not an F2 mass/CP calculation or an approved geometry. The F1 [decision](wo03-g80-f1-decision.md) already reports the fixed-CP algebraic point-ballast option **36.827 g at z120 mm**. That leaves only **29.475 g** of adverse planning headroom before any new ballast retainer, body splice, revised eye, measured wire, thermal stock or other increment. A ballast solution placed exactly on the 1-calibre boundary gives no useful static margin for uncertainties, and its nose attachment/packing remains unproved.

For any selected F2 arrangement, write every signed row once with `replaces_id`, function, material/stock identity, finished mass, source geometry, station/first moment, cost basis and uncertainty. With `M` and `Q=M·z_CG` for the same complete F1 mass case, a pure move of existing part `i` from `z_i` to `z'_i` contributes **zero mass** and `ΔQ_i=m_i(z'_i−z_i)`. New ballast or an added keeper contributes **positive mass** `m_j` and moment `m_j z_j`. Replaced physical stock contributes `−m_old, −m_old z_old` and `+m_new, +m_new z_new`; never claim a changed location as an old-part deletion. Thus `M'=M+ΣΔm`, `Q'=Q+ΣΔQ`, `z'_CG=Q'/M'`, with a newly evaluated `CP'` and `z'_CG≤CP'−D` required for 1 calibre. Also rerun the adverse 20 g/motor-CG case separately. Known F1 `electrical_harness` **9 g** and `recovery_harness_wiring` **5 g** are estimated allowances, not measured spare wire length; relocating electronics or changing the recovery path needs a measured/justified signed wire and connector delta. The `recovery_output_mount` **6 g** is a mounting budget, not unused wire stock.

## What the existing envelopes say about moving mass

Stations are millimetres from the nose, positive aft. The F1 spec's `position_m` is the front of an axial envelope; the **point CG stations** below come from the F1 record. Purchased and soft envelopes are only placement proxies. Several `40×20×10 mm` boxes for sled, switches and budgets are placeholders, not verified physical solids. The body bore is **64.77 mm** (z160–1220) and the nose is z0–160 with a 30 mm shoulder. No nominal nonintersection below is an installation, tool-access or deployment pass.

| Source item(s) | Existing mass and point CG | Existing front and box or span | Constraint before moving forward |
| --- | --- | --- | --- |
| Nose attachment | `nose_anchor_plate` 12.873 g at z181.25; `nose_recovery_eye` 9 g at z180 | Plate z178–184.5, eye envelope z165–195 (30×14×14 mm); nose/shoulder z0–190 | The eye/plate must remain accessible and positively captured. No empty forward compartment is established inside the ogive or shoulder. |
| Soft recovery pack | `parachute` 35 g at z242.5; `shock_cord` 18 g at z290; `recovery_connectors` 9 g at z262.5; `recovery_protection` 6 g at z285 | Parachute box z210–275, 65×47×47 mm; shock cord z240–340, 100×30×25; connector z250–275, 25×15×10; protection z280–290, 10×40×12 | The boxes overlap axially because they are soft stowage estimates, not a solved pack. A 47×47 rigid square's diagonal exceeds the 64.77 mm circular bore; actual soft packed shape, deformation, extraction and order need evidence. The 15 mm nominal gap from eye end z195 to chute start z210 cannot contain any of the listed electronic boxes by axial length alone. |
| Main logger power and board | `battery` 30 g at z392.5; `flight_computer` 12 g at z400.5 | Battery z365–420, 55×30×15 mm, lateral offset (−15,0); board z370–431, 61×18×6, offset (+10,−15) | Both already sit immediately aft of the pack's nominal z340 end. Putting either entirely before z340 would require a new radial/axial packing and restraint design; a point-mass change cannot prove fit. Main power and independent recovery must stay separate. |
| Logger sled/sensors | `avionics_sled` 11 g at z370; IMU 2 g z450, baro 1 g z472.5, high-g 1 g z497.8, microSD 3 g z515, logger switch 3 g z435, regulator 4 g z450 | Sled placeholder z350–390; IMU z440–460, baro z465–480, high-g z485–510.6, microSD z505–525; switch z415–455 and regulator z430–470 placeholders | A forward move must preserve sensor orientation/rigidity, pressure port, arming and SD/USB access, restraint and cable bend/strain relief. Placeholder boxes do not prove a slide path. |
| Independent recovery electronics | `independent_recovery` 6.5 g z579.05, dedicated battery 3.6 g z620, rotary switch 3.7 g z619.288, carrier 8 g z570 | Controller z560–598.1, 38.1×20.32×6; cell z605–635, 30×15×4; switch z605–633.575, 28.575×15.875×12.7; carrier placeholder z550–590 | Keep its own battery, switch, output and routing. Forward relocation increases or changes lead geometry; switch external access, arming isolation, cell restraint and trigger wiring need actual layout. |
| Existing wire and output budgets | `electrical_harness` 9 g at z440, `recovery_harness_wiring` 5 g z600, `recovery_output_mount` 6 g z710 | Each has a 40×20×10 mm placeholder envelope at z420–460, 580–620 and 690–730 respectively | These point/box budgets do not encode actual flexible routing. Credit an old allowance only for a measured function it truly replaces; add lead, connector, guard and process mass at real stations. |

Pure movement of the **30 g main battery** would require its point centre near **−434 mm** to supply the whole adverse first-moment deficit by itself, outside the vehicle. Moving the **67 g logger core** (battery, computer, sled, IMU, baro, high-g, microSD, logger switch and regulator; existing mass-weighted point centre **405.542 mm**) alone would require its new centroid near **35.374 mm**, inside the nose and incompatible with the current envelope set. Even moving that group to z250 mm as a mathematical point would recover only about **10,421 g·mm**, less than half the **24,801 g·mm** deficit, before revised wires/retention and before proving pack fit. These are arithmetic screens only; the existing z210–340 recovery pack and z165–195 anchor prohibit any claim that such a group fits. A mixed placement/ballast/structural-mass change could be considered only with a complete exact-once ledger and real packing/access proof.

## Cost audit and owner-stock status

The F1 record's **$333.95** is the sum of 42 *consumed-part engineering allowances*, including one **$34** G80 motor. It excludes purchase pack quantities, shipping, tax, tools, spares, proof-test materials and any F2 additions. It is not a current shopping cart or evidence of purchase. The old [guide/motor source survey](wo03-launch-guide-motor-trade.md) recorded a **$43.99** G80-10T offer at that time, so the F1 $34 allowance is not a verified current price. The F1 **$14** one-piece body allowance is especially provisional because the [stock hold](wo03-g80-f1-supply-holds.md) found no listed 1,060 mm blank at the specified OD/ID; a splice or different stock would change both cost and installed mass. Exact motor/retainer tube fit is also held.

**Every zero-price F1 row is listed here.** Zero means the source estimate omitted a price. It does **not** establish that the owner owns the item or that it is free. No owner-specific invoice, inventory photo, part/revision/lot, quantity or condition evidence was found in the inspected project sources. If the owner later confirms stock, record that provenance and separate *cash still to spend* from *consumed physical part cost*; all masses remain counted.

| Zero-price ID | F1 mass (g) | F1 price field | Source/function and required cost evidence |
| --- | ---: | ---: | --- |
| `fin_tabs` | 26.093166 | $0 | Integral through-wall tabs are booked separately from `fin_set` 77.220 g. Confirm the selected birch sheet/cut plan and whether the $9 fin-set material allowance includes tab stock/kerf; no free mass or second material purchase is inferred. |
| `independent_recovery` | 6.500 | $0 | EasyMini-type independent controller mass/outline has a [source study](wo03-recovery-package.md); selected revision, actual supplier price, taxes/shipping and owner-stock status remain unconfirmed. |
| `recovery_battery` | 3.600 | $0 | Dedicated 1S 120 mAh cell estimate; exact connector/polarity, condition, product price and owner possession are unconfirmed. Do not substitute the logger battery. |
| `recovery_power_switch` | 3.700 | $0 | Separate rotary arming switch envelope; exact selected part, DC suitability, mounting stock/price and owner possession remain unconfirmed. |

The full 42-row F1 mass/point-CG/cost transcription follows below. All nonzero prices are still estimates/allowances. For F2, use `cost_to_buy = Σ(selected purchase quantities×verified item prices) + shipping/tax/tools` and a separate consumed-material ledger. Any owner-owned exact stock can reduce only *new cash outlay* once verified; it never reduces rocket mass. A replaced F1 row may have a negative **bookkeeping allowance** in an F2 comparison only if the actual function and procurement are replaced, while new stock/processing adds positive mass and cost. The $0 lines cannot be treated as negative cash credit.

## Exact-once F2 change register to fill after stock selection

| Function needing a signed decision | F1 rows retained unless replaced | Required F2 evidence before credit or admission |
| --- | --- | --- |
| Full-length body stock or permanent splice | `body` 145.926053 g / $14 | The exact one-piece 66.675/64.77×1060 mm blank is unsourced. A chosen real stock length/OD/ID/tolerance may replace the entire `body` mass/shape, or a splice adds sleeve/adhesive/finish and station; preserve one actual body, no free old-body credit. Recheck nose, fin slot, ring, guide, CP/CG and recovery load transfer. |
| Fin panel and integral tabs | `fin_set` 77.220 g / $9; `fin_tabs` 26.093166 g / $0; `fin_internal_bonds` 14 g / $3; `outer_fin_fillets` 10 g / $2 | Stock thickness/areal mass, cut/kerf, tab/ring notch, adhesive and finish all remain exact-once. The F1 minimum-stock movement and ring/tab overlap fail; new tabs/reinforcement need positive mass and changed load path. |
| Fixed mount and thrust/reverse retention | `motor_tube` 9.627315 g / $4; `forward_ring` 21.929 g / $4; `aft_ring` 10.965 g / $2; `ring_bonds` 9 g / $2; `motor_retainer` 22 g / $18; `retainer_adhesive` 2 g / $1; `mount_external_shield` 9.872 g / $5 | Current 78010/009750 tube and case interface unverified. Any tube/bore/ring/retainer/thermal relief correction needs full mass, shoulder/liner/nozzle fit, access and hot properties; the old A1 seat cannot reappear as a free fix. |
| Recovery and nose anchors | `body_recovery_eye` 9 g, `nose_anchor_plate` 12.873 g, `nose_recovery_eye` 9 g, `heat_leader` 8 g, `shock_cord` 18 g, `recovery_connectors` 9 g, `parachute` 35 g, `recovery_protection` 6 g | A stronger eye alone does not fix ring/body or nose attachment. New line length, sewn ends, chafe/heat stock, pack volume and positive plate retention require masses/costs/stations and full severe/normal/snatch checks. |
| Repositioned electronics and guides | All named logger/independent electronics, sled/carrier, `electrical_harness` 9 g, `recovery_harness_wiring` 5 g, `recovery_output_mount` 6 g, `rail_buttons` 5 g and `rail_backers` 4 g | A pure relocation changes first moment but leaves part mass and procurement. Additional wire, straps, guards, pressure ports, switch backers, cable service loops and guide installation need positive rows; no shared-power credit. Validate packed envelope, insertion, retrieval, arming and guide-button geometry. |
| Forward ballast if selected | No F1 ballast row | Add actual dense **nonmetallic** material, pocket/capture/adhesive/fasteners, finished mass, station, cost, proof and effect on nose separation/packing. The 36.827 g at z120 is a boundary comparator, not selected stock or a fit pass. Retain separate 50 g growth and 20 g adverse probe. |
| Distributed process/finish | `finish` 12 g / $5; `service_allowance` 6 g / $2 | State what existing coatings, wire restraint, screws, ports and process mass cover, then add or replace only exact functions. Do not absorb a known splice/ballast retainer into the 50 g allowance. |

The primary's selected F2 stock geometry should close this register with every F1 ID retained/replaced once and each new F2 ID positive, including actual owner-stock and price basis. **Stop** if an apparent stability fix relies on an unsourced tube, unretained nose weight, overlapping recovery pack, uncharged wire, zero-price assumption, or a source-model guide headroom after aerodynamic/motor changes. F1's static, ring, fin, motor-fit, stock and thermal failures remain until a same-identity F2 result addresses them.

## Complete F1 source price and mass transcription

The following rows are the frozen F1 record, sorted by ID. The point station is for mass bookkeeping and does not certify a physical box centre or packing clearance. A $0 entry is explicitly flagged above.

| F1 row ID | Mass (g) | Point CG (mm) | Cost allowance (USD) |
| --- | ---: | ---: | ---: |
| `aft_ring` | 10.964699 | 1193.250 | $2.00 |
| `avionics_sled` | 11.000000 | 370.000 | $5.00 |
| `baro` | 1.000000 | 472.500 | $15.00 |
| `battery` | 30.000000 | 392.500 | $18.00 |
| `body` | 145.926054 | 690.000 | $14.00 |
| `body_recovery_eye` | 9.000000 | 1069.000 | $4.00 |
| `electrical_harness` | 9.000000 | 440.000 | $5.00 |
| `fin_internal_bonds` | 14.000000 | 1135.000 | $3.00 |
| `fin_set` | 77.220000 | 1145.556 | $9.00 |
| `fin_tabs` | 26.093166 | 1135.000 | **$0.00** |
| `finish` | 12.000000 | 470.000 | $5.00 |
| `flight_computer` | 12.000000 | 400.500 | $32.00 |
| `forward_ring` | 21.929397 | 1081.500 | $4.00 |
| `heat_leader` | 8.000000 | 1035.000 | $5.00 |
| `high_g_accel` | 1.000000 | 497.800 | $24.95 |
| `imu` | 2.000000 | 450.000 | $18.00 |
| `independent_recovery` | 6.500000 | 579.050 | **$0.00** |
| `logger_power_switch` | 3.000000 | 435.000 | $3.00 |
| `logger_regulator` | 4.000000 | 450.000 | $4.00 |
| `micro_sd` | 3.000000 | 515.000 | $10.00 |
| `motor` | 128.200000 | 1156.000 | $34.00 |
| `motor_retainer` | 22.000000 | 1227.500 | $18.00 |
| `motor_tube` | 9.627315 | 1137.500 | $4.00 |
| `mount_external_shield` | 9.871950 | 1130.000 | $5.00 |
| `nose` | 38.000000 | 100.177 | $5.00 |
| `nose_anchor_plate` | 12.873332 | 181.250 | $2.00 |
| `nose_recovery_eye` | 9.000000 | 180.000 | $4.00 |
| `outer_fin_fillets` | 10.000000 | 1140.000 | $2.00 |
| `parachute` | 35.000000 | 242.500 | $30.00 |
| `rail_backers` | 4.000000 | 470.000 | $1.00 |
| `rail_buttons` | 5.000000 | 470.000 | $6.00 |
| `recovery_battery` | 3.600000 | 620.000 | **$0.00** |
| `recovery_carrier` | 8.000000 | 570.000 | $4.00 |
| `recovery_connectors` | 9.000000 | 262.500 | $8.00 |
| `recovery_harness_wiring` | 5.000000 | 600.000 | $4.00 |
| `recovery_output_mount` | 6.000000 | 710.000 | $5.00 |
| `recovery_power_switch` | 3.700000 | 619.288 | **$0.00** |
| `recovery_protection` | 6.000000 | 285.000 | $8.00 |
| `retainer_adhesive` | 2.000000 | 1212.500 | $1.00 |
| `ring_bonds` | 9.000000 | 1135.500 | $2.00 |
| `service_allowance` | 6.000000 | 470.000 | $2.00 |
| `shock_cord` | 18.000000 | 290.000 | $8.00 |

