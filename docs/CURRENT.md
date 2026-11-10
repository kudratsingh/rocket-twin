# Current engineering and inspection checkpoint

**Local CAD datum inspection:** Parts bank → Template recipes now links the two
existing nominal tube/ring solids to five selectable analytic guides: axis,
bore, outside cylinder and both annular end planes. Bore selection ghosts only
the displayed solid; camera and exported bytes remain independent. Exact local
CAD +Z maps to viewer −Y. These are parameter-derived datums, not kernel face
IDs or accepted mating interfaces. The tube remains 31.369 mm OD / 29.169 mm bore / 165 mm long;
stock/motor fit is unresolved. [Scope, use and limits](studies/frontend-reference-parts-20261109/implementation.md).
Combined checks pass: 153 Python tests, one previously executed benchmark
skipped, and 411 published web cases (415 local includes four unpublished A2
cases), plus type/build/lint/format and Python static checks. P87 reached the ring view and datum controls in native AX, but the 80 s input
cap stopped before a datum click; no screenshot/ghost/camera pass. Full builder,
physical and flight acceptance remain open. PR128 source-intent preview is
merged at `95fddb209197c6a412900c903b22061925f57172`. Inquiries remain UNSENT.

**Unsaved source-intent preview:** Saved drafts now offers an explicit planning
preview for marking and restoring source exclusion intents. P85 observed prepare0
and fin_set exclusion1; P86 observed Restore0 and original opaque identity. All55
source rows, saved3 and six saved files remain unchanged. The UI retains the
unresolved function/evidence; mass credit/effective inventory/CG/inertia stay null,
and every candidate/simulation/engineering/flight flag stays false.
[Scope and actual evidence](studies/frontend-draft-composition-20261109/integration.md).
This is not full Add/Replace/Connect or a physical fin correction. Owner confirmed
`make preview-dev`; the new API route works, with source-only reload configured.
The reload cycle itself is not separately observed. Inquiries remain UNSENT.

**Live metadata drafts and review export:** After the owner's normal-host
restart, P81–P83 verified one source fork, metadata save, exact reload/history,
actual reviewJSON download and stale-write recovery in the designated Chrome
window. Independent persisted-byte checks verify all three revision hashes,
unchanged source/55 records and no fourth revision from the rejected stale Save.
The 772,101-byte review file matches saved revision2; no geometry assets or
import/restore/candidate/simulation approval is implied. One clearly labelled
validation draft remains, at revision3. [Actual lifecycle and readback](studies/frontend-draft-foundation-20261109/browser-lifecycle.md).
Blank drafts, Add/Replace/Connect, candidate resolution and undo/revert remain
open; all physical/flight gates and UNSENT inquiries stay unchanged.

**RP1 assembly and service walkthrough:** Engineering now has a separate
**RP1 assembly & service** topic with seven source-linked concept steps and
selectable part groups. App supplies the already verified current inspection;
all 55 identities and exact source revisions are checked. No CAD/physics job,
physical sequence completion or engineering adoption occurs. P79 reached step 7;
controls, critical warnings and upper diagram are visible. Lower groups/details
are AX-only and full scrolling/part-return legibility remains partial. Native
33.868 s / 40 s and evidence 65.650 s / 120 s met this limited packet's bounds.
[Integrated path and evidence](studies/frontend-rp1-assembly-20261109/integration.md).
The buried recovery anchor's destructive replacement limit and failed/unknown
fin/cord/joint evidence stay explicit. All build/thermal/recovery/flutter/flight
gates remain open; inquiries UNSENT. Draft/export UI PR125 is merged at
`41cd32dcae03abb5ae090fcf91dfaf827a17317f` after exact-head required checks.
Owner restart is confirmed; P81–P83 now cover the bounded metadata lifecycle.

