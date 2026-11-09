# Current frontend release worklist

**Current desktop follow-up:** PR115 is merged at
`71a84ecde02c81d7ccfce98aa1d4bda82814d3c4` after corrected exact-head
workflow42563763036 and both required jobs succeeded. Original failed CI remains
recorded. Local follow-up adds lazy source-bound CAD downloads for all four
archived configurations, component/whole-assembly file scope, and a readable
source-identity notice for the unresolved Apogee/EasyMini record.311 local tests,
type/lint/format/build pass. [Archive integration](studies/frontend-archive-downloads-20261108/integration.md).
P38 verifies transverse cut/flip; P40 corrects P39's notice layout; P42 verifies
G80 assembly STEP/provenance with fresh matching bytes; P43 verifies actual
G54/finned-G12/finless-G12 models and file controls. No new CAD readback or physical
qualification is inferred. P44 accepted and completed one real Tiny CPU run,
`exp-c174705a75b8474290b523e8fb7c1267`; its45second trajectory is partial,
with landing unavailable. P45 compares it with the matching saved baseline, jumps
to apogee and downloads the actual CSV. The3,006 exported source samples preserve
117,234 raw values exactly; this is bounded playback data, not all9,000 source rows.
The metadata JSON download remains blocked: P46 automatic approval review rejected
changing Chrome’s persistent multiple-download permission before any action.
Explicit owner authorization for only http://127.0.0.1:5173, or owner action on the
prompt, is pending; no retry or workaround is permitted. Browser restoration was
not completed. [Run evidence](studies/frontend-desktop-experiment-20261108/source-verification.json). Inquiries UNSENT;
physical engineering and WO-03/04/05/flight gates remain unchanged.

**Desktop inspection increment (November 8):** Source-verified part/assembly GLB
and separate inspection STEP downloads, adjustable along/across section cuts,
selected-part nominal3D dimension guides, focused detail cases and a manufacturer
PCB mounting reference are implemented locally. Existing-source STEP export
reconstructs26 records/36solids; it does not add missing hardware or manufacturing
qualification. [Walkthrough](studies/frontend-desktop-detail-20261108/walkthrough.md)
· [Portable CAD/mesh pack](../output/rp1-desktop-inspection-pack/index.html).
P34 observed actual150degree section change; P35 observed ring isolation,31.9mm
guide and fresh registeredGLB/provenance download, with popover/label obstruction
preserved as historical failures. P36 verifies the corrected unobstructed ring
view plus actual STEP/provenance downloads; P37 verifies the manufacturer PCB
mounting table, JSON export and Escape/focus return. Fresh downloaded bytes/source
records independently match.301 localtests/type/lint/format/build pass;
four preserved unrelatedA2 tests remain outside publication. Native and physical
acceptance remain distinct. All inquiries UNSENT. PR114 is merged at
`c1777c39cbbc6816dcca4c32dd6b98b20242bfa0` after required workflow42560496864
and both jobs succeeded. Publish this capability through its own required checks.

**Owner priority — desktop engineering capability (November 8):**
Prioritize fully functional, interactive desktop rocket inspection, source-backed
CAD and intricate components/connections, graphics, experiments and replay.
Mobile/compact-layout polish and exact-pixel viewport campaigns are secondary and
must not delay those capabilities. Preserve completed layout evidence and open
checks; deferral is not a pass. Continue from current RP1/AD1 v2, keeping historical
CAD/run identities separate. Model actual documented detail where available;
label envelopes, concepts and undefined hardware rather than inventing precision.
[Saved direction and next capability](studies/frontend-desktop-detail-20261108/priority.md).
Existing engineering, purchase, physical/test and flight gates are unchanged.

PR113 is merged at `7a7ac044f251641839b7266891542d2c3dc50688` after both
required jobs and workflow42559067077 succeeded. The clock correction is source-verified;
P26 remains unqualified and no full native retake has occurred.

