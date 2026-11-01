# G80 bridge — coarse numerical consistency, engineering acceptance open

The saved actual bridge geometry now has two Elmer fields that pass the
unchanged global force and reciprocal-work checks. This is a useful component
numerical result, **not strength, stiffness, fit or convergence acceptance**.
The active rocket and its flight predictions are unchanged.

| Question | Result | Limit |
| --- | --- | --- |
| Input geometry and loads preserved? | 22,495 quadratic tetrahedra, seven material regions, 42,715 used nodes; exact original 3,184 / 1,072 load tokens, support mapping and mesh checks retained. | Same original connection, material and fixed-support assumptions; sampled Jacobians are not a continuous geometry proof. |
| Did calculations finish? | Both native logs end `ALL DONE` and return codes are zero. EQUAL used15.172 CPU/15.566 wall seconds; SINGLE14.745 CPU/15.078 supervised wall seconds. | Original EQUAL workflow stopped on output discovery. SINGLE supervision failed on a terminal RSS query. Neither stopped workflow is relabeled successful. |
| Do saved fields balance force? | Separate read-only EQUAL/SINGLE evaluations pass the unchanged1e-5 N criterion. Axial residuals−7.884e-10 / −1.115e-9 N, encoding bounds4.178e-14 /5.025e-14 N. | Applies to these mapped Float64 fields and source loads; not a stress or discretization-error bound. |
| Is reciprocal work consistent? | Cross-work0.04008097325330081 /0.04008097325330107 N·m; difference2.637e-16 versus4.840e-16 N·m propagated encoding bound. | One coarse geometry; does not establish regional stress or displacement convergence. |
| What deformation was observed? | Maximum displacement magnitude0.380782 mm distributed load /1.157007 mm single-washer load. | No bridge deflection acceptance follows. The separate1 mm fin-tip criterion must not be applied to this different part. Contact, retention and linear-model validity need their own assessment. |
| Were resource guards fully successful? | One CPU requested; observed SINGLE root RSS maximum1.059 GB, with native CPU/wall below the declared limits. | The terminal RSS-reader failure remains unexplained; true child peak/tree RSS unavailable. Full memory-guard compliance is not claimed. |

The saved CalculiX actual-bridge failures remain unchanged: reaction residuals
104.697 /22.093 N and reciprocal-work discrepancy32.229 N·mm. No physical
geometry correction caused this new result: the existing Elmer direct path was
verified on the known cases, then used on the preserved bridge inputs. The
comparison does not identify why the older CalculiX result failed.

The EQUAL workflow searched the wrong output locations. Its log names
`../field_t0001.vtu`, and the separate read-only evaluation used that unique
saved file without rerunning it. The remaining SINGLE continuation first
stopped before preflight on a Python import path; its one path-only replan
launched SINGLE once. The native process finished, but the supervisor recorded
an RSS `ESRCH` failure near exit. Read-only recovery then checked its saved field
and reciprocity. All stops, admissions, hashes and disabled configurations are
preserved. No native case was repeated.

The [source audit](wo03-elmer-load-field-semantics.md) explains why the saved
load vector contains both point loads and support reactions. Only the mapped
support entries are summed for the reaction check. The separate
[exit audit](wo03-bridge-supervisor-exit-audit.md) preserves the resource gap;
it does not infer an unsampled memory peak from the parent or last sample.

## Remaining design acceptance and bounded next step

Recovering these fields closes the observed coarse reaction/reciprocity
obstacle for this Elmer calculation. It does not close the installed load path.
Before assigning strength or stiffness credit, verify the applicable stress
output on a known case, retain the actual bond/bearing/support assumptions,
and meet the existing three-grid displacement (<5%) and regional-stress (<10%)
convergence criteria. Check relevant hot properties, contact/retention and
linear-model limits. A single-washer1.157 mm displacement requires interface
interpretation; it is not silently rounded or called acceptable.

No further native attempt is authorized by this report. First address the
narrow terminal-supervision bookkeeping with existing software checks and
preserve its failed record; then declare any required stress/refinement packet
and its stopping conditions. Thermal acceptance, installed fin/root/flutter,
complete recovery attachments and packaging remain open. Reuse the compatible
mass/static/flight results until actual design changes require revalidation.

Evidence: [diagnostic controls and results](wo03-elmer-bridge-diagnostic.md),
[compact stop/recovery manifest](../runs/wo03-elmer-bridge-recovery-20261101-v1/manifest.json),
[EQUAL recovery](../runs/wo03-elmer-bridge-recovery-20261101-v1/equal-recovery-summary.json),
[SINGLE recovery and reciprocity](../runs/wo03-elmer-bridge-recovery-20261101-v1/single-recovery-summary.json).
Large meshes, VTUs and full status histories remain local and hashed.
