# G80 fin-load intake from saved 180 s flight telemetry

**Result: identity-checked, read-only diagnostic only.** This is a scalar panel
load estimate calculated from `q(t)` and `alpha(t)` in the saved 52-part G80
flight Parquets. It is **not** a simulator-recorded per-fin force, a validated
aerodynamic model, an installed-root analysis, or a validated load bound. No
flight, CAD or structural solver ran for this packet, and no DF3 multiplier is
applied.

The candidate is `62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009`
(52 parts). The extractor revalidated all **24** candidate provenance hashes
and **44** 180 s flight provenance hashes against the preserved files; each
record's before/after source-hash maps match. The recovery-horizon config is
`180.0 s` with `5 ms` samples, and the three Parquets contain **36,000 rows
each**. The producer flight record does not store Parquet output digests. The
SHA-256 values below were computed by this extractor and included in its own
direct-input snapshot before and after the reads:

| Case | Extractor Parquet SHA-256 | Peak speed |
|---|---|---:|
| `nominal_calm` | `f8d273130037be286c3bf1348da6fc5f45a76cf4370bf908898088784b04feaa` | 147.925 m/s |
| `growth_low_thrust_high_drag` | `3410dbbe3c72ffa850e1b8785a39e4247fbd06b9e6e7183a3c69e0574adb668a` | 111.667 m/s |
| `growth_high_thrust` | `c560845ca11bec0a4728e92a39f7b77596346b22294cf7890e3e72558dae47d3` | 165.903 m/s |

The maximum saved case speed, **165.903 m/s**, is a candidate-specific input
for a later flutter screen; it is not a flight envelope or flutter pass.

## Method and event boundaries

The script reuses `normal_force_coefficient_per_radian` from
[`fin_attachment.py`](../src/analysis/fin_attachment.py) and `planform_geometry`
from [`fin_design.py`](../src/analysis/fin_design.py). For the resolved fin it
gets planform area **0.0084 m² per fin**, span **0.070 m**, and slope
`CNa=1.698653753 rad⁻¹`. For every non-landed sample it calculates:

```text
CN(t) = min(CNa × abs(alpha(t)), 2)
Fnormal(t) per fin = q(t) × CN(t) × area per fin
|Mroot(t)| per fin = Fnormal(t) × span/2
```

This uses a uniform normal-pressure distribution and places the resultant at
half-span. The CAD fin plane is XZ with normal −Y before the three 120° sector
rotations. With local X radial/outward and Y tangential/fin-normal, a positive
`+Y` force on the first `+X` fin gives `rX × FY = +MZ`: an **axial root
torque**, not a radial-X rail-bending moment. Because the calculation uses
`abs(alpha)`, it reports resultant and moment magnitude; it does not reconstruct
the physical load sign. Each per-fin result is not multiplied by three.

The saved 180 s flight record supplies `electronic_apogee_trigger_s` and
`inflation_complete_s` directly. The candidate trigger lag is 0.3 s and canopy
inflation duration is 0.3 s. The canopy-opening/inflation interval is trigger +
0.3 s through the recorded inflation-complete time. The three reported phases
are powered predeployment, coast predeployment, and postdeployment; the latter
includes the 0.3 s inflation ramp and subsequent descent. The Parquet contains
no explicit deployment state, so these event times come from the saved flight
record and candidate recovery timing. They are cross-checked against the
telemetry down-coordinate minimum. Landed samples are excluded.

A **10° absolute-alpha cutoff** is used only to report how many samples lie
outside a provisional small-angle diagnostic band. It is not claimed as a
validated method domain or a changed requirement. At large alpha, especially
during descent, this scalar estimate is out of its intended small-angle scope.

## Results by saved case

The following entries are maxima of the scalar estimate within each phase.
Numbers are per fin; moments use the 35 mm half-span arm. Postdeployment
maxima occur at alpha near 90° and are outside the diagnostic band, so they
must not be interpreted as meaningful aerodynamic loads.

| Case | Powered predeployment: force / moment / max angle | Coast predeployment: force / moment / max angle | Postdeployment: force / moment / max angle | Landed samples excluded |
|---|---:|---:|---:|---:|
| Nominal calm | 0.512 N / 0.0179 N·m / 0.791° | 0.0897 N / 0.00314 N·m / 90.0° | 0.337 N / 0.0118 N·m / 90.0° | 13,005 |
| Low thrust, high drag + 50 g | 0.502 N / 0.0176 N·m / 0.884° | 0.0894 N / 0.00313 N·m / 90.0° | 0.362 N / 0.0127 N·m / 90.0° | 19,901 |
| High thrust + 50 g | 0.698 N / 0.0244 N·m / 0.871° | 0.0920 N / 0.00322 N·m / 90.0° | 0.362 N / 0.0127 N·m / 90.0° | 10,327 |

