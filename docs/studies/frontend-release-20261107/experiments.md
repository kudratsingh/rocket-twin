# Experiments and replay release source packet — 2026-11-07

This packet implements the remaining bounded source workflows for RV-09, RV-10,
RV-12 and RV-13. It does not establish browser interaction, runtime performance,
engineering readiness, physical acceptance or full WO-05 completion. The
production `replayPose.ts` from the independent PR90 pose work is unchanged.

## Inventory and resulting workflows

| Task | Existing evidence | Added source behavior | Remaining acceptance |
| --- | --- | --- | --- |
| RV-09 / FT-019–021 | Complete archived G80/G54/locked-finned-G12 requests, persisted source hashes, queued/running/complete/failed records, stale-load suppression | Explicit unsigned 32-bit seed and tiny/sim preset; normalized request digest; requested/effective settings, seed/RNG and declared resources; idempotent request keys; immutable new retries; inspectable saved failures/cancellations/interruption; partial-trajectory disclosure | RV-Q22 browser workflow; RV-Q23 source fixtures pass, browser behavior remains unobserved |
| RV-10 / FT-022–023 | Single local CPU slot | Two to four declared member requests; serial concurrency 1; complete cases, resource/storage/cancellation policy before Run; each member carries the same batch ID/member list and its own identity/status/error; filterable run library, batch progress and saved metadata; cancel all remaining members | RV-Q24 designated-runtime observations, including a running cancellation and reload |
| RV-12 / FT-024 | Two independently identified matching-CAD runs, source/setting differences, channel semantics/units checks, nearest native sample readouts | Explicit absolute or recorded-event comparison clocks with visible offsets and native-time readouts; unequal support and missing samples remain gaps; shared zoom/pan/range; keyboard plot cursor; selected-range native CSV and identity/offset/range JSON exports | RV-Q28 browser chart/selection/export observation |
| RV-13 / FT-026–027/029 | Recorded monolithic pose, event-derived phase limitation, trajectory and follow/free cameras | Fixed-pad camera, metric grid/scale and honest request-wind legend; visible recorded CG marker; reduced-motion playback starts paused; memoized chart geometry; bounded JSON and Arrow stream with source/schema/sampling metadata; bounded rolling frame/load instrumentation | RV-Q27/Q29/Q30 actual browser evidence; representative ≥120 s / 1 kHz host/viewport/memory/frame measurements |

The form permits only the three complete archived simulation configurations.
RP1 AD1, other inspection candidates and finless unguided configurations remain
unavailable for execution. No historical mesh, motor or inertia is substituted
for RP1. PID/RL, full-scale/staging and new physics remain in their assigned
later work orders.

## Lifecycle and bounds

`POST /api/experiments` accepts the original complete request plus `seed`.
`POST /api/experiment-batches` accepts 2–4 complete `cases`, `concurrency: 1`
and `resource: "local-cpu"`. A single process owns one local CPU slot for the
entire batch; a concurrent single or batch request receives HTTP409. Requests
with `Idempotency-Key` return the original member IDs for identical inputs;
reusing a key for different inputs receives HTTP409. The form prevents duplicate
clicks and retains an uncertain submission key in session storage until a reply
is received. Reusing saved settings produces a draft and a new attempt, without
changing the original record. Missing historical seeds remain unavailable and
cannot silently become a reproducible draft.

The inherited tiny preset declares 0.005 s steps / 45 s horizon / at most9,000
steps per member; sim declares 0.001 s / 360 s /360,000. A four-member sim batch
therefore declares at most1,440,000 model steps, serially. These are simulation
horizons, not measured wall-clock or memory guarantees. Each member retains
record/resolved/Parquet artifacts locally without automatic deletion; compressed
bytes and JAX compilation memory depend on the host. No remote/paid execution,
automatic retry, repeated campaign or owner-artifact deletion is introduced.

`POST /api/experiments/{id}/cancel` persists `cancel_requested` for every
unfinished batch member. It acknowledges a request, not immediate termination.
The worker checks before setup, before and after the compiled JAX rollout, and
before admitting its result. An in-flight compiled rollout can finish first.
Cancelled/failed/interrupted members cannot supply telemetry via the replay API.
An owning API process that ends before a terminal save is reconciled to
`interrupted` when its record is next read; automatic resumption is not attempted.
This is a single-process local API contract; sharing the run directory between
independent API worker processes is unsupported.

