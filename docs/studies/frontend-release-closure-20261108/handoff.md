# Frontend release handoff — November 8, 2026

The preview supports read-only RP1 Design/Engineering, compatible archived experiments, saved-run replay/comparison/export and recorded Analysis. It is not complete frontend acceptance or engineering/build/flight approval. This handoff summarizes recorded source and runtime evidence; full acceptance remains open.

**Publication checkpoint:** PR105–108 are merged. PR108 final head `8f6c02a65d5f0d58187c138d211c1e718ce80e63` passed both required jobs/workflow42489804785; main at camera-packet intake is `47bc74a12b6d186bf8a9b68ef6e7ad45f044410a`. The separately scoped camera correction follows its own required-check PR. Code/native observations never imply full engineering or frontend/work-order acceptance.

## Open and use

From the normal host terminal, with the existing pinned environment:

```sh
cd /Users/kudratsingh/Machine-Learning-Projects/rocket-twin
make preview
```

Start at [RP1 Design](http://127.0.0.1:5173/?workspace=design&design=G80-F2-RP1-AD1-definition-v2). This is the normal local URL, not a claim that this documentation task started or checked the host.

| Workspace | Usable path and evidence boundary |
| --- | --- |
| Design | Current `G80-F2-RP1-AD1-definition-v2`: **55 source records / 26 mesh-bearing records**, with six functional groups and explicit display maturity. Meshless allowances/envelopes remain records; missing hardware detail is unavailable. Independent navigation/parts panels, Move/Rotate/zoom, Fit/Frame/Reset, staged Breakdown and contextual construction previews have scoped current-window observations. Display offsets and previews do not establish physical fit, assembly sequence or an adopted fin alternative. |
| Engineering | Select a mapped fin-root or recovery part, then **Open matching Engineering connections and findings**; return through the exact AD1 part link. Direct entry: [RP1 connections](http://127.0.0.1:5173/?workspace=engineering&view=rp1-connections). Links carry source/part identities. Unmapped relationships and installed-joint properties remain unavailable; source parentage is not proof of physical attachment. |
| Experiments / Flight Replay | Choose an existing complete compatible archived configuration, then load a saved run. Design and experiment selection have separate URL state. [Saved G80 replay](http://127.0.0.1:5173/?workspace=replay&design=G80-F2-RP1-AD1-definition-v2&experiment=modular-performance-v1&run=exp-cf9e47a650074144856caf50775846d2) supports exact-time entry including 11.150 s; matching archive CAD is admitted only for its own run. RP1 cannot borrow that actor or flight prediction. |
| Comparison / export | P3 compared `exp-d0baf4168f7f41e687a1b5f12e14cc3e` with `exp-d57656d638d5412d95b03198e9fb73d7`, disclosed seed differences, aligned both at saved burnout 1.8079 s and exported **1500 original recorded samples** plus identity/range metadata. Native timestamps were preserved inside the selected aligned range. Normal bounded payload, opt-in native full-rate payload and bounded drawing are separately labelled. Raw selected-profile telemetry remains authoritative for pose, readouts, metrics and exports. |
| Analysis | [RP1 Analysis](http://127.0.0.1:5173/?workspace=analysis&design=G80-F2-RP1-AD1-definition-v2) shows recorded scalar findings: optimistic **7.301 MPa FAILED SCREEN**, **1.805 mm** component movement versus retained **1 mm**. Installed movement/peel/finished recovery capacity and compatible spatial stress/deformation/temperature maps remain unavailable. P4 observed the corrected full neutral rocket and functional groups; no invented field or archived baffle was attached. |

Frozen RP1 specification is `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`; inspection geometry is `238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`. Inspection geometry is not complete manufacturing CAD or qualified mass/inertia/aerodynamics.

## Completed scoped observations and remaining cases

- [P1/ledger closeout](ledger-reconciliation.md): contextual fin return, PCB dialog correction, direct camera controls and named interior/detail/alternative slices; RV-Q42–45 close only at their prescribed mixed source/native scope.
- [P3 saved workflows](../frontend-saved-workflows-20261108/browser.md): existing batch observation/metadata export, aligned comparison/range CSV, event-linked recovery explanation, missing-run 404 and recovery. FT027's schematic uses saved event markers; canopy/line/section dynamics remain unavailable and recorded 3D attitude is unchanged.
- [P4 correction](../frontend-final-checks-20261108/browser.md): whole neutral RP1 Analysis and groups visible after the earlier clipped-tip failure; one declared two-member archived-G80 Tiny batch completed both 9000-row members. Cancellation is **inconclusive**: the native click expired before any HTTP acknowledgement; no termination or retry is claimed.
- **Responsive/keyboard:** [P5 stopped at entry](../frontend-responsive-1440-20261108/browser.md): actual content remained **1965×1074 CSS px / DPR 2**, not requested 1440×900. Dependent responsive cases were unexecuted. The same-window actual-size prerequisite remains; unsupported setters/DevTools are not retried. Full keyboard and listed fault/malformed/delayed/worker-failure branches remain partial or unexecuted.
- **Performance:** [P2](../frontend-replay-drawing-20261108/browser.md) loaded the exact saved G54 native fixture with **132856 rows / 1006 drawn trail positions**. Its 600-RAF mean **16.6676667 ms** exceeds the unchanged 60 fps interval target; the scene was offscreen during relevant captures. It is diagnostic-only. Both earlier failures remain failed. Later visible diagnostic controls were not followed by another measurement; bounded source-work counts are not browser FPS, GPU timing or memory/endurance acceptance.


## Current window and remaining gates

Owner-authorized native Window→Zoom resized the same window from1965×1074 to2240×1109CSS/DPR2. No exact bounds entry was available; prescribed sizes remain pending. See [resize evidence](../frontend-owner-resize-20261108/browser.md). Independent current-window checks may proceed through the sole designated owner; no DevTools or other-window bypass.

G80 RP1/AD1 v2 remains preliminary. G54 and G12 PID-to-RL are separate committed tracks. All five inquiries remain UNSENT. No purchases, physical work, supplier/lab contact or engineering/build/flight approval follows from frontend publication.

## Latest inspected correction

[P6](../frontend-current-functional-20261108/browser.md) verifies actual nose and separated-motor picks, Motor/Recovery stage displays, restored zero, target selection and keyboard pan at2240×1109CSS. The collapsed invalid-link warning failure remains recorded. [P7](../frontend-part-link-recovery-20261108/browser.md) verifies its one correction: visible warning plus Clear invalid part link, exact-source recovery and new valid part selection. Final fresh wholeRP1view has26/26, Move on, both panels/Parts and Frame disabled. That correction is merged as PR107 after required hosted jobs passed.

Actual local images: [Motor breakdown](../../../runs/frontend-current-functional-20261108/motor-breakdown.jpg), [Recovery breakdown](../../../runs/frontend-current-functional-20261108/recovery-breakdown.jpg), [corrected whole Analysis](../../../runs/frontend-final-checks-20261108/analysis-initial.jpg). These are genuine native captures at their recorded window/source; offline image viewing is separate from browser interaction evidence.

## Scene + telemetry

The [layout increment](../frontend-replay-layout-20261108/integration.md) puts the scene/timecontrols beside four plots at a wide centre. [P8](../frontend-replay-layout-20261108/browser.md) verifies actual wide readability and explicit state retention across2240→1120→2240CSS. Full lower narrow-scroll coverage and numeric free-camera pose remain unverified. [Actual wide capture](../../../runs/frontend-replay-layout-20261108/wide-initial.jpg).

[P9](../frontend-replay-unequal-windows-20261108/browser.md) verifies G80/G54 admission and both-valid100s, but native input did not establish125. Final restore exceeded260s by3.484s; budgetFAIL is retained. The copy-only clock fix has live AX/core confirmation. No outside-A/inside-B or FPS pass. The subsequent owner-assisted P10 resolves the applied125 clock/readout branch; CUA is idle.

[P10](../frontend-replay-manual-boundary-20261108/browser.md) independently observes owner-entered125: A outside116.029/all four readouts unavailable, B inside132.856/recorded125.014 values. This is status/scalar evidence, not independent body-pixel proof. The comparison is preserved paused at125 for owner review, with no further action needed for this increment's publication.

## Following the continuing comparison

[Camera follow](../frontend-replay-follow-20261108/integration.md) now selects only available recorded positions. At125, Auto follows B because A ended; explicit A holds with the source reason, B follows B and Free is independent. [P12](../frontend-replay-camera-buttons-20261108/browser.md) verifies all four buttons and an identifiable B rocket in fresh new-source images. [Actual final capture](../../../runs/frontend-replay-camera-buttons-20261108/final-auto-b.jpg). Source poses/time/readouts are unchanged. Fit is A-only. Fixed pad/missing B branch and full acceptance remain open.

PR108 is merged after both required checks at47bc74a12b6d186bf8a9b68ef6e7ad45f044410a; this camera increment follows through its own required-check PR. The app is left at the owner's paused125 comparison, Auto B, rather than resetting their review to Design.
