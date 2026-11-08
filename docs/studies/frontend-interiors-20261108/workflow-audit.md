# Interior inspection workflow audit — November 8, 2026

The next increment should make a useful interior view reachable in one action, then let the user focus a subsystem and compare its recorded alternatives without replacing the active vehicle. Better camera buttons alone do not expose parts hidden by an opaque shell. Smoother rendering also does not turn an envelope into detailed engineering geometry.

This is a source/UX audit only. It makes no code or browser changes. The earlier second external-change guard pause and DevTools rejection remain in force; no browser retry is authorized by this document. The new [acceptance checklist](acceptance.md) separates implementation checks from fresh designated-window observations.

## Current source findings

- `Viewer.tsx` puts Transparent shell, Section and Breakdown inside Scene tools. The drawer offers useful controls, but a fresh user must discover and combine them before seeing internals. Transparency and a staged breakdown serve different inspection needs and should not be presented as interchangeable.
- `PartsTree.tsx` exposes six functional assemblies with separate Frame group and Isolate group buttons. Its exact record/mesh totals and meshless guards should remain. A subsystem entry should support a direct inspection action that selects its group, makes its supported internals visible and frames those contents, rather than expecting several independent actions.
- `InspectionPanel.tsx` already explains a selected part's function, dimensions, source parentage and evidence. Keep that detail beside a useful model view. A meshless record must remain selectable and must not turn a prior interior view into an empty scene.
- `FinAlternatives.tsx` opens a modal over mounted Design, includes a return control, uses native dialog Escape and restores focus. It guards the RP1 design/specification and explicitly labels FP1/FR1 as unadopted schematic-only alternatives. Preserve this separation while making the entry and comparison easier to scan. The November 8 browser packet did not exercise this dialog, so its accessibility and return behavior remain source evidence only.
- The earlier source-owned breakdown uses two stages: groups separate first, then supported members of the opened group separate. This is an illustrative display transform, not a feasible physical disassembly sequence or verified clearance.

## Compact workflow

| Task | Intended behavior | Preserve / stop condition |
| --- | --- | --- |
| IU-01: Inspect interior | A persistent, plainly labelled viewport action reveals the chosen subsystem's internals; with no subsystem selected, it reveals the available internal assemblies. It must be useful without opening Scene tools. Use explicit shell hiding/ghosting/section or a documented combination; frame the revealed contents. Show which mode and subsystem are active. | Snapshot the previous display and camera before entering. No source, geometry identity, mass or simulation change. Missing compatible presentation metadata gives an explicit unavailable reason. |
| IU-02: Inspect subsystem | Motor and retention, Recovery and Avionics and power each have one direct Inspect action. Selecting it reveals the appropriate supported contents, frames them and leaves the Parts/Details linkage usable. Retain Rotate/Zoom/Reset controls in the viewport. | A group with zero meshes keeps the existing scene and explains what can be read instead. Group counts remain records versus meshes; no invented piece counts. |
| IU-03: Reveal a selected part | Choosing motor tube, motor or a supported avionics envelope from the tree produces a visible target. When shell occlusion prevents inspection, reveal the supported target deliberately and explain the active shell/section state. Frame retains the actual view angle unless a labelled preset is selected. | Keep stable IDs. Render, picking, labels and camera bounds consume the same display transform. Frame cannot attach a foreign mesh or fabricate a solid for missing geometry. |
| IU-04: Reversible view | A clear Return to previous view exits the temporary interior/subsystem view. Restore assembly separately returns display offsets to zero and clears the display-only section/isolation state as documented. | Restore the saved camera and prior visibility when returning from temporary inspection. Keep the current source and selected stable ID. Do not conflate Return, Fit, Reset camera and Restore assembly. |
| IU-05: Compare alternatives | One Compare fin alternatives action is available from Fins and roots and applicable fin Details. Start with current AD1 plus FP1/FR1 cards/columns: status, geometry availability, recorded dimensions/mass basis, findings and source. Keep the active RP1 identity visible. | No Apply/adopt action, active configuration swap, replacement 3D mesh or recomputed physics. Only compatible recorded values may be differenced. Missing values stay unavailable. |
| IU-06: Accessible compare/return | Keyboard users reach the same entry. Dialog title, initial focus, contained tab order, scrolling, close/return and Escape work at normal and narrow layouts. Loading/error states explain the actual data failure. Return focuses the opener. | Retain Design source, selection, camera, sidebar tab/width and view state. No hidden click target or background shortcut may mutate Design while the modal is active. |
| IU-07: Detail truth | Improve visibility and source-supported shapes where the frozen source actually defines them. Keep envelope, allowance and missing-geometry labels prominent in both model and Details. List omitted details beside the selected object. | New authored geometry requires its own exact source/dimension/asset identity and source checks. A cosmetic tessellation or material change cannot change its maturity. |

## Supported detail versus unknown detail

Baseline audited here: RP1 AD1 v2 specification `811b3bed…1660`, inspection geometry `238d01e5…b608`, presentation `4ed997e3…c005b`. A later detail increment must publish and verify its own tuple; these hashes are not a blanket identity for new assets.

| Record / shape | Actual source supports | Keep explicit |
| --- | --- | --- |
| Motor tube | Ideal tube length165 mm, outer radius15.6845 mm, inner radius14.5845 mm, wall1.1 mm. | Source-dimensioned ideal inspection solid; actual tolerances, pairing and installed joints unverified. |
| Aft ring / forward ring | Recorded annulus dimensions. The forward ring is an ideal notched annulus in the current inspection manifest. | Proposed forward-ring2 mm edge roundovers are omitted; finished cord passage, clearance and fit are not established. |
| Motor | Nominal128 mm length,29 mm diameter envelope. | No detailed casing, nozzle, retention interface or supplier-exact hardware model may be inferred from that envelope. |
| Fin set / integral tabs / root wedges | Recorded planform/thickness/bounding dimensions and source quantities3 panels,3 integral tabs,6 wedges. Panels and tabs co-move. | No qualified installed root/joint, bond thickness or strength implied by a clearer rendering. Keep separate accounting records and existing failed findings. |
| Recovery | Packed shock-cord box120×40×40 mm, connector box25×15×10 mm, parachute envelope80 mm length/25 mm radius. | These do not define cord routing, knots, connector articulation, packing or manufactured installation. |
| Kevlar wrap | The record and engineering relationship remain inspectable. | The manifest calls its old box stale: dressed choker, knots, moving route and packing geometry unavailable. Do not resurrect that box as an installed route. |
| Avionics / power | Example source envelopes: computer61×18×6 mm, IMU20×15×4 mm, battery55×30×15 mm. | Board components, ports, mounting holes, connector directions and wiring details are unavailable unless separately sourced. |
| Allowances / missing geometry | Retain all55 source records and their mass/provenance. | Twenty-five allowances and four missing geometries do not need separate visible solids. “High detail” must never silently change this coverage claim. |

Primary implementation and source-detail work can proceed independently of this audit. Browser acceptance resumes only after explicit window coordination and a stable integrated-source handoff; prior screenshots do not pass the new interior workflow.
