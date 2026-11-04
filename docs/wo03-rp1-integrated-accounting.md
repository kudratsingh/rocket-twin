# RP1 fin alternatives: integrated ledger audit

**Bookkeeping decision, 2026-11-03:** FP1 and FR1 are separate proposed replacements for frozen **G80-F2-RP1-AD1 v2**. They cannot be stacked, and neither reported saving is admitted installed weight. FP1 passes only a provisional nominal component screen and fails diagnostic sensitivity; FR1 stops on finite-support movement and one-sided body-fillet demand. This audit makes no new attachment, material, guide or flight calculation. The primary engineering decision remains the load and attachment definition before construction.

The [machine-readable audit](../configs/studies/rp1-integrated-ledger-audit.json) preserves the source hashes, changed component rows, point-mass moments, 16 saved cases and cost treatment. It reads the published [FP1 screen](studies/rp1-fin-precedent-replacement/screen-record.json), [FR1 execution](../runs/wo03-rp1-fin-root-20261104-v1/record.json), and frozen [AD1 v2 execution](../runs/wo03-rp1-attachment-definition-20261103-v2/record.json). The resolved source specification is [`g80-f2-rp1-ad1-v2.yaml`](../configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml), SHA-256 `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660` in both studies. All FR1 declared local source hashes match its record. FP1's local study, producer, motor curve and five of six runtime dependencies match its published hashes; local `src/vehicle/schema.py` is `9b801a824ae617fbd9f70d2b54c81045e54e38f42eb97d041d13482917bb42ee` versus FP1's published `e11d777cce363e45fd07376b45db4bde640cea00fefda8377ced735250de5093`. This known local variation prevents treating the local tree as an exact FP1 runtime reproduction. No producer was rerun.

## Exact-once function and mass allocation

| Row/function | Frozen AD1 v2 | FP1 proposal | FR1 proposal |
| --- | ---: | ---: | ---: |
| `fin_set` external panels | 78.831677 g plywood | 68.445000 g plywood | 84.696300 g nominal CFRP |
| `fin_tabs` integral tabs | 25.917587 g plywood | 22.336931 g plywood | 27.640520 g nominal CFRP |
| `root_gussets` six wood wedges | 26.277226 g | Conditional removal | Conditional removal |
| `root_extra_bond_finish` wedge-specific bond/finish | 4.000000 g | Conditional removal | Conditional removal |
| `ad1_slot_fill` | 0.150000 g | Retained | Conditional removal for changed slot process |
| Carbon face stock, panel + tab | — | 35.176756 g | Integral in the two CFRP rows above |
| New carbon face bond, panel + tab | — | 3.597623 g, including 50% process increment | — |
| New edge/termination finish | — | 0.800000 g | 2.000000 g |
| `fin_internal_bonds` + `outer_fin_fillets` | 14 + 10 g | Both retained | Both retained |
| Other bond/finish rows | Ring bonds 10 g, forward root fill 0.763109 g, aft fill 0.145896 g, global finish 12 g | All retained; no second credit | All retained; no second credit |

The FP1 proposal replaces panel/tab material and removes the two wedge-specific rows, while its existing slot-fill allocation remains. Its **4.670180 g** saving is conditional on the carbon faces actually replacing brace stiffness and the installed root passing. FR1 replaces the panel/tab material, conditionally removes the same two wedge rows plus the **0.150 g slot-fill row**, and adds 2 g edge finish. Its **20.839669 g** saving is proposal accounting under nominal stock. Neither proposal credits body-slot cutout paper, transfers the retained 14/10 g fillet budgets to the new material, or removes ring/root/aft fill and global finish. All other AD1 vehicle functions, including motor, heat protection, recovery, guides and avionics, remain charged.

| Frozen or proposed subtotal before separate growth | Accounting rows | Mass | First moment from nose |
| --- | ---: | ---: | ---: |
| AD1 v2 | 55 | 884.549218 g | 0.651209085 kg·m |
| FP1 against AD1 | 58 | 879.879038 g | 0.645911412 kg·m |
| FR1 at nominal 3.175 mm stock against AD1 | 53 | 863.709549 g | 0.627476001 kg·m |

The FP1 minus AD1 first-moment change is −0.005297672 kg·m; FR1 minus AD1 is −0.023733084 kg·m. These are sums of saved component masses and CG stations, with no physical inertia inferred. FP1 versus FR1 is a comparison between alternative proposals: FR1 is 16.169490 g lighter at its nominal stock assumption. It is not an extra saving to apply after FP1.

## Saved complete cases at unchanged launch reference

The table transcribes prior case outputs. Every total includes **50 g at station 1250 mm**. Adverse rows additionally include **20 g aft and the saved 12.8 mm motor-CG probe**. The nylon main cases of **55 g** and **68 g** are an estimate and a metadata probe, respectively; neither is measured or a verified upper bound. Speeds use the saved 1.5 m usable-guide model and the unchanged formal **15 m/s** and separate planning **15.5 m/s** criteria. Conditional 1.8 m output does not change the reference or establish real equipment.

