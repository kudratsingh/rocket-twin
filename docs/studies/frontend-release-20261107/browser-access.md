# Frontend release: supported access findings and browser protocol

**Current result:** the owner explicitly reassigned the sole current Chrome window to this verifier. Supported native Chrome control works in the same CUA runtime, and after the owner restarted the normal-host preview the live API and rendered 26-mesh RP1 model match the exact current inspection source. Genuine Design, Engineering, Analysis and saved-run observations are recorded below and in [browser-results.csv](browser-results.csv). The extension browser-host failure and original ownership investigation are historical; compound acceptance rows remain partial where subpaths are unexecuted.

**Latest correction and measurement:** the exact-time component import collision was reproduced and corrected with an explicit `.tsx` import, then a normal Chrome reload succeeded. Exact recovery and landing requests now work. Two separately authorized source-state G54 browser profiles loaded all 132,856 saved rows: the initial attempt failed 60 fps (p95 33.20 ms, mean 17.83 ms), and one changed-source follow-up improved but still failed (p95 17.70 ms, mean 17.50 ms). No third attempt was made. Ordinary Offline request recovery and an explicit development render-error fixture were observed; normal transport and bounded playback were restored. See the current outcome section below.

Date: 2026-11-07. This records bounded access research, subsequent explicit
owner reassignment, and supported native interaction with the same authorized
Chrome window. Native Chrome access now works through `cua_repl`; the extension
browser access host remains unavailable. After the owner restarted the normal
host preview, the live RP1 API visibly matched geometry digest `238d01e5…28b608`
and the app actually rendered all 26 inspection meshes. Verification is now in
progress, with compound acceptance rows tracked in [browser-results.csv](browser-results.csv).
No other app/window,
headless/CDP path, sandbox escalation or preview startup was used by this agent.

## Current observed state

**Post-restart update:** The owner reported restarting the preview. A fresh native
Chrome visit to `/api/vehicles/G80-F2-RP1-AD1-definition-v2` visibly showed exact
geometry hash `238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`,
matching spec/record identities and null canonical resolved/CAD identity.
The actual Design canvas rendered the source-derived nose, body, fins and motor,
with 26/26 loaded bounds and saved nominal-55 CG/CP estimate labels. Source part
`baro` was found through search, selected in the tree and explicitly framed;
its simplified-envelope label and 1/1 loaded bounds were observed.
Screenshot `runs/frontend-browser-20261107/rp1-baro-framed-1440x900.png` is the
unchanged native capture (2880 × 1800 raster, SHA-256
`543119eaae2e37adffc897083ba1a38b6a4b1ca0a6e35dc4e3bc67a912d31411`).
The earlier stale-backend observations below are historical, not the current
blocker. Browser interactions are now executable in the authorized window.

That first selected-part capture exposed overlapping bottom selection/framing/
missing-solid messages. The primary subsequently moved the framing and
missing-solid readouts into Scene tools; the actual restored assembly and open drawer recheck showed both readable without overlap. The primary also replaced nested React roots for scene labels and corrected orientation placement. A reload/console-display clear followed by selection, section, hide/restore and workspace transitions showed no new synchronous-unmount errors; the pinned upstream THREE.Clock deprecation remains visible.
Native AX-index clicks also proved offset for adjacent app buttons within
Chrome's scaled responsive viewport. Screenshot-coordinate clicks correctly
selected visible Parts and Details; no header-dispatch code defect was found.
DevTools controls outside the emulated page remain usable by native AX index.

After the owner explicitly authorized the sole open Chrome window and any tabs
needed within it, the primary assigned `/root/browser_access_sol` sole browser
verification ownership. A documented `cua.getApp('Google Chrome')` call succeeded
and exposed that same sole window, titled `Rocket Twin · Vehicle inspection`,
with one initial tab at `http://127.0.0.1:5173/`. This is supported native input
through the existing CUA runtime, not another browser/runtime or a headless/CDP
route. No automatic approval rejection occurred on either new discovery call.
The historical ownership rejection remains preserved below.

