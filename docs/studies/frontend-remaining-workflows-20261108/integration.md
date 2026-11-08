# Primary workflow integration

The source-lane experiment-analysis.json is a historical freeze of its original seven code/test files and saved-manifest observations. Primary integration then checked the Analysis guard against the existing Python `src/analysis/records.py` consistency rules. The current response guard additionally requires flight_ready=false, preserves unavailable-evidence semantics, rejects measured fields without located-point association, rejects inconsistent part sample counts, requires design-margin definitions and available spatial mesh/registration metadata. The new analysis-consistency-guard test exercises those cases. This is the same backend contract, not a new engineering threshold.

The source-lane synthetic fixture explicitly carries flight_ready=false. Two original lane files therefore have newer integrated hashes; do not treat the lane JSON's original hashes as current publication hashes. Existing optional saved nominal-fin manifests still pass. No original record, spatial data, geometry or engineering result was regenerated.

A focused16-case integration check passed with no skips, including existing field-boundary, monitor and response tests. Full relevant source checks and hosted required jobs are recorded at publication. Missing raw cache/analysis assets remain explicit optional skips in other environments, never real-field validation.

This first workflow PR intentionally excludes the independent Replay drawing and recovery-storyboard files. They are mounted only in the next separately identified rendering increment, keeping the monitor/Analysis correction independently buildable. Native monitoring/error branches remain open until separately observed.

Integrated local suite:228tests passed, no skips; type/lint/format/packaged build passed. Four preserved A2 tests and eight next-increment drawing/storyboard tests are outside this focused publication;216 cases belong to its published source. The hosted job remains the authoritative clean-checkout result.
