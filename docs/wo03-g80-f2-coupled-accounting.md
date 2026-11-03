# G80-F2 selected package: coupled accounting and load screens

**One bounded arithmetic packet; no engineering admission.** Source: selected [F2 v2 specification](../configs/vehicle/candidates/g80-f2-ballast.yaml), [executed F2 record](../runs/wo03-g80-f2-selected-20261103-v2/record.json), frozen [F1 v2 record](../runs/wo03-g80-f1-preflight-20261102-v2/record.json), and the [F2 decision](wo03-g80-f2-decision.md). The [new accounting record](../runs/wo03-g80-f2-accounting-20261103-v1/record.json) contains all 50 source rows, 43 signed F1→F2 changes, group IDs, cost bases, cut allocations and guide brackets; [exact script](../scripts/wo03_f2_accounting.py) is source pinned there. The sole successful arithmetic execution used **0.236 s wall** under the declared one-CPU, 10-CPU-second and 20-wall-second caps. A first launcher attempt failed immediately on `ModuleNotFoundError: src` before any calculation or record write; the import path was corrected once, and the bounded packet then completed. No CAD, FEA, flight, heat or browser run was made here.

## Exact-once mass and cost reconciliation

| Account | F1 frozen | F2 selected | Signed change |
| --- | ---: | ---: | ---: |
| Identified component/allocation rows | 42 | 50 | 43 changed, moved or newly added rows in the signed ledger |
| Parts mass before full growth | 767.505913 g | **867.559981 g** | **+100.054068 g** |
| Estimated consumed-part cost | $333.95 | **$458.71** | **+$124.76** |
| Full separate growth | +50 g | +50 g | Unchanged and counted once |
| Nominal full-growth total | 817.505913 g | **917.559981 g** | +100.054068 g |
| Additional adverse aft case | +20 g and motor-CG probe | +20 g and motor-CG probe | Separate from the 50 g and parts ledger |
| Adverse full-growth total | 837.505913 g | **937.559981 g** | +100.054068 g |

Every F1 part ID that remains has its own old mass, new mass, point first-moment and cost in `signed_part_deltas`; eight additional F2 IDs enter positively. A relocation has zero mass delta but a signed moment change. The installed F2 body replaces the F1 body mass only through the explicit two-blank `body`/`upper_body`/`body_splice`/seam/adhesive rows. The full 50 g is never used to hide a known splice, fin, eye, wiring or ballast item.

The largest source changes are the two LOC tube blanks and permanent splice, the one $69.75 birch sheet (fin stock plus rings/gussets/plate), the AeroTech mount tube and retainer family, the $43.99 G80 source price, the Eggtimer Apogee controller/cell package and the captured **17.815997 g washer ballast plus 7 g capsule/fastener budget**. F1's main electronics move forward without deleting their mass. Exact current G80-10T 78010/12912/19002 mating, delivered eyes, Eggtimer live stock and finished part weights remain holds in the [F2 decision](wo03-g80-f2-decision.md) and [supplier intake](wo03-g80-f2-suppliers.md).

All eight **$0** F2 source rows are **bundled material from purchased stock**, not owner-owned items: `fin_tabs`, `forward_ring`, `aft_ring`, `nose_anchor_plate`, `root_gussets` use the charged birch sheet; `upper_body`, `body_splice`, `splice_seam_patch` use the second charged LOC tube blank/offcut. Their masses remain counted. The base `body` row charges **$20.54 for two LOC blanks** and `fin_set` charges **$69.75 for one sheet**; price entries of $0 on cut pieces avoid charging the same purchase twice. No owner-stock invoice, inventory identity, lot or measured condition is evidenced. F2's $458.71 is an estimated consumed-parts total, not a current shopping cart including tax, shipping, tools or proof stock.

## Physical retention groups, overriding parent fields

The F2 spec's `parent` field is an assembly-tree link. It does **not** establish what separates from the vehicle or what a recovery eye carries. The following explicit physical hypothesis is the selected F2 arrangement to be tested. In particular, the nose plate/eye have `parent: body` in the source but are assigned to the nose; `upper_body` and `body_splice` have `parent: nose` but are fixed body stock. The nose electronics and output well extend beyond the printed z0–160 mm ogive/shoulder envelope, so positive carrier retention, connector disconnection and actual extraction are essential. The count/sums are exact source row accounting, not measured retained groups.

