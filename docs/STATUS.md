Warning: truncated output (original token count: 17839)
Total output lines: 1047

# Status

Updated: 2026-11-01 (run IDs use UTC)

## Current work order

**Delivery priority — ADR-0011:** one complete conventional fixed-motor G80
engineering package first. Substantial custom construction, maximum practical
performance within the no-HPR scope and committed PID-to-RL development remain
core. G54 upgrade and G12 controls/finless evidence stay separate and committed.
G80-specific readiness does not complete aggregate WO-03 or clear other modes.
See [G80 intake](wo03-g80-package-intake.md) and
[fit candidate](wo03-g80-fit-candidate.md). The exact current G80 reproduces the
0.02093 mm mount/shell minimum against 0.1 mm; one 32.2 mm mount-radius proposal
passes the in-domain stack at 0.12102 mm and remains a separate engineering
candidate pending its complete load/heat/recovery/flutter integration.

**Current capture comparison — both specified envelopes stopped at preflight:**
B moves reverse load into an unreinforced plywood rail: projected bearing12.50MPa
exceeds the generic10MPa screen, and its specified12mm pin cannot engage both
fork lugs. C intersects the modular coupler; trimming its section to fit leaves
ideal recovery stress29.87MPa above the estimated25MPa hot G11 screen. Defined
stock ledgers include pins/washers/splices/rings and separate full50g growth,
but complete installed mass remains unavailable. No CAD/FEA is admitted for
either unchanged proposal. See the [comparison and decision](wo03-g80-capture-decision.md).

The failed bond-only bridge remains visible: fixed-support DF3 mean shear
3.965/4.007MPa exceeds the estimated1MPa hot-bond screen; force/work consistency
does not establish installed strength. No strength, thermal or complete-package
acceptance requirement closes here. The one next direction is a **short captured
G11 aft subframe connected to the aramid backbone**, with separate verified
body/fin/motor restraints, not a third executed candidate. G80 first; G54/G12
remain separate. Working vehicle, preview assets and earlier flight predictions
are unchanged. Native budgets were not spent; no failed path was rerun.

The two new mesh-only pilots pass their input guards but do not establish
uniform regional refinement; no new structural solver run followed them. The
known-case stress-output path passed separately. Existing numerical results
remain useful diagnostics, while the physical G80 package and WO-03 stay open.

**Actual bridge numerical result:** two saved Elmer coarse fields pass the
unchanged strict force and reciprocal-work comparisons. Maximum displacement
is0.381 mm distributed /1.157 mm single-washer; no stress, fit or convergence
acceptance is claimed. Original output-discovery and terminal RSS-supervisor
stops are preserved separately from read-only field recovery; no native case
was repeated. See [results and next gate](wo03-g80-bridge-elmer-results.md).
The complete G80 package, installed fins, recovery and thermal acceptance remain
open; working vehicle and prior flight predictions are unchanged.

