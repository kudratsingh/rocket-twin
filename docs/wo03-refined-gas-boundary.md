# WO-03 targeted linear gas-boundary subdivision

The one authorized pilot is **incomplete at the boundary count cap**. Its saved
partial boundary is a valid conforming partition of the frozen optical PLC, but
it does not meet the requested axial/planar resolution. No Gmsh volume mesh,
factorization, heat equation, new optical rays or thermal acceptance was attempted.
There was no second attempt or automatic relaxation of the rules or caps.

The evidence is in
`build/wo03-refined-gas-boundary-pilot-v1/{report.json,result.json,derived-boundary.npz}`.
The parent report records 8.551 s elapsed and unchanged pinned inputs. The result
records the source hashes, exact selected face IDs, every batch and all partition
checks. `freeze-summary.json` records final publication-file hashes separately
from the immutable as-run hashes in `report.json`.

The source is the fitting candidate `69df790ec9bcba1465be4fa9861a7ad5fbc467091cbf58f44dee069e56e00bac`,
with the actual interior fluid STEP, 1,785 physical faces and the frozen fine
optical PLC: 71,917 vertices / 144,690 triangles. Its STEP SHA256 is
`1400eb53b79afdb41784aa06c5e0b45f8dc717027041fa6fc4f96d42d3b7fec0`;
its fine-boundary SHA256 is
`fc435123d45a21aefacea906b259d1a5298895092374ba12bc489c868c1c948e`.
The old interior radius, all solid barriers, slots, seams, openings and reservoir
labels are inherited without CAD regeneration or projection. This preserves the
old piecewise-linear geometry; it does not establish exact-BRep approximation
accuracy beyond the frozen source evidence.

| Requested rule | Actual physical selection | Initial maximum | Saved maximum | Target |
| --- | --- | ---: | ---: | ---: |
| Case and inner liner axial edge span | Original faces 902 / 942, cylinder families | 187 mm | 70.125 mm | 12 mm |
| Case end bands, radius below 16 mm | Fore/aft stations 1013 / 1200 mm, ±0.4 mm; case, liner, original foil, thrust and retention parts | 187 mm | 70.125 mm | 0.1 mm |
| Fore pad/retention corner axial span | Thrust-pad/retention parts, z=1010–1013 mm, radius below 16 mm | 9 mm | 2.25 mm | 0.1 mm |
| Planar in-plane edge length | Fore-retention plane 858 and case caps 901 / 903 | 24.6202 mm | 9.14568 mm | 1 mm |

Selection uses `part_id` and `physical_surface_family`. Radiation group IDs only
resolve that family; they are not treated as physical face IDs. The liner inner
cylinder is the positive radial void-normal family of radius 14.7 mm; the case
radius is 14.5 mm. Closed edge/interval intersection grades edges entering an end
band, including an endpoint on the band. The fore retention plane is the closest
horizontal retention plane below the actual case fore station, at 1010 mm.

| State | Nodes | Triangles | Violating edges |
| --- | ---: | ---: | ---: |
| Original | 71,917 | 144,690 | 4,010 |
| Saved partial partition after five batches | 101,741 | 204,338 | 47,681 |
| Next conforming independent batch, predicted only | 120,069 | 240,994 | — |
| Authorized cap | 120,000 | 240,000 | — |

The next batch was rejected before applying it. The saved partition has added
29,824 nodes and 59,648 triangles. A split is shared by both incident triangles;
the deterministic highest-ratio independent batch marks at most one edge per
triangle. General red/green templates also support two or three marked edges.
Each midpoint is the linear average of existing endpoint coordinates, and every
child retains its original optical parent and affine barycentric map.

This method consumes nodes quickly because the source has long, narrow triangles
across the 187 mm case/liner span. An edge touching a small end band must be
bisected recursively, and subdivision creates additional in-parent connecting
edges that can themselves enter the band and remain long. Conformity also splits
the neighboring triangle on every marked edge. The actual violating-edge count
rose from 4,010 to 47,681 while the largest axial span fell from 187 to 70.125 mm.
This is evidence that this particular midpoint strategy exhausted its authorized
budget before completing the anisotropic target; it is not a lower bound on the
node count of every geometry-preserving discretization.

The saved partition passes these checks:

- All 71,917 original vertices retain their bits and all 1,785 face IDs remain.
- Every child is oriented like, coplanar with and barycentrically inside its
  original optical triangle. Maximum affine reconstruction roundoff is
  7.106e-15 mm and maximum normal-plane roundoff is 3.447e-15 mm.
- Maximum relative per-original-parent area discrepancy is 8.715e-14. Parent area
  conservation also preserves each inherited material/group area to roundoff.
- Every boundary edge has incidence two; no holes or extra boundary faces were
  created. The inherited parent orientation is retained.
- Oriented volume is 475596.00645407476 mm³ before and
  475596.00645407353 mm³ after, a relative difference of about 2.6e-15.

These checks establish the validity of the derived linear partition. They do not
establish a completed volume mesh, internal-cell embedding, FE conditioning,
spatial convergence or thermal acceptance. The four gates remain: valid partial
boundary partition **passed**; requested discretization/calculation **incomplete**;
numerical solution accuracy **not established**; temperature acceptance
**uncomputed**. The source-independent tests exercise all seven nonempty split
templates, a shared-edge pair, a closed 20 µm barrier, endpoint/radius interval
selection and deliberately different physical-face/group IDs.

The NPZ interface is `vertices_mm`, `triangles`, `triangle_face_index` (zero-based
original physical face index), `original_optical_parent_triangle_ids` (zero-based
original optical row), and `child_vertex_parent_barycentric` of shape
`(child, child-local vertex, original-parent-local vertex)`. New wall quadrature
is required; old optical M/B/D cannot be copied. For a child vertex matrix Λ,
linear registration obeys `T_child = Λ T_parent` and the power-conjugate transfer
is `q_parent = Λ.T q_child`. This is an interface statement, not an executed
coupling calculation.

A possible subsequent method, requiring a separate primary decision, is
constrained anisotropic remeshing **inside each original planar optical triangle**:
insert axial intersections directly, share identical subdivisions on every
original edge, retain all original vertices and all material/face constraints,
and triangulate the resulting strips without crossing an original parent edge.
It would need the same child-in-parent/orientation/area/closed-volume proof and
original-parent barycentric registration. It must preserve tiny rims, every
barrier and all reservoir/face labels without projecting points, moving curves,
merging faces or copying optical quadrature. No such method was implemented or
run in this pilot.

For isolated publication, the new analysis module uses only NumPy and typing.
The runner imports frozen `src.analysis.cad_gas_mesh` helpers `load_source`,
`sha`, `interior_seeds`, `tetrahedralize`, and `verify_volume_mesh`, so importing
the runner (including its fixture test) also requires that module, PyYAML and
the already pinned CadQuery 2.8.0 / OCP 7.9.3.1.1 and Gmsh 4.15.2 imports. The
unattempted volume seed path additionally uses VTK 9.6.2. No dependency was
installed or upgraded. The tests require pytest;
no ignored build data is needed for their source-independent fixtures.

Validation at freeze: the three focused tests passed; Ruff, Black and strict
mypy passed for the new source and runner. After the actual pilot, the only
analysis-code edit explicitly wrapped the already-boolean interval mask in
`np.asarray(..., dtype=np.bool_)` for strict typing; no rule, coordinate, cap or
numerical algorithm was changed, and no actual pilot was repeated. The as-run
source hashes remain recorded unchanged.
