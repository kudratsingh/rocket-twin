# G11 manufacturer property source review

**Source review only. No active property, specification, or vehicle input is changed.** The current generic G11 strength screen remains 50 MPa cold / 25 MPa hot. The manufacturer figures below do not establish project allowables, and no structural pass is inferred.

The accompanying [study data](../configs/studies/wo03-g11-load-properties.yaml) captures source identity, values, test/direction metadata, ambiguities, and hot-property availability for downstream review.

## Primary-source findings

| Failure mode / property | BASFF G11 H-class TDS | Atlas Fibre G-11 Type GEB PDF | Interpretation for this project |
|---|---|---|---|
| Flexure | 450 MPa at 20 °C; 350 MPa after 1 h at 150 °C; perpendicular to lamination; ISO 178 | 517 MPa; PDF gives no direction, standard, or temperature. Atlas HTML annotates the value “LW-A, 0.125 in.” | Only BASFF supplies a specific 150 °C-conditioned mechanical value. It is flexural and direction-specific, not a general hot strength. Neither is a design allowable. |
| Compression | 260–550 MPa; ISO 604; table label “// - ⊥” | 434 MPa; PDF gives no direction, standard, or temperature | BASFF’s extracted table does not map each endpoint to the two directions. Atlas HTML reverses its PDF tensile/compression labels. Do not use for directional bearing or crushing acceptance. |
| Tension | 310 MPa parallel to lamination; ISO 527 | 255 MPa, orientation/standard/temperature unstated | Atlas HTML instead assigns 63 ksi (434 MPa) to tensile. The conflict is unresolved; no accepted tensile bound is selected. |
| Shear | Not reported | 151 MPa, with direction/standard/temperature unstated | Not a joint allowable. Hot shear is unavailable. |
| Bond | Not reported | 15 MPa “bond strength,” basis unstated | Does not establish adhesive strength, peel resistance, surface preparation, or a structural bond allowable. |
| Elastic modulus | 24,000 MPa; ISO 178; direction and temperature unstated | Not reported in the reviewed table | Does not replace the active 10 GPa estimated weak-direction screen without grade, layup, and direction matching. |

BASFF’s official [G11 H-class technical data sheet](https://www.basff.it/fileup/Immagini/G11%20ENG.pdf) labels itself Rev. 03, 14 June 2007. Its table text reports the values above, density 1.9 g/cm³, coefficient of linear expansion 15 × 10⁻⁶ K⁻¹, and a maximum operating temperature of 180 °C. The 180 °C rating is not evidence of retained mechanical strength at that temperature. The source table was inspected in the official PDF text extraction; visual confirmation of the compression-direction endpoint mapping was not possible, so the ambiguity is retained.

Atlas Fibre’s [2024 G-11 / MIL-I-24768/3 Type GEB datasheet](https://www.atlasfibre.com/wp-content/uploads/2023/04/G11_DataSheet-2024.pdf) was visually inspected in the manufacturer PDF. Its table says the data are informational, makes no warranty, and notes that individual batch/product test data require a specific request and written agreement. The official [Atlas G-11 page](https://www.atlasfibre.com/material/g-11/) assigns 63 ksi to tensile and 37 ksi to compression, the reverse of the PDF. The HTML page also restricts its 75 ksi flexural listing to LW-A at 0.125 in. The PDF itself does not contain those labels. This catalog inconsistency is not resolved by assuming the larger value or treating either sheet as a certified lot report.

## Temperature and failure-mode limits

At 150 °C, the only mechanical source value found is BASFF’s flexural strength after one hour at temperature, perpendicular to lamination. No 150 °C tensile, compression, bearing, shear, or bond value was found in either manufacturer source. These modes are therefore **unavailable**, not zero and not passed. The BASFF one-hour condition also does not establish equivalence to the actual part’s temperature/dwell history.

The project’s generic hot value of 25 MPa is an existing estimate, not a manufacturer-reported hot allowable. The 150 °C flexural datum must not be substituted into compression, bearing, pin-hole, shear, or bonded-interface checks. Conversely, the stronger typical flexural values must not be used to raise the global screen just because they exceed a current demand.

The current recovery bridge analysis has been reported to reach up to 86 MPa factored stress. That is a comparison prompt only: before any margin is evaluated, link the exact executed record and identify the component, stress component, laminate direction, applicable temperature/dwell, and criterion. Comparing 86 MPa directly with a grade-level flexural result is not a mode-matched qualification. The 50/25 MPa global values remain unchanged by this note.

## Qualification still required

- Identify the actual purchased G11 grade/class, sheet or bar product form, laminate axes, and local part orientation.
- Obtain a traceable lot certificate and the test methods, specimen orientation, conditioning, and statistical basis for the material used.
- Resolve Atlas’s tensile/compression discrepancy and BASFF’s compression-direction mapping before using those properties.
- Establish local material temperature and dwell, then obtain mode- and direction-matched hot data. The reviewed sources provide no 150 °C shear, bearing, tensile, compression, or bond value.
- Test representative machined holes, bearing, bonds, peel, and assembled joints; supplier laminate numbers alone do not qualify these details.

No active material profile or acceptance criterion is adopted here. Coupon and joint testing, source-grade confirmation, and the separate thermal/load-path reviews remain open.