**Early preview publication:** [PR #36](https://github.com/kudratsingh/rocket-twin/pull/36)
is merged after both required jobs passed in run41301490761. It adds the
separate72-part archived G80 retention inspector without attaching its geometry
to active-design experiments. The prepared snapshot is local and hash checked.
The host API needs to load the updated code; the owner restart question remains
pending. New-candidate browser verification/screenshot is unavailable because
automatic approval review rejected the designated frontend agent's computer-use
call for an agent-ownership prerequisite. The designated agent reconfirmed
its assignment in an ownership-only handoff; runtime ownership remains unresolved
and no supported in-session reset was documented. No new computer-use call or
bypass was attempted. See
[preview scope and commands](wo04-g80-retention-snapshot-preview.md).

**Structural-method decision:** the two small layered-bar Elmer cases now
individually pass all-node displacement and the unchanged strict force gate.
The original log-classification stop remains preserved; the EQUAL result was
assessed from saved output, and only the remaining SINGLE case was run. B1
output precision remained insufficient and B2 failed its known displacement.
The source-identical bridge conversion now passes its input checks after
separating mesh-volume preservation from CAD approximation; direct nodal-RHS
semantics also pass the separately admitted matching known-answer case. Use this bounded path; no real
bridge strength or stiffness acceptance follows. Thermal qualification remains
separately unresolved. See [decision](wo03-structural-solver-decision.md).

**Latest integrated G80 candidate, still unadopted:** the 72-part keeper/bridge
package now has a complete component ledger, actual CAD-derived CG/full tensor
and same-identity static/flight results. Loaded mass772.982g plus separate50g
gives822.982g; growth CG829.167mm, loaded/burnout margin1.1663/1.5483cal.
All four guide screens pass, minimum16.848m/s versus15 on the assumed1.5m
guide. Nominal apogee620.610m versus RocketPy620.650m passes the5% comparison.
All trajectories reach modeled ground; recovery sizing remains open, along
with actual bridge equilibrium, hot joints, installed fin/root/flutter,
thermal acceptance and the three recovery overlaps. The
[staged report](wo03-g80-staged-retention-results.md) and
[closure table](wo03-g80-current-closure.md) keep these design failures separate
from later physical qualification. Active vehicle/preview assets are unchanged.

[PR #33](https://github.com/kudratsingh/rocket-twin/pull/33) publishes the
isolated72-part package. Both required jobs passed in run41294021497 before
merge; those repository checks do not close the recorded engineering findings.

**Recovery correction study, not adopted:** one larger commercial canopy
candidate now passes all five modeled6m/s vertical-descent screens, including
an illustrative20% lower drag-area sensitivity. The complete package retains
full50g growth and a separate5g line/connector allocation:844.582g, growth
loaded margin1.419cal; minimum guide16.366m/s. Supplier drag and packed size
are unverified, and wind impact diagnostics remain adverse. A metadata-only
copy corrects the allocation's missing build entry with bitwise identical
simulator inputs; the original failed check remains preserved. Stage3 retained
metrics/landing samples but not full replay telemetry. See
[results](wo03-g80-canopy-stage3-results.md).

The [recovery-path audit](wo03-g80-recovery-path-intake.md) and
[plain-body axial screen](wo03-g80-recovery-axial-screen.md) identify a further
design blocker: the paper upper tube alone crosses the selected cut, and the
existing off-nominal opening demands exceed its estimated strength screen.
A local forward spreader alone does not bypass that serial path. Lightweight
continuous-tether versus body-reinforcement alternatives are being assessed;
no connection capacity, physical failure prediction or adoption is claimed.

[PR #34](https://github.com/kudratsingh/rocket-twin/pull/34) publishes those
canopy and recovery-path findings. Both required jobs passed in run41294969753
before merge; the physical recovery system remains unqualified.

**Backbone layout prerequisite:** the source-pinned straight-route study clears
both nominal manufactured-solid envelopes but leaves only0.45mm inflated
coupler clearance. The selected60° reference avoids the other route's unresolved
adhesive-budget envelope. Forward/nose/payload and independent aft attachments,
bends, slack, pressure isolation, deployment and service remain open; no
installable tether or complete recovery result is claimed. See
[route evidence](wo03-g80-backbone-route.md). Requirements/interfaces/FMEA
retain their stable IDs and open statuses, with the new isolated G80 evidence
linked separately from active/G54/G12 acceptance.

**Controlled thermal-tool decision, complete:** the three classic Elmer A
cases agree with the preserved vectorized fields within 5.4e-12 K. Both fail
the unchanged exact-field check; switching implementations is rejected as a
correction. Conductive-heat reference errors pass separately, while local,
Robin and algebraic heat accounting remain unavailable. The independent
read-only reference/coordinate audit does not identify the cause. The
[completed comparison](wo03-elmer-classic-comparison.md) and
[decision](wo03-elmer-campaign-decision.md) leave actual geometry unqualified;
no further solve, new custom heat method, changed limit or baffle acceptance
follows. The launch-cap stop and its one declared replan remain preserved.

[PR #32](https://github.com/kudratsingh/rocket-twin/pull/32) publishes that
closed comparison and audit. Both required jobs passed in run41293406423
before merge. Actual-baffle qualification remains open.

**Latest bridge outcome — numerical acceptance failed:** a geometry-derived
48/24 edge resolution meets the unchanged washer-area and mesh ceilings:
42,850 nodes/22,495 tets, area error+0.000049781mm² versus0.0002mm².
CalculiX completes both static steps, but support force balance fails by
104.697N and22.093N; these are far beyond print precision. The
[final diagnostic](wo03-g80-final-coarse-diagnostic.md) preserves raw output
as **unvalidated**, with no strength, stiffness or installed-load-path pass.
Read-only checks confirm complete reaction rows, matched quadratic interface
faces, zero support displacement and positive sampled Jacobians; cause remains
unidentified. No more actual3D mesh/solver/edge variants are selected for this
packet. The proposed multi-material/multi-support known-case checks are now
recorded below with their print-precision limits. Conditional hand estimates
cannot close peel, keeper load sharing or material qualification.

The subsequent [read-only reciprocal-work audit](wo03-g80-bridge-reciprocity-audit.md)
also finds32.229N·mm disagreement versus a3.253e-6N·mm print bound, using
complete native steps at times1/2. This strengthens the response-validation
stop without identifying its cause. The
[backend/output assessment](wo03-ccx-backend-output-assessment.md) distinguishes
documented alternatives from verified installed behavior. A separate small
known-case binary/backend diagnostic is preparation only; no new native case
or actual-bridge retry is authorized by the research.

**Known mechanical outputs:** [A/B flat-bar diagnostics](wo03-ccx-reaction-fixture.md)
and the [Poisson-coupled D case](wo03-ccx-poisson-diagnostic.md) complete with
printed displacement agreement and near-zero observed global force residuals.
The strict1e-5N force certificates remain unavailable because conservative
native print-rounding bounds are larger; none is a strict pass. C is unrun
following input-moment failure. The original three native slots are exhausted,
with no actual bridge retry or fourth fixture selected. These cases do not
reproduce or explain the bridge's104.7N deficit. The one-MPC line is explicitly
an estimated upper bound; matrix equation counts match unique SPC arithmetic,
so it does not establish an undocumented constraint.

[PR #31](https://github.com/kudratsingh/rocket-twin/pull/31) publishes those
known-case diagnostics and input-evidence priorities. It merged after both
required jobs passed in run41292058740; successful repository checks do not
turn the unavailable strict certificates or failed actual bridge into passes.

**Method evidence remains scoped:** the [geometry-only stage](wo03-g80-bridge-boundary-case.md)
passes source Circle identification;96/32 then exceeds the node cap. The
[noncancelling arc-area budget](wo03-g80-washer-area-budget.md) justifies48/24
without relaxing criteria and fits the existing ceilings. That closes input
preparation and bounded calculation completion, not output accuracy.

**G80 recovery/fin decisions:** the [same-candidate fin-load intake](wo03-g80-fin-loads.md)
separates powered, coast and recovery phases from saved180s telemetry; large
angles remain unsupported and installed strength/flutter open. The
[canopy source screen](wo03-g80-recovery-canopy-sources.md) identifies a modest
mass-increase sizing candidate but adopts no hardware or packing assumptions.

**Keeper/service continuation:** the unchanged proposed parts now have completed
nominal 5 mm-spaced pre-shell support insertion and aft cap/motor removal samples,
with no sampled blockers. [Results](wo03-g80-keeper-service.md) and
[rotation bound](wo03-g80-nut-rotation-bound.md) retain the earlier inconclusive
5° diagnostic; a source-specific fixed-axis ±15° barrier is separately calculated
and observed. This is not torque, tolerance, all-path capture or strength
qualification. Separate STEP parts and component masses are available: keeper
15.410 g, bridge10.177 g, modified plywood/guides40.448 g. The [mass audit](wo03-g80-retention-mass-audit.md) distinguishes the old 7 g
hardware lump, supplier fasteners and integral keeper pads. The subsequent
72-part staged integration above resolves that bookkeeping into a full
mass/CG/inertia model and its own flight results; actual hardware qualification,
locking and bond properties remain unresolved. Frozen52-part flight predictions
are not assigned to the changed parts.

**Published native bridge evidence:** [PR #30](https://github.com/kudratsingh/rocket-twin/pull/30)
is merged after both required jobs passed (run41287248347). Those jobs preserve
the engineering equilibrium failure. Subsequent small-fixture evidence is a
separate increment and does not retroactively accept the bridge.

**Published preparation:** [PR #29](https://github.com/kudratsingh/rocket-twin/pull/29)
is merged after both required jobs passed (run41285473769). It contains the
known-boundary helper, fin-load/source intake and process-exit race correction.
The actual-boundary/native-output failure above is a subsequent separate
increment, with all expanded acceptance and release gates retained.

**Published guarded evidence:** [PR #28](https://github.com/kudratsingh/rocket-twin/pull/28)
is merged after both required jobs passed (run41284107292). It publishes the
completed frozen-package recovery horizon and stopped structural inputs.
Subsequent independent area/fin-source studies and a narrow process-exit
[race correction](wo03-owned-process-guard.md) are separately recorded.

**Published retention/service milestone:** [PR #27](https://github.com/kudratsingh/rocket-twin/pull/27)
is merged after both required jobs passed (replacement run41282972324). Its
nominal keeper/service and structural prerequisites preserve open acceptance.
The subsequent guarded bridge attempts and recovery-horizon follow-up are
separate evidence, not retroactive results of that PR.

**Published G80 milestone:** [PR #26](https://github.com/kudratsingh/rocket-twin/pull/26)
is merged after both required jobs passed (run 41278070445). The same-package
mass/static/guide/flight evidence and preview handoff are published; expanded
engineering acceptance remains open.

**Latest retention study, separate from the 52-part package:** sourced M3×35
screw/nut/9 mm washer candidates replace the placeholder hardware dimensions.
The first nominal check stopped on 1.098419 mm³ washer/mount overlaps; one
recorded input-layout replan clears screened overlaps with R20.7 mm relief.
Three washer/bridge probes are 54.538 mm². No tolerance minimum or capture pass:
washer OD tolerance is missing, all three sampled radial nut/washer removal
paths meet the installed shell, and no keeper was modeled. Actual replacement
hardware mass increment is unresolved. [Executed evidence](wo03-g80-retention-geometry.md).
The [4 mm G11 captive keeper](wo03-g80-captive-retention-plan.md) now has the
separately recorded nominal service samples above; tolerance, strength and
complete mass reconciliation remain open.
The earlier two-attempt packet is stopped; a different keeper function needs
its own declared geometry/assembly check, not a blind third layout retry.

**Completed recovery horizon, frozen G80 proposal:** all three 52-part cases now
reach modeled ground by 128.370 s in the bounded 180 s run. The [report](wo03-g80-recovery-horizon.md)
closes only the old 45 s incompleteness: predicted ground speeds are 5.966,
6.180 and 6.178 m/s, so growth cases exceed the preliminary 6 m/s screen.
There is no independent recovery-flight comparison or physical qualification.
The new retention/keeper geometry is absent from these results; its complete
replacement ledger and revalidation remain open.

**Latest integrated G80 proposal (52 parts, not active):** the selected mount
and recovery packaging now share one normally validated resolved identity
`62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009`.
[CAD and mass reconciliation](wo03-g80-integrated-candidate.md) give 748.569 g
nominal / 798.569 g with full 50 g aft allowance, growth-case CG 818.503 mm and
1.3278-calibre margin. Independent preliminary static comparison passes.
[Affected same-package flight](wo03-g80-integrated-flight.md) gives nominal
631.216 m versus RocketPy 631.249 m; conservative full-growth guide departure
16.955 m/s versus 15 m/s. All three 45 s recoveries remain incomplete.
Separate STEP/GLB exports are available; active design/preview assets stay
unchanged. Three explicit positive contact-envelope overlaps still require
resolution; no nominal screen is presented as physical fit approval. The
[closure table](wo03-g80-current-closure.md) distinguishes these open design
items from later physical qualification. G80 recovery switch research now
proposes a DC-rated C&K candidate; it has not replaced the SWA1 envelope in
this 52-part package.

**Earlier mount-only G80 checks (43 parts):** the same 43-part proposal, with its conservative
4.620 g incremental adhesive budget, is 743.804 g nominal / 793.804 g including
full 50 g aft growth. Loaded growth-case CG is 820.927 mm and passive margin
1.2911 calibres; this has not replaced the active 739.462 g design. The
[nominal flight comparison](wo03-g80-candidate-flight.md) gives 633.432 m JAX
versus 633.392 m RocketPy, within the 5% apogee/time gates. The conservative
low-thrust/high-drag/full-growth case leaves the configured 1.5 m guide at
17.068 m/s versus 15 m/s. All three 45 s trajectories have incomplete recovery.
[Actual mount areas](wo03-g80-mount-loadpath.md) correct the last-ring bond
proxy by -10.85%. [Accelerating cuts](wo03-g80-axial-cuts.md) and
[saved-flight load bounds](wo03-g80-axial-flight-bounds.md) give a maximum
sampled uniform DF3 stress of 1.643 MPa at the forward shell-only cut against
the estimated 2 MPa screen. This scoped result excludes local shell/joint,
buckling, hot-material qualification and other winds; aft parallel-path loads
remain unresolved. The [hardware proposal](wo03-g80-recovery-hardware.md)
retains separate independent recovery and unresolved switch/connector details.
Complete recovery integration, installed fin/root/flutter, actual bonds and
thermal acceptance remain design blockers, not physical-test-only deferrals.

**Next G80 mechanical correction:** the [manufacturing definition](wo03-g80-mount-fabrication.md)
identifies a real unclosed retainer-block butt joint hidden by fused plywood CAD.
One proposed G11 bridge with rail tabs and through-bolt nut/washer capture is
selected for the next bounded geometry/load check. It is not in the 52-part
proposal; longer hardware, ring relief, bridge stiffness, nut access and added
mass remain unverified. No butt-joint tensile-glue strength is credited.

**Thermal-tool campaign is complete, not qualified for actual-baffle acceptance.**
[PR #25](https://github.com/kudratsingh/rocket-twin/pull/25) is merged after both
required hosted jobs passed (run 41276622684).
The isolated Elmer setup succeeded within the 600 s limit (489.423 s including
107.013 s owner download). The declared nine A/B/B_strong results completed;
A-2 was reused after a documented output-location-only replan, not rerun.
All A refinements miss the unchanged 1e-7 K criterion; B/B_strong stay within
verified fixture envelopes but complete conservation and method evidence are
missing. [Comparison](wo03-elmer-thermal-comparison.md),
[closed-campaign decision](wo03-elmer-campaign-decision.md).
No more open-ended custom heat solver or actual geometry run is selected.

**Current preview check (2026-11-01):** the designated Chrome agent refreshed
the existing tab and confirmed the42-part G80 inspector,739.46g mass and real
3D rocket at http://127.0.0.1:5173. The shell could not connect/rebind local
ports, but browser-to-host access worked. The requested owner restart is
unnecessary; no owner action is pending for this check. No full visual campaign
was repeated; earlier four-configuration verification retains its date.

**Usable preview:** the owner restarted `make preview`; the designated Chrome
agent verified all four configurations, real 3D inspection, saved G80 replay
and comparison with differing winds visible. The earlier API outage recovered;
its cause remains unknown. The [delivery walkthrough](wo04-preview-delivery.md)
gives startup and limits. URL: http://127.0.0.1:5173. Incompatible/failed/missing
Analysis remains unavailable and does not block the basic preview. Full
WO-04/05 and physical/paid/WO-10/flight gates remain unchanged.

**Owner-resumed session (2026-10-31 Pacific):** the previous timed session was
saved and stopped. The owner subsequently resumed WO-03 and the limited early
frontend work; the old deadline no longer pauses this session. WO-03 remains
open, with no new acceptance or release authorization.

**Latest installed-root correction:** [actual face common areas](wo03-root-contact-faces.md)
show that the nominal body slots leave only 281.731 of 355.097 mm² shell-backed
area per historical G12 foot. Analytic clipping independently matches that area.
The [corrected spring sensitivity](wo03-clipped-foot-contact.md), with unchanged
rigid supports and tab-column proxy, raises smooth DF3 foot-normal demand from
2.357 to 2.648 MPa for the 0.1 mm bond. Foot/tab service force becomes
50.404/7.225 N. This supersedes the full-foot assumption for this sensitivity;
it establishes no installed strength or conservative full-joint bound. Hot
normal/peel capacity, actual support compliance, edge stresses and flutter remain
open. Earlier numerical/physical results keep their original source identities.

[PR #22](https://github.com/kudratsingh/rocket-twin/pull/22) is merged after
both [required hosted jobs](https://github.com/kudratsingh/rocket-twin/actions/runs/41260368011)
passed. It publishes the previous source and thermal-output prerequisites.
The new root-contact packets are separately recorded in
`runs/wo03-root-contact-correction-20261101T012547878277Z/record.json`.

**Latest bounded work:** the [G12 source refreeze](wo03-refreeze-g12-root.md)
validates the historical 77-part reconciled identity and preserves the original
layered-fin and rounded-frame STEP files. This closes a source-loading
prerequisite, not installed strength, clearance, flutter or a mass saving.
The [proposed installed-root case](wo03-installed-root-next-case.md) records
the remaining geometry/material prerequisites; it has not been executed.

The [CalculiX output probe](wo03-ccx-output-probe.md) confirms float32 NT/RFL
output for installed A-2. Its first reader-format failure stopped the packet;
A-4/A-8 were not run. The preserved A-2 bytes were decoded read-only, and a
truncated-record self-check improved the reader. Output precision still cannot
establish the unchanged 1e-7 K / 1e-10 W checks. Neither thermal tool qualifies
an actual-baffle attempt; the required matrix and 45°C screen remain unchanged.

The [solid map](wo03-fin-material-map.md) now uniquely matches all 60 historical
G12 fin solids to the AST-preserved material recipe. Contact-face mapping and
installed strength/stiffness/flutter remain ope…5839 tokens truncated…#1.
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
