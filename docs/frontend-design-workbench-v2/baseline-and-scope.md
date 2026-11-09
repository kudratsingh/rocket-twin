# Baseline, authority and scope

## Exact starting checkpoint

Remote main was refreshed on November 9, 2026:
`38e70be0d2df59c81e2d6cb52b97d4b58444496f`. PR118 is merged; its final head
`515cecd1378826c9fd852257fd4e9be7da27a18a` passed workflow42587975052 and both
required jobs. The earlier formatting failure remains historical. Local source
has preserved unrelated A2 work and two interrupted PCB control files; exclude
these from publication until their owner completes and verifies them.

| Source/feature | Current state | Consequence for this revamp |
|---|---|---|
| Frozen RP1 | `G80-F2-RP1-AD1-definition-v2`; spec SHA `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660` | Never overwrite it with library or draft changes |
| AD1 definition / saved evidence | Pinned by `src/api/rp1_inspection.py`; 55 stable IDs | Preserve exact links, unknowns and recorded mass cases |
| Core display geometry | SHA `238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`; 26 mesh-bearing records:10 source-dimensioned,16 envelopes;25 allowances,4 missing | Detail work extends source coverage, not inferred physical qualification |
| Mechanical close-up | 18 source child assets from7 parent records; catalog SHA `1044bc7aeacad0802fe74add1fecbc77aeddcd0ed09f493c685bb639d271eda1` | Children are representation features, not extra mass lines |
| Adafruit5374 reference | Pinned Eagle XY:26 placements,82 pads,208 routes,26 vias,14 nets | Detailed planar reference; populated heights/mounting remain unavailable |
| Design/Engineering | Inspection, section, explode, part evidence, CAD exports and linked drawings exist | Reuse; do not rebuild the application shell |
| Experiments/replay | Existing Python/JAX requests, saved runs, comparisons, pose checks and exports | Retain exact vehicle/run pairing; RP1 full inertia is unavailable |
| Analysis | Recorded RP1 scalar findings; no compatible current spatial fields | Show findings now; never color a current mesh using an old study |
| Native evidence | P57 PCB graphic passes; P59 opening/tab/separation/Fit observed; half-shell edge proof partial | New interactions need fresh scoped verification |
| Legacy ledgers |29 RV tasks,43 FT tasks,47 acceptance rows at intake | Keep their IDs, statuses and linked failures |
| Source gaps | Retainer19002/009750 identity, tube note/dimension mismatch, unresolved recovery product, installed electronics details | Catalog conflicts block reuse as verified hardware; no invented precision |

Current source opportunities and pins are in
[the bounded packet](../studies/frontend-component-depth-next-20261109/source-opportunities.md).
The interrupted PCB edits are described in its [handoff](../studies/frontend-component-depth-next-20261109/pcb-controls.md);
they are **code-only and unverified**, not part of the accepted baseline.

## What the owner has now authorized

Detailed inspection/CAD presentation, source-owned parts-bank development,
reversible local draft composition, backend previews and supported alternative
experiments under the existing workflow. This is an explicit narrow extension of
CLAUDE's viewer-only rule: the browser may author a **draft specification through
validated controls**, while CAD and physical calculations remain in Python.
It may not silently mutate a frozen source, run arbitrary uploaded code, substitute
an archived vehicle, or make purchases/contact suppliers.

A draft's model readiness is independent of engineering acceptance. It may be
saveable and inspectable while fit, loads or full inertia remain missing. It may
run a flight only when its complete supported simulator contract is satisfied.
The user can inspect current RP1 while archived G80 uses only its own saved runs.

## Retained requirements

D1's8.83 N·m/331.125 N once-factored fin envelope,1mm movement, estimated material
screens, full separate50g growth, separate20g aft/motor probe and55/68g uncertain
harness cases remain. Keep1.5m usable guide,15m/s formal and15.5m/s planning
separate. Longer equipment remains conditional. Preserve stopped FR1/FP1 and
other candidates as unadopted/historical; no new fin variant or detailed FEA is
admitted by this frontend plan.

WO-03 structural/thermal/recovery/fit/flutter requirements, the unchanged45°C
thermal screen, prototype/physical testing, purchases, paid runs, WO-10 review and
flight release remain open and separately authorized. G80 custom fabrication and
practical performance, G54 upgrade and committed G12 PID-to-RL remain in the plan.

Digital-only orbital-launcher work and extension interfaces remain assigned to
WO-05b and later G-FOLD work. Future digital-scale library/assembly records need
their own class/frame validation; physical model-rocket limits and flight-release
claims must not be transferred to that separate simulation. This revamp neither
removes nor prematurely implements those milestones.
