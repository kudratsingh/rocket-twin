# Isolated 72-part G80 stage 2: static and flight results

The exact unadopted candidate `90b2a9ad780fc81d11171363432c46088531817ddb6570fe9f800429bde2bdfc` passes the requested **preliminary static comparison and all four guide-speed screens**, but **all four modeled landings exceed the 6 m/s total ground-speed screen**. This is not flight release, recovery qualification, structural acceptance or adoption. No CAD, structural or thermal run was performed in this stage.

The copied resolved spec, stage-1 record and manifest were byte-identical to the retained stage-1 files. The staged `Vehicle` validated normally at the real staged CAD revision `344f646f81e15d42ab54e7d996179581d638c6046bf1d006935b028709eca53f`; all recorded source hashes remained unchanged. The source motor is the existing preliminary AeroTech G80 curve, the motor is fixed, `tvc` is absent, and these are unguided modeled trajectories. Cases use dt=0.005 s, a 180 s horizon, 850 m elevation hypothesis and the existing 1.5 m guide. The full growth sensitivity is an additional 50 g at 1.212 m, not an expended or removed allowance.

Nominal loaded mass is **772.982 g**, with its balance point **804.403 mm aft
of the nose**. The full separate allowance gives **822.982 g** and
**829.167 mm**. The mass model removes the prior 7 g retention lump once,
replaces it with itemized hardware and a distinct 1 g estimated locking/materials
reserve, and retains finish, fin bonds and the conservative adhesive budget.
That reserve is not an identified locking method or a measured supplier mass.

Independent RocketPy 1.13.0 static comparison passed its existing mass/CG/CP/stability thresholds at loaded and burnout states. With full aft growth, static margins are **1.1663 cal loaded** and **1.5483 cal burnout**, above the existing 1 cal screen; CP is 906.140 mm. A separate source-method **+12.8 mm motor-CG** assumption gives 831.161 mm loaded CG and **1.1360 cal** with full growth. That shift is an exploratory +10% motor-length sensitivity, not a measured CG or certified tolerance. The preliminary static launch screen gives 16.328 m/s. The schema's `all_parts_have_build_and_cost` check means a build record exists; several new zero-dollar values are explicitly **unpriced placeholders**, not confirmed free parts.

| Case | JAX apogee / time | Guide exit | Powered max α / tilt | Trigger / inflation complete | Landing time | Landing total ground speed / horizontal | Landing downrange |
| --- | --- | ---: | --- | --- | ---: | --- | ---: |
| Nominal calm | 620.610 m / 10.390 s | 18.772 m/s | 0.827° / 1.598° | 10.395 / 10.995 s | 111.495 s | 6.071 / 0.134 m/s | 7.805 m |
| Full 50 g, 0.85 thrust / 0.95 time / 1.2 drag, 0.5 N guide friction | 433.240 m / 9.040 s | 16.848 m/s | 0.926° / 1.857° | 9.040 / 9.640 s | 77.710 s | 6.281 / 0.124 m/s | 8.847 m |
| Full 50 g, 1.15 thrust / 1.05 time | 725.369 m / 11.070 s | 19.700 m/s | 0.916° / 1.818° | 11.075 / 11.675 s | 125.015 s | 6.279 / 0.148 m/s | 11.373 m |
| Nominal, steady 3 m/s east wind, zero gust | 618.312 m / 10.390 s | 18.770 m/s | 8.788° / 5.316° | 10.395 / 10.995 s | 114.145 s | 6.731 / 3.248 m/s | 293.792 m |

All four guide speeds exceed 15 m/s and all trajectories were finite and landed within the 180 s horizon. The total speeds shown are ground-relative magnitudes from the last telemetry row before the landed flag, sampled on the 5 ms grid. **All exceed the requested 6 m/s total-ground-speed screen.** The existing static parachute-area estimate uses a 6 m/s steady **vertical descent** target; that vertical-only physical quantity is different from total ground speed, particularly in wind. This record does not claim a separate vertical-speed check or substitute horizontal speed for either quantity. Trigger, inflation, wind, drift and landing are outputs of the existing simulation, not physical recovery or range validation.

For the nominal calm case, RocketPy predicted **620.6499 m / 10.391778 s** versus JAX 620.6096 m / 10.390 s: differences **0.00650% in apogee** and **0.01711% in time**, within the existing 5% comparison gate. The RocketPy ascent comparison uses shared mass/inertia inputs and does not independently validate the full tensor, wind response, attitude, downrange or recovery; the growth and wind cases have no RocketPy comparison. The complete loaded full-growth inertia tensor in body axes, kg·m², is:

```text
[[ 0.000912688389,  0.000190626821, -0.000188729546],
 [ 0.000190626821,  0.137634031175, -0.000000113582],
 [-0.000188729546, -0.000000113582,  0.137635975742]]
```

All loaded/burnout tensors and lateral CG values remain in the [flight record](../build/wo03-g80-integration-staging/checkout/build/wo03-g80-stage2-flight/record.json), with sampled [landing details](../build/wo03-g80-integration-staging/checkout/build/wo03-g80-stage2-flight/landing-screens.json), [static record](../build/wo03-g80-integration-staging/checkout/build/wo03-g80-stage2-static/record.json) and [source/resource ledger](../build/wo03-g80-integration-staging/checkout/build/wo03-g80-stage2-supervision/record.json). Telemetry parquet stays local. Stage 1's source-equivalent geometry and full mass bookkeeping are preserved; the three recovery overlaps, hardware/locking details, anchor, installed fin/root/flutter, bridge reaction failure and unqualified thermal route remain open.

The static child used **14.056268 CPU s / 14.691 s wall**, maximum sampled RSS **168,738,816 bytes**. The four-case flight child used **19.592993 CPU s / 18.522 s wall**, maximum sampled RSS **530,235,392 bytes**. These are separate process samples, not simultaneous combined peaks. One worker and single-thread library settings were requested with live 2 GiB RSS guards; flight child CPU exceeded wall, and OS affinity was not established. The declared limits were 60 CPU/60 wall static, 120 CPU/120 wall flight and a separate 30 CPU s setup reserve, with 210 CPU s planned under the 600 s ceiling. The source ledger includes staged code, motor/config inputs and unchanged original/copy hashes. Matplotlib fell back to a temporary writable cache and Arrow reported denied optional CPU-cache `sysctl` queries; the logged runs and saved outputs completed. No purchase, production promotion or active preview asset was changed.

The [compact publication record](../runs/wo03-g80-staged-retention-20261101-v1/record.json) retains the candidate identity, tensors, cases, reference results, landing screens, source hashes and resource limits without bulk geometry or telemetry. The exact resolved candidate and staged source patch are included there; reconstructing the underlying CAD comparisons additionally requires the separately retained local baseline and keeper STEP sources identified by hash.


### Saved vertical landing audit

The last pre-landed samples give downward velocities of 6.0697 m/s (nominal calm), 6.2799 (growth low thrust), 6.2768 (growth high thrust), and 5.8955 (3 m/s wind). Three exceed the existing 6 m/s vertical descent target; the windy case is below that vertical target but exceeds 6 m/s total ground speed. The latter remains an extra diagnostic. Source Parquet hashes before and after read-only extraction are preserved in the compact record.
