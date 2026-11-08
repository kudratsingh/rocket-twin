# Focused Design/Engineering closure observations

The approved six-minute packet completed its normal current-window cases without a guard, access failure or correction attempt. Earlier failed/exhausted packets remain unchanged. No Replay, performance measurement, simulation, DevTools or viewport workaround was attempted.

Release baseline: merged PR104 `ecd0f74bae33ec3ef019e690ef95c023b92ecbe9`, source head `a07c9e1fe962a81b576963fd6e092e8ec9db2aaa`; the primary froze Design source for this packet. The [offline plan](plan.md) records PR101–104 publication metadata and the narrowed scope. Browser evidence remains separate from merge/check evidence.

| Case | Actual observation |
| --- | --- |
| Fin group entry / Return | Fins and roots→Compare fin alternatives opened the preview-first dialog, with AD1/model-limit tables collapsed below it. Return retained Fins group, custom 438.9°/60.9°/0° camera, current interior visibility and focus on the group opener. |
| Selected fin Details / Escape | Selected `fin_set`→Details→Compare fin alternatives→Escape retained its exact RP1/spec/part URL, 267 px sidebar, selected Fin set target and 438.9°/60.9°/0° camera. Focus returned to the Details opener. The tree showed 23/26 visible before and after these contextual paths, retaining the existing shell-hidden view. |
| PCB Escape correction | `high_g_accel` Details→Open PCB layout→Escape now closed only the drawing. The sidebar stayed open, native app AX stayed populated, part/spec URL and camera stayed intact, and focus returned to Open PCB layout. This is the new source-fix observation; the earlier failed capture remains a failure in its original packet. |
| Keyboard route and history | A normal load of the previously observed exact `fin_set` Design URL was followed by ten actual Tabs, which focused Engineering; Enter opened Engineering. Browser Back returned Design and Forward returned Engineering, retaining the same configuration/specification/part. This is a specific route/history case, not the unknown/stale/legacy URL matrix. |
| Actual drawing export | Engineering→RP1 FP1/FR1 studies→Export study SVG produced a fresh 14788-byte browser download. The copied bytes parse as SVG and embed RP1/specification, exact FP1 study/source hashes, unaccepted/not-adopted status, installed acceptance false and units. SHA-256: `d18eca4472ba0f350d50794f0d7954d5b7a73ce49251756c629bf973e1079508`. |

Final capture shows same-source RP1 Design, no individual part URL, 26/26 meshes visible, both panels/Parts open, interior off, source detail on, dialog/tools closed and Move selected. Whole rocket produced 45°/54.7°/0°, Target: Assembly. Computer use ended before the 360-second cap; the [session record](../../../runs/frontend-release-closure-20261108/record.json) gives the exact capture-backed elapsed time.

These observations address normal subpaths in RV-Q42/Q45, PR103 dialog Escape, and portions of RV-Q05/Q07/Q11/Q16/Q21/Q34. They do not pass compound rows containing unexecuted responsive, full-keyboard, missing/mismatched, delayed/malformed or other fixture branches. No finished alternative assembly, manufactured PCB/fit, engineering/build or flight acceptance is inferred. All inquiries remain UNSENT.

Four unchanged native JPEGs, native AX records and the actual downloaded SVG are local evidence under `runs/frontend-release-closure-20261108/`. Screenshots include browser chrome and establish no CSS viewport size. The [inventory](evidence.json) hashes the finalized record and excludes itself. No gallery or shared-ledger edit is part of this packet.
