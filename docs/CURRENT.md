# Current engineering and inspection checkpoint

**G80 first. C1 is preliminary. R1/C2/C3 remain rejected.** Substantial custom
construction, maximum practical performance and committed G12 PID-to-RL remain
core goals; G54 remains a separate upgrade. Expanded WO-03 and every build,
purchase, paid-run, firmware-review and flight-release gate stay open.

## Engineering decision

Prefer **A: integrated through-body motor/fin can** for a bounded connection
study; **neither A nor B is admitted to detailed vehicle CAD/FEA**. Both are
separate concept studies, not changes to C1 or the active vehicle.

| Complete case, separate50 g included | Mass | Balance from nose | Stability |1.5 m departure |1.8 m conditional departure |
| --- | ---: | ---: | ---: | ---: | ---: |
| A nominal |968.309 g |844.352 mm |1.856 cal |14.914 m/s |16.341 m/s |
| A additional20g/motor-CG |988.309 g |853.756 mm |1.713 cal |14.743 m/s |16.155 m/s |
| B nominal |995.812 g |852.518 mm |1.732 cal |14.680 m/s |16.086 m/s |
| B additional20g/motor-CG |1015.812 g |861.506 mm |1.596 cal |14.516 m/s |15.907 m/s |

A saves161.498 g from C1 but still needs29.911 g additional saving for the
adverse **formal15 m/s** case on the unchanged1.5 m guide. Separate15.5 planning
needs84.455 g. Longer usable travel remains unconfirmed and conditional.
The retained-upper interface audit also fails the proposed A/B cold-fit stack:
64.0mm model coupler /64.4mm bore gives0mm worst-case radial clearance under
the declared bounds, versus0.1mm required. [Audit](wo03-architecture-interface-audit.md)
records the issue without resizing a part or changing frozen mass results.
The other controlling items are finished hot root/recovery joints, finite
cap/body load spreading, exact G80/retainer fit, heat and installed stiffness.
Full rotational inertia is unavailable. **No installed engineering requirement
closed.** The two-arrangement study is complete and stopped at admission.

- [Decision and complete mass/margin evidence](wo03-architecture-decision.md)
- [Actual function allocation and A/B concept drawings](wo03-architecture-function-allocation.md)
- [Primary-source and later owner-only measurement plan](wo03-architecture-source-packet.md)
- [Unsent ROC/MDARS equipment questions](wo03-launch-owner-confirmation-20261102.md)
- [Bounded work list and responsibilities](wo03-current-worklist.md)

## Open the inspection workbench

Run `make preview` at the repository root, then open:

`http://127.0.0.1:5173/?workspace=engineering`

The preserved arrangement/section/force/mass views now have companion graphical
views selected with `&view=comparison`, `recovery`, `thermal`, `electrical`,
`assembly` or `requirements`. They display versioned backend data and link
selection to the current C1 inspector when a valid part mapping exists.
New A/B concepts have no fabricated C1 part/CAD association.

| Local artifact | What can be inspected |
| --- | --- |
| `output/rocket-twin-review/index.html` and `review-pack.zip` |Self-contained gallery and downloadable pack of recorded drawings/native images |
| `output/engineering-walkthrough/index.html` |25 C1/R1 SVG drawings with units, source/status and configuration metadata |
| `output/engineering-walkthrough-rendered/contact-sheet.png` |25 real offline raster pages; representative labels/arrows actually inspected |
| `output/engineering-workbench-extended/index.html` |New comparison/recovery/thermal/electrical/service/requirement SVGs and actual PNG previews |
| `output/wo03-architecture/architecture-A-motor-fin-can.png` |Dimensioned A concept and protected volumes, not detailed CAD |
| `output/wo03-architecture/architecture-B-outer-captured-roots.png` |Dimensioned B concept and unresolved connections |

The135 C1 source allocation/envelope rows are not a manufacturing-ready CAD
assembly. Archived72-part CAD remains separate. Recorded thermal histories
and failed fixtures stay historical/incompatible with current C1; absent spatial
fields/time samples/pins/inertia stay unavailable. Deployment/service storyboards
are illustrations, not validated mechanism/deployment simulations.

Offline image rendering now works with the installed documented AppKit
image-document API. Actual image inspection identified and corrected exported
arrowhead portability; no browser/window or dependency installation was used.
Raster images do **not** prove browser interactions or frame rate. Host URL
reachability, clicks/downloads, responsive layout and WebGL remain pending the
designated browser agent's runtime-ownership prerequisite. The last automatic
approval rejection is not retried or bypassed.
