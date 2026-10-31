# Failed coarse gas field: localized nonmonotone stencils and boundary resolution

The completed coarse gas operator remains **numerically failed and unaccepted**.
This read-only diagnosis locates its large undershoot/overshoot and shows that
the saved values satisfy the local discrete equations even while violating the
stated unforced temperature interval. Both gas and consistent Robin stencils
have positive offdiagonal coefficients at the offending nodes. A unique root
cause or the share due to conditioning versus discretization is **not proved**.
No factorization, mesher, heat solution, repair, clipping or parameter change is
performed here. The source study's `numerical_checks_pass=false` remains false.

Final packet:
`runs/wo03-gas-field-diagnostic-20261031T062755149138Z/record.json`.
The final read-only worker took **4.13 seconds supervised**; both diagnostic
captures and small artifact reads remain well below the 120-second one-CPU data-
analysis allowance. The earlier packet is retained at
`runs/wo03-gas-field-diagnostic-20261031T062222972537Z/`; the final packet adds
boundary midplane traces and the explicit hot-neighbor Robin terms, using the
same immutable inputs and no new field solve.

## Source, field and evidence gates

The source is the **completed observed** record
`build/wo03-actual-gas-observed/coarse-nominal/record.json`, its saved ten nodal
fields and reduced response maps. The mesh is the existing valid coarse PLC
export: 80,186 nodes /427,940 tetrahedra. It is the old optical-PLC gas mesh,
with the nominal material half-wall operator and required-hot probe air
conductivity **0.04 W/(m K)**. It is not the failed optimized medium mesh or a
new native-boundary mesh. All source hashes remain unchanged.

The selected probe prescribes motor surfaces at **573.15 K**, every material
bulk and gas opening at **308.15 K**, and zero surface Neumann input. It has no
radiation or solid transient feedback. The fore/cylinder/aft motor physical
temperature hypotheses were explicitly aliased in the source study, not measured.

| Gate | Status |
| --- | --- |
| Actual factor and saved probe completion | Complete in the separate source study |
| Coarse geometric mesh checks | Passed within their declared scope |
| Actual numerical field accuracy | **Failed; no credible temperature prediction** |
| Material/transient temperature acceptance | Unavailable; no acceptance follows |

## Extreme locations and local equations

The hot probe has 13,562 below-ambient nodes: **11,570 boundary and 1,992
interior**. One node exceeds the prescribed maximum. There are **194 surface
group means below ambient**, so the failure is not confined to isolated interior
values. Full group locations, coordinate bounds, source-face points and field
extrema are retained in `all-group-field-locations.json`; no material owner is
invented for shared boundary nodes.

| Quantity | Minimum node | Maximum node |
| --- | --- | --- |
| Zero-based node ID | 22602 | 79848 |
| Saved T | **181.615257 K** | **602.731406 K** |
| CAD X/Y/Z, mm | −4.566763 /11.635922 /1010.000000 | 13.596834 /−4.606460 /1012.994316 |
| Boundary status | Shared G11 retention face 858/group 467 and mica thrust-pad face 895/group 487 | Interior, no incident Robin boundary triangle |
| Region | Fore retention aft face /pad inner R12.5 mm edge | 5.684 µm ahead of the prescribed motor fore plane |
| Incident tetrahedra | 5 | 14 |
| Minimum incident scaled determinant | 0.0164354 | 0.00120473 |
| Maximum local edge-J condition number | 23.9332 | 376.2285 |

For each incident tet, the script recomputes only its geometric 3×3 Jacobian
inverse and `Ke=k*V*grad(N)·grad(N)`. It adds the existing preintegrated Robin
triangle rows with the saved original-facet vertex permutations. This is a
local coefficient/residual audit, not a new PDE factor or solve.

