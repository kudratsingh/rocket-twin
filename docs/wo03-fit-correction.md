# WO-03 copy-only fit correction study

Run: `wo03-fit-correction-20261030T221424086743Z`  
Detailed report: [fit correction report](../build/wo03-fit-correction/20261030T221424086743Z/report.json)  
Run record: [fit correction record](../runs/wo03-fit-correction-20261030T221424086743Z/record.json)

This study compares three geometry packages on regenerated copies of G80, G54,
and finned G12. It did not edit active vehicle YAML or CAD source. Each candidate
was rebuilt from the resolved parts; changed structural part volume, mass, local
CG, and inertia were reconciled from CadQuery properties and the existing material
density basis. The report records per-configuration CAD identities and before/after
source hashes (`inputs_unchanged: true`).

## Fit interval method

Clearance is calculated as host radial feature minus insert radial feature. The
worst manufacturing interval adds the applicable feature tolerances; hole diameter
tolerances are halved to obtain a radial allowance. Host and insert temperatures
are varied independently from the 15 C reference to each material's declared
engineering limit. This independent-temperature envelope is a conservative fit
sensitivity, not a paired thermal history. The G12 rail uses its inward rectangular
face and the farthest rectangular corner, rather than a round bounding radius.

CTE bases:

- G11 uses a supplier-data span of 11–15 µm/(m·K) from [Atlas Fibre's G11 data
  sheet](https://www.atlasfibre.com/wp-content/uploads/2023/04/G11_DataSheet-2024.pdf)
  and [BASFF's G11 data sheet](https://www.basff.it/fileup/Immagini/G11%20ENG.pdf).
  These are different suppliers' nominal data, not a measured lot or laminate
  direction for this part.
- Aluminum uses 23.6 µm/(m·K), converted from Hydro's 6061 average 13.1 µm/(m·°F)
  over 68–212°F in its [6061 alloy data sheet](https://www.hydro.com/Document/Index?id=560718&name=Alloy+6061.pdf).
  The shield alloy/temper is not identified as 6061, so this is an explicit proxy.
- Mica uses a broad 10–28 µm/(m·K) in-plane sensitivity interval from the
  [Gund Company Mica M silicone-bonded mica data sheet](https://thegundcompany.com/wp-content/uploads/2024/03/Mica-M-Silicone-Bonded-Mica-Paper-Laminate-by-The-Gund-Co.pdf),
  which gives typical values at 110°C and 250°C. The installed sleeve's exact
  composition is not confirmed against that product.
- Plywood and cardboard CTE values remain the estimates in
  `configs/engineering/wo03.yaml`.

These ranges let the study quantify sensitivities. They do not establish purchased
material identity, thermal pairing, actual process capability, or assembled fit.

## Package results

Values below are minimum clearances after the study's manufacturing tolerances and
independent in-domain thermal expansion bounds. Required radial fit is 0.10 mm.

| Package | Fixed mount to shell, G80/G54 | G12 foil to rectangular rail face | G12 grip ring to gimbal bore | G12 rail corner to gimbal bore | 25-pose CAD sweep |
|---|---:|---:|---:|---:|---|
| A: mount R32.0 mm; rail depth 3.5 mm at R17.5 mm | 0.321 mm, screen pass | 0.178 mm, screen pass | 0.611 mm, screen pass | 0.628 mm, screen pass | No rigid intersections reported |
| B: mount R32.3 mm; rail depth 3.5 mm at R17.5 mm | 0.021 mm, screen fail | 0.178 mm, screen pass | 0.611 mm, screen pass | 0.628 mm, screen pass | No rigid intersections reported |
| C: mount R32.0 mm; rail depth 3.0 mm at R17.6 mm; bore R20.5 mm | 0.321 mm, screen pass | 0.528 mm, screen pass | 0.811 mm, screen pass | 0.977 mm, screen pass | No rigid intersections reported |

The current fixed-mount R32.3 mm package remains below the 0.10 mm fit criterion
under this stack. The TVC rail correction clears the foil face without omitting the
foil or rounding the rail section. Package C adds more margin, while reducing rail
section thickness further and enlarging the gimbal bore. Its mass changes therefore
need updated load-path review before selection.

Copy CAD mass deltas relative to each active configuration:

| Package | G80 | G54 | G12-F |
|---|---:|---:|---:|
| A | −0.984 g, CG −0.406 mm | −1.064 g, CG −0.357 mm | −2.163 g, CG −0.890 mm |
| B | 0 g | 0 g | −2.163 g, CG −0.890 mm |
| C | −0.984 g, CG −0.406 mm | −1.064 g, CG −0.357 mm | −4.443 g, CG −1.830 mm |

CG deltas are body-axis values along the vehicle longitudinal coordinate. The full
candidate inertia matrices and shape hashes are in the JSON report.

## Bearing and linkage dimensions

The current CAD generator uses a 3.4 mm pivot bore and 3.2 mm link bore; resolved
CAD pins are 3.0 mm and rods 2.0 mm. The current pivot tolerance stack falls short
of the 0.05 mm per-side requirement. A source-backed dimensional candidate is a
3 mm McMaster-Carr 91595A113 dowel listed at 3.002–3.008 mm, DIN 6325-m6 / ISO
8734, 7 mm length and HRC 52. The listed 7 mm row gives no double-shear strength
rating, and this is not an identified installed pin. For a proposed machined
bearing bore Ø3.200±0.020 mm, the resulting diametral clearance is 0.172–0.218
mm, or 0.086–0.109 mm per side. That exceeds the 0.05 mm dimensional minimum by
at least 0.036 mm. Pin identity, bore process capability, temperatures, wear,
lubrication and load capacity remain unverified, so this is not fit qualification.

The current TVC CAD cylinders have no positive axial retention feature. The outer
pivot pin spans radial stations 25.0–32.2 mm, overlapping 1.7 mm of the fixed
frame wall and 4.0 mm of outer-gimbal wall; its tip is nominally about 0.265 mm
clear of the paper shell. The inner pivot spans 21.8–28.8 mm and overlaps 3.8 mm
of outer-gimbal wall and 2.2 mm of inner-gimbal wall. Neither pin has a head,
groove, clip, cap, shoulder or fastener. The 0.5 mm kraft shell is not credited as
a retainer. Axial demand and retention capacity are unavailable.

A DIN 6799 size-2.3 E-clip candidate (PTS A6799023) is listed for a 3–4 mm shaft,
with 6.3 mm maximum OD and 0.60 mm thickness. No axial load capacity is used.
Its envelope does not fit the unrelieved 0.5 mm frame-to-shell annulus or 1.0 mm
nested-ring gap. It would require local relief/repositioning, exact clip geometry
and orientation, new structural checks, tolerance/thermal stacks and full pose
sweep. No clip fit or retention pass is claimed.

The study's proposed future vehicle parameters are
`tvc.pivot_pin_diameter_mm`, `tvc.outer_pivot_bore_diameter_mm`,
`tvc.inner_pivot_bore_diameter_mm`, `tvc.link_rod_diameter_mm`, and
`tvc.link_bore_diameter_mm`. They are recorded in the study YAML only. Each
generated candidate includes a reconciled `resolved-candidate.yaml` for downstream
structural checking. No CAD generator parameter was changed here.

## Motion and remaining limits

Every package/configuration regenerated actual CAD copies and ran the current
25-pose inclusive pitch/yaw sweep. No rigid intersections outside the existing
joint-zone exclusions were reported; the existing conservative liner/shell bound
also remains positive. This is finite pose evidence. Purchased pivot clearances,
joint-zone articulation, continuous motion, wiring slack/bend, assembly access,
adhesive layers, metrology, and dynamic loaded mechanism behavior are not verified.

Narrowing G11 rails changes their load-bearing cross section. The fit study gives no
strength credit and does not replace the required rail, ring, foreplate, guard,
pin, bond, and connected-body structural checks. All packages are proposals only:
`active_adoption: false`, `physical_fit_verified: false`, `flight_ready: false`,
and acceptance remains open.
