# WO-03 fixed-shaft linkage correction

## Correction and evidence boundary

`src/cad/kinematics.py` now reads each fixed servo shaft and neutral horn tip from
the actual `servo_horns` CAD segments and part station. It checks that the rod's
neutral endpoint matches that declared horn tip. The former code used the rod
tip's axial station as the shaft station. That works for the active flat arms but
silently moves the shaft and shortens the lever when an arm is canted axially.

**Historical aft-canted diagnostics in the recovery audit require revalidation.**
The 115° candidate's reported 11/25 motion conflicts, 0.06147 rate ratio and
associated canted pose clearances came from the former inferred-shaft model.
They are retained as historical computations, not evidence for the actual fixed-
shaft six-millimetre mechanism. The independent mass ledger, root-adhesive
reconciliation, conservative guide arithmetic and hand recovery/rail load bounds
are unaffected. The original outward-arm/cap conflict and flat inboard-arm neutral
interference are separate geometry findings.

For non-monotone canted linkages, equal residual signs at the ±60° model limits
do not establish that no interior solution exists. The corrected solver first
recognizes exact neutral closure, preserves the old full-bracket solution when
available, and otherwise brackets interior roots on a 0.5° search grid. It chooses
the root nearest neutral and exposes alternatives in the result. This is a
bounded position solver, not proof of continuous assembly-branch tracking: a
tangent root without a sign change can still be missed, and independent poses
do not establish a physically continuous path. Geometry, servo authority, torque,
rate, tolerances and collision checks remain separate acceptance gates.

## Executed checks

`tests/test_kinematics.py` verifies five frozen pre-correction flat-arm positions,
including both axes and combined corners. Those outputs are unchanged within the
test tolerance. A canted six-millimetre arm retains its actual 1.012 m shaft
station and length at neutral and two perturbed positions; each rod retains its
specified length. A mismatched nominal horn/rod endpoint is rejected.

```zsh
.venv/bin/python -m pytest -q tests/test_kinematics.py
make cad
```

The code revision changes the CAD provenance identity even though active flat-arm
geometry is preserved. Fresh active CAD exports and compatible analysis records
must use the new revision; no historical analysis identity is relabeled. An earlier
export that spanned source edits is explicitly rejected by `inputs_unchanged: false`
(`wo03-20261031T021932201706Z`). It is not acceptance evidence.

The next clearance study restores original outward six-millimetre horn/rod
geometry and evaluates real cap windows and port/load sections. It must check
all changed-part pairs, declared tolerances and motion coverage before any
integration decision. No active specification is changed by this solver fix.
