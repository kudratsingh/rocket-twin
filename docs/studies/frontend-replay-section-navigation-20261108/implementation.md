# Replay section navigation — November 8, 2026

This bounded presentation packet addresses the actual P18 scroll overshoot without changing replay time, runs, URL, sources, actors or physics. P18's fifteen native artifacts remain frozen. No browser interaction, new run or performance measurement was performed here.

## Integration contract

Primary owns `Experiment.tsx` wiring; this packet does not edit it or its stylesheet. Import the component with its explicit extension on macOS:

```tsx
import { ReplaySectionNavigation } from './ReplaySectionNavigation.tsx';
```

The pure helper is named `replaySectionTarget.ts`, a distinct basename from the component even on a case-insensitive filesystem. The component explicitly imports this `.ts` helper and imports its own stylesheet.

1. Add `data-replay-workspace` to the existing replay `main`; the outer research region remains its scroll owner.
2. Place `<ReplaySectionNavigation />` at the top of that main, in normal flow before the scene/dashboard.
3. Add `data-replay-section="scene"`, `"telemetry"`, `"events"`, `"validity"` to their existing destination sections and `tabIndex={-1}` to each.
4. Add `data-replay-section="details"` and `tabIndex={-1}` to the existing native **Playback instrumentation** `<details>` element. The helper opens that genuine destination disclosure before focusing/scrolling, preserving its normal uncontrolled open/close behavior. Do not target a hidden descendant.

Visible order is **Scene, Graphs, Events, Validity, Data & limits**. Buttons are semantic `type="button"` controls inside a labelled navigation landmark. No hooks, callback props, state or extra scene instances are required.

`jumpToReplaySection(origin, section): boolean` resolves the origin's nearest `[data-replay-workspace]` and selects only a known constant destination whose nearest workspace is that same root. Nested or adjacent workspaces cannot supply a fallback target. Disconnected origin/root/target, unsupported keys and absent destinations return false without unrelated focus or global queries. A valid jump focuses with `preventScroll: true`, then calls `scrollIntoView` with automatic behavior/start alignment. It never writes replay state or URL.

The self-contained stylesheet keeps the navigation sticky at its scroll container's top, wraps buttons without negative margins and reserves target scroll margin. Native rendering, narrow wrapping and heading visibility remain for the designated browser owner to observe; SSR and DOM-method fixtures cannot establish those pixels.

Integration source inspection found that `workspaces.css` makes `.research-scroll-region` own scrolling while its Experiment child grows with content. The legacy `main { overflow: auto }` could remain an inactive overflow ancestor and trap sticky positioning. The one scoped correction sets `overflow: visible` only on `.research-scroll-region > .experiment > main[data-replay-workspace]` in the new navigation stylesheet. This preserves the existing single outer scroll owner; old layout styles are unchanged. Actual sticky tracking and jump visibility still require native observation.

## Focused checks

Four source tests cover workspace/nested-target scoping, missing/disconnected destinations without unrelated focus, opening only the target native details before focus, and actual component SSR with five ordered semantic buttons. Fixtures are in-memory objects and SSR; no browser fault injection or owner-run read occurs.

Scoped Prettier/ESLint and TypeScript typecheck pass. No full frontend, performance or engineering acceptance follows. All source/physical/build/flight gates, separate G54/G12 tracks and five UNSENT inquiries remain unchanged.
