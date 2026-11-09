# Rocket Twin design workbench v2

**Owner visual reference set — November9:** Use the [saved reference gallery and
goal map](reference-set-20261109.md) for geometry depth, section hatching/edges, assembly hierarchy,
measurements, transparent interiors and process views. FW2-020/FW2-A15 also require
a readable physics → guidance → PID/RL controller → actuator → rocket-response
system map, with sensors/estimation, recovery, power and logging paths. Link blocks
to actual backend/specification evidence, signal units and coordinate frames.
Mark current G80 unguided behavior and planned G12 capabilities honestly. This is
a visual/interface requirement, not adoption of the pictured hardware or a new
physics engine. Supplier inquiries and all physical/controller/flight gates remain.

**Owner direction: November 9, 2026 — complete the plan, then start.** Build an
engineering workbench where the owner can inspect the rocket down to supported
construction details, understand its systems and connections, assemble a separate
rocket draft from a reusable parts bank, and compare complete alternatives through
the existing backend. This is the full next revamp, not another camera-only pass.

G80 custom construction and practical conventional performance remain first.
G54 performance and G12 PID-to-RL are separate committed tracks. Keep the present
RP1/AD1 v2 frozen, with its engineering findings visible. No inquiry, purchase,
physical work, paid run, firmware review or flight release is authorized here.

## The finished experience

1. Open the current rocket or a saved draft. See its exact revision, geometry
   coverage, mass basis and unresolved engineering findings.
2. Move from the whole rocket to a subsystem, part, joint or source-supported
   feature. Rotate, move, zoom, section, isolate, separate and measure the
   represented geometry; return without losing context.
3. Read dimensioned arrangement, section, joint, assembly and service drawings.
   Follow actual structural, recovery, thermal, electrical and control paths.
   A diagram selection selects the matching object and evidence.
4. Browse a parts bank containing custom designs, purchased products, stock/cut
   templates, recorded alternatives and explicit nonphysical allowances. Inspect
   dimensions, interfaces, material, mass, source, price basis and supported CAD.
5. Fork a design or start a structured draft; add, replace and connect parts.
   The backend explains incompatibilities and missing inputs. Save/undo/export
   without overwriting the source design. The first version uses explicit forms
   and connection choices; freehand dragging is optional, not a prerequisite.
6. Compare complete alternatives: geometry, required hardware, cost, mass and
   balance, stability, guide departure, recovery demand and engineering findings.
   Run only configurations with complete supported simulation inputs, then replay
   and compare their actual saved telemetry with assumptions visible.
7. Export an identity-bearing CAD/drawing/BOM/assembly/test packet. Inspection
   detail, engineering acceptance, authorization to prototype and flight release
   remain separately stated. A successful virtual build is not permission to fly.

## Plan documents

| Document | What it settles |
|---|---|
| [Baseline and scope](baseline-and-scope.md) | Current assets, immutable sources, gaps, authority and migration |
| [Architecture](architecture.md) | Parts, instances, interfaces, drafts, backend jobs and evidence identities |
| [Parts bank and builder](parts-bank-and-builder.md) | Library contents, assembly workflow, compatibility and alternative evaluation |
| [CAD and engineering views](cad-and-engineering-views.md) | Detailed geometry, drawings, mechanisms and all required visualizations |
| [Workspace journeys](workspace-journeys.md) | Navigation and concrete desktop interactions |
| [Phased roadmap](phased-roadmap.md) | Ten phases, visible deliverables, dependencies and stopping decisions |
| [Task backlog](backlog.json) | Machine-readable tasks, owners, files, acceptance and budgets |
| [Acceptance matrix](acceptance.csv) | New scenario IDs and evidence type; planned is not passed |
| [Verification and migration](verification-and-migration.md) | Existing RV/FT mappings, negative cases and retained failures |
| [Risks and decisions](risks-and-decisions.md) | Source gaps, blocking scope and smallest future owner inputs |
| [Execution handoff](execution-handoff.md) | Parallel ownership, first bounded slice and publication workflow |

The task backlog owns task status; this README does not grant acceptance.
Legacy RV/FT records remain intact. FW2 is additive and explicitly reopens
source-constrained draft composition previously deferred under RV-21. It does not
reopen stopped fin/thermal studies or unrestricted numerical/control development.
See [ADR-0017](../adr/0017-parts-bank-and-detailed-design-workbench.md).

## Delivery and completion

Each phase ends in a usable vertical slice with source/code checks, required
hosted checks and scoped actual browser observations. Implementation proceeds
through unblocked tasks; unavailable supplier geometry blocks only dependent
claims. The parts bank starts with the current 55 records, then reusable templates
and source-supported alternative definitions. It is not a claim that 55 distinct
finished manufactured components already exist.

**Full workbench completion requires the new acceptance scenarios, preserved
existing journeys and honest geometry coverage.** Critical undefined hardware
cannot be renamed “detailed” to close the milestone. Software may be handed over
in working increments while model completeness or engineering acceptance stays
open. Legacy failed performance evidence remains failed until its own criterion
is met or the owner explicitly revises it. Mobile polish stays secondary.

Planning is complete before new phase implementation starts. Initial work is
P1's read-only catalog/API/UI and exact links to the current inspector, alongside
P2/P3's existing-source recovery guides and mechanical cut/selection improvements.
No waiting for the five UNSENT inquiries is required for these slices.
