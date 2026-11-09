# Existing saved failure/reuse target

**No credible saved worker-failure target exists in the inspected metadata.** All **13** existing `runs/exp-*/record.json` files have `status=complete`, with no saved error. There are no failed, cancelled, interrupted or nonterminal attempts. Seven successful runs have incomplete trajectories; that is a result scope, not worker failure.

The [metadata audit](saved-failure-reuse.json) preserves every original ID, status, profile and record hash. It scanned fewer than 200 records in approximately **0.007 CPU seconds**. No API call, telemetry read, simulation, browser action, synthetic fixture or record edit occurred. A collection/network error or artificial fixture must not be presented as an actual saved worker failure. No new run is proposed to manufacture this branch.

## Available partial-result/reuse target only

`exp-c174705a75b8474290b523e8fb7c1267` is a real **complete attempt with a partial trajectory**, not a failed attempt. Its settings are archived `modular-performance-v1`, Tiny **45 s / 9,000 steps**, wind **1 m/s toward 0°**, gust **0**, seed **20261107**. Landing remains null. Current input files, simulation code and CAD revision match its saved identities; its registered 42-part geometry manifest hash also matches.

- Resolved specification: `c18abfee2444307e46eaaca55197693a3d9353bd8d8d8ac42162ffd238ef1d5e`
- Simulation code: `a58cde7fad6f24188887b019b4dc9632413ef1b20a0cacc7c1382c3010aa8d6f`
- CAD revision: `1193713d0f4a7ad8393a00a0a03e7aaa04e9aa9393d2034691ef7126ae3cdd3b`
- Original record SHA-256: `ea22ffc8aeeaef6098b14ee2f3a44782ba9593d0d6503d40c6cea59bfcd43d1b`

If primary chooses to observe successful-partial-result/draft reuse after its selection fix, use the normal existing Experiments route while preserving Design:

`/?workspace=experiments&design=G80-F2-RP1-AD1-definition-v2&experiment=modular-performance-v1`

Filter by the exact ID with Run status **all** or **complete**, then select that saved record. Expected details are **Status: complete**, **Complete** progress, partial trajectory and missing landing. **Reuse request as draft** should copy the exact settings above and report that the saved record is unchanged; **do not click Run on CPU**. This needs no export, permission change or download workaround. An optional source-supported direct route adds `&run=exp-c174705a75b8474290b523e8fb7c1267`; no browser route was executed by this audit.

This can establish only partial-result and draft-reuse interactions if actually observed. **Saved failed/cancelled/interrupted error presentation remains without a credible existing attempt to observe.** There is no reason to label the successful partial run as an error or enlarge the simulation scope.

## API/schema trace

`src/api/experiments.py` implements `GET /api/runs`, `GET /api/runs/{run_id}` and `GET /api/experiments/{run_id}` through `_record`. `_record` may mark stale nonterminal work interrupted; reading files directly avoided changing any status here. `Experiment.tsx` selects noncomplete saved attempts without loading telemetry and shows `error`, falling back to `progress`, in Saved attempt details. Its `reuseRequest` changes draft form state only; current validation is `runLifecycle.ts:requestDraft`, not an assumed new submission. URL construction follows existing `navigation.ts` and `experimentContext.ts` helpers.

No new acceptance gate or review is introduced. Engineering, build and flight status remain unchanged; all supplier/lab inquiries stay UNSENT. Primary retains native scheduling and publication.
