# Clearer CAD inspection — limited WO-04 increment

Owner direction: 2026-11-02 Pacific. Improve the saved frontend's rocket and
internal-part visualization while C1 engineering continues. The existing
React/Three.js renderer, three-panel layout, mesh API and recorded geometry
identities are retained. No new dependency, physical model or CAD generation.

## Controls

- **Overview / Front / Side / Motor end** frame the currently visible geometry
  or a previously focused part from the named direction. The motor-end view
  looks along the rocket from its aft end; it is an end view, not a side view.
- **Focus part**, **Focus in 3D**, or **F** centers the camera on the selected
  part's actual loaded mesh bounds. A hidden selected part is restored while
  other visibility choices are retained. Parts without a mesh cannot be focused.
- **Fit visible** fits the currently visible assembly at the chosen angle.
  **Reset view / R** restores the overview and clears camera focus. Part
  selection, visibility, section and explosion settings are preserved by reset.
- **Transparent shell** makes recorded outer-body parts translucent so internal
  parts can be selected through them. The shell remains selectable in the parts
  tree. It does not change the source wall thickness, material or analysis.
- **Selected-part label** identifies the selected part and its source material
  in the scene. The existing right inspector provides the specifications,
  function, build method, connections and evidence.
- **Wireframe** shows the triangles of the display mesh. These are not a
  finite-element analysis mesh or a statement about numerical convergence.
- The **X/Y/Z orientation widget** follows the camera. The source mesh frame
  remains unchanged, with Y pointing toward the nose. It is an indicator;
  use the named view buttons to change viewing direction.

Orbit, zoom, pan, section cut, hide/isolate, exploded view, source CG/CP markers
and recorded experiments/replay are retained. Ghost styling, wireframe and part
labels are excluded from recorded Analysis rendering. Selecting a different
configuration clears focus and display settings to avoid carrying candidate
part IDs or styles into another design.

## Geometry and engineering boundaries

The active reference assemblies and the separate archived **72-part G80 retention
candidate** use their existing exact CAD exports. Camera framing uses their
actual visible bounds; the unloaded fallback uses recorded vehicle length only.
No mesh, engineering specification, mass, balance, motor or flight input changes.

**C1 is still a numerical mass/balance study without a complete CAD export.**
The archived retention candidate is not C1 and cannot supply its geometry,
strength or thermal evidence. The viewer does not construct missing C1 joints.
Engineering acceptance, purchases, physical work, paid runs, WO-10 review and
flight release retain their existing gates. Full WO-04/05 remains open.

## Verification and remaining observations

Executed locally:

- `npm --prefix web test`: 22 tests pass, including depth-aware camera framing
  in portrait/wide viewports, motor-end orientation, tiny bounds, invalid input,
  hidden-part focus/visibility and display-state reset across design changes.
- `npm --prefix web run build`: TypeScript and production build pass. The
  existing large-bundle warning remains.
- `npm --prefix web run lint` and `npm --prefix web run format:check`: pass.
- Read-only HTTP checks returned200 for the running Vite server and API.
  Vite serves the new viewer module and styles; the catalog lists all four
  active configurations and the available archived candidate. The G80 endpoint
  returns42 parts with42 mesh URLs. This establishes source/API availability,
  not a browser rendering or interaction result.

No browser verification or screenshot is claimed for these controls. The earlier
automatic approval review rejected the designated frontend agent's runtime
ownership check; that recorded blocker is unresolved. No alternate window,
computer-use attempt or headless workaround is used by this increment.

Pending designated-window checks: all four active models and the archived
candidate; camera presets, focus after hide/explosion, internal selection through
the shell, wireframe/section combinations, label readability, narrow desktop
scrolling, orientation tracking and unchanged Analysis/replay. These remain
unobserved runtime behavior; the local tests do not replace visual inspection.

## Open on this Mac

Start the existing preview in the owner's terminal:

```sh
cd /Users/kudratsingh/Machine-Learning-Projects/rocket-twin
make preview
```

Expected URL: <http://127.0.0.1:5173>. Existing compatible CAD exports and the
prepared candidate snapshot must remain available. Vite reloads frontend source
changes; an API restart is required only after backend code changes. This
increment does not regenerate CAD or change the backend.
