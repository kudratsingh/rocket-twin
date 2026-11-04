# RP1 FP1 / FR1 joint and material reconciliation

2026-11-03 local. Read-only evidence reconciliation for the primary-owned
FIN-LOAD/ATTACHMENT decision. FP1 and FR1 remain independent, unadopted records.
Ordinary plywood, FP1 carbon-faced plywood and FR1 monolithic carbon must each
receive the same explicit load/support/property scrutiny; carbon is not preset.
No construction, allowance, load, temperature limit or material strength is changed.

The declared source ceiling was **8 unique primary URLs / 12 minutes including
failures**, starting 2026-11-04 07:27:01 UTC. All eight slots were used in the
source pass, closed at07:30:17 UTC; later reads only revisited those URLs. CP005 direct fetches were
unreliable; manufacturer-indexed text is identified separately. The aircraft-ply
rules PDF was image-only in this tool and supplies no extracted certificate or
property evidence here. No supplier contact, purchase, test, numerical solver,
browser or Git operation occurred. Only this new note and
[its source/hash register](../configs/studies/rp1-joint-material-evidence.yaml)
are written. The recommendations below are a later test-plan proposal, not a
request to measure unpurchased hardware or authorization to build/load a fixture.

## Reconciliation result

FP1's nominal **0.961240 mm** total is a conditional model point. It includes
0.861240 mm panel/core/tab movement and an **unverified0.100 mm** allowance for
the remaining tube/body/ring/fillet connection. It is not an installed movement
prediction or a verified property envelope. Its perfect secondary-bond action
and fixed motor-side boundary cannot borrow a pass from FR1's separate finite
root study. FR1's spring and paper-tube-torsion assumptions are also unverified;
its failed sensitivities are not proof of physical impossibility.

Both retain **8.83 N·m and331.125 N**, already factored three once. They are an
explicit inherited moment/resultant envelope, not the direct40 kPa/5° result for
the current60 mm fin. No force, moment,1 mm movement or strength criterion is
lowered in this reconciliation. Any load-definition revision belongs to the
integrated decision, not to a material source interpretation.

| Quantity | FP1 assumption / saved behavior | What evidence actually establishes |
|---|---|---|
| Wood E | Nominal1 GPa; diagnostics5 and8 GPa | No exact02-20750 directional conditioned lower **and upper** bound. Higher E attracts more wood load in the composite section. |
| Wood strength / core shear |5 MPa bending; G200 MPa /1 MPa shear | Provisional inputs, not ten-ply stock allowables. The shear direction through a laminated thickness must be identified; in-plane shear and rolling/interlaminar shear are not interchangeable. |
| CP005 skins |0.45–0.55 mm, E45 GPa, stress150 MPa, density≤1600 kg/m³ | Receiving/model requirements; supplier page gives characteristic laminate data but no verified conditioned minima or thickness range. |
| Secondary film |0.03–0.05 mm per face; full composite action | No examined adhesive source validates this film range on the exact porous plywood/cured-carbon pair. |
| Root/skin termination | Mean interface shear0.551 MPa nominal; peel capacity null | A lower mean than1 MPa does not establish skin-end peel, bond slip, core tear or installed root stiffness. |
| FR1 laminate | Rock West204-11 nominal CLT E, plus half-E probe | Reference calculation and sensitivity, not measured flexural/hot-wet limits. Neither is a transfer rule for FP1 skins or wood. |

The collected FP1 material inventory contains useful rejected leads—G10/G11,
Divinycell, thin cured carbon and UD prepreg—but its JSON does not itself include
the final02-20750/CP005 leads. Those appear in the FP1 study and decision prose;
the present register supplies their direct-source trace. Ingredient data for a
different core, prepreg, thickness or layup cannot complete FP1's missing inputs.
The FR1 inventory remains [the earlier fin-input packet](wo03-rp1-fin-input-sources.md)
and the FR1 study/connection definition. Neither inventory contains a tested
finished RP1 connection.

## Both wood stiffness extremes matter

These are saved FP1 outputs, not new calculations:

| One changed input | Total movement mm | Maximum wood bending MPa | Result under retained screens |
|---|---:|---:|---|
| Wood E1 GPa |0.961240 |1.435489 | Nominal conditional point |
| Wood E5 GPa |0.860616 |4.822862 | Passes this isolated point; little wood-strength margin |
| Wood E8 GPa |0.813091 |7.123776 | Fails5 MPa despite less movement |
| Carbon E30 GPa |1.275045 |1.602428 | Fails1 mm |
| Wood G100 MPa |1.130022 |1.435489 | Fails1 mm |
| Extra attachment0.25 mm |1.111240 |1.435489 | Fails1 mm |

For bonded bending, `curvature = M / Σ(EI)` and material stress includes its own
E times curvature and distance from the neutral axis. Increasing wood E can
therefore raise wood stress while reducing curvature. A low wood E is not a
universally conservative material choice. The producer's one-input diagnostics
do not evaluate combined low-carbon-E/low-core-G/high-wood-E corners, asymmetric
faces, thickness/bond variation or bond slip. No new combined calculation is run
here. A future integrated assessment needs mutually compatible, conditioned
property ranges and the upper-E wood stress check with the retained5 MPa screen.
Discovering stronger wood does not silently raise that screen.

