# Saved replay record audit — 2026-11-03

The existing `exp-cf9e47a650074144856caf50775846d2` telemetry records a nearly nose-up vehicle during descent. At T+11.150 s the NED down velocity is +5.4560 m/s, while the nose axis has down component −0.99747: the nose points upward. The angle between nose and velocity is 173.664°. This is a recorded simulated state, not a diagnosis of the renderer or a physically validated recovery attitude. A flight can point nose-up while descending; never rotate the saved attitude to match velocity or repair historical data.

The run is the older `modular-performance-v1` G80 reference, locked and unguided with zero wind/gust, not F1 or F2. The recorded event `landing` is **116.02900000018997 s**, and the last of 116,029 rows at that time has `landed = 1`. Landing velocity is clamped to zero, so its direction and nose-to-velocity angle are unavailable. The inflation-complete metric is model-derived; deployment is the recorded modeled deployment start, not evidence of an independently recorded canopy state.

| Target time (s) | Recorded time (s) | Height AGL (m) | NED down velocity (m/s) | Nose from up (°) | Nose to velocity (°) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.170 | 0.170 | 1.503 | −19.084 | 0.000 | 0.000 |
| 10.395 | 10.395 | 635.187 | +0.0012 | 3.126 | 87.062 |
| 11.150 | 11.150 | 632.676 | +5.456 | 4.076 | 173.664 |
| 116.029 | 116.029 | 0.000 | 0.000 | 4.125 | unavailable |

[Producer](../runs/wo04-replay-record-audit-20261103-v1/producer.py) reads the saved Parquet and chooses the nearest raw row at each target. It normalizes the recorded quaternion, rotates the body +x axis into NED and compares it with recorded NED velocity; zero velocity returns null. [Machine-readable results](../runs/wo04-replay-record-audit-20261103-v1/record.json) retain row indices, raw quaternions, vectors, event times and hashes. No trajectory was generated, interpolated or changed. `src/sim/frames.py` specifies body +x noseward, NED world and scalar-first wxyz body-to-world quaternions; `src/sim/telemetry.py` specifies NED and SI units.

The saved run's code digest and the digest of the current flight/input/CAD-mass source set both equal `dde080e919510712c4a1daa1175cc76f8ca1bfafd46135cbdaae0448a3e71a90`, using the exact file ordering and scope in `scripts/wo02_sim.py:code_digest`. This supports correspondence within that digest's scope, not an identity claim for the frontend, runtime or all dependencies. Current `src/sim/dynamics.py` uses point drag with modeled inflation and damps angular rates once opening exceeds 0.1; its comment explicitly says recovery attitude dynamics are not meaningful in this simple canopy model. It does not establish suspended-body orientation.

Artifact SHA-256 values: record `c52dbc2829b1d8e30b3fef1d411eb0ca07afc04cf6d62fb80a63f1715bcc5997`; resolved file `6ba69951e46f57334155a7a9d101ad8a935ed381c9594eef79e915dc4d02e31f`; telemetry `ce81a775e824239e9587b95b932c5385834f56e2a2616ff73069b240d95bf5ae`. These match the planning-kit diagnostic's saved artifact hashes. The resolved specification hash *recorded in the run* is `c18abfee2444307e46eaaca55197693a3d9353bd8d8d8ac42162ffd238ef1d5e`; it is distinct from the resolved JSON file hash.

One diagnostic execution took 0.47 s wall, 0.29 s user and 0.06 s system time; no simulation, downloads, browser or Three runtime were used. PyArrow emitted sandbox-denied CPU-cache/NEON sysctl warnings but successfully read the data. Its default read threading was not explicitly constrained, so a strict single-CPU execution setting is unverified despite the measured CPU time. This audit does not validate interpolation, display transforms, rendered labels, camera, frontend performance, physical recovery, engineering acceptance or flight release.