| Retained group | Rows | F2 parts mass | Intended membership and physical qualification gap |
| --- | ---: | ---: | --- |
| Nose with captive equipment | 21 | **193.955001 g** | Printed nose, nose plate/eye, ballast and capsule, all logger/independent recovery electronics, cells, carriers, switches, their wiring and recovery output mount. This requires a rigidly retained, removable carrier and confirmed connection/packing through the nose opening; parentage and an envelope image do not prove it. |
| Soft recovery goods | 5 | **76.000000 g** | Parachute, shock cord, connectors, protection and two-branch heat leader. Their deployed length and force ownership vary in time; the 8 g heat leader point at z1035 mm is not a rigid aft body mass. |
| Retained body/motor/fin and guide | 24 | **597.604980 g** | Upper and lower paper sections, permanent splice/patch/adhesive, motor tube/rings, fins/tabs/gussets/bonds, motor/retainer, two body eyes, shield, rail/buttons and distributed finish/service rows. The 50 g growth and adverse +20 g are assigned to this body group below for conservative case accounting. |
| **All F2 parts** | **50** | **867.559981 g** | No missing or duplicated ID. |

## Recovery force and two opposed eyes

The retained historical severe screen is **20.4 m/s, 0.3 m stopping travel and DF3 once**. Its constant-deceleration factor is `3 × [20.4²/(2×0.3)+9.80665] = 2110.21995 N/kg`. This is an energy-equivalent **mean-force proxy**, not a measured peak or a line-snatch/inflation solution. F2's original source record gives whole-case 1,936.253 N nominal and 1,978.458 N adverse; this packet partitions that exact same whole mass once and recombines it without assuming actual simultaneous branch tension.

| Common-acceleration account | Nominal full growth | Adverse +20 g aft | Meaning |
| --- | ---: | ---: | --- |
| Nose group | 193.955001 g → **409.288 N** | Same **409.288 N** | Equivalent nose retained-mass demand if engaged at the same deceleration; not a measured nose-eye peak. |
| Soft goods group | 76.000000 g → **160.377 N** | Same **160.377 N** | Inertial bookkeeping only; canopy aerodynamic force, cloth and line dynamics are outside this group multiplication. |
| Body group plus full 50 g | 647.604980 g → **1,366.589 N** | 667.604980 g → **1,408.793 N** | Candidate body-eye downstream free body, assuming this group follows common axial arrest. |
| **All groups** | **917.559981 g → 1,936.253 N** | **937.559981 g → 1,978.458 N** | Equals the complete F2 historical-model force; not an additional load on top of its groups. |

The two body eyes are at opposing **R23 mm**, azimuth 30°/210°. For the **body-group** severe proxy, a declared **70/30** split gives **956.612/409.977 N** nominal and **986.155/422.638 N** adverse. Opposed radial forces leave an eccentric moment `0.4 F_body × 0.023 m`: **12.573/12.961 N·m**. A one-eye body-group sensitivity is the full **1,366.589/1,408.793 N** at 23 mm, **31.432/32.402 N·m**. An even more conservative one-eye **whole-force** sensitivity gives **44.534/45.505 N·m**, but whole force and partitioned branch forces must not be added to each other. The nose eye is at R26.5 mm; if its entire nose group reaches one eye, the same proxy is **10.846 N·m**. These are equilibrium/moment demands, not eye, ring or adhesive capacity. Real cord angle, ring flexibility, imperfect branches, unsupported wood and event timing can change them.

The finished M4 eye still needs exact supplier shank, eye, nuts, washers and locking verification. The source proposes **30 mm threaded shank/45 mm overall** with **≥25 mm usable thread**, while the ring stack consumes about 19.4 mm including washers/nuts/projection. The 14 mm ring-strip failure in the F2 decision is not repaired by splitting two eye masses or by this force balance. Canopy inflation and line snatch stay distinct from the historical mean-force case; no load criterion is reduced.

## Near-forward-ring paper-body cut

At **z1075 mm**, the selected lower LOC tube is z458–1220 mm, OD **66.802 mm**, ID **65.024 mm**. The source model treats its **98.191914 g** as uniform stock, so the aft 145/762 mm portion contributes **18.685 g** of known mass at this cut. The 24 g motor tube spans z1055–1220, of which 145/165 mm is aft; that contributes **21.091 g**. These are *real length fractions* of the selected uniform tube estimates, not allocations by each full tube's point CG. All other wholly aft source envelopes are counted once. The record lists their exact IDs and the known-fore rows.

