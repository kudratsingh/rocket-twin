# First design-workbench v2 implementation

The [full plan](../../frontend-design-workbench-v2/README.md) was completed before
implementation and published through PR119. This first vertical slice implements
a read-only Parts bank inside Design and improves the existing PCB inspection
controls. It does not implement Add/Replace/Connect or full candidate building;
those remain in phase P5 and its dependent checks.

## Open it

Start from the repository root with `make preview`, then open
<http://127.0.0.1:5173/>. With G80 RP1/AD1 v2 selected, choose **Parts bank** in the
header. The large dialog keeps the assembly mounted behind it. Search/filter,
select a catalog entry, read its function/material/nominal dimensions/source mass,
installed station, geometry maturity, issues and source-budget cost. **Inspect
installed part** returns to the exact Design part and opens its Details.

If the already-running API lacks the new route, only an actual404 admits the
explicitly labeled prepared source snapshot from the same Python catalog builder.
Any source failure, stale record or non404 error remains an error, not a historical
fallback. `make parts-bank` prepares that snapshot without CAD or flight work.
Restarting the normal-terminal preview loads the new live API routes. The
prepared-path native observation and in-process API tests are separate evidence.

## Source and accounting

The frozen RP1/spec/AD1/record tuple is unchanged. There are55 source definitions
and55 installed occurrences, each with its own stable identity/revision. An
occurrence has one accounting quantity; fin count is group metadata, not a reason
to multiply the source fin-set mass/price. Display children and distributed
allowances do not add new BOM lines. No physical mass, CG, inertia or geometry was
recomputed or adopted.

The current catalog has26 verified installed-reference meshes. These are globally
placed RP1 inspection assets: `reusable_local_geometry:false`, their viewer frame
and registered instance are explicit. They cannot be dropped into a new assembly
as if they were native local product CAD. Future templates/interfaces remain a
separate task. Source-only test fixtures correctly contain no available meshes.

Retainer19002/009750, tube dimensions/legacy notes, controller identity and PCB
source limits remain visible. Prices are source group budgets, not verified unit
quotes; zero budgets never mean free hardware or confirmed owner stock. All
physical verification and engineering acceptance remain open.

## Checks and observation boundaries

- Backend/source/export: seven focused cases, plus two actual FastAPI TestClient
  cases for list/detail/group accounting, unknownIDs, deniedPOST and source-drift
  rejection. No live owner service or physics solve is started by these tests.
- Client: four actual-source admission/filter/transport/SSR cases, strict55-way
  definition/instance/source/geometry/frame/conflict checks and read-only states.
- Existing archive preparation initially failed on the broadened API file hash;
  [the narrow compatibility correction](catalog-compatibility.md) preserves all
  original registry/assets and adds four focused cases. The six affected archived
  CAD web cases then pass.
- The corrected combined local run passes333 web cases (four unrelated preserved
  A2 cases are excluded from this publication;329 in scope) and13 focused Python
  cases. Ruff/Black/mypy, TypeScript/lint/format/build pass. After the observed
  detail-pane correction and ruler-label spacing adjustment, seven affected web
  cases plus type/lint/build pass again. Required hosted results apply only to
  the final publication head; no earlier green head is substituted.
- New native bank and PCB control observations are recorded separately. This
  document does not convert a source fixture or SSR render into browser acceptance.

All inquiries remain UNSENT. G80 custom construction/practical performance and
G54/G12 PID-to-RL remain committed. D1, stopped solver limits, separate50g growth,
20g adverse/motor probe,55/68g harness,1.5m/15formal/15.5planning and all physical,
thermal/recovery/flutter, WO-10 and flight gates remain unchanged.

## Actual bank observations

The first P60 attempt stopped on a verifier evidence-helper binding failure before
any feature could be verified; it remains a failed tool attempt, not an app pass.
A separate supported zero-input restoration confirmed the Chrome/filesystem
handles and finite cutoff clock. P61 then loaded55 definitions/occurrences via
the prepared snapshot, searched the retainer, showed source budget and installed
reference limits, and returned from forward_ring to its exact settled Design
URL/spec/part with rendered geometry. The retainer conflict existed in AX but
stayed below the captured fold; the next selection retained the prior scroll.

One focused correction moved existing warnings immediately below the heading
and keyed the detail pane by selected definition. P62 actual images verify the
19002/009750 conflict visibly at the top, a real detail scroll followed by
forward-ring heading/action restored at the top, and Return to rocket retaining
forward_ring Details. Heading−309.2°/tilt61.5° remained; normal selection changed
the subsystem/target, so complete visibility/camera-state preservation is not
claimed. Category-dropdown, wider keyboard/error and archive-bank branches were
not all exercised.

- [P60 tool failure](../frontend-parts-bank-native-20261109/browser.md)
- [P61 actual catalog and exact-part return](../frontend-parts-bank-corrected-native-20261109/browser.md)
- [P62 visible warnings and scroll reset](../frontend-parts-bank-visibility-native-20261109/browser.md)

P1 remains in progress overall: true reusable local template/interface admission
is not supplied by this installed-reference catalog. Future draft authoring,
candidate resolution, full detailed CAD and engineering acceptance are not
claimed by this first usable source-bank increment.

## PCB controls observed after integration

P63 actual images show readable source XY rulers, exact25.4/17.78mm endpoints,
top-only gold routes, bottom-only purple routes and corresponding face checkbox
states. Reset restores both layers, All nets and the default oblique view. The
reference deliberately defaults to U1; the packet's initial expectation of
clearing selection was incorrect, and no selection-clear pass is claimed. Optional
changed-footprint/net actions were not exercised. Some fine-silk artwork extends
outside the board and clips at the canvas boundary; that limitation stays visible
and does not establish physical silkscreen placement or populated package height.
[P63 actual observations](../frontend-pcb-controls-native-20261109/browser.md).

Closing left exact high_g_accel Details in the Avionics/power group, with main
heading−309.2°/tilt61.5° retained. Normal source selection changed target/group;
no full visibility or complete camera-pose preservation claim is made. The browser
lane is idle. The screenshot walkthrough is an offline artifact, not extra live
interaction acceptance.

## Remaining P1 coverage

The current client admission expects the matching loaded RP1 inspection identity.
The backend/source-only fixture supports zero optional meshes, but a true
source-only viewer with no inspection-geometry identity is not yet an admitted
client startup path. Broader bank operation without prepared CAD, all category
dropdowns and native error/keyboard branches remain P1/P9 work. This is a scoped
current-asset release, not a claim that every fresh-machine/data-missing branch
is complete.
