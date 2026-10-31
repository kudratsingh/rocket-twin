# Existing coarse cell-adjacency validity audit

Read-only result: every shared facet in the immutable coarse mesh passes the
local geometric opposite-side test. This is **not** global embedding,
nonadjacent-cell intersection, PDE accuracy or temperature validation.

Input `build/wo03-cad-gas-actual-v1/coarse/mesh.npz` remains SHA256
`aefc71e318393ae781fefb5e5d2195eb6383dc32214f292eb4445f1de86b4351`.
All427,940 tet elements are strictly positively oriented. All783,535 internal
facets with incidence2 have their two opposite vertices strictly on opposite
geometric sides. Same-side faces=0, zero-side faces=0. The incidence histogram
is144,690 exterior facets and783,535 internal facets.

`scripts/wo03_coarse_cell_adjacency.py` sorts facet triples only to establish
the common basis and retains each incident cell's opposite vertex. It uses a
conservative64-epsilon orient3d arithmetic filter; uncertain signs alone are
evaluated as exact binary-rational determinants of the original float64
coordinates. The actual source requires0 exact escalations. Fixtures include a
valid pair, a deliberately folded pair whose elements are both positive, and
an exactly zero determinant that exercises the rational branch. No sign is
made acceptable by a geometric tolerance.

The full audit completes in1.566s with454MB peakRSS, inside oneCPU/120s and
existing750k-tet/150k-node limits. No Gmsh, node/cell repair, PDE or factorization
occurs. Original coordinates/connectivity remain unchanged. All zero/same-side
face coordinates/scales would be retained in the diagnostic NPZ; it is empty
for this source. Exact predicate details are retained only for nearzero cases.

Report `build/wo03-coarse-cell-adjacency-v1/diagnostic.json`, SHA256
`be73b8b84e80679a7c5e9109266df309e5320d65bf4722f76bc1e98c60876f5c`.
Bad-face archive SHA256
`5f9d594e92768dc95edf7084517de5f919b78b04ea0ac0b8a60de22c966a306c`.
Black, Ruff and strict mypy pass. The result excludes same-shared-face local
folding as an observed mechanism here; it does not explain or waive DMP
violations, poor conditioning, nonacute FEM effects or possible distant-cell
intersections. The duplicate-quotient middle remains rejected separately.
