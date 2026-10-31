# Condensed finite radiation and rejected ring-baffle geometry

The checked finite first-hit matrix now has a reusable, conservative radiation
operator for arbitrary supplied temperature groups. **The one R26 mm ring-baffle
candidate is rejected on nominal fit:** its foil and support pads intersect the
actual mount rails. Its optical result is preserved as an excluded-rail geometry
diagnostic. Neither this operator verification nor the optical result is a new
thermal transient or acceptance result.

## Executed evidence

- Algebra/mapping verification, no new rays:
  `runs/wo03-finite-thermal-20261031T030430877086Z/record.json`.
- Historical baffle optical/probe run, 4.5 million additional rays, one CPU,
  16.61 seconds, $0:
  `runs/wo03-finite-thermal-20261031T030547356589Z/record.json`.
- Actual-mount fit audit and rejection, no additional rays:
  `runs/wo03-finite-thermal-20261031T030801091027Z/record.json`.
  The current runner checks this fit before tracing and records rejection without
  running rays when the actual mount intersects the proposed parts.

The immutable source candidate is
`runs/wo03-multilayer-shield-20261031T022026246942Z/record.json`, resolved identity
`7aecfec03d1197a71be48a466b0530accf46b17a642382ef7ef484af6e6af531`, recorded CAD
revision `b3440d2b97dcaf525fc1f40c5cf224dda6d9e02fa7bedcb43d58f822a0793108`.
It is the fixed G54, preserved-bore, eight-foil candidate at the required
300°C / emissivity 0.9 / 35°C condition and `high_k_low_cp` corner. The baseline
matrix comes from the `fine_rays` level of
`runs/wo03-finite-radiation-20261031T025007289697Z/record.json`.
The preparer verifies candidate/part identities, historical source-snapshot
hashes, patch areas, raw first-hit counts and reproduction of the reciprocal
matrix. Every new run pins its own inputs and source snapshot.

## Exact radiosity condensation

Let `B` map each patch to exactly one supplied temperature group, `E=diag(eps)`,
`A` contain patch areas, and `F` be the checked reciprocal closed-enclosure view
factor matrix. With fixed geometry and emissivities:

`J = [I-(I-E)F]^-1 E B sigma T_group⁴`

`Q_into = -Bᵀ diag(A)(I-F) [I-(I-E)F]^-1 E B sigma T_group⁴`.

The inverse is eliminated once. For a reciprocal enclosure the resulting
signed matrix is a symmetric graph Laplacian with positive off-diagonal entries
and negative diagonal row sums. The implementation checks the original condensed
matrix and removes only floating-point asymmetry/row-sum noise. It introduces no
new geometric visibility or emissivity assumption. The saved matrix **includes
sigma**, so its units are **W/K⁴** and its sign convention is **net heat inward**.

