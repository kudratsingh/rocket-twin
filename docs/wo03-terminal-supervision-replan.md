# Narrow terminal-supervision replan

The saved bridge SINGLE returned zero and wrote its field, but its supervisor
failed when the final RSS query reported `ESRCH` and the root was not reaped
within the existing20 ms handshake. The [audit](wo03-bridge-supervisor-exit-audit.md)
does not establish the exact kernel/process timing or a true memory peak.
The failed run and its resource limitation remain unchanged. Its as-run helper
is retained at [commitc9dbbb6](https://github.com/kudratsingh/rocket-twin/blob/c9dbbb6d6033a7db84d00dffb12c18f1ad0dbf4e/scripts/wo03_owned_process.py#L134).

For future runs, the terminal handshake now permits **at most50 ms**, one
normal supervisor sampling interval, and bounded by the remaining case
wall allowance. This is a bounded process-exit bookkeeping policy, not a
temperature/force/convergence threshold or a longer analysis budget. No RSS
lookup is retried. A root that is still un-reaped at the end still causes the
same failure and cleanup; permission errors still fail. The RSS threshold,
root ownership checks, child CPU caps and case wall limits are unchanged.

The old20 ms choice could reject a terminal transition taking30 ms even though
that transition fits inside one ordinary50 ms observation interval. A
deterministic regression covers that case, a root remaining live after50 ms,
and a shorter remaining wall deadline. The complete owned-process tests pass
(7 tests), including the existing real macOS waitable-exit and live-RSS-failure
controls. This does not prove that the observed bridge failure had that cause
or that this policy fixes it in a large native process.

No Elmer rerun accompanies this change. No tree-wide or continuous-peak RSS
claim is added. Previously frozen preflight ledgers retain the old helper hash;
future analysis must create a fresh reviewed ledger that explicitly pins this
version, rather than rewriting earlier as-run source evidence. If the same
terminal failure recurs, stop and preserve it; do not keep extending this grace
or repeat the native case blindly. Further interpretation requires additional
process-state evidence and a new bounded decision.

The source change is limited to the handshake default and its explanation;
there is no new limiter or production numerical method. WO-03 engineering,
physical-test and flight-release gates remain open.