| Construction / stock | Main | Case | Total incl. 50 g | Static margin | Saved 1.5 m speed | Formal / planning mass headroom |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| AD1 v2 | 55 g | nominal | 934.549 g | 1.433 cal | 15.213 m/s | +23.794 / -30.750 g |
| AD1 v2 | 55 g | adverse | 954.549 g | 1.255 cal | 15.033 m/s | +3.794 / -50.750 g |
| AD1 v2 | 68 g | nominal | 947.549 g | 1.520 cal | 15.096 m/s | +10.794 / -43.750 g |
| AD1 v2 | 68 g | adverse | 967.549 g | 1.343 cal | 14.920 m/s | -9.206 / -63.750 g |
| FP1 provisional | 55 g | nominal | 929.879 g | 1.461 cal | 15.256 m/s | +28.465 / -26.080 g |
| FP1 provisional | 55 g | adverse | 949.879 g | 1.281 cal | 15.075 m/s | +8.465 / -46.080 g |
| FP1 provisional | 68 g | nominal | 942.879 g | 1.548 cal | 15.137 m/s | +15.465 / -39.080 g |
| FP1 provisional | 68 g | adverse | 962.879 g | 1.369 cal | 14.960 m/s | -4.535 / -59.080 g |
| FR1 3.175 mm | 55 g | nominal | 913.710 g | 1.561 cal | 15.406 m/s | +44.634 / -9.910 g |
| FR1 3.175 mm | 55 g | adverse | 933.710 g | 1.376 cal | 15.221 m/s | +24.634 / -29.910 g |
| FR1 3.175 mm | 68 g | nominal | 926.710 g | 1.649 cal | 15.285 m/s | +31.634 / -22.910 g |
| FR1 3.175 mm | 68 g | adverse | 946.710 g | 1.464 cal | 15.103 m/s | +11.634 / -42.910 g |
| FR1 3.429 mm | 55 g | nominal | 922.696 g | 1.505 cal | 15.322 m/s | +35.647 / -18.897 g |
| FR1 3.429 mm | 55 g | adverse | 942.696 g | 1.323 cal | 15.139 m/s | +15.647 / -38.897 g |
| FR1 3.429 mm | 68 g | nominal | 935.696 g | 1.592 cal | 15.202 m/s | +22.647 / -31.897 g |
| FR1 3.429 mm | 68 g | adverse | 955.696 g | 1.411 cal | 15.023 m/s | +2.647 / -51.897 g |

AD1's adverse 68 g probe already misses formal 15 m/s; FP1's adverse 68 g probe also misses it. FR1's nominal-stock and maximum-thickness saved cases clear formal arithmetically under their input assumptions, with only **2.647 g** formal headroom at maximum-thickness/68 g adverse. **Every saved FP1 and FR1 case misses 15.5 planning.** The published FP1 and FR1 static locations are based on the retained external planform/model; FR1's changed thickness and removed wedges have no validated new aerodynamic field. None of the case outcomes admits an installed construction.

## Cost and unclosed mass bounds

| Cost item | AD1 v2 | FP1 | FR1 |
| --- | ---: | ---: | ---: |
| Complete estimate | $476.688 | **Unavailable** | $585.428 |
| Wood sheet purchase | $69.75 on `fin_set` | Helper retains the old $69.75 allocation; exact Finnish birch purchase cost is unknown | $69.75 retained and moved to `forward_ring` for rings/nose |
| Carbon sheet purchase | — | No quoted complete purchase allocation; helper's zero costs are placeholders | One Rock West 204-11 sheet, listed $108.99, charged once |
| Difference from AD1 estimate | — | Cannot price from helper | +$108.740, including removal of $0.25 old slot-fill cost; old/new $2 finish charges cancel |

The FR1 cost is a **planned purchase allocation**, not evidence that the sheet is in stock or bought. Its $69.75 wood-sheet budget remains because the RP1 rings/nose still need wood; changing fin material does not remove that purchase. Shipping, tax and tests are excluded. FP1's source record explicitly marks the new component costs `null`; its temporary mass helper uses zeros only to satisfy the model and cannot establish a BOM total or a free purchase.

FP1 assumes proposed receiving windows for 5 mm Finnish birch, two cured carbon faces and thin secondary epoxy, with 750 kg/m³ wood and 1600 kg/m³ carbon mass budgets. Supplier-guaranteed incoming thickness/density and conditioned directional strength/stiffness are unavailable. Its 0.8 g skin-end finish and 3.598 g face bonds are process estimates. FR1 uses the listed 3.175 mm nominal and 3.429 mm maximum Rock West thickness and **1520 kg/m³ nominal density**; there is no verified maximum density or finished cut/edge/adhesive mass. Its 2 g edge seal and retained 14/10 g fillets are budgets, not weighed installed joints. FR1's maximum-thickness row therefore is **not a maximum finished vehicle mass**. Neither the 55 g nor the 68 g nylon value is a verified finished-main bound.

The load/attachment decision remains upstream of construction. The retained 8.83 N·m source envelope, combined force, asymmetric body/root reaction, finite tube/ring/body compliance, hot/wet adhesive/laminate behavior, skin termination peel and installed flutter still require justified source data or later representative tests. FR1's [joint supplement](../runs/wo03-rp1-fin-root-20261104-v1/joint-supplement.json) narrows area interpretation but does not establish complete movement or qualified capacity. Obtain exact stock, density, directional conditioned properties and process data from suppliers; then the primary can decide a bounded representative article and stop if the full installed route still lacks strength or movement evidence. Hardware is unpurchased; this audit calls for no owner measurement, new variant, producer, guide, trajectory, CAD, FEA or thermal run.
