# C1/R1 attachment preflight — stopped

`record.json` preserves the one completed 0.400 CPU-second hand/guide packet.
`executed-config.yaml` and `executed-script.py` are exact execution inputs.
`connection-audit.json` corrects the receiver/end torque reference to the rocket axis and adds
read-only finite-joint/end-demand sensitivities; it never rewrites the record.
`engineering-metadata.json` marks missing CAD, stress, temperature and flutter
fields unavailable. Scalar strip results are not geometry overlays.

The saved C1 record and source-lock ledger pin the complete prior identity.
All eight source files used from the generated staged checkout were byte-identical
to their maintained repository paths, mapped and hashed in engineering metadata.
No staged generated mesh, CAD bulk, dependency or simulator change is published.
The maintained `scripts/wo03_c1_fin_attachment.py` is byte-identical to its
as-run copy. It refuses overwrite; do not rerun to recreate valid saved outputs.
The first read-only audit is retained as superseded-connection-audit-v1 files;
its socket-centre torque was not the receiver-axis torque. The current audit
checks force/couple transport invariance and strengthens the failure screen.
No repeat/native refinement is admitted by the stopped R1 decision.

See `docs/wo03-c1-fin-attachment.md` for complete connection/weight/guide/static/
recovery results, source-property limitations and the one next construction
preflight. Original C1 and additional20g/motor-CG cases remain separate;
full50g is counted once. No active adoption or owner physical release.
