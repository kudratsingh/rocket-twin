# WO-03 bridge supervisor exit audit — 2026-11-01

## Scope and disposition

This is a read-only audit of the saved SINGLE continuation and the existing
owned-process supervisor. It does not change source, thresholds, the disabled
study configuration, or any execution record. The native status remains a
supervisor failure; the later read-only VTU recovery is a separate numerical
record. Neither is actual-bridge qualification.

## Saved SINGLE outcome

The durable native status at
[`status.json`](../build/wo03-elmer-bridge-single-continuation-v1/single/case/status.json)
records 267 successful RSS samples. The last and maximum observed root-process
sample is **1,059,078,144 bytes (1.06 GB / 0.987 GiB) at 15.0000 s**. The last
wall-loop sample is 15.0504 s. The following RSS query raised ESRCH; the stored
error says the launched root still appeared live after the bounded wait. The
20 ms maximum wait is specified in the helper, but its actual duration and the
elapsed time at the callback exception are not individually persisted. The
whole supervised call ended at 15.0780 s. It did not hit the 120 s wall limit.
The sample and terminal status are at `status.json` lines 3521–3523,
2438–2454 and 3526–3532.

The solver log says `ALL DONE`, and ends with 14.38 s solver CPU / 15.01 s real
([solver.log](../build/wo03-elmer-bridge-single-continuation-v1/single/case/solver.log#L2327),
lines 2327 and 2333);
the saved Popen return code is **0**. Nonetheless, supervisor status is
`failed`, `success` is false, and its error kind is `rss_reader`. Cleanup records
SIGTERM sent through `Popen.terminate`, then `root_reaped`, with no cleanup
errors. There is no separate timestamp/duration for the root wait or cleanup
reap. Post-reap child CPU accounting is **14.745329 s** (14.391384 user +
0.353945 system); supervisor CPU accounting is **0.049950 s** (0.023341 user +
0.026609 system). The parent launcher record gives **1.885838 s CPU**,
**16.891680 s wall**, and **510,656,512 bytes parent peak RSS**.

The timing and return code are consistent with a process-exit / RSS-observation
race near normal solver completion. They do not prove that race caused ESRCH:
the persisted sequence instead says the bounded wait still saw the root as live,
then cleanup requested termination and reaped it with code 0. No process-state
trace resolves what happened between the failed RSS query, wait, signal and
reap. The saved log's `ALL DONE` is evidence of solver output completion, while
the supervisor result remains failed.

The later recovery record independently evaluates the saved VTU and reports a
strict force check and output-precision reciprocity as passing. It neither
changes the original failed supervisor record nor measures process memory.

## What the resource record can support

`run_owned` calls the RSS callback with only `process.pid`; descendant
enumeration is separate and is used to track/signal owned PIDs, not to sum RSS.
Thus the 2 GiB guard and 1.06 GB observed maximum apply to sampled **root RSS**.
The samples were about 50–60 ms apart, so 1.06 GB is a sampled maximum, not a
continuous peak. The status has no direct-child `ru_maxrss` field, and no
descendants were recorded for this run. **Direct-child peak RSS is unavailable**;
aggregate process-tree RSS and a true unsampled 2 GiB peak cannot be claimed.
The parent peak is a separate process's peak and must not be substituted for
the native child's or the tree's peak.
The root-only callback and descendants policy are at
[`wo03_owned_process.py`](../scripts/wo03_owned_process.py#L323) lines 323–328,
and the per-root RSS call/error path is at lines 473–483.

The helper's policy is narrowly scoped: on RSS ESRCH it polls/waits on the
launched root for at most 20 ms, bounded by the case deadline; it does not retry
RSS or signal descendants on this path. If that wait still leaves the root live,
it raises the recorded RSS-reader failure and normal cleanup follows. This code
does not create a general grace period or relax the RSS threshold.

## Smallest useful software follow-up

The focused macOS test
[`test_rss_esrch_for_waitable_root_is_resolved_as_normal_exit`](../tests/test_owned_process.py#L85)
already exercises the real libproc ESRCH-after-exit race and verifies successful
return code 0. The smallest next check is to run that one test and add no new
limiter. If it needs further coverage, the narrow addition should deterministically
exercise `_root_reaped_after_rss_esrch` at both boundaries: root reaped within
the bounded wait returns true; wait timeout with root still live returns false.
This would validate the supervisor's bookkeeping branch without another native
case. It would not establish why the saved ESRCH occurred, child/tree memory
compliance, or solver/bridge accuracy.

## Evidence paths

- [Saved admission, compact summary and launch log](../runs/wo03-elmer-bridge-single-path-replan-20261101-v1/): one authorized SINGLE invocation; retry and qualification are false.
- [Native solver log](../build/wo03-elmer-bridge-single-continuation-v1/single/case/solver.log): native output ends `ALL DONE`; it records 14.38 CPU / 15.01 real seconds.
- [Native supervisor status](../build/wo03-elmer-bridge-single-continuation-v1/single/case/status.json#L8): cleanup and CPU accounting (lines 8–25); ESRCH and return code (2442–2454); sampled maximum and total wall (3521–3532).
- [Parent launcher record](../build/wo03-elmer-bridge-single-continuation-v1/record.json#L162): parent CPU, wall and parent peak RSS (lines 162–164); input/source/runtime/prefix unchanged.
- [Read-only recovery](../build/wo03-elmer-bridge-single-continuation-v1/single-readonly-recovery.json): later VTU force/reciprocity checks and recovery-process resources, kept separate from native-run supervision.
- [Supervisor implementation](../scripts/wo03_owned_process.py#L134): 20 ms root wait; [RSS query/error path and cleanup](../scripts/wo03_owned_process.py#L473).
- [Existing focused test](../tests/test_owned_process.py#L85): macOS waitable-root ESRCH race control.
- [WO-03 closure plan](wo03-closure-plan.md#L22): invalid/numerical failure/cap stop policy; no automatic backend switching or rerun.


### Executed narrow software check

The primary subsequently ran only the existing waitable-root ESRCH test:
`.venv/bin/python -m pytest -q tests/test_owned_process.py::test_rss_esrch_for_waitable_root_is_resolved_as_normal_exit`.
It passed in0.25 s. No Elmer process, source change or native retry occurred.
This demonstrates the already-covered waitable-exit branch; it does not
reproduce or explain the saved SINGLE failure, prove a true child memory peak,
or change that failed supervision status.
