# Recorded engineering fields — rocket-twin.analysis.v1

The offline/backend export boundary is `src/analysis/records.py`. The Analysis
viewer contract is in UI.md; acceptance spans WO-03 -> WO-04 -> WO-05. The first
implementation supports scalar samples with JSON assets; large solver fields may
add a versioned binary transport later without changing provenance semantics.

A manifest identifies the configuration, exact resolved-spec SHA-256, CAD/generator
revision SHA-256, and shape hash per part. Cases record loads/boundaries and sources.
Each scalar field names quantity/component/criterion, SI units, association,
coverage, optional exact transient times, a hashed data asset, reported extrema and
evidence. Available assets contain `values[frame][sample]`; static fields have one
frame and no time axis. `null` is unavailable coverage, never a zero. Part fields
have one sample per declared part. Node/element/integration-point/measured-point
fields require analysis-mesh identity and explicit offline registration metadata.
The producer must supply the corresponding coordinates/connectivity and CAD-to-
viewer transformation; no nearest-surface reassignment is inferred by the client.

Use Pa, m, K or dimensionless `1` for stress, displacement, temperature and margin.
Store margin formula, criterion and threshold; no universal isotropic yield criterion
is assumed. A field's `reported_extrema` carries exact solver-sample peaks/locations;
spatial/time interpolation, averaging, exclusions and display deformation scaling
remain visible metadata. A lumped thermal result stays a part mean, not a detailed
FE temperature field. Measured points retain sensor location/time/uncertainty and
cannot silently tint whole surfaces as measured.

Evidence records provenance (`calculated`, `estimated`, `measured`, `unavailable`)
separately from validation (`unvalidated`, `numerically_verified`,
`physically_validated`, `failed`, `unavailable`), known-case/convergence flags,
assumptions, limits, sources, uncertainty and required physical tests. Calculated
results can use estimated boundaries; expose both. An unavailable field has a reason,
zero sample count and no data asset. This is absence, not a calculated zero or pass.

`export_record()` verifies dimensions/checksums and writes the manifest/assets.
`load_compatible()` is the backend consumer boundary: it rejects configuration/CAD
identity mismatches, path escapes and damaged artifacts. Historical incompatible
runs can still be listed with the reason, but cannot attach to current geometry.
The export tests use explicit synthetic fixtures; they are schema/transport tests,
not structural or thermal evidence for this rocket. Actual analysis results remain
open WO-03 deliverables until their solver/input/report records exist.

The current producers are `scripts/wo03_engineering.py` (bounded part-mean thermal
histories and elementary structural scalar screens) and `scripts/wo03_vibration.py`
(executed single-fin shell fields through `src/analysis/fin_fields.py`). An entirely
uncomputed quantity is exported as unavailable. The fin adapter verifies the source
part shape, raw mesh and solver deck hashes, node/element counts and IDs before
exporting SI displacement magnitudes and per-element maximum absolute spanwise
normal stress. The latter is a component diagnostic, not a wood failure criterion
or a structural design margin. Only the modeled fin instance is covered.

Spatial assets embed the separate S6 analysis mesh and its hash, with an explicit
affine registration from its millimetre midsurface to the viewer's metre frame.
No solver value is implicitly attached to a CAD outer-face vertex. Known-case and
mesh-convergence flags can mark numerical verification while material, root-joint
and physical validation remain open. Regenerate CAD/analysis together after a
configuration or generator change; matching old part geometry alone does not make
an old whole-vehicle result current.

The alternate `make thermal-study` producer exports the opaque-wall axial-band
model with a radially resolved liner and part-mean overlays. It keeps the initial
model available, records known-case/refinement evidence and rejects incompatible
geometry through the same backend boundary. See [thermal refinement](wo03-thermal-refinement.md)
for the model assumptions, failed temperature screens and physical test needs.
