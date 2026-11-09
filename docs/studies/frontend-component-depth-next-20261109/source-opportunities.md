# Next source detail and first parts-bank slice

**Add AD1 recovery-passage source guides to the existing tube/ring close-up, then reuse those exact source definitions as the first parts-bank slice.** The current data support station, passage and reservation graphics. They do not define another finished hardware solid. This packet adds no implementation, geometry or engineering adoption. The [machine-readable packet](source-opportunities.json) records exact source hashes, fields, proposed scope and remaining gaps.

The local primary handoff records PR118 merged after both required jobs/workflow42587975052 succeeded, head `515cecd1378826c9fd852257fd4e9be7da27a18a`, merged main `38e70be0d2df59c81e2d6cb52b97d4b58444496f`. This is attribution to `.cache/component-depth-handoff.json`, not a new remote verification. The existing18 mechanical children and manufacturer PCB layers remain the baseline. Frozen RP1 specification `811b3bed…1660`, AD1 definition `e9db49f2…2555`, core geometry `238d01e5…b608` and all55 IDs match the recorded source pins.

## One addition ready from current data

In **Recovery passage**, keep the existing forward-ring/tube assets and add selectable dimension brackets and source callouts. This explains where the proposed wrap, passage, knot reservation and protective sleeve belong without depicting an invented cord. Values below come from [AD1 v2](../../../configs/studies/rp1-attachment-definition-v2.yaml), `route` and `cord.kevlar`.

| Reference | Source value, mm aft of nose | Viewer Y, metres | Honest graphic |
|---|---|---|---|
| Forward ring |1060–1072.2|.1900–.1778|Existing notched annulus and station bracket|
| Proposed wrap band |1072.2–1077|.1778–.1730|Axial bracket alongside existing tube; no cord wall/thickness|
| Proposed sleeve interval |980–1060, length80|.2700–.1900|Separate axial bracket ending ahead of ring|
| Knot axial reservation |1077–1127|.1730–.1230|Bracket and explicit reservation label; no dressed-knot mesh|

The passage is **4.5mm wide ×5mm radial depth at60° from the first fin**. Ring bore is31.9mm; tube OD31.369mm. Sleeve minimum flat internal width is8mm, explicitly ending before the4.5mm passage; no fit claim follows from those different measurements. Proposed cord maximum diameter3.8mm and knot radial reservation16.5–30.5mm are proposals, not measured dimensions. The proposed2mm edge roundover remains omitted because edge selection/blend termination is undefined. Existing ring notch and source station data are already useful without adding that radius.

Register azimuth against the **actual existing notch** and its source rotation. The producer's exact CAD-mm → viewer-m conversion is `[CAD_x/1000, 1.25−CAD_z/1000, CAD_y/1000]` in [assembly.py](../../../src/cad/assembly.py), `mesh`; do not derive a new rotation from an informal body-axis label. Do not apply display offsets twice. Exclude source guides from material/fit conclusions and label them **source proposals/reservations**. Preserve parent selection and close-up camera on return.

The new capability is inspection of the documented construction intervals relative to actual ring/tube geometry. The existing [AD1 connection diagram](../../wo04-rp1-connections-20261107.md) supplies relationship context; this increment adds spatial datum registration, not another disconnected diagram. One bounded implementation/correction slice is plausibly20minutes using existing assets; that is a planning estimate, with no export, dependency or solver required. Primary retains implementation and acceptance decisions.

## Why the other hardware is not ready

| Target | Existing source/model | Exact blocker |
|---|---|---|
|`motor_retainer`|Nominal45mm long, OD44.4/ID28mm annular envelope|Frozen `learn` names **AeroTech19002**, but `engineering.function` names **Estes009750**. Resolve product/revision correspondence, then obtain controlled cap/collar bore/depth, thread/engagement, lip/seat/thrust-ring/nozzle dimensions and tolerances. Collected19002 family compatibility is insufficient.|
|`motor_tube`|Current source165mm cut, OD31.369/ID29.169, wall1.1mm; `learn` identifies12912/305mm stock|Historical build/CAD/service notes still name1.140in ID/1.210in OD mount-kit dimensions. Keep the exact current shape as a source template; do not silently reconcile notes or claim actual supplier correspondence/fit.|
|`avionics_sled`|90×30×2mm **distributed allowance**, described as a removable two-rail carrier|Rail profiles/spacing/supports, holes/fasteners, actual board registration and populated height/connector stack are absent. Adafruit5374 XY holes/layers already exist separately; they do not define sled hardware.|
|`independent_recovery`|Generic envelope|**Eggtimer Apogee versus EasyMini v3.0 remains unresolved.** Neither product's hole pattern or revision can populate the installed record.|

These facts are in frozen [RP1 parts](../../../configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml), `parts[id=…]`, and the already-collected [manufacturer source report](../frontend-desktop-detail-20261108/next-detail-sources.md). Historical M3 retention dimensions in `configs/studies/wo03-g80-retention-hardware.yaml` belong to source identity `62e8de9e…`, not RP1; their detail cannot fill these gaps.

## Evidence-aware parts bank for phase1

Keep **library definitions** separate from **installed instances**. A library definition owns its immutable revision, product identity, source/locator/hash/licence, native frame, dimension basis, asset hashes, maturity and named interfaces. An installed instance owns the existing part ID, configuration/spec/definition/core tuple, quantity, placement, cut/preparation and connection evidence. The18 detail children remain representation pieces of parent IDs, not18 extra BOM items. Changed assemblies must have separate draft lineage; frozen RP1 stays intact.

Use explicit categories rather than a single “CAD available” badge:

- **Manufacturer document features:** licensed Adafruit XY, with unknown heights and U1 discrepancy retained.
- **Source-dimensioned template:** current tube/ring dimensions and existing meshes, with per-part maturity preserved; source-defined does not mean manufactured or qualified.
- **Nominal envelope:** retainer/controller/eye packaging context; no invented contact surfaces.
- **Missing geometry:** cord/guide hardware; source callouts without stale budget-box solids.
- **Distributed allowance:** bonds/carrier/sleeve budgets; no unique rigid solid or duplicate mass.
- **Archived separate lineage:** historical hardware remains searchable as attributed reference, never inherited as RP1 installation. Lineage is independent of geometric detail.

Each attachment/interface needs named owning features, datum/axis/frame/units, nominal dimensions and explicitly known or unknown tolerances, opposing surfaces, axial engagement/contact, material/process, and source locator. Fasteners need exact product/thread/length/stack; cords need exact termination/contact definition. Electrical interfaces need connector/pin/net/orientation, power boundary and mounting/strain relief. Mechanisms need source-defined degrees of freedom, travel and stops; illustrative explode motion supplies none of these. Keep geometric compatibility, engineering evidence and physical test results separate.

For the first vertical slice, register **the current165mm tube template and current notched forward-ring template**, show their existing installed instances, source-axis/station relationship and recovery guides, and make source/unknowns directly inspectable. A later scratch assembly can reuse those exact definitions under primary's draft architecture. Core versus optional/detail meshes are representation choices, **not alternative hardware**. Changed drafts inherit no mass/inertia, capacity or flight result; tests/experiments need matching source identities and the required data before comparison claims.

Hardware is unpurchased. No owner measurement, supplier contact, purchase, source revision, CAD/export rerun, FEA or simulation was performed or requested. All five inquiries remain UNSENT; D1 and engineering/physical/flight gates are unchanged.
