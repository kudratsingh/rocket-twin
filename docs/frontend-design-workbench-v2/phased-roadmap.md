# Phased delivery roadmap

Ten phases and 46 concrete tasks. Start from merged PR118; keep five workspaces, source identities and all existing release gates. Effort is a provisional number of focused implementation increments, not a calendar promise or permission to spend. Re-estimate after the first working parts-bank slice. Supplier data can block particular CAD/engineering claims without blocking the rest of the workbench.

| Phase | Usable outcome | Dependency | Approximate scope |
|---|---|---|---|
|P0 · Freeze the checkpoint and contract|A complete executable plan and unchanged usable preview.|Current checkpoint|Before P1|
|P1 · Usable source-owned parts bank|Search current parts, inspect their source and return to installed geometry.|Contracts from P0; exact task dependencies below|2 focused implementation increments|
|P2 · Detailed parts, interfaces and CAD|Critical source features and recovery datums are inspectable; missing geometry is actionable.|Contracts from P1; exact task dependencies below|3 bounded detail increments|
|P3 · Deep CAD inspection and drawings|Drill into every admitted feature, see inside joints and export labeled source geometry.|Contracts from P2; exact task dependencies below|3 inspection/drawing increments|
|P4 · Systems, mechanisms and construction explanations|Clickable engineering diagrams explain actual routes, assumptions and failure points.|Contracts from P3; exact task dependencies below|3 systems increments|
|P5 · Build separate rocket drafts from the bank|Add, replace, connect, save and undo without changing the baseline.|Contracts from P4; exact task dependencies below|4 builder increments|
|P6 · Coupled checks and engineering alternatives|The complete effective package receives consistent backend checks and invalidation.|Contracts from P5; exact task dependencies below|3 coupled-check increments|
|P7 · Experiments, replay and fair alternative tests|Run admitted candidates, inspect telemetry and compare exact assumptions.|Contracts from P6; exact task dependencies below|3 experiment increments|
|P8 · Analysis, verification and calibration workbench|Understand compatible results, open requirements and measured updates.|Contracts from P7; exact task dependencies below|2 evidence increments|
|P9 · Construction pack and integrated release|Usable detailed workbench plus honest construction/test exports; remaining physical gates explicit.|Contracts from P8; exact task dependencies below|3 release increments|

## Parallel delivery, not a serial waiting list

P0 is written first. Then run P1 backend/catalog and UI integration alongside source-only P2 work and bounded P3 cut/selection improvements. Once interfaces exist, P4 diagrams can proceed without waiting for all purchased product geometry. P5 draft storage and commands can proceed with source templates, but P6/P7 require actual complete inputs. P8 shows current findings immediately; it does not wait for nonexistent spatial fields. P9 instructions draw from admitted sources; physical execution remains later.

## Task deliverables and admission decisions

## P0 — Freeze the checkpoint and contract

A complete executable plan and unchanged usable preview.

| Task | Deliverable and pass condition | Depends on |
|---|---|---|
|FW2-001 · Freeze current sources and interrupted edits|Record PR118, the 55 source IDs, geometry identity, and preserved unpublished code; do not restart setup.|baseline|
|FW2-002 · Define parts, instances, interfaces and draft authority|Document immutable definitions, occurrences, connections, and results separately, with narrow draft-edit authority.|FW2-001|
|FW2-003 · Publish roadmap, backlog and acceptance|State every dependency, owner, stop condition, and end-state criterion; preserve the old ledgers.|FW2-002|
|FW2-004 · Map migration and first bounded slice|Preserve existing journeys and failures, exact code/source/native evidence boundaries, and file ownership.|FW2-003|

If a required case fails or critical source data are missing, stop that claim and record the controlling issue. One focused correction is allowed; then explicitly replan, without starting a reinforcement/solver family, relaxing criteria or blocking independent tasks.

## P1 — Usable source-owned parts bank

Search current parts, inspect their source and return to installed geometry.