**Latest integrated frontend checkpoint (November 8):** PR112 is merged at
`cc98fb6e9424d99d62c8ceb41d68489da6f1031c` after exact-head web,
preliminary-model and overall workflow42550284458 succeeded. Replay controls
are above the scene; explicit Scene/Graphs/Events/Validity/Data & limits navigation
keeps the lower content reachable. P23 verifies Fixed pad and A-only labels;
P25 verifies keyboard section activation. [Whole-flight P26](studies/frontend-full-replay-qualification-20261108/browser.md)
is closed **unqualified**: one invalid startup interval and a finite-only timing
miss remain preserved. Its first overall closeout also exceeded360s by at least9.767s.
The bounded correction now anchors playback on the first RAF timestamp and retains
later invalid intervals; source tests pass, but this fix has not been qualified by
a new full native replay. [Clock decision](studies/frontend-replay-clock-anchor-20261108/integration.md).
No automatic retake, threshold relaxation or new optimizer/solver campaign follows.
G80 RP1/AD1/D1, G54 and G12 PID-to-RL are unchanged; all five inquiries UNSENT.
Engineering, physical/build, thermal/recovery/flutter, WO-10 and flight gates stay open.

**Current published source and follow-up:** PR111 merged at
`0eabac94604d1c2d711567076ced17b1860de4a5` after both required checks. The
[flow-controls follow-up](studies/frontend-replay-flow-controls-20261108/integration.md)
passes source checks and genuine P17 layout/input observations. P19/P20 direct
section destinations reach all plots/diagnostics/scene in available wide/tiled
layouts; P21 separately restores Fill. P22 fin breakdown is observed but co-motion
remains partial. See [section evidence](studies/frontend-replay-section-navigation-20261108/integration.md). Broader exact-size,
performance/data and engineering gates remain open. Supported fresh AX sync works;
no repeated Ready prerequisite or denied-method bypass. Five inquiries UNSENT.

**Autonomous frontend completion (November 8, after PR110):**
The owner requests continuation through the existing frontend checklist without
routine approval pauses. [Current packet](studies/frontend-completion-20261108/plan.md)
implements responsive focus restoration, consistent recorded-data exports and
comparison framing; local checks/build pass. P14/P15 stopped on changed owner
context/runtime guard, so new native interaction acceptance remains pending. PR110 is merged
at main `6a12c2b8b2a78d436cc24ecac7c05c80c5eb6ca7` after exact-head required checks;
its viewport helper is information-only. Native current-window evidence is scoped:
P13 observed2240×1109CSS/DPR2;100% zoom is owner-reported. Exact prescribed sizes,
representative performance and unavailable source-data branches remain open.
G80 RP1/AD1/D1 and G54/G12 PID-to-RL remain unchanged. All five inquiries are UNSENT;
no supplier, purchase, physical-test, firmware or flight authorization follows.

**Viewport-helper clarification:** [Current note](studies/frontend-viewport-clarity-20261108/report.md). The owner is not asked to chase pixel counts for ordinary use or unblocked development. The helper is information-only; its misleading target selector is removed. P13 observes actual2240×1109CSS and successful Hide, while100% zoom is owner-reported. Prescribed-size cases remain pending until a supported coordinated method is available; criteria are unchanged.

**Published baseline at the camera packet's intake:** merged PR108/main `47bc74a12b6d186bf8a9b68ef6e7ad45f044410a`; final head `8f6c02a65d5f0d58187c138d211c1e718ce80e63` passed both required jobs/workflow42489804785. PR105–107 precede it. G80 RP1/AD1 v2 and all archived identities remain separate. Preview publication never implies engineering/build/flight or full work-order acceptance.

