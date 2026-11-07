# Frontend release: supported access findings and browser protocol

**Current blocker:** owner consent and the named verifier are resolved. The supported inventory returned **“The browser access host is unavailable”**. Chrome running does not expose a browser tab. The original ownership investigation below is historical; do not use it to ask for the same consent again. Normal-host preview startup and live browser checks remain pending.

Date: 2026-11-07. This records bounded access research, the subsequently
owner-authorized first discovery call, and an unexecuted verification protocol.
No browser tab, native application, headless/CDP path, sandbox escalation or
preview startup was used. It does not establish browser access, a running host
preview or browser acceptance.

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

## Earliest required owner/provider action

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
approval rejection. No native Chrome app, alternative runtime, reconnect, retry
or other route was attempted. Browser access is now blocked by the unavailable
browser access host, despite the newly explicit owner authorization. The next
provider/owner action is to make the supported Chrome browser access host
available and expose the permitted existing window/tab. The available evidence
does not establish an exact repair setting or command. Browser rows remain
blocked, with this new concrete prerequisite replacing uncertainty about consent.

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

## Grouped live-browser protocol — pending

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

Final release-ledger disposition: all37rows remain traceable. Twelveoffline rows
have source evidence;24access/browser rows are blocked by runtime (with compatible
field data additionally missing for covered-field visual paths); optional
Mission ControlRV-Q35 is not applicable because RV-17 is explicitly deferred.
This supersedes the initial pre-disposition count of25blocked rows; it does not
turn any unobserved browser check into a pass.
