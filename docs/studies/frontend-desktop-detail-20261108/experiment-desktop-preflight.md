# One desktop experiment → saved run → comparison/export packet

**Use the supported archived G80 reference, one Tiny run, and its existing matching seeded calm baseline.** This preflight read frontend/API source and saved `record.json` metadata only. It executes no simulation, telemetry read, cancellation, browser action or source change. The [machine-readable packet](experiment-desktop-preflight.json) records request, source identities, baseline, actions and stop conditions.

**Tiny is 45 seconds, not 9 seconds:** current UI and API specify **0.005 s × 9,000 steps = 45 s**. The API resource declaration and execution case agree. A first-nine-seconds visual segment ends before the saved baseline's apogee/deployment; that is not a nine-second Tiny profile or evidence those recorded events are missing.

## Exact single-run setup

| Control | Required value |
|---|---|
| Vehicle and motor | **Performance · G80 reference** — `modular-performance-v1` |
| Steady wind (m/s) | **1.0** |
| Wind direction toward (° clockwise from north) | **0** |
| Gust amplitude (m/s) | **0** |
| Preset | **tiny · 45 s / 9,000 steps** — select explicitly; UI defaults to `sim` |
| Random seed | **20261107** |
| Bounded seed sweep | **Unchecked** — exactly one case |

The run uses local CPU, concurrency one, sensor noise enabled, elevation 850 m and locked/unguided control. No new motor, controller, source geometry, paid run or flight condition is adopted. RP1 has no admitted flight configuration; do not submit it or borrow archived geometry for it.

Record and preserve the actual Design source/view state before entry. The expected restored RP1 source is `G80-F2-RP1-AD1-definition-v2`, specification `811b3bed…31660`, geometry `238d01e5…28b608`; its actual native state remains for the verifier to observe. `App.tsx` and `experimentContext.ts` give Experiments a separate configuration. Choosing G80 there must not replace the working Design.

## Compatible existing baseline

Use **B = `exp-d0baf4168f7f41e687a1b5f12e14cc3e`**, a complete saved attempt with a **partial trajectory**. Its settings are the same G80/Tiny/seed/direction/gust as above, with wind **0 m/s**. All five recorded source-input hashes match present files. Its exact identities also match current source:

- Resolved specification: `c18abfee2444307e46eaaca55197693a3d9353bd8d8d8ac42162ffd238ef1d5e`
- Simulation code: `a58cde7fad6f24188887b019b4dc9632413ef1b20a0cacc7c1382c3010aa8d6f`
- CAD revision: `1193713d0f4a7ad8393a00a0a03e7aaa04e9aa9393d2034691ef7126ae3cdd3b`
- Baseline record SHA-256: `5acd508733529ff9588a7f0d6e759b03371d155ac94c0c38726b6db413506559`

It records 9,000 samples and `trajectory_complete=false`. Events are ignition 0 s, guide exit about 0.17 s, burnout 1.8079 s, apogee about 10.4 s, deployment about 10.7 s and **landing null**. Landing is outside this recorded Tiny case; partial recovery is expected from this baseline. These are saved metadata observations, not new results or promises about the future wind run.

The future **A ID must come from the actual accepted response**. Only after its saved configuration, seed, case, code/spec/CAD and full input-hash dictionary match may the pair be described as a matched-source/profile/seed wind-speed sensitivity. Expected setting differences are wind 0→1 m/s and the derived north-wind case 0→1 m/s; direction remains 0°, east wind and gust remain zero. No controlled physical or scientific-quality comparison is inferred from a GUI pairing. Historical 116/132-second `sim` runs differ in duration/timestep and code identity and are not substitutes for this Tiny baseline.

## Minimum native actions and observations

1. Capture the actual Design identity/state; enter **Experiments** and set the six controls above. Confirm the experiment context is G80 and the seed sweep is unchecked.
2. Click **Run on CPU once**. Capture exactly one accepted `exp-…` ID and its observed queued/running/terminal states. If acceptance is uncertain, inspect saved attempts without submitting again.
3. If the attempt completes within the observation deadline, load that actual ID as **A** from Saved runs. Confirm exact recorded settings, source identities, validity and full/partial status. Stop on failure or mismatch.
4. Find the exact baseline ID above in Saved runs and click its **Compare** button. Confirm A is the new run and B is the baseline. Use **Absolute elapsed time**, offsets zero, and normal **bounded** playback; do not enable the full-rate benchmark.
5. Inspect actual event/missingness labels, scrub to a recorded in-range event, and use **Fit both trajectories**. Optionally **Play → Pause for at most five seconds** to observe interaction. This is not a full-flight or frame-rate qualification retake.
6. Remain paused, **Reset plot range**, then request **Download A range CSV** and **Download A metadata JSON** once. Observe actual downloads named `<newRunID>-playback.csv` and `.json`. Metadata must retain A/B identities, selected profile/range, offsets and differences; missing values remain missing. No export is expected to be full-resolution telemetry in bounded mode.
7. Return to Design and verify the original source/view state remains preserved. Restore only changes made within this packet.

## Resource and stop boundary

Allow **one submitted run**, at most **9,000 model steps**, a **90 s computation-observation deadline**, and a **180 s overall native packet guard**. Keep a 30 s reserve for closeout; stop optional actions rather than overrunning. No batch, automatic retry, cancellation experiment, full native playback/performance campaign or data repair follows.

**The current API does not enforce a hard 90 s worker timeout.** Cancellation is cooperative before/after compiled rollout. At the 90 s deadline, stop packet actions and report the observed state; do not claim the worker terminated. If guaranteed worker termination within 90 s is mandatory, this packet cannot meet that requirement without a separately authorized bounded runner. Historical recent Tiny attempts finished rapidly, but they do not guarantee a future duration.

Stop on changed/private context, wrong source, uncertain/multiple acceptance, failed attempt, source/profile/seed mismatch, missing compatible baseline, export coverage rejection or deadline. Preserve the attempt and evidence; no retake. Source preflight, actual backend execution and native interaction remain separate evidence classes. All five inquiries remain UNSENT; engineering/build/thermal/recovery/flutter/WO-10 and flight gates remain unchanged.
