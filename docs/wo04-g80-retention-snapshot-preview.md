# Experimental G80 retention snapshot in the early inspector

The separate **Experimental G80 retention candidate · 72 parts** selector entry
is a read-only archived snapshot. It is unadopted, engineering acceptance is
open, and the active 42-part G80 reference and the other three configurations
remain separate. It represents candidate resolved SHA-256
`90b2a9ad780fc81d11171363432c46088531817ddb6570fe9f800429bde2bdfc`
and staged CAD revision
`344f646f81e15d42ab54e7d996179581d638c6046bf1d006935b028709eca53f`.
It does not include the later 73-part canopy candidate or its results.

The source was validated under its own isolated staged CAD factory and normal
schema, then projected into the existing read-only inspector. The projection's
nominal modeled mass is **772.981712 g**, with CG **804.403217 mm** from the
nose and a separate **50 g** growth allowance. These values come from the
resolved model and are checked against the published 72-part run record. All
72 displayed GLBs were copied byte-for-byte from the staged export. The 21
service parts' generic source accounting envelopes are not displayed as their
physical dimensions: their recorded CAD bounding sizes are labeled as bounding
sizes, not purchased hardware dimensions.

Select the candidate under **Candidate designs — not adopted**, choose parts
in the tree and use the ordinary highlight, hide, isolate, explode and fit
controls. Experiment and Analysis modes show an inspection-only explanation
for this snapshot. Select the active G80 reference to run or replay existing
flights; an active 42-part run cannot be attached to this 72-part geometry.
No compatible accepted stress or temperature overlay is attached. The bridge
reaction-force and reciprocity checks failed; the thermal method is
unqualified, and installed root/flutter and recovery remain open. This is not
physical qualification, an adopted design or flight authorization.

## Local preparation

With the original staged checkout, 72-part export and published compact run
record retained locally, from the repository root:

```zsh
.venv/bin/python scripts/wo04_prepare_candidate_snapshot.py
make preview
```

Open <http://127.0.0.1:5173>. The helper does not regenerate CAD or run flight
physics: it creates a temporary copy of the staged runtime, validates the
archived resolved configuration and manifest with that staged CAD contract,
checks source hashes against the published record, projects the inspector data
and backend-derived 5% burn samples, and copies the existing GLBs into
`build/wo04-g80-retention-snapshot/`. It refuses to overwrite an existing
snapshot. The root API checks the pinned snapshot index, projection and each
served mesh hash; missing or changed files are unavailable. The staged runtime,
source GLBs and prepared snapshot are local artifacts and are not part of a
source-only checkout. A fresh checkout cannot prepare this snapshot until those
exact local artifacts are restored. This local source-bound projection is not a
new CAD or engineering analysis.

The prepared index SHA-256 is
`53ea17425115ec5ebefe7c1327f95b6cf1c99723bb48306185e382803f03fc26`;
projection SHA-256 is
`9762211e0f51aef9140e04d3c76a846079cf4fc736bc2ba6813a3bce22badfe9`.
The published source manifest SHA-256 is
`bc29e4a72f25d9931991646153ab659b4ec084cc62bfcd541d86747d91a51d99`.
The separate 72-part mass/samples and GLB hashes are retained in the local
snapshot; the index does not promote candidate geometry into active designs.

## Validation and current limit

The in-process API loaded the actual prepared snapshot, returned 72 parts,
the recorded mass and CG, served a candidate GLB, and rejected the snapshot as
an experiment configuration. All 72 copied GLBs matched their staged sources
and 21 service parts received labeled CAD bounding sizes. Automated synthetic
fixtures exercise candidate/active catalog separation, missing or altered
projection, mesh tampering, allowlisted paths, supported burn increments and
experiment rejection. The frontend and API checks are recorded in the handoff.

Current browser verification of this increment has **not** been performed:
automatic approval review rejected the computer-use documentation call, saying
the designated frontend-agent ownership prerequisite was not satisfied. An
older screenshot of the active preview is not evidence of this new candidate.
The changed API must be loaded by the host API process before its UI can expose
the candidate; the running host process's current revision has not been
verified in a browser. Full WO-03/04/05 acceptance and all physical, paid-run,
WO-10 review and flight-release gates remain open.
