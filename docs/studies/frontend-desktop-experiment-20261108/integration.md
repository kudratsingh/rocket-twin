# One real desktop experiment, comparison and export

## What is usable

The normal app accepted exactly one archived G80 CPU experiment,
`exp-c174705a75b8474290b523e8fb7c1267`, with Tiny45s/9,000steps,
wind1m/s toward north, gust0 and seed20261107. P44 observed Running, completion,
and loading the actual saved result. RP1/AD1v2 remained the separate working
Design; no RP1 flight was submitted.

P45 loaded baseline`exp-d0baf4168f7f41e687a1b5f12e14cc3e` alongside it,
confirmed matching source/profile/seed and displayed the wind differences. The
apogee jump selected10.395s, Fit both selected Free orbit, and the scene/trails and
four recorded plots were visible. Nearly overlapping paths do not establish
independent pixel proof of both entire actors. No Play/performance qualification
or new batch campaign is claimed.

The actual browser CSV download completed. Its3,006 retained playback samples
come from the9,000-row source; all117,234 common raw numeric values and exact
sample times match the saved Parquet. This is not a full-resolution export or
independent validation of derived quantities. [CSV evidence](csv-download-verification.json).

Both runs have partial trajectories and no recorded landing. Computation
completion is distinct from a complete flight. Wind/aerodynamic/recovery model
limitations remain visible; these are preliminary unguided predictions, not
hardware or flight validation. [Exact source/settings evidence](source-verification.json).

## Metadata export resolved after specific authorization

P45's metadata request opened Chrome's multiple-download prompt. P46 automatic
approval review rejected allowing that persistent permission before execution;
that historical rejection is preserved. P48 later dismissed the prompt with
Escape while testing an independent inspection feature, without granting anything.

The owner then explicitly answered **Authorize this local site**, only for
`http://127.0.0.1:5173`. P49 requested A metadata through the normal app, and Chrome
reported Done without a new permission prompt. No Allow/Block/settings action
occurred, so no persistent permission change is inferred.

The primary independently verified the fresh42,723byte downloaded JSON,
SHA-256`72374b5052ab542b13e7126d3559252cd3b96cc05e9f73a666f7efb0a8bf0e77`.
Both embedded records exactly match actual saved A/B records; identities, wind
comparison, zero offsets, inclusive range and3,006/9,000 sample scope agree.
Missing landing and partial trajectory remain explicit.
[Metadata evidence](metadata-download-verification.json).

P49 restored whole RP1 Design; the download bubble remained open. P50 separately
verified and restored Design after the selected-part correction. Neither result
retroactively passes P45/P46/P48.

[Native run](../frontend-desktop-experiment-native-20261108/browser.md) ·
[Comparison/export boundary](../frontend-desktop-experiment-replay-native-20261108/browser.md) ·
[Historical approval block](../frontend-local-download-permission-native-20261108/browser.md) ·
[Authorized completion](../frontend-authorized-metadata-native-20261108/browser.md).

## Scope and gates

Existing archived source identities are unchanged. RP1 geometry, D1 engineering
criteria, G54 and G12 PID-to-RL remain separate. Five supplier/lab drafts are UNSENT.
No physical engineering requirement, WO-03/04/05 milestone, prototype build,
thermal/recovery/flutter, WO-10 or flight-release gate closes from this packet.

## Saved result to an independent draft

P52 changed only draft wind to3m/s while saved A remained wind1. One Reuse A action
restored wind1/direction0/gust0/Tiny45s/seed20261107/sweepoff. No Run, export or worker
request occurred. The primary independently checked the original record SHA-256
`ea22ffc8aeeaef6098b14ee2f3a44782ba9593d0d6503d40c6cea59bfcd43d1b`
remains unchanged. [Byte evidence](draft-reuse-verification.json) ·
[Actual native reuse](../frontend-draft-reuse-native-20261108/browser.md).

A read-only audit found13complete attempts and no actual failed/cancelled worker
record. Seven partial trajectories must not be mislabeled failures. That missing
native error-case coverage remains explicit; no failed run was manufactured.