| Outcome | Owner | Actual state / next evidence | Stop / dependency |
| --- | --- | --- | --- |
| Accurate task/acceptance state | Primary | Reconcile stale43-task ledger to28-task RV implementation map; old browser ownership block is resolved, denied viewport setup remains blocked. | Source/audit completion is scoped; no blanket browser pass. |
| Reliable experiment monitoring | Sol HIGH workflow agent | Implemented/source-tested paused monitoring and all accepted-member tracking. P3/P4 observed saved/batch metadata; acknowledged cancellation and worker-failure branches remain unverified. | No new simulation needed for source correction. Native behavior remains separate. |
| Fail-closed Analysis identity | Same workflow agent | Implemented/source-tested exact identity, manifests/cases and missingness. P3 observed failed scalars and unavailable fields; P4 observed corrected whole neutral RP1/groups. No compatible spatial fields. | Never fabricate spatial maps or turn failed/superseded fields accepted. |
| Bounded replay drawing | Sol HIGH replay agent | Saved-G54 before/after drawing comparison and one correction completed. Raw pose/metrics/export data, extrema, event neighbours and gaps are retained. P2 remains diagnostic-only, with failed mean target and offscreen scene. | Preserve raw data/poses/metrics/exports/gaps/events;10CPU/30wall diagnostic cap honored. One correction, then stop on regression or performance miss. |
| Contextual fin, PCB dialog, history/export | Sole native verifier | P1 completed326.625seconds below360; contextual returns, corrected PCB Escape, history and actual SVG export observed. Remaining branches stay scoped. | Stop guard/access/cap; no blocked DevTools/viewport retry. |
| Integrated saved-run/replay validation | Same verifier after code stable | P3 saved workflows and P4 correction/Tiny batch are complete with immutable records. Current-window P6 is separately bounded; exact-size matrix remains pending. | No automatic extension of completed packets. Native performance is distinct from source-work counts. |
| Focused publication | Primary | Relevant local checks plus required exact-head hosted jobs, then routine merge. Keep code lanes separable. | No extra review gate or forced bypass. |

## Release scope and remaining data

The required first release is read-only Design/Engineering, supported complete-configuration experiments, saved-run replay/comparison/export and honest recorded Analysis. Motor alternatives mean complete existing compatible configurations; fin construction preview is not live component replacement. True candidate regeneration/editing is FT043 later scope; Mission Control is optional. FT027 has an implemented and observed event-linked recovery schematic. The recorded monolithic 3D pose is unchanged; actual canopy, harness and separated-body dynamics remain unavailable.

Some compound checks still lack browser branches. Owner consent and native-window ownership are resolved; exact responsive sizing remains unavailable through the documented runtime. The earlier rejected DevTools route remains prohibited. Compatible current spatial results, finished hardware details and full RP1 flight mass/inertia/aerodynamics are source/engineering dependencies. A neutral/unavailable view is required now; it must not imply a fake zero, stress map or RP1 flight prediction.

## G80 engineering track

VP1 is complete for source/inquiry and lab-quotation review; frozen D1/AD1/FP1/FR1 remain untouched. All five drafts remain UNSENT, no actual send dates/replies or lab quote exist and no clock starts. A credible installed-fin decision still needs the staged evidence/method and later owner-authorized measurements. No purchases, lab/supplier contact, physical test, new construction variant or stopped numerical campaign follows from frontend autonomy.

[Packet budgets/evidence policy](studies/frontend-release-closure-20261108/ledger-reconciliation.md). Update this short list at each coherent outcome; historical logs are supporting evidence, not current engineering acceptance.

## Latest integrated outcome

PR105 and PR106 are merged after their exact-head required checks. New drawing/storyboard/visible controls/diagnostics and full Analysis canvas correction are implemented; source and native observations are linked in [integration](studies/frontend-replay-drawing-20261108/integration.md). P1/P3/P4 genuine functional paths are recorded; P2 is diagnostic-only, not60fps acceptance. The one new Tiny batch completed both9000-row members; actual cancellation is inconclusive and was not retried.

The exact-size matrix still needs actual1440×900/1280×720/900×720 CSS content areas, not merely target selection. The owner authorized agent resizing; one documented native Window→Zoom changed1965×1074 to2240×1109/DPR2, but no exact bounds entry was exposed. [Resize record](studies/frontend-owner-resize-20261108/browser.md). The rejected DevTools route is not retried. Independent current-window checks continue; no additional owner consent is needed. Engineering remains at the same VP1 evidence gate, with all five drafts UNSENT.

The additional ordinary-edge feasibility observation stopped after22.279s with no gesture: the cropped native view did not establish a usable edge or resizable mode. This does not prove resizing impossible. [Record](studies/frontend-window-resize-20261108/browser.md). Browser control is idle; the requested owner manual step remains pending.

## Current-window correction after PR106

P6 completed474.036s/480: unknownworkspace recovery, exact-source native history, actual nose/transformed-motor picks, Motor/Recovery staged displays, zero restoration, target dropdown and keyboard pan. It preserved a hidden invalid-part warning failure; fin/tab co-motion and other compound branches remain unexecuted. The final P6 enabled Frame control has an undiagnosed selection-scope caveat.

