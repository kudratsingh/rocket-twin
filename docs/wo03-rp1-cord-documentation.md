# RP1 exact cord documentation — bounded source packet

2026-11-03 local; research closed 2026-11-04 05:16:34 UTC. This packet identifies
commercial cord records and the limits of their documentation. It makes no
architecture, mass-ledger, allowable or admission decision. Balanced RP1 v2 and
all earlier records remain separate. Hardware is unpurchased; the questions in
[the prepared supplier request](wo03-f2-recovery-supplier-questions.md) remain
**UNSENT**. No owner measurement or purchase request is made here.

The declared ceiling was 12 unique primary URLs / 15 minutes, counting failed
URLs. Research used all 12 URLs in 3 min 9 s. Two URLs were inaccessible; six
direct-access attempts failed, including four repeat fetches of the video after
one readable retrieval. Search discovery and repeat URLs do not increase the
unique count. The complete URL/access register is
[rp1-finished-cord-sources.yaml](../configs/studies/rp1-finished-cord-sources.yaml).

## Exact commercial records

| Field | Apogee 30327 | LOC NW-12 |
|---|---|---|
| Manufacturer record | [1500 lb Kevlar product](https://www.apogeerockets.com/Building_Supplies/Parachutes_Recovery_Equipment/Shock_Cord/Kevlar_Cord_1500), model 30327 | [Shock Cords](https://locprecision.com/products/shock-cords), inline variant 39778657730751, SKU NW-12 |
| Construction / size | Braided, hollow core; explicitly distinguished from tubular. OD 0.137 in (0.35 cm); tolerance absent. | 3/8 in tubular nylon, nominal 12 ft, factory-sewn loops. Width/thickness tolerance, loop geometry and bearing-point length absent. |
| Commercial snapshot | $1.71 per foot, minimum 10; displayed stock 10+. | Variant price 1239 cents = $12.39; `available: true`, `inventory_management: null`. This is an orderability flag, not a counted stock quantity. The page's default $8.12 / SC-500 selection is another product. |
| Mass evidence | Listed 2 g (0.07 oz); the listing does **not explicitly state per foot**. Per-foot mass remains an inference. | No documented finished physical mass. Inline commerce field `weight: 68` has no stated unit or finished-flight basis. Adjacent 12/15 ft variants share 68, and another much larger variant has 18: do not promote this field into a measured harness mass. |
| Advertised strength | 1500 lb test label; raw versus terminated, minimum versus typical, method and conditions unstated. | 1020 lb tensile label for the 3/8 in tubular class; raw versus complete sewn assembly and test conditions unstated. |

The exact LOC variant permalink and product `.js` endpoint failed access; the
variant identity, price and flag above were readable in the original page's
inline data. These are manufacturer storefront facts observed on this date,
not a reservation or supplier response. Neither product has a documented
revision/lot identity in the examined listing.

The [2017 LOC update](https://locprecision.com/blogs/rocket-journal/q4-2017-loc-update)
describes **flat** 3/8 in webbing, 950 lb, with a 12 ft mass of 1.2 oz. That is a
different construction/rating from today's tubular 1020 lb description. It does
not establish the current NW-12 mass, even though the nominal width and length
match. The existing 55 g main and 15 g leader budgets remain estimates in their
own source record; this packet does not replace either with catalogue metadata.

## What the manufacturer actually supports about terminations

The evidence below establishes published procedures or cautions, not a finished
joint allowable. No percentage knot efficiency is assigned.

| Source / location | Supported instruction or observation | Limit for RP1 |
|---|---|---|
| [Apogee Video 87](https://www.apogeerockets.com/Advanced_Construction_Videos/Rocketry_Video_87), transcript 00:09–00:29, 01:22–02:51, 03:41–04:37 | Low/mid-power demonstration: a slip knot cinches around the motor tube against a ring. Author reports a prior ring pull-through. He warns that CA-stiffened cord can break fibers during repeated bending and uses wood glue in this example. | Cord SKU, knot geometry, loading and strength are unreported. The video separately directs high-power viewers to another build; its adhesive/process is not an exact-30327 qualification or an RP1 process change. |
| [Apogee Mega Mako manual](https://www.apogeerockets.com/downloads/PDFs/04996_Mega%20Mako-instructions-web.pdf), kit 04996; p2 parts; p4 Step 6; p8 Step 30; p9 Steps 31, 34–35 | Parts 29544/29545 are 1500 lb Kevlar cut lengths. The manual uses a two-ended tube-wrap Y-bridle with double knots and epoxy coating; tied loops have taped tails, and a loop-through-loop junction is specified. | Stronger class-level precedent than generic knot advice, but these cut-part numbers are not explicitly declared equivalent to 30327. Two legs, supporting geometry and bond details differ. No measured capacity, bend ratio or conditioning data. |
| [Apogee Newsletter 338](https://www.apogeerockets.com/education/downloads/Newsletter338.pdf), May 7 2013; pp2, 5–6, Fig 8 | LPR replacement tutorial shows a square-knotted removable Kevlar loop with accessible tail; the knot can be secured with a small glue drop. Author reports heat deterioration after repeated ejection exposure and describes inspection access. | Different cord/rocket scope. The removable loop is deliberately kept out of ring fillets, unlike the Mega Mako bonded example. These are different procedures, not interchangeable qualification data. |
| [LOC Micro-Magg current page](https://locprecision.com/products/micro-magg), description; [linked instructions](https://cdn.shopify.com/s/files/1/0568/7489/3503/files/instructions-2020.pdf?v=1623675601), pp1–2 | Current page explicitly names NW-12 and a ring eyebolt. Manual lists NW-12, describes a separate 2 ft Kevlar mount, then conditionally uses a sewn loop for the parachute connection. | The manual's mixed generic instructions do not establish one unambiguous delivered NW-12 end-to-end route. No finished sewn-loop capacity or approved NW-12-to-30327 junction is supplied. |

These sources support the existence of practical knotted, wrapped and looped
connections. They do not establish that any one procedure preserves either
catalogue tensile label. No specific knot, tail length, adhesive, splice, sewing
pattern or joining method is selected here. In particular, a knot described in a
different kit does not supply an unmeasured RP1 load capacity.

## Exact data still unavailable

| Missing item after this search | What a supplier document could resolve | What later representative evidence would still control |
|---|---|---|
| Finished NW-12 mass/range; nominal length datum; sewn-loop dimensions, thread and stitch pattern | Exact current drawing, manufacturing specification and mass tolerance | Actual build ledger and packing geometry; no present hardware exists to measure. |
| 30327 mass-per-length basis, OD tolerance, braid/grade/finish and cut-part equivalence | Explicit unit basis and product specification | Installed cord length, tails and knot envelope; current estimates are not weights. |
| Raw versus finished strength for both labels; minimum/typical, test rate, gauge length, lot/sample count, failure mode | Traceable raw-cord and complete termination reports | The actual leader/main junction and installed paper/plywood/bond load path. A line report alone cannot qualify these joints. |
| Load-extension/unloading and rate-dependent energy behavior for NW-12 and 30327 | Product-specific curves with length, preload, conditioning and rate | Coupled deployment behavior with the selected route and packing; no stopping distance or peak coefficient is inferred here. |
| Minimum bend/contact diameter, abrasion limits, cyclic knot seating/slip and permitted loop mating surfaces | Exact product installation limits and characterized terminations | Actual ring edge, body lip, junction and repeated-flex contact. Generic knots have no assigned efficiency. |
| Hot/wet residual strength and extension, ejection exposure, UV/age effects and rejection criteria | Conditioned exact-product/finished-end results and inspection rules | Representative installed shielding, heat/chafe exposure and repeated deployment evidence under a later authorized plan. |

Apogee's product FAQ links [Newsletter 591](https://www.apogeerockets.com/Peak-of-Flight/Newsletter591)
and its [PDF](https://www.apogeerockets.com/education/downloads/Newsletter591.pdf)
(Jan 17 2023). Its nylon/heat, low-stretch cord and zippering discussion is useful
qualitative material guidance (PDF pp6–12). It supplies no exact NW-12 or 30327
force-extension curve, hot/wet retention factor or finished termination rating.
Likewise, LOC's 175% stretch statement is for its **elastic** range, not NW-12.
No generic raw Kevlar-fiber/nylon property is substituted for the braided or sewn
product, and heat resistance is not treated as immunity to ejection damage.

## Documentation outcome

The exact LOC SKU and current offered price are now resolved at storefront level;
physical stock count, current revision, finished mass and strength basis remain
open. Apogee identity, advertised OD, price and strength label are resolved at the
same level; its mass-per-foot basis remains unconfirmed. Published manufacturer
termination procedures were found, but no exact finished RP1 cord/junction rating
or environmental/dynamic curve was found within the declared search.

The prepared supplier questions therefore remain useful and unsent. Supplier
documentation may close product-specific fields; installed conditioned joint and
deployment evidence remain separate later gates. This source packet performs no
new calculation, solver run, selection or physical qualification.
