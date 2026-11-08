# Direct camera movement correction — November8

The owner reports that rotation alone does not let them reposition a bottom close-up or return easily to the whole rocket. Prior native rotation/zoom evidence did not establish this workflow. This corrective packet changes display interaction only; RP1 source geometry, AD1/D1, mass, simulator and engineering gates remain unchanged. Inquiries UNSENT.

## Bounded scope and implementation

One input/UI correction, focused regression checks, one designated same-window browser attempt and at most one correction recheck within four active minutes. No DevTools, responsive-matrix bypass, other window, new engine, simulation or engineering calculation. Stop on unsupported runtime/access, guard or cap; preserve failures.

Move view / Rotate view are visible choices. Ordinary left drag defaults to Move; a scene point follows the pointer in the viewing plane without rotating. Right/middle/Shift/Ctrl always pan; Alt rolls; two-pointer pan/pinch remains. Click selects; dragging cannot fall through to surface picking. Mode changes explicitly dispose and rebind the gesture owner.

Pan uses the perspective scale including camera zoom and immediately updates its world matrix. Independent projection tests check exact pixel displacement across roll/poles, equal camera/target translation and unchanged rotation/distance. The original pan signs were correct and retained.

Whole rocket resets to Overview and frames all loaded assembly bounds even after a selected-part close-up. It preserves visibility/isolation; Restore assembly is the separate visibility/display reset. Fit assembly retains the current angle.

## Executed evidence and limits

Fourteen focused tests pass. All208 local frontend tests pass (four preserved/unpublished A2 cases excluded from publication scope); typecheck, lint, formatting and packaged build pass. The final explicit effect dependency also passed typecheck/lint; hosted checks validate the published integrated tree.

The [native browser record](browser.md) preserves an initial default-Move drag that incorrectly rotated. After explicit mode-dependent binding and one normal reload, the verifier observed Move translation retaining45/54.7/0, Rotate changing to15/38.7, wheel zoom retaining displacement and aft-ring Frame→Whole returning Overview. This does not isolate the cause of the in-flight-HMR failure. Native elapsed212.967s, within240s. The final view is whole assembled RP1, Move selected, Assembly target, aft_ring selection retained.

The [inventory](evidence.json) hashes14 artifacts. JPEGs/AX are local-only; the small session record is tracked. Prescribed viewport dimensions, physical mouse sensitivity/latency, modifier gestures and arbitrary hidden sets were not browser-tested. Earlier13/29/9 inventories remain unchanged. No further CUA attempt in this packet; no engineering/build/flight acceptance.

Open the running preview and reload once to load the completed handler/UI together. Move view is the default; Rotate view changes drag behavior, and Whole rocket recovers the overview.
