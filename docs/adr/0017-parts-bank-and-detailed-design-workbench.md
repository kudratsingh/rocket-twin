# ADR-0017 — Detailed inspection, parts bank and virtual rocket assembly

Status: accepted owner direction, November 9, 2026; implementation is phased and
acceptance is not granted by this record.

## Decision

The owner requests full planning documents, then implementation of a detailed
engineering workbench: intricate source-supported component CAD, drawings and
system/mechanism explanations; a reusable parts bank; virtual assembly of separate
rocket drafts; and consistent alternative checks/experiments. Execute
[Design workbench v2](../frontend-design-workbench-v2/README.md) through its phased
backlog and acceptance matrix while preserving the existing application.

This explicitly extends CLAUDE.md's viewer-only rule and the deferred editing
portion of RV-21. The browser may author **separate draft specifications** through
validated part, parameter, placement and connection controls. Python remains the
source/validation/CAD/physics implementation. This is not unrestricted in-browser
surface modeling, executable CAD uploads, an engine change or automatic design
adoption. Existing RV/FT statuses and failures are not reset or silently promoted.

Keep definition, installed occurrence, connection, display representation, draft,
resolved candidate, result and evidence identities distinct. Every saved candidate
has an immutable source/parameter/geometry/model lineage. A part swap includes its
hardware, interfaces, mass, aero/recovery and other affected dependencies. Unknown
inertia or source data blocks only the operations that require it, with useful
field-specific reasons. No borrowed archived flight model or compatible-looking
mesh fills missing inputs.

Frozen G80 RP1/AD1 v2 and earlier stopped studies stay unchanged. Start the bank
from its55 records and current CAD/source evidence, then add reusable templates
and sourced products under their own revisions. Geometry maturity is separate
from material/joint strength, fit, thermal, recovery and physical verification.
CAD detail cannot convert an estimate into a measured component or installed pass.

## Delivery and authority

Write the complete P0 plan before P1 implementation. Proceed with bounded,
independently owned Sol HIGH lanes for source/catalog, backend, frontend and
bookkeeping; the primary owns architecture and integrated acceptance. Only the
existing designated `/root/browser_access_sol` may verify the permitted Chrome
window through the supported runtime. No alternate browser/headless/CDP workaround.

Retain the existing stack, five focused workspaces, large desktop visual, two
independent collapsible left columns, bottom drawer, experiments and replay.
Mobile polish is secondary. Source-compatible scalar/field Analysis and export
status remain honest. Full workbench delivery requires the new criteria and
preserved journeys, rather than a screenshot or task count.

G80-first custom construction and maximum practical conventional performance,
G54 upgrade and committed G12 PID-to-RL remain core goals. No physical
interchangeability requirement is reintroduced. The work-order sequence remains;
ADR-0009's early WO-04/05 exception continues. Full WO-03/04/05 prerequisites,
D1 loads/movement/material/guide/mass policies, stopped-solver limits, owner build,
purchase, supplier/lab contact, paid-run, WO-10 and flight gates are unchanged.
The five inquiries remain UNSENT and no reply clock starts.
