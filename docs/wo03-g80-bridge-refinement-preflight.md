# G80 bridge refinement preflight

**Three eligible refinement levels are not saved.** The only retained actual
bridge mesh that passed the complete independent input checks is the 1.5 mm
bulk, 48/24 washer-boundary case used for the current Elmer coarse diagnostic.
The [inventory](../build/wo03-g80-bridge-refinement-preflight-v1/record.json)
records metadata, deck, record and physical-source hashes. No mesh generator or
solver was run in this inventory.

| Saved actual attempt | Nominal bulk size | Mesh and input disposition |
| --- | --- | --- |
| 48/24 area-budget coarse | 1.5 mm | 42,850 declared nodes; 42,715 used (128,145 displacement DOFs); 22,495 C3D10 tets; 1,574 support nodes. Independent load, ownership, positive-Jacobian and mesh-to-CAD volume checks passed. |
| Earlier mapping replan | 1.5 mm | 31,435 declared nodes; 31,222 used (93,666 DOFs); 15,819 tets; 1,574 support nodes. Washer mesh area exceeded the unchanged 0.0002 mm² criterion, so this deck is not an eligible comparison level. |
| 96/32 boundary coarse | 1.5 mm | Stopped before input completion at 63,788 nodes and 34,591 tets, exceeding the 50,000-node guard. |
| Earlier coarse traction | 1.5 mm | Stopped before input completion on an applied-moment guard; its EQUAL y-moment was −0.00691142 N·mm. |

The two saved mesh metadata files identify the same pinned bridge STEP, six
film recipe/source identities and washer sources, and the same CAD volumes:
G11 `5500.998158 mm³`, each epoxy film about `9.939777 mm³`. These matching
identities alone do not turn the failed earlier mapping case into a valid
refinement. The accepted-input mesh's three washer areas are approximately
`54.53809825 mm²`, versus `54.53804847 mm²` source area; each difference is
`0.00004978 mm²`. Its mesh-to-CAD volume difference is about `4.55e-6`
relative for G11 and at most about `3.11e-11` for the epoxy films, within the
existing 1% check. Its SINGLE load is 150 N with moment
`[3312.5471695, −1912.5, 0] N·mm`; the preserved Elmer conversion checked the
serialized nodal forces and moments without replacing the affine pressure by a
uniform traction. EQUAL is 150 N with nominally zero moment. These are applied
loads, not evidence of installed joint strength.

The earlier mapping mesh has the same nominal size rather than a declared
finer size. Its washer area is `0.00052251 mm²` above source on each patch;
the later full-input check was never passed despite the adapter's intermediate
metadata status. The 96/32 attempt and earlier traction attempt likewise did
not produce eligible completed input. The original CCX coarse reaction failure
and the Elmer SINGLE supervisor failure remain recorded; the latter's field was
recovered separately for numerical evidence, not retroactive resource
compliance. No conclusion about stress convergence follows.

A next source-preserving preflight would need **two genuinely refined meshes**
for this same physical geometry, six material films, constrained rail-back
faces and declared affine washer-resultant loading. Each must independently
meet the existing volume, washer-area, connectivity, positive-Jacobian,
node/tet, load-force and moment, mapping and source-pin gates before any
comparison. Explicit mesh controls and resource feasibility need a primary
engineering decision; this inventory authorizes no generation. The existing
coarse case alone cannot establish memory or time scaling. Its roughly 1.06 GB
sampled root RSS and about 15 CPU seconds indicate a possible risk against the
unchanged 2 GiB root RSS and 120 CPU-second per-case limits, not a prediction
that finer levels will fit or fail.

If separately authorized, the proposed SINGLE-only three-level packet would
reserve 3 × 120 native CPU seconds, 120 parent CPU seconds and 60 setup CPU
seconds, totaling 540 under 600. Existing displacement and regional stress
convergence requirements remain unchanged; output mapping and solver evidence
must be established for every level. It is not authorized by this preflight.
