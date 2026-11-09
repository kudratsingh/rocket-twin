# Execution handoff and first implementation

The owner requested full planning first, then action. The README, contracts,
view/flow specification, ten-phase roadmap,46-task backlog,36-scenario acceptance
matrix and migration/verification plan constitute P0. Publish that coherent plan
through a focused PR, then implement the first unblocked slice while its ordinary
checks run. Do not wait for supplier replies, buy hardware or change frozen RP1.

## Current versus planned

PR118 is the source checkpoint, not this plan's completion. It supplies actual
PCB layers and18 mechanical child assets. P57/P59 observations are scoped; the
new work needs new evidence. Partial local PCB axis/marker/helper edits were
interrupted before tests; they stay preserved and out of the plan-only PR. Four
unrelated A2 source/test files remain unpublished. No repository setup restart.

## First usable slice — P1 read-only parts bank

Deliver **Parts bank** inside Design, backed by a Python catalog derived from the
frozen RP1 sources. It must cover55 records exactly, distinguish definitions from
installed occurrences, expose units/material/mass basis/geometry maturity/source
and identity conflicts, filter/search, and open the exact installed part and its
existing CAD/evidence. Missing assets remain unavailable. This slice does not yet
claim Add/Replace/Connect commands or a working candidate builder; those are P5.

Backend catalog generation must be read-only and deterministic. Avoid a CAD or
flight solve. Current geometry/record source pins remain unchanged. Use an API
and/or explicitly prepared backend-generated snapshot with an exact source/hash
contract; if the live API is stale, report that fact and use only an identical
source-verified prepared snapshot, never historical substitute data. If the owner
normal-terminal preview must restart, give the exact command after preparation.
Continue independent code/export checks in the meantime.

Acceptance for this slice: all55 source IDs once, stable definition revision,
separate installed location and group/mass semantics; unsupported source or
product conflict fail closed; search/filter/source inspection; bank→Design exact
part/spec selection; old viewer/experiments/replay preserved. Matching source
checks, focused tests, type/lint/format/build and required hosted jobs precede
merge. Browser observation remains a separate actual state.

## Ownership during P1

| Owner | Exclusive initial files | Task |
|---|---|---|
| Sol HIGH backend/source lane |`src/api/parts_bank.py`, `tests/test_parts_bank.py`, optional new preparer/snapshot module explicitly agreed with primary |Catalog projection, identity/conflicts/nulls and tests; no `app.py` edit |
| Sol HIGH frontend lane |New `web/src/parts-bank/*`, `web/tests/parts-bank*.test.mjs` |Catalog UI/types/source validation; no App/store/navigation edits |
| Primary |`src/api/app.py`, `web/src/App.tsx`, shared routes, entry points, FW2 status/acceptance, PR integration |Connect API and Design submode, self-check whole slice, exact-head checks/merge |
| Source/graphics lane when independently available |New source packet/export files only by explicit handoff |Recovery guides/CAD opportunities, no frozen source edits |
| Existing browser owner |New bounded native evidence folder only |Original permitted Chrome window, no source editing |

Do not assign overlapping glob ownership when tasks execute. Transfer ownership
explicitly before a later task changes the same file. No independent review gate
is added; all outputs receive normal integration checks.

## Resource and stopping rules

- One read-only catalog/API fixture, one stale-source fixture, one invalid/unknown
  field fixture, and focused client source/selection scenarios for initial P1.
  No flight, CAD generation or solver is needed. Target each focused check below
  two minutes; a failure stops and gets one concrete correction.
- Before later geometric jobs declare cases, at most120wall/90CPU seconds per new
  case, maximum600CPU seconds per packet. Existing closed exporters/solvers remain
  closed; production verifiers may only verify/copy the exact existing assets.
- Initial browser packet: one desktop source fixture, at most180seconds native,
  reserve time to close/restore, with a declared input cutoff. One scoped
  correction, then record/replan. No unsupported method or approval bypass.
- Alternative smoke initially at most two single tiny runs or one batch of at
  most four cases, only after complete candidate admission; existing resource
  validation and per-case120second target apply. No automatic large campaign.
- Preserve exact original and failed records. A cap is not permission to raise
  resources or relax load, material, mass, temperature or performance criteria.
- Hosted checks follow the existing workflow/timeouts. Routine focused PRs merge
  after required exact-head jobs pass. No force push, generated-bulk commit,
  secret publication or unrelated source inclusion.

## Progress report and handoff

Report capabilities the owner can open, exact design/source coverage, concrete
engineering requirements actually closed (usually none for UI work), actual
native observations versus code/offline checks, failures/blockers, next bounded
slice and any indispensable owner action. Include local URL/startup, source-labelled
exports and original screenshots. Keep current selection/camera context explicit
when the browser is handed back. Never equate plan, task count, CI, a detailed
model or simulated success with prototype/flight readiness.
