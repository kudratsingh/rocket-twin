# Desktop workspace journeys

This describes the intended operator flow for Design workbench v2. It is a UI contract for planned work, not a claim that the
parts bank or draft builder is already implemented. The data rules are in [architecture](architecture.md),
[parts bank and builder](parts-bank-and-builder.md), and [verification and migration](verification-and-migration.md).

## One shell, five workspaces

Keep **Design, Engineering, Experiments, Flight Replay and Analysis** as the five top-level destinations. Design has four local
submodes: **Inspect, Parts bank, Build draft and Compare**. They do not create a Mission Control dashboard or move experiments
into the drawing canvas. A source strip always names the displayed configuration or draft revision, spec/geometry maturity, and
whether the view is active, historical, unadopted or a local draft.

On desktop, two independently collapsible columns sit adjacent on the left: navigation/assembly tree and contextual details. A
large centered 3D/2D canvas remains the primary work area. A slim bottom drawer holds the active view's layers, dimensions,
evidence, jobs or plots; it is closed by default where the content can fit in context. Opening a deep inspector or drawing must
leave a visible return path and restore keyboard focus to its opener. Keep the current selection, camera and source when either
column or the drawer is toggled. Desktop capability comes first; compact/mobile layout remains a later matrix, with no implied
acceptance from desktop behavior.

| Destination          | Default work surface                                               | Context controls and outcome                                                                                                                   |
| -------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Design · Inspect     | Current source-bound assembly, part tree and dominant canvas       | Select, search, fit, isolate, section, explode, dimensions and detailed CAD/source status; return to whole assembly.                           |
| Design · Parts bank  | Source-owned definitions with filterable families and maturity     | Inspect a definition, stock or allowance without adding it; open only supported CAD and interfaces; show missing data.                         |
| Design · Build draft | Separate local revision and complete inventory                     | Explicit Add, Replace, Connect, Preview, Save draft and undo/redo; backend returns eligibility or field-level blockers.                        |
| Design · Compare     | Two immutable source/draft/candidate snapshots                     | Side-by-side inventory/geometry/evidence differences with matched units and separate source identities; no automatic physics calculation.      |
| Engineering          | Source-pinned arrangement, joint, system and verification drawings | Follow drawing node to the matching assembly/part/feature; view force, recovery, thermal, electrical and control paths with evidence maturity. |
| Experiments          | Eligible complete configuration and run setup                      | Choose supported backend inputs, submit a real local job, see progress/error and saved run ID; rejected drafts remain drafts.                  |
| Flight Replay        | One saved run or a compatible pair                                 | Scrub one recorded clock, inspect source pose/events/validity, compare channels and export recorded data.                                      |
| Analysis             | Compatible recorded cases and registered fields/scalars            | Select quantities, time and part coverage; stale/incompatible or absent spatial results remain visibly unavailable.                            |

## Inspect from whole vehicle to feature

1. Open current RP1 or an explicitly selected archive/candidate. The left tree starts at **assembly → subsystem → part →
   feature**; breadcrumbs show that exact path, IDs and source revision. A child fin panel, tab, ring layer, pad or trace
   retains its parent part ID and never becomes another BOM mass line.
2. Click a source-supported mesh or tree row. The context column shows function, material, dimensions with units, mass basis,
   geometry maturity, source file, applicable evidence and unresolved findings. A meshless row stays selectable for
   text/evidence; Focus and Isolate explain why they are unavailable.
3. Choose 3D, arrangement 2D, a section, a joint close-up or a linked drawing. Selection transfers only through a declared
   mapping. A drawing with a relationship node cannot silently select unrelated CAD, and a foreign source shows an unavailable
   mapping. Back to assembly preserves the parent selection and camera when it remains compatible.
4. Use orbit, pan, zoom, Fit visible, Fit selected and Reset. Show datum, body axis, axial station direction and native units; a
   local axes indicator does not imply measured registration. Fit follows **displayed** bounds when pieces are separated. Hidden
   or failed assets are excluded and reported as missing.
5. Section, transparency, hiding and explosion are display operations. The body half-shell view clips existing triangles and has
   an open, uncapped cut; it does not create a machined surface. Zero separation restores source coordinates. Each nonzero
   offset is labeled illustrative, not an assembly extraction path or clearance check. Dimensions distinguish source nominal,
   measured, inferred bounds and unavailable tolerances.
6. Mechanisms appear only when the source defines joint axes, degrees of freedom, stops and supported range. Otherwise show a
   static representation and an explicit **motion undefined** status. No animation invents travel, loading or dynamic clearance.

## Browse and assemble a separate draft

