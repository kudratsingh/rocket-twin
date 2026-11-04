# RP1 fin/root input sources — bounded evidence packet

2026-11-03 local. This packet traces the retained load/material hypotheses and
documents one possible **monolithic quasi-isotropic carbon/epoxy fin with integral
through-wall tab and finite fillet bonds** for a later primary-owned study. It
does not select thickness, change the load case, resurrect the stopped C2 socket,
change an active specification or establish admission. RP1 AD1 v2 remains frozen.

Before browsing, the ceiling was declared as **14 unique primary URLs / 18 minutes,
including failures**. Research began 2026-11-04 06:20:33 UTC and the last new URL
was read at 06:23:54 UTC. All 14 URL slots were used. No unique URL was wholly
inaccessible; one repeat shell download of the already readable tolerance PDF
failed DNS. No contact, purchase, owner measurement request, solver, browser or Git
operation occurred. The [source register](../configs/studies/rp1-fin-input-sources.yaml)
records URLs, scope, local hashes and missing properties. The primary redirected
the final four slots from G10 to finished CFRP evidence; G10 remains context only.

## Load history and what is actually retained

| Input | Trace | Evidence boundary |
|---|---|---|
| 25 kPa, 5°, DF3 | [Engineering profile](../configs/engineering/wo03.yaml), `loads` | Original prescribed engineering screen; no exact current G80 flight observation establishes it. |
| 40 kPa at 5°, DF3 | [Fin-design study](../configs/studies/wo03-fin-design.yaml), `bounded-40kpa-5deg` | Explicit upper sensitivity **at 5° only**, carried into F1/F2. Not an all-incidence or current RP1 flight bound. |
| Historical 8.830347836 N·m / 220.758695902 N per fin | [C1 source lock](wo03-c1-attachment-source-lock.md) | Older span90/root120/tip60 mm C1 planform, already factored three once. |
| Frozen F2 2.905255025 N·m / 108.947063440 N per fin | [F2 selected record](../runs/wo03-g80-f2-selected-20261103-v2/record.json), `fin_screen` | Span60/root130/tip65 mm; its own 40 kPa/5°/DF3 result under the repository formula. |
| AD1 v2 8.83 N·m / 331.125 N | [AD1 producer](../scripts/wo03_rp1_attachment_definition.py), `plate_displacement`; [final record](../runs/wo03-rp1-attachment-definition-20261103-v2/record.json) | Current 60 mm tapered distribution is explicitly **rescaled to the retained 8.83 N·m**. This is a separately imposed moment envelope, not the direct current-planform 40 kPa/5° result. |

That last distinction explains the larger AD1 movement demand. The AD1 producer
first forms an already factored pressure distribution, then normalizes its moment
to 8.83 N·m. It does not apply a second independent DF3. The retained moment is
approximately three times the frozen F2 current-planform result; that historical
transfer must be stated as its own load assumption. **This packet does not reduce
or replace it.** The required 40 kPa/5°/DF3 case and current AD1 movement case are
both preserved for the next primary-owned calculation.

