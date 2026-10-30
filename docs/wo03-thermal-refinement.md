# WO-03 opaque-wall thermal refinement

This is a recorded alternative model of the current, unchanged geometry. It does
not qualify materials or establish an exact motor-case temperature history.
Reproduce with `make thermal-study`. Source settings are
[wo03-thermal-topology.yaml](../configs/studies/wo03-thermal-topology.yaml) and the
existing engineering inputs; algorithms are `thermal_radial.py` and
`thermal_topology.py`. The initial lumped results remain historical evidence.

## Why this model was added

The initial network assigned a direct case-radiation approximation to many nearby
parts. That approximation can bypass the opaque liner and thermal guard and does
not form a consistent enclosure. It also treated the liner as one temperature.
The alternative resolves the liner radially and partitions actual annular geometry
by axial station. Only adjacent radial barriers exchange across each modeled gap;
frame rails are not converted into full-length opaque tubes. End rings, the pivot
ring, liner and aft shield use their actual specification stations. Other parts
remain single thermal capacities, with explicitly estimated contact paths.

For each radial cell, `C dT/dt = sum(Q)`. Cylindrical resistance is
`ln(ro/ri)/(2 pi k L)`; capacities sum to the adopted CAD mass times specific heat.
Half-wall conduction remains in series with each gas/radiation gap. Concentric
long-cylinder grey radiation includes the reciprocal inner/outer areas. Surface
temperatures are solved behind the half walls before applying `T^4` exchange.
Internal exchanges enter the two connected nodes with opposite sign. Only the
outer shell has direct ambient convection/radiation; upper-bay cooling and heat
from electronics are separately declared estimates.

Equation sources: [DOE heat-transfer handbook, HT-02 pp. 11–13](https://www.energy.gov/documents/doe-hdbk-1012-92vol2)
for cylindrical/composite conduction and [COMSOL radiation theory](https://doc.comsol.com/6.3/doc/com.comsol.help.heat/heat_ug_theory.07.053.html)
for visible-surface/view-factor treatment. This implementation uses its own stated
coaxial reduction, rather than claiming a COMSOL or full-geometry solution.

## Executed numerical evidence

Record: [`wo03-thermal-20261030T182422090687Z`](../runs/wo03-thermal-20261030T182422090687Z/record.json).
NumPy 2.4.6 / SciPy 1.17.1, implicit BDF on CPU; source inputs unchanged during the run.

- A separate logarithmic steady cylinder solution matches the 4/8/16-cell model:
  maximum temperature error below `2e-13 K`, heat-rate relative error below `9e-15`.
- A closed two-capacity transient matches its exponential analytical solution to
  `9.4e-9 K`; energy error is below `1e-12 J`.
- The actual four-configuration runs use 4/8/16 liner cells. The maximum final-two
  whole-history part-mean change is **0.110 K**, below the declared 0.2 K screen.
  Halving maximum time step from 2 s to 1 s changes recorded means by less than
  **1e-5 K**. Discretization checks do not validate topology or material inputs.
- Energy residuals, histories, raw asset hashes and exact configuration/CAD/part
  identities are recorded. SI part-mean fields pass the Analysis backend consumer.
  Radial liner histories remain separate from the part-mean overlay; no outer-face
  spatial gradient or measured temperature is fabricated.

## Upper-scenario calculated peaks

The exterior case is prescribed at 250 °C through source burnout, decaying with a
120 s time constant from a 35 °C ambient, with 300 s of post-burn observation.
These are exploratory boundaries, not published measurements of the offered motor.
Other low/high settings retain the declared property/contact/convection bounds.

| Configuration | Liner | Mount | Inner / outer gimbal | Aft shell | Fin bond |
|---|---:|---:|---:|---:|---:|
| G80 reference | 217.4 °C | 51.0 °C | N/A | 55.2 °C | 52.2 °C |
| G54 conditional | 219.3 °C | 55.7 °C | N/A | 63.7 °C | 59.0 °C |
| G12 finned | 224.9 °C | 88.1 °C | 72.1 / 63.7 °C | 59.0 °C | 56.6 °C |
| G12 finless | 224.9 °C | 88.6 °C | 72.6 / 64.3 °C | 60.3 °C | N/A |

The provisional screens remain 120 °C for the unspecified phenolic grade, 60 °C
for loaded printed ASA, and 45 °C for the bonded wood/paper/epoxy assemblies.
Several screens fail in every upper scenario. In the finned G12 case the aft guard
also reaches 85.3 °C, servo-envelope means about 47 °C and the flight-computer mean
49.3 °C. Exact component ratings, local hot spots and exposure limits remain open.
These numbers are calculated with estimated inputs; none is measured evidence.

The changed gimbal/mount predictions quantify sensitivity to model topology. They
are not evidence that the new temperatures are physically accurate. Both models
retain adverse conclusions and the earlier results have not been overwritten.

## Limits and required next verification

The coaxial long-cylinder approximation ignores finite-end view factors. Split
clamps, holes, drive lugs, rails, off-axis servos, deflected mechanisms, gas
circulation and nozzle/plume exposure require further treatment. Only the liner
resolves radial gradients. Contact, material properties and cooling paths are
estimates; prescribed case heating does not impose a finite motor heat inventory.
The result is not a universally conservative bound on every component hot spot.

The next design comparison must cover shielding/emissivity, liner/insulation
thickness and grade, radial space, mounting/load transfer and heat-soak time, with
mass and tolerance consequences. Actual case/liner/gimbal/bond temperatures need
later instrumented verification; hot coupons, adhesive cure/creep, loaded mechanism
and electronics checks remain owner-performed WO-09/10 gates. Until those model and
design issues are resolved, thermal acceptance and expanded WO-03 acceptance stay
false. No geometry, hardware, motor choice, purchase or flight is released here.
