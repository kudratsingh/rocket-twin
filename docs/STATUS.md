# Status

Updated: 2026-10-30 (run IDs use UTC)

## Current work order

**Owner-directed return to WO-03 (2026-10-30):** engineering development is resumed.
Frontend preview and computer-use work remain paused. Saved preview edits and run
records remain local; its focused PR has not yet been opened. The current work is
the complete brace-ring/bond/body load path, required thermal cases and recovery
within the unchanged G12 guide/mass screen, including installed fin/root behavior.
Candidate corrections remain isolated until one complete package is revalidated.

**WO-03 active and open; authorized early WO-04/05 preview is paused.**
Custom construction, maximum practical conventional performance and committed
PID-to-RL remain core. [ADR-0009](adr/0009-early-inspection-experiments.md) records the
owner's explicit sequence exception for read-only inspection, recorded Analysis,
real backend experiments and replay/comparison. Full WO-04/05 prerequisites and
completion criteria remain; no engineering, physical-build or flight release.

The current correction studies verify finite axial/peel calculation fixtures,
reject the thin paper doubler, and identify the brace-stiffness loss from enlarged
shield bores. Segmented foils preserve the original bores and calculate G54
44.749°C in one combined hot/degraded-foil corner, with only 0.251 K reserve;
the complete candidate matrix and a compatible G12 shield remain open. The
forward-shifted carbon/PVC fin/root copy is 81.948 g, with explicit gap bonds.
Reallocating duplicated root adhesive removes 3.626547 g from the vehicle bill.
The complete recovery/fin copy with an 8 g thermal mass probe passes the guide
arithmetic narrowly (10.01298 m/s on current rails), but rod/cassette motion and
matched/single-leg rail capacity still fail. No candidate is adopted. See the
[closure table](wo03-package-closure-progress.md), [thermal correction](wo03-multilayer-shield.md),
[fin/root study](wo03-trainer-fin-package.md) and [recovery audit](wo03-recovery-budget-closure.md).

Latest local validation: `make check smoke` passes **148 tests**, lint, formatting
and strict typing. `make benchmark` passes the unchanged active static platform
and actual G80/finned-G12 RocketPy comparisons, including the 4,096-environment
CPU step: `wo01-platform-20261031T015813020621Z` and
`wo02-20261031T015813539484Z`. These are regression results for the active vehicles,
not acceptance or flight predictions for the rejected/candidate corrections.

The unmerged local preview is `http://127.0.0.1:5173`; its local `make preview`
launcher and frontend changes are held for a separate PR while preview work is paused.
The owner started the host servers because this session cannot bind ports or reach
npm. The configuration-switching bug (duplicate sibling component keys retaining
earlier parts panels) is corrected. The post-fix Chrome cycle verified one parts
list and one centered viewer for all four designs, selection, isolation, body
hiding and explosion. Two browser-triggered full CPU JAX runs completed, replayed
and loaded as a comparison: G80 calm `exp-173525a242be493e8e3268471b8e16aa` and
conditional G54 with 3 m/s eastward wind `exp-da02d58e35af404faf2802bea54c942b`.
Preview evidence is saved locally in `docs/wo04-early-preview.md`. TypeScript, lint, three
frontend boundary tests and the production build pass. The API serves actual
hash-checked CAD/specification data, and a real tiny JAX experiment test passes. These are
implementation checks, not full work-order acceptance. Experiment runs are
preliminary and unguided; finless unguided execution is unsupported.

The active specs now combine the recovery package, stiffer fins/gussets, hot G11
supports, mica/foil and serial end-pad isolation, improved fits and motor retention.
The mode-level recovery power override was found and corrected in all six variants;
the resolved-network regression passes. [ADR-0008](adr/0008-integrated-wo03-corrections.md)
and [closure table](wo03-correction-closure.md) identify adopted parts and open items.

G54's defined full-growth/depletion minimum is **1.045596 calibre**, with **867.991 g**
including the full 50 g allowance. It remains conditional: an additional exploratory
motor-CG sensitivity fails, along with high-case/degraded-foil shell temperature.
[Mass, CG and full inertia](wo03-integrated-vehicle.md) use the complete package.

