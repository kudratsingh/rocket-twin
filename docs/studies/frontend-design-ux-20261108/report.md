# RP1 Design interaction correction — November 8, 2026

Source: the [owner's interaction review](owner-review.md), continuing from published PR97 / main `a4db05ef4cbd68fd957a1c803d98557d6171ea3e`. This packet changes inspection presentation and interaction only. The prior release's recorded browser evidence remains historical evidence for that implementation.

## Frozen design and display identity

- Design: `G80-F2-RP1-AD1-definition-v2`.
- Source specification: `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`.
- Display geometry: `238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`.
- 55 source records, 26 mesh-bearing records; source quantities and bundled solids are separate concepts. Mass allowances need no separate solid; missing geometry stays unavailable.
- Source physical positions, geometry, mass, D1 loads and engineering findings are unchanged. Presentation offsets are illustrative, not a collision-free construction/service sequence.

## Bounded delivery and ownership

| Deliverable | Owner / attempt budget | Acceptance / stop |
| --- | --- | --- |
| Stable independent panel toggles | Sol HIGH designated browser owner; one 45-minute implementation plus one correction | Same labelled controls in both states, retained tabs/width/selection/camera; browser focus and dimensions observed separately. Stop at inaccessible authorized window, no bypass. |
| Actual camera pose and target | Sol HIGH camera owner; one 60-minute implementation plus one correction | Independent projection tests, continuous horizontal angle, poles/roll, actual readout; fit/frame retain angles, reset Overview, clipping recovers. No replay math change. |
| Functional groups and staged offsets | Sol HIGH source owner; one 60-minute implementation plus one correction | Every stable ID has exactly one primary group, exact source guards, real mesh bounds prove selected display separation, zero exact source positions. No CAD/physics adoption. |
| Tree, selection safety and fin comparison | Primary | Meshless selection never blanks the scene; source parentage not a structural claim; in-context AD1/FP1/FR1 preserves Design state. Stop at missing source data with unavailable state. |
| Combined verification and publication | Primary + sole designated Chrome owner | New RV-Q38–42 evidence, required exact-head hosted checks before merge. Earlier screenshots do not pass new behavior. No extra review gate. |

## Implemented shared-state changes

The available mesh IDs are registered from the verified source document before it is displayed. Isolate and Frame refuse meshless selections at the store boundary, in addition to disabled Details and scene-tool controls. Such a record still selects its stable ID, opens details and links to compatible evidence. Group isolation records the previous hidden IDs and restores them on exit; Restore assembly preserves source and selected stable ID.

The functional tree reports records and meshes separately and labels the display maturity of each record. It uses the same source/geometry admission helper as the staged breakdown. Selecting a displayed component reveals its functional group and row. Recorded source parent/child relationships in Details are explicitly provenance, not proof that one part physically supports another.

Fin comparisons open in a modal over the still-mounted Design scene. Closing via its return control or Escape returns focus to the opener without changing the source, selected ID, display state or camera. The global inspection keyboard handler ignores open-dialog input. AD1's failed panel calculation and missing installed evidence remain explicit. FP1 and FR1 remain distinct unadopted schematic-only studies; no alternative 3D geometry or accepted stress map is created.

## Verification status

Integrated local checks pass: 188 frontend tests (including four preserved unrelated/unpublished A2 tests;184 belong to this publication), lint, formatting and production build; seven new Python presentation tests plus scoped Ruff/Black pass. The [panel](panels.md), [camera](camera.md) and [presentation](presentation.md) reports separate source/numerical tests from visual behavior. The owner restarted the host preview after preparation. The sole designated Chrome agent is checking RV-Q38–42 against the combined implementation; new live interaction acceptance remains pending its recorded outcomes. No screenshot or browser pass is claimed by this source-only publication.

The five supplier/lab inquiries remain UNSENT. No new material, construction variant, solver campaign, purchase, physical test or flight is admitted. G80 stays first; G54 and G12 PID-to-RL remain separate committed tracks. No engineering requirement closes merely because this display packet passes.

## Bounded visual correction

The initial actual native captures exposed two real overlay failures: new assembly-display controls covered the existing 3D/2D tabs, and the always-visible camera readout covered the selected part’s Engineering/Details summary. The controls are now in the existing Scene tools drawer; their explanatory text remains available there. The selected-part summary is positioned above the readout in its owning stylesheet. An initial duplicate override lost to the later-loaded stylesheet and is preserved as a failed correction observation; the owning-rule correction is visibly clear in the designated agent’s subsequent native capture. The new camera controls remain visible with Scene tools closed. These observations are confined to the current native window, not the requested viewport-size matrix.

Automatic approval review rejected opening Chrome DevTools, citing the restriction against console/CDP or bypass tooling. No retry or indirect viewport workaround followed. Ordinary app interactions and native captures continued in the same authorized window. Exact responsive viewport/capture setup remains unavailable under that review; it is not inferred from the native raster size. The full RV-Q38–42 rows cannot close on those limited observations alone.
