# G80 washer boundary: 48/24 area budget

The single proposed **48 outer / 24 inner quadratic segments per full circle** passes the independent annulus known case and its stricter predeclared noncancellation budget. It remains a proposed boundary discretization; no actual bridge mesh or solver was run in this increment.

For an exact circle of radius `r`, the area of the corresponding `n`-segment quadratic boundary is `n r² [(4/3) sin(π/n) − (1/6) sin(2π/n)]`. Before executing the fixture, the [plan](../build/wo03-g80-washer-area-budget-v1/plan.json) recorded the absolute deficit for each boundary and required their **sum**, rather than relying on cancellation, to remain at or below 0.00015 mm²:

| Circle | Radius | Segments | Absolute disk area deficit |
| --- | ---: | ---: | ---: |
| Outer | 4.5 mm | 48 | 0.0000388925763 mm² |
| Inner | 1.7 mm | 24 | 0.0000886737493 mm² |
| **Sum** | | | **0.000127566326 mm²** |

The sum leaves 0.000072433674 mm² to the existing 0.0002 mm² absolute patch-area guard, exceeding the required 0.00005 mm² headroom. This is a known-circle boundary approximation bound, not a bound on every additional 3D meshing or geometry effect.

One small 2D annulus used the unchanged source-pinned boundary helper, explicit Gmsh `Circle` curves, quadratic triangles and Gauss6 integration. The exact area was **54.538048466319 mm²** and the integrated area **54.538098247492 mm²**, for **+0.000049781173 mm²** signed error. The independent quadratic-arc calculation and integration agreed to 2.85e-14 mm². The centroid was within 6.5e-17 mm of the exact center; the minimum sampled surface Jacobian was positive at 0.131992. The actual boundary counts were 48/24, with 1,048 nodes and 488 triangles. These small 2D counts do not predict the 3D bridge count or prove its node/area guards will pass. The config copies the same original bridge and washer STEP hashes; the helper itself was unchanged (SHA-256 `df163d8e70655abbbb9d1a7d2ad8253195d5e92b5efc7f85dd5d4fe79251b071`).

The [fixture result](../build/wo03-g80-washer-area-budget-v1/result.json), [case script](../build/wo03-g80-washer-area-budget-v1/case.py), [runner](../build/wo03-g80-washer-area-budget-v1/run.py), and [study config](../configs/studies/wo03-g80-washer-boundary-area-budget.yaml) preserve the calculation. The one requested-worker case had a 10 CPU s and 10 s wall cap, used **0.151152 CPU s** and **0.269819 s process wall**, and recorded **59,195,392 bytes** peak RSS. The packet's setup and case were limited to 20 CPU s. The prior structural accounting is approximately **273.304 CPU s**; a separate **20 CPU s** preparation allowance and a possible **90 CPU s** later case reservation would place the conservative total below 600 CPU s. These allowances are not claimed as measured usage.

Any actual bridge trial requires a separate decision. The prior 96/32 source configuration and node-cap failure remain intact. This 48/24 proposal is the final planned boundary-resolution variation for a future full 3D attempt in this increment: if that separately authorized attempt still fails a guard, stop the full 3D route and evaluate a different bounded representation rather than tuning more Gmsh settings. Existing node, element, memory, area, balance and acceptance criteria remain unchanged.
