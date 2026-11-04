# Inspection asset readiness — 2026-11-03

All four recorded reference configurations have matching local manifest/source
identities and a complete set of listed GLB files. **G80 reference** is a useful
first inspection choice: it has 42 recorded parts, source dimensions and part
explanations. It is the older `modular-performance-v1` reference, not the
current dedicated G80-F2 or RP1 concept. This is a file readiness result; it
is not an observation of a running API, browser, WebGL, part selection or
engineering acceptance.

| Catalog configuration | Saved manifest | GLBs present / required | Parts with nonempty geometry / learn text / CAD bounding box | Identity and coverage |
| --- | --- | ---: | ---: | --- |
| G80 reference `modular-performance-v1` | `build/modular-performance-v1/manifest.json` | 42 / 42 | 42 / 42 / 42 | Match |
| G54 conditional `modular-performance-g54-hypothesis` | `build/modular-performance-g54-hypothesis/manifest.json` | 42 / 42 | 42 / 42 / 42 | Match |
| G12 finned trainer `modular-tvc-finned-v1` | `build/modular-tvc-finned-v1/manifest.json` | 53 / 53 | 53 / 53 / 53 | Match |
| G12 finless concept `modular-tvc-finless-v1` | `build/modular-tvc-finless-v1/manifest.json` | 51 / 51 | 51 / 51 / 51 | Match |

No listed GLB was missing, out of its expected `parts/<part-id>.glb` path or
associated with a mismatched recorded part-shape identity. The check compared
configuration, resolved-specification hash, CAD-source revision and each part
shape hash with current resolved source, and verified exact part coverage.
Nonempty geometry means a source geometry dictionary exists; it does not mean
that every manufacturing dimension, interface, internal mechanism or drawing
is known. Bounding boxes are stored CAD envelopes and learn text is recorded
explanation; neither demonstrates physical fit or flight readiness. 2D
source-dimensioned representation is implemented for supplied inspection data,
with unsupported shapes marked unavailable; this file inventory did not count
drawable 2D envelopes or observe actual 2D rendering.

The manifests do **not** record expected GLB byte digests. The accompanying
[record](../runs/wo04-inspection-asset-readiness-20261103-v1/record.json)
fingerprints the currently present mesh bytes, but those fingerprints alone do
not independently prove the files match the bytes originally exported. The
source-level API reads the manifest and snapshots each GLB hash at application
startup; it rejects changed files during serving. A running host instance may
have different source, artifacts or startup identity. The four Design catalog
entries depend on the API/source availability; no separate prepared Design
catalog fallback was established in this file audit.

## Separate current concepts

- **F2 `G80-F2-fixed-stock-ballast-v2`:** prepared engineering fallback
  `web/public/engineering-workbench/preparedg80-fixed-f2.json` is present; all
  10 listed source hashes match. Its source drawings and local joint CAD are not
  a complete F2 vehicle mesh. Full F2 engineering acceptance remains open.
- **F2-C1 `G80-F2-C1-fit-proposal-v2`:** prepared engineering fallback
  `web/public/engineering-workbench/f2-c1.json` is present; all 13 listed
  source hashes match. It is an unadopted connection proposal with no complete
  vehicle CAD. Old ring diagnostic fields do not represent its changed fit.
- **RP1 `G80-F2-RP1-balanced-v2`:** the record identity and its three source
  hashes match. The separately identified recommendation has a local
  [offline drawing index](../output/f2-recovery-precedents-balanced/index.html);
  no complete vehicle CAD or Design-catalog registration is established. It is
  not adopted and its installed recovery and root-support evidence remains open.

Prepared F2/F2-C1 snapshots are engineering-source projections, not Design
vehicle fallbacks. Their frontend fallback applies only to an exact missing-route
404; a source error, mismatch or other server failure is not an equivalent
fallback condition. The presence of these ignored prepared files does not prove
the active host serves them.

## Method and remaining observation

The audit read the API implementation before choosing file-only checks. Its GET
routes do not invoke CAD or engineering/flight solvers, but app startup also
constructs snapshots and performs mass/aero calculations; this audit made no API
calls and performed no CAD, numerical simulation or server start. It resolved
the four specifications using the existing schema and compared saved manifests
and source files. Initial invocation failed to import `src` from a temporary
script; setting the repository on `PYTHONPATH` corrected the setup. The
successful inventory took 0.473 seconds wall and 0.430 seconds CPU, within the
15 CPU / 30 wall budget; RP1 source hashes were separately read afterward.

For actual usability, the owner can use the normal-terminal steps in
[the verification checklist](frontend-owner-verification-20261103.md) once
appropriate, and the designated browser agent must observe the permitted
window after its runtime-ownership prerequisite is resolved. A sandbox `EPERM`
probe does not establish whether a host listener exists. No browser access or
workaround was attempted for this inventory.