The actual initial site was reachable at Chrome zoom 125%, showing RP1's older
drawing-only API source. Reload did not change that state. A second tab in the
same window displayed `/api/vehicles/G80-F2-RP1-AD1-definition-v2`; native browser
Find for `inspection_geometry_sha256` returned **No results**. In contrast, the
served prepared `/engineering-workbench/rp1-ad1-inspection.json` visibly contained
the current source-derived inspection status and geometry digest
`238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`, with matching
specification `811b3bed…`, record `bc349a24…` and canonical resolved/CAD hashes null.
These observations isolate a stale live API response alongside an updated
prepared source. They do not attribute the running API to the combined release.

Chrome zoom was then reset to 100% with the documented native key API. Ordinary
Chrome DevTools UI, without entering console code or using a remote protocol,
exposed the responsive viewport controls. Width **1440** and height **900** were
confirmed in those controls. A native DevTools **Capture screenshot** action
downloaded the old-backend viewport; Chrome confirmed the download completed.
The unchanged image is retained at
`runs/frontend-browser-20261107/old-backend-design-1440x900.png` (2880 × 1800 raster,
SHA-256 `b45dbc42c6e6a1d2b25e85133712e074dfb7a9539947d2841be8ec229ebc9175`).
The 2× raster dimensions are observed; a JavaScript `devicePixelRatio` read was
not performed. This screenshot is explicitly old-source evidence, not the
current RP1 3D model or release-layout acceptance.

A temporary `chrome://version/` tab in the same window reported Google Chrome
156.0.8078.80 (Official Build, arm64), revision
`fb096c0011f9d50f0a264a9376420cdea9c421e3`, macOS 27.2 (Build 26B123), and
V8 15.6.75.27. That temporary version tab was then closed; the original Design
tab remains selected with the 1440 × 900 responsive viewport ready for recheck.

Read-only native Console UI showed a failed resource with HTTP 503 for
`/api/motors/aerotech-g80-10t-SKU78010-provisional/curve`, plus React DevTools
informational text. This failure belongs to the observed older served state and
must be rechecked after restart before attributing it to the current source.

The historical next owner action was to restart the existing preview from the normal host
terminal (`Ctrl-C`, then `make preview` at this checkout), retain its output, and
report readiness. The verifier then reloads the same Chrome tab and checks the
live API's geometry digest, 26 mesh references, four saved mass cases and actual
rendered model before proceeding with the full protocol. Extension/plugin repair
is no longer the blocking path while supported native same-window control works.

## Access result

The original designated Terra runtime remains unidentified in the available
project records. No supported restoration or ownership reassignment command was
found in the available tool metadata or installed browser documentation. This
is a bounded finding about the inspected surfaces, not proof that the runtime
provider has no recovery mechanism.

