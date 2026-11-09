# Narrow-layout focus restoration — 2026-11-08

Scope: RV-Q07 keyboard/reachable controls and RV-Q12 responsive drawer restoration.
This packet addresses one source-confirmed focus-target selection gap. It does not
complete either compound browser criterion.

## Finding and bounded correction

`restorePanelFocus` previously accepted an opener when it was connected, tabbable,
and outside a `[hidden]` ancestor. A responsive CSS rule can instead remove a control
from layout without changing those properties. For example, the Design context
resizer is `display: none` below 1100 CSS px. A target hidden between dismissal and
the next animation frame could therefore be selected instead of the stable panel
button. Disabled and inert targets were also not excluded.

The implemented guard rechecks the target after the existing animation-frame delay:
connected, tabbable, outside hidden/inert ancestors, enabled, with rendered client
rectangles and visible CSS visibility. It retains a usable original opener;
otherwise it uses the existing stable panel toggle. An unavailable or hidden
fallback is not focused. It adds no layout state or scrolling operation.

No shell resize/scrolling change is justified by this source inspection. Existing
compact panel dimensions and scroll containers are retained. The current replay
source, camera, telemetry, exact source identities and all engineering records are
outside this change. All five inquiries remain UNSENT.

## Validation boundary

The focused test uses explicit DOM method doubles to verify deferred target choice,
a resize hiding the opener before the callback, detached/untabbable/hidden/inert/
disabled targets, CSS visibility, valid opener retention, and missing/hidden fallback.
These checks exercise production target-selection logic. They do not measure browser
layout, actual focus, keyboard reachability, viewport overflow or zoom behavior.

The staged production function first passed an isolated Vite SSR override check for
a valid opener and seven unusable-target cases. After primary confirmed the native
lane idle, the component and existing test fixture were applied. The new focus test,
existing layout-shell tests and workspace-chrome test pass (four tests total).
`npm run typecheck` and `npm run lint` pass. Owned-source Prettier checking passes. The initial global
format check reports only the concurrently edited `replayTrajectoryBounds.ts` in a
separate lane; that file is outside this packet's ownership. Primary subsequently formatted that lane and the integrated global formatting check passes.

P14 stopped before UI action when native entry found the owner's unrelated Settings
context. This blocks the native verification; it is not a failed focus or scrolling
observation. No browser action was performed by this source worker.

## Remaining native checks

In the authorized Chrome window, record actual CSS viewport and zoom. At desktop
and compact widths, open Parts/Details, reach the last control by keyboard and scroll,
then dismiss using Escape and the close control. Confirm focus returns to a visible
usable control. Resize while a potential opener becomes hidden, dismiss the panel,
and confirm the stable toggle receives focus without changing the selected part,
camera or source. Check rail, details and tools scroll ends, no horizontal body
overflow, and retained native browser zoom. RV-Q07/RV-Q12 remain partial until their
full scenarios are observed; this source packet supplies no new browser acceptance.