| Task | Deliverable and pass condition | Depends on |
|---|---|---|
|FW2-005 · Definition and occurrence catalog|Represent all 55 current records once. Keep library revisions distinct from installed placement and representation children.|FW2-004|
|FW2-006 · Read-only bank API and source errors|Provide source-pinned list and detail responses with exact units, null values, and useful stale or missing-source errors; do not generate assets or write sources.|FW2-005|
|FW2-007 · Parts bank search and filters|Show readable categories, materials, maturity, physical versus budget roles, source conflicts, availability, and price basis.|FW2-005|
|FW2-008 · Installed-part and CAD links|Link a bank entry to the current Design part, evidence, and available CAD. Return with the exact specification and part ID; explain missing assets.|FW2-006, FW2-007|
|FW2-009 · Named reusable template admission|Register source-based tube and ring templates and known interfaces; unresolved product matches do not become verified hardware.|FW2-005, FW2-008|

If a required case fails or critical source data are missing, stop that claim and record the controlling issue. One focused correction is allowed; then explicitly replan, without starting a reinforcement/solver family, relaxing criteria or blocking independent tasks.

## P2 — Detailed parts, interfaces and CAD

Critical source features and recovery datums are inspectable; missing geometry is actionable.

| Task | Deliverable and pass condition | Depends on |
|---|---|---|
|FW2-010 · Template and feature-source contract|Define allowlisted generators, parameter ranges, stock orientation, exact source assets, local frames, and installation transforms.|FW2-009|
|FW2-011 · Fin/root and body connection detail|Use current AD1 geometry only. Holes, slots, tabs, rings, and contact annotations match sources; adopt no new construction variant or strength claim.|FW2-010|
|FW2-012 · Recovery passage and attachment guides|Register exact station and azimuth guides with the linked force route; keep knot and sleeve reservations distinct from finished hardware.|FW2-010|
|FW2-013 · Purchased electronics and mounting detail|Use sourced PCB, package, and connector features and exact installation where known; unknown heights and product conflicts visibly block claims.|FW2-010|
|FW2-014 · Motor/retainer and stock identity closure register|Record exact conflicting products and dimensions and the evidence needed to resolve them; admit detailed hardware only on a matching source.|FW2-010|

If a required case fails or critical source data are missing, stop that claim and record the controlling issue. One focused correction is allowed; then explicitly replan, without starting a reinforcement/solver family, relaxing criteria or blocking independent tasks.

## P3 — Deep CAD inspection and drawings

Drill into every admitted feature, see inside joints and export labeled source geometry.

| Task | Deliverable and pass condition | Depends on |
|---|---|---|
|FW2-015 · Hierarchical feature inspection|Navigate assembly, subsystem, part, and feature with material, function, connection evidence, selection highlighting, and context restoration.|FW2-008, FW2-011|
|FW2-016 · Reliable cut, isolate and camera controls|Show cut-face and motor-end views, meaningful clip/isolate/hide, per-piece visibility, and Fit that preserves context; actual edges are visible in native use.|FW2-011|
|FW2-017 · General arrangement, joint and manufacturing drawings|Link same-revision orthographic, section, joint, and dimension graphics across 2D and 3D; preserve scale, tolerance, and unknown labels in exports.|FW2-011, FW2-012, FW2-015|
|FW2-018 · Geometry detail levels and CAD export manifests|Record STEP, GLB, SVG, DXF, and STL scopes, units, feature-to-parent mapping, and cache identity; do not commit generated bulk files.|FW2-010, FW2-017|

If a required case fails or critical source data are missing, stop that claim and record the controlling issue. One focused correction is allowed; then explicitly replan, without starting a reinforcement/solver family, relaxing criteria or blocking independent tasks.

## P4 — Systems, mechanisms and construction explanations

Clickable engineering diagrams explain actual routes, assumptions and failure points.

| Task | Deliverable and pass condition | Depends on |
|---|---|---|
|FW2-019 · Load paths and free-body diagrams|Link thrust, reverse, fin, guide, and recovery cases through actual joints; infer no unsupported support or equal load sharing.|FW2-012, FW2-017|
|FW2-020 · System map, recovery and electrical architectures|Show recovery topology/netlist plus actual physics, estimation, guidance, PID/RL and actuator feedback with units, frames and implemented/planned status; preserve independent recovery and unknown pins.|FW2-012, FW2-019|
|FW2-021 · Thermal and compatible evidence graphics|Show real contacts, materials, openings, and recorded histories or cases; do not spatially fabricate failed, superseded, or missing data.|FW2-017, FW2-019|
|FW2-022 · Mechanism motion and kinematic status|Show joint axes, travel, stops, linkages, and wiring envelopes; distinguish illustrative poses, sampled clearance, and validated motion.|FW2-010, FW2-015|
|FW2-023 · Assembly and service walkthrough|Link access to fasteners and bonds, motor removal, battery/arming/recovery service, and assembly stages to parts and evidence.|FW2-017, FW2-020, FW2-022|

