# Finite shield ends and ring-window radiation diagnostic

The segmented eight-foil G54 candidate's **0.251 K shell reserve is not supported
by a conservative radiation-geometry model**. Finite opaque rays expose a mount
heating path that the independent axial-band approximation omits. This diagnostic
does not recalculate temperatures and does not establish that the actual shell
passes or fails. WO-03 thermal acceptance remains open.

At the source run's recorded 27 s material temperatures, the finite model gives
**6.550 W net radiation into the mount**, compared with **1.368 W** from the
long-cylinder band model evaluated at the same temperatures. Cold black end
reservoirs are used for this comparison. Repeating the rays gives 6.566 W;
halving the maximum axial patch length gives 6.513 W. The roughly 5.2 W difference
is much larger than those sampling/discretization changes. It is an instantaneous
radiation difference, not an added constant heat source or a predicted temperature
increase.

## Identity and reproducibility

Executed record:
`runs/wo03-finite-radiation-20261031T025007289697Z/record.json`.
The run uses 4,360,000 first-hit rays including its known cases, one CPU worker,
4,096-ray chunks, 6.60 s elapsed and $0 paid compute. Raw/reconciled view-factor
matrices, counts and hits are archived as NPZ files, with an explicit JSON patch
inventory at every level. Its immutable source snapshot contains the old record,
resolved candidate, old temperature histories and diagnostic sources.

Source transient:
`runs/wo03-multilayer-shield-20261031T022026246942Z/record.json`, candidate
`eight_total_foils_wide`, G54, preserved ring bores, three 10-degree spacer pads,
required combined 300°C case / emissivity 0.9 / 35°C ambient,
`high_k_low_cp` material corner.

- Resolved candidate identity:
  `7aecfec03d1197a71be48a466b0530accf46b17a642382ef7ef484af6e6af531`.
- Recorded CAD revision:
  `b3440d2b97dcaf525fc1f40c5cf224dda6d9e02fa7bedcb43d58f822a0793108`.
- The runner verifies the candidate identity, every recorded part-shape identity,
  and every old source-snapshot hash, then records hashes of the generated input
  candidate/history files as well. It checks that its inputs stay unchanged.
- The original result is a calculated shell peak of 44.748953°C at 92 s against
  the unchanged 45°C substrate screen. It is not a measured motor or shell history.

Run from the repository root with the existing environment:

```sh
.venv/bin/python scripts/wo03_finite_radiation.py --preset tiny
.venv/bin/python scripts/wo03_finite_radiation.py --preset sim
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m pytest -q tests/test_finite_radiation.py
```

The `tiny` preset is a smoke diagnostic. The `sim` preset executes the ray and
patch refinements below and enforces a 4.8 million-ray cap. Generated run assets
remain ignored. No active spec or shared transient RHS is changed.

## Geometry and surfaces

The diagnostic covers **1.013–1.200 m**, exactly the source liner interval. It
uses the recorded motor case cylinder, mica sleeve, original foil, all 30 finite
added foil segments, four in-span mount rings, their adhesive annuli and the
inner shell. Ring positions, individual thicknesses/bores, foil thicknesses,
segment starts/ends and the 0.68 mm mount-to-shell bond gap come from that resolved
candidate. Each annular solid has inner/outer cylinders and finite annular end
faces. Solid overlap is rejected. Contacting mica/foil and mount/bond/shell faces
are removed from the radiating enclosure; no radiation passes through a solid.

The added segments stop 0.5 mm before and resume 0.5 mm after each 3 mm ring,
leaving aligned **4 mm windows**. The first two added layers continue to 1.200 m;
the five outer layers end at 1.1765 m ahead of retention. These finite boundaries
let rays cross axial bands and strike ring end faces or other foil segments.

All material surfaces have contaminated-case emissivity **0.9**, including both
sides of every added foil. The motor cylinder follows the existing prescribed
external-case profile, not an invented measurement. Other surfaces use the
recorded material-node temperatures; the mica inner cylinder uses the recorded
innermost radial cell. There is no radiating cylindrical gap between contacting
mica and original foil. The inner shell is an explicit receiving/radiating
surface; it is not replaced by an ambient sink.

