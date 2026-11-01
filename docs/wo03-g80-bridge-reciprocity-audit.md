# WO-03 G80 bridge reciprocal-work audit

**Result:** the preserved 48/24 bridge deck and DAT do not satisfy the two-load Maxwell–Betti reciprocal-work identity within the conservative decimal-printing bounds. This is a read-only diagnostic of the existing stopped 1.5 mm case. It does not change or replace its earlier 104.697 N force-equilibrium failure, explain the cause, establish a CalculiX defect, or provide a strength result.

The complete calculation is reproducible with [proof.py](../build/wo03-g80-bridge-reciprocity-audit-v1/proof.py); the original [record.json](../build/wo03-g80-bridge-reciprocity-audit-v1/record.json) stores its inputs/hashes, exact serialized CLOAD entries, every as-run DAT displacement string for both steps, all support RF output strings, completeness checks and work bounds. The compact hash-checked projection is [here](../runs/wo03-g80-reciprocity-20261101-v1/record.json), with its [projection script](../runs/wo03-g80-reciprocity-20261101-v1/proof.py). No mesh or solver was run for this audit.

## As-run deck conditions

The inputs are the preserved `build/wo03-g80-bridge-area-budget-coarse-v1/bridge_1p5mm/case.inp` and `case.dat`, with the sibling `mesh-meta.json` and stopped campaign record. The washer-boundary config specifies 48 outer and 24 inner full-circle-equivalent segments. The deck uses 42,850 nodes, 22,495 C3D10 tetrahedra and 1,574 support nodes.

The serialized deck has two `*STATIC` steps and exactly one `*CLOAD,OP=NEW` block per step. One `*BOUNDARY` block precedes step 1 and fixes DOFs 1–3 on `SUPPORT`; no step-specific boundary changes appear. There is no `*NLGEOM`, contact, DLOAD/DSLOAD, or nonlinear material keyword. All seven material regions have one `*ELASTIC` definition: G11 uses E=10,000 and ν=0.3; each of six epoxy regions uses E=100 and ν=0.3. Under the deck's N/mm convention these moduli are N/mm²; printed U is in mm and reciprocal work is N·mm. The deck therefore supplies the same homogeneous supports and linear-elastic material law for both responses.

Every serialized load row is included in the record. Step 1 serializes 3,184 DOF-3 nodal loads, corresponding to 50 N on each of the three washer patches. Step 2 serializes 1,072 DOF-3 loads, 150 N on patch 0 and none on patches 1 and 2; `OP=NEW` replaces the first load pattern. The summed resultants from the actual deck coordinates are:

| Step | Patch force resultants | Total force (N) | Total moment about origin (N·mm) |
|---|---|---:|---|
| 1 | 50, 50, 50 N | (0, 0, 150) | approximately (0, 0, 0) |
| 2 | 150, 0, 0 N | (0, 0, 150) | (3312.547169, −1912.500000, 0) |

Deck nodal coordinates match `mesh-meta.json` within the deck's own printed coordinate precision. The serialized nodal loads match the saved per-node pressure weights within the force token's last-place rounding. Both `ALL` displacement sets contain exactly 42,850 unique rows; both `SUPPORT` force sets contain exactly the 1,574 support-node rows. There is one output table for each set and step.

## Reciprocity calculation

The audit evaluates the requested dot products directly from the deck's exact decimal CLOAD tokens and the as-printed DAT displacements:

| Work | Calculation | Result |
|---|---|---:|
| W12 | Fstep1 · Ustep2 | 34.2550925181 N·mm |
| W21 | Fstep2 · Ustep1 | 2.0260281334 N·mm |
| Absolute difference | |W12 − W21| | 32.2290643847 N·mm |
| Relative difference | difference / mean(|W12|, |W21|) | 177.663% |
| Conservative combined print bound | W12 and W21 token-rounding bounds summed | 0.00000325270 N·mm |

Each CLOAD and U token was treated as a decimal rounded by at most half of its last printed place. For every product, the bound includes `|F|·δU + |U|·δF + δF·δU`, summed over every serialized load term. The observed difference is far outside that bound; no additional engineering tolerance was introduced. The input CLOAD tokens are the exact numerical loads in the deck; their half-last-place intervals are reported only as a conservative serialization uncertainty.

This diagnostic assumes the step-2 DAT field is the absolute solution for the step-2 `OP=NEW` load pattern, as the independent two-case reciprocity check requires. The deck contains no extra history-dependent constitutive or geometric terms that would invalidate linear reciprocity. The difference is too large to be explained by field printing. It narrows the issue to inconsistency in the actual response/deck/output pairing or a violated model/solution assumption, but this audit does not identify which. It is not evidence of a CalculiX bug.

## Existing stop and limits

The preserved stopped campaign record remains `actual_acceptance: false`. Its independent equilibrium diagnostic for the 150 N step reports support reaction `(2.66e−7, 1.83e−7, −45.3032) N`, a `104.6968 N` axial residual, and a reaction-print rounding bound of about `1.13e−5 N`. That failure is copied into the new audit record for context and was not edited. A reciprocity discrepancy does not erase or explain the force-balance result.

Source hashes for the deck, DAT, mesh metadata, stopped campaign record, known-area result, executed configs/adapter and installed CalculiX binary are identical before and after the read-only audit. The exact input identities and output arrays are in the machine-readable record. The audit does not pass the actual bridge, validate reactions, establish load transfer, assess material strength, or authorize another solve.
