# Agent entry point

Read `CLAUDE.md`, then `docs/PLAN.md`, `docs/ENVIRONMENT.md`, and the current
work order named in `docs/STATUS.md`. Follow their work order sequence and
validation benchmarks. The project is currently in WO-03, expanded by ADR-0007 to include executed
structural, thermal and tolerance/motion analysis. Expanded WO-03 acceptance
remains open.

The owner's latest delivery priority is one complete conventional fixed-motor
G80 engineering package first (ADR-0011). Preserve substantial custom building,
maximum practical performance and committed PID-to-RL development. G54 upgrade
and G12 controls remain separate committed tracks. G80-specific evidence never
clears their findings or aggregate WO-03 acceptance. Deliver the saved early
frontend preview under ADR-0009; do not rebuild it or change graphics engines.
Report outcomes, blockers, next bounded deliverable/stop condition and required
owner input. Ordinary local fixes and focused PR/check/merge work remain autonomous.

ADR-0012 records the owner's parallel launch-guide/motor comparison and a
conditional G80 supported1.8m usable-guide planning option. Keep the resolved
1.5m reference unchanged until actual equipment, guide-button geometry/mass and
complete-configuration checks support an explicit revision. Guide-model mass
ceilings are conditional, not an approximately1kg universal limit. Retain15m/s,
separate15.5 planning and full separate50g; larger budgets clear no other gate.

The owner's 2026-10-31 continuation uses `docs/wo03-closure-plan.md`: isolate
thermal errors on known cases, qualify actual geometry or justified bounds,
then revalidate one complete package. Follow its declared attempt budgets and
stop/replan conditions; do not repeat invalid or capped full-size methods blindly.
Preserve the saved preview; the latest limited resumption is described below.

Later owner direction on 2026-10-31 resumes the saved early frontend inspection,
experiments and replay **code and non-browser checks** through a bounded Terra
agent. The owner subsequently authorized that frontend agent to perform browser
verification in the designated Chrome window. It alone owns computer use for this
verification; the primary must not use computer tools concurrently. Record actual
observations and screenshots, with failures or unavailable checks explicit.
The declared Elmer campaign is closed in
`docs/wo03-elmer-campaign-decision.md`; neither solver qualifies for an
actual-baffle attempt. Preserve the earlier external-tool record as historical.
Do not start another open-ended custom heat-solver project. The previous timed stop was fulfilled and later
revoked by explicit owner resumption; it is historical, not a current pause.

## Owner-authorized early inspection and experiment preview

On 2026-10-30 the owner explicitly authorized limited WO-04 and WO-05 work in
parallel with WO-03: first a usable, read-only design inspector using actual CAD
and resolved specifications; then compatible recorded Analysis overlays; plus
working experiments and replay using the existing Python/JAX simulator. Record
exact design/run identities, explain quantities in plain language and show open
engineering findings. Keep candidate designs separate from active configurations.

This is a limited sequence exception, not completion of WO-03, WO-04 or WO-05.
Full milestones retain their prerequisites and benchmarks. Preserve engineering
acceptance, physical-build, paid-run, WO-10 owner review and flight-release gates.
Preview simulations are preliminary and unguided where applicable; PID and
reinforcement-learning controllers remain in their assigned later work orders.
See ADR-0009 and the current work-order/status records.

## Git workflow and autonomy

The owner authorizes GitHub pushes and PRs for this project. This supersedes the
previous local-only restriction on GitHub changes. The repository is
`kudratsingh/rocket-twin`; keep it private until the owner explicitly requests
a visibility change.

- Use a work-order branch and Conventional Commits. Commit and push after
  substantial, coherent work items; open a focused PR and update it as work
  continues. Split a large work order into focused PRs when useful.
- Keep development moving. Run the relevant checks, self-check against the work
  order, and record validation and remaining limitations in the PR. Do not add
  an independent review pass or request owner review for every PR.
- Routine changes may proceed through PR and merge after required checks pass,
  subject to repository protections. Do not wait for owner approval on ordinary
  PRs or bypass required GitHub checks/reviews.
- Retain explicit review gates, including owner review of WO-10 flight-computer
  firmware and abort logic. Ask only for a required decision, missing access, or
  an action outside existing authorization. Purchases, physical work and paid
  runs still require the owner's involvement.
- Never force-push shared branches, commit secrets/generated bulk data, or claim
  a push/PR succeeded without confirming it. If GitHub access is blocked, record
  the concrete blocker and continue useful local development.

## Parallel work

The owner explicitly authorizes subagents to accelerate this work and prefers
lower-cost models for bounded routine tasks. Delegate independent implementation,
traceability/document generation and plots with clear file ownership; retain
critical engineering decisions and integrated acceptance with the primary agent.
Avoid overlapping edits and an extra independent-review pass. Verify delegated
outputs through the same required checks before publishing.

## Computer use restriction

The owner explicitly reassigned frontend browser verification to the bounded
frontend Terra agent on 2026-10-31. Its only permitted browser window is the Chrome
window containing the Atlas Fibre G11 PDF; other tabs in that same window are
allowed. Do not use any other browser or application window. The primary and
other agents must not use computer tools concurrently with that verification.
Other work uses code and shell tools. Coordinate any later reassignment explicitly.