The physical view-factor and radiosity references remain the primary sources in
[the finite-radiation method](wo03-finite-radiation.md):
[COMSOL's radiosity equations](https://doc.comsol.com/6.3/doc/com.comsol.help.heat/heat_ug_theory.07.052.html)
and [Argonne SAM equations 3.18–3.23](https://publications.anl.gov/anlpubs/2025/05/196116.pdf).
The condensation follows directly by linear elimination and summing patch heat
into its owning temperature group.

Interface in `src.analysis.finite_radiation`:

```python
operator = condense_radiosity(F, areas_m2, emissivities, patch_group_names)
group_ids = operator.node_names
C = operator.inward_operator_w_k4
Q_inward_w = operator.heat_rates(T_group_k)  # stable evaluation of C @ T**4
```

The group names may identify material nodes or distinct **physical surface**
groups. The latter permits a common-surface conduction/radiation solve; the
operator itself does not equate surface temperatures with material temperatures.
The baseline evidence exports both **41 material/reservoir groups** and
**314 separate surface groups**. Black fore/aft openings remain explicit fixed
reservoir groups; the prescribed case cylinder is another explicit reservoir.
Emissivity changes require rebuilding the operator.

Each NPZ contains `inward_operator_w_k4`, ordered `node_names`,
`patch_node_index`, `patch_radiosity_response_w_m2_k4`, the reciprocal `F`, areas
and emissivities. The accompanying patch JSON identifies all physical faces.

| Verification, 24 arbitrary group-temperature vectors from 280–650 K | Material groups | Separate surfaces |
| --- | ---: | ---: |
| Maximum difference from a full direct patch-radiosity solve | 2.15e-11 W | 1.09e-11 W |
| Maximum total energy residual including reservoirs | 8.09e-14 W | 6.31e-14 W |
| Exactly isothermal 350 K maximum heat | 0 W | 0 W |
| Maximum signed-matrix column sum magnitude | 1.48e-25 W/K⁴ | 5.66e-26 W/K⁴ |

These are algebraic checks of the already sampled/reconciled finite model.
They do not reduce geometry, material or boundary uncertainty. Independent direct
radiosity agreement is also checked at every baffle ray/refinement level.

## Diagnostic material mapping and the required transient boundary

`MaterialRadiationAdapter` validates the complete ODE node-name order and maps
the original source temperatures as:

- Mica inner cylinder → `motor_liner.cell_0`; any exposed outer cylinder → the
  last radial cell. A newly exposed finite mica end face requires an explicit
  radial temperature mapping and is rejected by the current mapper.
- Other material faces → their recorded part node.
- Motor cylinder → `motor_case_boundary`.
- Black axial openings → explicit `fore_end_reservoir` / `aft_end_reservoir`,
  with independently declared `ambient` or `case` temperature assumptions.

The source ODE order is all liner cells followed by `thermal.part_ids[1:]`.
The adapter declares every covered and excluded node: the baseline has 84 ODE
nodes without optical coverage. These include existing noncoaxial support
elements; their radiation is excluded, rather than unknown temperatures being
silently assigned zero or ambient. Missing/nonfinite temperatures and reordered
states are errors.

Its `rates(temperature_k, case_temperature_k=..., ambient_temperature_k=...)`
returns material heat, external net heat into materials and a conservative pair
ledger. **This material-temperature adapter is diagnostic only.** Replacing mixed
gap exchange with independently half-wall-resisted air conduction plus radiation
evaluated at material-node temperature would remove the original common surface
coupling. No such replacement transient is implemented or called by this runner.

A valid replacement must solve gas conduction and radiation at the **same unknown
physical surface temperatures**, behind their actual solid half-wall resistance.
Case-cylinder exchange must be counted once; direct contacts and lumped contacts
must stay in their original paths; the shell's external convection/radiation must
remain separate from its inner finite enclosure. The separate primary-agent
common-surface integration is the next engineering step, not an outcome of these
records.

## One fully specified baffle family and its fit rejection

The one evaluated geometry adds two foil annuli at each of four in-span rings:

- Exact source bore radius **15.8 mm**, unchanged; baffle outer radius **26 mm**.
- Contaminated foil thickness **20 µm**, emissivity **0.9** on all surfaces.
- Fore baffle occupies `[ring_front−0.270 mm, ring_front−0.250 mm]`; aft baffle
  occupies `[ring_aft+0.250 mm, ring_aft+0.270 mm]`.
- Existing segmented foil ends stay 0.500 mm from the ring faces, leaving a
  **0.230 mm nominal axial gap** to the proposed baffles. This is not a tolerance,
  warpage, installation or vibration pass.
- Each baffle has three 10° support sectors centered at 0°, 120°, 240°, radii
  25.0–25.5 mm. Their actual stack is ring / 20 µm epoxy / 210 µm mica /
  20 µm epoxy / foil, exactly filling the 0.250 mm stand-off.
- Supports use the existing normal `sector_pads` generator. Its eight-segment
  inscribed polygon gives 0.999920674 times circular-sector area; the mass/contact
  ledger matches that actual polygon geometry.

There are 32 new normal-generator parts: eight foil annuli, eight three-sector
mica compounds and sixteen three-sector adhesive compounds. All individual
solids are valid and their CAD volumes agree with the analytical polygon/annular
volumes. Nominal added mass is **0.604500 g**: 0.578642 g foil, about 0.023320 g
mica and 0.002538 g epoxy. The isolated study reserve is 0.750 g. This is an
estimated-density design ledger, not a measured mass or full-vehicle budget pass.

Individual part validity did not establish installed fit. The actual mount's
rails intrude inside the proposed R26 mm annulus. For the first front assembly:

| New part | Intersection with actual mount |
| --- | ---: |
| Foil baffle | 0.552493 mm³ of 26.788989 mm³ |
| Three mica sectors | 1.297864 mm³ of 1.388081 mm³ |
| Each adhesive sector compound | 0.123606 mm³ of 0.132198 mm³ |

The full fit audit is in the rejection record. **This candidate is not buildable
as specified and is not selected.** No second collar geometry or further rays
were run. The optical annular model deliberately excludes real angular pads and
rails, so its earlier result is preserved at exactly that evidence level. Real
sector pads are never represented as fictitious opaque full annular disks.

## Optical change and the new heat paths

The geometry probe reduces original-foil direct visibility of ring end faces,
but creates broad baffle-to-ring visibility:

| Geometry/ray level | Original foil → ring end faces | Original foil → baffles | Baffles → ring end faces |
| --- | ---: | ---: | ---: |
| Original finite model, 1.2 million rays | 3.077% | unavailable | unavailable |
| Baffles, 0.3 million rays | 0.530% | 2.965% | 49.877% |
| Baffles, 1.5 million rays | 0.526% | 3.144% | 49.871% |
| Independent 1.5 million-ray repeat | 0.516% | 3.323% | 49.807% |
| Refined 7.5 mm patches, 1.2 million rays | 0.476% | 3.186% | 49.790% |

The baffle fine-level original-foil → ring-end fraction has a conservative
individual 99% interval **0–1.171%**, compared with the original model's individual
99% interval **2.375–3.779%**. All baffle levels have zero escaping rays and
compatible exact simultaneous reciprocity intervals. Fine-level raw reciprocity
L1 discrepancy is 1.711% of total area before the explicitly reported matrix
reconciliation. These sampling results concern the stated annular geometry only.

The new baffles need their own energy balance. Their temperature histories are
unavailable. At the old run's recorded **27 s** snapshot, two explicit temperature
probes demonstrate why visibility reduction cannot be called a thermal pass:

| Assumed baffle temperature probe, cold missing ends | Net radiation into mount | Net radiation into all baffles | Effective baffle → ring radiation |
| --- | ---: | ---: | ---: |
| Set to recorded mount, 310.085 K | 2.131 W | +4.668 W | 0 W |
| Set to recorded original foil, 430.788 K | 14.670 W | −22.104 W | +12.538 W |

These are explicitly prescribed **probes**, not predicted baffle temperatures,
confidence bounds or thermal equilibria. Holding a baffle at the mount temperature
while it absorbs 4.668 W assumes an unstated heat sink unless that energy is
transferred into its support or accumulated. The effective pair decomposition
includes diffuse reflections through the condensed operator; it is not a new
direct-view-factor measurement.

Using the declared bulk properties, each three-sector bonded mica stack has
**0.009014 W/K** conductance, excluding unmeasured additional interface resistance.
The broad parallel 0.250 mm air gap has an estimated **0.213254 W/K per baffle**
using `k_air=0.04 W/(m K)` and actual face area minus support area. At the second
120.703 K temperature-difference probe, these eight paths would give 8.704 W
through supports and 205.923 W through the parallel air gaps. Those large
hypothetical powers are not actual transient loads: they show that assigning a
hot foil temperature to the new baffles without solving their common surfaces
and heat balance is untenable. Gas conductance cannot be discarded because the
direct optical view improved.

## Reproduction and state

```sh
.venv/bin/python scripts/wo03_finite_thermal.py --geometry baseline
.venv/bin/python scripts/wo03_finite_thermal.py --geometry ring_end_baffles
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m pytest -q tests/test_finite_thermal.py
```

The current baffle command records actual-mount fit failure and runs no new rays.
The historical optical record retains its immutable pre-fit-check source snapshot,
raw counts/matrices, new-part definitions, CAD volumes and temperature probes.
No material limits, emissivity, 300°C source, 35°C ambient or 45°C substrate screen
were relaxed. No active configuration, shared thermal RHS, paid run, physical
work, Git or UI change is included. `transient_integrated`,
`thermal_acceptance_available`, `active_adoption` and `flight_ready` remain false.