If a required case fails or critical source data are missing, stop that claim and record the controlling issue. One focused correction is allowed; then explicitly replan, without starting a reinforcement/solver family, relaxing criteria or blocking independent tasks.

## P5 — Build separate rocket drafts from the bank

Add, replace, connect, save and undo without changing the baseline.

| Task | Deliverable and pass condition | Depends on |
|---|---|---|
|FW2-024 · Draft identity and revision storage|Fork or create a structured blank draft with immutable revisions and atomic local saves; frozen sources and old runs remain unchanged.|FW2-009, FW2-010|
|FW2-025 · Add, replace and remove part commands|Use explicit quantity, placement, and parameters, required-system placeholders, a change preview, and clear undoable operations.|FW2-024|
|FW2-026 · Interface graph and compatibility|Validate named contacts, engagement, tolerances, power, and motion; count adapters and hardware; unknown does not mean compatible.|FW2-009, FW2-025|
|FW2-027 · Deterministic candidate resolution|Resolve complete YAML, manifest, and inventory with exact provenance, stock preparation, and units; reject duplicates, cycles, and missing functions.|FW2-025, FW2-026|
|FW2-028 · Save, undo, restore and export draft|Reload the exact revision, differences, and UI state; recover from stale writes and errors; export a new identity without overwriting RP1.|FW2-027|
|FW2-029 · Visual candidate and replacement comparison|Show assembly, part, and connection changes, required hardware, and open findings; retain alternative status and separate source lineage.|FW2-017, FW2-027, FW2-028|

If a required case fails or critical source data are missing, stop that claim and record the controlling issue. One focused correction is allowed; then explicitly replan, without starting a reinforcement/solver family, relaxing criteria or blocking independent tasks.

## P6 — Coupled checks and engineering alternatives

The complete effective package receives consistent backend checks and invalidation.

| Task | Deliverable and pass condition | Depends on |
|---|---|---|
|FW2-030 · Complete mass, balance and inertia availability|Count the installed inventory exactly once and document the full inertia tensor when available; keep growth, adverse, and harness probes separate; never use zero for unknown.|FW2-027|
|FW2-031 · Static/aero/guide/recovery checks|Use actual geometry and valid assumptions; separate formal and planning criteria and guide equipment; update recovery demand with changed mass.|FW2-030|
|FW2-032 · Dependency invalidation and engineering readiness|Invalidate only affected results when parameters, interfaces, or sources change; explain missing-input blockers; do not inherit an installed pass.|FW2-031|
|FW2-033 · Coupled alternative scorecard|Compare nominal and adverse complete packages across mass, fit, loads, heat, stability, guide, and cost; show stop reasons, uncertainty, and source evidence.|FW2-029, FW2-032|

If a required case fails or critical source data are missing, stop that claim and record the controlling issue. One focused correction is allowed; then explicitly replan, without starting a reinforcement/solver family, relaxing criteria or blocking independent tasks.

## P7 — Experiments, replay and fair alternative tests

Run admitted candidates, inspect telemetry and compare exact assumptions.

| Task | Deliverable and pass condition | Depends on |
|---|---|---|
|FW2-034 · Resolved-candidate experiment admission|The existing Python/JAX path accepts only complete supported snapshots; borrow no inertia or aero and make no silent motor swap; save progress and errors.|FW2-027, FW2-030, FW2-032|
|FW2-035 · Matched single/batch alternative experiments|Use bounded paired settings and immutable run identity; retain per-member cancellation and errors; list every difference.|FW2-033, FW2-034|
|FW2-036 · Replay current candidate geometry and pose|Match exact geometry, CG, frame, quaternions, time window, and event cursor; mark unavailable attitude without a borrowed pose; keep archived runs matched.|FW2-018, FW2-034|
|FW2-037 · Graphs, sensitivities and portable experiment exports|Show actual telemetry, extrema, units, gaps, synchronized cursor, and comparison windows; sensitivity probes are not confidence bands.|FW2-035, FW2-036|

