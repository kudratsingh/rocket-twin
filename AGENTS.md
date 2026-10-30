# Agent entry point

Read `CLAUDE.md`, then `docs/PLAN.md`, `docs/ENVIRONMENT.md`, and the current
work order named in `docs/STATUS.md`. Follow their work order sequence and
validation benchmarks. The project is currently in WO-01; advance only when
its stage-appropriate benchmark is met and recorded.

## Git workflow and autonomy

The owner authorizes GitHub pushes and PRs for this project. This supersedes the
previous local-only restriction on GitHub changes.

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