1. Enter Parts bank from a selected part or the Design submode. The selected family, exact definition revision, source/license,
   parameter schema, native frame, supported CAD, interface names, product/stock identity, quantity and price basis are visible.
   **Unknown stock, cost, tolerance or inertia is unavailable**, never zero. Historical or unadopted entries display their stop
   reason and cannot pass as qualified drop-in replacements.
2. Choose **Fork current** or an explicitly supported **Blank draft**. A blank draft shows required propulsion, structure,
   guidance/avionics where applicable, recovery, electrical and launch-interface subsystems as incomplete placeholders. It
   cannot run as a body-only rocket. The active RP1 source remains read-only; opening or saving a separate draft does not change
   the active vehicle or adopt hardware.
3. **Add** creates a unique occurrence with quantity, placement and named interface. **Replace** shows the removed occurrence
   and dependent connections; it never silently credits its mass. **Connect** names both mating features, process/retention and
   evidence. Typed entries use the source's units, range and datum with conversion visible. Numeric keyboard input is
   sufficient; freehand drag is optional presentation, not the sole way to assemble a candidate.
4. Before a command is committed, show its intended changes. The backend validates the base revision and returns a new draft
   revision or field-level errors. Stale revisions, duplicate IDs, wrong frames/units, unsupported parameters, incomplete
   quantities and incompatible mating features show errors next to the affected occurrence. Preserve the draft and undo path
   after rejection.
5. **Preview** asks the backend for bounded CAD/drawings on the chosen revision. It shows queued/running/failed/cancelled/ready
   and exact generated-asset identity. **Resolve** produces a separate immutable candidate only with a complete source inventory
   and dependencies; missing mass/inertia, aero, motor/recovery, controls or other required simulation inputs block Run. A
   successful geometric preview is not a simulation or engineering pass.

## Connections, systems and alternatives

From a selected joint, **Open connection** shows its graph alongside the associated drawing and 3D parts. Tree parentage,
geometric overlap, a planned contact and a verified load path have different statuses. Mark each graph edge as recorded
relationship, nominal geometry, calculated, tested, failed, superseded or unavailable at the applicable source revision; never
color a whole subsystem green from one component result. Show missing fasteners, adhesive spatial geometry, installed fit and
force evidence as gaps.

The Systems view in Engineering follows a chosen path through structural support, thrust/retention, recovery, thermal
protection, electrical power, signals and any supported controls. Each node opens its part, connection, diagram, source and
affected check. Unsupported recovery knot routing, populated PCB height or actuator motion remains unavailable. A diagram is
source-pinned 2D evidence, not a substitute for detailed installed CAD.

Design · Compare accepts two explicit immutable snapshots. Show added, removed, replaced and moved occurrences; complete
adapters, wiring, adhesive, finish and allowances; separate estimated versus measured costs; mass/CG/full inertia only when the
backend supplies a valid basis; and invalidated checks. Keep current RP1, G54 and G12 identities separate. A stopped FP1/FR1
study may appear as context but cannot be treated as an installed replacement. A candidate can be inspected while blocked for
simulation or engineering use.

## Test, replay, analyse and export

From a resolved candidate, **Test in Experiments** carries its immutable ID and complete effective settings to the existing
Python/JAX path. The setup page shows eligibility, model/source hashes, seed, environment and resource preset. Run is explicit;
a parameter edit never launches CAD, FEA or a flight. An ineligible draft returns to its validation report. Save each real job
with its own status and immutable run record; copying settings creates a draft, not a second run.

**Open replay** carries only the saved run ID. Flight Replay shows the actual pose, event markers, validity gaps, plot units and
one authoritative recorded cursor. Two-run comparison requires declared compatibility; absent channels remain gaps and raw
backend extrema are distinct from display sampling. Analysis opens only recorded results with matching candidate, spec, CAD and
registration identity; its time control stays separate from replay unless an explicit recorded mapping exists. No field is made
up to fill a missing case.

**Export** chooses a named scope: selected part/assembly CAD, source drawing, resolved YAML, complete inventory/BOM, validation
report, run data or a bundled candidate packet. The confirmation lists exact source/candidate IDs, revision, units,
representation maturity, included files and known exclusions. Files carry matching hashes/provenance; unavailable assets are
excluded with reasons. Export is neither publication of an adopted vehicle nor permission to buy, build, load or fly.

## Recovery rules for every journey

Back/forward and deep links restore only compatible workspace, source, part, feature, draft and run context. A changed
configuration clears stale selection and displays the reason. Missing assets, HTTP errors, delayed A/B responses, cancelled jobs
and invalid drafts leave the other workspaces usable. Native behavior is checked by the designated Chrome owner against an exact
head; offline rendering or code checks alone do not accept a journey. The existing failed representative 60 fps benchmark
remains failed until its separate unchanged test passes.
