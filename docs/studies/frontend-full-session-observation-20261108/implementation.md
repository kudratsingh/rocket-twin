# Full-session observation hook — 2026-11-08

Candidate wiring is based on live `Experiment.tsx` SHA-256
`c0acbd028a6a7178d94bcd847ec86421f5fab4ade5201f6285b3ca2619e2b1a6`.
It remains staged at `.cache/full-session-observation/Experiment.tsx`; this worker
has not replaced live replay source or started playback/profile measurement.

## Measurement path

`useReplaySessionCapture.ts` uses the separately owned pure
`playbackSessionCapture.ts` recorder. A Play epoch captures exact A/B run/code/spec/
CAD identities, profile, speed and alignment. Advancing time is not an epoch
restart. Source-context changes clear stale retained observations, including while
paused. A layout effect records the committed UI cursor before passive recorder
cleanup; the previous context's cursor stays available when a source switch and
cursor reset commit together.

The existing RAF tick calls the stable `observeSession(elapsedMs)` once. It still
uses the original `playbackStep`, `setTime` update and 600-frame rolling profile.
The hook schedules no RAF and writes no clock, pose, controller or telemetry state.
Frame observations use committed cursor, document visibility/focus and a cached
IntersectionObserver ratio. IO observes the actual canvas queried from its existing
host ref. No per-frame rectangle/layout query occurs. Missing canvas/observer or
not-yet-delivered intersection remains unknown.

A persistent IO observer warms an actual canvas measurement for the loaded context
before Play. The capture can seed its first interval only from a matching context
key and the same canvas object; it never assumes a ratio of one. Context/profile/
speed changes invalidate the cache. A host child-list observer detects canvas
replacement, disconnects the old observer and clears its measurement; late callbacks
from the old canvas are ignored. The readiness caption shows only this lightweight
actual intersection state, updated by observer notifications rather than RAF ticks.
Do not admit the native profile until the actual current-canvas measurement is known;
unmeasured first frames are retained as unknown instead of deleted.

Window visibility/focus/resize events and IO callbacks enter the pure recorder's
bounded event history. ResizeObserver observes the canvas, records the initial
content rectangle as a baseline, and emits only later width/height changes. Stop
removes all listeners/observers and freezes the final observed cursor/wall time.
A stopped recorder is retained without cloning or sorting it.

Only a diagnostic download while paused calls the full snapshot. During-playback
exports set the additive full-session field to null; no snapshot sorting/cloning
runs in rendering, the RAF tick, periodic rolling-profile updates or cleanup.
The instrumentation caption is static and explains this distinction.

The pure recorder caps frames and events at 24,000 each; invalid/overflow/unknown
and hidden/unfocused/partial/resize conditions remain explicit. A strict numerical
mean threshold is separate from complete benchmark acceptance. An observed stop
or cursor endpoint does not establish full-flight completion. Intersection is a
cached browser observation, not proof against other-window occlusion, GPU
completion or GPU/process memory usage.

## Source checks

Three focused hook/adapter tests pass: listener/observer setup and cleanup, initial
unknown intersection, cached state, between-frame events, initial ResizeObserver
baseline, final cursor freezing, independent speed/source epochs, and the hook's
stable callback/dependency contract. The warm-cache test explicitly exercises a
first RAF before the new capture IO callback, unmeasured first RAF, stale source/
profile/speed, canvas replacement, late old-canvas callbacks and measured partial
intersection without upgrading it to full. These use browser method doubles and an AST
contract; they do not establish native React/browser timing or actual visibility.

Token comparison against the baseline preserves every existing callback after
removing the single added measurement call and its stable effect dependency. All
other function declarations remain identical except the additive diagnostic export;
camera, pose, scrub, raw export and numerical playback behavior are unchanged.

Root typecheck/lint/format pass. Candidate lint and in-memory TypeScript overlay
pass with zero diagnostics against the now-present primary-owned optional report
contract. Live replay source remains unchanged; coordinated application and final
integrated checking belong to primary.

## Integration and pending observation

Apply only the current `.cache/full-session-observation/Experiment.tsx` after
confirming the baseline hash, plus the new hook and tests. Keep the pure recorder
and primary-owned optional diagnostic report field in the same integrated source
packet. Run focused tests and normal web checks after the coordinated swap.

No benchmark is executed here. Primary must declare the one bounded current-source
native observation budget separately. Inspect actual source/host/viewport, full
session coverage, scene visibility, returned native data, sample cap, conditions,
load/scrub and memory evidence. Earlier P2 offscreen failure and stopped performance
campaigns remain immutable. No physics, engineering, physical or flight gates close;
all five inquiries remain UNSENT.

## Warmup correction frozen identities

- Hook: `4396f338b62e6c0103a4b188230a76f1707f3f44214bde086d00ce5962142e89`
- Hook tests: `5c70be016075a72d5a5c4d014715a2f1b2d540335aee9e35c041d816ccef9c74`
- Candidate Experiment: `c14f6786052b3cbaddb82185408b249765c271463444a73a6bb1df0550775772`
- Live Experiment remains the baseline hash stated above.

This repairs an identified asynchronous observation prerequisite. It is not a
benchmark retry or a newly executed performance result.

## Start/stop host heap completion

The adapter now invokes the existing `browserHeap(performance)` once at observation
start and once at stop. It copies both values and exposes them through the exported
`ReplaySessionObservationSnapshot` type as `host_javascript_heap.initial`, `final`
and `scope`. Missing/unsupported/throwing host access stays null, never synthetic
zero. Repeated snapshots, RAF observations and repeated stop calls perform no
additional heap reads. These are host-reported JavaScript heap observations, not
GPU or total-process memory, and they establish no automatic acceptance.

Four focused hook tests pass, including exactly two heap reads, defensive copies,
immutable stopped evidence and unavailable nulls. Typecheck and owned-file ESLint
pass; hook/test formatting was applied. No live Experiment edit, UI, context-key
field, clock change or native playback was introduced by this completion.