Dynamic pressure is `q = ρV²/2`; a normal-force coefficient and reference area are
still needed to obtain fin force. [NASA's coefficient explanation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/lift-coefficient/)
also cautions that geometry, viscosity and compressibility affect coefficient
transfer. In this repository, the diagnostic coefficient is
`CN = CNa × |alpha_rad|`, with the low-angle finite-wing slope from
[`fin_attachment.py`](../src/analysis/fin_attachment.py); the saved-flight extractor
caps CN at 2. The area is **one fin's planform**, not body reference area. Thus
40 kPa is not automatically a uniform 40 kPa difference across the fin. The
model's mean normal pressure is `q × CN`; the design factor multiplies demand once.
No extra factor of three is due merely to the rocket having three fins.

The scalar slope is a repository finite-wing approximation, not a measured
single-fin coefficient for this rocket. It does not resolve roll-dependent
incidence of each fin, body/fin interference, signed local flow from rates/gusts,
the two-face pressure field, torsion or in-plane loading. The earlier extractor
uses a uniform-load half-span arm; F1/F2 use the centroid of the linearly tapered
chord distribution. Neither choice validates installed root reactions.

## Historical trajectory evidence is not the RP1 envelope

The named source [fin-load intake](wo03-g80-fin-loads.md) and
[its configuration](../configs/studies/wo03-g80-fin-loads.yaml) refer to the older
**52-part** integrated G80 identity
`62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009`.
They do not refer to RP1 AD1 v2. Its documented values are:

| Old saved case | qmax kPa | Alpha at qmax | Peak speed m/s |
|---|---:|---:|---:|
| Nominal calm | 12.19855 | 0.00648° | 147.925 |
| Growth / low thrust / high drag | 6.97324 | 0.00590° | 111.667 |
| Growth / high thrust | 15.31527 | 0.00071° | 165.903 |

These are sampled modeled quantities, not flight measurements. The q peaks are
not simultaneous 5° events. The intake's separate `qmax × CN=2` sensitivities
deliberately combine independent extrema and are not simultaneous recorded loads
or validated bounds. Its time-aligned small-angle powered scalar forces are much
smaller, but the coefficient/domain and limited scenarios remain unvalidated.
Large coast/descent alpha lies outside the stated diagnostic band and cannot be
used as a linear high-incidence load result.

The current F2 decision explicitly deferred full new flight work. AD1 v2 says
full flight was not run and physical inertia remains unavailable. The global
engineering profile's 300 m/s vibration speed ceiling is itself labeled an
exploratory assumption until a matching flight envelope exists. It is not a
derivation of 40 kPa, and neither it nor the old 165.903 m/s peak constitutes a
current RP1 speed/q/incidence envelope. A defensible future load envelope needs
same-configuration, time-aligned q, Mach and local incidence plus justified wind,
rate and coefficient uncertainty. No source found here permits dropping the
retained required case.

## Plywood and temperature assumptions

The [engineering profile](../configs/engineering/wo03.yaml) starts from estimated
weak-direction birch-ply **E2 GPa / generic strength10 MPa**. The
[bonded-support study](../configs/studies/wo03-bonded-support.yaml) explicitly lists
hot **E1 GPa / strength5 MPa**, carried by the F1/F2 and AD1 producers. These are
50% engineering sensitivities, not a manufacturer hot-property curve. The profile
cites the USDA Wood Handbook as general wood context, but supplies no exact
aircraft-ply test or derivation making those scalar values selected-stock
allowables. [Earlier material evidence](wo03-material-evidence.md) already records
that aircraft plywood density evidence does not establish thin-sheet stiffness,
directional strength or hot joint properties.

The exact [Aircraft Spruce record](https://www.aircraftspruce.com/catalog/wppages/finnishbirch.php)
still identifies **02-20850**, nominal6 mm,12 plies,24×48 in half sheet,$69.75,
AB/B grade. It says half sheets are cut with grain. It gives no exact-lot elastic
tensor, bending/rolling-shear/tension-perpendicular/hot-wet properties or thickness
tolerance. AD1's5.8–6.2 mm incoming window is a proposed inspection requirement,
not that supplier's guarantee. Other Metsä layups and thicker general-purpose
birch tables cannot fill those fields.

The **45°C wood/paper screen** is a project provisional substrate criterion;
**65°C** is a separate conditional adhesive/process screen. Neither is an exact
wood service limit or a measured joint temperature. A prescribed300°C motor-case
scenario is not a300°C fin/substrate observation. No accepted RP1 temperature
field connects these numbers to a tested directional plywood allowable.

## One construction direction: solid quasi-isotropic CFRP with integral tab

The following are source inputs for that one construction direction, not three
admitted fin designs. Rock West204-11 is the principal examined stock identity;
the DragonPlate records expose the alternative-product/property limits.

| Exact offered laminate | Stock / dimensions | Finished-laminate information | Remaining limit |
|---|---|---|---|
| [Rock West204-11](https://www.rockwestcomposites.com/204-11.html), RevNC layup | 12×12×0.125 in, $108.99; order control present, no live counted stock displayed in retrieved page. Indexed snapshot said backorder; immediate supply is unconfirmed. | Infused carbon/epoxy; five fabric layers alternating0/90 and±45; density1.52 g/cm³. Ex=Ey6,664,000, Gxy2,546,000 in default imperial property table, interpreted as psi (about45.95/17.55 GPa). | These are explicitly unguaranteed **CLT reference calculations**, not tested D790 flexural properties. No finished flexural strength or hot/wet retention curve supplied. Table unit interpretation needs confirmation before a controlled engineering input. |
| [DragonPlate FDPLHP04T1212](https://dragonplate.com/quasi-isotropic-carbon-fiber-uni-sheet-1_8-x-12-x-12) | 12×12×1/8 in, $147.53, stated3–5 days before shipment; stock count absent. | Solid UD0/90/±45 prepreg laminate; approximate density0.056 lb/in³; listed Tg250°F. | Published modulus is **raw fiber** modulus, not laminate E. Finished E, flexural strength, tested Tg method/cure and thickness tolerance not supplied on this page. |
| [DragonPlate FDPLSC04____1212](https://dragonplate.com/quasi-isotropic-solid-carbon-fiber-sheet-1_8-x-12-x-12), different woven family | 12×12×1/8 in; $123.92 before finish selection; stated3–5 days. | Balanced/symmetric woven0/90/±45, approximate density0.055 lb/in³. | Listed maximum140°F (60°C), **not** the UD product's250°F. No finished elastic/flexural or tolerance data. Do not combine the two families' best fields. |

Rock West's linked [RW-PS-070 RevE, Aug6 2025 tolerance sheet](https://www.rockwestcomposites.com/on/demandware.static/-/Sites-rwc-master-catalog/default/dw5c7d718f/downloads/RW-PS-070-Stock-Plate-Panel-Angle-Tolerance-Sheet.pdf)
assigns solid infused/press-cured plate in the0.010–0.130 in band **±0.010 in**.
For nominal0.125 in this gives **2.921–3.429 mm**, a supplier tolerance-derived
range, not a measured cut part. Its stock flatness allowance is also broad; no
machined fin/tab flatness or bond-gap tolerance follows from nominal thickness.

Rock West lists Tg194°F (90°C). Its linked
[Rhino1411/4111 TDS, Rev0, p2](https://www.rockwestcomposites.com/on/demandware.static/-/Sites-rwc-master-catalog/default/dwfef1ba74/downloads/Rhino-1411-4111-Infusion-Resin-TDS.pdf)
locates that number in **neat-resin DSC**, after2 h35°C +4 h65°C +2 h85°C cure.
The same bulletin's86 ksi flexural result is for **A-260 unidirectional E-glass**,
not204-11 carbon fabric. Neither the neat-resin Tg nor that glass result supplies
the finished CFRP's loaded hot/wet flexural strength. Actual plate cure/lot and
property retention remain open; no raw fiber or neat resin value is a fin allowable.

## Root/joint precedent and missing evidence

[Madcow's fiberglass DX3 manual](https://madcowrocketry.com/content/pdf/fgdx3.pdf)
(K-170; pp1–2, Step3) documents1/16 in G10 fins with tangs bonded at the motor tube,
epoxy on both tang faces, and fillets on both fin/body sides. It also specifies
cleaning before abrading fiberglass. The
[current fiberglass kit page](https://www.madcowrocketry.com/2-6-fiberglass-dual-deploy-dx3/)
is A-0001, made to order,38/54 mm mounts. This is a conventional TTW topology and
surface-preparation precedent, not G80 approval, a carbon-tab bond test or a
paper-body joint stiffness. The separate [paper/ply DX3 manual](https://www.madcowrocketry.com/content/pdf/dx3.pdf)
(K-126, p1) lists G80T-7 and1/8 in plywood. Its G80 recommendation does not transfer
to the fiberglass version or exact current78010 G80-10T.

The [ES6292 bulletin](https://ptm-w.com/technical-library/product-bulletins/Adhesives%20Bulletins/ES6292%20Bulletin.pdf)
supports adhesive/process material context only. Its glass-process shear and Tg
results do not specify finite CFRP-tab/paper-motor-tube/paper-body/ply-ring joint
rotation, peel or allowable bondline. No source here establishes root Kθ,
paper crush/interlaminar strength, machined tab edge strength, ring/end transfer,
actual fillet stiffness, hot-wet mixed-mode strength or installed flutter.

G10 context reinforces the same boundary: [NorplexNP500A](https://www.norplex-micarta.com/wp-content/uploads/2017/07/TDB_NP500A.pdf)
has directional D790 typicals, but is not identified as
[Rock WestG10-125-1212](https://www.rockwestcomposites.com/g10-125-1212.html).
[Norplex's explanation](https://www.norplex-micarta.com/structural-materials/what-is-g-10/)
explicitly notes that a generic G10 designation does not fix resin chemistry or a
minimum hot/wet Tg. Neither generic G10 nor CFRP panel properties qualify a joint.

The primary can therefore study one exact monolithic CFRP stock and its complete
replacement mass under unchanged loads, while retaining unknown hot/directional
strength where appropriate. Whether it is stronger **and lighter as an installed
assembly**, and whether the finite conventional TTW root transfers the demand,
remain decisions/calculations outside this source packet. No supplier strength,
mass saving, rigid support or engineering pass is selected here.
