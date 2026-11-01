# G80 bridge support-traction lower bounds

**The current rigid-support model has adverse face-average shear demands.** In
the 150 N SINGLE service case, the two most loaded support faces have
force-resultant tangential traction lower bounds of **1.322 and 1.336 MPa**;
applying the existing design factor of three once gives **3.965 and 4.007 MPa**.
These exceed the separately estimated **1 MPa hot epoxy shear screen**. This
is a model-based adverse comparison, not a measured joint capacity, a
mixed-mode allowable or an installed-strength conclusion. The EQUAL case has
DF3 tangential bounds of 1.044–1.065 MPa on all six faces. Local peak and
regional stress convergence remain unverified.

The saved Float64 displacement-load fields and exact original-to-compact node
mapping were used. All 1,574 supported nodes partition into six disjoint
source `rail_back` sets. Each face's CAD area is `99.540830698 mm²`; the
maximum difference from the existing source-area check is `4.78e-10 mm²`, under
the unchanged `0.0002 mm²` tolerance. Fitted plane residuals are at most
`7.52e-11 mm`, and all fitted normals have negligible axial component. Normal
sign is defined by the largest absolute component being positive; it is not a
claim about outward orientation. Tangential magnitudes and the axial component
are unaffected by this sign convention.

For a planar face of area A, integrating its traction gives its resultant F;
therefore its maximum traction magnitude is at least `||F||/A`, and its
maximum tangential traction is at least `||F_tangent||/A`. The values below
use the saved support reactions, in N, with source local x/y/z axes. Areas are
mm², so N/mm² is MPa. Axial traction is signed; tangential and total values are
magnitudes. DF3 multiplies service values once. Neither average magnitude is a
local stress distribution or proof of adhesive wetting.

| Case | Film | Support reaction (Fx, Fy, Fz), N | Mean total bound, MPa | Mean tangential bound, MPa | DF3 tangential, MPa | Mean axial shear, MPa |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| EQUAL | 0 | −24.644, −46.474, −25.209 | 0.5860 | 0.3542 | 1.0625 | −0.2532 |
| EQUAL | 1 | −24.268, 46.563, −24.756 | 0.5832 | 0.3483 | 1.0448 | −0.2487 |
| EQUAL | 2 | 52.689, 1.905, −25.269 | 0.5874 | 0.3549 | 1.0648 | −0.2539 |
| EQUAL | 3 | −28.305, −44.308, −24.761 | 0.5838 | 0.3480 | 1.0439 | −0.2487 |
| EQUAL | 4 | −28.000, 44.572, −25.221 | 0.5864 | 0.3539 | 1.0618 | −0.2534 |
| EQUAL | 5 | 52.529, −2.258, −24.785 | 0.5839 | 0.3488 | 1.0463 | −0.2490 |
| SINGLE | 0 | 0.445, −39.670, 22.702 | 0.4592 | 0.2281 | 0.6843 | 0.2281 |
| SINGLE | 1 | −87.750, 106.722, −98.001 | 1.7017 | 1.3215 | 3.9646 | −0.9845 |
| SINGLE | 2 | 136.781, −23.526, −98.972 | 1.7125 | 1.3356 | 4.0068 | −0.9943 |
| SINGLE | 3 | −35.230, −19.149, 23.326 | 0.4660 | 0.2346 | 0.7037 | 0.2343 |
| SINGLE | 4 | −1.228, −15.671, 0.498 | 0.1580 | 0.1426 | 0.4278 | 0.0050 |
| SINGLE | 5 | −13.018, −8.707, 0.446 | 0.1574 | 0.1412 | 0.4236 | 0.0045 |

The six face force sums match the unchanged global reader within `1.5e-14 N`
per component. EQUAL support moment is approximately zero; SINGLE support
moment is `[−3.31254716944, 1.91250000002, −4.94e-12] N·m`, opposing the
applied moment. Both saved fields passed the unchanged global force check in
separate read-only recovery. The original EQUAL output-location stop and SINGLE
RSS-supervisor failure remain recorded; numerical recovery does not repair the
latter's resource-compliance gap. The 150 N is the bridge preflight's service
load. The separate already-factored recovery load is not used here.

These are the **fixed rail-back reaction** lower bounds from the selected
linear, bonded, rigid-backing model; backing compliance, partial bond,
separation, peel and actual hot properties are unresolved. The exact relation
between the imposed support reaction and real adhesive-face load requires the
model assumptions to hold. A comparison to an estimated hot shear screen is
not an acceptance margin. The [compact record and source](../runs/wo03-g80-bridge-support-traction-20261101-v1/manifest.json)
contain all component, moment, normal, hash and resource details. The read-only
process used 4.153 CPU seconds and 4.190 wall seconds; source, prefix and
runtime pins were unchanged, and no solver ran.
