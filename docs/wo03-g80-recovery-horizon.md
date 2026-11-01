# G80 candidate: completed modeled recovery horizon

**Outcome:** the three frozen 52-part G80 cases now reach the modeled ground
within a 180 s horizon. This closes their previously incomplete *simulation
horizon* only. Recovery strength, packing/extraction, electrical operation and
physical qualification remain open. The later keeper/bridge proposal is absent
from these trajectories and cannot inherit their results.

The unchanged candidate identity is
`62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009`.
Loaded nominal mass is 748.569 g; growth cases add the full separate 50 g at
station 1.212 m. Geometry, source motor curve, mass, atmosphere, aerodynamics,
controller behavior and recovery model are unchanged from the
[45 s comparison](wo03-g80-integrated-flight.md). Only the observation horizon
changes. The original incomplete records remain historical evidence.

| Calm-air case | Modeled maximum height | Guide departure speed | Electronic apogee trigger / full inflation | Modeled ground time | Speed immediately before ground | Horizontal landing distance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Nominal | 631.216 m | 19.439 m/s | 10.400 / 11.000 s | 114.980 s | 5.966 m/s | 6.786 m |
| Full growth, low thrust / high drag | 443.578 m | 16.955 m/s | 9.080 / 9.680 s | 80.500 s | 6.180 m/s | 8.065 m |
| Full growth, high thrust | 735.115 m | 20.352 m/s | 11.060 / 11.660 s | 128.370 s | 6.178 m/s | 9.939 m |

All values are preliminary calculations. All three leave the configured 1.5 m
usable guide above its unchanged 15 m/s requirement; real guide/site evidence
is unavailable. The nominal ascent retains its independent RocketPy apogee/time
comparison within 0.01%, below the existing 5% gates. RocketPy ends at apogee
and **does not independently validate these recovery trajectories**. No attitude,
landing-distance or recovery agreement is established by that ascent comparison.

The common-upper specification describes a preliminary **6 m/s descent screen**
for its 750 mm canopy under stated density/drag assumptions. The two growth
cases are above 6 m/s; do not present them as passing that preliminary target.
This study neither changes the target nor selects a different canopy. The
complete configuration must reconcile allowable descent/landing loads, canopy
area and drag uncertainty, packing mass/volume and opening shock. A new canopy
would need its own consistent source, geometry and affected checks.

## Scope and uncertainty

The existing Python/JAX simulator uses ideal electronic apogee detection,
configured delay and progressive inflation, with a lumped canopy drag model.
The preliminary electronic trigger has no measured sensor/firmware/barometric
port error, actual deployment reliability, canopy oscillation or flexible
harness/separation dynamics. These are unguided cases with zero steady wind
and zero gusts. Small modeled horizontal distances must not be used as range
or launch-site assurances. Off-nominal delayed deployment and no-deployment
loads remain separate required engineering cases. Physical independence of the
recovery circuit, installation, arming, cell retention, packing and proof tests
are not established by a landing flag.

## Execution, limits and evidence

The packet was declared before launch: three existing cases, one requested CPU,
180 s simulated horizon at the unchanged 0.005 s step, 120 CPU s total and
120 s wall, 2 GiB sampled memory guard, no automatic extension or retry.
It completed in 16.730 s supervised wall time and 17.004 s reaped-child CPU.
The flight process separately reports 16.099 s wall and 5.620 s self CPU;
its reaped helper/import work explains why that self figure is not the packet
CPU total. No OS affinity or guaranteed unsampled peak memory is claimed.
The original execution warns that Matplotlib used a temporary writable cache;
no dependency upgrade or model/source change was made.

[Recorded flight results](../runs/wo03-g80-recovery-horizon-20261101T071057368358Z/record.json),
[compact process record](../runs/wo03-g80-recovery-horizon-20261101T071057368358Z/execution-summary.json)
and the adjacent executed source/study retain the exact inputs and hashes.
All before/after source hashes match. Full Parquet trajectories remain in
`build/wo03-g80-integrated-recovery-horizon-v1/`; bulk telemetry is excluded
from publication. No active vehicle or preview geometry was changed. G54,
G12, aggregate WO-03 and every physical/paid/WO-10/flight gate remain separate.