A successful numerical horizon without recorded landing remains `status:
complete` (the computation finished), with `trajectory_complete: false` and
`result_state: partial_trajectory`. The run library and replay disclose that
partial trajectory. This does not turn a partial flight into a full-recovery
result. Batch displays retain every member rather than dropping failed cases
from a success statistic; no aggregate scientific statistic is invented.

## Comparison, transfer and presentation

Display time is explicitly `recorded_time_s − offset_s`. Absolute elapsed time is
the default. A selected event alignment requires a finite nonnegative recorded
time in each run; otherwise offsets return to zero with an unavailable reason.
Native absolute sample/event times and coverage remain visible. A run's actor is
absent outside its own support. Missing samples split SVG curves, never form a
line across the gap; a channel with unavailable semantics or differing code/units
cannot silently overlay as a compatible comparison.

CSV exports contain only actual returned samples in the inclusive selected
plot range, using native recorded timestamps and blank missing values. Metadata
retains full run identities, independent coverage, selected range/count, offsets,
event choice and comparison differences. Peaks in result summaries are the saved
full-rate backend metrics; display-sample extrema are not relabeled as peaks.

The JSON playback response and `/api/runs/{id}/telemetry.arrow` export use the same
selection: at most3,000 uniform native samples plus two neighboring samples per
recorded event, retaining endpoints. With the present six-event record, the
upper bound is3,012 points per run. Arrow schema metadata carries run/source,
frame, units, channel meaning and sampling policy. The Arrow download is the
full returned window; the range CSV/JSON controls are separately labeled. Full
raw telemetry remains the Parquet artifact. No dependency upgrade is added.

Trajectory/chart geometry is memoized across shared-clock ticks. The optional
instrumentation disclosure records the most recent600 frame intervals with
median/p95/max/mean and API-plus-identity-check load duration. Its re-serialized
JSON byte count is explicitly neither wire transfer nor heap usage. No frame-rate
or memory number has been observed in a browser in this packet.

Follow, fixed-pad and free views do not change recorded body poses. One scene
unit is1 m; the ground grid is100 m wide with5 m squares. Wind direction/length
is an illustrative request setting, not measured weather. The white dot marks
recorded centre of mass. Recovery remains the recorded monolithic body with
approximate point-drag/inflation/angular-damping disclosure. FT-027's optional
schematic canopy is deliberately omitted: no separate-body poses, line tension,
body separation, nose motion or equilibrium attitude are available to depict.
No realistic recovery animation is fabricated.

## Verification and limits

The implementation budget declared before execution was mocked lifecycle/API
fixtures, small pure/SSR frontend fixtures, and the existing one tiny CPU test
in an isolated pytest temporary directory with a120 s deadline. That single
actual smoke finished within a2.92 s six-test invocation; no persisted owner
run or broad simulation campaign was created. It exercised the real shared JAX
backend, source hashes, resolved snapshot, telemetry and model-domain messages.

Final commands/results are recorded with the parent release packet. This lane's
verification includes the existing replay-pose, replay-window, validity, channel,
comparison, request-order, scaling and export tests, plus new release tests for
batch bounds, idempotency, controlled failure, immutable retry, interruption,
queued cancellation, Arrow schema provenance, clock/gap/range behavior, filters,
bounded profiling and unsupported-RP1 SSR. The SSR fixture is synthetic source
checking, not a browser observation.

All browser rows remain pending/blocked under designated-runtime ownership.
The116.029 s diagnostic does not satisfy the ≥120 s benchmark. No claim of60 fps,
measured heap usage, complete WO-03/04/05 acceptance or flight readiness follows.
Optional dashboard/aggregate campaign analytics and future multi-body recovery,
PID/RL, Earth-curvature/staging physics remain outside this release. All five
supplier/lab inquiry drafts remain UNSENT; physical/build/test, purchasing,
paid-run, WO-10 and flight gates are unchanged.

