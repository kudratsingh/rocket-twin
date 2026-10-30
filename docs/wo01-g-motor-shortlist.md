# WO-01: maximum practical G impulse, 1.6 mm baseline

Historical screen under the former 1.6 mm / three-second / average-TWR-3 requirements.
ADR-0006 supersedes those active constraints. Preserve all source findings and original
rejections; see [rebaseline trade](wo01-rebaseline.md) for reopened candidates and modes.

Reviewed 2026-10-29 (America/Los_Angeles). Local trade study, $0 compute.
**No exact configuration has cleared every required evidence gate.** The
recommendation for continued investigation is **Cesaroni 143G33-9A Mellow,
Pro29-3G case, standard Pro29 rear closure, no spacers**. This is an exact
hardware study candidate, not a purchase recommendation or a change to the vehicle.
Its recovery delay remains a later flight-analysis decision. G25W remains
quarantined; the molded F25 remains rejected. WO-01 is open.

## Constraints and calculation basis

Single commercial solid motor and existing TVC architecture; 1.6 mm tubes;
burn at least 3 s; average thrust / liftoff weight at least 3; loaded mass strictly
below 1.5 kg; single-motor impulse at most 160 N s. The 1.5 kg limit is a ceiling.
The starter's 320 N s aggregate allowance does not permit a single H motor.

The baseline weighs 529 g, including the 103 g F15 and original 16 g mount.
The motorless vehicle is therefore 426 g. Replace the complete assembled motor
once, without adding casing mass a second time. Screen with +20 g incremental
mount/retention mass and +50 g additional print/component growth, for **70 g
total allowance**. These are provisional engineering budgets, not measured
parts or proof that a mount can be built at that mass. The 20 g-only case is
retained for comparison, not used to describe a realistic total mass contingency.

`m_launch = 0.426 + m_motor_assembled + 0.020 + 0.050 kg`;
`TWR = published_average_thrust / (m_launch * 9.80665)`.

Reproduce summary screening with `make g-impulse-study`; inputs and source URLs
are in `configs/studies/g-impulse-selection.yaml`. Record:
`runs/wo01-motors-20261030T012229578107Z/record.json`.
All summary rows explicitly remain ineligible for selection. They do not invent
a thrust trace, motor CG, independent reference comparison or verified fit.

For a G motor to deliver at most 160 N s over at least 3 s, its consistently
defined burn-average thrust cannot exceed **53.333 N** (`I / t`). This is an
arithmetic screening bound, not a way to replace certification test data. It
eliminates most fast G motors from further long-burn investigation, including
otherwise attractive near-full G motors. Use measured/certified thrust rather
than the designation alone. A short low-thrust tail and rounded duration are
not evidence of three seconds of certified burn.

## Ranked follow-up shortlist

Priority accounts for requirement fit and evidence quality; impulse figures are
kept tied to their own sources. None is a fully verified eligible purchase.

| Follow-up priority | Exact candidate | Impulse / burn | Assembled motor; launch mass with 70 g allowance | Screening TWR | Decision |
|---|---|---|---|---|---|
| 1 | CTI 143G33-9A Mellow, Pro29-3G, standard rear closure, no spacers | 143.1 N s / 4.38 s | 197 g; 693 g | 4.81 | Best clear long-burn performance lead; 89.4% of 160 N s. Curve mass, California classification, installed dimensions and stock remain open. |
| 2 | CTI 159G54-12A Red Lightning, Pro29-3G | 159.1 N s / **2.97 s** | 198.2 g manufacturer (catalog also says 193 g); worst 694.2 g | 7.87 | Closest to full G but does not establish the three-second burn requirement. Do not promote rounded 3.0 s listings or a 3.026 s terminal-zero sample into a pass. |
| 3 | AeroTech G25W-10A SKU 072510, RMS-29/120 | Current reviewed TRA report: 109.49 N s / 4.20 s; legacy SU: 117.50 / 5.30, kept separate | Current product/report 168–170 g hypothesis; worst 666 g | 3.99 using report's 26.079 N | Quarantine retained. A directly checked US seller advertises stock, but source identity and curve/mass/envelope do not agree. |

