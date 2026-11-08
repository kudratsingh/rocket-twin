# P7 visible part-link recovery — 2026-11-08

The single changed-source recheck **passed its scoped Design cases in 97.282 active seconds**, within 150. Both stale and missing part warnings are visibly rendered in normal flow without opening Source & limitations. Clear canonicalizes the exact source URL, and valid nose/fin selection still works. P6's earlier hidden-warning failure remains unchanged.

| Case | Actual observation | Outcome |
| --- | --- | --- |
| All-zero stale spec + valid `nose` |Warning directly below header; Clear invalid part link visible; Frame selection disabled. No historical part substituted. |Passed |
| Clear stale link |Actual URL becomes exact RP1 spec 811b3bed…631660 with no part parameter; warning disappears. |Passed |
| Correct spec  + `missing-p7-part` |Same visible warning/control and withheld selection. Source disclosure was never opened. |Passed |
| Clear missing link |Canonical exact source URL with no part parameter and warning gone. |Passed |
| Valid selection |Exact nose route selected nose row; fin_set tree click changed selected row and actual URL to fin_set. |Passed |
| Restore |Canonical part-free RP1 Design, whole vehicle 26/26, Assembly 45°/54.7°/0°, Move on, Parts/both panels open, tools closed, Frame selection disabled. |Passed |

The exact warning reads: “Part link unavailable: the design, revision or part does not match this source. No historical part is substituted.” Both genuine warning screenshots were reviewed offline and show the warning/button below the header, rather than relying only on accessibility text. The resulting canonical URL is `/?workspace=design&design=G80-F2-RP1-AD1-definition-v2&spec=811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`.

Served App fingerprint is `a59c2cc9d05a6eb29d2a62ce5a740008d4446ac6ceb4cf966846a64ea3e36692`, verified before this packet and pinned in the [source freeze](../../../runs/frontend-part-link-recovery-20261108/source-freeze.json). P6 served the earlier `dad597467a57fe55a1ff86b9f7a3c409680e4c687feb1640f061bef0c4a8a183`; no later fix is retroactively attributed to its images. Primary owns publication and remote-check status. Specification/inspection geometry and engineering/physical gates did not change.

P7 used the same existing authorized Chrome window, with no resize. Its latest separately observed helper size was 2240×1109 CSS px, DPR 2 in P6; P7 did not remeasure CSS or claim a prescribed viewport. Fresh 4480×2460 native JPEGs include browser chrome. No performance Play, new simulation, other window/app, DevTools/CDP/console or source mutation occurred. No guard/access failure or automatic retry occurred. No separate Reload shortcut was needed because normal route navigation loaded the corrected source.

The final canonical fresh route shows Frame selection disabled. This is a P7 observation; the earlier P6 residual enabled control was not diagnosed or silently rewritten. Analysis-mode warning visibility, other malformed/foreign identity combinations, the exact-size matrix and representative performance remain outside this packet. The [session record](../../../runs/frontend-part-link-recovery-20261108/record.json) and validated inventory retain actual links, captures, source boundary and restoration. CUA is idle.
