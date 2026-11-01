# Integrated 52-part G80: flight and reference check

The frozen **52-part integrated G80 candidate** passes the requested nominal calm RocketPy apogee/time comparison and all three modeled **15 m/s guide** checks. None landed within the 45 s modeled horizon, so recovery completion and impact outcomes remain unavailable. These are numerical checks of one unadopted package, not flight readiness or integrated structural/thermal qualification.

The exact candidate identity is `62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009`. Its [candidate record](../build/wo03-g80-integrated-candidate-v1/record.json), resolved source and export manifest agree on the identity; the [flight record](../build/wo03-g80-integrated-flight-v1/record.json) pins its inputs, case settings, output and source hashes. These results belong to the integrated package and do not replace or retroactively attach to the earlier [43-part mount-only flight](wo03-g80-candidate-flight.md).

All cases use the existing G80 source curve, 850 m elevation hypothesis, calm air, 1.5 m guide, 0.005 s step and 45 s horizon. The growth cases explicitly place the **full 50 g** point allowance at **1.212 m**; the nominal case has no added allowance. The existing shared WO-02 CLI does not set that station in its study scenarios, so this packet supplies it explicitly without modifying that CLI or baseline.

| Case | Thrust / time / drag scales | Rail friction | JAX apogee / time | Guide exit | Recovery by 45 s |
| --- | --- | ---: | ---: | ---: | --- |
| Nominal, no added growth | 1.00 / 1.00 / 1.00 | 0 N | 631.216 m / 10.395 s | 19.439 m/s | Incomplete |
| Full growth, low thrust / high drag | 0.85 / 0.95 / 1.20 | 0.5 N | 443.578 m / 9.080 s | 16.955 m/s | Incomplete |
| Full growth, high thrust | 1.15 / 1.05 / 1.00 | 0 N | 735.115 m / 11.060 s | 20.352 m/s | Incomplete |

RocketPy nominal gives **631.249 m at 10.39563 s**. The relative JAX differences are **0.00525%** in apogee and **0.00605%** in time, below the unchanged **5%** threshold. The reference uses the same physical inputs and shared dry inertia, and ends at apogee; this comparison does not independently verify hardware properties or recovery. The existing reference wrapper does not apply the growth, thrust/time and friction overrides, so the two sensitivity cases are JAX-only and have no claimed RocketPy pass. Guide geometry, site conditions and actual motor hardware remain unverified.

## Mass and static properties

The resolved candidate's loaded mass is **748.569 g**, CG **792.220 mm**, and CP **906.140 mm** from the nose; nominal static margin is **1.7261 calibres**. With the full 50 g at 1212 mm, loaded mass is **798.569 g**, CG **818.503 mm**, and margin **1.3278 calibres**. At modeled burnout with the same point growth, mass is **736.069 g**, CG **791.544 mm**, and margin **1.7363 calibres**. These are the stated growth point and source depletion model, not measured mass or an exhaustive uncertainty campaign.

The loaded full-growth body-axis inertia tensor, kg m², is:

```text
[[ 0.000897904707,  0.000190457711, -0.000182873511],
 [ 0.000190457711,  0.134566343817, -0.000000113906],
 [-0.000182873511, -0.000000113906,  0.134568299577]]
```

The record retains all loaded/burnout tensors and lateral CG. The 50 g allowance is distinct from physical parts and the candidate's estimated incremental-annulus adhesive budget.

## Time-aligned modeled loads

The saved telemetry retains thrust, dynamic pressure and Mach. Axial drag magnitude below is reconstructed from the existing simulator's powered `q × area × Cd × drag_scale` expression; it is not an independent aerodynamic model, a measured force or a spatial drag partition.

| Case | At sampled peak thrust: time / thrust / drag | At peak powered drag: time / thrust / drag |
| --- | --- | --- |
| Nominal | 0.040 s / 101.929 N / 0.0089 N | 1.445 s / 27.021 N / 19.751 N |
| Full growth, low thrust / high drag | 0.040 s / 86.397 N / 0.0066 N | 1.400 s / 20.568 N / 13.034 N |
| Full growth, high thrust | 0.040 s / 117.515 N / 0.0099 N | 1.495 s / 33.489 N / 25.264 N |

The high-case 117.515 N sampled peak uses a 5 ms grid and 1.05 time scale; the 117.53 N structural source peak is not numerically identical. These global forces do not determine the shell-only force or the motor pressure/momentum-transfer distribution.

## Execution and boundaries

One child completed in **6.346 s wall / 5.304 CPU s**, peak RSS **444,809,216 bytes**. One CPU/library thread was requested; OS affinity was not established. All recorded source and code hashes matched before/after. The parameterized flight harness preserves its old 43-part defaults, and the earlier as-run source snapshot and results were not overwritten. Executed script SHA-256 `f3cb85ad26ac65a4404970bf4833389d754f55b876af2cc0c47ec1072ec878b1`; configuration SHA-256 `348efb2f168a9359317785b407cb1b6e2067ca51bfb31a9d01560434cd268c21`; record SHA-256 `7ac231bf8ecca3d3ac2494bd91832017803a4fdb5c2a9606a55f4ab97817c7bb`. Black, Ruff and saved-result assertions passed. No FEA or thermal solve was run.

Actual bond load sharing and strength, installed fin/root/flutter, out-of-domain hot fit, an approved thermal method, recovery hardware and full deployment, as-built properties and all physical/flight release gates remain open. The candidate has not been adopted into the active vehicle.

Published [same-package evidence](../runs/wo03-g80-integrated-package-20261101T053840103311Z/record.json) retains exact CAD/mass/static/flight compact records and their hashes. Generated geometry and full telemetry remain local. The 52-part identity is a proposal; working vehicle and release status remain unchanged.

## Growth-station clarification

This packet specifies the 1.212 m growth station explicitly. The current active
vehicles also declare `airframe.length_m = 1.212`, so the existing simulator's
default growth-station fallback already agrees for these vehicles. Omitting the
case override is not evidence that these current vehicles used 1.200 m. No
shared flight-code correction or baseline rerun is justified by that omission
alone; the earlier records retain their original settings and source identities.