At the minimum, gas diagonal is 1.08273×10⁻⁴ W/K, with two positive offdiagonal
entries totalling 1.28836×10⁻⁵ W/K. The Robin diagonal is 1.78133×10⁻⁴ W/K,
with seven positive offdiagonals totalling the same amount. The combined row
has **three positive offdiagonals**, totalling 1.30947×10⁻⁴ W/K. The saved
temperature satisfies that local gas-plus-Robin row with recomputed residual
**0 W**, or −2.78×10⁻¹⁷ W after shifting every temperature by the common cold
bulk value.

Three neighboring nodes—23283/23284/23285—are fixed at 573.15 K and share the
pad-side/motor-fore groups **487/494**. Each contributes a **positive Robin
coefficient 4.39942×10⁻⁵ W/K** to the minimum's row. Their total hot-neighbor
term in the shifted equation is **0.0349754 W**. This is a concrete consistent-
Robin trace mechanism capable of supporting a below-ambient free-node value in
the discrete equations. It is not a new physical heat-load prediction.
Those side triangles use nominal h≈564.647 W/(m² K); the adjacent retention
triangles use h≈55.556 W/(m² K). They retain the source half-wall uncertainty.

At the interior maximum, there is **no wall term**. Its gas row nevertheless
has four positive offdiagonals totalling 1.36204×10⁻⁴ W/K, against diagonal
8.39647×10⁻⁴ W/K. Its recomputed residual is 1.67×10⁻¹⁶ W. Thus a Robin-only
explanation is insufficient: the volume stencil also lacks the sign pattern
that would guarantee a discrete maximum principle. Positive offdiagonals alone
are not proof of an implementation bug or a complete causal attribution.

## Negative response locations and the µW ledger issue

The saved mean reservoir-response matrix has a minimum **−0.297996 K/K**:
fin end group 3, on the Z1190 mm plane, responding to the ambient gas-opening
state. The next is **−0.296180 K/K** for epoxy mount-bond-4 end group 4 on
Z1180 mm, for the same opening input. These are computed response coefficients,
not invented physical zero-temperature cases.

The coldest group mean is the aft-retainer fore plane **group 505, Z1203 mm**:
305.216634 K, **2.933366 K below ambient**. Its hot-case column is
**−0.0110693043 K/K**. Applying the stored mean map reconstructs all saved hot
probe means within **1.27×10⁻⁹ K**, confirming the symptom is present in the
returned operator as well as its particular field.

The most negative mean positive-load response is **−19.02593 K/W**, target
mount plane group 100 from source mount plane group 101 (original faces
188/190, opposing normals). Full top-20 source/target physical families,
locations, bounds and units are retained separately for reservoir and positive-
load maps. The global nodal-basis extreme locations are unavailable where their
full spatial columns were not saved; no new spatial reconstruction is inferred
from the reduced cache.

The hot probe's recorded heat-balance discrepancy is **−1.9981 µW**, and its
recorded maximum free-node residual is **5.52×10⁻¹⁰ W**. The uniform 300 K
field error is only **1.23×10⁻⁸ K**. These do not excuse either failed numerical
gate: the source's absolute heat/form tolerances remain unchanged. Nor can a
scalar µW bookkeeping correction be assumed to repair a 126.535 K undershoot,
negative mean-map coefficients, or locally balanced nonmonotone stencils.
Global conditioning/roundoff amplification has not been isolated by this
read-only study; all raw residual failures remain reported.

## Midspan cylinder comparison and axial boundary resolution

The independent steady long-cylinder reference uses motor radius a=14.5 mm,
liner inner radius b=14.7 mm, k_air=0.04 and nominal k_mica=0.45 W/(m K).
The existing first FV bulk centre is r_cell=14.71249469 mm, retaining the exact
radial half-wall coefficient **h=36,030.6036 W/(m² K)**. With all liner radial
bulk states held at 308.15 K,

`q/(2πL) = (Th−Tb)/(ln(b/a)/k_air + ln(r_cell/b)/k_mica)`