**Current source-workbench increment:** **Parts bank → Saved drafts** now
provides explicit RP1 forks, metadata saves and immutable history, preserving all 55
source accounting records. Stale writes preserve unsaved text. No blank rocket,
Add/Replace/Connect, candidate resolver or simulation admission is delivered.
[Use and limits](studies/frontend-draft-foundation-20261109/frontend.md).
The backend is merged in [PR124](https://github.com/kudratsingh/rocket-twin/pull/124)
at `7c588d87ca30e7140998d9c6c0e6a5b4dc995a64` after exact-head web/model checks.
Owner restart loaded the live draft routes. P81–P83 verify the bounded metadata
lifecycle; the earlier isolated bind denial stays historical with no bypass.
Only the new, clearly labelled validation draft was changed.
P76's blank-app failure is preserved. After the one scoped containment correction,
P77's single ordinary reload displayed the actual library and explicit stale-API404
restart explanation. No fork/save, boundary-fallback capture, Return click or
flight-computer branch was exercised. Estimated evidence closeout203.462s exceeded
180s; no whole-packet timing pass. [Native record](studies/frontend-draft-foundation-20261109/browser-library.md).

Engineering's **Download source SVG** exported an actual 47,779-byte G12 system
sheet with source identity and no external payloads. Its XML and established
offline rendering/readability pass. P74 readiness and P75 focus stops leave
standalone Chrome reopening unexecuted; no further artifact retry is admitted.
[Portable receipt and evidence](studies/frontend-system-map-20261109/export.md).
The flight-computer details explicitly retain a generic61 × 18 × 6 mm / 12 g estimate:
Teensy 4.1 is an unadopted reference, with exact product/mounting/height unavailable.
Current RP1/D1, all physical/flight gates and UNSENT inquiries remain unchanged.

**Autonomous source workbench continuation (November9):** The owner authorizes
continuing the existing plan while away. Named source recipes/features are added
to Parts bank, with full55-record dispositions and explicit reuse/identity limits.
Engineering gains a source-linked physics/instrumentation/recovery map and a
separate planned G12 PID/RL feedback view. Current RP1, D1 and all physical gates
remain unchanged; inquiries UNSENT. [Bounded packet and paths](studies/frontend-autonomous-20261109/integration.md).
Code/source checks and designated-window observations are tracked separately;
this does not close the full workbench, engineering or flight milestones.


**Control organization follow-up:** The owner requested the crowded control strip
be refined. View/Inspect/Source/Alternatives and Mouse/Frame/Zoom/Display/Views
now use labeled, wrapping normal-flow groups. Existing geometry, callbacks,
read-only evidence and fin-joint camera retention remain unchanged.
P69–P70 native checks verify group/menu reachability, display/section entries,
sidebar states and a visible whole model; numeric entry and full responsive/
field-legibility coverage remain outside this scoped claim.
[Bounded scope and verification](studies/frontend-control-layout-20261109/integration.md). Full work-order and physical/flight gates
remain open; all five inquiries are UNSENT.

**Current focused delivery — RP1 fin attachment inspector:** One source-bound,
read-only joint view reuses the registered nine-part/18-solid motor/fin/ring STEP,
adds two actual CAD-derived capped sections, clickable dimensions and exact
Engineering/Design return state. Frozen AD1 v2, failed fin findings and unknown
installed-joint behavior remain separate. [Scope and user path](studies/frontend-fin-attachment-20261109/integration.md).
Actual joint download/readback passes. P64/P65/P66 native evidence covers cuts,
dimensions, orbit/zoom/pan and root-drawing return. P68 verifies source-bound load-path/joint return and the settled original
main camera, mode and selection. The actual Design scene stays mounted;
[PR121](https://github.com/kudratsingh/rocket-twin/pull/121) stays focused on this
slice. All physical/engineering gates stay open; inquiries UNSENT.


**First v2 implementation — P1 source bank:** The full plan is merged in PR119
at `a896645a2325b470e8bd3c0054d9dc1ec36db66a`, after head41082ab… and required
workflow42594694204 passed. The first bank represents55 source definitions and55
installed occurrences, with source/price/identity conflicts and installed-reference
CAD frames explicit. P61 observed source-snapshot catalog/search/exactpart return;
P62 verified visible conflict warnings and new-part scroll reset. New live API
routes pass in-process tests; the existing host used an explicitly labeled prepared
snapshot after404. Full builder Add/Replace/Connect and template/interface admission
are later tasks. [Implementation and evidence](studies/frontend-parts-bank-20261109/integration.md). All engineering/physical
gates stay open and inquiries UNSENT. Existing archive audit/assets remain frozen;
a separately pinned equivalence record admits only the two added API routes.


**Current owner direction — full design workbench v2 (November 9):** Complete
the full phased plan, then implement detailed CAD/inspection and engineering
diagrams, a reusable source-owned parts bank, separate virtual rocket drafts and
consistent alternative checks/experiments. [Full plan](frontend-design-workbench-v2/README.md) defines ten phases,
46 tasks and36 new acceptance scenarios. ADR-0017 explicitly permits validated
draft composition while frozen RP1 and existing engineering/physical/flight gates
remain unchanged. Start P1's read-only current-source parts bank; preserve current
inspector/experiments/replay and all legacy acceptance states. Five inquiries stay
UNSENT. Sol HIGH lanes have separate ownership; primary integrates; only the
existing designated browser owner uses the permitted Chrome window.

PR118 is merged at `38e70be0d2df59c81e2d6cb52b97d4b58444496f` after exact final
head `515cecd1378826c9fd852257fd4e9be7da27a18a`, workflow42587975052 and both
required jobs passed. PCB source detail and18 mechanical pieces are the baseline;
half-shell edge proof and other unexercised controls remain partial. This is a
frontend checkpoint, not installed-fin, material, thermal or flight acceptance.


**Active owner direction — component depth:** The owner wants intricate parts and
construction detail beyond block envelopes. Implement source-based PCB structure
and fin/root/motor construction close-ups linked to existing part IDs, with local
selection/layers/camera controls. The frozen physical vehicle, mass/inertia and
existing preview remain unchanged; unsupported details remain unavailable.
[Current bounded packet](studies/frontend-component-depth-20261108/plan.md).
Code/source checks pass. P57 verifies the corrected PCB graphic; P59 verifies
mechanical opening, tab selection and separated-piece framing. Half-shell edge
visibility and unexercised controls remain partial. See the component-depth
integration record; no physical design or engineering gate changed.


**Published desktop checkpoint:** PR116 merged at`49459f36426a8a17108b65f904025abf7fc30735`
after exact finalhead`c1adab87bcc83f826739b5ac3d5dc735f0aa693c`, workflow42573819956
and both required jobs succeeded. Source snapshots matched118 remote blobs;
repository is public. [Code and browser closeout](studies/frontend-desktop-evidence-closeout-20261108.md).
P54 verifies the existing explicit detail/isolation action exposes the ring bore,
notch and seam; Frame-only body occlusion remains a separate limitation. P55
verifies representative slash/search/Editable-Escape-preserve/global-Escape-clear,
with no full keyboard/modal matrix claim. Browser is idle on wholeRP1, Parts open,
search blank, tools closed. No immediate owner action is required for the preview.
All physical/engineering gates and five UNSENT inquiries remain unchanged.

**Current desktop inspection delivery — PR116:** Source-bound archived part/
assembly CAD files, independent file scope, readable recovery-source conflict,
and explicit source-pinned fin/recovery links are integrated. Frozen RP1 remains
26 represented records across55 identities; detailed or qualified hardware is not
invented. [Publication and exact-head checks](https://github.com/kudratsingh/rocket-twin/pull/116).

P40/P42/P43 verify scoped notice/CAD/configuration paths. P44 completed one real
archived G80 Tiny run`exp-c174705a75b8474290b523e8fb7c1267`; P45 compared the
matching saved baseline and exported CSV. P46's permission rejection remains
historical. The owner explicitly authorized only the local site; P49 downloaded
the metadata JSON without a prompt or settings action. Fresh42,723bytes/SHA72374b…
match both actual records, sample range and differences. No persistent permission
change is inferred; metadata is no longer blocked.

P48 found a real settled return-selection failure. One correction separates
explicit selection intent from loading resets, hydrates overview links and keeps
empty-canvas misses from clearing a part. P50 verifies settled exactpart/spec/
recovery context, selected ring after assets load, Frame target, explicit Clear
and Whole restoration. Frame still leaves the internal ring occluded by the body;
it is not a clean-detail visibility pass. Initial P47 wrapper failure and P48
failure are preserved.P51 additionally verifies actual2D SVG-group selection retained in3D; its lower
annotation obstruction is preserved and corrected by2D-only flow layout inP53.
P52 verifies saved settings copied into a draft without a new run; independent
record bytes are unchanged. P53 shows the source/datum annotations unobstructed
and restores whole3D.318 local tests/type/lint/format/build pass; the finalCSS-only
change also passes format/build. Four unrelated A2 tests stay outside publication. Required hosted checks apply to the final PR
head; earlier green heads are not substituted.

[Connection correction](studies/frontend-rp1-evidence-routing-20261108/integration.md)
· [Actual experiment/export](studies/frontend-desktop-experiment-20261108/integration.md)
· [Future detail evidence](studies/frontend-desktop-detail-20261108/measurement-unlocks.md).
No owner measurement is requested for unpurchased hardware. All five inquiries
remain UNSENT. RP1/D1, G54/G12 PID-to-RL, strict failed performance benchmark,
engineering/WO-03/04/05, physical and flight gates remain separate/open.

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

**Comparison camera checkpoint (November8):** [Current worklist](frontend-release-worklist.md) records PR105–108 merged after required checks. The next camera-only increment has source tests and actual P12 Auto/A/B/Free button evidence at125, with B visibly in view and recorded values unchanged. P11's popup failure/2.599s overrun remains historical; P12 used a stricter90/120s guard and ended48.382s. Owner comparison125/AutoB is preserved. Exact-size/performance/full frontend and engineering gates stay open; RP1/AD1/D1, G54/G12 PID-to-RL and five UNSENT inquiries are unchanged.

**Autonomous release closure (November8):** [Current worklist](frontend-release-worklist.md) owns task reconciliation, experiment-monitor recovery, strict Analysis identity, bounded replay drawing and new targeted native checks. PR104 camera fix is merged. G80 RP1/AD1 v2 unchanged; all inquiries UNSENT. Engineering evidence/physical work and initial frontend release remain separate.

**Direct Move/Rotate correction (November8):** [Camera packet](studies/frontend-pan-20261108/report.md) makes Move view the default left-drag action and exposes Rotate view separately. Whole rocket returns to Overview/all loaded bounds; Fit assembly retains angles. Pan projection/gesture tests pass. Initial native Move-mode failure is preserved. After explicit mode-dependent gesture ownership and normal reload, the sole verifier observed translation with unchanged angles, rotation, zoom without recentering, and aft-ring Frame→Whole rocket. No geometry/engineering/flight change; inquiries UNSENT.

**High-g PCB reference (November8):** [Source-detail integration](studies/frontend-hardware-detail-sources-20261108/integration.md). The exact Adafruit5374 source board now has a selectable, licensed 2D footprint view in RP1 Details. Recorded board/envelope differences, ADXL343 source label and missing heights remain explicit; no 3D fit or silicon identity is inferred. Native browser opening is observed, Escape failed and its source correction awaits browser recheck. Offline900×810 SVG/PNG was visually inspected. Core geometry/AD1/D1 and engineering gates stay unchanged; inquiries UNSENT.

**Interior inspection continuation (November8):** [Source-supported interior workflow](studies/frontend-interiors-20261108/report.md). The owner requests easy direct manipulation, visibly useful internals and alternatives. Normal-flow Inspect interior/subsystem controls, optional hashed detail assets, missing-normal/depth/lighting corrections and a separate recorded fin-construction schematic are implemented. Core238…/all55 IDs and physical AD1/D1 remain unchanged. Optional ring/tube detail does not invent PCB/retainer/rope internals; FP1/FR1 remain unadopted. Current-window interior, framing, ring and fin-preview interactions are observed; final app restored to whole assembly. Code checks and browser evidence remain separate; the prior DevTools rejection and viewport limits remain. Supplier/lab drafts stay UNSENT, engineering/build/flight gates open.


**November 8 interaction checkpoint:** [Design UX report](studies/frontend-design-ux-20261108/report.md). Stable toggles, actual camera angles/roll, six functional source groups, staged display transforms, meshless safety and contextual unadopted fin comparison are implemented. Panel PR98 merged after both required checks. Current-window browser evidence verifies selected panel/camera/safety paths and the corrected control overlaps/direct isolation exit; RV-Q38–41 remain partial and Q42 unexecuted. A second external-change guard stopped verification without owner-ready restoration. Motor/recovery breakdown and fin-comparison walkthroughs need fresh window coordination; exact viewport setup was separately rejected by automatic approval review. No unsupported retry or bypass. Final code tests190 locally include four preserved/unpublished A2 cases;186 are in scope. All five inquiries remain UNSENT; engineering/build/flight gates unchanged.


**Design interaction correction packet (2026-11-08):** [Owner UX review](studies/frontend-design-ux-20261108/owner-review.md). Continue from published PR97/main `a4db05ef4cbd68fd957a1c803d98557d6171ea3e`. Four bounded display-only lanes: stable panel controls (Sol HIGH browser owner), actual camera angles/roll (Sol HIGH camera owner), versioned six-group/staged-breakdown metadata (Sol HIGH source owner), and primary-owned meshless selection/functional tree/contextual fin studies. Each lane has one implementation attempt and one correction; no new physics, CAD adoption, solver or native-rate performance campaign. Integrated source checks precede sole designated-agent Chrome verification at 1440×900, 1280×720 and 900×720. New interaction claims stay pending until observed; prior browser evidence is not reused to pass the new controls. Frozen AD1 v2/geometry `238d01e5…28b608`, D1, FP1/FR1 and all engineering/build/flight gates remain unchanged. All five inquiries remain UNSENT.


**Live verification checkpoint (2026-11-07):** [Actual browser evidence](studies/frontend-release-20261107/browser-access.md). Sole verifier `/root/browser_access_sol` completed the bounded normal-workflow checks in the owner-authorized Chrome window and restored RP1 Design at 1440×900/100%: 26 meshes, explicit Fit, no selection, guide off, both left columns open and tools closed. Actual captures establish default canvas/Focus dimensions, Side fits and a clean isolated barometer fit. Mapped fin/recovery links, all recorded configuration switches, Analysis missingness, real single/batch execution, replay/comparison/exports and request/render recovery have live evidence. Both full native-rate G54 measurements still miss the 60 fps target; follow-up p95 was 17.70 ms. Broader unexecuted/data-blocked branches remain partial; full frontend/work-order acceptance is open. No browser-owner input is pending. PR96 is merged; PR97 carries the closeout source/evidence through required checks. Local169tests include four unrelated saved A2 cases;165cases belong to the published scope, with orphan A2 work preserved locally. All five supplier/lab drafts remain UNSENT; WO-03, engineering, build and flight gates remain open.

**Frontend release candidate (2026-11-07):** [RP1 3D and remaining source workflows](frontend-release-20261107.md). Frozen RP1/AD1 v2 now has26 source-derived inspection meshes across55 audited records:10 source-dimensioned,16 simplified envelopes,25 mass allowances and4 missing geometries. Inspection identity is separate; no canonical inertia/flight/CAD adoption. Single/batch CPU experiments, replay comparisons/exports and recorded Analysis are implemented; experiments have their own context and cannot replace the working Design. All inquiries remain UNSENT. Owner authorizes the sole open Chrome window and necessary tabs, with `/root/browser_access_sol` as sole verifier; the first supported inventory returned **“The browser access host is unavailable.”** Consent and live API source attribution are resolved; remaining interaction checks stay open. No alternate runtime/bypass or engineering/build/flight acceptance. Optional Mission Control and future editing/fidelity have explicit deferred dispositions.

**RV-08 / RV-11 continuation (2026-11-07):** [RP1 parts and connection evidence](wo04-rp1-connections-20261107.md) adds exact AD1 design/spec/part links between Design and fin-root/recovery relationship drawings. Failed fin calculations stay separate from unverified installed joints; missing mappings are unavailable. [Independent saved-run pose checks](studies/replay-pose-20261107/report.md) validate production replay math, including the nose-up descent and marker-only invalid-attitude state. Code/source/offline checks do not establish browser interactions; the designated-runtime block remains. All five inquiry drafts stay UNSENT; continue from repository evidence without replies. WO-03, physical/build and flight gates remain open.

**Owner revamp direction (2026-11-07):** [RP1-first Design inspection](wo04-rp1-revamp-20261107.md). Use frozen G80-F2-RP1-AD1-definition-v2 as the current source/drawing design. Archived modular-performance-v1 is a separate matching-CAD/replay fixture; no historical mesh or inertia substitutes for RP1. Keep all five supplier/lab drafts UNSENT and proceed from repository evidence without waiting for replies. Expose estimates and missing details for later authorized measurement. Two adjacent independently collapsible left columns, dominant visual and a slim tools drawer replace the crowded Design layout. The 21 RV tasks map to the existing 43 FT tasks; code/offline checks and browser acceptance remain separate. WO-03, purchases, physical/test, paid-run, WO-10 and flight gates remain unchanged.

**Owner continuation (2026-11-06):** [VP1 inquiry-to-test decision](wo03-vp1-response-decision-20261106.md). The owner will supply actual send dates and replies for the five prepared inquiries. Track each actual send independently: one day-5 follow-up, day-10 business-day close; no dates or replies are recorded yet. Prepare one room-temperature test recommendation with the lab method, itemized all-in cost and D1 pass/fail meaning; return it for owner approval before purchases or testing. Frozen drafts/package and engineering criteria remain unchanged. Continue the next bounded frontend backlog task; browser observation remains separate from code/offline checks.

**Repository visibility — owner-confirmed public (2026-11-04).**
The owner explicitly confirmed that they made `kudratsingh/rocket-twin` public.
This supersedes the earlier private-only instruction and resolves the visibility
publication hold. Keep the repository public unless the owner requests another
change; do not attempt to restore Private. Continue the existing focused
PR/required-check/merge workflow. Supplier/lab contact, purchases, paid services,
physical work and flight release still require their existing authorizations.
The five VP1 inquiry drafts remain UNSENT; this confirmation concerns visibility only.

**Latest unblocked frontend increment (2026-11-06):** [VP1 programme inside the workbench](wo04-vp1-validation-workbench-20261106.md).
The separately source-pinned view has a selectable four-stage/nine-part SVG,
known versus unquoted costs and five exact UNSENT draft previews/copy/downloads.
Source/code/SSR checks pass; native PNG and browser visual/interaction acceptance
remain unavailable. There is no authorization, send, purchase or physical-test
action. Frozen engineering/source records and all owner gates remain unchanged.

**Current delivery: [VP1 owner-review validation package](validation/rp1-vp1/package-summary.md).**
One first test lead is ordinary6mm02-20850 birch with WEST105/206/406 fillets;
this is not vehicle adoption. Four product drafts plus one supervised-lab RFQ
remain frozen source drafts. No actual send dates or replies are recorded yet;
the owner will provide them for the separate response tracker. Each actual send
starts its own day-5 follow-up/day-10 business-day response window. No agent
outreach is performed. The next owner decision is the room-temperature method,
itemized all-in quote and pass/fail meaning before purchase or testing.

Room-pilot stock lists$236.75; conditional full stock reserve$269.49. Services,
fixtures, calibrated channels and delivery are unquoted, so the all-in total
is unavailable, never zero. A$5,000 planning reservation is an affordability
screen, not a price or spending permission. Method/replication/uncertainty and
stop conditions are in the [protocol](validation/rp1-vp1/protocol.md). No full
root execution is admitted without the specified method, supported construction,
written quote and owner authorization. S0 closes after10businessdays, with one
follow-up; do not wait for supplier aerospace allowables.

D1's8.83N·m/331.125N once-factored load,1mm movement, estimated material screens,
50g growth,20g adverse/motor probe,55/68g harness cases,1.5m/15formal/15.5planning
and physical/thermal/recovery/flutter/WO10/flight gates remain unchanged.
Frozen AD1, unadopted FP1/FR1 and G54/G12 PID-to-RL stay separate. G80 first,
substantial custom construction and practical performance remain core goals.

Frontend [portable RP1 SVG exports and graph zoom](wo04-rp1-export-20261104.md)
are merged inPR79 after required checks. Actual-source/code/SSR checks pass;
browser interaction remains unverified behind the unchanged ownership block.
Existing inspector, experiments and replay preserved; no browser workaround.

## Retained D1 engineering decision and historical checkpoints

**Current integrated decision: [RP1 D1 — load and attachment](wo03-rp1-load-attachment-decision.md), ADR-0015.**
The owner assigns primary integration; the coordination question is closed.
Merged FR1 PR75 (solid carbon) and FP1 PR76 (carbon-faced plywood) are separate,
**unadopted** studies. Frozen AD1 v2 stays unchanged. FR1 fails evaluated finite
movement/body-bond screens; FP1's nominal0.961 mm includes an unverified0.100 mm
attachment input and fails material sensitivities. No installed fin pass.

Enforce8.83 N·m /331.125 N, factor3 already applied once. Current-planform
40 kPa/5° arithmetic gives2.905255 N·m but is not an adopted governing case.
Older70 mm-fin calm flights cannot establish current60 mm RP1 loads/inertia.
D1 reconciles the source, complete-root model and exact-once mass alternatives;
12/16 combined material diagnostics fail, none is a qualified property bound.
No new fin variant, vehicle change, stopped solver retry or detailed CAD/FEA
is admitted. Next: [bounded representative evidence definition](wo03-rp1-d1-test-definition.md),
then source/whole-root evidence before one possible construction correction.
No purchase, supplier contact, physical test or owner hardware measurement.

[Accounting](wo03-rp1-integrated-accounting.md) preserves full separate50 g,
20 g adverse/motor probe and55/68 g unverified harness cases. D1 adds0 g.
All FP1/FR1 cases miss15.5 planning; FP1 adverse68 g also misses15 formal on
reference1.5 m. Longer equipment remains unconfirmed. G80 custom building and
practical performance first; G54 upgrade and committed G12 PID-to-RL separate.
WO-03, thermal/recovery/installed flutter, physical and flight gates stay open.

[Separate frontend study comparison](wo04-rp1-studies-20261104.md) adds source-linked
selectable relationship graphics. Actual offline PNGs inspected; browser
interactions remain unverified behind the unchanged ownership prerequisite.
Preserve inspector/experiments/replay and exact configuration identities.

## Earlier checkpoints — historical, not the current decision

**Latest attachment definition: [RP1 AD1 v2](wo03-rp1-attachment-definition.md).**
BalancedRP1v2 remains the frozen preferred research direction. AD1 specifies
exact30327/NW-12, proposed finished ends,6.5ftleader/12ftmain, contacts and a
[dimensioned sacrificial test plan](wo03-rp1-representative-test-plan.md).
It is not an adopted flight vehicle. The moved-ring fin's optimistic5.8mm
panel fails5MPa/1mm at7.301MPa/1.805mm; installed root/peel/flutter remain open.
No unchanged-fin detailed analysis or stopped solver retry follows.

Complete estimates add3.400g: nominal/adverse934.549/954.549g with separate50g,
CG763.693/775.602mm, static1.433/1.255cal,1.5m15.212909/15.033479m/s.
Formal headroom23.794/3.794g; planning deficits30.750/50.750g. The55gmain
remains estimated;68gmetadata is only a hypothetical probe, which fails adverse
formal speed. Final sleeve ends before the notch; no thermal/chafe pass.
[Final drawing pack](../output/rp1-attachment-definition/index.html) is concept
geometry, separate from current CAD. Test definition is ready for owner review,
not authorization to purchase/build/load it or fly. Finished strength is unknown.

Frontend [connections/evidence and recorded-sample readouts](wo04-inspection-evidence-replay-20261103.md)
pass integrated76webtests/type/lint/format/build; source-linked part navigation
and actual A/B sample timestamps/units are implemented. Browser behavior is
still unobserved behind the same designated ownership gate. No access bypass.
Full WO-03/04/05 and all physical/release gates remain open.

**Current recovery decision: [RP1 precedent recommendation](wo03-f2-recovery-precedent-decision.md).**
Carry a motor-tube wrap with a replaceable nylon main forward for definition;
keep the conventional F2 architecture and all earlier records frozen. This is
a research recommendation, not adoption. The single balance correction removes
redundant ballast-only parts and shortens the leader while preserving its route.
Selected balanced-v2 nominal/adverse estimates are931.149/951.149g including
full50g, CG763.302/775.261mm, margins1.439/1.260cal (1.149withaftcordstowage).
Reference1.5m departure15.243988/15.063562m/s passes15; formal headroom27.194/7.194g,
planning deficits27.350/47.350g. Conditional1.8m equipment remains unconfirmed.
Main nylon55g is an estimate; adverse formal maximum62.194g with other budgets
fixed. No growth use, reduced recovery case or detailed FEA is admitted.

The source study compares three kit families/four documented constructions.
The loop removes the proposed body-eye dependency, but moving the ring ahead of
tabs removes their old front support. Finished cord/knots, finite ring/tube/body
and revised root joints, heat and service remain open. [Current drawings](../output/f2-recovery-precedents-balanced/index.html)
are versioned concepts with actual offline images, separate from complete CAD.

The first inspection-slice correction is merged PR70: scroll/content height,
reachable details/search, source isolation, active2D shortcuts and section picking.
Integrated71 web tests/typecheck/lint/format/build and required hosted jobs pass; browser ownership remains
blocked with no exposed supported repair command. [Handoff](wo04-inspection-slice-20261103-v3.md).

[Read-only asset readiness](wo04-inspection-asset-readiness-20261103.md) confirms
source-matching listed mesh inventories: referenceG80 42/42, G54 42/42, finnedG12
53/53 and finlessG12 51/51. These are the older reference designs, not F2/RP1 CAD.
Current mesh bytes were fingerprinted; no independent expected GLB-byte hashes
or browser/WebGL acceptance is claimed. Supplier questions for the unpurchased
nylon/Kevlar are [prepared but unsent](wo03-f2-recovery-supplier-questions.md).

The F2-C2 joint-demand declaration below was superseded before arithmetic. RP1's
new small arithmetic had one preserved ledger-export failure and one declared
setup correction; no stopped F2/C1 solver was repeated. Hardware is unpurchased.

**Previous connection decision: [G80-F2-C1](wo03-g80-f2-c1-decision.md), not adopted.**
Frozen F2 remains the working reference below. The new proposal defines seven
conditional fit stacks and adds1.190g epoxy with zero wood-removal credit.
Nominal/adverse918.750/938.750g, static1.283/1.105cal, reference1.5m
15.359/15.175m/s. Formal speed passes; planning misses. No longer rail adopted.

The critical recovery pull **opens the blind-notch floor gap**, leaving adhesive
tension/side shear as the load route. Finished eyes, actual body/tab/mount support,
peel/wood strength and motor contact remain unresolved. Two numerical grids are
valid; the fine mesh and one defined replan stopped at the unchanged node cap
(last139953>100000). Required3-grid convergence is unavailable; no further retry.

[Verification supplement](../configs/engineering/g80-f2-c1-verification.yaml)
keeps existing requirement IDs and independent G54/G12 tracks. CurrentF2-C1
geometry remains a proposal; its generators are explicitly unadmitted and the
old32.3mm ring fields do not apply to new32.2mm geometry. No prototype/flight gate
or installed strength/thermal requirement closes.

Inspection refinement [PR68](https://github.com/kudratsingh/rocket-twin/pull/68)
is merged; both required jobs passed at `798d20ae722549f90648f5a2d709066156630c0b`.
The new [connection-study handoff](wo04-f2-c1-walkthrough-20261103.md) records
separate source-linked graphics, a dimensioned section, the complete coupled
table and offline image observations. Open
`http://127.0.0.1:5173/?workspace=engineering&view=g80-f2-c1` after `make preview`.
The study is not a new flight configuration or a compatible stress overlay.
Browser runtime ownership remains unresolved; read-only host diagnostics do not
bypass it. The owner subsequently confirmed that none of the exact motor,
mount tube, retainer or recovery-anchor hardware has been purchased. Do not ask
for measurements of unavailable hardware; missing mating data remains a supplier
dependency. Components remain budgeted purchases; none is authorized here.

**Current selected G80 follow-up: G80-F2-fixed-stock-ballast-v2.**
[Construction decision](wo03-g80-f2-decision.md) and
[exact-once coupled audit](wo03-g80-f2-coupled-accounting.md).
Actual-stock body splice, blind fin notches and compact retained-nose package
replace F1's unresolved stock/interference layout. F1 remains frozen history.

| Selected case (full separate 50 g included) | Mass | CG from nose | Static margin | Reference 1.5 m speed | Formal / planning mass headroom |
| --- | ---: | ---: | ---: | ---: | ---: |
| Nominal |917.560 g |773.559 mm |1.286 cal |15.370 m/s |+40.784 / -13.761 g |
| Additional 20 g aft + motor-balance probe |937.560 g |785.473 mm |1.107 cal |15.186 m/s |+20.784 / -33.761 g |

The formal 15 m/s and calculated 1-calibre screens pass within the declared
hypothesis; **both cases miss the separate 15.5 m/s planning target**. No longer
equipment is confirmed or adopted. Costs are $458.71 before unquoted shipping/tax;
recovery electronics are budgeted purchases, not assumed owner stock.

**Not admitted for prototype fabrication or flight.** Installed recovery/fin
joints, exact G80/retainer contact, thermal matrix, hot/wet properties and
installed flutter remain open. The local fin/ring CAD has zero solid overlap;
this closes that nominal geometry defect only. The ring diagnostic is stopped:
one inverted element in the middle mesh prevents a three-grid convergence or
strength claim. No retry/new solver or automatic construction revision follows.

New separate walkthrough: `make preview`, then
`http://127.0.0.1:5173/?workspace=engineering&view=g80-f2`.
[Offline drawings](../output/engineering-g80-f2/index.html) include arrangement,
splice/fin/nose layers, recovery branches and signed mass changes. Whole-vehicle
CAD and compatible stress/temperature fields remain unavailable. Offline images
and source/API checks are distinct from pending browser verification.

G80 first, custom fabrication and practical performance remain core goals;
G54 upgrade and G12 PID-to-RL keep their separate committed requirements.

## Frontend delivery checkpoint

The owner-supplied43-task kit is now tracked in
[the backlog](frontend-workbench-backlog.md), with focused workspaces under
[ADR0014](adr/0014-focused-engineering-workspaces.md). Astra MEDIUM implemented
shell/source isolation and linked2D; Terra HIGH delivered camera controls,
replay status and a four-sample saved-record audit. Primary integrated shared
routes/state. [Current usable-code handoff](wo04-focused-preview-20261103.md)
records exact pages, startup and pending browser tests.

F2 engineering PR66 merged after both required jobs passed at55599a2370962f195dea31faee49fb825c7646fe.
Inspection refinement PR68 is merged as recorded above. Launcher preparation
passes, but Vite cannot bind127.0.0.1:5173 in the sandbox (`listen EPERM`).
No live app or browser acceptance is claimed. The original designated-browser
ownership rejection remains unresolved and was not retried/bypassed.

## Historical checkpoints below

**Active follow-up: G80-F2**, [bounded packet](wo03-g80-f2-packet.md). Keep F1 frozen. Use obtainable stock, one fixed bonded splice, connected recovery/fin joints and coupled forward-placement/ballast comparison. G54/G12 remain separate; no new platform architecture. F1 numbers below are historical input, not F2 results.

**G80-F1 dedicated fixed conventional rocket is the delivery direction.**
[Current decision and complete budget](wo03-g80-f1-decision.md),
[bounded packet](wo03-g80-fixed-packet.md), [ADR-0013](adr/0013-dedicated-conventional-g80.md).
Physical interchangeability is optional; no future gimbal/servo hardware in G80.
G54 upgrade and G12/PID-to-RL remain committed separate tracks.

One correction finished: continuous body1060mm,1250mm overall, fixed TTW fins,
fixed paper motor mount and laminated forward ring. Nominal/adverse totals
**817.506/837.506g including separate full50g**, reference1.5m departure
**16.388/16.170m/s**. Both guide thresholds pass, but static margins
**.743/.556cal fail1.0**. The severe recovery ring strip still fails; actual
motor/retainer fit, installed root stiffness/flutter, hot/wet properties and
thermal matrix remain unresolved. A matching one-piece1060mm tube is not sourced; LOC stock is shorter with different bore/OD. **Not admitted to detailed vehicle CAD or
manufacture; no installed engineering requirement closes.** No third revision
or failed/stopped old campaign was started.

The new source-linked graphical snapshot is separate from old C1/A1 assemblies:
`make preview`, then `http://127.0.0.1:5173/?workspace=engineering&view=g80-fixed`.
It shows the42-row concept/envelope ledger, fixed construction/assembly,
recovery/motor/fin routes and failed current/first geometry comparisons. It is
not manufacturing-ready CAD. Backend GETs display saved calculations only.
Offline images and browser interaction acceptance are separately recorded in
[the walkthrough note](wo04-conventional-g80-walkthrough.md).

## Frozen historical checkpoints


**Current priority: G80-F1 dedicated conventional rocket**, under
[ADR-0013](adr/0013-dedicated-conventional-g80.md) and the
[bounded simplification packet](wo03-g80-fixed-packet.md). Physical aft/upper
interchangeability is optional. One fixed paper/plywood architecture is selected;
no G80 control/gimbal provisions. A2 intake stopped before numerical execution.
The A1 and earlier results below are historical, not the design to refine now.

**Current A1 decision: hold detailed admission.** The [connection report](wo03-a1-connection-decision.md)
includes a new [seat/liner occupancy failure](wo03-a1-occupancy-audit.md): proposed
seatz1193–1195 overlaps retained mica/foil ending1200. No automatic trim or move.
The remainder of the report
defines a sleeve, stop, keys, bolts, actual upper bond and routed harness. Bounded
aft clearance0.1171mm passes0.1 only within unmeasured inputs. Full added
hardware/mass is+106.454g versus frozen A:1074.762/1094.762g including separate50g.
Reference1.5m departure14.059/13.912m/s fails; adverse formal/planning deficits
136.364/190.908g. A conservative one-bolt combined demand463.661MPa exceeds
the existing200MPa hot-steel estimate. Paper/peel/bearing/thermal/flutter and
current motor/retainer remain unknown. No whole-vehicle CAD/FEA or next automatic
variant is admitted; no installed engineering requirement closed.

Published C1/A/B below remain frozen history. A1 is a separate snapshot and
changes no active or shared G54/G12 assembly. New external collar/head geometry
makes reused C1 CP/drag only reference hypotheses; full inertia/new CP unavailable.

The separate graphical A1 snapshot is now implemented at
`http://127.0.0.1:5173/?workspace=engineering&view=a1` after `make preview`.
[Offline A1 gallery](../output/engineering-a1-connection/index.html) provides
three actual inspected PNG/SVG drawings: sleeve/stop/key/harness/service and five
separate load paths; radial bolt stack/upper bond/root; and recorded fit, mass
addition and separate formal/planning deficit bars. These are
concept graphics, not CAD or browser screenshots. Current snapshot includes the
previously missing historical0mm fit finding; browser interaction stays blocked
by the designated-agent runtime-ownership prerequisite, with no retry/bypass.

**G80 first. C1 is preliminary. R1/C2/C3 remain rejected.** Substantial custom
construction, maximum practical performance and committed G12 PID-to-RL remain
core goals; G54 remains a separate upgrade. Expanded WO-03 and every build,
purchase, paid-run, firmware-review and flight-release gate stay open.

## Engineering decision

Prefer **A: integrated through-body motor/fin can** for a bounded connection
study; **neither A nor B is admitted to detailed vehicle CAD/FEA**. Both are
separate concept studies, not changes to C1 or the active vehicle.

| Complete case, separate50 g included | Mass | Balance from nose | Stability |1.5 m departure |1.8 m conditional departure |
| --- | ---: | ---: | ---: | ---: | ---: |
| A nominal |968.309 g |844.352 mm |1.856 cal |14.914 m/s |16.341 m/s |
| A additional20g/motor-CG |988.309 g |853.756 mm |1.713 cal |14.743 m/s |16.155 m/s |
| B nominal |995.812 g |852.518 mm |1.732 cal |14.680 m/s |16.086 m/s |
| B additional20g/motor-CG |1015.812 g |861.506 mm |1.596 cal |14.516 m/s |15.907 m/s |

A saves161.498 g from C1 but still needs29.911 g additional saving for the
adverse **formal15 m/s** case on the unchanged1.5 m guide. Separate15.5 planning
needs84.455 g. Longer usable travel remains unconfirmed and conditional.
The retained-upper interface audit also fails the proposed A/B cold-fit stack:
64.0mm model coupler /64.4mm bore gives0mm worst-case radial clearance under
the declared bounds, versus0.1mm required. [Audit](wo03-architecture-interface-audit.md)
records the issue without resizing a part or changing frozen mass results.
The other controlling items are finished hot root/recovery joints, finite
cap/body load spreading, exact G80/retainer fit, heat and installed stiffness.
Full rotational inertia is unavailable. **No installed engineering requirement
closed.** The two-arrangement study is complete and stopped at admission.

- [Decision and complete mass/margin evidence](wo03-architecture-decision.md)
- [Actual function allocation and A/B concept drawings](wo03-architecture-function-allocation.md)
- [Primary-source and later owner-only measurement plan](wo03-architecture-source-packet.md)
- [Unsent ROC/MDARS equipment questions](wo03-launch-owner-confirmation-20261102.md)
- [Bounded work list and responsibilities](wo03-current-worklist.md)

## Open the inspection workbench

Run `make preview` at the repository root, then open:

`http://127.0.0.1:5173/?workspace=engineering`

The preserved arrangement/section/force/mass views now have companion graphical
views selected with `&view=comparison`, `recovery`, `thermal`, `electrical`,
`assembly` or `requirements`. They display versioned backend data and link
selection to the current C1 inspector when a valid part mapping exists.
New A/B concepts have no fabricated C1 part/CAD association.

| Local artifact | What can be inspected |
| --- | --- |
| `output/rocket-twin-review/index.html` and `review-pack.zip` |Self-contained gallery and downloadable pack of recorded drawings/native images |
| `output/engineering-walkthrough/index.html` |25 C1/R1 SVG drawings with units, source/status and configuration metadata |
| `output/engineering-walkthrough-rendered/contact-sheet.png` |25 real offline raster pages; representative labels/arrows actually inspected |
| `output/engineering-workbench-extended/index.html` |New comparison/recovery/thermal/electrical/service/requirement SVGs and actual PNG previews |
| `output/wo03-architecture/architecture-A-motor-fin-can.png` |Dimensioned A concept and protected volumes, not detailed CAD |
| `output/wo03-architecture/architecture-B-outer-captured-roots.png` |Dimensioned B concept and unresolved connections |

The135 C1 source allocation/envelope rows are not a manufacturing-ready CAD
assembly. Archived72-part CAD remains separate. Recorded thermal histories
and failed fixtures stay historical/incompatible with current C1; absent spatial
fields/time samples/pins/inertia stay unavailable. Deployment/service storyboards
are illustrations, not validated mechanism/deployment simulations.

Offline image rendering now works with the installed documented AppKit
image-document API. Actual image inspection identified and corrected exported
arrowhead portability; no browser/window or dependency installation was used.
Raster images do **not** prove browser interactions or frame rate. Host URL
reachability, clicks/downloads, responsive layout and WebGL remain pending the
designated browser agent's runtime-ownership prerequisite. The last automatic
approval rejection is not retried or bypassed.
