# After-correction drawing work comparison — 2026-11-08

Result: **passed**. This is one read-only Node/data-preparation comparison, not a browser or third native60fps attempt. The original two browser failures and60fps criterion remain unchanged.

Same saved G54 run `exp-ab60bd4ac5c2412a9dd85f712072bca2`; native rows 132856. The frozen baseline remains unchanged in `web/tests/replay-drawing-work.test.mjs`.

| Work | Frozen native drawing baseline | Bounded native-index drawing |
| --- | --- | --- |
| Trajectory line instances | 132855 | 1005 |
| Potential instanced triangles | 797130 | 6030 |
| Trajectory preparation ms | 24.633500000000026 (geometry only) | 41.609916999999996 (index selection + geometry) |
| Four SVG native points | 531424 | 4208 |
| Four SVG point-string characters | 17343474 | 143954 |
| Four SVG preparation ms | 215.59612500000003 | 41.74649999999997 |

Native trajectory cap3000 retained positions; each plot cap1200. All values remain native samples. Per-range extrema, endpoints, drawable recorded-event neighbours and explicit missing-value segmentation are independently checked in the JSON evidence. Timestamp spacing alone never creates a gap. The actual dataset's explicit missingness is reported; synthetic gap tests remain separate evidence. Raw telemetry remains the pose/interpolation/readout/metric/export source.

Owner record and Parquet hashes unchanged: True. In-memory raw column hash unchanged: True. All frozen helper/test source hashes unchanged: True. Bulk arrays were not stored in these artifacts; the temporary fixture was deleted.

Additional CPU 1.686s / wall 2.016s against6CPU/15wall. Aggregate with frozen baseline: 2.970CPU / 3.533wall against10CPU/30wall. No retry occurred.



These are one-off preparation/geometry-size measurements, not browser layout/paint, GPU duration, memory/FPS measurements or proof of rendering dominance. Cold-function/JIT and the different included preparation phases prevent interpreting the times as a browser speedup ratio. No browser acceptance or60fps pass is established. See [work-comparison.json](work-comparison.json) for exact phases, checks and hashes.
