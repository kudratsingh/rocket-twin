# G80-F2-C1 — bounded supplier evidence

**Decision, 2026-11-03 local:** retain the current motor/tube/retainer family as a
provisional compatibility class, and keep exact installed fit on hold. One small
M4 stock eye meets the required thread length on its seller's specification,
but no complete closed-eye/washer/nut assembly is admitted within the existing
18 g budget. Neither a finished eye capacity nor the exact 14 mm OD / 4.5 mm ID
washer was established. This packet changes no F2 geometry, material, demand,
allowance, active specification or prior result. G80-F2-C1 is an additive evidence
identity, distinct from the earlier stopped G80-C1 construction candidate.

The packet was declared before browsing: **at most 12 unique source URLs and
15 minutes**, including failed URL attempts. It closed at **11 unique URLs**;
search discovery and repeat access to an already counted URL do not add another
unique URL. There were **three failed access attempts**: the Vital Parts product
initially failed then recovered; its data sheet returned 403; a repeat terminal
download of the already readable 19002 PDF failed DNS. Only the data-sheet URL
remained unreadable. The [source register](../configs/studies/wo03-g80-f2-c1-sources.yaml)
records the attempted URLs and evidence boundaries. No contact, purchase, paid
run, computer UI, hardware action, CAD, FEA or new engineering calculation occurred.

## Motor, tube and retainer evidence