All samples in each powered predeployment phase are within 10°. Coast
predeployment contains respectively **137, 139 and 147** samples above 10°;
postdeployment contains **20,856, 14,224 and 23,402** samples above 10°.
Across all non-landed samples, maximum absolute alpha is approximately 90° in
each case. This indicates the limits of the linear panel estimate in the
recorded coast/descent orientations, not a validated fin load.

The separately reported `qmax × CN=2` sensitivities are **not coincident
physical maxima** and not validated bounds:

| Case | qmax and time | alpha at qmax | Assumed force / root-moment magnitude per fin |
|---|---:|---:|---:|
| Nominal calm | 12,198.55 Pa at 1.445 s | 0.00648° | 204.94 N / 7.173 N·m |
| Low thrust, high drag + 50 g | 6,973.24 Pa at 1.400 s | 0.00590° | 117.15 N / 4.100 N·m |
| High thrust + 50 g | 15,315.27 Pa at 1.495 s | 0.00071° | 257.30 N / 9.005 N·m |

The `CN=2` value is imposed independently at the time of qmax; the recorded
alpha at those qmax samples is near zero. It is therefore a deliberately
separate sensitivity, not a simultaneous recorded load. Do not use it as an
operational maximum.

The original **40 kPa / 5°** panel design case reproduces **49.807129 N per
fin** and **1.74325 N·m** using the same formula. This is an arithmetic check
against the historical panel case, not a validation of the coefficient or
attachment.

## Provenance and run record

The executed compact output is
[`results.json`](../build/wo03-g80-fin-loads-v3/results.json), with the exact
executed script and config alongside it. The upstream candidate record is
[`build/wo03-g80-integrated-candidate-v1/record.json`](../build/wo03-g80-integrated-candidate-v1/record.json);
the flight and three source Parquets are in
[`build/wo03-g80-integrated-recovery-horizon-v1`](../build/wo03-g80-integrated-recovery-horizon-v1/record.json).
Candidate and flight input hashes were checked against the current saved
bytes, and direct input hashes were unchanged before/after this read. The
successful v3 processing interval was **0.244 s after module import**; total
self CPU was **0.4555 s** and peak RSS was **158,482,432 bytes**. The v3
`RUSAGE_CHILDREN` sample is zero because the extractor spawned no child. The
preserved v2 45 s extraction records 0.213 s processing interval and 0.4255 s
self CPU. The v1 path-failure record has 0.150 s elapsed but did not capture
CPU usage; therefore cumulative campaign CPU is **unavailable**, rather than
zero. The recorded processing intervals sum to 0.607 s, excluding module
startup. One-thread environment variables and a 10 CPU s / 20 wall s process
cap were set; OS CPU affinity was not claimed. PyArrow printed denied cache
and capability `sysctlbyname` diagnostics, but all three 180 s tables were
read, and the extraction's direct input digests were unchanged before/after
the read. The flight producer source hashes verify producer inputs; they do
not establish historical producer Parquet digests.

One earlier path-resolution attempt is preserved at
`build/wo03-g80-fin-loads-v1/failure.json`. A 45 s telemetry extraction is
preserved at `build/wo03-g80-fin-loads-v2`; its scalar results are a valid
short-horizon diagnostic for the older 45 s trajectory, but it is superseded
for this request because it does not cover the requested 180 s recovery phases.
The final v3 packet uses the saved 180 s record and Parquets. The path fix and
180 s source selection were input/harness corrections only; no physical model
was changed and the 10 CPU s / 20 wall s caps were not increased. The current
script has since received formatting-only changes; its AST matches the exact
as-run source in the v3 output directory, and that preserved copy remains the
execution provenance. The final source passed focused Ruff lint and formatting
checks. Black itself was unavailable in this environment, so no Black command
was run.

The recorded three-case peaks, loads and source identities support only a
candidate-specific diagnostic for choosing a later installed-root analysis
input. They do not qualify fin strength, deflection, attachment, flutter or
flight readiness.

The primary subsequently ran the installed Black module and Ruff on the source. Its AST still matches the preserved executed extractor; formatting and comments do not change the recorded arithmetic. Because v1 CPU was not recorded, cumulative CPU compliance for the multi-attempt intake is unavailable despite the short reported worker times and per-process caps. No further extraction is selected.

[Compact publication packet](../runs/wo03-g80-fin-load-intake-20261101T073101522036Z/record.json) retains all three input/extraction records and their as-run sources. Native flight telemetry remains local.
