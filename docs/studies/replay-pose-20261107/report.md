# Replay pose reference — 2026-11-07

The production scene and follow camera use `replayPose`, tested against independent scalar quaternion and matrix results generated from the exact saved `modular-performance-v1` run `exp-cf9e47a650074144856caf50775846d2`. [Compact reference](reference.json) contains the saved descent and five recorded-event brackets; [manifest](manifest.json) records source and artifact hashes, timing and tolerances.

A single PyArrow read of selected columns took 0.240 s CPU / 0.350 s wall after imports (116,029 full samples; 3,009 API-style selected samples), inside 30 s / 60 s limits. macOS blocked optional cache/CPU sysctl probes; Arrow completed. At T+11.15 s the saved raw velocity is +5.456039 m/s NED down and the reference nose is approximately 4.0763° from up. This is not, by itself, a renderer fault.

Synthetic identity, launch-up, sideways, q/−q, nonzero pivot, malformed or missing inputs, explicit gap limit, endpoints and unequal windows accompany recorded descent/event fixtures. Production pose output is checked to 1e-9 m for position/pivot and 2e-8 per matrix component, with event continuity checks. Missing attitude or CG retains valid position as a labeled marker; missing position and outside-window samples produce no actor. Gaps have no supplied source threshold; the optional helper threshold is tested but is not silently imposed in the app.

Quaternion normalization and SLERP, NED-to-scene/CAD-to-body matrices and CG pivot preserve the prior source convention. The model's simplified recovery attitude remains approximate, with no canopy/line or suspended-body dynamics. Node tests are not browser interaction, image, physical or flight acceptance.
