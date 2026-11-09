# P13 read-only viewport-helper clarity

The scoped helper check passed in **33.601 active seconds**, before the hard 90-second native cutoff and120-second overall cap. The owner reported100% page zoom; it was **not independently verified**, and DPR2 is not used as zoom proof. No zoom/window setting was changed.

The helper was already mounted in the authorized Chrome tab at `/?workspace=design&design=G80-F2-RP1-AD1-definition-v2&verifyViewport=1`. No navigation, reload or other tab/window interaction was needed. Actual content readout was **2240×1109 CSS pixels, DPR2**. This is current-size information, not prescribed1440/1280/900 layout acceptance.

| Case | Actual observation | Outcome |
| --- | --- | --- |
| Information-only readout |“Browser size · information only”, actual content size/DPR and explicit cannot-resize/page-zoom wording are visible. Comfortable window size is sufficient to use the app. |Passed |
| Old selector removal |No Requested size selector appears in the live helper AX or native image. |Passed |
| Reference disclosure |One click opens static1440×900,1280×720,900×720 list text. Copy explicitly says references are not resize controls; exact-size checks remain pending; DPR does not establish zoom. |Passed |
| Zoom distinctions |Copy distinguishes Chrome page zoom, rocket camera zoom and macOS Window→Zoom. No controls/settings were operated to verify those instructions. |Visible copy passed |
| Hide/normal Design |One Hide size information click removes the helper; RP1 tree,26/26 mesh visibility and normal scene controls remain available. |Passed |

The opened-reference and final-hidden screenshots were inspected offline. Both are genuine unchanged native JPEGs. The information panel fits within the current window. Final camera remained the owner's existing Custom30.3°/72.1°/0° Assembly target; no unrelated camera/part reset occurred. The helper is hidden in the current mount, while `verifyViewport=1` remains in the URL and may mount it again after a reload.

Before-action elapsed checks were12.837 and32.776 seconds. No native work was launched near the cutoff, and no further CUA followed the final capture. No simulation, Replay Play, resize, zoom shortcut, DevTools, fault injection, source edit or other application interaction occurred.

The new local helper fingerprint is `f12c6e8aea9b082e0f63b54ce568f6fee6402b46d2ff0747d74f82a1896b162e`, pinned in [source-freeze.json](../../../runs/frontend-viewport-clarity-20261108/source-freeze.json). It was unpublished at capture per primary. App/scene/math/source geometry were unchanged per primary; this helper packet did not reverify their API fingerprints. Publication remains primary-owned.

The [session record](../../../runs/frontend-viewport-clarity-20261108/record.json) preserves exact observations, owner-reported zoom, timing guards and retained state. Native raster dimensions are separate from the app's measured CSS values. Exact viewport, performance and engineering/physical/flight gates remain unchanged. Primary's `report.md` was not edited or inventoried by this agent. CUA is idle with normal Design usable and helper hidden.