One bounded correction moves the warning outside collapsed source details and adds **Clear invalid part link**, using the existing exact-source URL builder. P7 completed97.282s/150: stale spec and missing ID show the warning without disclosure, Clear restores the exact source/no part, valid nose and fin_set selection works, and a fresh wholeRP1route ends26/26 with Frame disabled. This does not retrospectively diagnose P6. Local236tests, type/lint/build pass; four preserved/unpublished A2 cases remain outside publication. That correction is merged as PR107 after required exact-head checks. [P6](studies/frontend-current-functional-20261108/browser.md) · [P7](studies/frontend-part-link-recovery-20261108/browser.md).

## Scene and telemetry follow-up

One source layout packet and one clock-label correction keep a single scene mounted, put core playback/time controls beside four linked plots at a sufficiently wide centre, and keep details reachable below. No model, raw data, callback, pose, numerical time or source-identity change. [Integration](studies/frontend-replay-layout-20261108/integration.md) records the bounded scope and exact pre/post preservation check.

P8 completed452.815s/480: wide scene/controls/fourplots readable; ordinary native Left/Fill measured2240→1120→2240CSS and retained time, channel, camera mode, A/B and range. Stacking was seen; all lower plot reachability and numeric free-camera pose remain unverified. P8's incorrect T+ label under aligned clock remains historical. One copy correction now says Time from burnout instead.

P9 is partial: both saved G80/G54 actors valid at100s; the native input path never established125s, so no outside-window/clamping verdict follows. Corrected relative clock text is confirmed in live AX and visible core, not a full HUD image. Final safe restore/capture ended263.484s against260, a3.484s budget overrun with no extension/pass claim. [P8](studies/frontend-replay-layout-20261108/browser.md) · [P9](studies/frontend-replay-unequal-windows-20261108/browser.md). No Play/nativefull/new run/FPS attempt occurred.

The owner subsequently entered125 and P10 verified the applied cursor/readouts; CUA is idle with that comparison preserved for the owner. No further number-input, resize or performance retry is implied. Exact1440/1280/900 sizes, full narrow scroll, numeric camera pose and performance remain pending; inquiries stay UNSENT and all physical gates open. Local237tests/type/lint/format/build pass at the final source. Four unpublished A2 cases remain excluded;233are in publication scope. The new focused PR must pass required hosted checks at its exact head.

## Owner-assisted125-second result

The owner entered125 through the ordinary interface. P10 completed50.664s/90 with no input/retry or model execution: applied absolute125 remains125, G80 A is Outside its116.029-second window with all four A readouts unavailable, and G54 B is Inside its132.856-second window with recorded values near125.014. [P10 evidence](studies/frontend-replay-manual-boundary-20261108/browser.md). This closes that clock/scalar data-window branch, not independent WebGL proof of A-body withholding or B-body visibility; the scene image shows trails without an identifiable current body. P9's failed native entry and3.484s overrun remain historical.

The comparison is left paused at125 for owner inspection. No further owner action is required for this increment's publication. Exact-size matrix, full narrow-scroll coverage, numeric free-camera-pose retention, acknowledged cancellation and representative performance remain pending under their own recorded gates. No further automatic retry follows from this result.

## Final camera-target increment

[Camera integration](studies/frontend-replay-follow-20261108/integration.md) uses available recorded A/B positions for the view only. Auto follows A then B; explicit A/B holds with a reason rather than substituting, and Free/Pad remain independent. Fit is honestly A-only. No recorded pose, time or flight calculation changed.

P11 first proved visible B fallback at125 but did not establish popup choices and overran150s by2.599s. One correction exposes direct camera buttons. P12 passed A-held/B-follow/Free/Auto with actual B-body images, unchanged125/readouts and one click each. It ended48.382s within a90s native cutoff/120s overall cap with per-call reserve checks. Fixed pad and missing-comparison disabled state remain unexecuted in the browser. [P12](studies/frontend-replay-camera-buttons-20261108/browser.md). Original failures/overruns remain immutable.

Final local241tests/type/lint/format/build pass; four unpublished A2 tests remain outside the237-case publication scope. Required exact-head hosted checks precede merge. The owner comparison is preserved paused at125, Auto B. No more owner input is needed to publish this increment; broader exact-size/data/performance/physical acceptance remains open.
