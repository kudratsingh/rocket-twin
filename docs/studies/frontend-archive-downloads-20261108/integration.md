# Recorded CAD access across desktop configurations

This follow-up to merged PR115 preserves frozen RP1/AD1/D1 and adds source-bound
file access for the four archived configurations. No vehicle, geometry, mass,
inertia, motor, solver or engineering acceptance changes.

## Usable source capabilities

Details → 3D geometry files now has a file-scope control: selected component or
whole rocket assembly. This affects only requested files; selection/camera stay
unchanged. RP1 retains its separate GLB/inspection-STEP registry. A lazy component
loads the archived registry only for other designs, avoiding its data cost in the
initial RP1 path. Unknown/incompatible sources remain unavailable.

The archive registry pins572 existing assets/54,892,740bytes across G80 reference42,
G54 hypothesis42, G12 finned53 and finless51 part records. Part GLB/STEP/STL and
assembly GLB/STEP exist; no assembly STL. Strict admission checks the exact resolved
specification, CAD revision, complete part inventory/shape/input maps and current
part object. Downloads verify registered response bytes before saving; no generic
unrestricted endpoint or CAD regeneration is added.

Formats remain distinct: GLB is placed viewer geometry in metres; legacy part STEP
is local CAD millimetres before assembly placement; assembly STEP is assembled
millimetres. STL stores triangles without units; the recorded producer used CAD
millimetres and may have applied print orientation/bed packing. This is not a new
STEP readback, qualified print pack or manufactured hardware. Existing archived,
conditional and finless unsupported-flight statuses stay visible.

`make workbench-archived-cad` verifies and copies existing registered local bytes;
normal `make preview`/Python backend remain unchanged. Preparation staged576 files
(572 assets plus four provenance copies) after checking source identities/hashes;
no backend restart was needed. Missing local files/hash changes fail preparation,
and missing optional browser downloads report unavailable. Generated bulk stays
ignored and out of Git.

## Evidence and remaining native work

The [archive audit](../frontend-desktop-detail-20261108/archived-cad-access.md)
and registry pin existing bytes, with no new geometry/physics calculation.
An independent [actual API contract check](../frontend-desktop-detail-20261108/archive-api-contract.json)
used real FastAPI TestClient responses:8/8 assembly/part admissions across all four
configurations, in1.884s wall/1.571CPU. This is separate from native browser work.

P38 separately observed a625mm transverse cut/opposite-side display flip on RP1.
P39 preserved a real recovery-notice layout failure: a global flex notice style
squeezed heading/paragraphs into columns. P40 verified the scoped display:block
correction and wrapped source paths/locators, then restored whole RP1. The source
notice leaves Apogee/EasyMini identity unresolved and does not modify the frozen
source or generic export eligibility.

P41 showed available archived file controls with the right format/frame caveats,
but its verifier required a sentence the component never promised. It stopped
before downloads. This is an orchestration-copy failure, not an app identity
mismatch or a completed download. The follow-up native download case must use
actual source/controls/registered bytes, not add that sentence to obtain a pass.

Four recovery-finding and six archived-access tests pass; full integration checks
and source fingerprints are recorded separately. Actual generated-byte tests skip
explicitly on fresh hosts without optional files. All source tests use tracked
registries rather than assuming generated public metadata. P39/P41 remain
immutable, and new native cases remain pending until observed.

No physical requirement closes from file access or source notices. All five
supplier/lab inquiries remain UNSENT. G80 first, substantial custom construction,
G54 and G12 PID-to-RL, engineering/thermal/recovery/flutter, WO-10, physical build
and flight gates remain intact. Mobile/exact-pixel polish remains secondary.

## Completed scoped native observations

P40 independently verifies the recovery source notice's corrected vertical layout
and wrapped locators, preserving P39's actual failure. P42 verifies selected-part
versus whole-assembly file scope without changing the nose selection/source/view;
it downloads G80 assembly STEP and provenance. The primary verified the fresh
3,170,614byte STEP SHA68b40b0e3f4fee92a3d3a9c5058340a200817e95ebb6e2af07ed870bdd13ff60
and414,370byte provenance SHAcd3cc2557c61df5f051fbc5a48002ef62678831e1639379364a19ead6398f49f.
[Download evidence](download-verification.json).

P43 separately shows actual G54 conditional42, finnedG12 trainer53 and finlessG12
concept51 record models, file controls and format/status labels. It does not
download all three or run their simulations. Finless flight remains unsupported;
no physical stability or control acceptance follows from its rendered geometry.

Final integrated311local tests/type/lint/format/build pass; four unrelatedA2 tests
are excluded from publication. Pure tests use tracked registries. Actual optional
CAD-byte and preparation tests are explicitly skipped on fresh hosts without those
local files; their local verification remains separate. The existing large-chunk
warning remains; archived registry is loaded lazily. Required hosted checks must
pass at this follow-up's exact head before routine merge.