The controlling records are [AGENTS.md](../../../AGENTS.md#computer-use-restriction),
[ADR-0016](../../adr/0016-rp1-frontend-revamp.md), and the
[recorded ownership blocker](../../frontend-browser-unblock-20261103.md).
The original saved handoff reports an automatic approval rejection because the
designated-agent ownership prerequisite was unsatisfied. The full original
reviewer transcript and a technical ownership-repair procedure are unavailable;
this audit does not reconstruct or embellish them.

| Inspected surface | Supported capability found | What it does not establish |
| --- | --- | --- |
| Codex task tool metadata | `list_threads`, `list_archived_threads`, `read_thread`; archive/restore a task, send a follow-up, create or fork a task | No described operation reattaches an original browser runtime or transfers its ownership. Task restoration is not runtime restoration. |
| Read-only recent/archived task discovery | Recent list exposed current Rocket Twin thread `01a18977-f879-7822-b971-9a31b266ec1d` and planning thread `01a189c6-947a-74e1-9fca-5b11735e3fdf`; archived list returned empty with no continuation | No original designated Terra runtime/agent identity surfaced. The recent list is bounded, so absence is not an exhaustive historical claim. |
| Read-only planning-thread messages | Recent messages repeat the owner request and the unresolved access prerequisite | They do not identify a repair mechanism or the original runtime. No follow-up was sent to another task. |
| Installed Chrome/browser troubleshooting docs, bundle `26.1027.51404` | Explicit browser-disconnect recovery and documented tab/window management | A project ownership rejection is not an observed disconnect. Tab selection/claiming and window management do not grant designated-agent authority. |
| Installed Chrome/browser management docs | Window/tab organization; explicit prohibition on denied-method workarounds | No ownership transfer, original-agent restoration or permission override is documented. No management API was called. |
| Current shell/PTY metadata | Sandboxed `exec_command` and `write_stdin` | A PTY does not turn sandbox execution into a normal host terminal. No available metadata describes a separate host-terminal launcher. |
| Available computer-use entry-point metadata | Browser/app selection and documented automation entry points | Merely exposing these entry points does not satisfy the existing rejected ownership prerequisite. None was invoked. |

Local documentation inspected:

- `~/.codex/plugins/cache/openai-bundled/chrome/26.1027.51404/docs/browser-troubleshooting.md`
- `~/.codex/plugins/cache/openai-bundled/chrome/26.1027.51404/docs/browser-control-interruption.md`
- `~/.codex/plugins/cache/openai-bundled/chrome/26.1027.51404/docs/capabilities/browser/management.md`
- Corresponding installed `browser/26.1027.51404/docs/` troubleshooting documentation.

No undocumented Codex setting, reconnect button, terminal launch mechanism or
runtime command is recommended. Naming a new Sol or Terra agent does not restore
the original identity. The current request permits arranging a supported
reassignment; it does not itself demonstrate that the runtime has granted one.

The primary's separate OpenAI documentation review found ordinary Chrome
setup/permissions guidance in [Using your computer and browser](https://developers.openai.com/training/walkthroughs/using-your-computer-and-browser)
and general API guidance in [Computer use](https://developers.openai.com/api/docs/guides/tools-computer-use).
Neither documented a repair for this project's designated-runtime ownership
rejection. The general computer-use API does not authorize a replacement
automation route for this project.

## Historical owner/provider handoff before the new reassignment

The owner/runtime provider must identify and restore the original designated
Terra execution context and its supported ownership of the existing Chrome
window containing the Atlas Fibre G11 PDF, or supply a supported replacement
runtime and an explicit named ownership reassignment through both runtime and
project instructions. Record the named agent/context, permitted window,
supported procedure and resulting ownership confirmation before browser work.
The primary and all other agents then abstain from concurrent computer use.

Concrete information to return to this task:

> Restore the original designated frontend Terra agent's supported access to the
> existing Chrome window containing the Atlas Fibre G11 PDF. If restoration is
> unavailable, provide the supported replacement execution context and the exact
> ownership-reassignment procedure, and explicitly assign that named agent sole
> verification ownership for that same window. Preserve the prior rejection and
> confirm how the prerequisite is now satisfied. No alternate window, headless
> browser, CDP route or rejected-action retry is requested.

This is a provider/owner handoff requirement, not a claim that a specific UI
control exists. Browser rows remain `blocked_runtime` until supported access is
actually established and attributed.

The primary presented the owner with an explicit alternative: assign sole
verification ownership to the current named agent `/root/browser_access_sol`
and attach or @mention the Rocket Twin tab in the original Atlas Fibre G11
Chrome window, or restore the original Terra context through the provider.

The owner then replied, as relayed by the primary: “you can use the chrome
window i have open, only 1 window, openwhatever tabs you need”, followed by
“open dev site” and “opened”. The primary explicitly designated
`/root/browser_access_sol` sole verifier and interpreted this reply as replacing
the historical specific-window restriction with the owner's sole current Chrome
window. Other agents abstain from computer use. This authorizes the supported
first discovery; it does not claim restoration of the original runtime.

The first documented call, exactly `await cua.getState()`, succeeded in returning
the API documentation and app inventory. It showed Google Chrome running but
returned `browsers: []` with the exact error:

```text
Browsers: Error: The browser access host is unavailable
```

No browser/tab was exposed for a supported claim. There was no new automatic
approval rejection. At that point no native Chrome app, alternative runtime, reconnect, retry
or other route had been attempted. Browser-tab transport was blocked by the unavailable
browser access host, despite the newly explicit owner authorization. The next
provider/owner action is to make the supported Chrome browser access host
available and expose the permitted existing window/tab. The available evidence
does not establish an exact repair setting or command. At that historical checkpoint browser rows remained
blocked. The later supported native same-window path above resolved execution access.

The primary's subsequent plugin-directory search returned no matching Chrome
entry; that bounded result is not proof the plugin is absent. The documented
owner setup path is ChatGPT → Work → Plugins, selecting Chrome and connecting
the extension if that option is offered. If it is already connected, the runtime
provider must restore the browser access host. No tool-level repair was exposed.
Another discovery call waits for a new owner-reported connection state; the
initial failure is not retried without that state change.

Preview startup is an independent host action. In a normal macOS terminal, from
this repository root, the owner should retain the output of:

```sh
.venv/bin/python scripts/wo04_preview_preflight.py
make preview
```

Then run preflight again in a second normal terminal while the launcher remains
running. See [the full startup instructions](../../frontend-owner-verification-20261103.md).
The fixed endpoints are `127.0.0.1:8000` and `127.0.0.1:5173`; do not change ports
or use another execution context to bypass the historical sandbox `EPERM`.
The preflight is advisory: its successful exit alone does not mean every check
passed. Record actual responses and served source identity. Host startup does
not resolve browser ownership; browser ownership does not prove host startup.

## Acceptance-matrix audit

At audit, `docs/frontend-revamp-acceptance.csv` SHA-256 was
`977ae9ffad064afd3f8c0e95d1059ecfd8a35fcbab988bb808fd870fbe1a131f`.
It contained 37 unique rows: 12 offline, one access and 24 browser. Status counts
were five pass, three partial, four pending and 25 `blocked_runtime`.
The 25 blocked rows comprise access RV-Q04 plus all 24 browser rows. This audit
does not change any result. Later integration may change offline statuses;
capture a fresh digest and counts before execution.

RV-Q35 is conditional on optional Mission Control. It needs an explicit
out-of-scope disposition if that feature is not implemented; lack of an optional
dashboard must not remain an unexplained release dependency. RV-Q30 requires
actual full-recovery telemetry at least 120 s long at 1 kHz and measured host
statistics. The existing 116.029 s diagnostic cannot satisfy that fixture.
The geometry/source audit subsequently identified raw saved G54 run
`exp-ab60bd4ac5c2412a9dd85f712072bca2` with 132,856 samples at declared
`dt = 0.001 s` and landing at 132.856 s, matching its saved G54 spec/CAD identity.
That available raw fixture is distinct from full-rate browser delivery: the
current telemetry endpoint decimates to approximately 3,000 samples plus events.
Full-rate browser workload and measured host statistics remain unobserved, so
RV-Q30 is pending rather than a performance pass. Offline RV-Q02/Q03/Q13 remain
separate geometry/replay evidence obligations.

## Grouped live-browser protocol — execution coverage below

Use the combined release source and build, not an earlier component branch.
Before every session record exact commit or source hashes, dirty state, served
build attribution, API/source identities, saved-run/analysis identities, browser
version, operating system, device-pixel ratio, actual viewport CSS dimensions
and browser zoom. Record screenshots, expected/actual observations, console and
network errors, result status, and issue/fix references per acceptance row.
An HTTP response or screenshot alone does not attribute the served frontend.

Required release sizes are **1440 × 900**, **1280 × 720**, and a declared narrow
width **below 1100 CSS px** (suggested 900 × 720). Measure actual CSS size after
each resize and zoom. At each size, cover navigation, panel/drawer restoration,
last-control reachability, page/tree/details scrolling, keyboard focus and
horizontal overflow. The retained planning kit additionally specifies
1280 × 800, 1440 × 900 and 1920 × 1080 at 100%, 125% and 150% browser zoom;
report unexecuted retained combinations as pending, or obtain an explicit scope
disposition. Never imply browser zoom preserves CSS dimensions.

| Group | Acceptance rows | Required observed flow and evidence |
| --- | --- | --- |
| 1. Access and host attribution | RV-Q04 | Confirm supported sole ownership of the existing permitted window and actual running host preview; record both independently. Stop browser work on rejection or missing ownership. |
| 2. Navigation, layout, accessibility | RV-Q05, Q07, Q09, Q10, Q11, Q12, Q34 | Visit all five workspaces; reload copied links; Back/Forward; stale/unknown links. In Design exercise four independent column combinations, slim tools, selected deep evidence and Focus/Escape restoration at every release size. Measure default canvas at both desktop sizes: at least 72% client width and 78% client height; Focus at least 95% width excluding scrollbar. Scroll/tab to final controls; narrow drawers must preserve state without clipping. Complete Design → Engineering → Design and record source/selection/camera identity. |
| 3. RP1 and archived inspection | RV-Q14, Q15, Q16, Q17, Q18 | Record frozen RP1 inspection source, modeled/envelope/missing classifications and selected part identity. Keep the archived complete assembly as a separate named fixture. Test small-part tree and model selection, explicit Fit/Focus/Reset, manual orbit/pan/zoom through resize/panel changes/late loads, section and clipped picking, hide/isolate/explode/restore, compatible 2D mapping and unsupported mappings. Side fit must span 80–90% usable height; end/tight fit 65–85% limiting dimension with at least 5% clearance at both sides. Record actual screen bounds and state; do not infer rendered clearance from camera mathematics. |
| 4. Independent failure and missing geometry | RV-Q06, Q18 | With a declared supported controlled fixture, exercise exact missing-route response, missing source, malformed data, HTTP 500, delayed A/B responses and one missing/delayed GLB. Record request/source identities; no stale or foreign attachment. Do not call a response-injection mechanism available until its documented capability is confirmed. Unavailable fixture branches remain pending. |
| 5. Engineering and exports | RV-Q21 | Navigate RP1 studies, VP1 and one historical topic; select a mapped component and follow exact part/case evidence. Pan/zoom, open/scroll evidence, download SVG and hash/inspect source, units and maturity. All five VP1 drafts stay UNSENT; export interaction confers no send/test authority. |
| 6. Experiments and batches | RV-Q22, Q24 | Use a named eligible archived complete configuration and approved bounded local preset. Observe queued/running/success/error, request/effective inputs, saved reload and failure recovery. RP1 flight eligibility stays unavailable without full admitted inputs. Declare a two-member fixture batch, concurrency, timeout and storage scope; exercise one failure, cancellation acknowledgement versus termination, reload and explicit retry, retaining every prior member/attempt. No paid run or new controller. |
| 7. Replay, comparison and presentation | RV-Q25, Q27, Q28, Q29, Q30 | Use exact saved records; play/pause/speed/scrub/event-jump; record cursor time across pose/timeline/plot and switches. Check T+11.150 s recovery and T+116.029 s landing for the named diagnostic. Preserve recorded nose-up descending attitude and explicit unsupported suspended-body limitation. Test unequal windows, absent events/channels, absolute/event-aligned clocks and offsets, gap handling, bounded export metadata/digest and peaks against raw metrics. Switch follow/pad/free camera; record scale/source/effect labels and reduced motion. Run performance only with qualifying full-duration data and measured host frame/memory/scrub statistics. |
| 8. Analysis and conditional scope | RV-Q32, Q33, Q35 | Show RP1 recorded findings with source identity. Attach 3D results only to exact compatible geometry/result records; inspect valid zero, uncovered region, missing timestamp, scalar-only and incompatible cases. Record legend, units, coverage and 1× deformation default. Change analysis time without implicit replay coupling. If optional dashboard exists, verify focused-page links/state; otherwise record explicit out-of-scope disposition. |

After a defect fix, rerun the affected flow against the combined release and
record its new source/build attribution. Final evidence reconciliation belongs
to RV-Q36; no browser result may be promoted from this protocol, source checks,
SSR, offline images or another revision's observations. WO-03, physical/build,
paid-run, WO-10 firmware review and flight gates remain open.

Historical pre-native release-ledger disposition: all37rows remain traceable. Twelveoffline rows
have source evidence;24access/browser rows are blocked by runtime (with compatible
field data additionally missing for covered-field visual paths); optional
Mission ControlRV-Q35 is not applicable because RV-17 is explicitly deferred.
This supersedes the initial pre-disposition count of25blocked rows; it does not
turn any unobserved browser check into a pass.

Historical checkpoint immediately after native control succeeded: RV-01/02 offline tasks
and RV-03 access are complete within their own scopes. RV-Q04 is now pass;
13rows have source/access evidence,23current-release browser rows remain pending
the currentAPIrestart (plus covered-field data where applicable), and optional
RV-Q35 is not applicable. The old-backend screenshot is not a current-release
layout or interaction pass. This supersedes the preceding host-only blockage
and pre-native row counts.


## Live verification outcome — current

The native session used Chrome100% zoom and responsive1440×900,1280×720 and900×720 CSS viewport controls. Raster captures are2×those dimensions. Current RP1 exactsource matched the post-restart API and actual26-mesh canvas. Both desktop columns collapse independently; Focus/Escape restores state. Narrow drawer failure was reproduced and rechecked after the primary corrected compact grid-area inheritance. Details reaches the final source/limitations control. Actual fit, baro selection/frame, section/hide/restore and exactsource Engineering/Back roundtrip worked. Camera fit ratios, all retained zoom sizes and the complete keyboard/race/failure matrix remain unmeasured or unexecuted.

Actual browser defects and corrections are preserved by paired screenshots: overlapping scene messages moved to readable stacked tools; nested React scene-label roots replaced; lower-left orientation overlap corrected; compact context drawer made visible; Analysis status/legend placed in a static stack. A reload and console-display clear followed by normal transitions did not reproduce synchronous-unmount errors. THREE.Clock upstream deprecation remains visible. The current RP1 motor curve is available from exactsource digest e79138a0…; the initial503 was old-backend evidence.

Analysis shows neutral RP1 geometry, scalar failed-screen findings and unavailable installed joint/compatible-spatial-field quantities. The actual exported comparisonCSV has one unavailable row with blank values, preserving unknowns. No compatible spatial field source exists for the unexecuted overlay/difference branches.

The new local execution scope was exactly one Tiny single and one two-member Tiny batch:27,000 declared modelsteps, serial CPU worker/concurrency1. The single completed in12.77s observed submit-to-terminal; the initial180s whole-packet stop was honored at~200s after UI work/compaction with batch unattempted. The primary explicitly replanned that remaining unattempted batch as one separate submission with167.23s execution allowance. Both batch members were terminal by the~27.82s observation bound. This does not turn the original packet stop into a pass. Process CPU time, core affinity and the intended120CPU-s ceiling were not measured. No extra run was made for cancellation/failure. Exact settings/IDs/exports are recorded in the row CSV; all three trajectories are45s partial records, not landing evidence.

The actual older116.029s G80 replay and new45s single demonstrate unequal windows. At58.651s the short actor/readouts are outside their recorded support; the older run remains inside support. Their simulation code identities differ, and quantitative B plots correctly remain withheld. Fresh batch members share code and source, permit real numeric comparison and preserve exact nearest-sample times. Same-seed single/batch comparison reports zero setting differences. Both new runs return3004/9000samples in the bounded profile. Genuine browser CSV/metadata exports retain exact inputs, source/CAD identity, selected range, offsets and timestamps; they are explicitly not full-rate telemetry.

See [browser-results.csv](browser-results.csv) for per-row partial/pass/unavailable coverage. These are actual interaction observations, not blanket completion of compound acceptance rows or engineering/physical/flight acceptance. Screenshot and export files remain unchanged in ignored runs/frontend-browser-20261107.


A subsequent exact-time control integration initially failed a real browser reload with `Uncaught SyntaxError: The requested module /src/experiments/ExactReplayTime.ts does not provide an export named ExactReplayTime` at Experiment.tsx:3:10, followed by the React error-boundary warning. The primary identified a case-insensitive macOS module-basename collision between the component and helper. Exact-time/recovery and full-rate profiling paused pending its correction; this new failure is distinct from the earlier resolved scene-label errors.

The unchanged screenshot/download inventory, dimensions and full SHA-256 digests are in [browser-evidence.json](browser-evidence.json).


## Exact recovery, profiling and failure recovery — completed observations

After the explicit `ExactReplayTime.tsx` import correction, a normal browser Reload succeeded. On sole saved G80 run `exp-cf9e47a650074144856caf50775846d2`, entering 11.150 and pressing Enter produced validity text “requested 11.150 s” and an actual nose-up, tilted vehicle with CG marker after modeled deployment. The separately labelled nearest bounded sample is at 11.143 s: tilt 4.074581992984311° and total speed 5.446069915438504 m/s. Vertical velocity was not displayed; the browser observation does not infer downward speed from total speed. The approximate recovery/suspended-body limitation remains visible. Native range AX reports 11.151 because that slider quantizes its representation; the exact input and pose request remain 11.150. At exact request 116.029 s, nearest endpoint height and speed both display zero, with no impact/contact-force inference.

One saved G54 full-rate attempt used `exp-ab60bd4ac5c2412a9dd85f712072bca2` in the same Chrome window, 1440 × 900 CSS px, 100% browser zoom, 1× playback. It loaded **132,856 / 132,856** native rows over 0.001–132.856 s with matching source. The displayed last load was **2652.4 ms**, including API/identity checks; response Content-Length was **113,412,840 bytes**, distinct from transfer/heap totals. Playback advanced 0.131→6.641 s and paused. Its rolling **600 recent frame intervals** were median **16.70 ms**, p95 **33.20 ms**, maximum **50.00 ms**, mean **17.83 ms**. This measured attempt does not meet a 60 fps requirement. It is not a full-duration real-time endurance pass or a repeated optimization attempt.

One exact 60.000 s full-rate scrub completed in **35.80 ms to the second animation-frame callback**, including scheduling rather than GPU-only completion. Nearest native sample was labelled 60.000 s. Host-reported JavaScript heap was 228,819,354 used / 264,020,494 allocated bytes after load; 214,933,232 / 283,395,348 after playback; 180,765,116 / 287,577,656 after scrub; limit 4,395,630,592 bytes. This nonstandard host estimate is not total process or GPU memory. No zero substitutes for unmeasured memory. The instrumentation scenario still said “bounded playback samples” while the actual profile and count were full-rate; this copy mismatch was reported. Normal bounded playback was restored afterward.

Ordinary Chrome responsive Throttling → Offline caused a saved-run selection to show `TypeError: Failed to fetch` and ERR_INTERNET_DISCONNECTED, including periodic run-library polls. No simulation was submitted. The failed load still said “Loading saved run…” alongside the explicit error; that copy issue was reported. Throttling was restored to **Disabled: No throttling**, and selecting the same saved record loaded it with matching source. This is transport/request recovery, not worker failure or an idempotent submission test.

The primary's explicit development-only `__previewFault=replay-render` fixture was exercised once. The actual shell retained workspace navigation and showed “This workspace could not be displayed” with the intentional display-fixture/no-calculation reason. The visible Reload link removed only the diagnostic flag while preserving AD1, spec, baro and saved-run context; the source-checked replay loaded. Normal Design navigation then preserved the same AD1/spec/baro. This is one controlled render recovery branch, not malformed, missing-source, HTTP 500 or delayed-data coverage. The fixture made no physics or backend-job change.

Current RP1 connections also showed genuinely mapped fin-set selection updating the diagram and URL to `part=fin_set`, with an exact AD1/spec Design target. The successful target click and VP1/study/historical export paths were not established by that observation and remain partial.


## Final bounded packet disposition

After immutable elapsed capture, accepted time-axis caching and profile-specific copy were corrected, the primary explicitly authorized one changed-source follow-up on the same saved G54 data. This loaded the same 132,856 native rows in 2547.4 ms with 113,412,840 response Content-Length bytes. The intended roughly 20 s interval actually took 26.347 s from immediately before native Play click to immediately before Pause; the cursor advanced 0.001→25.49 s at 1×. The rolling 600 intervals were median 16.70 ms, p95 17.70 ms, maximum 34.30 ms, mean 17.50 ms. One 60.000 s scrub took 29.30 ms to the second animation-frame callback. JavaScript heap used/allocated was 231,987,546/266,067,386 bytes after load, 240,596,762/306,745,106 after playback, and 181,922,573/186,652,141 after scrub; limit 4,395,630,592. This improved profile still misses 60 fps, so performance work stopped without a third attempt or threshold change.

Actual Side captures exposed a mirrored screen-right basis in asymmetric fitting. The primary corrected it and supplied a visible magenta framing-area guide from the same inset helper; no fit threshold or geometry changed. With Side and an explicit current-viewport Fit, screenshot-derived measurements were: 1440 default guide height 83.03% with at least 8.28% vertical clearance, and true 1280 × 720 default 83.25% with at least 8.14% (conservative 7.63%) clearance. Default canvas ratios were 78.26% width/86.89% height at 1440 and 75.55%/83.61% at 1280. These measurements come from genuine unchanged captures, not camera-math substitution. Focus captures show both columns absent and tools closed; the true 1280 Focus capture has guide off after a workspace remount and is used only for its visible layout.

The prior valid 720 resize-transition capture is retained: its manually retained camera gave 90.92% guide height and only 4.13% bottom clearance before the explicit current-viewport Fit. Original files labelled guide-fixed-1280x720 were actually 2560 × 1800 rasters (1280 × 900) and remain unchanged with explicit mis-sized copies. One supposed Focus capture was visually caught with Details still open and is preserved as a failed interaction. Only the distinct `...1280x720-refit.png` default and Focus files establish the final required-size states.

Baro was genuinely selected, isolated (54/55 hidden) and framed (1/1 bounds) with visible guide; its silhouette measured 78.31% of guide height with at least 10.84% clearance. The optional selected-part annotation covers its center, so the annotated capture is retained and the requested clean-label companion remains pending. Restore assembly subsequently showed 26/26 bounds and zero hidden parts.

Mapped fin-set and recovery-wrap Design→Engineering→Design roundtrips retained exact AD1/spec/part identity; Engineering selected the applicable fin-panel or recovery route. FP1 graph zoom/reset and SVG download worked, preserving UNACCEPTED/not-adopted, units and source hashes. VP1 S1 selection worked, all five inquiry labels remained UNSENT, and Aircraft Spruce preview/download/copy retained exact frozen SHA-256 `2394f0420a038494c2da526516022a930f296d4d7983ac5c9bd8018ffcafe537`; local feedback explicitly said “Still UNSENT”. The separate historical G80-F1 view correctly disclosed no same-design detailed CAD. No supplier/lab message was sent.

Native control then returned “The user changed /Applications/Google Chrome.app. Re-query the latest state with get_app_state before sending more actions” twice during short keyboard steps. The verifier honored the guard, re-queried supported state and found focus in the native DevTools Console prompt; that does not establish a free window. CUA work was yielded to avoid stale-state input. The clean-label baro companion, final G54/G12-finned/finless configuration-switch matrix, and final owner-ready restoration remain explicitly unexecuted. No console code, workaround, new app/window or new simulation followed. Last confirmed normal transport was No throttling and bounded replay paused before subsequent Design work; interrupted final resizing had Width 1440 with Height auto/empty, so no new screenshot is claimed as 1440 × 900 after that interruption.

`runs/frontend-browser-20261107/record.json` now preserves the initial old-backend baseline as historical and records fresh source identity, scenarios, exact runs/resources, both failed performance profiles and capture dispositions. The artifact hash inventory was regenerated after that session-record update. Final source fingerprints/publication attribution belong to the primary; this record does not claim an unpublished local head was merged.
