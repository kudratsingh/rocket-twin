# G80 selected candidate: bounded flight/reference check

The 43-part G80 candidate passes the specified **nominal calm apogee/time comparison** to RocketPy within 5%, and all three simulated guide departures exceed the configured **15 m/s** target. These are modeled checks of the selected local candidate, not vehicle, recovery or flight qualification. None of the three trajectories landed within the 45 s horizon, so recovery completion and impact outcomes remain **unavailable**.

The [execution record](../build/wo03-g80-candidate-flight-v1/record.json) has all cases, full loaded and burnout mass/CG/inertia tensors, source hashes and powered samples; the three time histories are retained beside it as Parquet. The exact resolved candidate identity is `0a1ad4c196e7bbd046704199e99bad1f6649bc237c3c07b0e4f26118d4572c4b`. It includes the full 4.620 g incremental-annulus adhesive **upper budget**, which is not proof of actual bond occupancy. It is the same unadopted 32.2 mm fixed-mount candidate used in the [load-path](wo03-g80-mount-loadpath.md) and [axial-cut](wo03-g80-axial-cuts.md) work.

## Cases and results

All cases use the existing source G80 thrust curve, 850 m elevation hypothesis, zero wind/gust, 1.5 m configured guide, 0.005 s time step and 45 s horizon. Noise is disabled. The low/high cases each add the **full 50 g at 1.212 m**, as a point-mass sensitivity. This packet explicitly sets `added_mass_station_m`; the existing `scripts/wo02_sim.py` study scenarios omit it despite the 1.212 m value in `configs/wo02.yaml`. No existing CLI, baseline or source was changed.

| Case | Thrust / burn-time / drag scales | Rail friction | Apogee and time | Guide exit | Recovery by 45 s |
| --- | --- | ---: | ---: | ---: | --- |
| Nominal, no added growth | 1.00 / 1.00 / 1.00 | 0 N | 633.432 m / 10.395 s | 19.574 m/s | Incomplete |
| Full growth, low thrust / high drag | 0.85 / 0.95 / 1.20 | 0.5 N | 445.762 m / 9.085 s | 17.068 m/s | Incomplete |
| Full growth, high thrust | 1.15 / 1.05 / 1.00 | 0 N | 737.257 m / 11.055 s | 19.834 m/s | Incomplete |

The nominal independent RocketPy calculation gives **633.392 m at 10.395585 s**. Relative apogee and time differences are **0.00633%** and **0.00562%**, respectively, both within the existing **5%** gate. RocketPy used shared physical inputs and dry inertia; agreement is an integrator comparison, not proof of measured motor, mass, aerodynamics or hardware. Its comparison ends at apogee. Only nominal is compared: the existing `reference_flight` wrapper does not apply the growth, thrust/time or friction overrides, so the growth cases are JAX sensitivities without a claimed reference pass. The rail and site assumptions also remain unverified in the field.

## Candidate mass and static geometry

The existing mass core gives loaded candidate mass **743.8042 g**, CG **794.639 mm** from the nose and CP **906.140 mm**. The nominal modeled static margin is **1.6894 calibres**. Adding 50 g at 1212 mm gives **793.8042 g**, CG **820.927 mm**, loaded static margin **1.2911 calibres**; at modeled burnout it gives **731.3042 g**, CG **794.000 mm**, margin **1.6991 calibres**. These are specific point-growth and depletion results, not checks of every growth position, uncertain motor CG or manufactured mass.

The full loaded growth-case body-axis inertia tensor, kg m², is:

```text
[[ 0.000893598398,  0.000190496156, -0.000034516968],
 [ 0.000190496156,  0.133772809482, -0.000000106158],
 [-0.000034516968, -0.000000106158,  0.133777805700]]
```

All other loaded and burnout tensors, including lateral CG, are in the record. The 50 g is separate from physical parts and the 4.620 g candidate budget.

## Time-aligned powered loads

The saved telemetry supplies thrust, Mach and dynamic pressure. The axial drag magnitudes below reconstruct the **existing simulator's** `q × area × Cd × drag_scale` expression at each sample; they are not a new aerodynamic method, a physical drag measurement or a spatial force partition.

| Case | At sampled peak thrust: time, thrust, drag | At peak powered axial drag: time, thrust, drag |
| --- | --- | --- |
| Nominal | 0.040 s, 101.929 N, 0.009 N | 1.440 s, 27.514 N, 19.999 N |
| Full growth, low thrust / high drag | 0.040 s, 86.397 N, 0.007 N | 1.395 s, 21.008 N, 13.197 N |
| Full growth, high thrust | 0.040 s, 117.515 N, 0.010 N | 1.495 s, 33.489 N, 25.555 N |

The high-case **117.515 N** is sampled at 5 ms with the 1.05 time scale; the existing structural screen's **117.53 N** is the source peak multiplied by 1.15. They are aligned in intent but are not asserted to be numerically identical. These global trajectory samples do not determine where drag acts, how thrust enters the motor case, or how much load flows through any shell cut.

## Execution and boundaries

The single bounded child completed in **20.073 s wall / 4.649 CPU s**, with **419,397,632 bytes peak RSS**. One CPU/library thread was requested; no OS-affinity claim is made. Candidate, motor, model and code input hashes were unchanged; script SHA-256 is `bddd92af57f7096b367a8cf86f6ee3013ba3a639e36cf6038aaac39f5ed00a08` and record SHA-256 is `5e1199682a4289a2b0a42f9aafecb038579634766c7949d057ca4f5eef3e43f1`. Black and Ruff pass, and saved settings, nominal reference gate, guide results, incomplete recovery and source hashes were checked. No new physics, thermal or FEA run occurred.

The fitted mount's out-of-domain hot sensitivity, actual bond coverage and load sharing, structural retention, fin root/flutter, complete recovery, material qualification, as-built motor/guide and physical/flight gates remain open. No active design was adopted.

## Published evidence

The [candidate-check packet](../runs/wo03-g80-candidate-checks-20261101T053200Z/record.json) retains the exact compact records and their source hashes, including the stopped fit input attempt. Generated CAD, resolved copies and full telemetry remain local; their hashes and reproduction sources are recorded. This is evidence for the separate candidate, not adoption or complete WO-03 acceptance.

## Growth-station clarification

This packet specifies the 1.212 m growth station explicitly. The current active
vehicles also declare `airframe.length_m = 1.212`, so the existing simulator's
default growth-station fallback already agrees for these vehicles. Omitting the
case override is not evidence that these current vehicles used 1.200 m. No
shared flight-code correction or baseline rerun is justified by that omission
alone; the earlier records retain their original settings and source identities.