The preserved PR #9 CAD export `wo03-20261030T205235088123Z` passes all six variants,
neutral rigid intersections and both 25-pose TVC sweeps at that CAD revision.
Local source-owned bore/machining support changed the CAD code identity. Fresh
`wo03-20261031T000244802098Z` passes all six CAD mass/solid/interface cases and both
25-pose TVC sweeps with unchanged inputs; active geometry remains the PR #9 design.
This export benchmark does not close expanded engineering acceptance. The preserved
27-case flight campaign `wo02-20261030T204849990760Z` passes the five nominal RocketPy
comparisons and 4,096-env CPU step with unchanged code/inputs. G12 reference errors
are now 2.064% altitude / 0.917% time, not the historical 0.004% claim.

Standard upper thermal cases pass after the combined corrections; G54 300 C and
contaminated-foil sensitivities still fail the conservative 45 C shell screen.
Dominant fin stress/displacement and body modes converge; small fin components,
installed-root peel/stiffness and full flutter remain open. Minimum frame/liner
fits, service/arming/routing and recovery-anchor capacity remain design items.
Physical qualification is separately retained in the owner-performed stages.

PRs #4–10 are merged after required hosted checks. Geometry remains the
[PR #9](https://github.com/kudratsingh/rocket-twin/pull/9) integrated baseline.
[PR #10](https://github.com/kudratsingh/rocket-twin/pull/10) publishes the subsequent
analysis/budget tools at `e41c6c0693da02afa27b1c208cbd97eb16c73261`; exact-head
workflow `41149095128` passed before merge.
The next correction package remains isolated: no braced-mount, recovery-anchor or
trainer-fin candidate is adopted merely because an individual screen passes.
Earlier closure-foundation test run: 123 tests passed; the latest local check is recorded above. See the [three-priority closure progress](wo03-package-closure-progress.md),
[checkpoint](wo03-current-checkpoint.md) and [results](results.md). No purchase, physical work or paid compute.

### Completed WO-02 milestone

**WO-02 numerical benchmark met on the owner's Mac CPU.** [Core PR #2](https://github.com/kudratsingh/rocket-twin/pull/2)
merged; [validation/study PR #3](https://github.com/kudratsingh/rocket-twin/pull/3)
merged with the final evidence and hosted checks. WO-03 is now active; the
following numbers are the preserved pre-CAD WO-02 baseline.

The completed WO-02 revision passed 65 tests, formatting/lint and strict typing. `make benchmark`
passes both the preserved static platform and actual G80/finned-G12 flight checks.
Full study `wo02-20261030T044930127544Z` compares all five nominal models within 0.004% of RocketPy,
checks a 4,096-env CPU step, and closes recovery in all 27 cases by 360 s. Tiny
`wo02-20261030T045326632046Z` takes 10.10 s (<120 s). Source/input hashes stay unchanged
through each final run. [Results](results.md) and [report](wo02-flight-study.md).

Conditional direction: keep G80 as reference; G54 leads the practical near-160 N s
upgrade trade (+20.7% nominal altitude, +80 g installed integration mass in the
preserved study). Its prior 1.023 cal aft-growth estimate was before latest CAD
reconciliation; the pre-integration all-growth-aft checkpoint failed 1 cal; ADR-0008 now records the combined correction and its remaining sensitivities. Fixed
G12 leads calm altitude but fails the conservative
3 m guide screen and weathercocks substantially. G33 has a departure shortfall.
No hardware/motor/delay choice is frozen. G25W remains quarantined.

Remaining gates: exact motor/source/hardware/lot/California/stock/club evidence;
actual site/altitude/footprint and guide; high-g sensor calibration and packaging for G80/G54;
CAD/measured mass, structural/thermal/recovery tests; PID authority then committed
RL, HIL and finless burnout transition. Custom mechanical work, maximum practical
conventional performance and serious PID-to-RL are all retained. No purchases,
physical work, paid run or controller implementation; WO-10 owner review remains.

### Completed prior milestone

**WO-01 rebaseline complete at preliminary numerical-model scope.** The revised
benchmark passes for performance, finned TVC and finless TVC; `make check smoke tiny
benchmark` passes with 53 tests. Evidence: `runs/wo01-platform-20261030T022439939715Z/record.json`.
WO-02 is now authorized and active; this evidence remains the completed WO-01 baseline.

Core objectives: meaningful custom fabrication/integration, maximum practical
no-HPR performance, and committed PID-to-RL training/embedded/real-flight comparison.
See [ADR-0006](adr/0006-modular-platform-rebaseline.md), [active WO-01](work-orders/WO-01-vehicle-spec-mass-cp.md)
and [bounded trade](wo01-rebaseline.md). Original fixed assumptions below are historical.

The historical WO-01 66 mm × 800 mm hybrid platform has shared upper equipment and distinct
fixed G80 performance / G12 finned TVC / G12 finless TVC aft models. Mass including
50 g growth: 522.0 / 625.8 / 582.2 g. Physical fins and offset servos enter mass,
inertia and aero; independent RocketPy endpoint comparisons pass for every mode.
Inventory previews include every part's build/cost/learn metadata. CAD and full BOM
remain WO-03/09. Every passing record explicitly retains `flight_ready: false`.

## Current open verification and access items

- Numerical motor hypotheses are source-consistent, but exact offered hardware,
  certificate/curve/envelope/CG correspondence, delay, lot and stock are not frozen.
  G80 direct checked pages are out of stock; G12 advertised length conflicts with
  report/curve. G25W remains quarantined. F25/G54/G50 threshold-only exclusions are
  reopened for their appropriate new modes; old rejection records are preserved.
- Confirm the actual California club/site/date. ROC/Lucerne remains an assumption.
  Exact California motor classification and club/RSO acceptance are independent
  prerequisites; a general motor threshold or passing model is not launch approval.
- WO-02 numerical flight/guide/wind/recovery checks are complete; actual flight
  qualification remains open. Later gates: CAD/load/heat/fit
  plans in WO-03; realistic PID/RL in WO-06/07; owner fabrication/measurement and
  independent recovery in WO-09; firmware/abort/HIL in WO-10; staged flights in WO-11.
  Finless negative margin and loss of TVC at burnout require a qualified recovery
  transition. RL is committed, with honest negative comparisons retained.
- Full dependency lock and fresh Mac/full-stack install evidence remain pending.
  Hosted CPU CI installs WO-01/reference pins on clean Linux; results are on PR #1.
  No dependency versions were upgraded in this rebaseline.
- Private GitHub repository `kudratsingh/rocket-twin` confirmed. Connector write access
  works; the full project is published on `wo-01-modular-platform` in
  [PR #1](https://github.com/kudratsingh/rocket-twin/pull/1). Local `.git` creation
  was previously denied and terminal GitHub connectivity/auth remain unavailable in
  this session; publish through the authenticated connector without stopping local
  development. Initial feature commit: `6eaa665b98d3d27b2e8386db5d9c4eb9f5887fd1`.
  GitHub CPU CI and merge status are available on the PR; the local benchmark above
  is independent evidence. Keep the repository private until owner direction changes.
- Initial hosted CI caught line-ending normalization in three archived `.eng` uploads.
  Restore original bytes through base64 Git blobs and protect `*.eng -text` in
  `.gitattributes`; do not rewrite provenance hashes. Final hosted result is on PR #1.
- No purchases, physical work or paid runs. No routine PR review requested; explicit
  WO-10 owner review and repository protections remain (`AGENTS.md`).

## Benchmarks met

| WO | Met on | Evidence (run id / PR) |
|---|---|---|
| 01 | 2026-10-29 | `wo01-platform-20261030T022439939715Z`; 53 tests; [PR #1](https://github.com/kudratsingh/rocket-twin/pull/1) |
| 02 | 2026-10-29 | Historical acceptance baseline: `wo02-20261030T044930127544Z`; 65 tests; [PR #2](https://github.com/kudratsingh/rocket-twin/pull/2), [PR #3](https://github.com/kudratsingh/rocket-twin/pull/3). Fresh unchanged-code full campaign: `wo02-20261030T173859843386Z` (27 cases, 4,096-env CPU, RocketPy comparisons, benchmark passed). |
| 03 | | |
| 04 | | |
| 05 | | |
| 05b | | |
| 06 | | |
| 07 | | |
| 08 | | |
| 09 | | |
| 10 | | |
| 11 | | |
| 12 | | |

## Spend

| Run id | WO | GPU | Hours | $ | Approved by owner |
|---|---|---|---|---|---|
| | | | | | |

Compute running total: $0. Hardware running total: $0.

## Historical blockers and decisions (superseded by rebaseline above)

- Motor download blocker is resolved: owner successfully ran the updated POST
  collector. Source bytes and raw API responses have been audited locally.
  A full `uv.lock` remains pending network-enabled resolution.
- Owner decided to retain the 1.6 mm body tubes and investigate stronger,
  long-burning 29 mm propulsion within WO-01. That design question is resolved.
  The 1.2 mm study remains archived and is not the working baseline.
- Source collection and local visual PDF review are complete. Exact G25W
  RMS/DMS identity, assembled mass/dimensions and current certificate correspondence
  remain unresolved: the reviewed TRA report says 62 g propellant, versus 97 g in
  the downloaded curve header. Historical G25 data correspond to the old NAR
  report but do not establish a currently purchasable RMS variant. Downloaded
  molded-case F25 is rejected for the default because its curve ends at 2.69 s.
- F22 post-test evidence is now resolved: owner downloaded the May 2, 2026 report;
  all three pages reviewed and unchanged PDF archived. Representative curve gives
  TWR 2.361 at 576.9 g with +20 g mount reserve. Reject F22 for this baseline.
  Seven-second-delay samples also failed for long delay; formal decertification
  is not inferred from that result. Historical curve remains comparison-only.
- Maximum-impulse G screen: CTI 143G33-9A Mellow + Pro29-3G case + standard rear
  closure is the first follow-up configuration, not selected. At 197 g assembled
  plus 20 g mounting / 50 g vehicle-growth allowance: 693 g and summary TWR 4.812.
  Checked reload/case/closure product pages are out of stock; curve mass semantics,
  complete installed envelope, exact California classification and club acceptance
  remain open. CTI 159G54 lists 2.97 s; no rounding to a three-second pass.
  See [ranked study](wo01-g-motor-shortlist.md). Actual club/date confirmation is
  pending; ROC at Lucerne is the PLAN assumption, not an owner-confirmed booking.
- `git init -b wo-01-vehicle` was denied by filesystem permissions on `.git`.
  No repository, remote, branch, commit, or PR was created.
- Preliminary 529 g vehicle gives average-thrust/weight 2.772 < 3. At the cited
  14.38 N average thrust, target mass is at most 488.8 g. Revisit CAD mass estimates
  or certified motor selection before accepting the benchmark.
- Club/RSO policy and selected recovery delay remain owner decisions before hardware work.

## Decisions taken by the agent (one line each, link ADR if any)

- 2026-10-29: Work starts at WO-01 per the kit. `make tiny` runs implemented stages only.
- Absolute part start stations increase aft from the nose; explicit CG offsets avoid
  treating every component's front face as its CG. Parent IDs are assembly membership.
- Added regulator, arming switch, pyro board and harness estimates to close missing
  netlist endpoints and mass accounting. No estimate was reduced to force a benchmark.
- Motor summary uses the cited NAR certificate/RASP header; `curve: null` explicitly
  records that the source `.eng` download is still absent. No thrust curve was fabricated.
- Preliminary negative finless static margin is expected; it is not a control validation.

## Latest continuation — 2026-10-29

- Rechecked shell access: PyPI DNS is still unavailable. Web research can read the
  documentation, but cannot install packages into the local environment.
- Next unblock step (normal macOS terminal at the project root): `make setup-reference`.
  This installs RocketPy 1.13.0 beside the existing pinned WO-01 dependencies. It is
  a local dependency install, costs no cloud compute, and does not install CAD/web stacks.
- Corrected ogive CP using external nose volume rather than a fixed 0.466 L factor.
  CP is now 0.0732321 m aft from nose; CG/mass/TWR are unchanged. The analytic
  tangent-ogive volume expression independently checks the numerical integral.
- F15 source selected for eventual byte-preserving import: ThrustCurve record
  `5f4294d20002e900000007e5`, John Coker, 2013, certification-derived. The older
  Howard Smart record explicitly describes an approximate reconstruction; do not
  silently substitute it. The selected source is a historical data snapshot, not
  a claim that the motor's certification status has been freshly established.
- G25W is only a candidate for later digital comparison. Its certification-labelled
  ThrustCurve file reports 152.4 mm / 170 g whereas the motor summary says 124 mm /
  121 g. Do not mix those variants or select it solely from the summary TWR.
  Sources: https://www.thrustcurve.org/motors/AeroTech/G25W/ and
  https://www.thrustcurve.org/simfiles/5f4294d20002e900000007ea/ .
- No paid runs, hardware changes, flight code or later work orders were initiated.

## Reference validation completed — 2026-10-29

- Owner's RocketPy installation verified: RocketPy 1.13.0, SciPy 1.17.1, NumPy 2.4.6.
- Run `wo01-20261029T215941498110Z` (`runs/wo01-20261029T215941498110Z/record.json`) passes the WO-01 static
  mass/CG/CP/margin tolerances at liftoff and burnout for the configured model and
  the opposite stub-geometry case. Errors are at floating-point precision.
- The adapter assembles independent RocketPy objects from part inputs; it does not
  feed our computed vehicle CG/CP to the reference. RocketPy requires a single dry
  airframe aggregate, so individual part measurements are not independently validated.
- Without `.eng` data, a constant-thrust GenericMotor is used ONLY to define the
  fully loaded/depleted endpoints. No intermediate thrust or flight result is claimed.
- Additional real-reference checks cover conical/elliptical noses and a transition.
  Inertia is excluded from this benchmark; adapter inertia placeholders are zero.
- 20 mm optional stubs yield liftoff static margin -2.687 cal with unchanged mass.
  This is an aerodynamic sensitivity case, not a buildable fins-on configuration.
  WO-02 requires a separate passively stable reference geometry after WO-01 closes.
- `make fetch-motors` was attempted: all three requests fail DNS. The collection
  script requests Estes F15, AeroTech F10 and G25 candidates through the documented
  API, saves every RASP variant and metadata under ignored `data/motor-downloads/`,
  and labels all data unreviewed. It does not certify, choose or order any motor.
- WO-01 remains open; WO-02 has not started. No paid compute was used.

## Downloader HTTP rejection — 2026-10-29

- Owner ran the original downloader from the normal terminal; search requests for
  all three candidates received HTTP 403. This differs from the session's DNS
  restriction. The rejection layer/cause is not yet identified.
- Updated search and download to the JSON POST interface shown by ThrustCurve's
  official example, with explicit JSON headers and an honest rocket-twin client
  identifier. GET is also documented; the prior method was not proven to be the cause.
- HTTP/API errors now save bounded response diagnostics to each candidate's
  `data/motor-downloads/<candidate>/error.json`. Cookies are excluded. The collector
  stops after 401, 403 or 429 rather than repeating requests across candidates.
- Regression checks exercise the outgoing method/body/headers, bounded 403
  diagnostics and stopping behavior. `make check smoke` passes (35 tests).
- A live attempt from this session still fails DNS, so successful server access
  is not claimed. The next terminal command remains `make fetch-motors`.
- Official protocol reference: https://www.thrustcurve.org/info/apidemo.html .

## Source review and geometry proposal — 2026-10-29

- Updated downloader succeeded in the owner's terminal. All local source hashes
  were checked both against inventories and base64-decoded API response bytes.
- Archived selected F15 source unchanged, with source/certificate/date sidecar.
  Reconciled mean thrust (14.379341 N) and impulse (49.6087275 N s) from that curve.
  Static RocketPy validation now uses the real source curve, not the placeholder.
- Archived F10 historical and both G25 variants with explicit unresolved/rejected
  review states. Missing certification dates are null, never fabricated from file
  upload dates. These entries do not pass `certified_curves_complete`.
- Catalog auditing now checks original hashes and calculated summary values; a
  configured motor must agree with its accepted source. Tamper rejection is tested.
- Intermediate-time mass check: the exact piecewise-linear thrust integral agrees
  with RocketPy's direct integral. RocketPy's default 100-sample spline of integrated
  mass differs by at most 3.92 mg / 2.03 micrometres CG over 501 sampled times; this
  numerical interpolation is documented in the test, not treated as physical error.
- Proposed 1.2 mm tubes are nominal three-wall shells at a 0.4 mm line width. Their
  masses are derived from volume and the same estimated PETG density; other masses
  were retained. No claim of structural adequacy is made.
- `make check smoke` passes (37 tests). Main geometry still fails TWR; proposal
  meets nominal TWR but has only ~10.3 g of mass headroom and unverified structure.
- No WO-01 completion, WO-02 start, physical build, procurement or paid compute.

Baseline evidence: `runs/wo01-20261029T220952512841Z/record.json`.
Proposal evidence: `runs/wo01-20261029T221057430780Z/record.json`.

## Owner direction and motor selection study — 2026-10-29

- Owner explicitly retained 1.6 mm tubes and authorized a local WO-01 motor-selection
  study. No thinner-shell adoption and no flight simulation until WO-01 closes.
- Added `make motor-study`: evaluates separate source-file hypotheses with +0/+10/
  +20 g incremental mounting reserves. RASP loaded mass includes casing/hardware
  once; it is not added again. The existing 16 g mount stays in every mass budget.
- At fixed motor-front station, the 124 mm and 152.4 mm G25 sources protrude 10 and
  38.4 mm past the unchanged 700 mm vehicle. Separate conditional cases move only
  the motor forward to preserve the aft station; they do not verify mounting fit.
- With +20 g mounting reserve, old-source G25 gives 565.7 g / TWR 3.996 / 5.3 s;
  RMS-labelled source gives 616.0 g / TWR 4.190 / 4.414 s. Their static RocketPy
  comparisons pass under uniform midpoint motor CG assumptions, not measured CG.
- Exact motor identity remains unresolved. AeroTech's certification index separately
  groups NAR G25 under single-use and TRA G25W-10A under RMS-29/120. The matrix and
  product page name the same reload but disagree on mass, propellant and duration.
  These fields are not mixed to manufacture an accepted candidate.
- F25W single-use is added for summary screening: manufacturer matrix says 98 mm,
  90 g, 25.6 N, 3.1 s. Its exact curve/variant must be checked: a different molded
  F25 source can burn less than 3 s. No duration requirement has been relaxed.
- Added `make fetch-motor-study-sources` to collect the matrix, dimension drawing,
  both G25 certification documents, F25 certificate and F25 API curves. PDF bytes
  and SHA-256 are archived for local review; no motor is auto-selected.
- Local attempt still fails DNS. The manufacturer-linked NAR PDFs are scans with
  no extractable text; web screenshots did not expose a usable image here. The
  TRA G25W-10A PDF timed out. Publication details/dates are not guessed.
- `make check smoke motor-study` passes (42 tests). Extra checks cover casing
  accounting, mounting reserve, geometric overhang, the 3 s floor, PDF response
  validation and unchanged baseline body parts.
- Main vehicle YAML remains unchanged in this study. The thinner proposal remains
  available under `configs/studies/tvc-ascent-f15-1p2mm.yaml`.
- No motor selected, no hardware ordered, WO-01 open, WO-02 not started, spend $0.

Motor-study evidence: `runs/wo01-motors-20261029T223729544856Z/record.json`.

## Source collection and visual review completed — 2026-10-29

- Ran `make fetch-motor-study-sources` successfully in this session: five PDFs
  and the F25 source curve are archived locally. The earlier DNS blocker did not
  recur. Rendered certificates, the RMS dimension drawing and matrix pages 2/4
  were visually reviewed; reviewed values/hashes are in the study evidence YAML.
- Historical NAR G25 report (tests dated 1995-09-02) supports the 124 mm, 62.5 g,
  117.50 N s, 5.30 s source. Its delay-specific initial masses explain the 119.7 g
  header as a rounded mean, not a selected delay. Certification issue date is
  unstated; a test date is not substituted.
- TRA G25W-10A letter dated 2013-12-10 lists 170 g loaded / 62 g propellant /
  149 mm / 4.20 s, with stated validity through 2018-12-31. It calls the motor
  Reload in the text and DMS in the graphs. The curve's 97 g header remains
  quarantined; the report does not resolve the RMS-29/120 identity or current status.
- RMS drawing shows a 31.75 mm aft closure and separately dimensioned aft span;
  nominal bore and a 140 mm summary cannot establish installed fit. No mounting
  changes or fit claims were made.
- F25's historical report gives 3.05 s, but the fetched newer molded-case curve
  ends at 2.69 s. Archived its unchanged bytes and rejection provenance under
  `configs/studies/motors/`, added it to the reproducible study and retained the
  three-second requirement. With +20 g reserve it gives 543.2 g / TWR 4.939;
  numerical static comparisons pass but nominal performance correctly fails.
- `make check smoke motor-study` passes (42 tests). The baseline, thinner proposal
  and original motor curves remain unchanged. No replacement selected, no paid
  compute/procurement/GitHub actions, WO-01 open and WO-02 not started.

Updated study evidence: `runs/wo01-motors-20261030T002511325861Z/record.json`
(UTC run ID; local date 2026-10-29).

## Next candidate screening — 2026-10-29

- Incorporated the owner's completed local visual review; G25W remains quarantined
  and the molded F25 remains rejected for its 2.69 s source duration. No previous
  certificate conclusion or source bytes were changed.
- Investigated F22J RMS-29/40-120 as the next 29 mm candidate. Its manufacturer
  pages publish 19.6 N / 3.31 s and separately sold RMS hardware, but mark the reload
  CLEARANCE / cancelled when stock is gone. Purchasability is not established by
  a manufacturer listing or a third-party stock aggregator alone.
- The -5J product lists 132.9 g, the -7J lists 135.6 g; the 2024 matrix assigns
  those masses to the opposite delays. Both masses are preserved as hypotheses,
  not silently resolved or applied to an exact selected delay.
- Current NAR interactive list (updated 2026-08-12) lists F22J with 55.08 N s and
  links a post-certification test, while older published performance is 65 N s.
  Do not combine the newer impulse with an assumed legacy duration/thrust curve.
- Added `make f22-study` (summary screening only) and `make fetch-f22-sources`
  (four source PDFs plus F22 RASP API data, archived separately under
  `data/f22-study-sources/` and `data/motor-downloads/AeroTech_F22/`). The correct
  hobby RMS-29/40-120 dimension drawing is requested, not the G25 RMS-29/120 drawing.
- At +20 g mounting reserve, legacy-summary screening gives 578.9–581.6 g and
  TWR 3.452–3.436. The newer 55.08 N s impulse would require burn duration no
  longer than 3.234–3.219 s to meet TWR 3 at those masses. This is a necessary
  feasibility bound, not a measured burn or a hybrid source curve.
- Added conservative mass-interval screening and configurable source-collection
  profiles. Summary outputs explicitly stay ineligible for selection and contain
  no invented time trace, CG or RocketPy comparison.
- `make check smoke f22-study motor-study` passes (44 tests). Hashes checked against
  the owner's last run: baseline and all four earlier study source curves unchanged.
- Shell network access still fails DNS here; the optional connected runtime could
  not start. No successful F22 download is claimed. Next normal-terminal step is
  `make fetch-f22-sources`. No manufacturer/vendor messages were sent.
- No replacement selected, no purchase, no hardware changes, WO-01 open, WO-02 not started.

F22 screening record: `runs/wo01-motors-20261030T003713058296Z/record.json`.
Source URLs and unresolved mass assignments: `configs/studies/f22-selection.yaml`.

## F22 source collection and historical comparison — 2026-10-29

- Ran `make fetch-f22-sources`: historical NAR certificate, hobby-case drawing and
  one RASP source downloaded. Current NAR post-test PDF returned HTTP 403; the
  collector skipped the other NAR PDF after denial and exited nonzero. A normal
  web read also returned 403. No successful current-report retrieval is claimed.
- Visually reviewed both complete downloaded PDFs. Historical certificate names
  RMS-29/40-120, effective 1993-12-23, tested 1992-07-18: 65 N s / 3.31 s /
  46.3 g propellant / 124 mm / 135.6 g loaded for delay 4. This is historical
  correspondence, not reconciliation of the current listing or clearance stock.
- Archived unchanged 2000-commented user RASP source in the study directory:
  64.996987 N s / 3.31 s / 134.2 g loaded / 125 mm. Sidecar explicitly retains
  current-test and exact-delay uncertainty. Original G25/F25 files were untouched.
- `make f22-study` now includes a historical source-curve static comparison. With
  +20 g reserve: 580.2 g / TWR 3.451, source-defined aft station held with 11 mm
  motor forward shift. RocketPy comparisons pass under the midpoint-CG assumption;
  no installed envelope, mount or gimbal fit is verified. Both summary mass
  hypotheses remain separate; no curve is adjusted to the newer impulse.
- Drawing is titled RMS-29/40, revision A dated 2003-10-08, and has additional
  projections/closure dimensions beyond nominal casing length. This is not proof
  of a complete installed F22 envelope. Reviewed fields and hashes are in
  `configs/studies/f22-source-evidence.yaml`.
- Rechecked public NAR listing (updated 2026-08-12): F22J still says 55.08 N s.
  The inaccessible post-test report's actual duration/trace/mass remain the
  immediate blocker. Legacy nominal performance does not establish current fit.
- `make check smoke f22-study` passes (44 tests). Baseline, thin proposal, original
  curves and earlier PDF archives have unchanged hashes. No motor selection,
  procurement, paid compute or GitHub action; WO-01 open and WO-02 not started.

F22 historical comparison: `runs/wo01-motors-20261030T005512950204Z/record.json`
(UTC run ID; local date 2026-10-29).

## Maximum-impulse G survey — 2026-10-29

- Screened all 93 catalogue G motors and checked direct manufacturer/vendor
  sources. G12ST-P is the highest-impulse in-stock match verified for the motor-only
  constraints: approximately 144 N s / 12.7 s, Wildman SKU 6030 available at $48.49.
  CAL FIRE letter dated 2021-03-03 explicitly classifies it as a Model Rocket Motor.
- It is unsuitable for the unchanged airframe: estimated 596.3 g with +20 g
  reserve gives mean TWR 1.934-2.052, below 3, and plugged recovery requires a
  design change. No G12ST-P adoption or purchase is recommended for this baseline.
- CTI 143G33-9A Mellow is the preferred design candidate: 143.1 N s / 4.38 s /
  32.7 N, estimated 643 g / TWR 5.186. Wildman and Chris' Rocket Supplies show
  no stock. Exact fit, source acceptance and corrected-stock bulletin status
  remain prerequisites; no buy-now US configuration was verified.
- CTI G54's manufacturer duration is 2.97 s and was not rounded up to satisfy
  the three-second constraint. Quarantine/rejection of G25W/F25 is unchanged.
- Recorded public-source survey and point-in-time stock hashes in
  `runs/wo01-g-survey-20261030T011221865663Z/record.json`. No vehicle/source-curve
  changes, procurement, paid compute, GitHub action or WO-02 work.

## F22 post-test and maximum-impulse G screen — 2026-10-29

- Imported owner's downloaded NAR post-test PDF unchanged; visually reviewed all
  three pages and extracted page 3 points separately. F22 fails baseline TWR:
  576.9 g / 2.361 at +20 g mount allowance. Report mean 14.52 N also fails.
- Report's FAIL concerns long seven-second delays; formal certification revocation
  is not inferred. Legacy curve bytes remain unchanged and historical-only.
- Added `make g-impulse-study`, comparing 29 mm leads and separate 32/38 mm options
  with +20 g mounting and +50 g vehicle-growth budget. Audited all 93 records of
  the existing full catalogue snapshot; six metadata leads remain before TWR,
  identity and stock filters. Rechecked G12ST-P's CAL FIRE model classification
  and live Wildman listing: eligible motor evidence exists, but vehicle TWR fails.
  No flight propagation.
- CTI 143G33-9A Mellow / Pro29-3G / standard rear closure / no spacers is the best
  clear long-burn performance lead: 143.1 N s / 4.38 s / 693 g / summary TWR 4.812.
  Not selected: checked complete configuration is unavailable, curve mass needs
  reconciliation, complete installed envelope and exact California classification
  absent. Larger diameters do not establish a qualifying improvement.
- Current NAR/Tripoli rules were checked; their 125 g criterion is not confused
  with old 62.5 g guidance. California classification and ROC acceptance remain
  independent gates. Asked owner to confirm actual club/date; no messages sent
  to clubs, manufacturers or vendors.
- [Full shortlist](wo01-g-motor-shortlist.md), with matching-source gaps, direct
  stock observations, profile comparisons and realistic mass allowance. G25W
  quarantine / F25 rejection / 1.6 mm baseline preserved. No buy recommendation.
- `make check smoke` passes: 44 tests. F22 static reference and G summary studies
  run successfully. WO-01 open; no hardware change, procurement, paid compute,
  GitHub action or WO-02 start.

F22 record: `runs/wo01-motors-20261030T011052177790Z/record.json`.
G summary record: `runs/wo01-motors-20261030T012229578107Z/record.json`.
