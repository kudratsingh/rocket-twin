# Actual boundary-to-material mapping: incomplete before temperature solving

The fitting G54 `69df790e…` gas boundary is fully identified, but its thermal
connections are **not complete enough for a temperature solve or acceptance**.
All **1,785 actual CAD fluid faces** have unique material-side BRep-component
ownership and retain their original 1,127 radiation group IDs. Of those faces,
874 have explicit nominal recipe-based half-wall paths, two liner ends have
explicit radial-cell strip paths, nine are external openings, and three are
separately prescribed motor surfaces. **897 material faces remain unavailable**
for direct Robin assembly. Missing connections never become insulation.

Executed record:
`runs/wo03-surface-materials-20261031T045222607795Z/record.json`.
No temperatures, gas solution, radiation solution, parameter increase, material
limit change or active adoption was produced. The 300°C / ε0.9 / 35°C case and
45°C substrate screen remain unchanged.

## Exact inputs and delivered tables

The source is the selected fitting-baffle candidate
`runs/wo03-baffle-fit-20261031T035358211715Z/resolved-candidate.json`, candidate
identity `69df790ec9bcba1465be4fa9861a7ad5fbc467091cbf58f44dee069e56e00bac`.
Its actual placed STEP parts, including notches, seams, sector pads, channels and
unchanged source solids, are read through the hash-checked geometry manifest.
No generic CAD regeneration or annular replacement occurs here.

The boundary handoff is
`build/wo03-cad-radiation-fitting-baffle-fine-bounded-v1/gas-boundary-handoff.json`.
It pins CAD revision
`1193713d0f4a7ad8393a00a0a03e7aaa04e9aa9393d2034691ef7126ae3cdd3b`,
the actual void STEP, face inventory, surface groups and ray-boundary files.
The void volume is 475,607.907582 mm³. Every geometry input remains unchanged
during this map. The handoff's historical gas-conduction code hash is reported
separately from the current hash: this mapping does not import or use that solver,
which another owner is developing. Geometry hashes are checked exactly.

The executed directory contains:

| Artifact | Meaning |
| --- | --- |
| `face-material-map.json` | One row per original one-based CAD fluid-face ID: part/material/profile, ancestry, actual component, radiation group, proposed bulk state or named reservoir, half-wall method, nominal/bounded k and h, or explicit unavailable reason |
| `group-material-map.json` | All original radiation groups and their face/component/state sets; no invented finer ray data |
| `component-state-proposals.json` | 339 included BRep-solid components, actual volume/centroid and homogeneous capacity-fraction proposals; source-state and sharing status |
| `connection-table.csv` | Compact quantitative face table; specialized liner strip paths and conditional sector geometry remain in the JSON |
| `record.json` | Input hashes, coverage/counts/areas, part summaries, symmetry tests, physical-feature proposals and blockers |

Original fluid-face IDs are preserved; source-face indices are zero-based as in
the handoff. Source material-side probes plus two new component probes at 10⁻⁵
and 10⁻⁶ mm into the material must identify exactly the same one component.
No face-center ownership or arbitrary material assignment at an edge is used.

| Boundary category | Faces | CAD area, mm² |
| --- | ---: | ---: |
| Nominal recipe-based finite half wall | 874 | 352,110.786633 |
| Unavailable half-wall map | 897 | 71,452.645686 |
| Liner ends with explicit FV strips | 2 | 74.895569 |
| Prescribed motor surfaces | 3 | 18,262.832078 |
| External openings | 9 | 6,839.603539 |

Face/group areas are checked without inventing unlisted boundaries. The actual
Boolean void has already removed buried source-source contacting faces. This
table introduces no gas or radiation through a liner/foil contact, glue layer,
buried pad interface or other solid contact.

## Common-surface connection method

