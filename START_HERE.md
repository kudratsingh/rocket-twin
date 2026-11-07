# Start here (owner)

1. The project repository is `kudratsingh/rocket-twin`, public by owner confirmation
   on November 4, 2026. Keep it public unless the owner requests a change. Agents
   push substantial work on branches and use PRs without routine owner review.
   Required checks and repository protections still apply; WO-10 firmware/abort
   logic retains its explicit owner-review gate. See `AGENTS.md`.
2. Start with a dedicated conventional fixed-motor G80 custom build. Physical
   interchangeability with G12 is optional under ADR-0013; shared software,
   instrumentation and the digital twin remain useful. Maximum practical no-HPR
   performance and committed G12 PID/RL remain core goals; G54 is a separate
   upgrade track. The next engineering milestone is [VP1](docs/wo03-vp1-response-decision-20261106.md):
   use actual inquiry send dates/replies to prepare one room-temperature test
   decision, including the lab method and all-in quote, for owner approval before
   purchases or testing. The original modular rebaseline is historical context.
3. Confirm the actual club/site and discuss each intended configuration with its
   RSO before hardware release. ROC/Lucerne is a planning assumption, not approval.
   A policy for active stabilization is not established by a numerical model pass.
4. Follow `docs/STATUS.md` and the work-order sequence. The agent writes code,
   specifications and build plans; the owner authorizes purchases and performs all
   physical fabrication, tests and flights. Every actual configuration has its own
   geometry, mass properties and validation evidence.
5. Paid runs still require per-run approval; the agent prepares config, CPU dry run
   and cost, and the owner launches. No cloud run is authorized by a PR merge.
6. Hardware procurement remains WO-09, after exact motor/lot/California evidence,
   stock, measured fit and release documentation. Plugged G12ST-P needs independent
   recovery. Preliminary budget: roughly $650–950 plus any new tools, shipping/tax,
   club fees and a $100–200 guide/test fixture if needed. Actual spend is in STATUS.

Stop or revise the relevant milestone when evidence fails:

- WO-02 flight validation outside 5% after two fix attempts: record and resolve it
  before building controllers on that model.
- Frontend or orbital WO over one week: split it and update STATUS.
- Proprietary figures or branding in the digital orbital vehicle: remove before merge;
  exact physical commercial motor/component names remain necessary provenance.
- RL does not improve on PID: report the multi-seed result, investigate residual RL
  per ADR-0004, and bound further paid experiments. Keep RL as a committed research
  milestone; do not hide failures or waive deployment gates.
- Abort or envelope excursion on a flight: resolve and document the cause before the
  next controlled flight. Finless coast/recovery requires its own qualification.