If a required case fails or critical source data are missing, stop that claim and record the controlling issue. One focused correction is allowed; then explicitly replan, without starting a reinforcement/solver family, relaxing criteria or blocking independent tasks.

## P8 — Analysis, verification and calibration workbench

Understand compatible results, open requirements and measured updates.

| Task | Deliverable and pass condition | Depends on |
|---|---|---|
|FW2-038 · Compatible scalar/spatial Analysis|Bind field identity to the exact candidate, CAD, and case; show units, legends, time, limits, and exaggerated deformation scale; missing stays unavailable.|FW2-018, FW2-021, FW2-032|
|FW2-039 · Visual requirements, risks and verification map|Navigate part or joint to requirement, FMEA, calculation, and test; clearly link failed or superseded status and future owner test plans.|FW2-019, FW2-020, FW2-033, FW2-038|
|FW2-040 · Measured-data revision and calibration hooks|Store provenance, uncertainty, and configuration for owner-provided measurements; preserve originals, separate calibration and evaluation, and rerun affected checks.|FW2-032, FW2-038, FW2-039|

If a required case fails or critical source data are missing, stop that claim and record the controlling issue. One focused correction is allowed; then explicitly replan, without starting a reinforcement/solver family, relaxing criteria or blocking independent tasks.

## P9 — Construction pack and integrated release

Usable detailed workbench plus honest construction/test exports; remaining physical gates explicit.

| Task | Deliverable and pass condition | Depends on |
|---|---|---|
|FW2-041 · Dimensioned fabrication and assembly pack|Match source CAD, drawings, stock orientation, tolerances, materials, parts, and service instructions by identity; critical missing features block final manufacturing readiness.|FW2-018, FW2-023, FW2-033, FW2-039|
|FW2-042 · Owner-performed inspection and test package|Provide representative coupon, root, fit, recovery, thermal, mechanism, and electrical plans with criteria and equipment; physical execution still requires authorization.|FW2-039, FW2-041|
|FW2-043 · Complete cost and procurement snapshot|Count each consumable, hardware item, service, quantity, and cut waste; date availability and quote basis; mark unquoted tools, services, and shipping; assume no owner stock or purchase.|FW2-030, FW2-041|
|FW2-044 · Integrated desktop browser journeys|Observe the full path through existing and new workspaces: parts bank → build → compare → supported run and replay → Analysis → export, with real graphics and negative cases at the exact release head.|FW2-007, FW2-016, FW2-028, FW2-033, FW2-037, FW2-038, FW2-041, FW2-043|
|FW2-045 · Measured loading and interaction performance|Declare a visible-scene fixture, method, and resources; preserve the failed 60 fps target and stop conditions; allow only one bounded correction for useful LOD or cache changes.|FW2-018, FW2-036, FW2-044|
|FW2-046 · Release, source coverage and handoff|Record required checks, PR merge, actual screenshots, startup, and export pack; account for every new acceptance check without calling source gaps or engineering gates complete.|FW2-040, FW2-042, FW2-044, FW2-045|

If a required case fails or critical source data are missing, stop that claim and record the controlling issue. One focused correction is allowed; then explicitly replan, without starting a reinforcement/solver family, relaxing criteria or blocking independent tasks.

## Finish conditions

- Functional release: first-person desktop journeys work with exact identity, useful graphics, save/error recovery and honest missingness.
- Detailed-model milestone: critical parts/joints have source-supported geometry or remain visibly open; missing critical hardware prevents a claim of fully detailed current rocket CAD.
- Engineering/prototype/flight: retain WO-03, later owner-performed tests, WO-10 and flight gates. Neither of the software milestones closes them.
- Existing failures: legacy performance/physics/thermal/material records stay unchanged. A new result must meet its own declared criterion; no silent waiver.
- Deliver a URL/startup commands, actual screenshots, portable source-labelled exports, complete change/status table and next bounded task.