The primary-selected model gives gas and solid the **same physical boundary
temperature** `Ts(x)`. A finite solid half wall connects that trace to its bulk
material state. Radiation enters that same trace. For a plane path,
`q'' = h(Tbulk − Ts)` with `h=k/δ`. For a cylindrical path,
`δ_eff = rs*abs(log(rs/rbulk))`, so `h=k/δ_eff`; multiplying by the actual face
area recovers the cylindrical resistance. These are solid conduction
coefficients, not a second gas-film coefficient. Fourier plane/cylinder
resistance follows [DOE-HDBK-1012/2-92, HT-02 conduction](https://www.energy.gov/documents/doe-hdbk-1012-92vol2).

All h values below are nominal modeling paths. They do not establish uniform
part temperature or bound a local hot spot. Physical wall thickness and its
normal direction come from the source recipe/actual geometry, rather than the
whole part bounding box. Actual CAD area is used; areas of removed contacts are
not reconstructed from an exposed face.

| Representative connection | Bulk state/path | Nominal h, W/(m² K) | Nominal G, W/K, if stated |
| --- | --- | ---: | ---: |
| Aft-shell inner surface, R32.5 mm | `aft_shell`, radial half wall of physical 0.5 mm paper tube; cylindrical effective δ=0.24810 mm | 483.6829 | 18.29413 over its nine exposed patches |
| Liner inner cylinder, R14.7 mm | `motor_liner.cell_0`, geometric FV centre; 16 radial cells through 0.4 mm mica | 36,030.6036 | 622.3151 over that cylinder |
| Each exposed liner annular end | Corresponding radial cell at each radial strip; axial δ=93.5 mm | 4.812834 | 0.000180230 per complete end |
| Original 20 µm foil outer cylinder | `motor_radiant_shield`, radial mid-wall path | 20,486,438.8 | — |
| Original foil's exposed annular ends | Same foil bulk state, axial δ=93.5 mm | 2,192.5134 | — |
| Fitting-baffle broad axial faces | Separate physical foil panel components; actual 20 µm axial thickness /2 | 20,500,000 | — |
| Fitting-baffle mica support circular sides | Separate pad components, actual R24.0–24.3 mm radial wall | 2,981.44–3,018.71 | — |
| Fitting-baffle 20 µm epoxy support circular sides | Separate bond components, same 0.3 mm radial width | 1,325.09–1,341.65 | — |
| Full bond 1 exposed annular ends | `mount_shell_bond_1`, actual 3 mm axial thickness /2 | 133.3333 | 0.0366415 over both ends |
| Example `shield_spacer_additional_shield_7_4_front` exposed axial faces | Distinct sector components, actual 1 mm axial thickness /2 | 900 | — |

The liner cylinder's G is distinct from the full liner-row sum, which also
includes its tiny end-path proposals. Very large thin-foil half-wall h values do
not represent a large gas-gap conductance: the gas-domain conduction still lies
in series at the unknown physical surface. These half walls must not be added
to a pre-existing material-node gas-gap resistance a second time.

## Liner ends retain radial states

The actual void exposes the liner's fore annulus, its inner cylinder and its aft
annulus. The outer cylinder touches the original foil and is absent from the
fluid boundary; the direct solid contact remains separate.

The existing FV construction uses equally spaced radial faces and geometric-mean
cell centres. On each end, strip `j` has actual area
`Aj=π(r[j+1]²−r[j]²)` and connects to **that same radial bulk cell j**. Each
JSON end row lists all 16 strip bounds, cell IDs, areas and individual
`Gj=k*Aj/δ`. No average material temperature, arbitrary single end-cell assignment
or single whole-end surface temperature is substituted.

The primary selected `δ=L/2=93.5 mm` as a coarse **one axial cell** hypothesis.
It is not a resolved end transient or an established conservative bound.
The explicit geometric-length sensitivity is:

| Axial half-path hypothesis | δ | Nominal G per end |
| --- | ---: | ---: |
| L/2, one-axial-cell baseline | 93.5 mm | 0.000180230 W/K |
| L/4, shorter axial/penetration hypothesis | 46.75 mm | 0.000360460 W/K |
| L/8, shorter axial/penetration hypothesis | 23.375 mm | 0.000720920 W/K |

Those alternatives were not solved. Changing the path length alone would alter
the model without corresponding axial heat capacities and states. Consistent
axial refinement and its effect are required before convergence/acceptance.
For gas assembly, a triangle crossing a radial FV boundary needs resolved
subfacets or boundary quadrature with the correct strip bulk ID at each
integration point. A mesh node is not assigned an invented material owner.

## Unavailable geometry and uncertainty

The following remain unavailable for direct solver loading; every affected row
has a named reason rather than h=0 or an insulation flag:

| Material region | Faces | Source geometry or next bounded mapping |
| --- | ---: | --- |
| Mount rings, rails, integral retainer blocks | 149 | Actual rings are 3 mm thick, rail stock 12×7 mm, block stock 12×12×20 mm before channels, trim and pockets. A face's local path and bulk/spreading state must be identified. Whole 210 mm mount length is not a half wall. |
| Fore retention plate/fingers | 33 | Physical plate is 9 mm, finger wall 2 mm, finger length 18 mm. The part's 18 mm geometry length cannot be used as every face thickness. |
| Aft retainer | 7 | Axial broad-face candidate δ=2 mm gives nominal h=125 W/(m² K); bore/OD/bolt-hole side spreading and separate face validation remain unavailable. |
| Actual G54 wood fin tabs | 15 | This source is the native plywood G54 fin set, **not** the trainer layered-fin study. Tab thickness is 6.35 mm, tab depth 6 mm, gusset base 3 mm. Exposed tab/gusset patches need directional paths and separate fin bulk states. |
| Purchased retention envelope | 15 | Three 3 mm shafts and 5.5 mm diameter ×3 mm heads are six BRep solids. Joining, exact material geometry and three physical hardware identities remain uncertain. |
| Baffle notch/seam edge faces | 144 | Actual edges/notches are preserved. No fictitious full annulus or 20 µm normal path through an in-plane edge is assigned. |
| Slotted mount-bond cut edges | 18 | Actual cut/channel shape and remaining epoxy coverage retained; no full-annulus replacement. |
| Radial-plane sides of sector pads/bonds | 516 | Normal thickness varies and is clipped by circular corners; requires resolved subregions/local solid conduction. |

At a sector-side point of radius r and half-angle α, the normal distance to the
sector bisector is `r*tan(α)`. That path remains inside the outer circle only
for `r<=Ro*cos(α)`. The JSON records this candidate formula, its valid interval,
sample distance and explicit outer-corner blocker. A centroid sample is not a
uniform face coefficient. The earlier provisional `r*sin(α)` expression was
corrected before freeze; no solver consumed it. Even a correct bisector path
would remain a lumped bulk-temperature approximation requiring validation.

For diagnosis, every material face has a first-exit **actual BRep normal chord**
sample. Interior points along the proposed chord must stay inside the same
source component. For the mount those samples range 1.8–210 mm; retention
2–20 mm; aft retainer 4–20 mm; fin tabs 6.35–100 mm; hardware 3–20 mm. These
large direction-dependent differences demonstrate why one bounding-box length
is unsuitable. Sample extrema are **not geometric bounds over each complete
face**, and half the sample chord is never silently accepted as a bulk path.

Material inputs are copied from existing engineering profiles and acceptance
sensitivities. Mica retains k=0.2–0.7 W/(m K), nominal 0.45. Epoxy retains the
existing 0.15–0.25 range, nominal 0.20. Other profiles retain the existing
0.7/1.3 coherent conductivity factors; aluminum nominal is 205, G11 0.25,
plywood 0.15 and paper 0.12 W/(m K). These are estimated sensitivity inputs,
not newly measured property confidence intervals. Exact material directions,
temperature dependence, adhesive coverage and process remain unknown.
Thickness/warping tolerances sufficient to bound these half-wall h values are
unavailable; the source's generic assembly linear tolerance cannot establish a
20 µm foil-thickness distribution. No invented lower thickness or zero missing
uncertainty is used to produce a finite thermal bound.

## Component, symmetry and radiation scope

**215 radiation groups contain multiple source BRep components.** One part name
or common plane/cylinder does not prove a connected or isothermal material body.
The table proposes separate component bulk states and provides homogeneous
volume fractions for preserving total heat capacity if primary adopts a split.
Those fractions do not decide thermal contact conductance or prove that touching
BRep solids are physically disconnected; the fastener shaft/head case is explicit.
Old lumped contact conductances must not be replicated once for every new state.

Three representative actual-part 120° rotation tests passed with **zero BRep
symmetric-difference volume**, at a declared 10⁻⁵ mm³ tolerance: `fin_set`,
`fitting_baffle_1_front`, and `fitting_baffle_1_front_mica_pads`. Their components
share a declared material profile. Full-domain geometry, all thermal boundary
inputs and independent manufacture equivalence were not proven symmetric.
No shared component temperature is therefore approved by this study.

The Robin implementation can retain shared gas nodes and attach separate h/bulk
connections per triangle. Facets may share an edge/corner without assigning the
shared node to one material; the assembled gas trace is continuous. Distinct
prescribed temperature IDs meeting at a node need the primary's consistent
physical-state definition; no corner priority is invented.

Radiation still has its original 1,127-group optical reduction. Gas can retain
full nodal temperatures, but `mean(T)^4` is not `mean(T^4)`. A true fourth-power
area integral/reconstruction or finer radiation grouping is required for an
explicit chosen coupling. Existing ray data do not magically provide finer
component/subface irradiation or radiosity. Groupwise uniform irradiation/
radiosity, load redistribution and resulting local error remain separate
approximations to document; the available mean temperature is not a hot-spot bound.

## Boundary and contact bookkeeping

The motor cylinder maps to
`prescribed_motor_case_surface_temperature_k`; its exact measured history remains
unavailable and the required exploratory source history is unchanged. The fore
and aft motor planes retain separate unresolved named physical temperatures.
The cylindrical envelope does not establish closure/nozzle/plume geometry or
make its end temperatures automatically equal to case temperature.

All three external openings may use the same explicit physical
`ambient_opening_gas_temperature_k` under the primary's ambient-gas hypothesis.
Each retains a separate named radiative brightness temperature. A hot radiative
environment does not automatically heat the prescribed gas boundary or vice
versa. No missing reservoir value falls back to 0 K, ambient or motor case.

Existing direct and lumped solid contacts remain separate. Their component
allocation, buried contact area, preload, bond coverage and contact resistance
are not derivable from an exposed gas face alone. The handoff's baffle ledger
is preserved: **0.053487243 W/K air and 0.002510387 W/K solid support per baffle**.
An actual gas-domain solve that includes those same 0.6 mm gaps replaces the old
air estimates; it must not add both. The source-bounded support route remains a
separate solid path, with real bond/mica/bond segments and uncertainties.

## Verification and stop condition

Reproduce with `.venv/bin/python scripts/wo03_surface_materials.py`.
The targeted fixture checks independent cylindrical resistance, exact radial-strip
area conservation and heat rates with distinct radial-cell temperatures, and
explicit-profile range precedence. Ruff, Black and one pytest fixture pass.
The actual ownership map, group coverage and selected BRep symmetry tests execute
on one CPU worker with $0 paid compute; inputs remain unchanged.

This task stops at the explicit mapping blockers. Primary owns material-state
selection, contact partitioning, Robin/radiation transfer, consistent axial
refinement and ODE integration. No material temperatures, 45°C passing claim,
complete-CAD conservative bound, physical qualification or flight release follows
from this table.
