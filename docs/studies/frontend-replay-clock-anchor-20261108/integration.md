# Correct startup time before another replay qualification

P26 is closed and unqualified. Its immutable full capture contains7,973 records,
one invalid first interval and a second observed cursor of approximately-0.0073s
after a requested0.001s start. Captured visibility/focus/intersection conditions
were otherwise known and valid; the invalid interval is not silently discarded.
[Native result](../frontend-full-replay-qualification-20261108/browser.md).

## Cause and adopted software correction

The old Play effect sampled `performance.now()` before the first animation callback,
then subtracted that value from the callback's frame timestamp. Those values need
not describe the same rendering phase. The browser supplies a common frame
 timestamp to its animation callbacks; [the HTML Standard](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html#run-the-animation-frame-callbacks)
and [MDN's requestAnimationFrame reference](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame)
describe that timestamp and a first-callback animation anchor.

The new clock uses the first finite RAF timestamp as its anchor. An anchor has no
preceding observed frame interval and does not move the replay cursor. Every later
interval is measured between RAF timestamps and reaches the recorder, including
invalid zero/backward/nonfinite values. Such values cannot advance playback;
the last valid anchor is retained so a regression cannot cause double advancement.
A later bad interval therefore remains an invalid measurement, not a passing subset.

The independent reproduction starts with a wall reading1000ms and first frame
991.7ms: the cursor stays0.001s. The next frame1008.4ms advances16.7ms. Negative
event-relative clocks remain valid: a cursor-5 with end-2 advances to-4.9 after
100ms and eventually clamps to-2. No arbitrary zero-origin requirement was added.
[Pure contract and tests](contract.md).

Primary wired the clock into the existing Play effect. It preserves the same
`playbackStep` speed/clamp, single scene, raw data, pose math and source identities.
The recorded flight/simulator is unchanged. This is a frontend timing correction,
not an adopted rocket, physics modification or a performance optimization.

## Actual verification and limits

All275 local web tests pass, including four preserved/unpublished A2 cases;
271 are in publication scope. TypeScript, lint, formatting and packaged production
build pass. Full-session recorder, browser adapter/warmup/heap and report tests are
software verification. The clock fix has not had another native full-session test.
P27's current-source Design handoff is not a runtime timing qualification.

P26's finite-only diagnostic mean16.66677119919719ms remains above the unchanged
16.666666666666668ms target. Because its first interval is invalid, it is not a
qualified all-frame timing result. Its native260.878s stayed under300s, while the
first offline closeout369.767s exceeded360s by at least9.767s; later accounting
adds time. Both failures remain explicit. No source fix repairs that old record.

The one-attempt qualification packet is closed. A corrected full-flight test needs
its own explicit bounded decision; no automatic retake, filter, rounding-based pass,
resource expansion or optimizer loop follows. Engineering, physical, thermal,
recovery/flutter, WO-10 and flight gates stay open; all five inquiries remain UNSENT.
