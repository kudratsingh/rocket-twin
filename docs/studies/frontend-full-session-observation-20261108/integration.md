# Full-session replay evidence, with its first executed limitation

This extends merged PR112/main `cc98fb6e9424d99d62c8ceb41d68489da6f1031c`.
The earlier rolling600-frame export is retained. New diagnostics also preserve the
last entire Play/source/profile/speed/clock epoch, capped at24,000 frame records
and24,000 condition events. Invalid values, unknown conditions and caps remain
explicit. The full snapshot is copied/sorted only for a paused export, not during
rendering, RAF collection, periodic updates or cleanup.

[Pure recorder](contract.md), [browser adapter](implementation.md) and the
[qualification plan](qualification-plan.md) define known-answer checks and limits.
The warmed IO cache uses actual measured intersection for the same context/canvas;
source/canvas changes invalidate it. Initial ResizeObserver notification only sets
a baseline. Host JavaScript heap is captured once at start and once at stop;
unsupported access remains null. No per-frame geometry read or clock mutation is
added by observation. Viewport intersection is not external-window occlusion/GPU
completion evidence. All raw frame/transition records remain local.

One native whole-flight observation P26 ran exact saved G54 ab60 with132856 native
samples to its natural132.856-second end. It retained all7973 frame records and
known visible/focused/fraction1 conditions, but its first interval was invalid.
The observer correctly withheld a full timing verdict; the finite-only diagnostic
mean is a strict tiny miss. [P26 report](../frontend-full-replay-qualification-20261108/browser.md)
keeps the raw identities, viewport, load, heap and budget overrun separate.
No retake occurred. The observed startup-clock defect then received a known-answer
[source correction](../frontend-replay-clock-anchor-20261108/integration.md), with
275localtests/type/lint/format/build passing; it has not retroactively qualified P26.

Other scoped native outcomes in this release are [P23 camera/single-run controls](../frontend-replay-pad-no-comparison-native-20261108/browser.md),
[P25 keyboard/Events](../frontend-replay-keyboard-correction-native-20261108/browser.md)
and [P27 owner-ready RP1](../frontend-owner-handoff-native-20261108/browser.md).
P24's verifier ReferenceError and P26's overall closeout overrun remain frozen.

The preview is usable, but full frontend/work-order acceptance is not declared.
Prescribed exact viewport sizing, remaining controlled fault/keyboard branches,
independent fin/tab motion proof, source-dependent Analysis/RP1 flight inputs and
qualified60fps remain separately open. No hardware, supplier contact, purchase,
paid run, PID/RL controller, firmware or flight approval follows from this work.