The first mount ring, forward thrust structure, actual commercial motor end
geometry/nozzle, aft retainer and upper bay lie outside this truncated enclosure.
Every free annular area at either axial end is an **explicit black boundary**.
Two sensitivity cases assign those boundary radiosities the recorded ambient
temperature or the source's prescribed case temperature at the same time. This
is a stated missing-boundary assumption. It does not establish bounds on actual
nozzle/plume radiation or replace the absent end-geometry model.

The annular representation fills angular fin slots/notches and excludes sparse
rails, sector spacer pads, foil seams/wrinkles and retention blocks/fasteners.
Their omission can change both occlusion and radiation into structure. Therefore
the result is neither an upper nor a lower bound for complete 3D CAD. It does
test the finite-end defect in the same coaxial reduction as the current model.
No TVC motion, angular ray tracing or CFD result is claimed.

## Equations and verification

For an opaque diffuse surface, uniform area points and directions with density
`cos(theta)/pi` estimate the view-factor integral by first-hit fractions:

`F_ij = (1/A_i) integral_i integral_j V cos(theta_i) cos(theta_j)/(pi*s²) dA_j dA_i`.

Analytic cylinder/plane intersections terminate each ray at the nearest opaque
surface. Rotational symmetry permits source azimuth zero while retaining both
transverse direction components. Rays are not bent to enforce a desired target,
continued through walls, or reflected during geometric counting. Multiple diffuse
reflections are included by solving the radiosity equations afterward:

`J = eps*sigma*T⁴ + (1-eps)*F*J`, `Q_out,i = A_i*(J_i - sum_j F_ij*J_j)`.

The physical identities are `sum_j F_ij=1` and `A_i*F_ij=A_j*F_ji`. Independent
Monte Carlo estimates obey closure exactly when every ray hits a boundary, while
reciprocity has sampling error. The run retains the raw matrix and tests
reciprocal exchange-area intervals using exact binomial Clopper–Pearson intervals
with a union bound over all directed pairs, providing 99% simultaneous coverage.
Zero observed reverse hits do not imply zero uncertainty. All levels have zero
escaping rays and mutually compatible reciprocal intervals.

For the radiosity solve, the mean reciprocal exchange-area matrix is adjusted
by symmetric diagonal equilibration to recover exact row areas. This explicit
sampling reconciliation introduces no new visible pair. At the fine level the
raw exchange-area L1 reciprocity residual is 2.007% of total area; the largest row
L1 adjustment is 0.160 (largely sensitive small-area patches). The reconciled
maximum row-sum error is below 1e-12 and reciprocity error is 2.17e-19 m². These
are algebraic properties of the reconciled matrix, not evidence of exact geometry.
At 27 s with cold ends, using the **unreconciled** matrix gives 6.602 W into the
mount, versus 6.550 W reconciled. Its unbalanced total heat residual is -0.114 W.
The independent-repeat raw result is 6.568 W and the patch-refined raw result is
6.506 W. The omitted mount path does not depend on enforcing reciprocity.

Known cases executed in the run:

| Independent check | Result |
| --- | --- |
| Equal coaxial disks, separation/radius = 1 | Analytic `(3-sqrt(5))/2 = 0.381966`; sampled 0.378397, inside the conservative 99.9% interval 0.364618–0.392177 |
| Closed cavity at uniform 350 K with unequal emissivities | Maximum absolute patch heat 8.38e-10 W |
| Closed nonuniform cavity | Total heat residual magnitude 1.35e-9 W |
| Concentric cylinders, length/outer radius = 500 | Raw inner-to-outer 0.999173; outer-to-inner 0.494001 versus infinite limits 1 and 0.5; reconciled heat differs from the infinite-cylinder solution by 0.0060% |

The final rocket snapshots conserve radiative energy, including the black end
reservoirs, to less than 3e-12 W. This verifies the stated radiation reduction and
its implementation; it is not a heat-soak or hardware validation.

Equation/reference sources:

