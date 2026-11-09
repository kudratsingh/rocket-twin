# Replay sections are directly reachable

Continue merged PR111/main `0eabac94604d1c2d711567076ced17b1860de4a5`.
This joins the flow-controls follow-up with one new navigation capability; no
physical design, saved telemetry, simulation or source identity changed.

## Usable behavior

A compact sticky **Replay sections** bar offers Scene, Graphs, Events, Validity and
Data & limits. Each button focuses/scrolls the actual corresponding existing region
inside its own replay workspace. Data & limits opens the genuine instrumentation
disclosure so its diagnostics control is usable. No global-ID fallback, route,
clock, data, source, pose or controller mutation. Unknown/disconnected/foreign
regions are withheld. Native keyboard-operable buttons use existing browser behavior.

The shared shell already owns whole-page scrolling. Its auto-height experiment
had retained `overflow:auto` on the main element, creating an inactive inner
scrolling ancestor for sticky positioning. The narrowly scoped new stylesheet
makes that main element visible-overflow only under the existing shell; no broad
layout or canvas-sizing rewrite. The margin reserves room for the sticky bar.
Source helper and component filenames are distinct for case-insensitive Mac
resolution. [Implementation and focused checks](implementation.md).

## Actual evidence

[P19](../frontend-replay-section-navigation-native-20261108/browser.md) completed
36.954s inside90native/120overall. Graphs showed all four complete plot panels;
Data & limits opened instrumentation and visibly exposed Download replay
diagnostics JSON; Scene returned the actual canvas/controls. Exact cf9 G80 A /
ab60 G54 B stayed paused Free0.001. No Play, scroll, resize, export, run or FPS test.
The sticky bar partly covers the Scene heading; it does not cover the inspected
controls/canvas/plot panels. Prescribed compact sizes and full keyboard remain open.

[P20 tiled evidence](../frontend-replay-tiled-navigation-20261108/browser.md)
shows all four plot panels, diagnostics/download and Scene through those same
buttons after one native Left tile, with exact comparison/pausedFree0.001 retained.
No CSS dimensions were measured, so this is available-size behavior rather than
900/1280/1440 acceptance. Fill was skipped at the action-launch cutoff; the
separate [P21 restoration](../frontend-window-restoration-20261108/observation.md)
performed one freshly observed Fill, closed the menu and preserved replay state
in4.9344s. P20's skipped action is not retroactively marked complete.

P18's two wheel overshoots remain historical partial observations, not diagnosed
as physically unreachable controls. P19 tests direct navigation instead of repeating
that wheel method. P17 separately proves the revised flow layout without a HUD
covering the visible near-overlapping trail. Complete independent A/B path pixel
proof remains partial; raw recorded bounds are checked offline, not manufactured
into browser evidence.

## Integrated source checks

All254 local web tests pass, including four preserved/unpublished A2 cases;
250 are in publication scope. TypeScript, lint, formatting and the packaged app
build pass. Four new helper/SSR cases cover source-local target resolution,
disconnected/foreign targets, real disclosure opening, focus/scroll behavior,
semantic buttons and unchanged URL. The AST layout test preserves one Canvas.
Source tests are not native keyboard, exact viewport or performance acceptance.

Engineering/build, thermal/recovery/flutter, physical/test/purchase/paid work,
WO-10 and flight approval remain separate open gates. RP1/AD1/D1 and G54/G12
PID-to-RL remain unchanged; all five supplier/lab inquiries are UNSENT.
