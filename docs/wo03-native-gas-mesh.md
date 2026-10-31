# WO-03 native BRep gas analysis mesh

This isolated pilot remeshes the exact fitting69df fluid STEP for analysis.
The frozen 80,186-node optical-PLC gas mesh and all raw radiation results remain
unchanged. New native triangles require **new wall quadrature and power-conjugate
cross-mesh registration**; optical M/B/D arrays must never be copied to them.
No thermal calculation, optical rays or adoption is part of this pilot.

The source is the frozen actual STEP SHA256
`1400eb53b79afdb41784aa06c5e0b45f8dc717027041fa6fc4f96d42d3b7fec0`.
Its proven native→1,785-original-face bijection is reused and reverified by
actual interior samples/trim classification and area after import. Original
material/reservoir face IDs and radiation-group IDs remain per boundary facet.
No Boolean, topology simplification, CAD healing, small-face/edge removal or
merging is performed. Shared boundary nodes remain shared; h/temperature
ownership is separate.

Gmsh4.15.2 settings are explicit: 4 mm bulk, 80 minimum circle points and
curvature points, 0.005 mm minimum size, minimum three curve points, all original
corner nodes and edge line elements required. This retains 20 µm edge endpoints;
it does not prove the approximation resolves every 20 µm barrier. At R32.5 mm,
an ideal uniform80-gon has25.1 µm sagitta, but actual surface triangles need not
follow that ideal. No global25 µm distance bound is claimed.

Every face reports area error, sampled projection distance, outside-trim counts,
normal alignment and signed penetration into the opaque side. For known20 µm
foil normal directions, a sampled penetration through the whole layer rejects
the approximation. All unique surface edges are checked against nonadjacent
facets before volume fill. That numerical test does not certify every coplanar
overlap or curved-CAD deviation. CAD-corner equality, complete face/curve coverage,
positive tet4 cells, tet exterior incidence, unchanged material-face labels and
volume are checked separately.

The old numerical guards remain: face area2%, group area0.5%, tet/faceted-volume
closure1e−6 and exact-CAD-volume error0.5%; node/tet caps150,000/750,000, one CPU,
hard300 s. Standard Gmsh volume quality optimization is enabled before validation;
surface nodes stay classified on the original BRep and corners must stay fixed.
No zero cell is dropped. Resource/time caps mean **incomplete**, not a numerical
temperature failure. A valid mesh, completed thermal calculation, numerical
accuracy and temperature acceptance remain four distinct gates.

Known split-wall/cavity/20 µm barrier fixtures pass at
`build/wo03-native-gas-fixtures-v3` under the unchanged old guards in9.15 s.
The first fixture run exposed float32 VTK intersection-output coordinates making
shared endpoints look like crossings; output was changed to float64, without
changing any geometry. These earlier failed checks remain recorded.

The one authorized actual pilot is
`build/wo03-native-gas-actual-coarse-v1`. No further actual attempt or budget raise
is authorized here. All face diagnostics are saved in `surface-audit.json` before
3D meshing, so an incomplete/invalid pilot is still reviewable. Full uniform
distance, barrier and solution-convergence certification is not inferred from
face IDs or positive volume alone.

The pilot stops after2D meshing in38.04 s with **300,980 surface nodes and
602,816 triangles**, exceeding the unchanged150,000-node cap before3D fill.
That is3.754 times the entire80,186-node frozen PLC mesh (4.185 times its
boundary population). No tet count, positive volume or factorization is
available. Source inputs remain unchanged during execution.

The saved audit independently demonstrates inadequate geometry approximation:
14 faces exceed the old2% area guard (maximum6.27366%);11 groups exceed the
old0.5% guard (maximum5.41855%). Twelve of109 sampled known20µm-normal faces
have penetration through the full layer, maximum24.4836µm on face1331,
`additional_shield_3_1`. Maximum sampled underlying-surface distance is35.218µm;
6,052 projections are outside trimmed faces. Those counts are diagnostics,
not certified trimmed-face distance bounds. All3,140 corners are retained
(maximum coordinate error1.26e−17mm), and all5,174 source curves have line
elements. Corner/face presence alone does not rescue the foil approximation.

| Gate | Actual pilot status |
| --- | --- |
| Valid volume mesh | Unestablished;3D not attempted after node cap |
| Complete calculation | Incomplete resource limit; no thermal calculation |
| Numerical accuracy | Observed surface-area/foil-penetration requirements violated; no global convergence claim |
| Temperature acceptance | Not computed |

Selfintersection and volume checks remain uncomputed because the node cap
stopped the sequence first. They are not silently passed. The report SHA256 is
`b3369d540ff1328a4bb43f504e80e3216afc2bc31642b7b345c88bc26c504c26`;
the complete1,785-face audit SHA256 is
`fda96e1a2c2b401356bbdd9413e30a9e8d59859baffdf0d63121ea98c0d64b8f`.
The short `compact-summary.json` links both without repeating every face row.

Future settings proposed, not executed: bulk3/2 mm with circle/curvature120/160.
Ideal R32.5 mm circle sagittae would be11.1/6.3 µm, but actual errors and cost
must be measured. They are not promises that either refinement fits the same
caps. No global numerical-accuracy claim is possible from this one coarse run.
In fact this isotropic curvature-sizing strategy is already over budget at80;
120/160 are accuracy targets requiring a primary method/resource decision,
not recommendations to launch automatically. Merely tightening them is
expected to increase cost and cannot make this pilot computationally suitable.

```sh
.venv/bin/python scripts/wo03_native_gas_mesh.py --stage fixtures \
  --output build/wo03-native-gas-fixtures-v3
.venv/bin/python scripts/wo03_native_gas_mesh.py --stage actual \
  --fixture-cache build/wo03-native-gas-fixtures-v3 \
  --output build/wo03-native-gas-actual-coarse-v1
```

Use fresh directories for an authorized replay. The source, config, settings,
logs and four gate statuses are recorded. Field/quadrature recomputation,
conduction assembly/factorization and thermal acceptance remain with the primary.
