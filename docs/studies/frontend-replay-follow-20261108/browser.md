# P11 Auto follow fallback at T125

**Auto B fallback visibly works on the new camera source.** The exact manual comparison survived HMR at absolute125, bounded and paused. The scene now clearly shows the recorded rocket body along the gold B trail, with the visible label “Camera follows B recorded position · Auto fallback; A: Outside recorded window · view only.” A remains unavailable in all four readouts; B's values remain unchanged.

The packet is **partial**: explicit A-only/B-only/Free modes were not established through native interaction. Actual duration was **152.599 seconds** against150, a **2.599-second overrun** during final read/capture; budget pass is false and no extension is claimed. No further CUA followed the final capture.

| Branch | Actual observation | Outcome |
| --- | --- | --- |
| HMR/manual setup |Exact A `exp-cf9e47a650074144856caf50775846d2`, B `exp-ab60bd4ac5c2412a9dd85f712072bca2`; absolute HUD125.000/core125.00/field125; bounded checkbox0/paused. |Passed |
| Auto fallback |Visible B rocket body +gold trail and visible B follow/fallback label. Aall four readouts unavailable; B nearest125.014 values unchanged. |Passed scoped new source usability |
| Explicit A-only |Actual dropdown offered Auto/A-only/B-only/pad/free. Down+Return left Auto unchanged. A fresh popup click then returned no AX change/no opened menu items. |Unexecuted; native control path unresolved |
| B-only/Free |No further menu/input method after the unresolved switch. |Unexecuted |
| End state |Same comparison125/Auto B/bounded paused, no Design reset or numeric entry. |State preserved; cap overrun retained |

This is independent new source camera evidence. P10's earlier no-identifiable-body images and P9's native input failure/cap overrun remain unchanged. The new B body is recognizable in both `auto-b.jpg` and `final-auto-b.jpg`. No numeric camera/pivot/pose-error measurement or physical recovery acceptance follows. A's unavailable window/status and no separate identified A body are not expanded into a global pixel absence proof. Historical trails are still source history.

The unsuccessful selector interaction is not classified as a source dropdown bug: the actual mode remained Auto, so the heldA/B-only/Free behavior was never exercised. Native focus/menu emulation versus source behavior remains unresolved. The first attempt's files were renamed `attempted-a-only-still-auto-b` before freeze so their actual Auto state cannot be mistaken for an A-only pass. No alternate coordinate/keyboard cascade or automatic runtime correction followed.

Served local Experiment fingerprint is `18dbf51fc34ee3ba0a3ffe047c0fa23a3bee5040b48df95eeab825947b61fb20`; helper `b89d0aa6c17749388efb0608cbe4ba8e2c2b778fa90702a191a36ca749e44888`; CSS b01/App a59 unchanged, as pinned in [source-freeze.json](../../../runs/frontend-replay-follow-20261108/source-freeze.json). PR108 base is merged at `47bc74a12b6d186bf8a9b68ef6e7ad45f044410a`; new candidate publication remains primary-owned. Source tests/preservation audits are separate from these actual native observations.

No Play/FPS, new load/reload, experiment, resize, numeric entry/setter, DevTools/CDP/console or other window/app interaction occurred. One normal upscroll exposed the scene; the original manual comparison/time stayed intact. Native JPEGs are unchanged; no current CSS size or exact viewport acceptance was inferred from raster. The [session record](../../../runs/frontend-replay-follow-20261108/record.json) preserves modes, values, timing failure, source boundary and actual owner review state. CUA is idle with Auto B at125.