and `T(r)=Th−q/(2πL*k_air)*ln(r/a)`. This gives a reference inner-liner surface
temperature **309.602932 K** and heat per length **4,835.196 W/m**. The Fourier
cylinder resistance follows [DOE-HDBK-1012/2-92, HT-02](https://www.energy.gov/documents/doe-hdbk-1012-92vol2).
This closed-form comparison is not a new rocket heat solution.

The central 40% axial interval, Z1069.1–1143.9 mm, is at least 280.5 gap widths
from the finite liner ends. Its twenty existing gap nodes differ from the
reference by **−0.759 to +79.440 K**, RMS **31.986 K**. At the actual Z1106.5 mm
midplane, evaluation of the saved boundary P1 trace gives:

| Surface | Existing facets /maximum axial span | Midplane saved trace | RMS against reference |
| --- | --- | --- | ---: |
| Motor cylinder, group 495 | 536 /187 mm | 573.15 K constant | 0 K |
| Liner inner cylinder, group 523 | 540 /187 mm | 307.448–315.498 K | 0.740954 K |

The curvature-controlled optical triangles span the **entire 187 mm length**
across a **0.2 mm radial gap**, axial-span/gap ratio **935**. The interior
4 mm lattice does not refine these fixed boundary facets. This is a concrete
analysis-resolution limitation, independent of physical CAD correctness.
End effects, junctions, the faceted radius, axial Robin coupling and the source
bulk approximation remain explicit; no rigorous finite-end error bound or
convergence conclusion is claimed from this reference.

## Existing ε0.9 radiation projection at this failed probe only

The script integrates the exact fourth power of each saved P1 triangle field:
its mean is the sum of the fifteen degree-four nodal monomials divided by
fifteen. This is compared with the fourth power of the existing group mean.
It multiplies only that difference by the **existing**
`runs/wo03-cad-radiosity-20261031T051129909396Z/foil-0.9-operator.npz` inward
operator. No radiosity factorization or coupled temperature solve is performed.

Gas-opening brightness and prescribed motor-surface differences are held
unchanged, so their **difference entries** are zero; no brightness temperature
is assigned 0 K or silently equated to gas temperature. Gas/radiation group
areas agree within 7.47×10⁻¹² relative. The largest material fourth-power
difference is 1.04539×10¹⁰ K⁴. Projected net-inward power changes reach
**0.0426244 W** at thrust-pad group 485, with half-L1 redistribution
**0.185864 W** and signed total 2.08×10⁻¹⁷ W. Group 505 changes by +0.0100519 W.
These are differences evaluated on an already unphysical uncoupled probe;
they are not corrected coupled heat rates, temperature margins or acceptance.

## Correction target and reproducibility

The evidence supports numerical work on the mixed Dirichlet/Robin corner trace,
its reaction-dominated spatial resolution and the gas stencil near the motor
fore boundary, plus axial boundary refinement in the thin cylindrical gap.
Any candidate discretization must retain common physical surfaces, conservation,
positive-wall energy and original geometry, then demonstrate bounds/known-profile
accuracy and refinement. This study chooses no repair and changes no method.
Material retuning, clipping temperatures/coefficients, or treating the valid
coarse mesh as proof of temperature accuracy would not address the evidence.

Reproduce with `.venv/bin/python scripts/wo03_gas_field_diagnostic.py` within the
read-only 120-second cap. All completed operator/field inputs are hash-pinned;
the final packet's `record.json` SHA256 is
`ee758ce8ee94bc87e16a961cb7ce17922be30fd87aaa823785bd6d535069052b`.
The extreme-stencil artifact SHA256 is
`7ca2e351883406695b43e0bdb5ac8030e6a172cf171c279b8c34339c475a3834`.
Ruff/Black pass. No shared/frozen, active, Git or UI files are edited; paid
compute cost is $0. Root owns subsequent failed-operator investigations and
numerical method decisions; none is a credible design prediction on this basis.