Final lane validation:

- Targeted frontend release/replay/comparison/channel/request-order/scaling/export
  suite:29 tests passed, including5 new release tests.
- New mocked backend lifecycle/Arrow suite:6 tests passed (1.23 s), including
  cancellation requested while a mocked rollout owns the CPU slot, then terminal
  acknowledgement after it returns; no additional real propagation. Existing backend suite
  previously passed3 tests, including the one actual isolated tiny CPU rollout;
  the original six-test invocation included the initial three lifecycle fixtures.
- Web TypeScript, lane ESLint/Prettier and production build passed. Vite retains
  its existing >500 kB chunk-size advisory; this is not a browser load measurement.
- Python Ruff, Black check and strict mypy on `src/api/experiments.py` passed.
- Toolchain emitted existing FastAPI/httpx TestClient and Three CommonJS
  deprecation messages. No dependency pins were changed to suppress them.

## RV-Q30 full-rate preparation — bounded follow-up

The default remains the normal ~3,000-sample event-preserving path. An explicit
`playback=full-rate-benchmark` request now returns **every native sample** of an
existing saved run. It rejects more than150,000 raw rows before materializing the
Parquet table, and rejects more than64 raw numeric/boolean scalar channels. The
nine current derived display channels bring the returned maximum to73. No run
is started, no record is changed, and no truncated/decimated response is silently
substituted for an over-budget benchmark.

At the maximum schema/row bound, numeric float64 cell storage alone is87.6 MB;
a conservative32 bytes per JSON numeric cell gives350.4 MB. These describe the
numeric payload envelope, not measured total transfer or peak memory: metadata,
parsing, derived arrays, CAD and rendering add overhead. Two compared runs can
double those per-run bounds. The actual response includes returned/raw counts,
channel count, numeric storage/envelope estimates and the profile policy. Arrow
exports retain their normal bounded behavior and are separately labeled in the
UI. Native CSV metadata identifies native-rate output rather than calling it
decimated.

The frontend option is off by default. Toggling it aborts active fetches, clears
both actors and profile counters, then reloads the same selected saved run IDs
through the existing record/frame/configuration/CAD hash checks. A native reply
must declare this profile and return exactly its raw row count with uniform
column coverage, within the cap. Stale or cancelled replies cannot attach an old
actor to the new profile. A separate Cancel saved-run load action aborts fetching
without cancelling or starting a simulation.

The existing G54 fixture identified by the parent release audit is
`exp-ab60bd4ac5c2412a9dd85f712072bca2` (132,856 rows /132.856 s /.001 s recorded
step). This lane did not reread it or run a simulation for this follow-up. The
synthetic4001-row Parquet fixture verifies that native mode preserves all rows,
default JSON and Arrow remain bounded, invalid mode requests fail, and row and
channel caps reject before `read_table` can materialize data.

Instrumentation now measures actual response Content-Length when exposed,
API/identity-check load duration, rolling animation-frame intervals, and scrub
latency to the second animation-frame callback. Content-Length is not total
network transfer; scrub latency includes scheduling and is not GPU-only
completion. Nonstandard `performance.memory` is displayed only when the host
returns finite values; otherwise the UI says memory is unmeasured. It never
substitutes zero. No60 fps, heap, scrub or long-run browser result is claimed.
The designated runtime, exact host/viewport, full-rate dataset and observed
measurements remain the RV-Q30 acceptance gate.

The additive route bridge (`initialRunId`, `initialComparisonId`, `onRunSelect`)
lets the primary's App/URL integration restore and navigate saved-run links.
Route loads use the same source checks, independent cancellation and stale-load
guards. Successful loads notify the primary; comparison clear reports null.
App/Design ownership and URL construction remain with the primary integrator.

Full-rate follow-up validation:8 backend lifecycle/Arrow/native-mode fixtures
passed in1.41 s;6 frontend release tests plus3 existing export tests passed;
source request-order and unequal-window tests also passed. TypeScript, lane
ESLint/Prettier, Ruff, Black, strict mypy and production build passed. No saved
G54 file read, real propagation, browser interaction or performance observation
was performed in this follow-up.