FP1's skin ends at45 mm of the60 mm span; its remaining15 mm is bare wood. The
producer changes EI abruptly there and computes mean shear flow in bonded areas.
That captures neither a real termination peel field nor finite adhesive shear
stiffness. Glue film supplies geometric separation in its section but no finite
slip model. Core G is an independent orthotropic input; it cannot be inferred
from an isotropic E/Poisson relation or replaced by a foam-core datasheet.

The FR1 supplement's corrected130 mm body-root face gives **1.125200 MPa**
single-face mean against1 MPa; its equal-share number is diagnostic only. Its
0.25–0.55 mm proposed aft gap is adhesive, not a butt stop. FP1's larger6.4 mm
stack and FR1's3.8 mm slot are different interfaces: their slots, bond areas,
carbon properties, root stresses and spare movement cannot be mixed. A new
integrated record must define one complete finite connection before admission.

## Exact stock and secondary-bond source findings

[Aircraft Spruce](https://www.aircraftspruce.com/catalog/wppages/finnishbirch.php)
lists **02-20750: nominal5 mm,10 plies,24×48 in half sheet,$88.90,AB/B**, with grain
along the cut half sheet. It does not guarantee4.8–5.2 mm, density≤750 kg/m³,
directional E/G, tension/compression/rolling shear or hot-wet strengths. The
[linked aircraft-plywood rules](https://www.aircraftspruce.com/catalog/pdf/Germanischer%20Lloyd.pdf)
are not a certificate tying a delivered lot to those proposed receiving values.
This packet extracted no text from that image-only PDF and assigns none of its
potential rules as tested product properties.

[CP005-2 manufacturer-indexed page](https://www.carbon-composite.com/en/Carbon-Plate-0.5mm/CP005-2)
identifies hot-pressed, cured0/90 fabric/epoxy, characteristic **EN2562 flexural
E60 GPa /850 MPa**, density1.56 g/cm³ and EN2563 ILSS about70 MPa. Its temperature
wording is “130°C (180°C)” with a short-term qualifier, without a test/cure or
hot-wet retention curve. These are finished-laminate characteristic values,
stronger evidence than raw-fiber values, but not guaranteed conditioned minima.
The product page offers several selectable sheet sizes; exact order dimensions
and price must stay tied to the selected variant. No0.45–0.55 mm tolerance is
established. Its ILSS describes the plate's own laminate, **not** the new
wood-to-cured-carbon adhesive interface.

| Candidate / primary source | Decision-driving process or data | What remains unavailable |
|---|---|---|
| [3M DP420 Off White V7, Dec2025](https://multimedia.3m.com/mws/media/2365939O/3m-scotch-weld-epoxy-adhesive-dp420-off-white.pdf), pp2–5 | Room-temperature epoxy-FRP lap result39.5 MPa uses25×102 mm adherends,12.7 mm overlap and **0.13–0.20 mm** films. Hot49/82°C aluminum14.9/2.7 MPa results use **0.25 mm** film. Preparation and cure are specified for the listed substrates. | Exact CP005/wood bond,30–50 µm film, hot-wet wood interface, peel and root stiffness. Aluminum conditioning results and bulk modulus are not those properties. |
| [ES6292 bulletin03Sep13-C4](https://ptm-w.com/technical-library/product-bulletins/Adhesives%20Bulletins/ES6292%20Bulletin.pdf), pp1–2 | Clean/roughened surfaces; mix100:31.5 by weight; normal heat-cure example follows2 h room-temperature gel with4–6 h at150–160°F. Typical wet glass/epoxy shear at150°F is1600 psi. | No bondline thickness range, exact wood/carbon substrate test or quantified peel capacity. Its cure temperatures do not qualify a wood/paper service-temperature limit. |
| [WEST bonding/clamping](https://www.westsystem.com/instruction/epoxy-basics/bonding-and-clamping/) and [surface preparation](https://www.westsystem.com/instruction/epoxy-basics/surface-preparation/) | Secondary bonding needs prepared cured surfaces; porous wood benefits from wet-out before the adhesive layer. Excessive pressure can starve the joint. Contamination removal precedes abrasion; cured-epoxy blush requires suitable removal. | No guaranteed30–50 µm cured wood/carbon film, conditioned stiffness or mixed-mode allowable. Generic instructions do not approve a particular adhesive/finish/CP005 process. |
| [WEST105/206 TDS, Oct2014](https://www.westsystem.com/app/uploads/2022/12/105-206-Epoxy-Resin.pdf) | Wood/composite wet-out and bonding application; minimum application16°C; thin-film cure/working times. DSC onset126°F and ultimate Tg139°F are cured-resin information. | No65°C loaded wood/carbon joint acceptance, exact film-range or hot-wet secondary-bond strength. Thin-film handling is not evidence for an arbitrarily thin structural bond. |

No adhesive is selected. The0.03–0.05 mm films may be difficult to maintain over
veneer roughness/absorption and the carbon finish; whether that happens is a
measured process question. Thickening the film or adding wet-out resin would
change thickness, mass and stiffness and needs explicit primary reconciliation.
Neither a large published lap value nor a glass transition temperature bypasses
that accounting or the peel requirement.

## Minimal representative evidence for a later reviewed test plan

The following is a common evidence sequence for ordinary plywood, FP1 and FR1;
only FP1 needs the additional skin/core process cell. Dimensions are proposed
engineering specimens, not a claim of compliance with an ASTM/EN method. A
qualified protocol/fixture review must define loading rate, guards, calibration,
conditioning, dwell/cycles and statistical treatment before any physical work.
At least three replicates per critical material direction/process/condition is
an initial repeatability screen, not a statistical design allowable.

1. **Identify the actual finished stock and bound its properties.** Reserve
   150×25 mm strips along both principal sheet directions, at actual thickness,
   for bare02-20750 and any independently considered ordinary plywood. Use two
   reviewed support spans,120 and60 mm, so bending and shear compliance can be
   separated rather than fitting everything to E. Record mass, dimensions,
   moisture, load/deflection, surface strain, irreversible set and failure mode.
   For CP005, use a matching thin-laminate flexure method with its full prescribed
   span/deflection limits rather than assigning a5 mm wood fixture to a0.5 mm
   sheet. FR1 similarly needs measured laminate D/E, directional strength and
   torsional/shear response. Test dry baseline and a documented representative
   wet condition at the retained45°C substrate state, retaining moisture during
   loading. A separate65°C adhesive/process condition does not authorize wood at
   65°C. Measure **both minimum and maximum wood E**, effective shear G and
   lower strength; reconcile their joint uncertainty before declaring a bound.

2. **Verify the finished secondary interface if FP1 remains under consideration.**
   First use25×102 mm actual carbon/wood coupons with12.7 mm overlap as an
   explicitly custom substrate variant of a lap geometry. Record force/slip,
   bondline cross sections, voids, adhesive penetration, crack origin and residual
   capacity after conditioning. At317.5 mm² overlap, the retained1 MPa mean screen
   corresponds to317.5 N; surviving that demand is only a process screen, not a
   peel or installed-root pass. Add25 mm-wide strip witnesses reproducing the
   actual FP1 cross section,45 mm skin-covered span,15 mm bare outboard span and
   full17.451 mm tab depth. Their actual skin-end geometry must match the
   eventual definition. Measure strain on both faces, relative slip and crack
   opening at the skin end under bending/reversed sign. Section same-batch
   witnesses to establish whether **both**30 and50 µm process endpoints are
   attainable without starvation. Acceptance data must demonstrate the claimed
   composite bending/shear compliance and no peel/delamination growth at the
   required load; nominal lap stress cannot replace this endpoint evidence.

3. **Measure the complete installed root, independently of panel material.** Use
   the retained240 mm body article, station980–1220, actual body/motor tube,
   rings1060–1072.2 and1190–1196, and integral tab1080.2–1189.6 with17.451 mm
   depth. Preserve the130/65/60/45 mm fin planform, actual slot, fillets, aft
   adhesive gap and recovery keep-out for the construction being examined.
   Grip the fore60 mm through a reviewed compliant saddle; neither ring nor
   motor tube is fixed ground. Measure grip slip/ovalization, body translation,
   fin-root rotation, tube twist, ring rotation and actual tip displacement.
   Separate force and moment loading identifies coupled translation/rotation
   compliance; a calibrated distributed-load test must then reproduce **both
   331.125 N and8.83 N·m** together with the declared panel distribution. A point
   load with the same resultant is only a root test unless panel-load equivalence
   is established. Reverse the fin-normal sign to expose asymmetric joints.

The measured installed response must stay within the unchanged **1 mm total** at
the required combined load, with uncertainties included and no progressive slip,
cracking, peel or permanent movement. To substantiate FP1's *particular* nominal
claim, remaining attachment motion must independently fit its **0.100 mm reserved
budget**; report separately the model's0.138760 mm residual to the total limit.
Do not silently replace one with the other. Measurement uncertainty should be
small relative to that budget (target≤0.010 mm in the relevant tip-equivalent
quantity). Interface strain/stress interpretation must use the measured
conditioned stiffness, check high-E wood attraction against unchanged5 MPa,
carbon against150 MPa where FP1 uses that screen, wood shear against1 MPa and
mean adhesive shear against1 MPa, while separately establishing the missing
peel/delamination capacity. No new factor of three is applied to already factored
loads. A successful small screening set still does not establish flight/fatigue
or population-minimum allowables.

This evidence can distinguish a material deficiency from bond starvation,
skin-end delamination, paper/tube compliance, ring motion or fixture slip.
Until those quantities are available, neither nominal FP1 success nor FR1's
different finite-support failure supplies the other's missing installed result.
The integrated decision remains with the primary before any new construction.
