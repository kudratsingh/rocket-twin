# Comparison camera target — bounded integration

Published intake is merged PR108/main47bc74a12b6d186bf8a9b68ef6e7ad45f044410a. This follow-up changes camera presentation only; G80 RP1/AD1 v2, archived run identities, JAX physics, pose/CG transforms and engineering evidence are unchanged. G54 and G12 PID-to-RL stay committed separately; all five inquiries remain UNSENT. No purchases, contact, physical work, paid runs or build/flight release.

## Decision and executed source packet

At the owner-assisted125-second comparison, A has no recording beyond116.029s while B continues to132.856s. Source inspection showed the old Follow camera targeted A only, so B could leave the view despite valid data. Do not infer a missing actor from the earlier trail-only pixels.

One35-minute source packet plus one targeted control correction selects only finite existing recorded positions. Auto follows A while available, then B; forced A/B never substitutes another run. With no chosen position, the camera holds with a reason. Valid position markers can be followed without inventing attitude. Pad/free remain independent. A visible view-only label names the target or held reason. The original ReplayCamera motion algorithm, FlightGeometry and MeshPart ASTs are unchanged; all66 Experiment hook names/order/runtime arguments remain unchanged. [Source preservation](preservation.json). No hooks/dependencies/pose interpolation/raw values/time/alignment/range/export changes.

The old numeric Fit action bounds only A. Both controls now honestly say Fit A trajectory. Combined A/B fitting is not implemented or inferred. No new fit algorithm or graphics engine was introduced.

| Finding | Correction / criterion | Evidence and result | Remaining scope |
| --- | --- | --- | --- |
| Follow A had no target after A ended, while B remained valid | Auto may choose only available A/B positions; expose source and reason | P11 actual B body visible along gold trail at125 with fallback label; P12 confirms final source | No physical/flight validation |
| Native popup selection did not establish A/B/Free modes | One correction replaces the popup with visible labelled pressed-state buttons | P12 one-click A-only held reason, B-only visible B body, Free no-follow, Auto B restored; time125/readouts unchanged | Fixed pad and B-disabled-without-comparison not natively exercised |
| P11 final capture overran150s by2.599s | Future native calls stop by90s inside120s overall; check remaining reserve before each call | P12 ends48.382s with all four required cases, no extra calls | P9/P11 overrun records remain failures |
| Camera source must not alter actor data | Existing geometry/pose/time functions and bindings remain | Four independent helper tests and source comparison; actual P12 unchanged scalar windows | Numeric orbit/pivot retention is not measured |

P11's popup branch remains unexecuted and budgetFAIL; it is not retroactively passed by P12. P12 is a separate new-source targeted check. No input, Play, resize, simulation, native-rate profile or FPS attempt was used. The owner comparison remains paused at125 with Auto tracking B. [P11](browser.md) · [P12](../frontend-replay-camera-buttons-20261108/browser.md).

Final local241tests, type/lint/format/package build pass. Four preserved/unpublished A2 cases are excluded, leaving237 in publication scope. Existing large-bundle warning remains. Unit fixtures are known-answer display tests, not measured flight evidence. Source hashes and actual native image provenance are recorded per packet; raw images/AX remain local, small records/inventories are published. Required hosted jobs must pass at this focused PR's exact head before merge.

## Acceptance limits

This closes the scoped follow-camera/explicit-button usability issue. It does not close exact1440/1280/900 viewport coverage, full lower stacked-plot reachability, acknowledged cancellation, native invalid-data/fault branches, representative60fps performance, missing geometry/spatial fields, WO03/04/05/10 or physical/thermal/recovery/flutter/flight gates. No further automatic correction or native retry is admitted by this packet.