- [Hamilton and Morgan, NACA TN 2836 (1952)](https://ntrs.nasa.gov/citations/19930083529),
  configuration factors for finite opaque surfaces, equal/opposed coaxial disks
  and concentric-cylinder enclosures, configurations A-5 and A-7/A-8.
- [COMSOL 6.3, View Factor Evaluation](https://doc.comsol.com/6.3/doc/com.comsol.help.heat/heat_ug_theory.07.053.html)
  and [Radiosity Method](https://doc.comsol.com/6.3/doc/com.comsol.help.heat/heat_ug_theory.07.052.html),
  diffuse visibility integral and radiosity/irradiation balance.
- [Argonne SAM theory manual (2025)](https://publications.anl.gov/anlpubs/2025/05/196116.pdf),
  equations 3.18–3.23: reciprocity, closure, net exchange and the infinite-cylinder
  two-surface reference.

## Quantitative finite-geometry finding

The raw first-hit view factor from the original foil's outer cylinder to mount
**end faces** is **3.077%**, with a conservative 99% sampling interval of
**2.375–3.779%**. The current bands include only radial cylindrical exchange and
assign this end-face route no radiation path. About 9.42% of original-foil rays
reach any mount surface. Direct first-hit values to shell, nonadjacent added
foils and missing ends are 0.175%, 0.424% and 1.369%, respectively. Their individual
99% Hoeffding intervals are in the record and are comparatively wide; small
fractions are not treated as accurately resolved zeros.

| Ray/patch level | Rays | Patches | Original foil → ring end faces | Mount incoming radiation at 27 s, cold ends |
| --- | ---: | ---: | ---: | ---: |
| Coarse rays | 200,000 | 314 | 3.025% | 6.495 W |
| Medium rays | 600,000 | 314 | 3.077% | 6.571 W |
| Fine rays, maximum axial patch 15 mm | 1,200,000 | 314 | 3.077% | 6.550 W |
| Independent fine repeat | 1,200,000 | 314 | 2.989% | 6.566 W |
| Maximum axial patch 7.5 mm | 1,000,000 | 490 | 3.039% | 6.513 W |

The fine-to-repeat change in mount radiation is 0.016 W (0.24%); fine-to-patch
refinement is 0.038 W (0.57%). These are observed numerical changes, not a formal
confidence bound on net power. The raw view-factor intervals quantify ray
sampling only. There is no confidence interval for the actual rocket temperature.

Each table value below holds the **same recorded material-node temperatures**
fixed, sets all material emissivities to 0.9, and compares radiation alone.
Gas conduction, contact conduction and the transient are not altered or added to
these values. The band comparison analytically evaluates its existing
long-cylinder radiation formula at those same nodes. The record also separately
provides the old solver's radiation reconstructed behind its half-wall
resistances; that is a different surface-temperature comparison.

| Recorded time | Band → mount | Finite → mount, cold/hot missing ends | Band → shell | Finite → shell, cold/hot missing ends |
| --- | ---: | ---: | ---: | ---: |
| 11 s | 1.087 W | 3.537 / 7.240 W | 2.175 W | 1.194 / 10.835 W |
| 27 s | 1.368 W | 6.550 / 9.416 W | 5.573 W | 3.830 / 11.292 W |
| 60 s | 1.118 W | 6.506 / 8.259 W | 6.239 W | 4.460 / 9.026 W |
| 92 s, old shell-peak time | 0.783 W | 4.785 / 5.922 W | 4.905 W | 3.535 / 6.494 W |

At 27 s the original foil alone transfers about **0.737 W** net to ring end
faces in the cold-end case; the rest of the mount increase includes the warm
added foil segments seeing those faces. Thus adding more segmented foil layers
without treating their ends can redirect heat into the ring supports. With cold
ends, the bands overstate instantaneous shell radiation while understating mount
radiation. With hot ends, both mount and shell are understated. A low algebraic
energy residual in the old transient does not make its geometry conservative.

## Correction direction and remaining gate

The next isolated candidate should shield the warm segment ends from the mount
ring faces using explicit, thermally isolated opaque collars/overlapping end
baffles, while retaining the structural ring bores. Its complete solids, spacer
contacts, foil aging assumptions, installation/motion clearance and mass must be
reconciled. Increasing layer count alone is not supported by this finding.
Finite surface-to-surface radiation must then be coupled back to conduction and
the transient over the full acceptance matrix, including missing end structure
and an angular treatment of rails/slots/spacers. No such corrected candidate or
transient has been completed by this diagnostic.

The 45°C screen, required 300°C/degraded-foil/35°C case, exact motor-history gap,
material/contact uncertainty, structural checks, G12 compatibility, physical
thermocouple/hot-soak/coupon tests and later release gates remain unchanged.
`thermal_acceptance_available: false`, `active_adoption: false`, and
`flight_ready: false` are explicit in every diagnostic record.
