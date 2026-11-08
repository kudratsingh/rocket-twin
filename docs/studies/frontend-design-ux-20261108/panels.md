# Design panel controls — 2026-11-08

The November 8 owner UX review requested independent, plainly labelled panel controls and internal Parts/Details tabs. This slice changes the Design shell and panel focus handling. It does not change the selected source, inspection store, geometry, viewer camera, engineering findings or supplier drafts.

## Implemented behavior

- The left end of the existing desktop header contains two persistent controls: **Show/Hide navigation** and **Show/Hide parts sidebar**. Their slots have fixed minimum widths, so changing Show to Hide does not move the adjacent control. Each controls the corresponding mounted panel and exposes its current expanded state.
- Parts and Details remain the two tabs inside the parts sidebar. The separate header Parts/Details openers and duplicate Layout-menu sidebar opener are removed. The internal close button remains available.
- Hiding and reopening the sidebar changes only its open state. The last Parts/Details tab and resized width remain in the existing versioned layout preferences. Both panels and the visual retain their existing mount positions. Selection and camera belong to their existing stores and are not copied into layout preferences.
- Closing the sidebar with its internal close button or splitter returns focus to the persistent sidebar toggle. Escape within the sidebar returns focus to the opening control, falling back to the persistent toggle if that control is disconnected, hidden or not keyboard focusable. Focus return waits for the hidden state to commit.
- Escape in the narrow overlaid navigation returns focus to its navigation toggle. Panel Escape is handled before the global clear-selection shortcut, including when focus is in the parts search input. Existing Focus snapshot/restore and its Escape behavior remain unchanged.
- Desktop header height remains 52 px, with the existing 56 px navigation rail and default 264 px sidebar. The default canvas allocation targets remain at least 72% of viewport width and 78% of height; this slice does not alter their thresholds.

## Source and software checks

Owned source changes:

- `web/src/workspaces/WorkspaceChrome.tsx`
- `web/src/workspaces/workspaceLayoutContext.tsx`
- `web/src/workspaces/InspectionWorkspace.tsx`
- Header/panel rules only in `web/src/workspaces/workspaces.css`
- `web/tests/revamp-layout-shell.test.mjs`
- `web/tests/revamp-layout-preferences.test.mjs`

Executed checks:

| Check | Result | Scope |
| --- | --- | --- |
| Targeted layout/chrome tests | 10 passed | All four rendered panel combinations; correct labels and expanded states; internal tabs; retained Details tab and width; one mounted visual; existing source markers; Focus preference restoration; focus-return scheduling and hidden/disconnected-opener fallback. |
| Scoped ESLint | Passed | The three owned TSX source files. |
| Prettier | Passed through formatting | Owned source, CSS and targeted test files. |
| Integrated TypeScript, initial attempt | Pending integration | Reported missing `FinAlternatives` imports and unfinished Viewer orbit-control symbols/unused variables in other active lanes. No errors were reported in this slice. The primary integrator owns the final check. |

The focus tests use a small document/window fixture to check the scheduled return target. SSR checks establish markup and stable mount structure. They do not establish actual browser focus, pixels or pointer interactions.

## Browser acceptance queued

No browser calls were made for this code slice. The primary integrator will signal when the combined source is ready; the existing designated verifier then uses the same owner-authorized Chrome window.

At 1440×900 and 1280×720, 100% zoom, verify both visible controls by pointer and keyboard for all four panel combinations. Check last-tab/width retention, selected part and camera retention, internal Parts/Details tab arrows, close-button/splitter focus return, and Focus/Exit focus/Escape restoration. With tools closed, measure the default canvas against the unchanged width/height targets.

At 900×720, verify the parts drawer opens, closes with Escape from its search input and Details tab, and returns focus to the opener without clearing selection. At narrow mobile width, verify the navigation overlay Escape return and the labelled controls remain reachable. Retain any failed or unexecuted outcomes explicitly; do not promote source tests into browser acceptance.

All five inquiry drafts remain UNSENT. WO-03, engineering/build, physical/test, paid-run, WO-10 and flight gates remain unchanged.
