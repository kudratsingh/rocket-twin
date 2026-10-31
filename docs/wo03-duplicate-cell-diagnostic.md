# Exact duplicate-cell diagnostic

Read-only result: **coalescing exact copies is insufficient**. The derived
proposal is not an accepted mesh, official cleanup or adoption. No Gmsh, PDE or
factorization call occurs. Original postraw files are hash-pinned and unchanged.

`scripts/wo03_duplicate_cell_diagnostic.py` defines equivalence only by the same
four original node IDs. It retains the lowest existing element tag, then row,
without canonicalizing the stored orientation. A known duplicate/simple-tet
fixture passes the unchanged validator after the exact quotient; distinct cells
remain untouched. No coordinates, boundary arrays, distinct cells or zero cells
are removed/perturbed.

Actual502251→502249 cells removes two duplicate occurrences. Element tags
1020572 and965166 are retained in the two classes. Geometric cell-set union
is unchanged by definition; this does not prove that union equals the CAD fluid
or that its declared material boundary is valid. The unchanged old whole
validator still rejects nonmanifold incidence. Two faces have three distinct
incident cells, at original node tags[7388,9928,91171] and[7388,25205,91171].

Derived exterior144696 differs from original fixed144690 (eight new/two missing
unique facets). Unchanged Gmsh boundary144692 has four new/two missing fixed
facets and one face/group area error21.742%, exceeding old2%/0.5% guards.
Two scaled determinants remain below1e−14 (minimum1.902e−17); zero count is0.
Signed tet-volume error against the source PLC is−1.25165e−4, failing1e−6.
No criteria are changed. `removeDuplicateElements` alone cannot resolve this
middle mesh.

Final report: `build/wo03-duplicate-cell-diagnostic-final/diagnostic.json`,
SHA256`b559cb45d6752db1ca965a20a329313858501fc413c39b372e7eba70ed651eb2`.
The diagnostic proposal SHA256 is
`e58ae202c0d8afe5d6939453594d47588c3173286f1e9f1b401a8af22e116b87`.
Runtime7.10s, peakRSS1.109GB, source inputs unchanged; 120s and existing
750k-tet/150k-node bounds retained. Black/Ruff/strict mypy pass.
