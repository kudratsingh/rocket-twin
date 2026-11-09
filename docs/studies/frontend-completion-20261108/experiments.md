# Experiments/replay bounded completion packet — November 8, 2026

Baseline supplied by primary: merged PR110/main `6a12c2b8b2a78d436cc24ecac7c05c80c5eb6ca7`. This packet audits RV-Q22/24/25/28 and makes one export correction. It performs no browser interaction, runtime fault injection, simulation, solver or vehicle change. All prior failed, capped, inconclusive and unexecuted observations remain unchanged.

## Existing capability and actual remaining evidence

| Criterion | Current source capability | Remaining evidence / limitation |
| --- | --- | --- |
| RV-Q22 — eligible reproducible runs | Complete archived-configuration requests, seed/preset/resource declaration, idempotent submission keys, saved identity/settings, reuse as a new draft; RP1 and finless unguided execution unavailable. | Native request/worker-error branches remain unexecuted. Source fixtures do not close them; no new run is justified merely to increase a count. |
| RV-Q24 — batch retention/control | Accepted membership is checked; observation reads every saved member, retains successful reads across transport failures, and distinguishes cancellation acknowledgement from terminal states. Saved metadata includes missing members explicitly; draft reuse preserves the original record. | P3/P4 retained complete members and exports. Actual acknowledged cancellation/termination remains inconclusive; controlled worker failure/retry and broader reload branches need their own declared evidence. No new batch/cancellation request occurred here. |
| RV-Q25 — shared replay cursor | Immutable elapsed capture, exact numeric time, recorded windows, event jumps, pause/speed controls and source-matched actor/camera handling already exist. P10/P12 preserve absolute125 with A unavailable/B valid and available-target camera behavior. | Measured speed-multiplier accuracy, endurance and remaining keyboard/window cases are not established by helper tests. No pose or clock correction was needed in this packet. |
| RV-Q28 — comparison/range export | Explicit recorded-event offsets, independent support, missing-value gaps, source/units comparison guards, plot range controls and original-timestamp CSV plus companion metadata already exist. P3 observed1500 selected raw samples. | Missing-channel/event branches remain source-fixture evidence where no native observation exists. This packet fixes the metadata coverage inconsistency below; it does not pass the compound browser criterion. |

## One concrete correction

`runExport.ts` previously validated the recorded time axis and channel coverage only when downloading CSV. The companion JSON metadata path independently counted samples and reported first/last coverage, allowing duplicate/nonfinite/reversed time axes or oversized channels to produce apparently usable provenance even though the identical CSV was withheld. The existing loader checks source/frame identities but can admit such axes; replay helpers then withhold the actor, making consistent export handling necessary.

Both export paths now use the same existing coverage validator. Metadata also validates its comparison run before publishing that peer's support. Empty/nonfinite/non-increasing time axes and channels with impossible coverage produce the same useful export error. No API, exported schema, source identity, event/pose math, sample selection or valid payload changes were introduced.

Short channels and null/nonfinite values remain explicit missing cells rather than invented zeroes. Genuine finite zero, unequal aligned coverage, recorded timestamps, original backend metrics and source metadata are preserved. An invalid selected range/offset continues to withhold metadata rather than fabricate selected coverage. Existing Experiment download error handling displays the helper error; no shared-file wiring patch is required.

## Source verification

- New `web/tests/export-coverage-consistency.test.mjs`: three deterministic in-memory tests for CSV/metadata agreement on invalid axes/coverage, invalid peer/range rejection, and aligned unequal coverage with zero/null/short values and source immutability.
- New tests plus existing `run-export.test.mjs` and `release-experiments.test.mjs`: **12 passed, zero skips**. This includes the existing unsupported-RP1 SSR source check; SSR is not a native browser observation.
- Scoped Prettier formatting and ESLint on `runExport.ts`, plus full TypeScript typecheck: **passed**. No broad simulation, saved owner-data load, browser packet or performance profile ran.

Only `web/src/experiments/runExport.ts`, the unique new test and this report belong to this packet. `Experiment.tsx`, `experiment.css`, shared state, ledger and browser records were not edited. The capability closed is consistent fail-closed companion export coverage; remaining native/fault/cancellation/performance criteria stay open.

G80 RP1/AD1/D1 and separate G54/G12 PID-to-RL identities are unchanged. All five supplier/lab inquiries remain UNSENT. Contact, purchase, paid run, physical/test/build, installed thermal/recovery/flutter, WO-03/04/05/10 and flight gates remain intact.