The [manufacturer's G33 data](https://pro38.com/products/p29-3g/143g33-9a/)
and CAR letter (printed page 8 of the
[June 2014 certification report, third-party-hosted copy](https://cdn.imagearchive.com/rocketryforum/data/attach/145/145324-2014-June-06-07-CERT-LTR-June-17.pdf))
agree on Pro29-3G hardware, nominal 29 x 187 mm, 197 g loaded, 79.1 g propellant,
143.1 N s, 32.7 N average, 66.1 N peak and 4.38 s. The letter is dated
June 17, 2014; testing June 6, 2014. The manufacturer's summary was checked;
the CAR letter was reviewed through web text extraction, not local visual PDF QA.
Historical certification evidence does not by itself establish current launch approval.

The [cert-contributor G33 RSE](https://www.thrustcurve.org/simfiles/5f4294d20002e90000000814/)
has 197 g initial mass and a matching approximately 143.3 N s thrust integral,
but **89 g `propWt`**, versus the reported 79.1 g propellant. Its 89 g is also
197 minus 108 g post-firing mass. Inclusion of delay/other consumables is a
possible explanation, not a verified correction. Preserve the source and resolve
the depletion semantics before a reference model is built. Its thrust samples
show a brief ignition peak, roughly 36–40 N through about 3.1 s, and a declining
tail to zero at 4.461 s. Summary burn and source terminal time are distinct.

The G33 offers substantial *mass* margin: at 32.7 N, TWR 3 allows at most
1.1115 kg, leaving about **418.5 g** above the 693 g screening case. This does
not validate its thrust profile throughout flight or justify building heavier.
At TWR 5, the same average thrust allows only about 667 g; the 693 g case would
need the RSO's judgment under the applicable club code.

Nominal 187 mm length would require moving the motor front from 586 to 513 mm
to preserve the source-defined aft station at 700 mm: **73 mm forward**. That
reaches the existing servo/TVC region. Neither bore equality nor a one-dimensional
shift proves compatibility. Needed before a proposal can be accepted: complete
case/closure/nozzle drawing, thrust-ring and retention interface, gimbal sweep,
servo/linkage clearance, thermal isolation, added moving mass and motor-CG
measurement/assumption. No mounting station, pivot or airframe part was changed.

The [G54 manufacturer page](https://pro38.com/products/p29-3g/159g54-12a/)
gives 2.97 s and 86.5 g propellant. Its
[cert-contributor RSE](https://www.thrustcurve.org/simfiles/5f4294d20002e900000006e7/)
instead uses 96.8 g `propWt` and ends at 3.026 s. Its strong initial thrust
declines from about 107–122 N to about 21 N at 2.418 s. The 193/198.2 g mass
discrepancy is also retained. The current project parser reports terminal-zero
time; this distinction must remain visible, rather than using tail duration to
erase contrary published burn evidence. No relaxation of the minimum is proposed.

## Other motors screened together

| Candidate | Published impulse / burn | Launch mass with 70 g allowance / TWR | Result |
|---|---|---|---|
| AeroTech G12ST-P, reformulated 2021 product | 143.97 N s / 12.70 s | 646.3 g / 1.78 | Reject TWR. About 31 N early peak drops to roughly 10–12 N sustainer. Plugged motor also requires electronic recovery. |
| AeroTech G11-P older dataset | 139 N s / 13.6 s | 650 g / 1.60 | Reject TWR; do not interchange with reformulated G12ST. |
| AeroTech G8ST-P, newer data | 130 N s / 19.8 s | 653 g / 1.03 | Reject TWR; its approximately 7.9 N published peak is also insufficient for TWR 3. |
| AeroTech G40W molded-case | 97.1 N s / 2.4 s summary; source terminal zero 2.30 s | 619 g / 6.74 | Reject burn. Historical 113.74 N s / 3.06 s PML/AeroTech data describe another dataset. |
| CTI 150G50-15A, Pro38-1G | 150 N s / 2.87 s | 714 g / 7.50 | 38 mm: reported burn fails. A shared 70 g sensitivity is not a designed 38 mm mount mass. |
| CTI 137G58-13A, Pro38-1G | 136.8 N s / 2.36 s | 708.5 g / 8.33 | 38 mm: reject burn. |
| AeroTech G69N-P, RMS-38/120 | 136.7 N s / 1.9 s | 697 g / 10.58 | 38 mm: reject burn, also requires plugged-motor recovery provisions. |
| CTI 127G46-11A, Pro38-1G | 127.3 N s / manufacturer 2.76 s | Not developed further | 38 mm: reject burn. |
| AeroTech G12-RCT, RMS-R/C-32/60-100 | Catalog 87.2 N s / 8.6 s (NAR list says 93 N s) | 627 g / 1.66 | 32 mm: reject TWR before resolving other discrepancies. |

Primary or certification-source references for these rows: manufacturer's
[Pro29 catalog](https://pro38.com/product-category/pro-29/),
[Pro38 catalog](https://pro38.com/product-category/pro-38/),
[G50](https://pro38.com/products/p38-1g/150g50-15a/),
[G58](https://pro38.com/products/p38-1g/137g58-13a/),
[TRA G12ST report](https://d3l66gvjdr7rqw.cloudfront.net/Templates/170652/myimages/g12st%20cert%20letter_1656544056805.pdf),
[G12ST newer curve](https://www.thrustcurve.org/simfiles/6015a048b94d0e00040a8436/),
[G8 newer curve](https://www.thrustcurve.org/simfiles/60159fcfb94d0e00040a8435/),
[G40 molded curve](https://www.thrustcurve.org/simfiles/5f4294d20002e90000000463/),
[G69 certification catalog](https://www.thrustcurve.org/motors/AeroTech/G69N/).
Catalog summaries are sufficient for a negative screen, not selection approval.

Other Pro29 G reloads in the manufacturer catalog burn less than 3 s. The
high-impulse G118/G125/G138 families also exceed the 80 N average-thrust boundary;
spark-producing and hybrid motors are outside the requested certification scope.
The old PML G40 is explicitly
[out of production](https://www.thrustcurve.org/motors/PML/G40W/).
The old G35 is
[out of production and 2.9 s](https://www.thrustcurve.org/motors/AeroTech/G35/).
Historical AeroTech G33's certificate expressly says High Power Rocket; an
obsolete certificate is not evidence of current no-certification eligibility.
No larger-diameter motor screened establishes a substantially better eligible
three-second option. A 38 mm redesign is therefore not recommended. It would
require a new bore, retention, gimbal rings/linkage and clearance assessment,
added-mass budget and new static comparison; none is silently applied here.
The complete existing ThrustCurve API snapshot in `data/g-motor-survey/all-g.json`
contains 93 G records (SHA-256
`8835c14ace71cf06f7f41b399f8b82277d5c1d7a14c91d7df57c7b104f8cb05d`).
All were checked, including out-of-production entries: 82 report burn below 3 s,
42 fail the general motor-type/thrust filters and 24 are marked OOP; these counts
overlap. Six metadata leads remain: G12-RCT, G25W, G8ST, G11, CTI G33 and G12ST.
The TWR, identity and availability screens above dispose of or hold each one.
Historical Ellis G20/G35/G37 are OOP, rather than hidden long-burn purchase options.
Audit: `runs/wo01-g-catalogue-audit-20261030T012229241691Z/record.json`.
The existing retrieval record is
`runs/wo01-g-survey-20261030T011221865663Z/record.json`; this audit did not claim
a new download. The catalogue is an index, not a substitute for all current
certification reports and exact stock records.

## Purchase and California eligibility evidence

Stock was read directly from product pages on the review date; no transaction,
account access, reservation or external message was made. A listing can change.

| Exact item | Direct source | Observed status |
|---|---|---|
| AeroTech G12ST-P DMS, Wildman SKU 6030 | [Wildman](https://wildmanrocketry.com/products/g12st-p-29mm-dms) | Archived direct product JSON `available: true`; live page Add to Cart, $48.49; fails vehicle TWR |
| CTI G33-9A reload, Wildman SKU 2771 | [Wildman](https://wildmanrocketry.com/products/pr29-3g-my) | Sold Out, $39.45; direct product JSON also unavailable |
| CTI G33-9A reload, product 1575 | [Chris' Rocket Supplies](https://www.csrocketry.com/rocket-motors/cesaroni/motors/pro-29/3g-reloads/cesaroni-g33-9a-mellow-rocket-motor.html) | Out of stock, $40.47 |
| CTI Pro29-3G case, product 1104 | [Same dealer](https://www.csrocketry.com/rocket-motors/cesaroni/hardware/pro-29/3g-hardware/cesaroni-29-3-grain-case.html) | Out of stock, $44.66 |
| Standard Pro29 rear closure, product 1237 | [Same dealer](https://www.csrocketry.com/rocket-motors/cesaroni/hardware/pro-29/6gxl-hardware/cesaroni-29mm-rear-closure.html) | Out of stock, $33.50 |
| CTI G54-12A reload, product 1146 | [Same dealer](https://www.csrocketry.com/rocket-motors/cesaroni/motors/pro-29/3g-reloads/cesaroni-g54-12a-red-lightning-rocket-motor.html) | Product page out of stock, despite older category page claiming stock 9; product page governs this screen |
| AeroTech G25W-10A, A072510 | [Rocket.Supplies](https://rocket.supplies/proddetail.php?prod=A072510) | Product page in stock 4, $34.99; accompanying specifications repeat conflicting legacy numbers |

CAL FIRE's March 3, 2021 letter explicitly approves **G12ST-P and G8ST-P as
Model Rocket Motors**, requiring the state seal and licensee registration on
motor or sealed packaging. The complete letter was visually checked locally at
`data/g-motor-survey/csfm-model-2021-03-03.pdf`, SHA-256
`e10724f77a5968a1b5baaf22ee0372b181c52d16755d06b1b9241ab0a3a58988`.
[Manufacturer-hosted original](https://d3l66gvjdr7rqw.cloudfront.net/Templates/170652/myimages/csfm%20rcs%20approvals%203-3-21_1656441446956.pdf).
G12ST-P therefore has useful exact California classification and purchase evidence,
but fails this vehicle's TWR with either the 20 g or 70 g allowance. Its advertised
147 mm length also differs from the test's 155.98 mm overall length; no full
installed-envelope correspondence is claimed.

No in-stock complete G33 configuration was verified. Aggregators were used only
to find leads; they are not evidence that an eligible motor can currently be bought.
The manufacturer's 2020 G33 ignition-pellet bulletin was also identified through
its [own forum announcement](https://www.rocketryforum.com/threads/cti-discussion-thread.162183/).
Affected-lot applicability and any factory-approved resolution need confirmation
for offered stock; no field modification is prescribed by this study.

Current [NAR high-power criteria](https://www.nar.org/content.aspx?club_id=114127&module_id=667402&page_id=22)
and [Tripoli code v2, January 2026](https://www.tripoli.org/content.aspx?club_id=795696&module_id=520420&page_id=22)
state the relevant 160 N s / 80 N boundaries and 125 g propellant criterion, with
hybrids and spark-producing motors treated separately. The G33's 143.1 N s,
32.7 N and 79.1 g satisfy those numerical boundaries. This is an inference from
current general rules, **not exact California or club clearance**. Do not reject
it automatically by treating an older 62.5 g definition as current nationwide policy.

Conversely, the manufacturer's
[FAQ](https://cesaroni-aerospace.com/frequently-asked-questions/) still calls an
approximately 80 g Pro38 G79 a US high-power motor. California's classification
and adopted rules must be established for the exact reload; this conflict is
not resolved by choosing the more convenient source. The
[OSFM program](https://osfm.fire.ca.gov/what-we-do/fire-engineering-and-investigations/fireworks/)
is the state classification authority. No exact G33 OSFM classification paper
or packaging seal was obtained, and the G33 catalog page does not display the
approval flag seen on some other motors.

[ROC's current rules](https://rocstock.org/flying-with-roc-2/) require an OSFM
stamp on motor, packaging or paperwork, inspection before every flight, stable
flight and safe recovery evidence, and certification for high-power flights.
Its posted waiver is 7,000 ft AGL. General eligibility does not establish RSO
acceptance of this finless TVC rocket or its eventual altitude. Tripoli normally
expects TWR 5; an RSO may allow 3. The project target remains 3, not an automatic
club approval. The actual club/date and prior active-stabilization acceptance
remain unconfirmed. No flight prediction has been made in WO-01.

## F22 post-test closes the earlier performance question

The owner supplied `Aero_F22J_2026-05-02_tr.pdf`. An unchanged copy is archived
at `data/f22-study-sources/current_nar_posttest.pdf`, SHA-256
`f7d8a5d3bcad0e7e32d11be0e8560552f41e6ee8b043241ff951f5ad98608b58`.
All three pages were rendered and visually reviewed. The May 2, 2026 six-motor
test gives 55.08 N s / 3.83 s / 14.52 N. The report says FAIL because all three
seven-second-delay samples had excessive measured delays; this is not itself
proof of a formal decertification.

The report's page 3 supplies a representative RASP trace and 130.9 g initial
mass. The extracted points were visually checked, preserved separately and not
scaled to the summary: 55.808607 N s / terminal time 4.178 s / 13.357733 N.
At +20 g mounting allowance it gives 576.9 g and **TWR 2.361**; even the report
mean thrust gives only **2.567** at that mass. F22 fails the unchanged baseline
before adding the further 50 g vehicle-growth reserve. Static RocketPy comparisons
pass under the same estimated motor-CG assumption; numerical agreement does not
make the motor meet the thrust requirement. Full evidence and reproducible input
are in `configs/studies/f22-source-evidence.yaml` and `f22-selection.yaml`.

F22 record: `runs/wo01-motors-20261030T011052177790Z/record.json`.
`make check smoke f22-study g-impulse-study` passes, 44 tests. Baseline, thinner
proposal, prior motor curves and earlier evidence archives remain unchanged.
No procurement, hardware change, flight simulation, paid run or external message.

## What would make an exact recommendation possible

For the recommended G33 study configuration, obtain a currently available,
identified reload lot and the matching Pro29-3G case/closure; verify current
certification and the ignition-pellet bulletin status; reconcile curve mass
semantics with the certification letter; obtain the complete assembled drawing
and actual mass/CG assumptions; verify OSFM model classification and ROC's
acceptance without HPR certification. Then prepare a separate vehicle proposal,
mount/retention mass budget and static reference comparison for review.

If those cannot be established, the present requirements do not yet have a
verified purchasable solution. No source data is stretched, no restriction is
relaxed and no ambiguous motor is selected to manufacture an answer.