The [AeroTech resource entry](https://aerotech-rocketry.com/pages/aerotech-resources)
links the [official RCS resource library](https://www.rocketmotorparts.com/page/aerotech-resources),
whose [instruction index](https://www.rocketmotorparts.com/page/instructions)
was inspected. Its linked G80 and kit PDFs are manufacturer documents; being
currently linked does not make their historical revisions current product drawings.
The library's [RockSim/kit-data page](https://www.rocketmotorparts.com/page/rocksim--kit-data)
exposed simulation data, not the required mating drawing. No dimensions were
extracted from rendered photographs or simulation files.

| Exact item / evidence | Supported manufacturer fact | Still unavailable; consequence |
| --- | --- | --- |
| **78010 G80-10T**; [linked New G80T instructions](https://d3l66gvjdr7rqw.cloudfront.net/Templates/170652/myimages/g80t_new_su_in_21003-1_1642626256946.pdf), P/N 21003-1, Rev. 12/11/07 | Historical instructions identify a molded thrust-ring G80T and describe insertion/retention. They state that casing/nozzle stay hot after operation and require a cooling interval before handling. | Current-lot case OD extremes; shoulder/ring OD, thickness, fillet and axial datum; nozzle projection; forward projection and fully assembled end-to-end length; polymer expansion/tolerance and permitted contact/retention loads. This old document does **not** control the current 78010 envelope. Its handling/storage guidance supplies no mount temperature or 45 °C substrate acceptance. |
| **12912 tube**; [official Initiator PDF](https://d3l66gvjdr7rqw.cloudfront.net/Templates/170652/myimages/initiator_in_8-04_1674501193528.pdf), 19911-8091, Rev. 8/12/04 | Parts list explicitly identifies the 12 in / 30.5 cm tube as 12912. The base manual uses the older 19001 hook/internal thrust-ring arrangement. | Controlled tube ID/OD, ovality, wall and straightness tolerances, actual cut mass, temperature/moisture behavior. The old kit locations do not define the shortened F2 mount or current retainer fit. |
| **19002 retainer**; [manufacturer-authored instruction scan at Harvey Mudd](https://pages.hmc.edu/spjut/NewE80/PDFs/Aerotech29mmMotorRetainerInstructions.pdf), two pages, no revision established | Identifies 19002, aluminum, single-use/RMS built-in-thrust-ring class; claims AeroTech 29 mm mount fit and possible fit to 1.235 in OD tubes. Instructions require a test fit, roughening the collar interior, keeping epoxy off threads and 24 h cure. | Collar ID/insertion depth and tolerances; lip ID/width/thickness; cap internal depth, seat and contact datum; cap/body thread form/engagement; axial clearance/preload; nozzle clearance; removal/tool envelope; adhesive specification and hot/reverse-load capacity. Academic hosting preserves manufacturer authorship but supplies no proof of the currently shipped revision. |
| **Compatible kit installation precedent**; [official Arreaux PDF](https://d3l66gvjdr7rqw.cloudfront.net/Templates/170652/myimages/arreaux_in_8-04_1674501620003.pdf), appended 19913UN 05/15, page 8 | Upgrade notice removes the old internal thrust ring/flange, hook and adapter. It moves the kit tube to project 1/4 in beyond the body and installs the screw-on retainer after the rear ring. | No exact current 78010–19002 mating drawing, contact pressure, finished load or F2 axial datum. This kit-specific projection is **not** adopted as an F2 dimension. |

The [frozen F2 supplier intake](wo03-g80-f2-suppliers.md) already records the
78010 product nominals, 12912 wall/length and 19002 nominal-family claim. Those
product summaries were not reopened to increase the source count. The earlier
Initiator storefront's explicit G80-10T/aluminum-retainer recommendation remains
a package compatibility precedent, not exact fit. Neither 124 mm catalogue case
length, the historical 128 mm curve envelope, nor a 2007 ring dimension is a
current assembled dimension. No motor alteration, trimming or dimensional
substitution is authorized.

## One small stock recovery-eye lead, with no capacity admission

The target remains **two opposed M4 eyes through the existing 12.2 mm plywood
ring**, each with at least 25 mm usable thread, the specified 14 mm OD / 4.5 mm ID
washers, and **18 g total** for the paired eyes, nuts and washers. The original
70/30 and single-eye demands remain separate checks. No equal-sharing credit or
generic steel strength is assigned to an eye, bend, weld or finished joint.

| Evidence | Published geometry / acquisition snapshot | Missing facts and disposition |
| --- | --- | --- |
| [Vital Parts MSEYE-M4-30-A2](https://www.vital-parts.co.uk/screw-eyes-metric/54718-mseye-m4-30-a2), the **one small stock lead** | Seller's own product specifies M4 × 0.70, **27 mm threaded length**, 30 mm listed length, 6 mm eye ID and A2 stainless. It describes an enclosed eye and light-duty attachment. At access: £0.22 excluding / £0.26 including VAT each; page offered Add to Cart, up to 79,000 available and dispatch within five days, while its variant table still said “Checking…”. | No defined length datum/total envelope, eye OD/section/bend radius, closure/weld process, dimensional tolerance, mass, proof/break/working load, angle/shock/fatigue/temperature rating or US delivery confirmation. The 27 mm thread is a nominal specification, not measured usable thread after runout. **Stock lead only; not selected or rocket-qualified.** |
| [Vital Parts data-sheet endpoint](https://www.vital-parts.co.uk/tools/datasheet/MSEYE-M4-30-A2) | Linked directly by that exact product. | HTTP 403; no data-sheet contents or CAD were acquired. No form was submitted. |
| [Huaxin 521 welded-eye family](https://www.cntzhuaxin.com/en/products/welded-eye-bolt.html), manufacturer comparator only | Manufacturer lists M4, H 51 / L 30 / F 10 mm and 0.005 kg, with 304/316 options. | Inquiry ordering only; exact stock/US purchasability, dimension datums/usable thread, bend/weld detail and finished load unestablished. H 51 mm cannot be silently fitted into the proposed 45 mm envelope. Its 5 g entry is not a completed paired assembly mass. **Not an alternative selection.** |

The Vital Parts page's suggested washer is 9 mm OD / 4.3 mm ID / 0.8 mm thick;
it is **not** the required 14 / 4.5 washer. Its suggested M4 nut is listed as
3.2 mm high and 7 mm across flats. These are seller specifications, not an
accepted hardware stack. No exact 14 / 4.5 flat washer with a controlled thickness,
mass and bearing basis was found within this packet. A larger washer, different
thread, bent-open eye, industrial lifting boss or another material grade is not
substituted. Manufacturer grade names are not finished capacities.

As a topology precedent only, the official Initiator manual's page 3 screws an
eye into its molded baffle and ties the recovery cord to it. That is a different
support and load path from F2's paired through-ring M4 anchors. It supplies no
F2 capacity. The primary retains the architecture decision if a qualified small
finished eye cannot be obtained; no loop/strap/ring redesign follows automatically.

## Smallest remaining owner evidence set

Available technical pages and linked manuals/data sheets were sought before
reducing the request to these grouped measurements. This is an evidence request
for actual identified items **if already available**, not an instruction to buy,
modify, assemble, fire or test hardware.

1. **Exact cold motor identity and envelope:** photograph 78010 packaging/lot and
   all external datums; measure maximum case OD, thrust-ring OD/thickness and
   its front/aft datum, nozzle projection, forward projection and complete length.
   No opening or alteration of the motor is required or authorized.
2. **Actual 12912/19002 pair:** identify delivered revisions; measure tube ID/OD
   and collar fit, insertion depth, cap/lip/seat dimensions and engaged thread;
   record which faces actually contact and the complete aft removal/tool space.
   Nominal fit still needs a controlled cold/hot tolerance and adhesive basis.
3. **One exact finished anchor stack:** identify eye/washer/nut stock; measure
   usable thread including runout, total/eye envelope and closure, washer
   ID/OD/thickness and nut engagement through the actual ring; weigh the complete
   paired assembly against 18 g. Record accessibility and harness bend/chafe at
   both eyes. No credit from the 27 mm catalogue thread alone.

Dimensions alone cannot close eye/weld capacity, plywood washer bearing/peel,
locking, asymmetric recovery loading, hot/conditioned strength or installed
ring/tab/tube/body load transfer. Those require product-specific capacity
evidence or a separately authorized, defined physical qualification plan.
The motor thermal field and operating fit also remain independent tests; the
historical hot-handling warning is not thermal analysis.

**Stop:** bounded source research is complete; exact motor
contact and complete finished recovery hardware remain held. No new capacity,
fit, prototype, flight or WO-03 acceptance follows. F2/prior records, the 1.5 m
baseline, formal 15 / separate 15.5 m/s, full separate 50 g and G54/G12 tracks
remain unchanged.
