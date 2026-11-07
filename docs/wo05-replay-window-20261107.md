# Replay comparison — respect each recorded window

This is a bounded correction to the existing preview, separate from the Design
revamp and from physical model validation. The
[pre-correction audit](studies/frontend-revamp-20261107/replay-contract-audit.md)
traced an inconsistent display: the shared cursor extends through the longer
comparison run, readouts withhold values outside each run, but the 3D actors were
held at their endpoints. The comparison validity panel also received a clamped
time. No simulation was rerun to establish this source-level defect.

The correction validates a finite strictly increasing time axis independently
for A and B. Each actor exists only within its own inclusive recorded interval.
The scene, comparison validity and camera use the shared requested time without
clamping it to a shorter run. Outside A, follow mode has no current position to
track; its path remains a recorded path. Both panels state **Outside recorded
window** or unavailable and show the supported time interval. At an exact endpoint
the saved sample remains eligible. An initial cursor before the first returned
sample also remains outside; no launch pose is extrapolated. A newly opened run
starts paused at its first actual saved sample, and restarting comparison uses
the earliest available recorded start. The audited run begins at T+0.001 s;
this avoids an empty initial actor while retaining honest support boundaries.

In-window interpolation, frame matrices, CAD pivot and quaternion interpretation
are unchanged. This does not fix or cosmetically rotate the saved nose-up descent.
The diagnostic remains a recorded result: at T+11.150 s, downward velocity is
5.456039 m/s while the nose is 4.076303 degrees from up. Recovery attitude is
approximate; separate canopy, lines and suspended-body motion are not modeled.
Further pose validation and an explicitly scoped marker-only recovery presentation
remain later RV-11 work, not a pass from this time-window correction.

Focused tests cover either run being shorter, nonzero starts, exact endpoints,
empty/unordered/repeated/nonfinite times and preservation of recorded samples and
the requested cursor. They establish pure time-gating behavior, not observed
Three.js actors or camera transitions. The combined local116-test suite, packaged TypeScript/build, lint and formatting
pass. Required hosted checks remain part of the focused PR workflow. Browser observations remain blocked by
the original designated-runtime prerequisite; no retry or bypass occurred.

The parallel [analysis inventory](studies/frontend-revamp-20261107/analysis-source-inventory.md)
is preparation for RV-14/15. None of 27 saved manifests matches the corresponding
currently saved CAD identity. Matching payload checksums do not establish mesh
registration or eligibility. AD1 has no matching complete CAD/overlay. The detailed
inventory remains a local generated artifact; the versioned index is compact.
No failed/superseded thermal field is promoted to an accepted current overlay.

Current RP1/AD1 source inspection and separate archived CAD/replay remain distinct.
No vehicle, mass, material, load, controller, recovery physics or engineering
acceptance criterion changes. Inquiries remain UNSENT; no purchases, physical
tests, paid runs or flight release are authorized.
