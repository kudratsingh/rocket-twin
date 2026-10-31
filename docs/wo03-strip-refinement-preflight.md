# WO-03 planar-parent strip count preflight

The unchanged targets cannot fit the **120,000-node / 240,000-triangle boundary
caps** while preserving the old optical vertices and parent edges. A relaxed
necessary count already requires 123,510 boundary nodes / 247,876 triangles;
even the original-edge requirement alone exceeds both caps. Direct strips can
avoid recursive midpoint spokes, but cannot remove the need to subdivide the
preserved long original edges.

This is a read-only count study. No candidate boundary/volume mesh, Gmsh call,
field solve, optical rays, geometry change or adoption was produced. The primary
retains the meshing decision. A larger budget is not authorized by these counts.

The canonical final record is
`build/wo03-strip-refinement-preflight-v1/final/{report.json,counts.json}`.
It completed in 7.321 s wall / 3.742 s worker on one CPU with a 60 s watchdog;
pinned inputs were unchanged. Earlier count-only and lower-bound development
records remain in the parent output directory. The final record supersedes them
and includes the explicit conservative roundoff padding. All four read-only
count executions together used 26.331 s wall; none was a mesh attempt.

| Count | Boundary nodes | Boundary triangles |
| --- | ---: | ---: |
| Frozen optical source | 71,917 | 144,690 |
| Necessary original-edge subdivision alone | at least 122,166 | at least 245,188 |
| Necessary edge subdivision plus cap-area requirement | at least 123,510 | at least 247,876 |
| Explicit conservative strip / 0.5 mm cap-grid construction | 164,240 | 329,336 |
| Existing authorized boundary caps | 120,000 | 240,000 |

The original closed triangulation permits at most 47,655 additional vertices
under both boundary caps: Euler's invariant gives two additional triangles for
each added surface vertex when the old vertices and topology are retained. The
necessary edge count is already 50,249 new nodes, before any cap-interior nodes.
The combined necessary bound is 51,593 new nodes, exceeding the available count
by 3,938. These are count constraints, not failed FE geometry or temperatures.

The source is the actual fitting candidate
`69df790ec9bcba1465be4fa9861a7ad5fbc467091cbf58f44dee069e56e00bac`,
with 1,785 physical faces and 217,035 unique original edges. The frozen boundary
SHA256 is `fc435123d45a21aefacea906b259d1a5298895092374ba12bc489c868c1c948e`.
The exact physical masks are reused from frozen `refined_gas_boundary.targets`:
case/inner-liner cylinders 902 / 942 have the 12 mm axial limit; selected parts
near the motor fore/aft stations 1013 / 1200 mm have the 0.1 mm end-band rule;
fore thrust-pad/retention parts use z=1010–1013 mm and radius below 16 mm; planar
fore-retention/case-cap faces 858 / 901 / 903 have the 1 mm in-plane edge limit.
Group IDs resolve physical families and are never substituted for face IDs.

For the necessary original-edge bound, integrate resolution work along each
preserved edge: `|dz|/0.1` inside the union of required local intervals, plus
`|dz|/12` elsewhere for case/inner-liner edges. An admissible child segment has
work at most one, so an edge requires at least `ceil(work)` segments. The cap
edge-length requirement adds its own necessary segment count. Only edges with
both radial endpoints strictly below 16 mm are credited for the local bound;
convexity of the radius ensures their whole chord is inside. The bound omits
2,272 other radial-crossing edges rather than overstate their cost. Non-global
regions outside local intervals add no work to this lower bound. Closed-endpoint
grading, minimum angle and tetrahedral quality are also omitted.

For cap area, a triangle whose three edges are at most 1 mm has area at most
`sqrt(3)/4 = 0.433012702 mm²`. The selected cap area is 3,608.443493 mm².
Summing each preserved cap parent's area requirement gives at least 9,408 cap
triangles. After the minimum original-edge points, the remaining cap-triangle
deficit requires at least 1,344 additional surface nodes: a new node increases
the cap triangle count by at most two, whether inside one parent or on a shared
edge. This area argument is not needed for the decisive edge-only cap result.
The necessary-count calculation alone relaxes limits by 1e-10 relative and pads
cap integer rounding downward, conservatively beyond the frozen 1e-12 comparison
allowance. Actual geometry guards, targets and resource caps are unchanged.

The explicit construction count uses rational z planes spaced by 12 mm from the
actual fore station; local 0.1 mm planes include one extra interval outside each
closed end band or fore corner. It cuts the entire selected original parent,
including any radius-above-16 portion, so this is a conservative construction
count. Each selected horizontal cap parent is cut by x/y lines on a 0.5 mm grid;
any edge inside one cell has length at most sqrt(0.5) mm, below 1 mm. It preserves
all original angular facets rather than claiming a new angular discretization.

| Explicit arrangement quantity | Count |
| --- | ---: |
| Unique original-edge / plane intersections | 77,965 |
| Proper interior cap-grid crossings | 14,358 |
| Parent strip line segments | 49,320 |
| Parent cap line segments | 27,781 |
| Modified original parents | 5,268 |
| Polygon cells on those parents | 96,727 |
| Transition-only neighboring parents | 6 |
| Added transition triangles on those neighbors | 30 |

Intersections are deduplicated by the original undirected edge and exact rational
parameter, using the original binary64 endpoints and rational plane stations.
Both incident parents receive the same edge point. Cap-grid points on an
original edge are charged there, rather than as parent-interior nodes. Proper
cap-grid crossings are counted with a floating orientation filter and exact
rational fallback at ambiguous edges. For a parent with B inserted boundary
points and I interior points, a conforming planar triangulation has
`T = 1+B+2I` children. Parallel strips have `F=1+nz` polygon cells; orthogonal cap
lines have `F=1+nx+ny+I`. These formulas count the arrangement without constructing
child coordinates, connectivity or a candidate mesh. Counts by original face and
part are retained in `counts.json`.

The conservative arrangement is not an optimal count or an upper bound once FE
quality requirements are added. A future implementation would still have to
demonstrate nondegenerate constrained triangulation, shared-edge conformity,
child containment/orientation, unchanged parent areas/closed volume and all
source geometry guards. Angular and transition quality can add nodes beyond
these counts. No surface quadrature can be copied from old optical facets;
original-parent barycentric registration and new quadrature would be required.

The future 150,000-node / 750,000-tetrahedron envelope is **unresolved**. At the
necessary boundary lower count, adding the old 8,269 interior lattice nodes would
give 131,779 nodes, leaving only 18,221 for uncounted costs. Applying old coarse
density ratios gives optimistic analogies of 703,284 or 733,127 tetrahedra. These
are not bounds or predictions of a valid fill. The explicit conservative surface
arrangement already has 164,240 boundary nodes before any volume points; its old
density analogies exceed 920,000 tetrahedra. Actual narrow-gap quality, Steiner
points, positive/scaled volumes, embedding, conditioning, factor resources and
numerical convergence remain unknown. The count study supports no heat result.

The script has source-independent shared-edge, strict grid-boundary and 20 µm
parallel-sheet count fixtures, and passed Ruff, Black and strict mypy. It imports
the frozen `cad_gas_mesh.load_source` and `refined_gas_boundary.{edge_table,targets}`
helpers; the existing NumPy/PyYAML/CadQuery/Gmsh environment is required. It calls
no Gmsh API. No dependency or prior frozen file was changed.
