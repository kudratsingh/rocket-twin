# WO-03 G12 layered-fin source refreeze

**The historical G12 proposal has a current-schema-valid resolved copy and an
inspectable assembly, but it is not an accepted installed-root design.** The
source is the archived 70 mm-span layered-fin/hoop proposal; it is separate
from the 69df G54 baffle candidate. No contact, strength, motion, thermal or
flight pass follows from this identity work.

The original hoop YAML (`81529f6a…`) still fails current validation with the
60 stale CAD-property errors previously recorded. The previously reconciled
77-part `runs/wo03-installed-root-20261031T041923712847Z/reconciled-source-only.json`
already reloads under the current schema. Its canonical resolved-spec SHA-256
is `4ff75b8f2c6ab47ddf90b546761d7fa6d4a72c3af9f382e6b3790cbeb19c1287`,
the exact historical installed-root identity. The output copy is byte-identical
to that reconciled JSON, SHA-256
`8528d3f550ab31f53e51dcd894ce4dced1f3e6acec26f322d6f047270de192af`.
It has no non-mass/non-cache part-field changes from the older hoop YAML. It is
an existing reconciled identity validated again, not a newly adopted design or
an assertion that clearing a cache corrected an engineering fault.

## Artifacts and provenance

The bounded output is `build/wo03-refreeze-g12-root-v1/`, with
`resolved-candidate.json`, `assembly.step`, exact copies of `fin-layers.step`
and `recovery-cap-frame.step`, and `record.json`. The record identifies all
input files, hashes, per-part comparisons and assembly hash. The original source
files were hashed before and after and were unchanged. The actual original
layered fin STEP `74a4a92b…` and rounded hoop-frame STEP `d012f279…` were
hash-checked and preserved byte-for-byte in the output. Reconstructing the
rounded recovery junction uses its recorded configuration; remaining shapes
use the current `src/cad/parts.py` generator and the existing schema. No
unpublished historical driver is imported. Current CAD and schema source hashes
were also saved after execution in `post-run-code-hashes.json`; they were **not**
hashed before the child ran and therefore do not establish unchanged code
during the run.

The output assembly is built with the two preserved real STEPs in their recorded
locations, plus those generated parts. The schema's generic exporter alone
would regenerate a homogeneous fin and omit the frame's added rounded saddles;
it does **not** reproduce this assembly. Use the explicit output assembly and
its source manifest, not the generic exporter, when inspecting the historical
proposal.

## What was compared

All 77 regenerated geometric volumes equal the previously reconciled per-part
cached volumes at the stored precision. For the 76 parts other than the layered
fin, geometric centroids and all nine components of inertia per unit mass also
match their historical cached values at stored precision. The fin's archived
centroid and inertia are **density-weighted composite** quantities; the new
geometric values use uniform volume and are recorded but not compared as if
identical. Its actual multi-material STEP is the original file. The record also
lists each new local and placed bounding box.

Historical per-part BReps or bounding boxes are not available for the other 75
parts. The two preserved STEP files establish exact source-file identity for the
fin and frame, but matching volume, centroid and inertia does not prove that
another part has the same detailed shape. Historical bounding boxes are recorded
as unavailable for those parts; no geometry-change or geometry-equivalence claim
is inferred from those matches. The new assembly STEP has not been used to
revalidate rigid interferences or motion.

The actual preserved fin and frame placements and their copied input geometry
retain the critical longitudinal references: fin root z=1.055–1.175 m, tab
z=1.065–1.165 m; frame z=1.012–1.180 m, frame channel and shell slot start at
z=1.065 m. The original three-fin STEP's placed z bounding box extends
1.0548–1.1752 m because its material layers/caps are included. The nominal
shell ends at z=1.175 m. These are source identity/coverage observations, not a
contact fit, bond wetting, compliance or tolerance pass. The complete source
parameters and bounds are in the record.

The older hoop YAML totals 781.641872 g; the reconciled copy totals 781.572198 g,
a 0.069674 g CAD mass reconciliation difference. No saving is credited to the
unchanged G12 guide or 50 g growth budget. Mass properties are modeled values,
not measured hardware.

## Boundaries and validation

One supervised child completed within the 120 s wall cap: parent-observed
elapsed time was 7.870 s; the worker reported 3.747 CPU s and 2.292 s wall
after its imports, with peak RSS 539,836,416 bytes. Thread environment variables
were set to one and one child was launched. Because reported process CPU time
exceeded the same measured worker wall interval, single-core execution is **not
established**; the observed process may have used additional native threads.
The parent wall measurement includes startup. No full FEA, thermal method or
flight propagation was run.

Black, Ruff and the focused property-comparison test passed. These verify the
comparison bookkeeping, not the assembled structure. The previous flat-horn,
fixed-shaft and motion-conflict history remains open; a current coupled pose,
clearance, structural contact/peel, root stiffness, material and flutter
assessment is still required. The 57.629 N contact sensitivity belongs to this
historical G12 family and is not transferred to 69df. No original artifact,
active configuration, design mass allowance, acceptance or release gate changed.

## Published evidence and reproduction boundary

The compact record is [`wo03-g12-source-refreeze-20261101T010604113596Z/record.json`](../runs/wo03-g12-source-refreeze-20261101T010604113596Z/record.json). It preserves the executed comparison,
completion/resource observations and post-run-only code hashes. STEP files and
the archived resolved candidate remain local generated/source artifacts.
Running `.venv/bin/python scripts/wo03_refreeze_g12_root.py` requires all
hash-matching archive paths in `configs/studies/wo03-refreeze-g12-root.yaml`;
a clean checkout without those artifacts cannot recreate this historical copy.
The archived installed-root configuration is a provenance input for a rejected
capture study, not an adopted design or an executed dependency on its driver.
