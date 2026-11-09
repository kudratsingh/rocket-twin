# Frontend completion — comparison framing, exports and focus

Continue merged PR110/main `6a12c2b8b2a78d436cc24ecac7c05c80c5eb6ca7`.
This increment changes inspection/replay usability and evidence handling only.
G80 RP1/AD1 v2 remains source `811b3bed…31660`, with26 mesh-bearing records
among55; no vehicle adoption, physics, telemetry, inquiry or hardware change.

## User-visible changes

- **Fit both trajectories** appears when comparison B is loaded. Both ordinary
  replay controls and the in-scene control use the same action. Without B the
  action remains **Fit A trajectory**. It enters Free orbit and encloses finite
  recorded positions from the loaded runs, including B's later recorded window.
  It does not clamp B to A, change the replay cursor, interpolate missing data or
  borrow geometry. Missing positions remain unavailable.
- Perspective framing accounts for the narrower horizontal/vertical viewing
  angle; a tall/narrow canvas no longer relies on a fixed distance multiplier.
  This is camera geometry, not an engineering or flight calculation. The view
  uses a containing sphere with10%plane-distance reserve and a sufficient far
  plane; pixel framing and responsiveness remain separate browser checks.
- **CSV and companion metadata** now reject the same invalid recorded coverage.
  Duplicate/nonfinite/reversed time axes and impossible channel lengths cannot
  publish apparently usable metadata while the corresponding CSV is withheld.
  Valid zeroes, short/missing cells, original timestamps and source/metric values
  remain unchanged. Invalid comparison coverage is also withheld.
- Closing a sidebar returns keyboard focus to a usable visible opener. If resize
  hid, detached, disabled or made that opener inert, the existing stable toggle
  is used if usable. No new page-level shortcut or layout behavior is introduced.

## Source and recorded-data checks

All249 local web tests pass, including four preserved unpublished A2 cases;
245 are in this publication's source scope. The ten combined focused tests pass.
TypeScript, lint, formatting and the production build pass. The build retains
its existing large-vendor-chunk warning; no frame-rate acceptance follows.

Four view-bounds tests cover the NED→east/up/south conversion, complete unequal
windows, invalid time/coverage, finite zero/missing positions, immutable source
arrays and independent sphere/frustum containment at aspect0.4/1/2.5.
One read-only recorded-data packet compares production view bounds against
independent NumPy min/max for all248,885 recorded position samples from saved
G80 cf9e and G54 ab60 runs. It passes, retaining each Parquet hash and exact
window in [recorded-bounds-check.json](recorded-bounds-check.json). Python work
reported0.767s; JS parse/calculation103.217ms. This is not a replay frame-rate
measurement, full RP1 flight or browser pixel proof. No simulation ran.

[Export findings](experiments.md) and [focus findings](navigation.md) retain their
individual scopes. Production source hashes are frozen for native verification;
old P12/P13 images never become evidence of the new Fit action.

## Native evidence and limits

P14 stopped at entry with zero UI actions when the owner was using an unrelated
Settings page. Native access worked; preview availability and reachability were
unexecuted. Private contents were not captured or retained. The owner subsequently
said Ready, authorizing the designated verifier's new separately budgeted P15.
See [P14](browser.md). [P15](../frontend-completion-verify-20261108/browser.md)
confirmed current RP1 entry, then the runtime's user-change guard stopped the first
navigation action. There was no retry, screenshot, pair/Fit/tiling/reachability
observation or final-state restoration claim. Last pre-action19.401s and guard
call5.912s remained bounded. The source fixes are code-verified, not newly accepted
browser interactions. A specific hands-off verification interval is requested;
independent publication continues without bypassing that guard.

The exact1440×900/1280×720/900×720 matrix and representative long-run performance
criterion remain open, as do data-dependent spatial-result branches. No previous
failed/capped attempt is rerun or overwritten, and no unsupported browser route is
used. Supplier/lab messages remain UNSENT; engineering, prototype, purchases,
physical tests, paid work, WO-10 and flight approval are distinct open gates.
