# Owned-child guard: bounded exit-observation race correction

A macOS full-suite run exposed a real timing issue in the offline execution
supervisor: the operating system reported that the launched root process no
longer had an RSS record (`ProcessLookupError`, ESRCH), while `Popen.poll()`
still returned no exit status. The guard failed closed and cleaned up a then
freshly enumerated child. This did not produce an accepted calculation or lose
the durable log/status, but it prevented the orphan fixture's intended exit
path. The original suite outcome (283 passed, one failed) and exact failure
record remain preserved; a previous successful focused run did not establish
that this race was covered.

The narrow correction allows **only the launched root's RSS ESRCH observation**
a bounded wait/reap, at most20ms and no longer than the remaining case wall
budget. If it exits, the existing return-code and historical-descendant checks
run. If it remains live, the RSS failure still stops the run. The helper does
not retry RSS indefinitely, wait on an unrelated PID, suppress live permission
or generic reader errors, or signal a historical PID after root exit. No CPU,
wall, memory or solver-accuracy threshold changes.

Six focused process cases passed after the correction, including a deterministic
real-libproc exit race and persistent-live ESRCH failure. Platform-specific
libproc fixtures run on this Mac and explicitly skip on Linux; generic process
logging/failure checks remain portable. Source formatting by the primary is
checked with the project's installed Black module and Ruff before publication.
The preserved bridge trials used their original helper hash; their failure
and resource records are not rewritten as successes under this fix.

[Compact preserved failure/source packet](../runs/wo03-owned-process-exit-race-20261101T073354288267Z/record.json)
identifies the old helper, tests and status. This is execution reliability work
for bounded offline analyses, not a structural, thermal, physical or flight
acceptance. Future actual calculations need their own pinned inputs and budget.

The final primary check passed285tests plus3subtests in61.27s, after Black/Ruff/mypy. No native bridge solver was invoked by this check or selected for automatic retry.
