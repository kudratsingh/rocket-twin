# RP1 D1 — integrated fin-load and attachment decision

**Decision: keep 8.83 N·m and its consistent 331.125 N per fin enforced; admit no new construction.** D1 reconciles merged [FR1 PR75](https://github.com/kudratsingh/rocket-twin/pull/75) and [FP1 PR76](https://github.com/kudratsingh/rocket-twin/pull/76). The primary owns integration; the former cross-thread coordination question is closed. Neither study is adopted. Frozen AD1 v2 is unchanged. This is a load/material/connection decision packet, not another fin variant or a flight/build release.

Identity: `RP1-D1-load-attachment-decision-v1`, [executed record](../runs/wo03-rp1-d1-20261104-v1/record.json), [executed source](../runs/wo03-rp1-d1-20261104-v1/executed.py), [formatted audit utility](../scripts/wo03_rp1_load_attachment_decision.py). AD1 SHA-256 is `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`. D1 changes no vehicle part or physical mass. [ADR0015](adr/0015-rp1-load-and-attachment-evidence.md) records the governing interpretation; the original studies and failures remain authoritative at their original scope.

The declared packet was one CPU, 10 CPU seconds / 20 wall seconds, 16 combined FP1 material points using the existing elementary method, two historical formula evaluations, read-only flight/source checks and ordinary-plywood linear scaling. No flight, guide, CAD, FEA or thermal solve. The calculation body took 0.0165 CPU / 0.0223 wall seconds, excluding interpreter/import setup. One completed execution is retained; later formatting/lint fixes changed no arithmetic and its exact executed source is archived. No capped campaign was restarted. Supplier reconciliation used eight primary URLs within its declared 12 minutes. Bookkeeping transcribes 16 saved cases without recalculation.

## 1. Governing load recommendation

A fin's turning load is the force multiplied by its distance from the root. Here span is radial distance from the body; the per-fin moment is about the rocket's longitudinal direction for a tangential fin-normal force. Units are newtons (N) and newton-metres (N·m). The current tapered area is 0.00585 m² and its spanwise force centroid is 26.6667 mm. The normal force is not dynamic pressure times area alone: the small-angle normal-force coefficient also matters.

The historical formula is `F = q A CNa alpha × 3`, `AR = 2 span²/A`, `CNa = 2π AR/(2+sqrt(4+AR²))`, with alpha in radians. It assumes small angle and an unvalidated finite-aspect-ratio coefficient; Mach/Reynolds, interference, transient/rate and large-angle coverage are not established. The original 25 kPa / 5° profile was an engineering input; 40 kPa was a sensitivity, not a validated flight envelope. The factor of three is applied **once**, before the entries below.

| Case and acceptance role | Fin span / root / tip | Factored force | Factored moment | Decision |
| --- | --- | ---: | ---: | --- |
| Original C1 historical 40 kPa / 5° sensitivity | 90 / 120 / 60 mm |220.758696 N |8.830348 N·m | Historical formula origin; retain its original results |
| `RP1-FIN-Q40-A5-D3`, same formula on current planform | 60 / 130 / 65 mm |108.947063 N |2.905255 N·m | Separate diagnostic, **not adopted as the governing gate** |
| `RP1-FIN-LEGACY-883`, retained admission envelope | Current 60 / 130 / 65 mm distribution rescaled |331.125 N |8.830000 N·m | **Enforced** until a justified revision is explicitly recorded |

The 3.03932 ratio between retained and current-formula moments is a legacy-planform envelope, not another factor of three. A tip force at 60 mm would give only 147.1667 N for 8.83 N·m; it is not the consistent 331.125 N resultant and must not be used to understate connection shear. Neither 40 kPa nor 5° is claimed as a proven maximum. Retention of the inherited case is a conservative project admission decision pending a justified operating/adverse envelope, not a claim of measured aerodynamics.

### Flight compatibility and time alignment

The source-matching historical 52-part candidate is **not RP1**: it has a 66 mm × 1212 mm body and rectangular 120/120 mm, **70 mm-span** fins. RP1 has a 66.802 mm × 1250 mm body, 130/65 mm tapered 60 mm fins, different rings, recovery, mass distribution and unresolved physical rotational inertia. A second saved 739 g reference experiment also belongs to the older modular reference, not current RP1. Reusing either vehicle's attitude history would invent current flight evidence.

The local historic extraction `build/wo03-g80-fin-loads-v3/results.json` was read without rerunning it. All three saved flight Parquets, candidate/flight records, resolved candidate and study hashes match the extraction. The current producer script differs, while its saved `build/wo03-g80-fin-loads-v3/executed.py` matches the original `9298f95d…` hash. D1 records the current mismatch explicitly; the original source and outputs are historical evidence, not a current-tree reproduction.

| Historical powered flight only | Maximum dynamic pressure and its time | Angle at **that same time** | Peak coincident scalar estimated force / moment (DF1) |
| --- | ---: | ---: | ---: |
| Nominal calm |12.199 kPa at1.445 s |0.006483° |0.512339 N /0.017932 N·m at0.605 s |
| Growth / low thrust / high drag |6.973 kPa at1.400 s |0.005895° |0.502438 N /0.017585 N·m at0.720 s |
| Growth / high thrust |15.315 kPa at1.495 s |0.000710° |0.698344 N /0.024442 N·m at0.620 s |

These are calm-air scalar estimates, DF1, using that older fin's slope and span/2 centroid; they are neither recovered per-fin forces nor current factored design loads. The extraction preserves each load's simultaneous pressure and angle. No combination of maximum pressure, maximum incidence near apogee, or post-deployment 90° attitude is admitted. The cases show why independent maxima cannot be combined, but do not establish current wind/gust/rate bounds.

**Missing before a lower governing case can be adopted:** a fully defined current geometry and physically based inertia range, exact motor-source hypothesis, credible wind/guide/attitude/rate envelope, simultaneous pressure/incidence histories or a justified conservative bound, coefficient validity and uncertainty. No precise RP1 inertia or flight condition is invented. If these support a revised gate, present the complete retained-versus-proposed consequence comparison for a specific recorded decision. No arbitrary owner choice of a smaller number is requested now.

## 2. Complete attachment model and current evidence

The proposed construction family remains conventional through-the-wall fins: one integral tab passes through the paper body to the motor tube; rounded external epoxy fillets and internal bonds connect finite, flexible structures. Manufacturer examples are construction precedents, not capacity certificates. Carbon is optional. FP1's new layered tab and FR1's solid carbon tab have different stiffnesses and receiving slots, so their reactions cannot be copied.

```text
Distributed fin pressure → fin panel → integral tab
                              ├─ external fillets → paper body → ring perimeter / body shell
                              ├─ internal bonds → motor tube → ring bore bonds → ring → body
                              └─ aft tab-end adhesive (0.4 mm gap) → aft ring → body/motor tube
Forward ring is ahead of the tab: it is NOT a direct front-tab support.
Each arrow is a physical route requiring joint capacity AND finite deformation evidence.
```

The diagrams in the [separate workbench view](wo04-rp1-studies-20261104.md) expose these relationships. They do not imply equal sharing, accepted restraint or spatial stress/temperature fields.

| Connection or deformation | Defined geometry / existing evidence | Acceptance gap |
| --- | --- | --- |
| Panel / integral tab | Span60, root130, tip65 mm; tab109.4 ×17.451 mm | Directional conditioned E/G and strengths, fabrication tolerances; panel movement alone is insufficient |
| FP1 skins / core | Nominal5 mm wood; two0.5 mm skins through tabs and inner45 mm span; proposed maxstack6.4 mm | Finished secondary bond, finite slip, termination peel, core rolling shear, laminate separation; actual stock bounds unknown |
| Motor-side root bond | Rounded tab inner flatR15.95 versus tube outerR15.6845 mm; actual finite fillet/contact region, not a clamp | Adhesive thickness/fillet process, peel and slip, paper crushing/tearing and tube ovalization/twist |
| Body-side fillets / slot | Retained14 g internal +10 g external joint budgets; different slots per study | Joint finite translation/rotation and unequal side loading, actual contact widths and peel; a mass allowance is not a joint geometry/capacity |
| Aft tab end | Endz1189.6; ring begins1190 mm:0.4 mm adhesive gap, proposed bounds0.25–0.55 mm | No direct butt contact; elastic stiffness, mixed-mode capacity and ring bending are unverified |
| Rings and body | Forward1060–1072.2 mm, aft1190–1196 mm; motor tube1055–1220 mm | Ring bore/perimeter bonds, body bending/ovalization, finite outer support and accumulated movement; no perfectly rigid ends |
| Recovery / service | Loop1072.2–1077 mm; proposed knot box50×20×14 mm at1077–1127, R16.5–30.5, sector60° | Unchanged cord access, chafe/heat and motor removal still need actual geometry/fit; no new structure may occupy them |

A complete linear root representation maps force and moment into translation and rotation: `[y, theta] = Croot [F, M]`. It must include the flexible tab, motor tube, ring/bonds and body plus the body- and aft-side parallel routes. Body reactions depend on displacement compatibility and actual joint stiffness/contact. They are not `F/2` or `F/3` by convenience. Verify force/moment balance and reciprocal work, then separately verify strength, stiffness and method validity. Balance alone does not qualify a connection.

D1 independently checks the known cantilever tab compliance against the existing elementary method. For a fixed motor-side cut, its symmetric matrix is `Cff=h³/(3EI)+h/(kGA)`, `Cfm=h²/(2EI)`, `Cmm=h/EI`; its off-diagonal terms are equal. FP1's nominal tab contribution is0.505505 mm. The fixed cut is only a diagnostic boundary, not an installed support. An installed solution needs the motor-side compliance and finite body/aft connections; their stiffness matrices remain unknown. FR1's optimistic tube torsion and example spring values are not measurements or guaranteed bounds.

**Do not double-count the root.** FP1's panel bending plus panel core shear is0.355736 mm. A measured or validated **complete** root response replaces its0.505505 mm tab term **and** arbitrary0.100 mm extra reserve. With its other nominal assumptions, the remaining whole-root ceiling is0.644264 mm minus measurement/model uncertainty. This is an arithmetic requirement, not evidence of achieved movement. Merely assigning a spring to meet it closes nothing. Likewise the0.138760 mm residual after the fixed-cut component model is not a demonstrated allowance.

FR1's best evaluated finite-support point is1.185194 mm and its full130 mm single-face body mean is1.125200 MPa versus1 MPa. They fail at their stated sensitivity scope. The unqualified extra aft restraint means complete installed movement is unavailable; the result is not proof no real construction can ever pass. FP1's0.961240 mm already includes the unverified0.100 mm; it is not an installed pass.

## 3. Material decision and ordinary plywood

[Primary-source reconciliation](wo03-rp1-joint-material-reconciliation.md) and [source register](../configs/studies/rp1-joint-material-evidence.yaml) identify the exact gaps. PlywoodE1 GPa /5 MPa derives from a historical50% reduction of estimated2 GPa/10 MPa, not a conditioned stock certificate. Retain these screens. Do not invent a replacement reduction factor or transfer raw-fibre, resin-Tg, catalogue laminate or aluminum-lap data to a finished wood/carbon/paper joint.

Aircraft Spruce02-20750 is nominal5 mm ten-ply Finnish birch ($88.90 half sheet), but receiving4.8–5.2 mm,750 kg/m³ and directional hot/wet properties are not guaranteed. CP005 supplies characteristic cured-laminate values, not the proposed conditioned minima or skin-stock tolerance. Rock West204-11 CLT references likewise do not establish hot flexural or finished-joint properties. The [3M DP420 Off White data](https://multimedia.3m.com/mws/media/2365939O/3m-scotch-weld-epoxy-adhesive-dp420-off-white.pdf) uses0.13–0.20 mm film for room-temperature epoxy-FRP laps and0.25 mm for the cited hot aluminum laps: those results do not qualify FP1's30–50 µm porous-wood/cured-carbon secondary bond. WEST's [bonding guidance](https://www.westsystem.com/instruction/epoxy-basics/bonding-and-clamping/) warns against starvation. No adhesive is selected by D1.

D1 evaluates16 combined diagnostic points: woodE1/8 GPa × carbonE30/60 GPa × woodG100/200 MPa × bondfilm30/50 µm, at the existing minimum wood/skin dimensions and enforced load. **12 fail one or more retained screens**. Movement ranges0.694625–1.443827 mm; wood stress1.435489–9.692833 MPa. Higher wood stiffness can attract more wood stress in a bonded layered section. These are diagnostic inputs, not established bounds; full bond action is still assumed and peel remains unavailable. No passing point qualifies FP1, and no new fin construction follows from this calculation.

Ordinary plywood was not dismissed. Linear scaling of saved AD1 component results gives:

| Existing wood component model | Retained8.83 N·m: movement / stress | Unadopted2.905 N·m diagnostic: movement / stress |
| --- | --- | --- |
| Optimistic bonded wood wedges,5.8 mm fin |1.805416 mm /7.301269 MPa |0.594020 mm /2.402271 MPa |
| Bare5.8 mm panel |3.988119 mm /12.114699 MPa |1.312175 mm /3.985990 MPa |

These exclude a validated installed root and do not adopt the smaller case. They show that justified loads and real wood/joint properties could change the construction choice. Carbon is not predetermined. Under the still-enforced case the saved wood component fails, while carbon alternatives have their own unresolved/failed inputs. **No one complete correction is admitted to detailed construction analysis yet.**

## 4. Complete weight and launch consequences

D1 adds **0 g**. The [exact-once ledger audit](wo03-rp1-integrated-accounting.md) reconciles all58 FP1 /53 FR1 rows against55 AD1 rows and all16 saved mass/stock/harness cases. FP1's−4.670180 g and FR1's nominal−20.839669 g are alternative, conditional credits; they are not cumulative or accepted installed savings. Both retain14 g internal and10 g external bonds plus ring/fill/global finish budgets. Stock density, finished bond/edge mass and harness ends remain unverified. Full inertia remains unavailable, not zero.

| Alternative / unverified main mass | Nominal / adverse full total | Nominal / adverse1.5 m speed | Formal15 mass margin (nom / adverse) | Planning15.5 mass margin (nom / adverse) |
| --- | ---: | ---: | ---: | ---: |
| Frozen AD1 /55 g |934.549 /954.549 g |15.213 /15.033 m/s |+23.794 /+3.794 g |−30.750 /−50.750 g |
| FP1 /55 g |929.879 /949.879 g |15.256 /15.075 |+28.465 /+8.465 g |−26.080 /−46.080 g |
| FP1 /68 g probe |942.879 /962.879 g |15.137 /14.960 |+15.465 /−4.535 g |−39.080 /−59.080 g |
| FR1 nominal stock /55 g |913.710 /933.710 g |15.406 /15.221 |+44.634 /+24.634 g |−9.910 /−29.910 g |
| FR1 nominal stock /68 g probe |926.710 /946.710 g |15.285 /15.103 |+31.634 /+11.634 g |−22.910 /−42.910 g |
| FR1 max-thickness stock /68 g probe |935.696 /955.696 g |15.202 /15.023 |+22.647 /+2.647 g |−31.897 /−51.897 g |

Every row includes full separate50 g at1250 mm. Adverse adds20 g aft and the12.8 mm motor-CG probe. The audit contains the remaining cases, CG, static margins and first moments; its linked AD1/FR1 records retain recovery demands. FP1 did not record a recovery calculation. Those launch/balance outputs are transcribed saved estimates. The common external aerodynamic reference is retained, not revalidated after changed thickness/wedges. FP1 adverse68 g fails formal; all FP1/FR1 cases miss planning. FR1's maximum-thickness case is not a bound on finished mass. Longer guides remain conditional/unconfirmed and the1.5 m reference is unchanged. Current mass limits depend on the saved launch assumptions, not a universal rocket weight ceiling.

FP1 full purchase cost is unavailable: helper zeros are placeholders. FR1's$585.428 estimate retains the wood purchase for rings/nose and adds one$108.99 carbon sheet; no component is owner stock or purchased. D1 adopts neither ledger.


### Coupled balance and unchanged severe recovery proxy

[All16 complete consequence rows](../runs/wo03-rp1-d1-20261104-v1/complete-consequences.json)
link the saved mass/CG/guide figures to the unchanged severe mean proxy
`3 m (20.4²/(2×0.3)+9.80665)`. This is a once-factored stopping-distance estimate,
not an inflation or measured peak force. Only this scalar arithmetic was added
to FP1's saved mass rows; no new trajectory or recovery mechanism is assumed.

| Alternative / main | CG nominal / adverse from nose | Model stability nominal / adverse | Severe whole mean proxy nominal / adverse |
| --- | ---: | ---: | ---: |
|AD1 /55 g |763.693 /775.602 mm |1.433 /1.255 cal |1972.1 /2014.3 N |
|FP1 /55 g |761.832 /773.838 mm |1.461 /1.281 cal |1962.2 /2004.5 N |
|FP1 /68 g |756.016 /767.981 mm |1.548 /1.369 cal |1989.7 /2031.9 N |
|FR1 nominal stock /55 g |755.137 /767.495 mm |1.561 /1.376 cal |1928.1 /1970.3 N |
|FR1 nominal stock /68 g |749.314 /761.624 mm |1.649 /1.464 cal |1955.6 /1997.8 N |
|FR1 max thickness /68 g |753.095 /765.210 mm |1.592 /1.411 cal |1974.5 /2016.7 N |

## 5. Closure and next bounded deliverable

| Item | D1 result | What remains before engineering acceptance |
| --- | --- | --- |
| Integration ownership / concurrent studies | **Closed:** user assigns primary; both merged records reconciled | No coordination approval needed |
| Load arithmetic / case identities | **Closed at definition scope:** old/current geometry and once-applied factor distinguished | Current operating/adverse bound and any lower-gate decision |
| Nominal budget interpretation | **Closed:**0.100 mm is an assumption; complete root cannot be counted twice | Substantiated installed displacement/strength |
| Exact-once proposal accounting | **Closed as bookkeeping:** alternatives and55/68 probes explicit | Actual finished stock/adhesive/harness mass |
| Installed fin strength,1 mm movement, peel and flutter | **Open:** neither construction admitted | Conditioned properties, complete finite root, aerodynamic/dynamic validity and later tests |
| Thermal, recovery, exact motor/retainer, build/flight | **Open, unchanged** | Their recorded evidence and owner-performed gates |

The next bounded deliverable is the [representative material/root evidence definition](wo03-rp1-d1-test-definition.md) plus a supplier-response matrix, **before** a construction correction. It defines a small staged article, load fixture, process and acceptance; this is a plan only. Documentation can establish stock tolerances, layup and process recommendations. It currently cannot establish finished root compliance, wood/paper peel or hot/wet joint capacity. If those remain unavailable, stop analytical admission at that missing evidence; do not pick a spring, run full CAD/FEA or create a reinforcement family.

**Owner involvement:** no immediate coordination decision, hardware measurement or purchase is needed for D1. Hardware is unpurchased. Supplier questions remain unsent. A later specific request to contact suppliers or purchase/build/test the defined sacrificial article requires owner authorization; flight release is a separate gate. A reduced governing load requires its own supported decision, not a request to choose a passing number. G80 custom construction/performance, G54 upgrade and committed G12 PID-to-RL remain intact; a G80 result transfers no acceptance to the other tracks. WO-03 remains open.
