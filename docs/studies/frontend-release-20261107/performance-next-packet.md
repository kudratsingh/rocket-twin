# Next bounded performance packet — proposed, not executed

The current inspection/experiment preview is usable. Both recorded full native-rate
G54 attempts remain failed against the 60 fps target. The second measured mean
17.50 ms and p95 17.70 ms. Their source, heap/load/scrub observations and earlier
failures stay in the session record. No third attempt is part of this closeout.

The normal profile uses approximately 3,000 source samples plus event neighbours;
its frame rate was not measured by the full native-rate attempts. WO-05 explicitly
allows display decimation for its 120-second/1-kHz dataset benchmark. That does not
change the 60 fps target or establish a pass for either profile.

The next question is whether SVG plots or trajectory drawing dominate the remaining
cost. Use one existing Chrome Performance trace, at most 15 seconds, in the sole
permitted window, with the same saved G54 dataset and declared viewport/profile.
No new flight simulation or engine/dependency change is needed. Stop if the trace
cannot isolate a useful cause; do not invent a sequence of optimization variants.

If the trace supports it, admit one display-only correction: retain the original
source arrays for pose, exact-time interpolation, metrics and exports, while bounding
rendered plot/trajectory geometry. Preserve real gaps, recorded events and explicit
sampling metadata. Headline peaks must still come from raw backend metrics. Do not
use a reduced drawing as a lower-rate physical simulation or a confidence interval.
If another bottleneck controls, record that finding before selecting a correction.

Suggested next-packet allowance: one 45-minute source slice plus one correction;
small renderer-data checks at most 10 CPU / 30 wall seconds; one post-change browser
measurement at most 30 seconds of playback, using saved telemetry only. These are
proposed limits for a separately declared packet, not an automatic increase to the
completed attempt budget. A performance miss, identity/gap/peak regression or
unclear bottleneck stops that packet. Preserve the result and the unchanged target.

Keep the existing engine and the working owner preview. Coordinate exclusive browser
availability before another measurement. Engineering, prototype-build, purchases,
physical work, firmware review, PID/RL and flight-release gates remain separate.