Five rows have unresolved spatial/load ownership at this plane: `ring_bonds` 10 g, `mount_external_shield` 10 g, `body_recovery_eye` 18 g, distributed `finish` 12 g and `service_allowance` 6 g. Their **56 g total** is bounded from zero to wholly aft, not assigned according to a point station or display box. The full 50 g growth, and separately the extra 20 g adverse case, are conservatively aft for both bounds. The paper gross annulus area is **184.087 mm²**, with circular second moment **99,989 mm⁴**. Under the ideal serial paper-only assumption:

| Severe case at z1075 | Aft mass bound incl. growth | Axial force | Gross axial stress | Axial + 70/30 eccentric bending proxy | Axial + one-eye bending proxy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Nominal known-aft lower | 440.429 g | 929.401 N | **5.049 MPa** | 7.905 MPa | 12.189 MPa |
| Nominal all-uncertain-aft upper | 496.429 g | 1,047.573 N | **5.691 MPa** | 8.910 MPa | 13.739 MPa |
| Adverse known-aft lower | 460.429 g | 971.606 N | **5.278 MPa** | 8.264 MPa | 12.743 MPa |
| Adverse all-uncertain-aft upper | 516.429 g | 1,089.778 N | **5.920 MPa** | 9.269 MPa | 14.293 MPa |

The project's **2 MPa kraft axial strength** is an estimated scalar screening input, not a measured hot/wet allowable; even the **known-aft lower axial proxy** exceeds it if paper alone transmits this severe load. The eccentric beam expression uses `σ_b=M R_o/I` with a 23 mm eye radius; it is a diagnostic demand only. It does not prove actual paper failure or a safe alternate path. The true eye → 12.2 mm notched forward ring → tab/motor tube/fin/body transfer, discontinuous slots, epoxy shear/peel, shell ovalization and how the body supports its retained mass remain unmodeled. A ring or motor tube must not be treated as rigid ground or credited as a complete bypass without compatible finite joints and proof. Some process masses are spatially unresolved even if their *function* belongs aft.

## Ballast and guide decisions still open

The selected ballast is **17.815997 g** of washers at about z55 mm plus **7 g** of capsule/fastener budget at z50 mm. Together **24.815997 g** imply **52.367 N** under the same severe common-deceleration proxy. This only sizes a *required demand to investigate*: actual washer/bolt identity and finished masses, legal nonstructural metal use, positive fastener capture/anti-loosening, printed-nose/plywood bearing and pull-through, cold/hot/wet conditioning, separation snatch, ejection and repeated handling need their own capacities and tests. The full **nose group 409.288 N** cannot be replaced with the smaller ballast-only number when checking the nose eye and carrier. The 7 g reserve does not prove the keeper, washers and fastener are fully installed or retained.

Using the unchanged [`screen_launch`](../src/vehicle/benchmark.py) guide model with the selected **937.559981 g adverse full-growth loaded mass**, 24-step bisection brackets the mathematical minimum usable guide travel as:

| Adverse target | Required usable travel bracket | Existing 1.5 m reference |
| --- | ---: | --- |
| Formal 15 m/s | **1.463609017–1.463609120 m** | Source result 15.185577 m/s; formal model pass. |
| Separate planning 15.5 m/s | **1.562666643–1.562666746 m** | Source result 15.185577 m/s; planning model fail. |

The bracket width is numerical precision, far smaller than uncertainty in actual guide equipment, start/release losses, button span/mass, motor thrust and drag. **1.5 m remains the resolved baseline**; 1.562667 m is an equipment-dependent planning need, not an adopted rail or site. Existing 1.8/1.971 m calculations remain conditional. This guide screen says nothing about the failed paper/ring/anchor path, fin motion, thermal acceptance, exact motor fit or flight release.

**Next bounded stop:** obtain actual eye/ballast carrier/washer details, quantify a finite recovery ring-to-body/fin/tube path and real force sharing, resolve the paper cut with supported hot/wet properties, confirm usable guide hardware if planning speed controls, and preserve the F2 source/cost and mass identities. If those inputs are absent, the branch and bending calculations remain failed or unavailable screens, not construction approval.
