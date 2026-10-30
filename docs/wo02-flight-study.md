# WO-02 flight validation and delivered-performance study

Status: numerical benchmark met on Mac CPU; physical/control/launch gates remain. The JAX core merged in [PR #2](https://github.com/kudratsingh/rocket-twin/pull/2).
Paired validation and this study are in [PR #3](https://github.com/kudratsingh/rocket-twin/pull/3).
Do not infer flight readiness or a frozen motor choice from a numerical comparison.

## Objectives retained

Maximize practical conventional flight performance within the no-HPR scope while
building a substantial custom platform and preserving serious PID-to-RL research.
Shared upper equipment, custom aft interfaces, structures, fins, motor supports,
gimbal and avionics integration remain engineering work. A motor with more nominal
impulse need not deliver more altitude after its mass, thrust history and drag.
The digital orbital launcher, G-FOLD and existing work-order sequence are unchanged.

## Reproduce

```
make setup-sim
make check smoke tiny benchmark
make flight-study
```

`configs/wo02.yaml` defines the study, `configs/sim-model.yaml` records unmeasured
sensor/actuator estimates, and the resolved vehicle YAML owns actual hardware,
geometry, recovery, mass and inertia. Every case retains source/code hashes,
explicit perturbations, a resolved vehicle snapshot and its run identity. Parquet
telemetry is generated locally; CI can use `--summary-only --json-report` without
storing large trajectories. The simulator is one pure JAX `step`, shared with the
batched path. No NumPy or frontend flight-physics twin is introduced.

## Actual configurations and source hypotheses

| Configuration | Source / installed numerical model | Added integration allowance beyond the base performance module |
|---|---|---|
| Starting G80 fixed performance | Historical 2007 G78-labelled G80 curve, 128.2 g / 128 mm; current G80-10T summary differs | Existing fixed mount, liner, retention and physical fins |
| G12 finned TVC trainer | Reformulated G12ST-P source, 150 g / 156 mm, plugged | Actual gimbal, servos, supports, links, thermal guard and larger fins; gimbal locked for reference validation |
| G54 fixed alternative | Native RSE t/f transcription, 198.2 g / 187 mm, 96.8 g depletion hypothesis | +10 g support reinforcement estimate; mount/liner extend forward; assembled motor hardware counted once |
| G33 fixed alternative | Native RSE t/f transcription, 197 g / 187 mm, 89 g depletion hypothesis | Same +10 g support estimate and longer installed envelope |
| G12 fixed alternative | Same G12 source; separate actual fixed-motor assembly | +8 g thermal barrier and 3 m usable guide; no gimbal/servo mass |

RSE conversions preserve t/f values and native loaded/depletion fields in a separate
study archive; they are not original byte-identical downloads or new accepted
certification files. Manufacturer/certificate propellant figures for G54/G33
(86.5/79.1 g) differ from RSE headers (96.8/89 g). A named depletion sensitivity
changes the numerical mass-loss hypothesis while retaining original files and
loaded mass; effective loaded/depletion/burnout masses are reported per case.
It does not reconcile the motor or establish certification correspondence.

G80 remains the starting reference, not a frozen purchase. G25W remains quarantined.
Earlier short-burn rejections are historical; no universal three-second gate is
reintroduced. Exact current motor/lot/case/closure/envelope/source/California and
club acceptance remain open. Prior stock observations are not a purchase release.

## Independent comparison and numerical scope

Benchmark each actual finned baseline against RocketPy 1.13.0 for apogee AGL and
time-to-apogee within 5%. Use the same physical inputs and source breakpoints,
standard tropospheric atmosphere at an assumed 850 m MSL site, constant standard
gravity, vertical usable guide, calm wind and zero guide friction. No altitude
or damping coefficient is fitted to achieve agreement. The reference assembles
its own motor and aerodynamic surfaces from part inputs and integrates its own
flight. Declared dry inertia is a common input, not independently validated inertia.

The JAX model uses quaternion/RK4 mechanics, impulse-based depletion, full parallel-
axis inertia with CG motion, surface normal forces and rotational surface velocity.
Guide departure is irreversible. Noise, bias, sample rates, range clipping,
barometer lag and servo delay/deadband/rate/position limits are present. The
4,096-environment CPU step uses this same mechanics path. Tiny uses 5 ms steps;
the full study uses 1 ms. Sensor timing is quantized to the physics clock.

A calm vertical match validates integration and assembled axial performance under
these assumptions. It does not establish accurate wind/attitude derivatives,
servo load authority or a controller. Small-angle subsonic aerodynamics are
estimates; flag free-flight powered alpha >15 degrees or Mach >0.8. Detailed
exhaust mass-flux/jet damping, gimballed mass motion, flutter, structure and heat
are not resolved. These limitations constrain later PID/RL and hardware release.

## Preliminary mechanical screens

The retained WO-01 guide screen uses constant loaded mass plus 50 g growth, 85%
thrust, Cd 0.8 and 0.5 N guide friction. It is a conservative screen distinct from
the variable-mass flight simulations. Growth is placed fully aft for static margin.

| Mode | Nominal loaded g | Conservative guide m/s | Growth-aft launch margin cal |
|---|---:|---:|---:|
| G80 performance | 472.03 | 20.90 | 1.321 |
| G12 finned TVC | 575.77 | 11.66 | 1.288 |
| G54 performance | 552.03 | 21.26 | 1.023 |
| G33 performance | 550.83 | 11.12 | 1.029 |
| G12 fixed, 3 m guide | 501.83 | 14.15 | 1.194 |

Performance departure target remains 15 m/s, TVC 10 m/s. Thus G33 on 1.5 m and
fixed G12 on 3 m are conditional alternatives, not accepted replacements merely
because they predict greater altitude. G54's margin is close to the preliminary
one-calibre floor with aft growth. No structural or fin-root proof is implied.
Longer guidance, controlled mass/CG or a new physical design may improve an option;
change the actual design and revalidate instead of lowering a failed threshold.

## Uncertainty, wind and recovery

Sensitivity cases combine 50 g aft growth, 85% thrust, 95% burn-time scale, 120%
drag and 0.5 N friction; an optimistic corner uses 115% thrust, 105% duration and
80% drag. These are engineering stress cases, not measured probability bounds or
motor certification tolerances. Near-160 N s candidates are not declared eligible
because a perturbed curve happens to fit a numerical gate. Preserve certification
and actual launch eligibility as independent decisions.

Wind cases use steady crosswind and bounded smooth gusts, with an explicit height
profile. Report guide speed, powered tilt/angle-of-attack, altitude and downrange;
no wind envelope is flight-qualified by this approximate open-loop study. The
reference 5% completion benchmark is calm; wind agreement is not assumed.

Recovery uses the specified 750 mm canopy, estimated Cd, apogee event, trigger lag
and inflation time. Full cases report whether impact was actually reached within
the horizon. Point-drag descent and inflation are not deployment or opening-load
qualification. Motor delay probes are separate no-canopy ballistic sensitivities;
only the exact offered delay/hardware can become a procurement configuration.
**G12ST-P is plugged and has no motor ejection or motor-recovery backup.**
Independent recovery and power isolation require WO-09/10 testing.

Finless TVC is not claimed validated by either finned comparison. Powered control,
abort authority and the unstable burnout-to-recovery transition remain explicit
WO-06/07/09/10/11 gates; an unpowered gimbal cannot stabilize the finless coast.
No PID/RL superiority claim or unsafe flight follows from this work order.

## Results and next decision

Final paired values, uncertainty/drift/timing, sensor-range findings and run IDs
are in [results](results.md), full Mac record `wo02-20261030T044930127544Z`, tiny `wo02-20261030T045326632046Z`
and steady-wind reference `wo02-wind-20261030T045434689213Z`. The 65-test suite and local benchmarks pass.
All five calm comparisons are within 0.004%; all 27 cases reach impact by 360 s.
The actual club/site/date, operating altitude ceiling and usable guide equipment
remain unresolved. Delivered altitude must be weighed against drift, guidance,
recovery, heat, structural loads, stock and eligibility before freezing hardware.

## Conditional direction after the study

Keep G80 as the starting reference; prioritize G54 as the near-160 N s upgrade
if exact source/hardware, stock, California/club evidence and aft-growth margin
can be closed. Fixed G12 is the calm-altitude leader but has guide/wind/heat/recovery
penalties. G33 also needs a departure redesign. Do not freeze hardware from these
figures alone. Preserve long-duration G12 TVC for PID-to-RL research, with measured
actuator authority and a qualified operating envelope still required.

The source comparison caught a duplicate-origin RASP import defect that suppressed
CTI reference mass depletion. Validated point arrays and explicit depletion tests
now close it; prior coarse passes are superseded. Code/input hashes are captured
before and checked after each run. A passing result always retains flight_ready=false.
