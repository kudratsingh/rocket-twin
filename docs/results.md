# Results

## Preliminary model calculation — WO-01

Single CPU calculation, **unvalidated**, not flight data. Date: 2026-10-29; seed: 0;
cost: $0. Run ID: `wo01-20261029T212018229556Z`. Config SHA-256: `213d1416def0cef8c21d065380e38155f0c0c6ca1f35062d917fa504e9a2ac19`.
Code SHA-256: `af25b12c21b5daa1ef6e0ef228e61517aa996cd26473cd89520fe7fd5f62315d`. Full numeric evidence: `runs/wo01-20261029T212018229556Z/record.json`.

| Quantity | Liftoff | Burnout |
|---|---:|---:|
| Mass (kg) | 0.529 | 0.469 |
| CG (m aft from nose) | 0.416131 | 0.387108 |
| CP (m aft from nose) | 0.07323214 | 0.07323214 |
| Static margin (cal) | -4.3961 | -4.0240 |

Average-thrust/liftoff-weight: **2.772**, below the WO-01 target of 3.
`make check smoke tiny` passes; `make benchmark` deliberately exits nonzero while
thrust/weight and certified-curve imports remain unresolved. The static reference gate now passes.

Burn duration is a cited 3.45 s from the [historical NAR certificate hosted by
ThrustCurve](https://www.thrustcurve.org/motors/cert/60c63bfcb5bc370004713e7f/F15.pdf).
The 0.103 kg nominal loaded motor mass is from its RASP header; the recovery-delay
variant is not selected. No current certification or flight-readiness claim is made.

Ogive CP now uses the volume identity from Barrowman's slender-body treatment,
checked against the analytic tangent-ogive volume. This replaces the initial
0.466 L approximation (74.56 mm) with 73.2321 mm; the initial report remains in
its original run record. [RocketPy's nose implementation](https://docs.rocketpy.org/en/latest/_modules/rocketpy/rocket/aero_surface/nose_cone.html)
uses the same volume identity. RocketPy 1.13.0 has now been executed locally (see below).

The default has no fins, so the nose dominates its normal force and static margin
is negative. Inertia uses circular shell slices for the nose and coaxial box/cylinder
envelopes elsewhere; detailed CAD validation is pending. The nose's radial wall
approximation excludes its shoulder. Off-axis placements are not modelled. Uniform
propellant depletion fixes motor CG and does not model grain regression. Motor curve
integration, once imported, maps time to depleted fraction via cumulative impulse.
Drag coefficients and printed masses remain estimates.

No WO-01 benchmark is claimed. No trajectory simulation has started.

## Static-property reference check — WO-01

Run `wo01-20261029T215941498110Z`; config SHA-256 `213d1416def0cef8c21d065380e38155f0c0c6ca1f35062d917fa504e9a2ac19`;
code SHA-256 `73b29268807ce9033cb35964fde0d053eac3e71896b617c37f2b4156a76e7fff`. Single CPU run, seed 0, cost $0.
Evidence: `runs/wo01-20261029T215941498110Z/record.json`. Reference: RocketPy 1.13.0.

| Case | Burn endpoint | Max CG/CP difference (m) | Margin difference (cal) | Benchmark |
|---|---|---:|---:|---|
| configured | liftoff | 5.97e-16 | 7.11e-15 | pass |
| configured | burnout | 5.97e-16 | 7.11e-15 | pass |
| stub_geometry_sensitivity | liftoff | 4.72e-16 | 5.33e-15 | pass |
| stub_geometry_sensitivity | burnout | 4.72e-16 | 5.33e-15 | pass |

These static quantities are **validated against the reference for the stated inputs**.
The inputs still contain estimated component masses. RocketPy receives a separately
aggregated dry airframe plus a motor; it does not independently measure or validate
those component masses. Inertia, drag and trajectories are excluded.

Since no source curve is present, the comparison uses a constant-thrust GenericMotor
only to evaluate the fully loaded and fully depleted endpoints. No intermediate
thrust result or certified-curve validation is claimed. The sensitivity case toggles
stub aerodynamics without adding fin mass; it is not a physical fins-on vehicle.
Both its liftoff margin (-2.687 cal) and the default margin (-4.396 cal) are negative.

The numerical equality is expected when two implementations use the same mathematical
model; it checks units, geometry transfer, CP buildup, motor accounting and signs.
It is not evidence of aerodynamic fidelity or flight readiness.

## Imported motor data and mass tradeoff — WO-01

The selected historical F15 source is archived byte-for-byte in
`configs/vehicle/motors/Estes_F15.eng`; its sidecar records SHA-256, source URL,
certificate date (2012-11-25), and historical-data scope. The configured mean thrust
and impulse are now derived from its exact samples. No current certification or
recovery-delay selection is implied.

| Source curve | Mean thrust (N) | Burn (s) | Loaded mass (g) | Review |
|---|---:|---:|---:|---|
| Estes F15, selected 2013 dataset | 14.3793 | 3.450 | 103.0 | Accepted for digital model |
| AeroTech F10 historical | 10.6645 | 7.050 | 83.0 | OOP listing; 92 vs 85 mm length unresolved |
| G25W-10A, 152.4 mm file | 25.3089 | 4.414 | 170.0 | Quarantined: differs from 124 mm listing |
| G25, 124 mm derived file | 22.1697 | 5.300 | 119.7 | User-labelled source; certificate reconciliation pending |

The F10 and G25 certification dates are unknown from available records. Their
metadata retains null dates and unresolved status; no file submission date is
substituted for certification. References and source snapshots are in each sidecar.

| F15 model | Tube walls | Liftoff mass (g) | Average-thrust/weight | Static reference |
|---|---:|---:|---:|---|
| Main spec, unchanged geometry | 1.6 mm | 529.0 | 2.772 | pass |
| Separate shell proposal | 1.2 mm | 478.4 | 3.065 | pass |

Baseline run `wo01-20261029T220952512841Z`; proposal run `wo01-20261029T221057430780Z`.
Both records include input hashes for motor data and sidecars. The proposal is
`configs/studies/tvc-ascent-f15-1p2mm.yaml`; it does not replace the main vehicle.
The mass reduction is annular shell volume × estimated 1270 kg/m³ PETG density,
with every other part estimate retained. Proposed line width is 0.4 mm × 3 walls.

The nominal F15 limit for thrust/weight 3 is 488.8 g, leaving only 10.3 g headroom
in the proposal. Strength, buckling, print tolerances, joints and layer adhesion
remain unverified. Both finless configurations retain negative static margins.
No design is declared flight-ready, and `certified_curves_complete` remains false.

Intermediate mass-depletion checks use cumulative impulse. Direct RocketPy
integration agrees; its separately sampled mass Function introduces up to 3.92 mg
mass / 2.03 micrometres CG difference in a 501-time diagnostic sweep, consistent
with interpolation of 100 sampled integrals. Endpoint agreement remains at numeric
precision. No flight trajectory was run.

## Stronger 29 mm motor study — WO-01, 1.6 mm tubes retained

Owner direction: keep the existing 1.6 mm working geometry; investigate stronger
long-burning 29 mm motors. The thinner-shell proposal remains available but is not
adopted. Reproduce: `make motor-study`. Evidence:
`runs/wo01-motors-20261029T223729544856Z/record.json` (single CPU run; $0).

All rows below retain the original airframe and its 16 g mount, then add **20 g
incremental mounting/retention reserve**. Motor loaded masses come from each
separate RASP header; inferred dry casing/hardware is already counted once.
Motor midpoints are assumed CGs, not measured mass-distribution evidence.

| Source hypothesis | Loaded motor / inferred dry (g) | Liftoff mass (g) | Mean thrust / liftoff weight | Burn (s) | CG liftoff / burnout (m) |
|---|---:|---:|---:|---:|---:|
| f15_reference | 103.0 / 43.0 | 549.0 | 2.671 | 3.450 | 0.424141 / 0.397287 |
| g25_124mm_single_use_historical | 119.7 / 57.2 | 565.7 | 3.996 | 5.300 | 0.429544 / 0.403653 |
| g25w_10a_rms_source | 170.0 / 73.0 | 616.0 | 4.190 | 4.414 | 0.442647 / 0.408790 |

These are **unselected source hypotheses**, not complete mechanical designs.
The 124 and 152.4 mm source cases exceed the 700 mm vehicle bounds if their front
stays at 586 mm. Conditional cases above move the motor forward by 10 and 38.4 mm
respectively to hold the aft end at 700 mm. No tube, mount, gimbal or avionics part
is moved. Nominal diameter alone cannot establish fit: the 29 mm bore, actual
closure/flange diameters, axial support, retention and gimbal swept clearance
require inspection. `mechanical_fit_verified` stays false in every case.

RocketPy mass/CG/CP/margin comparisons pass at both burn endpoints for these
conditional positions. Agreement validates transfer and calculation under the
same midpoint-CG assumption; it does not validate motor mass distribution, mount
compatibility, structural strength, thermal isolation or flight behavior.

The [G25W-10A product page](https://aerotech-rocketry.com/products/product_c968e0dc-44a1-0a42-42dc-d69b16336291)
lists 168 g motor mass, 62.5 g propellant and 4.5 s thrust duration. Its 120 N s
and 22.2 N average also need definition/variant reconciliation. The
[manufacturer's 2024-12-19 matrix](https://d3l66gvjdr7rqw.cloudfront.net/Templates/170652/myimages/aerotech%20master%20motor%20matrix%2012-19-24_1734643280505.pdf)
G25W-10A row lists 117.1 g, 63 g and 5.3 s. Neither summary matches all fields of
the downloaded RMS-labelled curve (170 g, 97 g, 4.414 s). Do not combine the light
mass from one source with the stronger thrust of another to declare a motor selected.

The [manufacturer certification index](https://www.rocketmotorparts.com/page/nar-tra-certification-docs)
separates older NAR G25 single-use and TRA G25W-10A RMS-29/120. Their source
certificates and the [RMS dimension drawing](https://d3l66gvjdr7rqw.cloudfront.net/Templates/170652/myimages/rms%2029%3A120_1698856038824.pdf)
need local visual review to establish exact configuration and certification dates.
Source text extraction alone does not resolve the scanned certificates.

F25W single-use is a useful **screening-only** candidate: the matrix lists 29 mm,
98 mm, 90 g, 25.6 N and 3.1 s. With a 20 g reserve that would imply 536 g and
summary-only TWR 4.87. No CG, reference comparison or time trace is inferred from
those summary values. A different molded-case F25 dataset describes less than a
3 s burn, so exact variant and source data are essential before evaluating it.

`configs/studies/motor-source-evidence.yaml` records the source conflicts.
`make fetch-motor-study-sources` collects the primary PDFs and F25 data for the
next review. **No motor is selected. WO-01 remains open; no flight simulation.**

## Local source-document review — WO-01

Date: 2026-10-29 (America/Los_Angeles). `make fetch-motor-study-sources`
successfully archived all five original PDFs and the F25 API response. PDF hashes
are in `data/motor-study-sources/manifest.json`; reviewed fields and source hashes
are retained in `configs/studies/motor-source-evidence.yaml`. Complete certificate
pages, the dimension drawing, and matrix pages 2 and 4 were visually inspected.
This review concerns historical documents, not current certification or availability.

- **Historical G25:** the NAR report records tests on 1995-09-02, 124 mm casing,
  62.5 g propellant, 117.50 N s measured impulse and 5.30 s burn. These correspond
  to the historical source curve. Its 119.7 g loaded header is consistent with
  the rounded mean of three delay-specific report masses (121.0, 120.9, 117.1 g),
  not one selected recovery delay. The report says certification is "Continuing"
  but gives no certification issue date. The test date is not used as that date.
- **G25W-10A:** the TRA letter is dated 2013-12-10, reports a 2013-11-03 test and
  states validity through 2018-12-31. It lists 170 g loaded, **62 g propellant**,
  149 mm length, 109.49 N s and 4.20 s. Its text calls the motor a Moonburner
  Reload while both graph titles say DMS. The downloaded curve has **97 g
  propellant** and 152.4 mm length. Duration definitions may differ, but the
  mass/identity conflict is unresolved. The source remains quarantined; no header
  is silently corrected and the 616 g study remains a conditional source hypothesis.
- **RMS-29/120 drawing:** nominal 29 mm alone does not establish fit. The aft
  closure is dimensioned 1.250 in (31.75 mm). The 5.503 in axial span excludes a
  separately dimensioned 0.368 in aft-closure span, and the nozzle extends farther
  aft. A 140 mm summary is not the complete installed envelope. The drawing
  establishes neither loaded mass nor correspondence to the ambiguous G25 report.
- **F25:** the historical NAR report records 1995-09-03 tests, 3.05 s burn,
  35.6 g propellant, 97 mm casing and approximately 90 g initial mass. The newly
  fetched user-source curve explicitly describes a newer molded case (file
  comment dated 2005-03-02): 97.2 g loaded, 38.8 g propellant, 98 mm and **2.69 s**.
  It is archived byte-for-byte under `configs/studies/motors/`, separately from
  the vehicle motor catalog, and **rejected for the default under the unchanged
  three-second requirement**. Historical duration/mass are not applied to this curve.

Reproduce numerical screening: `make motor-study`. Evidence:
`runs/wo01-motors-20261030T002511325861Z/record.json` (single CPU run, $0).
The molded F25 with +20 g incremental reserve gives 543.2 g, average TWR 4.939
and 2.690 s; `nominal_performance_pass` is false. Static RocketPy agreement does
not override the failed duration criterion. All four source hypotheses retain
`selected: false` and `mechanical_fit_verified: false`.

`make check smoke motor-study` passes (42 tests). Main vehicle, thinner-shell
proposal and all existing `.eng` bytes are unchanged. WO-01 remains open. The
remaining motor-selection blocker is a traceable, purchasable exact configuration
with matching curve, assembled mass/dimensions and certification evidence; no
motor purchase, hardware change or WO-02 work follows from these calculations.

## F22J follow-up — summary screening only

The next candidate is AeroTech F22J using the **hobby RMS-29/40-120 hardware**,
which is different from the G25W RMS-29/120 hardware. The
[manufacturer -5J page](https://aerotech-rocketry.com/products/product_b3edb817-b2c0-a3c6-8575-8d8eb5427353)
publishes 132.9 g and the
[-7J page](https://aerotech-rocketry.com/products/product_3b9b0b1e-10a7-5992-86c4-c86c67780c2d)
135.6 g, both at 19.6 N average / 3.31 s. The 2024 manufacturer matrix reverses
those two delay-mass assignments. Both product pages mark the motor as clearance,
cancelled once stock is gone. No exact delay, assembled mass or live stock has
been accepted from these contradictory summaries.

More significantly, the [current NAR interactive list](https://www.nar.org/content.aspx?club_id=114127&module_id=670148&page_id=22)
(updated 2026-08-12) lists F22J at **55.08 N s**, 29 × 125 mm, 46.3 g propellant,
delays 4/7, with a linked [post-certification test report](https://www.nar.org/docs.ashx?id=1770551).
This differs from legacy 65 N s / 5/7-delay summaries. Neither a manufacturer
clearance page nor the old RASP reconstruction establishes correspondence to
that newer test. Web retrieval of the NAR report returned HTTP 403 in this session.

Reproduce `make f22-study`. Record:
`runs/wo01-motors-20261030T003713058296Z/record.json` (single CPU screening, $0).
The retained 1.6 mm airframe contributes 426 g without motor, already including
its original 16 g mount. Add **20 g incremental mount reserve**:

| Published assembled-mass hypothesis | Screening liftoff mass | TWR using legacy 19.6 N | Maximum burn duration compatible with TWR 3 if impulse is 55.08 N s |
|---|---:|---:|---:|
| 132.9 g | 578.9 g | 3.452 | 3.234 s |
| 135.6 g | 581.6 g | 3.436 | 3.219 s |

The last column comes only from I / (3 m g), a necessary feasibility bound. It
is not a burn prediction and does not replace any source curve. The unchanged
minimum three-second burn therefore leaves a narrow conditional duration window
under the newer impulse, pending the report's actual duration/curve and mass.

`selection_eligible` and `selected` remain false. No F22 thrust samples, CG or
reference comparison have been fabricated from summaries. Exact assembled
geometry, mass, hardware inclusion, current certification correspondence and
purchasability remain unresolved. The two mass hypotheses are preserved separately.

`make fetch-f22-sources` collects the historical manufacturer-hosted certificate,
correct hardware dimensions, current NAR test/original documents, and F22 API
source files into a separate archive. No existing motor curve, baseline or thin
shell study is overwritten. Source inspection precedes any acceptance or WO-02 work.

## F22 local source review — partial collection

Date: 2026-10-29 (America/Los_Angeles). `make fetch-f22-sources` downloaded
the historical manufacturer-hosted NAR report, hobby-case drawing and one
ThrustCurve RASP file. It **exited nonzero** because the current NAR post-test
document returned **HTTP 403**; the original NAR-hosted document was then not
requested, as designed. Manifest: `data/f22-study-sources/manifest.json`.
Complete available PDF pages were rendered and visually reviewed. Source fields,
hashes and unresolved items are in `configs/studies/f22-source-evidence.yaml`.

The historical report explicitly identifies the F22 reload with RMS-29/40-120
hardware, certification effective 1993-12-23, and tests dated 1992-07-18. Its
ten-motor test reports 65.00 N s, 3.31 s burn (0.23 s standard deviation), 46.3 g
propellant, 124 mm casing and 135.6 g initial mass for the four-second delay.
This resolves the historical certification date and hardware identity, not
the conflicting modern product delay/mass labels or newer post-test performance.

The unchanged RASP source (comment dated 2000-07-04, API labelled `user`)
integrates to **64.996987 N s / 3.310 s / 19.636552 N**. Its header says 125 mm,
134.2 g loaded, 46.3 g propellant and delays 4/7. Archived original bytes and
comparison-only provenance under `configs/studies/motors/AeroTech_F22_legacy.*`.
Its mass/length are retained as source assumptions, not overwritten from the PDF
or applied to a specific current commercial delay variant.

`make f22-study` now also compares this historical curve against RocketPy for
static properties. With +20 g incremental reserve, it gives **580.2 g / TWR
3.451 / 3.310 s**. Holding the source-defined aft station requires an 11 mm
forward shift; the fixed-front case exceeds the unchanged vehicle by 11 mm.
Reference agreement uses the same unmeasured midpoint motor-CG assumption.
Evidence: `runs/wo01-motors-20261030T005512950204Z/record.json` (single CPU run,
$0). This is historical conditional performance only; `selected` and
`mechanical_fit_verified` remain false. Both prior published mass hypotheses
remain separately preserved in summary screening.

The hobby-family drawing's title is **RMS-29/40 MOTOR DIMENSIONAL DRAWING**,
revision A (2003-10-08). It shows a 1.230 in (31.242 mm) aft closure, 4.874 in
nominal casing span and additional forward projections to 5.994 in. A separate
0.250 in aft-closure span and nozzle extend farther aft. Neither the 124/125 mm
casing summary nor this generic sheet alone proves the complete F22 envelope,
retention or gimbal clearance. No actual mounting design was changed.

The public NAR interactive listing was rechecked: revision 2026-08-12 still
reports **55.08 N s**, 29 x 125 mm, 46.3 g propellant and delays 4/7. The linked
post-test PDF also returned 403 through normal web retrieval. Its test date,
duration, actual trace and assembled mass remain unknown. The legacy curve is
not scaled, stretched or relabelled as that test, and its nominal pass does not
resolve current motor suitability. No additional document requests followed
the web access denial.

`make check smoke f22-study` passes (44 tests). Previous vehicle/proposal/source
and G25/F25 PDF archive hashes were checked unchanged. F22 remains unselected;
G25W stays quarantined and molded F25 stays rejected. The inaccessible newer
F22 report is the immediate evidence blocker. WO-01 remains open; no purchase,
flight simulation or GitHub action was performed.

## G-class catalogue and purchase survey — 2026-10-29

Scope: maximize total impulse with published burn >= 3 s, no high-power flyer
certification, and verifiable US purchase availability; retain the working
airframe and its TWR >= 3 requirement. Surveyed all 93 G-class records returned
by ThrustCurve (explicit `maxResults: 200`, not its default 20-record subset),
then checked manufacturer data and direct vendor inventory. Catalogue metadata
is a screening index, not acceptance of every archived curve.

Evidence: `runs/wo01-g-survey-20261030T011221865663Z/record.json` (CPU arithmetic
and public source/stock checks, $0). Source responses are in ignored
`data/g-motor-survey/`. No source curve, vehicle YAML or earlier archive was changed.

- **AeroTech G12ST-P:** highest-total-impulse in-stock motor verified under the
  stated motor constraints. Manufacturer matrix / published test summaries give
  approximately 144 N s, 12.7 s burn, 150.3 g loaded and approximately 11-12 N mean
  thrust. Wildman's direct product JSON returned `available: true`, SKU 6030,
  $48.49. Its product page agrees on 144 N s and 12.7 s. The manufacturer product
  page separately says 160 N s / 13.3 s; that conflicting summary is not used to
  claim a full 160 N s certified motor. Exact installation dimensions and curve
  revision would still need reconciliation before spec adoption.
- Current NAR certification guidance lists the G-motor high-power triggers as
  hybrid/sparky, >80 N average, >=125 g propellant, or rocket mass >1,500 g.
  The G12ST-P's listed 82 g and low thrust do not trigger those conditions for
  a qualifying model rocket. CAL FIRE's 2021-03-03 letter explicitly approves
  G12ST-P as a **Model Rocket Motor**; complete letter visually reviewed and
  archived with hash e10724f77a5968a1b5baaf22ee0372b181c52d16755d06b1b9241ab0a3a58988.
  These are not blanket launch-site or active-stability flight approvals.
- G12ST-P fails the retained vehicle's performance criterion: 426 g airframe
  excluding F15 + 150.3 g motor + 20 g reserve = **596.3 g**. Average TWR is
  **1.934** using 11.31 N or **2.052** using nominal 12 N. TWR 3 would require
  total mass <=384.4 g or <=407.9 g respectively, with electronic recovery added:
  this is a plugged motor with no motor-ejection charge. It is not recommended
  as a replacement for the unchanged baseline.
- **Cesaroni 143G33-9A Mellow / Pro29-3G:** manufacturer confirms 143.1 N s,
  4.38 s, 32.7 N mean, 197 g loaded, 79.1 g propellant and 29 x 187 mm. With
  +20 g reserve, conditional mass is 643 g and average TWR 5.186. This is the
  better design candidate for the existing airframe, pending complete fit and
  source acceptance. Wildman's direct product JSON says unavailable; Chris'
  Rocket Supplies also says out of stock. No buy-now US source was verified.
  If stock is found, check the manufacturer's 2020-10-01 G33 ignition-pellet
  bulletin and corrected-stock status; no field modification is proposed here.
- Higher-impulse Cesaroni 159G54-12A is rejected by the unchanged duration
  constraint: manufacturer publishes **2.97 s**, which is not rounded up to 3 s.
  Catalogue G50 IMAX likewise lists 2.87 s. No duration threshold was relaxed.

Purchase recommendation for the unchanged baseline: **hold purchase**. G12ST-P
meets the motor-only request and is buyable, but fails this vehicle's TWR gate;
G33 is the preferred design candidate but unavailable at verified sellers. No
verified in-stock replacement meets all retained project requirements. Existing
G25W quarantine and F25 rejection remain in force. No motor was selected or
ordered; WO-01 remains open. No code changed and no additional tests were needed
for this source survey; the last implementation check remains 44 passing tests.

## F22 post-test import and maximum-impulse G screening

Date: 2026-10-29 (America/Los_Angeles). Owner downloaded
`Aero_F22J_2026-05-02_tr.pdf`; archived an unchanged copy at
`data/f22-study-sources/current_nar_posttest.pdf` (SHA-256
`f7d8a5d3bcad0e7e32d11be0e8560552f41e6ee8b043241ff951f5ad98608b58`).
Rendered and visually reviewed all three pages. The six-motor May 2, 2026 test
reports **55.08 N s / 3.83 s / 14.52 N**, and FAIL for excessive delays in all
three nominal seven-second samples. That is not a formal decertification notice.

The included page 3 RASP points were extracted and visually checked separately
from the legacy curve: **55.808607 N s / 4.178 s terminal time / 13.357733 N**,
130.9 g header initial mass. These representative curve numbers are not forced
to equal test-summary averages. At +20 g mounting allowance: **576.9 g / TWR
2.361**, versus **2.567** using the report's higher mean thrust at the same mass.
F22 is rejected for the unchanged baseline. Static RocketPy comparison passes
under the midpoint-CG assumption; no fit or flight validation is implied.
Reproduce with `make f22-study`; run
`runs/wo01-motors-20261030T011052177790Z/record.json`.

The owner's new maximum-impulse G objective was screened collectively, retaining
1.6 mm tubes, one TVC motor, >=3 s burn, TWR >=3 and loaded mass <1.5 kg.
[Ranked shortlist and evidence](wo01-g-motor-shortlist.md) records the common
mass budget, thrust-profile differences, exact source conflicts, stock checks,
California/ROC requirements and separate larger-diameter negative screen.
Use `make g-impulse-study`; run
`runs/wo01-motors-20261030T012229578107Z/record.json`.

The leading *follow-up* configuration is **CTI 143G33-9A Mellow + Pro29-3G case
+ standard Pro29 rear closure, no spacers**. Manufacturer and CAR data give
143.1 N s / 4.38 s / 197 g assembled. With **20 g incremental mounting plus
50 g vehicle-growth allowance**, summary screening gives **693 g / TWR 4.812**.
These allowances are estimates, not measured mount/print masses. A full matched
curve, California classification and complete installed fit remain unresolved;
checked reload, case and closure product pages say out of stock. No exact
configuration has cleared every selection gate. This is not a buy recommendation.

CTI 159G54 is closer to full G (159.1 N s) but manufacturer burn is 2.97 s;
its sampled terminal zero at 3.026 s and rounded 3.0 s listings are kept distinct.
G12ST, G11 and G8 fail TWR. Current molded G40 is shorter than three seconds;
legacy PML figures are not substituted. The 38 mm G50 gives 150 N s / 2.87 s,
so no larger mount redesign is justified by a verified qualifying improvement.
G25W quarantine and F25 rejection remain intact. A direct seller advertises
G25W-10A stock, but repeats conflicting legacy specs; availability does not
resolve technical identity.

Current NAR/Tripoli public criteria use a 125 g propellant criterion along with
160 N s / 80 N and propellant-type limits. Older 62.5 g guidance and manufacturer
classification text conflict; no automatic nationwide 62.5 g exclusion is imposed.
California exact-motor OSFM evidence and ROC's prior approval of active finless
stabilization remain separate required gates. Club/date was asked of the owner;
ROC at Lucerne remains the project-plan assumption. No approval is claimed.

`make check smoke` passes (44 tests); `f22-study` and `g-impulse-study` run locally.
Baseline, thinner proposal, previous curves and earlier PDF hashes verified
unchanged. All added analysis remains in WO-01. No motor selected, purchase,
hardware change, flight simulation, paid compute or external message.

## Modular platform rebaseline — 2026-10-29

Owner rebaseline supersedes the fixed F15/1.6 mm/three-second/average-TWR-3 assumptions.
[ADR-0006](adr/0006-modular-platform-rebaseline.md) and
[trade, mass/cost and verification](wo01-rebaseline.md) preserve custom fabrication,
maximum practical no-HPR performance and committed RL as core objectives. Earlier
results/rejection reasons above remain historical evidence; no old result was edited
into a pass. The digital orbital/G-FOLD work and WO sequence are unchanged.

Final preliminary benchmark: [`wo01-platform-20261030T022439939715Z`](../runs/wo01-platform-20261030T022439939715Z/record.json),
UTC 2026-10-30 / local 2026-10-29. `make check smoke tiny benchmark` passes: ruff,
black, strict mypy (21 source files), **53 tests**, and real RocketPy static comparisons
for all three actual modes. Runtime 1.07 s for the benchmark on CPU.
No trajectory, CAD, controller or hardware result is claimed.

| Mode | Nominal loaded g | With 50 g growth | Guide exit m/s | Useful thrust-time proxy s | Margin with growth aft, launch / burnout cal | Parts budget |
|---|---:|---:|---:|---:|---:|---:|
| performance | 472.03 | 522.03 | 20.90 | 1.55 | 1.321 / 1.792 | $392 |
| tvc_finned | 575.77 | 625.77 | 11.66 | 11.69 | 1.288 / 1.723 | $455 |
| tvc_finless | 532.15 | 582.15 | 12.16 | 11.73 | -6.871 / -6.364 | $446 |

Guide speeds use 85% source thrust, constant loaded mass including 50 g growth,
estimated drag/friction and actual mode guide travel (1.5 m performance; 2.4 m TVC).
The performance target is 15 m/s; TVC 10 m/s at a provisional lower wind. Useful
TVC time is the longest contiguous post-guide interval above 1.2 times worst-case
weight: >=2 s required, >=5 s preferred. It is not closed-loop control authority.
Average TWR and three seconds are no longer universal gates. The finless margin is
**negative**, an explicit instability result with later active-control and
burnout-to-recovery gates; its screen does not claim passive stability.

Each mode has its actual part tree, fin mass/radial inertia, motor geometry, full
inertia tensor (including offset servos), CG and CP. Shared upper parts agree by
resolved value; all parts have `learn` and build/cost metadata. Derived resolved
specs and inventory previews are generated beside records (ignored outputs).
Static RocketPy agreement checks endpoint mass/axial CG/CP/margin, not physical
inertia, structural strength or real assembled hardware. Fin sets and moving
motor hierarchy are actual parts rather than an aerodynamic-only switch.

Recommended preliminary families: G80-10T SU SKU 78010 fixed mount for performance;
reformulated G12ST-P DMS SKU 071200 on a custom gimbal plus independent recovery for
TVC. G80 current versus historical curve dimensions/summary and G12 advertised length
remain unresolved. Web RASP transcriptions are explicitly labelled numerical
hypotheses, not byte-verified downloads or exact current purchasable motor matches.
Direct checked G80 pages show no stock; G12 Wildman offers Add to Cart at $48.49
at the study timestamp. Availability and exact motor/lot/California/club acceptance
must be rechecked before procurement. No flight-qualified motor is selected.

G54 is reopened as a near-160 N s performance upgrade; G33 as a higher-thrust TVC
alternative. Larger bores remain a separate quantified trade. F25's former short-burn
rejection is superseded for performance: the old curve gives about 15.8 m/s guide
exit, but only about 1.8 s useful time in the trainer. F15/F22 still fail revised
guide screens; G25W remains quarantined for conflicting identity/mass/source data.

The 66 mm hybrid kraft/plywood/printed ASA architecture retains substantial custom
joint, structure, gimbal, wiring and recovery integration work. Shared upper budget
245.75 g / ~$309; unique common plus performance and trainer hardware and one motor
of each family ~$538. Planning envelope ~$650–950 plus any new tools, shipping/tax,
fees and ~$100–200 guide/test fixture. These are estimates, not purchases or quotes.
A 750 mm canopy/35 g budget meets preliminary 6 m/s sizing under stated rho/Cd;
packing, opening loads, actual descent and power independence remain unverified.

Negative design screens remain recorded: short guide and initial trainer fins failed
before actual fin span/guide changes; canopy allowance grew after sizing. See
`wo01-platform-20261030T015149592090Z` and `wo01-platform-20261030T015256135912Z`.
All runs retain `flight_ready: false`. Flight, structural/thermal, PID/RL, HIL,
independent recovery and actual club/RSO gates remain in their later work orders.
WO-01's revised preliminary benchmark is met; no later work order has started.

Original baseline SHA-256 remains
`eeb392ee6169629c3bcc0b31c17b7fc8d8bb14230fd8966c7c0d404b80d85d7a`.
The thinner proposal and old curve files remain unchanged. No purchase, physical
work, paid run or flight authorization was exercised. GitHub pushes/PRs are now
separately authorized and ordinary owner review is not a development gate.

Initial hosted CI exposed text-upload newline normalization in three archived
curves (F10, F15, newer G25). Their local originals/hashes were unchanged; restored
raw bytes to GitHub via base64 blobs and added `*.eng -text` to `.gitattributes`.
The provenance test caught the publication fault; no curve values or hashes were
adjusted to force a pass. Hosted validation evidence is linked on the PR.

Publication: [private repository WO-01 PR #1](https://github.com/kudratsingh/rocket-twin/pull/1).
Local validation is recorded above; hosted check/merge status is shown on the PR.

## WO-02 — actual-mode flight validation and delivered performance (2026-10-29 local)

Core: [PR #2](https://github.com/kudratsingh/rocket-twin/pull/2). Validation/study:
[PR #3](https://github.com/kudratsingh/rocket-twin/pull/3). Both original objectives
remain: maximum practical conventional performance and substantial custom building,
plus committed PID-to-RL and embedded/real-flight research. Hardware is not frozen.

**Final Mac CPU study:** [`wo02-20261030T044930127544Z`](../runs/wo02-20261030T044930127544Z/record.json).
All five nominal apogee/time comparisons pass within **0.004%**, against the required
5%; all 27 nominal/sensitivity/wind cases are finite and reach impact within the
360 s horizon. Source/code hashes are captured and checked unchanged during the run.
The full study took 113.59 s; the 4,096-environment step after compilation
took 4.03 ms (~1,015,181 env-steps/s).
This is one batched step, not PPO training or full-rollout throughput.

`make check smoke` passes: ruff, black, strict mypy (35 source files), **65 tests**.
`make benchmark` passes WO-01 static checks plus WO-02 actual-mode trajectory and
batch gates. Tiny run [`wo02-20261030T045326632046Z`](../runs/wo02-20261030T045326632046Z/record.json)
took 10.10 s, below 120 s. JAX/jaxlib 0.4.38, RocketPy 1.13.0,
NumPy 2.4.6, SciPy 1.17.1 and PyArrow 23.0.1 run on macOS arm64 CPU/Python 3.11.16.
No GPU, paid run, purchase, hardware action or controller implementation.

| Actual source hypothesis | Loaded g | Apogee JAX / RocketPy m AGL | Apex time JAX / RocketPy s | Largest comparison error | Variable-mass guide exit m/s | Peak powered specific force g |
|---|---:|---:|---:|---:|---:|---:|
| G80 fixed reference | 472.03 | 697.94 / 697.95 | 9.651 / 9.651 | 0.00166% | 24.41 | 22.13 |
| G12 finned TVC | 575.77 | 902.69 / 902.70 | 18.592 / 18.592 | 0.00093% | 13.65 | 5.56 |
| G54 fixed hypothesis | 552.03 | 842.42 / 842.44 | 10.853 / 10.853 | 0.00389% | 24.41 | 22.74 |
| G33 fixed hypothesis | 550.83 | 824.14 / 824.15 | 11.968 / 11.968 | 0.00352% | 12.96 | 11.64 |
| G12 fixed / 3 m guide | 501.83 | 1023.36 / 1023.37 | 18.675 / 18.675 | 0.00146% | 16.65 | 6.37 |

These are numerical source hypotheses at assumed 850 m MSL, calm vertical guidance,
zero guide friction, estimated drag and the actual mode mass/geometry. RocketPy
integrates its own dynamics/surfaces/motor from common inputs; dry inertia is shared
as a declared input, not independently measured or validated. Nominal guide speeds
are distinct from the conservative loaded-plus-50-g / 85%-thrust guide screens in
[the study report](wo02-flight-study.md). G33/1.5 m and fixed G12/3 m fail the retained
performance guide screen under that allowance; altitude alone does not accept them.
G54 has only 1.023 cal launch margin with all growth aft.

| Mode | Low/high engineering-corner altitude m | Low-corner variable-mass guide m/s | Nominal impact time s | Nominal impact speed m/s |
|---|---:|---:|---:|---:|
| G80 fixed reference | 534–888 | 21.06 | 158.3 | 4.62 |
| G12 finned TVC | 534–1261 | 11.74 | 192.9 | 5.08 |
| G54 fixed hypothesis | 637–1085 | 21.48 | 180.5 | 4.87 |
| G33 fixed hypothesis | 599–1081 | 11.25 | 176.8 | 4.91 |
| G12 fixed / 3 m guide | 649–1395 | 14.23 | 232.2 | 4.68 |

Bounds combine specified thrust/time/drag/mass/friction variations, not measured
probability intervals or certified motor tolerances. Native G54/G33 source depletion
versus certificate-propellant hypotheses give 842.42→845.76 m and 824.14→825.41 m;
small numerical sensitivity does not resolve source identity or legal qualification.

| Mode | Max powered tilt: 1 m/s / 3 m/s+gust deg | Altitude: 1 m/s / gust case m | Net landing displacement: 1 m/s / gust case m |
|---|---:|---:|---:|
| G80 fixed reference | 1.92 / 7.23 | 698 / 692 | 169 / 655 |
| G12 finned TVC | 26.84 / 73.17 | 848 / 528 | 182 / 180 |
| G54 fixed hypothesis | 1.84 / 7.04 | 842 / 836 | 194 / 765 |
| G33 fixed hypothesis | 3.75 / 14.23 | 822 / 798 | 144 / 615 |
| G12 fixed / 3 m guide | 16.61 / 53.49 | 999 / 782 | 47 / 235 |

The gust case is 3 m/s at 10 m, height exponent 0.14 and a bounded 1 m/s gust,
not uniform 3 m/s at every altitude. Maximum free-flight powered angle of attack
stays below 15 degrees in these cases; large body tilt still violates a useful
vertical-control goal. These are uncontrolled locked-gimbal flights, not PID/RL
results. Landing displacement is an endpoint, not a certified footprint radius;
upwind powered travel can cancel later drift. Actual site/altitude/footprint limits
remain unknown. No operational wind envelope follows from this model.

Ancillary constant 1 m/s comparison:
[`wo02-wind-20261030T045434689213Z`](../runs/wo02-wind-20261030T045434689213Z/record.json).
G80 apogee/time differences are 0.0104% / 0.0034%; finned G12 1.153% / 0.530%.
This checks another condition, not gust spectra, attitude histories or real aero.

**Recovery and sensors:** G80's 10 s delay probe is ~2.16 s after nominal apogee,
about 20.4 m/s downward in the separate no-canopy sensitivity. Its -10 study SKU is
not accepted as the flight delay. G54's 12 s probe is ~4.17 s late at ~36.4 m/s.
Exact offered delays and tolerance envelopes must be verified later; independent
apogee recovery is not permission to ignore a secondary motor charge. G12 is
plugged: it has no motor ejection/backup. Canopy drag/inflation/descent are estimates,
not deployment or opening-load qualification. Finless burnout-to-recovery remains
an explicit later control/recovery gate.

G80/G54 nominal specific force reaches 22.13/22.74 g (high corners 25.44/26.14 g),
exceeding the current 16 g accelerometer model. Observations clip accordingly.
A suitable high-g measurement path, with mass/cost/datasheet/bench evidence, is
required before hardware/control release; no sensor rating was silently increased.
The G12 trainer reaches ~5.56 g, but weathercocks ~26.8 degrees at 1 m/s and ~73.2
in the gust case. Useful powered duration alone is not control authority: WO-06
must assess fin torque, gimbal travel/moment, servo loading and realistic estimation
before PID acceptance, followed by committed RL/HIL and honest negative results.

**Recommendation:** retain G80 as the starting validation/commissioning reference.
G54 is the leading conditional near-160 N s performance upgrade: ~20.7% more nominal
altitude with robust guide exit in this model, at +80 g installed support/motor mass
and tight aft-growth margin. G33 adds altitude but has a departure shortfall. Fixed
G12 is the calm-altitude leader (~46.6% above G80), but needs improved conservative
guidance, a verified low-wind envelope, long-burn thermal tests and independent
recovery; it is not automatically the practical choice. Keep the custom modular
platform and separate long-duration TVC research mode. Exact source/hardware,
California/club acceptance, stock, measured loads/mass, sensor/recovery and control
gates remain before hardware selection. G25W quarantine remains.

**Negative/revised evidence:** early CTI reference cases passed coarse 5% comparisons
while a duplicate explicit zero sample in RocketPy's RASP importer produced NaN
initial thrust and constant motor mass. The adapter now passes validated source
points once; new endpoint/intermediate depletion regressions catch that failure.
Pre-fix frozen CI record `wo02-20261030T043548761902Z` is retained as superseded,
not accepted reference evidence. Local exploratory `wo02-20261030T044446147368Z`
is also superseded. The earlier 240 s horizon missed two high-altitude recovery
cases; 360 s now closes them. Exact source archives were not edited to force a pass.
A headless plotting backend also replaced a failed macOS GUI plotting invocation.

## Initial engineering checkpoint — WO-03, calculated (not measured)

These are model outputs and preliminary calculations, not coupon, component, flight,
or hot-soak measurements. The property bounds, loads, restraints and case-temperature
history are estimated. Full identities and machine-readable manifests are in the
linked run records. No result clears the affected physical verification gate.

### CAD export / mass properties

Latest formal CAD record [`wo03-20261030T180113490389Z`](../runs/wo03-20261030T180113490389Z/record.json)
completed in **67.41 s** at **$0** with `inputs_unchanged: true` and
`cad_export_benchmark_passed: true`. Six generated modes passed their
mass-reconciliation and print-volume checks, six nominal interface checks passed,
and both TVC configurations passed the inclusive 25-pose sweep at ±4.9847°. The
continuous cylindrical liner-to-shell radial bound is **5.135 mm**. These are CAD
calculations, not measured mass, fabricated fit or strength; the radial cylinder
bound does not establish full mechanism/tolerance/wiring access. The earlier
34.71-second export [`wo03-20261030T175718278493Z`](../runs/wo03-20261030T175718278493Z/record.json)
is retained as the passing neutral export without formal motion proof.
`expanded_wo03_benchmark_passed` and `flight_ready` remain false.

### Structural calculations and finite-element result

Latest engineering run [`wo03-engineering-20261030T175947969565Z`](../runs/wo03-engineering-20261030T175947969565Z/record.json)
has unchanged inputs and exports calculated part-level stress, margin, temperature, and displacement
quantities with identities and evidence status. Unsupported gimbal displacement
is explicitly marked unavailable (not zero). Export-consumer checks pass, but the
engineering benchmark is false.

| Model result | Calculated value | Evidence status and limitation |
|---|---:|---|
| G80 performance fin, spatial shell field | Mesh: 2,028 nodes / 969 elements; max displacement **12.053 mm**; max \|Sxx\| **12.926 MPa**; separate regional shell von Mises **10.890 MPa** | Calculated spatial fields from [`wo03-vibration-20261030T175839356500Z`](../runs/wo03-vibration-20261030T175839356500Z/record.json); not measured. Displacement, axial normal stress and regional von Mises stress are different quantities. Input properties and idealized attachment remain estimated. Strict raw-deck, mesh and part-shape identity guard passed. |
| G80 performance fin, independent hand screen | **13.281 MPa** fin stress; **31.875 mm** upper-bound tip deflection; margin **−0.749** using the estimated 10 MPa strength bound and design factor 3 | Calculated with estimated properties and simplified load model; adverse screen, not test data. Its displacement is not the spatial FEA maximum. |
| Finned-TVC fin, independent hand screen | **21.521 MPa**, **72.835 mm** upper-bound tip deflection, margin **−0.845** | Calculated, estimated strength/load and simplified boundary. Does not represent a measured failure. |
| TVC gimbal neck-only screen | **2.604 MPa**, margin **+0.024** | Calculated with estimated 8 MPa strength bound; excludes eccentricity, holes, transverse rod loads, print anisotropy and bearing/contact. Not a closed load path. |
| Pinned motor-mount rails, buckling screen | Margin **−0.911** performance, **−0.653** finned TVC, **−0.947** G54 | Calculated conservative pinned-length Euler screen; not a tested collapse or a detailed slotted/retained-part FEA. Requires resolution. |

### Thermal and recovery load scenarios

The bounded transient network uses estimated lumped part properties, simplified gap
conduction/contact and approximate radiation. It applies an exploratory 120/250 °C
external-case step through burn then exponential cooling; this is not an exact-motor
measured case-temperature trace. In the upper hot-soak calculation, finned-TVC
peaks include motor liner **230.9 °C / provisional 120 °C screen**, motor mount
**130.2 / 45 °C**, inner gimbal **96.6 / 60 °C**, and fin bonds **59.1 / 45 °C**.
The nominal lower scenario also calculates the TVC motor mount at **54.3 °C** against
the provisional **45 °C** screen. The G54 hypothesis upper scenario calculates
liner **227.4 / 120 °C** and mount **91.5 / 45 °C**. These indicate failure of the
assumed screens, not that hardware reached these temperatures. Detailed internal
propellant/combustion, gradients, verified interfaces and physical soak remain open.

Recovery harness forces are scenario calculations, not deployment measurements:
the finned-TVC model yields factored totals from **55.1 N** (5 m/s, 0.6 m stop) to
**1,265.5 N** (20.4 m/s, 0.3 m stop). The 20.4 m/s case is an archived late-delay
off-nominal probe, not an approved motor delay. Anchor, bulkhead, local bond and
opening-shock behavior are not qualified.

## Latest WO-03 status

Integrated vibration record [`wo03-vibration-20261030T175839356500Z`](../runs/wo03-vibration-20261030T175839356500Z/record.json)
has `known_cases.passed: true` and unchanged inputs. Spatial field exports and
consumer checks pass for performance G80, finned-TVC G12 and G54; finless has no
applicable fin field. Overall vibration/flutter acceptance remains false. Solver
fixtures and numerical convergence do not close physical strength, flutter, material,
joint, tolerance-expanded motion, wiring, recovery, or service gates.
Use [current checkpoint](wo03-current-checkpoint.md) for current completion state.

Reproduce the figure with `scripts/wo02_plot.py --config runs/wo02-20261030T044930127544Z/record.json`;
output `build/reports/wo02-flight-trade.png` is generated and ignored. Source model
and verification limits: [WO-02 report](wo02-flight-study.md). WO-02's numerical
benchmark is met; WO-03 remains active, with no physical release or later controller
qualification claimed.

## WO-03 bounded follow-on studies — 2026-10-30

[PR #6](https://github.com/kudratsingh/rocket-twin/pull/6) and
[thermal PR #7](https://github.com/kudratsingh/rocket-twin/pull/7) merged after
required hosted CPU checks passed. Expanded WO-03 is still open; the following
studies do not adopt new vehicle geometry or hardware.

The [opaque-wall thermal refinement](wo03-thermal-refinement.md), record
[`wo03-thermal-20261030T182422090687Z`](../runs/wo03-thermal-20261030T182422090687Z/record.json),
passes its analytic, energy, 4/8/16-cell and time-step checks. Maximum final-two
part-mean history difference is 0.110 K. Its upper assumed case scenario still
exceeds provisional limits: finned G12 liner/mount/inner gimbal/outer gimbal means
224.9 / 88.1 / 72.1 / 63.7 C; G54 shell mean 63.7 C. Model topology changed the
predictions; neither model has physical temperature validation. Part-mean SI
Analysis exports pass the exact-identity backend check.

The [tolerance study](../configs/studies/wo03-tolerances.yaml), record
[`wo03-tolerances-20261030T182928948369Z`](../runs/wo03-tolerances-20261030T182928948369Z/record.json),
separates manufacturing nominal, independent temperatures within provisional
material screens, and a wider out-of-range heat sensitivity. In the material-domain
screen, representative minimum clearances are 0.0727 mm for body/coupler and
−0.1476 mm for mount/liner, against a 0.1 mm radial requirement. Centered key-flank
clearance is half the total slot-minus-key width; its 0.0637 mm bound also fails
0.1 mm. Unilateral key location and exact purchased dimensions remain unavailable.
The TVC cylindrical radial bound is 3.960 mm within the material domain, with
3.368 mm in the wider heat sensitivity; this does not clear full mechanism/wiring.
Source hashes before/after match; ordinary negative screens are recorded, not waived.

The [fin-construction study](../configs/studies/wo03-fin-design.yaml), record
[`wo03-fin-design-20261030T184422172911Z`](../runs/wo03-fin-design-20261030T184422172911Z/record.json),
evaluates 40 preserved-planform/construction combinations, 80 load screens and
320 static overlays including 50 g aft growth. The G80 baseline distributed
beam estimate is 11.27 mm, 6.5% below the matched 12.05 mm S6 calculation; the
31.87 mm conservative tip-load upper estimate remains separate. No candidate
satisfies both original upper screens. Sandwich stiffness improvements add aft mass
and can reduce the static margin below 1 cal. Typical ingredient properties and
unsupported thickness transfers do not qualify a bonded fin or clear flutter.

The [support-tube pilot](wo03-mount-loadpath.md), record
[`wo03-mount-loadpath-20261030T185139862170Z`](../runs/wo03-mount-loadpath-20261030T185139862170Z/record.json),
connects the proposed forward stop to an extended liner and centering rings/cradle
in vehicle copies. Neutral solid overlaps are absent. G80 mass changes +1.79 g
and CG +0.58 mm; the G54 full-length/0.1-knockdown Euler sensitivity fails, while
its actual segment loading/support and shell/joint stability remain unmodeled.
Bond average-stress results do not qualify load transfer, aft case capture, local
ring bending, pins, heat or assembled strength. No active adoption.

[Recovery-power options](wo03-recovery-power-study.md) compare a lightweight
EasyMini/120 mAh 1S proposal (25.8 g with explicit allowances) with an RRC3+/9 V
proposal (80.2 g). Front stations and hypothetical split-face offsets are explicit;
nominal boxes do not establish connector, restraint, static-port, electrical or
physical fit. Neither option is selected or purchased.

`MPLCONFIGDIR=.cache/matplotlib .venv/bin/python scripts/wo03_assembly_figures.py
--preset tiny` generates actual-export assembly, shell-hidden and gimbal-internal
stills under `build/wo03-inspection/`. The source index records GLB/manifest/spec/CAD
hashes; these are inspection aids, not motion proof. Re-run `make cad` first if
geometry changes. Custom construction, maximum practical conventional performance,
PID-to-RL and every existing release gate remain intact. Paid compute/purchases $0.

## CAD vs spec mass (WO-03)

| Part | Spec mass (g) | CAD mass (g) | Δ % |
|---|---|---|---|

## Ascent controllers — sim, 1,000 episodes/cell, 3 seeds (WO-06/07)

| Controller | Cell | Tilt RMS (°) | Max tilt (°) | Tilt at burnout (°) | Apogee σ (m) | Gimbal effort | Aborts | Run ids |
|---|---|---|---|---|---|---|---|---|
| PID | nominal | | | | | | | |
| PID | wind | | | | | | | |
| PID | randomised | | | | | | | |
| RL | nominal | | | | | | | |
| RL | wind | | | | | | | |
| RL | randomised | | | | | | | |

## Orbital mission vs cited class figures (WO-05b)

| Quantity | rocket-twin | Cited class figure | Source | Δ % | Run id |
|---|---|---|---|---|---|
| Liftoff thrust-to-weight | | | | | |
| Max-Q (kPa) and T+ | | | | | |
| MECO velocity (m/s), altitude (km), T+ (s) | | | | | |
| SECO orbit (km × km) | | | | | |
| Payload delivered (kg) | | | | | |
| Stage-1 landing propellant (kg) | | | | | |
| Engine-out at T+60 s: orbit reached? | | | | | |

## Lander — orbital stage 1 from entry-burn end, sim (WO-08)

| Method | Cell | Success % | Pos. error (m) | Vel. error (m/s) | Fuel used (kg) | Run ids |
|---|---|---|---|---|---|---|
| G-FOLD | nominal | | | | | |
| G-FOLD | disturbed | | | | | |
| PPO | nominal | | | | | |
| PPO | disturbed | | | | | |

## Flights (WO-11/12)

| Flight | Date | Motor | Controller | Wind (m/s) | Tilt RMS (°) | Max tilt (°) | Apogee (m) | Sim-predicted apogee (m) | Outcome | Log id |
|---|---|---|---|---|---|---|---|---|---|---|

## Negative results, crashes and surprises

- (record here)

## WO-03 integrated active vehicle — 2026-10-30

ADR-0008 adopts the recovery, fin/root, support/retention, thermal and fit corrections
into the active shared and mode specs. The original WO-02 record and proposal-only
runs remain historical; they are not rewritten as integrated passes. Full details,
including unresolved design failures versus owner-performed qualification, are in
[the closure table](wo03-correction-closure.md) and
[generated mass/CG/full inertia report](wo03-integrated-vehicle.md).

- Complete CAD/export/nominal motion: `wo03-20261030T205235088123Z`, 237.27 s,
  unchanged inputs, all six variants pass. Both inclusive 25-pose TVC sweeps pass
  at commanded +/-0.087 rad; nominal neutral rigid intersections are zero; continuous
  cylindrical liner/shell bound is 5.135 mm. This is not full tolerance/wiring or
  continuous-mechanism verification.
- Complete source-hypothesis flight: `wo02-20261030T204849990760Z`, 27 cases, five
  nominal comparisons, 4096-env CPU step and unchanged code/input hashes. G80/G54/
  finned G12 nominal apogees 635.19/755.53/531.16 m; G54 gain about 18.9%. Maximum
  nominal RocketPy discrepancy is G12 altitude 2.064% and time 0.917%, within 5%; the
  preserved earlier 0.004% result does not describe the updated vehicle. Finned G12
  uncontrolled locked-gimbal nominal tilt reaches 26 degrees; wind/low-thrust cases
  retain severe attitude results. This is not a PID, RL or flight success.
- Mass including 50 g growth: G80 789.462 g, G54 867.991 g, finned G12 830.147 g,
  finless695.944 g. Minimum established growth/depletion passive margins are 1.314793/
  1.045596/1.218129 cal for the finned modes. The previous G54 .991 and first combined
  .961 revisions failed; no rounding/allowance waiver was used. Additional **unsourced
  exploratory** motor-CG aft shift 10% of length gives G54 .980899 cal; exact CG or more
  design margin remains required. Finless negative passive margin is expected and
  carries no passive-stability pass claim.
- Corrected opaque/radial and serial end-pad thermal model:
  `wo03-thermal-20261030T204848956297Z`, four current-identity exports/consumer checks,
  known cases and spatial/time refinement pass, unchanged inputs. All standard upper
  cases pass configured limits. G54 shell still fails45 C in the 300 C case (46.33 C)
  and contaminated-foil case (47.10 C). Fasteners use a conditional stainless assembly
  profile; the old generic 60 C electronics limit is retained only as sensitivity.
- Support hand calculations: `wo03-motor-support-20261030T204829437762Z`. Fixed 9 mm
  G11 web and 18 mm integral bond fingers give G80/G54 hot plate margins+.504/+.263,
  hot finger-bond+.899/+.595. G54 hot net-rail Euler margin+.173. Pin bore orientation
  is radial: axial edge ligament 1.3 mm, not the earlier incorrect radial-wall-minus-
  bore estimate. Detailed contact/local stress, exact case/closure/nozzle capture,
  thread/washer/preload and positive pin retention remain open.
- Minimum-thickness fin panels: `wo03-fin-acceptance-20261030T204800907793Z` and
  `wo03-fin-acceptance-20261030T205213529823Z`; actual rectangular/gusset model, five
  S6 mesh levels, orthotropic estimated properties. Cold displacement 0.3307 mm and
  half-stiffness 0.6612 mm pass 1 mm; estimated directional DF3 strength passes. Dominant
  stress/displacement/modes converge; small Syy/tau relative checks remain failed,
  even though their values are below 1% of their strength bounds. Criterion not waived.
- Installed fin/root records `wo03-fin-installed-20261030T205715365284Z`,
  `wo03-fin-installed-20261030T205816596002Z`, and
  `wo03-fin-installed-20261030T210211507451Z` retain unrated peel/root stiffness and
  severe max-q times CN2 bare-shell/single-rail failures. Current coincident panel
  force estimates are 1.253/1.183/.390 N; full Cartesian sensitivities are 308.2/272.8/
  57.63 N and are not coincident operational maxima. Low-AR/root/body/control flutter
  remains unqualified despite positive numerical panel speed ratios.
- Exact nominal geometry fields: `wo03-fin-nominal-fields-20261030T210337367164Z`.
  Three vehicle-bound exports use actual 6.35 mm geometry; displacement about 0.28967 mm
  at 40kPa/5deg. Single 5 mm mesh, calculated/unvalidated, no convergence borrowed from
  minimum copies. Minimum 6.05 mm fields were correctly rejected against nominal CAD.
- Vibration/body: `wo03-vibration-20261030T205443545391Z`, all four current models,
  known fixtures, mesh, mass/CG and rigid-nullspace checks pass. Tube domains end at
  actual 1.200/1.175 m, with outboard mass levers; overall envelope 1.212 m is not a fake
  zero-stiffness tube. Body first modes roughly 16–26 Hz; gross gimbal screens 32.6–
  51.6 Hz. Measured compliance/damping/excitation/filter/actuator coupling is pending.
- Tolerances: `wo03-tolerances-20261030T205656390867Z`. Coupler in-domain minimum
  .2732 mm and key centered per-flank .26447 mm pass. Fixed mount/shell .02093 mm and
  TVC rail/outer-foil cold .030 mm fail .1 mm; unavailable expansion/installed envelope
  data is not a thermal pass. A remote cassette end-block envelope is no longer
  falsely used as the grip-plane radius.
- Recovery: `wo03-recovery-integration-20261030T204618137637Z`, dedicated source/
  switched positive/return/output graph passes all modes. Mode-level main-battery
  override fixed; regression covers all six resolved variants. Modeled package
  circumscribed 58.728 mm vs shoulder 61.6 mm gives 1.436 mm radial space, not physical
  packing proof. Switch mounting/arming access, board retention, wire routing and
  rated anchor/bulkhead transfer remain open design items; off-nominal factored
  anchor demand reaches 1831.7 N. Physical continuity, pulse, extraction and deployment
  tests remain owner-performed later gates.

Local Ruff/Black/strict mypy and 116 tests pass. STEP/GLB and inspection previews are
regenerated locally; the preview camera now derives its station limits from the
actual meshes. G80 reference/G54 conditional/G12 controls, custom fabrication and
committed PID-to-RL remain. **Expanded WO-03 benchmark=false; no WO-04 start.** No
purchases, fabrication, paid run or physical/flight release; WO-10 owner review remains.


## WO-03 bonded brace / explicit thermal matrix / complete recovery budget — 2026-10-30

The [current closure progress](wo03-package-closure-progress.md) records the executed
three-priority studies and separates isolated candidate results from PR #9 active
geometry. Exact clipped rail sections and the internal-ring buckling model replace
optimistic section/support assumptions. The complete bond/shell/joint path remains
open. The 420-row thermal matrix keeps 35°C / 300°C / contaminated foil required and
failed, with unchanged 45°C substrate screen; 25°C rows are proposals only. The G12
complete recovery ceiling is 119.767 g at the unchanged conservative guide/departure
criterion and full 50 g growth. The current 111.034 g allocation leaves 8.734 g.

Local follow-on test run: 123 tests pass. No candidate-only pass closes the installed
fin/root, retention, joint, thermal, recovery-service or integrated WO-03 gates.
No WO-04 start, physical build, purchases, paid run or flight readiness is claimed.


## WO-03 correction revalidation after returning from the preview

The owner resumed WO-03 while frontend/computer-use work stays paused. G80 remains
the reference, G54 conditional and G12 the committed PID-to-RL trainer. Active
vehicle geometry is unchanged and expanded engineering acceptance remains open.

- Verified finite axial/shear and normal/peel fixtures reject the lightweight
  100 mm upper-paper doubler under the retained material screens. Enlarging mount
  bores for continuous multilayer shields removes substantial brace-ring stiffness;
  the old 3.7439 frame factor cannot be reused.
- Segmented eight-layer fixed-motor shields retain the original ring bores and
  calculate G54 44.748953°C / G80 limiting mount 43.249891°C in one combined
  300°C / ε=0.9 / 35°C corner. G54 reserve is only 0.251 K, with +8.899 g;
  G80 adds 5.880 g. Source snapshots match every recorded input hash. Full matrix,
  tolerances, support stiffness and a compatible TVC shield remain open.
- The explicit carbon/PVC fin/root candidate moves 25 mm forward to remove the
  unsupported 25 mm root foot and charges real gap bonds. Fin mass 81.947891 g;
  panel estimate 0.606381 mm at 57.629 N/fin under minimum/hot assumptions. Installed
  root stiffness/peel, compression/wrinkling and dynamic flutter remain unresolved.
- An exact-once ledger removes 3.626547 g duplicated tab/gusset adhesive, leaving
  4.373453 g residual from the old 8 g budget; every additional new bond remains.
- The coherent recovery/cap/link copy adds 66.081 g. With 8 g thermal mass
  sensitivity it passes the unchanged conservative guide arithmetic at 10.01298 m/s
  on current rails, only 0.663 g mass margin. Eleven of 25 combined-motion poses
  still interfere, and matched/single-leg rail loads exceed the estimated capacity.
  A mass subtotal is not compatible thermal hardware or mechanical acceptance.
- Smooth shared-core canopy opening loads do not bound short-stroke snatch. The
  failed 0.3 m recovery structural screen remains required; no limit was waived.

Evidence: [method/fin archive](../runs/wo03-resume-methods-20261031T020000Z/record.json),
[recovery archive](../runs/wo03-recovery-closure-20261031T020015531834Z/record.json),
[thermal G54](../runs/wo03-multilayer-shield-20261031T020146392505Z/record.json),
[thermal G80](../runs/wo03-multilayer-shield-20261031T020146392490Z/record.json),
[closure table](wo03-package-closure-progress.md).

`make check smoke` passes 148 local tests, lint, formatting and strict typing.
`make benchmark` passes the unchanged active static platform and G80/finned-G12
RocketPy flight comparisons plus 4,096-env CPU step. Records:
`wo01-platform-20261031T015813020621Z`, `wo02-20261031T015813539484Z`.
The latter tiny G12 errors are 2.0744% altitude/0.9285% time; historical WO-02
acceptance evidence is preserved. No candidate flight-accuracy or engineering
acceptance claim is inferred. Cost $0; no purchases, physical work or paid runs.

## Thermal material-layout and fitting-baffle continuation — 2026-10-30

- Executed actual-CAD occupancy: slotted ring area606.201718 mm² partitions into540.359846 glue,57.243246 fin,8.598626 open. No full-area parallel air through adhesive is valid; actual open paths still require compatible radiation/gas mapping. [Connection table](wo03-interface-occupancy.md).
- Correct common-surface finite proxy and analytic derivatives: current pre-baffle e250 candidate, CAD1193713, thirty case/corner/end scenarios. Required combined high-k means46.058694°C mount /43.525445°C shell with ambient ends;51.974698/50.083576°C with hot-end assumption. Former one-point pass superseded; no boundary or45°C screen waiver. [Report](wo03-thermal-model-corrections.md).
- Circular-pad fix is explicit candidate-only. Active cache regeneration preserves exactly all six geometries/materials/masses/CG/full inertia. New active CAD and static/flight regressions pass with unchanged inputs. [Cache/geometry proof](wo03-circular-pad-candidate.md).
- Fitting baffle69df candidate:32 new parts nominal clearances pass;24panels/588 sampled rigid assembly poses pass. G54 mass846.009911g;−0.078409g;1.197510cal minimum full growth/depletion; independent RocketPy static endpoints pass. Thermal/structural/flight/root acceptance remains open; no G12 credit.
- G12 forefoil stays rejected as thermal solution:0.753216g,45.912899°C versus45. Part-mean Analysis fields exported only for compatible e250 diagnostic; unavailable part coverage stays unavailable. No active candidate adoption, build, paid compute or flight release.

Compact source-linked evidence: `runs/wo03-thermal-layout-20261031T042330617623Z/record.json`. Full ignored histories/meshes/STEP/source snapshots retain their original hashes locally.

## Actual-CAD thermal layout and common-surface methods — 2026-10-30

**WO-03 remains open; no new actual-baffle temperature pass.** Curated executed
evidence: `runs/wo03-actual-geometry-20261031T052235281133Z/record.json`. Exact candidate `69df790…` / generator
`1193713…` retains notches, seams, adhesive and finite supports. Raw rays/actual
meshes stay local and are pinned by SHA256; no measured strength/temperature.

- Actual occupancy removes duplicate gas through glue while retaining 8.598626 mm²
  open midradius area at each slotted ring. First-hit geometry preserves that
  opening and blocks rays at real solids.
- Three optical levels have zero escaped rays; last global exchange change is
  3.184%. Local convergence remains open. Baffles see adjacent rings strongly,
  so direct-path blocking alone establishes no cooling.
- Gas coarse mesh: 80,186 nodes / 427,940 tetrahedra, all 144,690 source facets
  retained, PLC closure 1.18e−14 relative. Middle mesh is rejected for a zero-
  volume cell; fine attempt reaches 300.05 s cap. No convergence pass.
- Unweighted radiation balancing exceeds simultaneous sampling intervals at 26
  entries and is rejected. Count-likelihood fitting satisfies closure/reciprocity
  and those intervals, but widths up to 0.858 do not establish local precision.
- Common-surface calorimetry over 6/48/384 tetrahedra differs from an independent
  scalar solution by at most 3.86e−15 W; energy error <3e−15 W. Physical gas at
  300 K remains distinct from radiative brightness at 500 K.
- Local regression: 199 tests, Ruff/Black 200 files, strict mypy 74 modules.
  These include unpublished preview/study work; focused-PR checks apply to the
  published subset. No dependency upgrade, paid run or physical work.

The 45°C substrate screen and required 300°C + contaminated-foil / 35°C case
are unchanged. Earlier 44.749°C band-model and 46.059/51.975°C pre-baffle proxy
results retain their historical scopes; they are not new-baffle fields. The
baffle's 846.010 g / 1.197510 calibre remains a separate fit/static candidate
result. Active masses and G12 departure assumptions are unchanged; G12 receives
no thermal or mass credit from the G54 baffle.

[Connection/closure report](wo03-thermal-model-corrections.md),
[gas mesh](wo03-cad-gas-mesh.md), [radiation fit](wo03-cad-radiosity.md),
[coupling verification](wo03-gas-radiation.md).


## Actual replacement-baffle numerical diagnosis and debug transient — 2026-10-30 local

**Completed diagnostic; failed numerical model; temperature acceptance unavailable.**
Candidate `69df790…`, CAD `1193713…`, run
`wo03-actual-transient-20261031T061319026057Z`: 3.026 s burn plus300 s soak,
492.070 s execution,1,062 evaluations,140 part means. Required combined300°C case,
foil emissivity0.9,35°C ambient,nominal properties only. Debug motor-support mean
50.672°C / aft substrate42.585°C / foil-baffle peaks67.497–77.031°C.
**These are not credible physical predictions or a pass against45°C.**

- The separate complete gas-factor repeat returns before its900 s budget but
  fails field checks:181.615–602.731 K under308.15–573.15 K unforced reservoirs,
  194 below-ambient group means. Local rows reproduce the extremes; the trace has
 187 mm axial facets across a0.2 mm gap. No clipping or weaker threshold.
- Global ODE energy residual0.001700 J against2,790.395 J is small. Separate
  connection-energy quadrature has470.811 J maximum local imbalance and remains
  unverified; no accepted dominant-route totals are inferred.
- Stable local heat accounting is implemented and verified separately. Twelve
  fixture levels preserve solve matrices, factors, fields and G/R exactly; C/J
  differ only at recorded roundoff scale. Read-only actual-field ledger residual
  falls to0.103 µW under unchanged1 µW criterion, without changing any field or
  retroactively passing the failed source operator.
- Captured middle replay has five exact flattened cells. One volume optimization
  removes zero cells but has duplicate/nonmanifold topology; duplicate-only
  coalescing remains invalid. Native meshing and targeted planar-boundary
  refinement hit their declared resource caps. The latter preserves surfaces and
  openings but does not achieve its resolution targets; no new volume/heat result.
- Debug Analysis exports force failed validation, retain exact case/configuration/
  CAD identity and mark missing coverage unavailable. Consumer check passes; no
  active registration. Ordinary transient execution blocks failed/incomplete
  source operators; source-artifact and output/vehicle tampering are rejected.

`make check` passes Ruff/Black(222files),strict mypy(77modules); full local smoke
passes224tests. These include local paused preview tests; the focused engineering
PR receives its own exact-head hosted checks. PR #13 is merged at8e71c206… after
all required replacement hosted checks passed (41172768750). Subsequent diagnostics
are the next focused local increment. No dependency upgrade, physical work,
paid run, candidate adoption, full WO04 transition or flight release.

[Detailed diagnostic and gate table](wo03-actual-debug-transient.md).
Curated executed numerical evidence: `runs/wo03-numerical-diagnostics-20261031T065322651352Z/record.json`.
Raw fields/operators/meshes remain local and hash-bound. The active vehicle,
45°C screen,G12 departure requirement/full allowance and all later gates remain.


## Bounded closure and engineering isolation — 2026-10-31

**No complete package or thermal design is accepted.** PR #14 merged at
`a900b884c89e4c77a1c6f338a8cc2fd4c0549c5d` after every required exact-head
check passed in41178650950. [The fixed closure plan](wo03-closure-plan.md) now
states three deliverables, compute caps and stop/replan decisions.

- Mesh preflight closes the resource-feasibility question for the old scheme:
  necessary original-edge subdivisions alone require≥122,166nodes/245,188tris,
  already above120k/240k. A failed cap does not imply failed temperature design;
  another identical full-size attempt is not justified.
- Error isolation: nine independent fixture levels complete in2.303s wall/1.992CPU s.
  Exact linear935:1 gap passes all unchanged tolerances. Curved strong-wall nodal
  error4.616905→1.155561→0.287913K; finest true-boundary undershoot0.287798K.
  Local/global ledgers and5% map convergence pass while local-temperature and
  strict reference-heat checks remain failed. This isolates a spatial/wall-input
  mechanism and forbids promoting energy closure to actual accuracy.
- Support/recovery audit:2.010s. Current69df bore15.8mm retains the brace-ring
  section; the rejected24.8mm-bore penalty is unrelated. Actual channel43.429mm²,
  weakI158.005mm⁴; oldframeλ3.743855 cannot transfer. Netflank110.0505N is distinct
  from upperjoint58.2161N. Conservative DF3 shell-transfer envelope3.20887MPa
  exceeds2MPa. Recovery all-through-rails1,388.822N exceeds660N. Branch forces
  balance, but interface/peel/retention capacities remain unknown.
- Installed-fin audit:6.05s. Common tab/foot equilibrium is verified and converged;
  ideal rigid0.1mm foot carries96.157% root moment and requires2.357MPa hot normal
  capacity atDF3. Actual foundation is unverified; required pure-rotation stiffness
  is360–361N·m/rad, or pure-translation147–148kN/m. No full installed/flutter pass.
  Historical G12+8g thermal mass probe9.98513m/s and rejected cheek9.97616m/s
  remain below10m/s. Full50g and unconfirmed5m guide are unchanged.
- Four mutable recovery YAML aliases have changed source hashes/stale caches.
  Embedded source mass/force ledgers reproduce, but no historical geometry pass
  is transferred. Original failures and copies remain retained.

Motor exterior temperature/end/soak histories, foil condition, hot/wet paper and
bond properties, installed-root stiffness and G54 motorCG are decision-driving
uncertainties. Required evidence is explicit in the plan and individual audits;
no numerical convergence result resolves an estimated material input.

Curated executed evidence: `runs/wo03-closure-evidence-20261031T072741974902Z/record.json`.
The actual-baffle diagnostic remains failed;45°C and combined300°C/degraded foil/
35°C cases remain. No active geometry/mass/CG/inertia change, build, paid run,
frontend/browser activity or flight release. [Current closure table](wo03-package-closure-progress.md).


The two authorized fixture-only corrective wall trials are complete and rejected.
Trial1 (2.524s wall) removes envelope violations but leaves4.21108W strong-wall
continuum source defect at the finest grid. Trial2 (2.534s wall) preserves original
B/D exactly and restores continuum net heat to≤7.48e-13W, yet strong-wall nodal
error remains9.02025K and nested-field change8.430% fails5%. Discrete ledgers
close in both; neither is actual accuracy evidence. This branch is stopped after
two trials; production thermal arrays, failed actual cache and required limits
are unchanged. [Method decision](wo03-thermal-method-decision.md).

The fin-attachment report now explicitly flags its axial-Z root-moment to radial-X
rail-bending mapping as unverified; old numerical surrogate values are retained,
with no installed-capacity or acceptance promotion. The source-bound installed
contact audit above remains the separate recorded calculation at its as-run code.


PR15's first hosted run41181626411 failed before tests because the installed-fin
audit imported an unpublished local driver helper. The unchanged function is now
published in `src/analysis/fin_contact.py`, with AST equivalence to its original
as-run source and a regression importing the published audit and checking its
independent planar-contact/foundation fixtures. Seven relevant local tests,
Ruff/Black and strict module typing pass. The original failed hosted run remains
historical; required checks must pass on the replacement exact head before merge.
No actual engineering calculation or acceptance result changed.


## WO-03 external thermal tools: research-first checkpoint (2026-10-31)

Elmer plus existing CalculiX2.23 were assessed under two declared600CPU-second
packets, oneCPU/120s per case, separate600s setup caps. Elmer setup preflight
stopped after8s with no identified accessible arm64 binary and shell DNS failure;
no Elmer solver ran. CalculiX completed A at2/4/8 and the existing cylinder at
three levels using0.305709 childCPU s, peak cumulative childRSS16.27MB.
Inclusive CalculiX setup wall time is unmeasured, so its setup-budget compliance
is unverified. Two input errors and the explicit format-only replan are preserved.

Cylinder finest field error0.23505K, heat error0.369% and last-two change0.657%
pass those individual existing criteria. Output precision cannot establish the
strict exact-temperature/energy checks; local balance is unavailable. B/B_strong,
narrow finite-wall annulus, transient, contact and radiation remain unexecuted.
The decision is **no actual-baffle solver selection or run**. No production heat
method, required matrix,45C screen or working vehicle changed. See
[comparison and prerequisite decision](wo03-external-thermal-decision.md),
[Elmer sources/setup](wo03-elmer-literature.md),
[CalculiX evidence](wo03-ccx-thermal-comparison.md) and
`runs/wo03-external-thermal-tools-20261031T083118518450Z/record.json`.

The owner separately resumed early preview code/non-browser checks through a
Terra agent. Browser verification/screenshots remain paused pending owner testing.
Failed or incompatible analysis cannot become accepted active overlays.


## WO-03 timed-session load routing and cut equilibrium (2026-10-31)

The archived G12 layered-fin contact calculation is not the69df G54 baffle copy.
Its2.017N m tangent root moment is axial-Z; expressing the same wrench about
the body axis gives3.919N m. This does not add load or determine rail torsion.
Physical Fz/Mx/My remain unknown/null; the old radial-X rail-bending surrogate
remains unverified. Hash-verified historical STEP sections are recorded, with
no material-capacity or installed-flutter acceptance.

For the separateG54 thermal copy, all170 placedSTEP files passed source-hash,
validity and source-CG-in-bounds checks in one bounded60s child (reported6.58s
wall). BRep-extents and nominal-extents cut bounds agree within1.5e-14N across
ninecuts. At1.006m combined nonmotor-path demand is51.682–73.091N under
the explicitly assumed single motor contact. Assigning all of it to the gross
shell would giveDF3 1.507–2.131MPa, straddling the unchanged2MPa estimate;
actual shell/rail/bond shares remain unknown. The prior3.20887MPa all-transfer
scenario remains failed. T/M=157.7084m/s² is inertial-plus-weight specificforce,
not netflight acceleration (verticalnodrag T/M−g=147.9017m/s²).

Three self-contained known-case tests and local static checks pass. The
executed pre-format support source and current formatted source have identical
ASTs. No newgeometry, FEA, heat calculation, designadoption or physicaltest was
performed. Complete recovery/thermal/fin integration remains open. Evidence:
`runs/wo03-load-routing-cutloads-20261031T093433446466Z/record.json`, [fin routing](wo03-fin-load-routing.md),
[support cuts](wo03-support-cutloads.md). Ownerrequested stop remains09:49UTC.


## WO-03 resumed G12 source prerequisite (2026-10-31 Pacific)

The owner resumed work after the saved timed-session stop. The historical
77-part G12 layered-fin/hoop reconciled copy reloads and retains canonical
identity `4ff75b8f2c6ab47ddf90b546761d7fa6d4a72c3af9f382e6b3790cbeb19c1287`.
The fin and rounded frame STEP files are preserved byte-for-byte; all 77
geometric volumes and 76 comparable centroids/full inertia match archived
property precision. The fin's density-weighted properties are not compared
with uniform-volume geometric properties. Detailed historic shape equivalence
is unavailable for the other 75 parts. No installed strength, clearance or
flutter acceptance follows, and no 0.069674 g reconciliation saving is credited.

One child completed in 7.870 s parent-observed wall time, with 3.747 CPU s and
2.292 s worker wall after imports, peak RSS 539,836,416 bytes. Single-worker
execution was requested but single-core compliance was not demonstrated.
All recorded source artifact hashes match before/after; CAD/schema code hashes
were captured after execution only. Active vehicle, CAD, schema and simulator
sources match the published baseline across 53 files checked independently.
No active design or physical/paid/WO-10/flight gate changed.
Evidence: [`record.json`](../runs/wo03-g12-source-refreeze-20261101T010604113596Z/record.json);
[source report](wo03-refreeze-g12-root.md).


## WO-03 output precision and fin-solid mapping (2026-10-31 Pacific)

One new CalculiX A-2 output-only diagnostic completed (0.012015 child CPU s,
0.0200 s wall, 6,160,384 bytes peak RSS). The first reader's framing error
stopped the declared packet; A-4/A-8 were not run. Read-only decoding of the
preserved NT/RFL fields confirms 4-byte node IDs and float32 values. NT spacing
is 3.05e-5–6.10e-5 K; maximum encoded-field difference from the exact A answer is
2.4414e-5 K. This cannot establish the unchanged 1e-7 K field criterion. The
small encoded overshoot of the fixed wall is compatible with float rounding,
not a demonstration of a solver temperature violation or a verified local
maximum principle. Film-integrated heat and 1e-10 W balance remain unavailable.
A malformed-file self-check caught and corrected a truncated-record reader
weakness; no solver rerun followed. Neither external tool qualifies actual heat
predictions; the old impossible baffle fields remain failed.

For the separate historical G12 candidate, the preserved construction recipe
uniquely maps all 60 fin solids by centroid/bounds/volume and two-way Boolean
comparison (reported maximum symmetric difference 0 mm³ at kernel precision).
193 overlapping-bounds pairs had reported zero intersection; the other 1,577
pairs have bounding-box intersection upper bounds at most 3.84e-11 mm³. This
closes solid identity only. Face contacts, installed strength and flutter remain
open. A single child used 7.495 CPU s / 5.118 worker wall s, parent 5.436 s,
peak RSS 513,458,176 bytes. One-worker/thread settings were requested, but
single-core execution is not demonstrated. Sources/configs were unchanged
through execution. The offline helper's later typing comment changes no function
AST and no CAD-source revision; the saved preview remains compatible.

Evidence: [compact record](../runs/wo03-output-solid-map-20261101T011408613691Z/record.json),
[thermal output](wo03-ccx-output-probe.md), [material map](wo03-fin-material-map.md).
No active vehicle, gate or full work-order acceptance changed.


## WO-03 actual root contact and clipped sensitivity (2026-10-31 Pacific)

The original layered G12 fin and G11 frame plus the explicitly current-generated
shell give 281.731344 mm² shell-backed area per foot, versus 355.097301 mm²
on each inner foot face. The shell slots remove 20.6608% of nominal support.
Known planar full/half/gap and cylindrical fixtures pass; independent slot/arc
integration matches BRep common area within 2e-9 mm². Nominal geometric
coincidence does not prove wet bonding, manufacturing fit or material capacity.

After reproducing the archived full-foot matrices/root motion, the masked
rigid-foundation spring sensitivity gives 2.648 MPa smooth DF3 normal demand
versus 2.357 MPa for a 0.1 mm bond. Foot force is 50.404 N and tab force
7.225 N; root-added tip motion 1.197 µm. The old paired planar tab-column
approximation is retained; its boundary differs from the total tab/potting
BRep area because the cylindrical corner has no full opposing planar column.
No full 3D load split, edge-peel or conservative joint bound is inferred.

The contact fixture/actual children used about 7.361 CPU s total. Their actual
child CPU exceeded wall time despite one-worker/thread settings, so single-core
execution is unproved. The clipped arithmetic child used 0.271 CPU s / 0.303 s
wall, 49,643,520 bytes RSS. Three quadrature levels converge, equilibrium
residual is at most 3.56e-14 in the recorded force/moment components, and source
hashes are unchanged. Active vehicle, mass/CG/inertia, CAD and flight model are
unchanged; no rerun is presented as a new physical performance prediction.

Evidence: [compact record](../runs/wo03-root-contact-correction-20261101T012547878277Z/record.json),
[actual contact areas](wo03-root-contact-faces.md),
[corrected sensitivity](wo03-clipped-foot-contact.md). Installed capacity,
foundation, recovery/thermal integration and flutter remain open WO-03 items.


## 2026-10-31 continuation: closed thermal campaign and selected G80 checks

The [Elmer campaign decision](wo03-elmer-campaign-decision.md) closes the declared
small-test campaign: the tool builds/runs, but A fails the unchanged 1e-7 K
known-field checks, refinement is nonmonotonic and complete heat/conservation
and actual-geometry coverage remain unavailable. Neither solver qualifies the
real baffle. Required thermal cases and 45°C substrate screen are unchanged.

The separate [32.2 mm G80 mount candidate](wo03-g80-fit-candidate.md) passes the
cold and in-domain radial stack at 0.150/0.12102 mm against 0.1 mm; its
out-of-domain component-hot sensitivity fails and is retained. The 4.620 g
incremental-annulus upper budget gives 743.804 g loaded, plus a separate full
50 g growth reserve. Actual last-ring surface is 541.114 mm² rather than the
old 606.956 mm² proxy; adhesive coverage, ring/rail/body sharing and retention
remain open. [Load-path evidence](wo03-g80-mount-loadpath.md).

[Candidate flight/reference](wo03-g80-candidate-flight.md) passes nominal
apogee/time comparison (633.432 vs 633.392 m) and guide departure in the three
explicit cases (19.574/17.068/19.834 m/s vs 15). Full-growth loaded passive
margin is 1.2911 calibres, with growth at 1.212 m. Recovery is incomplete at
45 s. Saved-flight [forward shell cut bounds](wo03-g80-axial-flight-bounds.md)
are 1.479/1.158/1.643 MPa maximum sampled uniform DF3 stress, below the
estimated 2 MPa screen under their near-vertical assumptions. These exclude
local joint stress, shell buckling and material qualification; they are not
complete structural acceptance. No active vehicle/CAD or physical/flight gate
changed, and no G54/G12 finding is cleared by the G80 evidence.

The [early preview delivery](wo04-preview-delivery.md) records actual designated
Chrome checks after restart: all four configurations, actual geometry, saved
replay/comparison and unavailable incompatible Analysis. No engine migration.


### Same-package G80 follow-through

The [52-part integrated proposal](wo03-g80-integrated-candidate.md) combines
that mount correction with the existing recovery packaging and regenerates
normal CAD caches. Exact identity is `62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009`.
Mass is **748.569 g + separate 50 g**, growth CG **818.503 mm**, margin
**1.3278 calibres**. Independent preliminary static comparison passes. Its own
[flight comparison](wo03-g80-integrated-flight.md), rather than borrowed
mount-only results, gives **631.216 m JAX / 631.249 m RocketPy** and conservative
guide exit **16.955 m/s**, exceeding 15 m/s. Recovery remains incomplete at
45 s. Three named envelope-contact overlaps are unresolved; no physical fit,
installed load path, fin flutter or thermal acceptance follows. Separate
STEP/GLB exports preserve the working vehicle and preview unchanged.


### G80 through-bolt geometry: stopped conflict and nominal correction

The [retention study](wo03-g80-retention-geometry.md) uses sourced candidate
M3×35/hexnut/9 mm washer envelopes. Its first nominal attempt stopped on
1.098419 mm³ per-washer interference. One input-layout replan changes relief
start R21.5→20.7 mm, retaining 9.6 mm width; screened solid overlaps clear and
three bridge-bearing probes are 54.538 mm². No tolerance acceptance: washer OD
tolerance is unavailable. All sampled radial removal paths meet the shell;
keeper/capture, structural capacity and complete mass/CG/inertia remain open.
The original failure is preserved, with its missing first CPU/before-hash data
explicit. The replan used 5.405 measured CPU s; aggregate CPU is unavailable.
The [captive keeper plan](wo03-g80-captive-retention-plan.md) proposes pre-shell
nut assembly and routine aft cap/motor service; no new keeper CAD run has
executed in that record. Working vehicle, preview and all release gates remain.


### Unchanged keeper geometry: staged service and mass evidence

The first keeper trial stopped on an inconclusive 5° collision-volume probe.
A separate source-specific [analytic rotation barrier](wo03-g80-nut-rotation-bound.md)
justifies investigating bounded centered rotation without changing geometry or
silently passing that old diagnostic. The [one service continuation](wo03-g80-keeper-service.md)
observes 1.406745 mm³ at ±15°, repeats the old probes, and completes nominal
5 mm-spaced pre-shell insertion and aft cap/motor removal samples without
blockers. It exports partial study STEP parts and masses, not a new complete
vehicle: keeper15.410 g, bridge10.177 g, modified plywood/guides40.448 g.
Tracked child CPU is 13.979 s for continuation, 18.428 s including the earlier
keeper child; caps were not reached. Hardware/adhesive ledger, installed force
sharing, torque/strength, tolerance, thermal and complete mass/flight acceptance
remain open. G54/G12 findings, active designs and the preview remain unchanged.

## Frozen G80 candidate: recovery horizon completed — 2026-11-01

The [bounded recovery follow-up](wo03-g80-recovery-horizon.md) retains the
52-part identity and all existing physics/settings, extending only the horizon
from45 to180s. All three cases reach modeled ground at114.980/80.500/128.370s;
pre-ground speeds are5.966/6.180/6.178m/s and calm-air horizontal distances
6.786/8.065/9.939m. Growth cases exceed the preliminary6m/s screen; no target
is relaxed. Nominal ascent remains within0.01% of RocketPy apogee/time, which
does not validate recovery. The packet completed in16.730s wall/17.004s
reaped-child CPU under120s/120CPU limits. Exact sources match before/after.
This closes simulation-horizon incompleteness only; deployment, installed load
paths, canopy uncertainty and the later keeper/bridge package remain open.
Active designs, preview, other modes and release gates remain unchanged.

## G80 bridge inputs: moment corrected, area gate still open — 2026-11-01

The [guarded bridge packet](wo03-g80-bridge-fea.md) records a geometry-only
pass, the first coarse load-moment stop, and one explicitly declared equivalent
washer-resultant mapping replan. The latter produces31,435nodes/15,819C3D10
tetrahedra, with maximum bounded pressure perturbation0.00363323% (<0.5%).
Independent serialized applied load/moment checks pass. Its mesh washer area
is54.538570981mm² versus54.538048466mm² CAD; +0.000522514mm² exceeds the
unchanged0.0002mm² guard. It stops beforeCCX; no stress, reaction, displacement,
energy or installed-strength result exists. The one mapping attempt used
2.599childCPU s/2.728wall s; no second retry or laterlevel follows. Existing
limits and all failed/stopped source snapshots remain preserved.

The [retention ledger](wo03-g80-retention-mass-audit.md) leaves the complete
new package mass/CG/inertia unresolved, while the [fin intake](wo03-g80-installed-fin-intake.md)
identifies the exact unclosed G80 root/flutter evidence. Full local checks pass
(Ruff, Black, mypy;279tests plus3subtests), supporting software consistency only.
The macOS process-control tests run locally; only their platform-specific
libproc probes skip on Linux. No acceptance or physical-release gate closes.

## G80 source-specific preparation: boundary accuracy, fin loads and recovery sources

The [known annulus comparison](wo03-g80-washer-area-method.md) isolates
quadratic circular-boundary approximation: area errors are+.006444961,
+.000408875 and+.000025650mm² for24/8,48/16 and96/32 outer/inner segments.
The last meets the unchanged.0002mm² criterion; analytic arc area agrees
within1.7e-13mm². Source-pinned small-case controls pass; actual bridge
fragmentation and3D feasibility remain unverified, with no further actualtrial.

The [G80 fin intake](wo03-g80-fin-loads.md) reuses exact52-part180s telemetry.
It reports powered scalar per-fin estimates.502–.698N and.0176–.0244Nm
root-torque magnitudes, distinct from unvalidated noncoincidentCN2 sensitivities
and unsupported large-angle coast/recovery estimates. No installed-root or
flutter pass follows. [Official canopy source options](wo03-g80-recovery-canopy-sources.md)
replace none of the active parts; the35g allowance remains unsourced, and
sizing-only substitutions use full-growth burnout mass with50g retained.

A [macOS exit-observation race](wo03-owned-process-guard.md) found during the
full local suite is preserved and narrowly corrected; the subsequent current
suite passes285tests plus3subtests, withBlack/Ruff/mypy checks. This supports
execution reliability, not engineering closure. The designated Chrome agent
confirms currentG80 preview availability; all working core/vehicle/UI source
files checked against publishedGit blobs remain unchanged.

## G80 bridge: first completed native run, failed equilibrium — 2026-11-01

[Geometry and input-control evidence](wo03-g80-bridge-boundary-case.md) confirms
three source-centred Circle patches. The96/32 coarse grid stops at63,788nodes
versus50,000. A [separate analytic area budget](wo03-g80-washer-area-budget.md)
justifies48/24 through the sum of absolute disk deficits0.000127566mm² below
its0.00015budget, without changing the0.0002actualarea gate. The one final
coarse case then passes input guards at42,850nodes/22,495tets, with areaerror
+0.000049781mm². CalculiX returns0 and finishes both loadsteps.

The [native-output diagnostic](wo03-g80-final-coarse-diagnostic.md) fails strict
force balance: equal/single axial reaction totals−45.3032/−127.9073N versus
+150Napplied, residual104.6968/22.0927N, millions of times the printed
roundoff scale in the equalcase. RawU/stress/work isunvalidated, notstrength
evidence. Read-only node/face/output/Jacobian checks do not identify thecause.
Mesh/solverCPU9.513/7.130s and19.644wall remainwithin45+45CPU/120wall
limits. Nativefields staylocal; compactsource/failure/audits are archived.
No furtherfull3D attempt, thresholdrelaxation, activevehiclechange oraccepted
Analysisoverlay follows. Next is smallknown-answer output verification.

## Mechanical known-case output diagnosis — strict certificates unavailable

The [flat A/B cases](wo03-ccx-reaction-fixture.md) and [Poisson D diagnostic](wo03-ccx-poisson-diagnostic.md)
complete as the three declared native fixture slots. Printed displacements meet
their analytical references and observed force residuals are near numerical
zero, but1e-5N certification remains unavailable due to conservative native
rounding bounds; no threshold is relaxed. OriginalAB stops afterA; B is a
separate authorized diagnostic, D the finalslot. C remains unrun after its
input moment failure. Cases support only their stated printed-resolution
comparisons, not actualbridge validation. The estimated-upper-bound MPC row
is not evidence of a hiddenMPC; equation counts match uniqueSPC arithmetic.
Source/input/binary hashes and all stopped histories are archived, with no
additional fixture, actualbridge or accepted Analysis field selected.

## Controlled Elmer implementation comparison — complete, unqualified

The three classic A2/A4/A8 cases completed exactly once after one explicitly
recorded resource-only launcher replan. The prior launch failed before Elmer
executed because a child could not raise its inherited CPU hard cap; that
failure and its misleading pre-launch flag interpretation remain preserved.
The completed packet reserved270CPU s below600, with native children0.740CPU s
and parent1.213CPU s. SIF physics, all four mesh files, UMFPACK, precision and
the original saved Vec outputs were unchanged.

[Classic results](wo03-elmer-classic-comparison.md) agree with Vec within
5.4e-12K. Both fail the unchanged1e-7K exact-field threshold, with nonmonotone
errors1.93e-5/1.12e-4/3.74e-5K. Classic conductive-heat reference errors pass
their separate tolerance; local/Robin/algebraic energy balances and raw-C
convergence remain unavailable. Density warnings are retained, not suppressed.
The [read-only audit](wo03-elmer-local-error-audit.md) reconstructs the reference
from literal SIF values and finds exact saved-coordinate matching; spatial
errors persist and their cause is unidentified.

The [updated decision](wo03-elmer-campaign-decision.md) rejects implementation
switching as a correction and leaves both tools unqualified for actual-baffle
acceptance. The0.000112K toy error is much smaller than a physical design
temperature margin, but cannot bound actual-geometry errors or fill missing
conservation/refinement evidence. No threshold, required thermal case,45°C
screen, active vehicle, preview asset or release gate changes. No automatic
new grid, solver run or production heat method follows this closed campaign.

## Integrated G80 retention package — isolated Stage 1/2

The72-part candidate `90b2a9ad780fc81d11171363432c46088531817ddb6570fe9f800429bde2bdfc` now includes modified mount/guides, separate keeper/bridge, explicit M3/M2 hardware and1g estimated locking/materials reserve. The old7g lump is removed once; finish, fin bonds, conservative adhesive budget and the full50g allowance remain. Twenty-one affected solids match pinned STEP sources. Loaded mass772.982g, growth mass822.982g, growthCG829.167mm and full tensors are reconciled at the real staged CAD revision. Active designs and preview assets remain unchanged.

[Static/flight results](wo03-g80-staged-retention-results.md) pass preliminary independent static comparison and growth loaded/burnout margins1.1663/1.5483cal. Four guide departures exceed15m/s (minimum16.848m/s); nominal apogee620.610m vs RocketPy620.650m and time errors meet5%. All four180s trajectories reach modeled ground. Saved vertical speeds6.070/6.280/6.277/5.895m/s mean three fail the unchanged6m/s vertical-descent target. All four total-ground-speed diagnostics exceed6; these are distinct physical quantities. No independent descent/wind validation follows.

This closes changed-part bookkeeping and affected numerical comparisons only. The actual bridge reaction failure, hot load paths, installed fin/root/flutter, thermal qualification, locking/tolerances and three recovery overlaps remain open. The [closure table](wo03-g80-current-closure.md) keeps those design items separate from later owner measurements and proof/deployment/flight gates.

## G80 larger-canopy screening and recovery load-path decision

[Five isolated cases](wo03-g80-canopy-stage3-results.md) replace the35g canopy placeholder once with supplier-listed51.6g Apogee29095, assumeCd0.75 under the existing circle-area convention, and retain full50g growth plus a separate5g line/connector sensitivity. All sampled vertical speeds5.049–5.849m/s pass6; guide minimum16.366m/s passes15 on the assumed1.5m guide. Windy total speeds6.027/6.553m/s exceed6 as a separate impact diagnostic. Nominal apogee613.213m vsRocketPy613.234m meets5% ascent comparison; it does not validate descent, wind, canopy opening or physical packing. Full-growth masses839.582/844.582g have loaded margins1.361/1.419cal.

The original73-part sensitivity failed build/cost metadata completeness. A new unpriced metadata-only copy has all20 builder arrays bitwise equal across its four cases and unchanged full mass/CG/tensor; original failed evidence remains intact. Only metrics and last-prelanding samples were retained from Stage3; full trajectories are unavailable for replay/guide-row audit. No repeat was run to fill that gap. Drag-area sensitivities are illustrative assumptions, not measured confidence bounds. No active design or preview asset changes.

The [recovery intake](wo03-g80-recovery-path-intake.md) and [plain-body cut](wo03-g80-recovery-axial-screen.md) reveal an actual design dependency: at0.500m the paper body is the only modeled structural path. A conservative wholly-aft mass lower bound gives existingDF3 off-nominal gross demands4.631–10.416MPa versus the configured estimated2MPa paper screen. This is a failed design screen under its assumptions, not measured material failure. Local anchor/spreader strengthening alone cannot bypass the serial cut; continuous lightweight recovery load paths or body reinforcement require evaluation. The20.4m/s probe is not an approved delay and opening-shock uncertainty remains.

All numerical, supplier, hot-joint, anchor, packing, thermal, installed-root/flutter and owner-performed physical qualification gates remain open where not explicitly closed. G54/G12 evidence is separate. No purchases, physical work, paid compute or flight release.

## Source-pinned recovery route and reciprocal-work diagnostics

The [bounded straight-route check](wo03-g80-backbone-route.md) imports all72 individual saved STEP parts. Both nominal3.5mm and inflated4.1mm straight cord envelopes clear modeled manufactured solids at the two declared azimuths; minimum inflated clearance is0.45mm at the coupler. Select60° as the next layout reference because180° intersects an adhesive budget envelope of unresolved actual occupancy. No attachment, bend, slack, deployment or service path is modeled. Itemized terminal/protection mass and complete-package revalidation remain required.

The [read-only reciprocal-work audit](wo03-g80-bridge-reciprocity-audit.md) on the preserved bridge finds W12=34.25509 andW21=2.02603Nmm, a32.22906Nmm difference against3.253e-6Nmm conservative printing uncertainty. Both native fields are complete and are end-of-step results at times1/2, oneincrement each. Linear source/deck conditions and unchanged hashes are recorded. No new solver was run; the result does not identify a tool bug or validate strength. The [backend/output research](wo03-ccx-backend-output-assessment.md) records documented alternatives and unresolved installed-format/precision behavior, with no automatic execution.

A [guide-clock proof attempt](wo03-g80-guide-clock-audit.md) remains unadmitted after source review found its constrained-motion precondition does not cover internalRK4 release. Its hypothetical arithmetic/conditional flags are not acceptance evidence. No missing trajectory was fabricated or run repeated. Requirements, interfaces and FMEA retain stable IDs/open status and link the isolated evidence separately from active/G54/G12 acceptance.


## WO-03 structural solver decision — 2026-11-01

The same saved layered-bar problem was compared through isolated output/backend
pilots. B1 completed but could not certify step1 force at 1e-5 N once float32
encoding uncertainty was included. B2 completed but failed known displacement
(maximum transverse magnitude 0.08850 mm versus the 1e-8 mm zero-component gate).
Both stopped records remain preserved; no actual bridge rerun used either route.

Elmer StressSolve/direct UMFPACK loaded the isolated pinned module and produced
Float64 fields. Its original EQUAL packet stopped because the log classifier
matched an unused keyword name; a separately admitted read-only assessment of
that saved output passed displacement and strict force. The remaining SINGLE
case was then separately admitted once and passed: maximum axial error
6.2241e-15 m and axial support residual9.547e-11 N (Float64 encoding bound
1.066e-14 N). EQUAL maximum axial error was2.0751e-15 m and axial force
residual−1.793e-11 N. No sign, numerical criterion or physical input was changed.
Original stop, recovered evidence and continuation are distinct records.

The [decision](wo03-structural-solver-decision.md) selects this specific existing
solver path for bounded bridge input preparation, not engineering acceptance.
Each native small case used under0.2 CPU seconds; process success is separate
from its known-answer checks. Setup is partly unmetered. Memory samples/caps
cover root processes only, not aggregate trees; the earlier module-build tree
claim is explicitly unverified. Active vehicle/CAD and G54/G12 are unchanged.
WO-03, actual bridge, thermal, installed-fin/flutter and recovery acceptance
remain open. No physical work or paid compute occurred.


The bridge input-only v2 conversion retains42,715 used nodes with an explicit
ID map;135 unused nodes carry neither support nor load. It checks one connected
component, seven material regions,1,574 supported nodes/694 support faces and
exactly roundtrips3,184/1,072 original load tokens. The original stop compared
CAD with mesh volume at a serialization threshold. Saved G11 mesh volume is
5501.023169931971 mm³; converted serialized geometry gives5501.023169933384 mm³,
while CAD is5500.998158294296 mm³. The unchanged1e-8 preservation check now
compares mesh against mesh; the separate original1% mesh/CAD check also passes.
This is a corrected comparison target, not a relaxed physical criterion.
The [input report](wo03-elmer-bridge-input.md) preserves the stop and diagnosis.
No actual bridge solve occurred; direct nodal-RHS verification remains separate
from the uniform-traction known cases and is not yet qualified.


The separately admitted single [nodal-RHS B fixture](wo03-elmer-nodal-fixture.md)
now passes using the exact13 original SINGLE load tokens with Target Nodes /
Displacement3Load. Native Float64 fields map all593 nodes; maximum axial error
6.2246e-15 m and axial support residual9.533e-11 N (encoding bound1.066e-14 N).
Child usage0.172743 CPU/0.216612 wall seconds, sampled root RSS13,778,944 bytes;
parent1.292624 CPU seconds. All source/prefix/generated hashes match after.
No actual bridge solve, retry, sign change, threshold change or vehicle adoption.
This supersedes only the preceding statement that this source path was untested.


## G80 actual bridge: recovered coarse Elmer fields — 2026-11-01

On the preserved22495-tetrahedron/7-material model, EQUAL and SINGLE saved
Float64 fields pass the unchanged1e-5 N force criterion; axial residuals are
−7.884e-10 and−1.115e-9 N. Reciprocal-work difference2.637e-16 N·m is within
4.840e-16 N·m encoding bound. Maximum displacement magnitude0.380782 and
1.157007 mm respectively. These are coarse numerical consistency observations,
not stress, convergence, contact, hot-material or installed-strength acceptance.
See [quantitative report](wo03-g80-bridge-elmer-results.md).

Both native processes returned0/loggedALLDONE, but EQUAL workflow missed its
output directory and SINGLE supervisor failed its terminalRSSquery. Separate
read-only recoveries used the saved fields; no native case was rerun. An import-
path-only continuation stop occurred before any SINGLE native process. All
stops/admissions/outputhashes and restored disabledconfigs remain preserved;
SINGLE resourcecompliance remains unverified. NativeCPU15.172/14.745 seconds,
well below120/case; tree/truepeakRSS are unavailable. Current mass/CG/tensor,
activevehicleCAD and flight predictions are unchanged. WO-03 remains open.


## G80 bridge stress and support screen — 2026-11-01

A separately known-case-verified element/Gauss postprocessor recovered local
stress without projecting it across G11/epoxy interfaces. Raw150 N service
G11 sampled von Mises maxima85.246/257.346 MPa, film shear maxima1.455/4.418 MPa
and largest positive film-normal values1.770/8.285 MPa are diagnostic only:
no laminate, mixed-mode/peel or converged capacity is established. The source
bridge preflight applies DF3 to demands once; the CAD variable's word“design”
is ambiguous, and already-factored recovery1782.253 N is a separate case.

Independent support-force/area lower bounds give DF3 tangential values
3.965/4.007 MPa on two critical SINGLE faces against the estimated1 MPa hot
shear screen; EQUAL values1.044–1.065 MPa are also adverse. This justifies
keeping the bond-only candidate unaccepted under the stated model without
calling local stress peaks converged. [Support record](wo03-g80-bridge-support-traction.md),
[stress method and evidence](wo03-bridge-gauss-stress.md).

One3 mm mesh pilot stopped on a metadata key-type mismatch after meshing; its
saved input was checked read-only, not regenerated. The remaining2 mm pilot
ran once and passed input guards. Together with the saved1.5 mm grid they have
21341/30384/42850 declared nodes but do not demonstrate uniform regional
refinement; film normal span remains0.1 mm. They are not a three-grid stress
convergence result. The physical bridge web remains2 mm in all cases.
Known B native stress output separately passed its original axial2% and the
primary-declared full-component2% checks. No further actual-component native
solve or working-vehicle change occurred in this increment. WO-03 remains open.


## WO-03 G80 rail capture / continuous-frame decision — 2026-11-01

**Both specified envelopes stopped at hand preflight; no installed requirement
closed and no CAD/FEA admitted.** The previous bond-only bridge remains adverse:
DF3 mean shear3.965/4.007MPa versus estimated1MPa hot screen. Numerical force and
reciprocal-work consistency does not establish installed capacity.

B's optimistic full-width pin bearing is12.50MPa versus generic10MPa plywood;
bearing requires pin≥3.75mm while net section needs hole≤3.25mm under that same
unqualified screen. Its12mm pin cannot span the16.2mm fork outside width. C's
strips intersect the real coupler; fitting its bore leaves≤59.665mm² and ideal
already-factored recovery stress29.87MPa versus estimated25MPa hot G11, before
joints/holes. Generic strengths are estimates, not hot joint allowables.

The defined stock ledgers, including separate full50g growth, are B820.702g
with specified removal credits /847.608g without, and C1016.315/1043.221g.
These are **not installed masses or bounds**; unknown attachments, clipping,
shielding and adhesive remain. Full CG/tensors and source identities are in
[runs/wo03-g80-capture-comparison-20261101-v1](../runs/wo03-g80-capture-comparison-20261101-v1/manifest.json).
The [supplemental hand packet](../runs/wo03-g80-capture-bounds-20261101-v1/record.json)
checks conditional support flexibility, pin engagement and isolated kA/L heat
routes. Six independent arithmetic checks pass;0.059 CPU s within the declared
10 CPU/15 wall-second packet. No transient temperatures or thermal acceptance
are produced. Required300°C/contaminated-foil/35°C cases and45°C substrate
screen are unchanged.

[Integrated decision and closure table](wo03-g80-capture-decision.md) selects
one next direction only: short captured G11 aft subframe linked to the protected
aramid backbone, with separate body/fin/motor restraints. It is not a third
executed candidate. Active vehicle, previous flights, inspector/replay and
separate G54/G12 tracks remain unchanged. New browser verification is blocked
by the designated agent's unresolved runtime-ownership prerequisite; its
ownership-only handoff confirms no retry/bypass. Physical qualification and
all release gates remain later; aggregate WO-03 is open.


## WO-03 S1 short subframe admission — 2026-11-01

One specified G11 cassette/clevis arrangement is **not admitted** before detailed
CAD/FEA. [Connections, force diagram, margins and decision](wo03-g80-short-subframe-decision.md)
cover motor, fin, body and recovery joints without rigid-support strength credit.
The [packet](../runs/wo03-g80-short-subframe-20261101-v1/record.json) retains
source hashes, removal ledger, all defined component/hardware budgets and the
unchanged archived guide implementation.

Source844.582g including full50g grows to a1057.417g cut-blank/preliminary budget;
mandatory-solid mathematical floor is937.673g under the retained estimated
ledger. The unchanged20.4m/s/0.3m/DF3 recovery case therefore gives1978.696N at
the floor or2231.382N at the budget, rather than carrying the old1782.253N
unchanged. M6 clevis net ratio1.136 does not close bearing: projected demands
25.368/28.607MPa exceed the generic25MPa hot comparison, not a qualified bearing
allowable. M3x16 heel screws cannot span minimum17.3/17.8mm stacks.

The source1.5m mass-only guide screen gives14.190m/s at the full budget versus
15m/s; its full-mass ceiling is958.398g. Mandatory solids plus just the defined
M3 sets reach985.079g. These are conditional model/ledger bounds, not physical
measurements or a new JAX/RocketPy flight. No temperature, installed fin/root/
flutter, full inertia, actual CAD or interface acceptance follows. One hand
packet used0.385CPU s within10CPU/20wall; no native or free-flight calls and
no automatic variant was run. Required thermal cases and45C screen remain.

Required IF-RECOVERY-001 change is a dimensioned through-frame saddle/strap
load-spreading endpoint and coupled complete mass budget, with actual eye/pin/
foot support, not an ideal fixed connection. No industrial lifting hardware,
longer guide or raised property limit is adopted. Active vehicle and separate
G54/G12/RL gates remain unchanged. PR41 and independent replay-race fix PR42
are merged after both required jobs passed (41359972531/41361056195). Browser
runtime ownership remains unresolved; code tests are not visual verification.


## WO-03 IF-RECOVERY-001 S2 coupled admission — 2026-11-02 UTC

**Not admitted.** [S2 diagram, dimensions and joint/mass decision](wo03-g80-saddle-study.md)
records one closed-strap/G11-saddle and independent compression-carrier concept.
[Load audit](wo03-recovery-load-assumptions.md) keeps5/20.4m/s, required.3m and
DF3, identifies mean energy-equivalent force versus unmeasured opening peak,
and recalculates complete participating mass plus separate50g. No force, stroke
or factor was reduced for the design.

Diagnostic S2 full mass932.677g (882.677+50) is124.740g below S1. Guide15.230m/s
passes formal15 but misses the predeclared15.5 planning margin by.270; its
source-model mass target is903.854g, needing28.823g reduction. Severe demand is
1968.154N. CG estimate836.297mm with partial±6.522mm cut/backbone sensitivity;
old-source CP proxy gives1.058/0.959cal nominal/aft, not a new aero benchmark.
No full inertia/CAD or physical mass qualification follows.

Tube whole-force mean10.421MPa/scalar ratio2.399 does not establish contact.
At25% effective contact it is41.682MPa versus estimated25. Point-junction saddle
pressure24.775MPa has only1.009 scalar ratio and requires an unprovided lateral
reaction or free-motion assessment. Finished hot loops and eye capacity remain
unavailable. Nominal16.1mm keeper grip grows to16.65mm under stated assumptions
versus16.0 minimum; as-run aft foot has3.8mm gap to rail ends. Motor/carrier
expansion sensitivities can close case endplay; they are not temperature results.
Required300C/dirtyfoil/35C and45C substrate matrix remains.

V1 output stopped on NumPy-boolean JSON serialization; one output-only retry
preserved computational AST/config equality. V2 final pair is small, but first
fore-collar32to64 change.052988g exceeds declared.05g. Original records remain;
maintained code now checks every adjacent pair and regression tests enforce it.
No criterion relaxation, another grid, CAD/FEA/heat or free flight followed.
[Two-attempt packet](../runs/wo03-g80-saddle-study-20261102-v2/manifest.json)
records.921CPU/1.123wall direct-child total; parent/setup CPU unmeasured.
[Read-only connection audit](../runs/wo03-g80-saddle-connections-20261102-v1/record.json)
used.371CPU under3CPU/5wall after those observed totals. S2 outputs remain
unqualified diagnostics; all three saved levels miss the planning target.

Required interface reconsideration is a common positive recovery carrier /
fin-frame / body receiver with independent motor thermal capture and service.
The retained modified wood frame is about34.39g, not a free removal credit.
No next prototype or native analysis is admitted. Active designs, separate
G54/G12/PID-RL and physical/purchase/paid/WO10/flight gates are preserved.
Independent frontend graph-provenance PR44 merged after both required jobs
passed in41366658113; browser runtime ownership remains blocked, without retry.


## Integrated G80 aft admission — 2026-11-01 local / 2026-11-02 UTC

**Decision: no credible complete arrangement selected.** S2 evidence is now
published in merged PR45 after both required jobs passed in41370492131.
Its stopped output attempt, failed0.05g adjacent-pair volume check and unresolved
physical interfaces remain unchanged; no stopped calculation was repeated.

The [integrated aft decision](wo03-integrated-aft-proposal.md) evaluates one
additive receiver sketch jointly with fin/body capture and motor retention.
Six cheeks span the3.8mm receiver gap on paper, but the complete joint is not
accepted. Additional named stock44.812g gives927.490g nominal partial stock
plus separate50g =977.490g. This is not complete installed mass or a bound.
It exceeds the saved source-guide15m/s mass ceiling958.398g by19.092g and the
separate15.5 planning ceiling903.854g by73.636g. No exact new guide speed or
complete inertia is claimed. The same20.4m/s/.3m/DF3 opening screen at that
subtotal is2062.718N; nominal5m/s gives150.944N. Conditional point-junction
curvature pressure25.966MPa exceeds the unchanged provisional25MPa screen;
finished hot harness/contact capacity and actual reactions remain unavailable.

A partial station sensitivity gives CG840.742–860.157mm and old-source-CP
margin0.991–0.697cal; it is not a full uncertainty bound or new static/aero
benchmark. Motor thermal endplay remains unqualified, including the saved
negative-gap sensitivity. Required thermal cases and45C substrate screen remain.

The specific architecture direction replaces duplicated wood frame/carrier/
collars with one positively connected aft receiver. Removing the named139.061g
source bundle once leaves705.521g including growth; all replacement functions
and hardware must fit a gross198.333g at15.5 planning or252.877g at formal15
under the same guide-model hypothesis. These are admission ceilings, not free
credits or an accepted design. No further physical variant, CAD, native stress/
heat or free-flight campaign was admitted. Body/fin/harness/motor joints,
service, thermal and installed flutter stay open. Active vehicle, preview CAD,
G54 upgrade and G12/PID-to-RL evidence remain separate and unchanged.

[One saved-data arithmetic packet](../runs/wo03-g80-integrated-aft-decision-20261102-v1/record.json)
completed within its declared2CPU/5wall-seconds allowance; after-import work
was0.003919CPU/0.004183wall seconds, with setup/earlier hand work unmeasured.
This closes the bounded admission decision, not an engineering acceptance
requirement or physical verification gate.


## Coupled S3 receiver and launch-guide/motor comparison — 2026-11-01 local

Owner-authorized parallel Sol HIGH launch study:12 unique motor/usable-guide
hypotheses with formal15m/s, separate15.5 planning and full separate50g.
G80 total formal/planning mass roots at1.5/1.8/2.4/3m are958.398/903.854,
1126.575/1063.511,1446.649/1368.353,1745.798/1654.908g. The strict<1500g
physical ceiling supersedes larger mathematical roots. At1.8m the complete
source replacement budget is421.054/357.990g. These are conditional model
ceilings, not desired mass or a universal≈1kg limit. G54 has source/data/
certification/state/stock/integration gaps; G33 fails even at3m. G25W quarantine
and separate G12/PID-to-RL remain. The three same-hypothesis executions total
2.420CPU/2.528wall seconds; metadata-only provenance corrections did not rerun.
See [comparison](wo03-launch-guide-motor-trade.md) and
[ADR-0012](adr/0012-conditional-launch-guide-options.md).

Current CAD has rod lugs, not1010/1515 buttons. ROC lists rail types without
lengths; MDARS lists approximately10ft1515 and1010 backed by1515. Neither our
access nor pad/start/release/wind/acceptance is confirmed. The owner explicitly
confirmed nothing booked; both sites remain conditional. Baseline1.5m is
unchanged. For S3's1227mm tail and old250mm upper-lug leading edge with assumed
100mm pad offset,10ft clear overall gives only1.971m illustrative usable travel.

The [S3 connected layout](wo03-g80-connected-receiver.md) gives real matching
end datums, positive cap joints, motor stop keys, captive fin pins and explicit
strap/skirt/service openings. It is NOT ADMITTED: new budget494.101g gives
1149.622g nominal + separate50g =1199.622g; loaded/burnoutCG892.599/879.220mm,
CP906.140mm and margins0.205/0.408cal versus1.0. Full intrinsic tensor unavailable.
Guide1.5/1.8/1.971m gives13.200/14.469/15.146m/s; last passesformal15 only,
misses15.5 planning. Severe loaded mean opening screen2531.467N, nominal185.246N;
burnout severe2399.578N. Constant heavy channels alone214.534g dominate mass.
Current24mm aft-cap bore also prevents29mm motor service without releasing the
recovery cap. No CAD/FEA/heat/free flight or active adoption follows.

V1 interpreter/import and input-key failure are preserved. One explicitly
authorized input-wiring correction produced v2 at0.502CPU/0.581wall seconds;
failedCPU unavailable, observed failed wall0.532s, not zero. A separate read-only
primary connection audit adds full recovery cap sensitivity (M3tension503.27MPa
versus estimated200),75%-width loop pressure33.085MPa versus25, actualhole net
ligaments and opposing half-depth fin contacts1.577/1.328MPa. The favorable raw
full-face0.363MPa proxy is superseded. Force/moment balance verifies arithmetic,
not installed capacity. Serial paper/bonds/peel, contact, hot finished eyes,
nozzle/thermal clearances, installed root/flutter and all later qualification
remain open. New thermal6g allocation is not an accepted shield; required
300C/dirtyfoil/35C and45C substrate cases remain unchanged.

Independent frontend PR48 merged after both required jobs passed in41377369956:
missing metadata in both runs now remains unavailable rather than a false match.
Twelve frontend tests and build/lint/format pass. Browserownership and agent
port-binding blockers remain without retry/bypass. Existing preview geometry
and all physical/purchase/paid/WO10/flight-release gates are preserved.


## C1 coupled mass / balance revision — 2026-11-01 local

[Selected preliminary direction](wo03-g80-mass-balance-revision.md): closed
G11 receiver with counted local socket/hardpoint/key/process stock and swept,
tapered fin panels. No ballast or equipment move is selected. Complete nominal
1079.807g plus separate50g =1129.807g; replacement package424.286g,69.815g below
S3. CG879.798mm, recalculated CP966.828mm give1.319cal loaded/1.546 burnout;
requiredCGfor1cal900.828mm. With extra20g aft beyond50g and source12.8mm
motor-CG exploratory probe, loaded mass1149.807g/CG887.264mm/margin1.206cal.
This probe is not a validated uncertainty bound. Full intrinsic inertia unavailable.

Lightening with old fins gives0.391cal, not a pass. Its8g nose carrier plus
51.781g nonmetal slug reaches exactly1cal at1193.674g, but exceeds the proposed
24x45mm/2400kg/m3 slug capacity48.858g. Nominal radial profile is clear; packing,
retention and actual nose fixture remain unverified. Existing equipment cannot
supply S3's missing0.06293kgm moment: an unbuildable all-equipment-at225mm upper
bound is0.01428kgm, while5mm whole-main-sled move gives0.000420kgm only. No
source equipment, independent recovery supply or aft50g reserve is relocated.

SelectedC1 guide1.5/1.8/1.971m gives13.663/14.975/15.676m/s:1.8 FAILS formal15
and is not rounded upward. Additional20g probe gives13.526/14.826/15.519.
Required nominal usable travel1.805867m for15 or1.927373m for separate15.5;
old-lug/start assumption gives2.882867/3.004373m clear overall, not actual
available equipment. Owner confirms NOTHING booked at eitherROC/MDARS;
[short confirmation sheet](wo03-launch-equipment-confirmation.md) preserves
current official types/inventory/dates/support and missing actual geometry.
The1.5m baseline is unchanged; advertised10ft is never accepted as usable travel.

Opening mean screens atfullmass: A oldfins2392.764N, B withcarrier/ballast2518.916,
selectedC2384.141N, Dadditionalprobe2426.345N, same20.4m/s/.3m/DF3. Fin force/
root moment afterDF3 rise to220.759N/8.830Nm versus149.421/5.230. Those loads,
new thin-body/socket construction and unchanged adverse cap/body/harness,
thermal/45C/300Cmatrix, exactmotor, guide/club and installedflutter findings
remain open. Positive mass/static screens do not qualify this construction.
NoCAD, stressmesh, heatmethod orfreeflightcampaign ran;activevehicle/previewunchanged.

Four scenario/three guide-probe packet withtwo selected-case travel roots used
0.605CPU/.689wall under20CPU/30wall. Initialkeyvalidationstop preceded numerical
work and is preserved in v1; one primary-authorized key-wiring correction kept
config/numbers unchanged. Separately oneCP-only RocketPy1.13.0 comparison agrees
atMach0 within3.33e-16m, using1.189CPU/2.045wall under20CPU/20wall. Placeholder
reference mass/inertia do not validate the candidate's full vehicle. Exact source
hashes and separate evidence scope are in the saved v2records; no stoppedS3 or
12-combination motorstudy was repeated. G80first,G54upgrade,G12/PID-RL and all
physical/purchase/paid/WO10/flight-release gates preserved.

## 2026-11-02 C1 installed-fin preflight

**Current C1 attachment checkpoint (2026-11-02):**
[C1 source identity](wo03-c1-attachment-source-lock.md) is frozen at1079.807g
nominal + separate50g =1129.807g. The one [R1 installed-fin reinforcement
preflight](wo03-c1-fin-attachment.md) is stopped before CAD/native analysis:
+70.111g, bridge mean hot shear4.756MPa>estimated1MPa, corrected ideal aggregate
movement1.039mm>1mm, adverse static margin0.991984cal<1.0. Nominal/adverse
masses1199.918/1219.918g miss conditional15.5m/s planning by47.602/67.602g.
Adverse formal speed15.000251870m/s on illustrative1.971m has only0.035501g
headroom and is not useful margin. C1 remains selected preliminary; no active
change or installed/thermal/flutter acceptance. The one next construction
preflight is a lightweight sandwich fin/dense captured root and mechanically
closed socket, with complete replacement mass and finite end/body connections.
Keep1.5m baseline, full50g,15m/s formal and separate15.5 planning unchanged;
all equipment remains unconfirmed. G54 and G12/PID-to-RL stay separate.

Known rectangular-beam final error0.0000391%; three-level strip-integration
final change0.0005064%. Contact equilibrium closes arithmetic, not installed
strength. Packet0.400CPU/0.478wall seconds within20/30s; no native/CAD/thermal
or free flight. The read-only connection audit corrects receiver torque
reference without rewriting or rerunning the original packet. Full inertia,
actual C1/R1 CAD, thermal fields and installed flutter remain unavailable.

## 2026-11-02 C2 and first engineering walkthrough

**C2 bounded correction — rejected before detailed CAD/FEA (2026-11-02):**
The [complete sandwich/socket preflight](wo03-c2-sandwich-socket.md) removes
196.092g and adds250.021g, net+53.929g. Full50g nominal/adverse totals are
1183.736/1203.736g, loaded margins1.139/1.034cal. Hypothetical1.971m speeds
15.263/15.116m/s pass formal15 only; planning15.5 and unchanged1.5m fail.
Receiver-pad hot mean shear3.828MPa>1, floor58.501MPa>25 and motion2.328mm>1
fail; actual nominal2D harness/link envelopes overlap. No installed engineering
requirement closes. Do not admit CAD/native analysis or another local glued pad.
The necessary interface change is continuous structural socket/receiver/end
moment transfer compatible with the recovery route. C1 stays preliminary; G54
and G12/PID-to-RL stay separate. Existing physical/paid/WO10/flight gates remain.
The saved axis-to-tip conversion now uses123mm: C1/R1 scalar aggregates
3.198/1.054mm; earlier3.179/1.039 proxies remain preserved as superseded.

The frontend implements linked source-derived arrangement/sections, forces/freebodies, R1addition ledger and mass/launch plots. C1CADnull, no fake spatialfield. Code/API/SSR evidence and blocked browser ownership remain separate; see walkthrough/inventory.


## 2026-11-02 C3 continuous-connection preflight

**C3 continuous-connection preflight — not admitted (2026-11-02):**
The [one bounded packet](wo03-c3-continuous-connection.md) replaces local pad
transfer with integral channels and positive cap pockets as design intent.
Its aft central barrel node physically overlaps independent motor arms;
nominal harness gap0.647848mm becomes−0.052152mm after the existing bounds,
below0.1mm. Complete counted mass adds105.504g: nominal1235.311g and adverse
1255.311g each include full separate50g. Illustrative1.971m departure14.891938/
14.754038m/s fails formal15; adverse stability0.957949cal also fails.
No installed engineering requirement closes; no CAD/FEA/thermal/free-flight
run is admitted. Keep the59.299g body-support receiver counted until a defined
replacement earns its credit. Next interface must separate motor-retention
travel from end-fastener stock and combine body-support/torsion functions;
do not restart a local-pad or unchanged-channel variant. G80 stays first,
G54/G12 remain separate,1.5m baseline and all gates unchanged.

The single10CPU/15wall-second packet used0.353/0.421seconds. Four read-only
evidence checks verify frozen sources, complete mass/balance/opening accounting,
retained failures and missing capacities; they are not strength qualification.
The executed script remains archived; only dict-literal lint normalization was
made afterward, with normalized-AST equivalence checked without rerunning physics.
