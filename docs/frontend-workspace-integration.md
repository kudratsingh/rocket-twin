# Focused workspace shell integration

Primary integration is now implemented in App.tsx/store.ts, with independent Engineering topic loading and linked2D. The contract below remains implementation reference; browser interaction acceptance is still pending.

2026-11-03 bounded shell increment. Components are implemented; primary integration
and actual browser observation are separate states. No shared files or engineering
workbench/F2 modules were edited by this implementation owner.

## Components and ownership

- `web/src/workspaces/WorkspaceChrome.tsx`: `WorkspaceFrame`,
  `WorkspaceNavigation`, `WorkspaceIdentityStrip`.
- `web/src/workspaces/InspectionWorkspace.tsx`: stable mounted inspection slots,
  panel visibility, focus view and Escape handling.
- `web/src/workspaces/navigation.ts`: pure URL helpers and workspace labels.
- `web/src/workspaces/workspaces.css`: local layout styles, imported by components.
- `web/tests/workspace-navigation.test.mjs` and `workspace-chrome.test.mjs`:
  URL/identity regression and server-rendered semantic checks.

The integrator retains App/store/types/API/global CSS ownership. These components
introduce no data fetches, physics, dependencies, source substitutions or run gates.

## App integration

Import the three chrome components, `InspectionWorkspace`, `readWorkspace`,
`workspaceHref` and `WorkspaceId` from their respective modules. Replace legacy
Mode with the canonical keys `design | engineering | experiments | replay | analysis`.
`readWorkspace(location.search)` accepts existing `inspect`, `workbench`, `experiment`
aliases and returns a recoverable notice for unknown workspaces.

Replace the outer `app-shell` with this composition; do not nest it inside the old
fixed-height/hidden-overflow shell:

```tsx
<WorkspaceFrame
  header={/* existing topbar: brand, relevant configuration picker and glossary */}
  navigation={
    <WorkspaceNavigation
      active={workspace}
      href={currentHref}
      onNavigate={(_workspace, href) => navigate(href)}
    />
  }
  identity={
    <WorkspaceIdentityStrip
      name={displayedSourceName}
      maturity={displayedGeometryMaturity}
      state={displayedResourceState}
      resource={displayedRunOrResultLabel}
      details={/* source links, full identities and detailed limitations */}
    />
  }
  footer={/* compact relevant workspace status, not stale inspection mass */}
>
  {/* independent workspace body and its loading/error boundary */}
</WorkspaceFrame>
```

In the Design branch replace the existing `inspection-workspace` main element:

```tsx
<InspectionWorkspace
  tree={<PartsTree key={vehicle.id} parts={vehicle.parts} candidateMessage={catalog?.candidate_message} />}
  visual={<Viewer key={vehicle.id} vehicle={vehicle} mass={mass} burn={burn} onBurnChange={setBurn} />}
  inspector={<InspectionPanel key={vehicle.id} vehicle={vehicle} mass={mass} />}
/>
```

The layout retains all three children in fixed positions and hides sidebars with
`hidden`, so focus/panel toggles do not remount the viewer or clear tree/inspector
state. Key by **source identity only**, never focus/visibility. Desktop columns
reserve 64% for the visual. Below 1300 CSS pixels, secondary panels move below the
full-width visual and can be hidden; this avoids squeezing the model at zoomed
widths. The scroll region owns page scrolling; panel scroll chaining remains enabled.
The header and navigation remain outside that scrolling region. Check that existing
footer content wraps at narrow sizes; do not restore a 700px shell minimum height.

Focus view hides secondary panels and enlarges the same visual. Escape capture
exits focus and restores focus to its button before legacy selection-clearing runs.
Keep global shortcuts limited to the active workspace; the App handler should return
when `event.defaultPrevented` and must not run inspection shortcuts in Experiments
or Replay. Any later modal/popover Escape policy must precede focus exit explicitly.

## Routing and identity integration requirements

1. Store the current relative URL in App; listen to `popstate`. Navigate with
   `history.pushState` then update App state. Do not replace every render with
   `replaceState`, which breaks Back/Forward. Navigation anchors retain standard
   modified-click/open-new-tab behavior and work without the click callback.
2. `workspaceHref` preserves `view`, design/run/part/result and fragments. Existing
   Engineering links remain valid. Keep topic routing in the workbench owner; this
   shell does not guess a topic or silently choose C1. Default Engineering must be
   derived from the currently supported source records, independently of archived CAD.
3. `designHref` deliberately clears `part`, `run`, `result`, `compare` on identity
   change. It does not establish that a retained `view` is compatible. Reset incompatible
   store state and show an explanatory message in App; validate URL IDs against
   fetched data before attaching anything. Unknown IDs must not silently select a
   different design. Do not carry unsupported experiment overrides across designs.
4. Mount the same experiment component for Experiments/Replay using the replay
   owner's presentation prop and route contract, preserving its run/time state.
   Do not key it by workspace. Do not invent a second experiment state or pose pipeline.
5. Move catalog/vehicle errors into the Design/Analysis branches they affect.
   Engineering and independently available run loading must remain reachable.
   Loading/retry states must identify the requested source without showing old
   content as current. Maturity/identity strings must come from the displayed
   record; the strip deliberately contains no C1/F1/F2/default source names.
6. Remove the duplicated acceptance banner/context strip after supplying the new
   identity strip. Keep open-finding severity visible and full limitations reachable.
   Engineering has its own source labels: until a compatible identity callback
   exists, use an explicit neutral label and direct the reader to the selected
   source inside that workspace rather than asserting a guessed design identity.

## Checks and pending acceptance

`npm run typecheck`, scoped ESLint, Prettier and route tests passed during the
component increment. The SSR test validates semantic output only. The integrator
must run the combined build/tests after shared-file changes. No browser, headless
browser or alternate computer runtime was used.

QA-02/03/05/08 remain pending in the designated browser: 1280×800, 1440×900,
1920×1080 at 100/125/150% zoom; actual visual width, long-content/panel boundary
scrolling, focus/selection/camera preservation, keyboard navigation and Back/Forward.
CSS proportions and SSR do not establish those outcomes. No engineering, physical,
flight or replay-performance acceptance is asserted by this shell increment.
