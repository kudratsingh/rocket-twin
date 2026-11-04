# F2 recovery precedent decision — RP1

**Carry forward a motor-tube wrap with a separate replaceable nylon main harness.**
This is the best-supported conventional topology among the examined paper-body
examples. It replaces the provisional paired body eyes and their small washer
contacts. It does not qualify the cord, knots, ring, paper or bonds for F2.
The complete RP1 estimate fails the unchanged 1.5 m guide requirement; **do not
adopt it or start detailed analysis**. The next decision is finished harness
mass/capacity and realistic launch equipment, not another heavier bracket.

## Four documented constructions, three kit families

| Exact example and instructions | G80 statement and mass meaning | Complete recovery route and relevance |
| --- | --- | --- |
| Madcow cardboard/plywood 2.6-inch DX3, current K-3126 linking [K-126 manual](https://www.madcowrocketry.com/content/pdf/dx3.pdf), pp2–4 | G80T-7 in linked manual; not exact current78010/-10 approval. Advertised15oz, not labelled loaded/empty. | Kevlar loop around mount against notched forward ring → bonded mount/rings/fin tangs → paper body. Nylon joins payload bulkhead eye; bulkhead/coupler bonds retain payload. Nose fastening is incompletely specified. Closest topology, but F2 is heavier and has different ring/tab positions. |
| LOC Hi-Tech PK-56, 2.63-inch paper/plywood, [current linked manual](https://cdn.shopify.com/s/files/1/0568/7489/3503/files/PK-56_HiTech_Build_Instructions.pdf?v=1639515959), pp1–4 | G80-7 with optional MMA-2 adapter for38mm mount. Advertised20oz, not labelled loaded/empty; builder variation stated. | Sewn-loop tubular nylon → forward-ring eye/nuts/washers → ring/mount/body bonds. Payload screw eye → bulkhead/coupler bonds → payload; nose is explicitly retained. Current storefront says Kevlar mount, a material/version difference from this manual. |
| LOC PK-56 [historical ©2013 manual](https://www.apogeerockets.com/downloads/instructions/PK-56_Hi-Tech_Assy.pdf), p2 | Historical version, not combined with today's three-ring instructions or assumed exact78010 compatibility. No measured loaded mass established. | Knotted mounting cord under epoxy on inner paper wall → body; elastic main cord → payload/nose arrangement. Two mount rings are separate. A direct wall patch is not preferred for F2's severe case without substrate/peel proof. |
| AeroTech Initiator89011, 67mm paper body/polymer fins, [current product](https://aerotech-rocketry.com/products/product_6884e3bb-9375-a3f8-ab43-42d8a31ec4ee) plus [19911-8091 Rev8/12/04](https://d3l66gvjdr7rqw.cloudfront.net/Templates/170652/myimages/initiator_in_8-04_1674501193528.pdf), pp3–6 | Current page explicitly recommends G80-10T; old manual's motor chart is separate. Manual specifies400g **without motor**; not an actual G80 loaded measurement. | Elastic cord → screw eye in molded baffle → baffle shoulder/flange and ring/mount/body bonds. Fin-Lok structure differs from plywood. Other cord end ties to molded nose-shoulder loop; chute attaches about1ft from nose. Current aluminum retainer differs from the old hook. |

The [two-kit source note](wo03-f2-recovery-precedents-source-notes.md) and its
register preserve exact versions and access limits. No catalogue number was
turned into a claimed loaded flight weight. F2's approximately0.92–0.95kg
conservative baseline, thick custom fins/gussets and instrumented nose differ
substantially. A manufacturer's G80 delay recommendation does not select F2's
deployment timing, validate a current motor envelope or confer launch approval.

## Cord behavior, heat, access and failure evidence

DX3 uses Kevlar near the mount, nylon farther forward and a canopy protector;
official total length and force-extension curve are not given. Hi-Tech's current
manual uses sewn-loop nylon and a blanket; its3ft tail instruction is not the
total harness length. The old Hi-Tech elastic system is a separate version.
Initiator lists8ft/2.4m elastic, a mesh/baffle heat system and accessible free
cord; its deep baffle anchor is installed before the mount is bonded. The
manual warns against glue on the working cord knot and requires recurring
cord, baffle and free-ejection inspection. None supplies a conditioned, transient
finished-anchor capacity or a complete later anchor-replacement procedure.

Firsthand accounts are separate evidence. The manufacturer-linked DX3 Caplinger
review reports nose separation and section contact on E30 flights; the Hi-Tech
Terry account reports a zipper after descending deployment, with exact revision
unknown. Both direct pages returned403; indexed text has that limitation.
An Initiator [Harry Holmes page](https://www.rocketreviews.com/aerotech-aerospace-initiator--by-harryholmes.html)
contains a dated2006 commenter reporting shroud-line breakage at the shock-cord
attachment, while another reports E30-to-G80 flights. Direct access was403;
these indexed narratives have no force traces, loaded mass or controlled sample.
The sources do not establish failure rates or the cause of our load case.

There is actual, but nontransferable, measured evidence in [Apogee Newsletter318](https://www.apogeerockets.com/education/downloads/Newsletter318_Large.pdf),
Todd Treichel,2012: thirty Kevlar-to98mm Blue Tube patch coupons, ten per adhesive,
approximately2cc adhesive,24h cure and10mm/min pull testing. Its reported J-B
Kwik mean54.9lbf concerns that specimen/process, not F2 paper, a motor-tube wrap,
hot/wet bonds or shock peaks. It supports a representative test plan, not an
F2 allowable. The source's material-ranking/statistical claims are not adopted.
PDF text was read; screenshot calls returned no inspectable pixels or timed out,
and local PDF download failed DNS. Do not claim the source diagrams were visually
verified. Our new exported concept drawings were separately rendered/inspected.

## One F2 recommendation and the physical connections

Identity: **G80-F2-RP1-wrap-recommendation-v1**, separate from frozen F2/F2-C1.
See [complete specification](../configs/vehicle/candidates/g80-f2-rp1-wrap.yaml)
and [executed record](../runs/wo03-f2-recovery-precedent-20261103-v1/record.json).
It is a research recommendation, not an adopted build configuration.

```text
canopy → connector/main nylon → accessible Kevlar/nylon service junction
       → long Kevlar leader → loop/knot around motor tube, aft of forward ring
       → localized cord/ring bearing + motor-tube contact (sharing unknown)
       → ring outer bond → fore paper/body splice/retained upper body
       → ring inner bond → motor tube → continuous fin-tab/root bonds
                           → aft ring + body/root joints → aft body and fins
main nylon → separately retained nose eye/plate/shoulder → instrumented nose
motor → independent retainer/thrust contacts → mount tube/rings/body
```

The body wrap is the sole body anchor: apply full body demand to its finished
termination. A loop does not eliminate crushing, slip, cut-through, tube
ovalization, ring bending, peel or paper axial stress. Check70/30 and single-side
contact as adverse probes; do not assume equal wrap traction or two independent
redundant anchors. Main cord/connector demand retains the whole severe proxy.
The nose eye and its plate remain separate unqualified connections, not deleted.

The current aft-of-ring wrap would intersect all three tabs. RP1 moves the fixed
forward ring from1075–1087.2mm to **1060–1072.2mm**, ahead of tabs1080.2–1189.6mm.
Proposed wrap window1072.2–1077.0mm leaves3.2mm nominal axial separation. One
inner-edge4.5mm-wide ×5mm-deep cord notch at60° replaces the eye holes and old
blind tab slots. Proposed cord diameter≤3.8mm and cut±0.05mm leave0.275mm minimum
per-flank clearance after the inherited0.05mm differential bound. These are
receiving/design assumptions, not vendor tolerances or measured hot clearance.
The mount bore and aft motor-removal corridor remain untouched by design intent;
exact retainer contacts and actual knot/bend envelope are still unknown.

**Moving the ring removes the old front-tab end/side ring bonds.** Their load
function is assigned to the continuous109.4mm tab-to-mount/root/body joints and
aft ring, whose installed flexibility, hot strength and flutter must be checked
for RP1. No old clamp/fin result transfers. All old adhesive allocations remain
counted as installation reserves; no imaginary glue bridge spans the new gap.
The moved ring/contact/cord also needs thermal revalidation before adoption.

Build sequence intent: define/test the loop and rounded notch on the exposed
mount, preserve a knot pocket between fin planes, install/bond the forward ring,
inspect the complete anchor and fillets, then install into the lower tube and
bond fins/aft ring. Motor removal stays independent. Route the long leader to an
accessible junction above the mouth, protecting paper-edge contact; keep the
canopy protector separate. This is an assembly plan, not a checked insertion or
deployment simulation. The deep wrap is not promised replaceable after cure;
damaged inaccessible anchorage requires structural rework, not a hidden repair.

## Complete replacement budget and components

| Allocation | F2-C1,g | RP1,g | Basis / available evidence |
| --- | ---: | ---: | --- |
| Paired body eyes/nuts/washers |18 |0 | Anchor function replaced by tube wrap in this proposal; no active-design credit |
| Heat leader |8 |20 | Proposed8ft Apogee30327;1500lb **label**,3.48mm nominal OD.20g estimates the2g listed sales-unit mass as per foot plus25%; mass basis/tolerance unconfirmed |
| Main harness |18 |55 | Proposed uncut LOC3/8in tubular nylon12ft/sewn loops,1020lb **label**.55g is an analogy/budget, not published LOC mass |
| Additional anchor/ring locking fillet |0 |4 | Estimated epoxy; working knot is not glued |
| Rounded-notch sealing/process |0 |1 | Estimated epoxy/finish |
| Custom soft mouth guard |0 |4 | Estimated sewn aramid-textile guard; no structural/zipper qualification |
| Forward-ring filled old notches/eye holes |0 |2.215 | Added wood at explicit800kg/m³ budget; old ring mass retained, zero new-cut credit |
| **Net complete change** | |**+42.215** | All other source allocations, including reinforcement, adhesives, connectors, nose/recovery electronics, power, motor and finish, retained once |

The [full55-row ledger](../runs/wo03-f2-recovery-precedent-20261103-v1/record.json)
includes every unchanged item. Ring becomes22.480g; its new notch earns no removal
credit. The proposed main mass uses a different Apogee1/2in nylon listing's
5.68g sales-unit mass, assumed per priced foot, scaled by width/length and
rounded upward. Neither same weave nor linear density is established. That
uncertainty materially controls admission; do not present55g as a measurement.

[Apogee30327](https://www.apogeerockets.com/Building_Supplies/Parachutes_Recovery_Equipment/Shock_Cord/Kevlar_Cord_1500)
was in stock;8ft installed from10ft minimum order costs$17.10 before shipping.
[LOC's nylon page](https://locprecision.com/products/shock-cords) lists3/8in12ft
with sewn loops and1020lb tensile. Its default$8.12 is a different selected
variant; RP1 uses a **$20 estimate**, with exact price/stock/mass unconfirmed.
The complete BOM estimate is **$488.05**, excluding unquoted shipping/tax/tests.
The former body hardware and leader costs are removed only with their replaced
functions; full existing plywood purchase cost remains. Hardware is unpurchased.

Do not substitute the smaller375lb LOC nylon (about1668N label) for the retained
whole severe demand. [Madcow P-183](https://www.madcowrocketry.com/kevlar-nylon-shock-cord-combo/)
is an in-stock$7.70 conventional reference with2.5ft Kevlar and5ft550lb nylon,
but supplies no finished assembly capacity/extension/mass. Its roughly2447N nylon
label leaves little unknown termination loss against RP1's2070N severe proxy.
The proposed1020lb nylon label is about4537N; the finished conditioned assembly
would need to retain at least45.6% of that label merely to meet this proxy.
These are required retained fractions, **not assumed knot-efficiency factors**.
Apogee29187 lip protection was not selected: its stated100/300lb cord fit does
not establish fit on30327. The custom4g guard is counted and remains unverified.

## Coupled result and admission decision

| Case, full50g included | Mass,g | CG from nose,mm | Loaded / burnout,cal |1.5m,m/s | Formal / planning headroom,g |1.8m conditional,m/s | Required whole / body proxy,N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RP1 nominal |960.965 |742.460 |1.751 /2.182 |**14.977020** |**−2.622 /−57.166** |16.411 |2027.848 /1354.190 |
| RP1 adverse |980.965 |754.480 |1.571 /1.980 |**14.804581** |**−22.622 /−77.166** |16.222 |2070.052 /1396.394 |

Adverse additionally includes20g aft and the saved12.8mm motor-CG probe. CP
remains859.442mm under the unchanged external fin/shape hypothesis; internal
changes do not validate actual drag, flight or flutter. RocketPy endpoints agree
for the same no-growth static model; allowance/adverse rows are analytic mass
moments, not independent full-flight comparisons. Full physical inertia is
unavailable. Packed cord centroids are estimates and may move during flight.

With other budgets fixed, the main harness must be **≤32.378g** for even the
adverse formal1.5m pass, with no useful development margin at equality. The
planning target would require a negative main mass; it cannot close by changing
only that cord. Do not automatically shorten rated sewn harnesses, spend growth,
claim an unconfirmed long rail, or invent a lower opening force. A verified
lighter finished harness or an explicitly confirmed/rebaselined launch setup is
the next specific mass/access decision.1.8m is a conditional comparison only.

The initial new RP1 process failed while serializing its ledger, using a wrong
Part attribute. Its producer/failure remain preserved. The one declared setup
correction captured the unchanged candidate; successful arithmetic took1.619s.
No stopped F2/C1 solve ran. Thread/affinity and process CPU usage were not recorded;
do not promote a requested single-CPU setting into measured enforcement. The
10CPU process cap and20wall packet limit were retained; no numerical acceptance
or further calculation is justified by this resource record.

## Required cases, proposed review and later verification

Retain20.4m/s,0.3m andDF3 once. The energy-average arrest case corresponds to
roughly70.7g before design margin; it is not a measured peak. The references
normally aim for apogee motor ejection and have substantially different mass,
length, cord and canopy. They provide no evidence for F2's20.4m/s initial speed,
0.3m effective travel, peak factor or thermal state. Nylon is not automatically
a bungee or a guarantee of0.3m stopping travel; low-stretch Kevlar is not flameproof
under unlimited exposure. Longer cord alone does not establish lower peak force.

Propose a separate mechanism/requirement review using the exact deployment
timing, relative section motion, inflation and measured force-extension/peak
data. Keep normal, credible early/late, line-snatch and canopy inflation separate,
as in the existing recovery-mechanism note. **No load or design factor is revised
by this recommendation.**

Before design admission, request supplier documentation for the exact sewn12ft
nylon mass, terminal test scope/minimum strength, environmental behavior and
extension; confirm actual cord diameter and permissible bends/contact. No owner
measurements of unpurchased hardware are requested. If not supplied, label these
as build/test-stage measurements and do not assume capacity. The current actual
mass/guide failure and lost front support still independently hold RP1 admission.

Later owner-performed verification should use representative identical tube,
ring, loop, knot, adhesive, cure and temperature/moisture conditions. First test
separate cord/finished terminations and ring/tube/paper joints to observe slip,
crush, peel, delamination and residual damage; then load the assembled path with
asymmetric/side pulls, recording force, displacement and failure location. The
owner must plan safe fixtures for kilonewton loads; this document authorizes no
physical work. Separate packing/extraction, edge-chafe, nose retention, motor
service, temperature logging and staged deployment tests remain necessary.
Calibrate deployment mechanics using measured data, keeping independent
evaluation cases. Static proof alone does not validate transient opening loads.

**Outcome:** a conventional attachment topology is selected for further
definition; paired body M4 hardware is no longer a required design choice.
No installed strength/thermal/flight requirement closes. G80 custom fabrication,
G54 upgrade and G12 PID-to-RL remain separate committed tracks, with all
WO-03, physical, purchase, paid, firmware-review and flight-release gates intact.
