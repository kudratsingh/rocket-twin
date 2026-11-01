# G80 recovery canopy source screen — preliminary, not selected

**Scope:** bounded comparison of three manufacturer-listed parachutes for the
frozen 52-part G80 candidate. This is source research and first-order sizing
only. It changes no configuration, candidate mass, recovery model, target,
purchase state, or engineering acceptance. Product listings and performance
ratings are not evidence of fit, deployment, opening load, lifetime, or flight
qualification.

**Point-in-time listing check:** 2026-11-01. Prices and availability below are
what the official product pages reported during this check; they can change.
No vendor was contacted.

## Frozen baseline and sizing relationship

The frozen candidate is 748.569 g nominal and 798.569 g loaded with the full
separate 50 g growth allowance. In the low-thrust/high-drag full-growth case,
62.5 g of motor propellant has depleted by modeled landing, so the **6.180 m/s
landing-speed anchor corresponds to 736.069 g burnout mass**. The other
full-growth case reached 6.178 m/s and the nominal case 5.966 m/s. The
**preliminary 6 m/s screen stays unchanged**. Those are idealized modeled
values, not recovery qualification or an independent recovery-flight
comparison. See the [bounded recovery horizon](wo03-g80-recovery-horizon.md).

The common-upper YAML assigns the current parachute a 0.75 m canopy diameter,
Cd 0.75, and 0.035 kg mass. The mass is explicitly `estimate: true`, the cite is
null, and the note says actual canopy Cd, packing, opening shock, and descent
speeds require validation. Therefore **35 g is a placeholder estimate, not a
verified purchased-canopy source mass**.

For same atmosphere and terminal drag balance, use only as a provisional sizing
relationship:

```text
v_new / v_old = sqrt(m_new / m_old) * (D_old / D_new) * sqrt(Cd_old / Cd_new)
```

Using **736.069 g at burnout** as the mass anchor, the existing 750 mm / Cd
0.75 assumption implies an equivalent diameter of
`750 * (6.180 / 6.000) = 772.5 mm` at unchanged mass to reach 6 m/s,
corresponding to **0.4687 m²** under a flat circular-area model. Hypothetical
canopy substitutions retain the same 50 g growth allowance already included
in that burnout mass: `m_new = 736.069 g - 35 g estimate + published product
mass`. The resulting masses are 752.669 g, 750.069 g, and 837.147 g. Applying
the provisional area balance gives 0.4793 m² / 781.2 mm for Apogee, 0.1628 m² /
455.3 mm for Fruity Chutes, and 0.1817 m² / 481.0 mm for Rocketman. These are
equivalent flat-circle area/diameter values. The first uses Apogee's own rough
Cd 0.75 suggestion. The latter two use vendor-stated Cd 2.2 only conditionally:
the cited product pages do not define the reference-area convention for that
coefficient, so it cannot be assumed directly comparable with the existing
circular-area Cd 0.75 model. Neither value asserts that an annular canopy has
that fabric/projected area. This is not a new simulation result; actual
projected area and reference-area convention must be established before Cd
values can be combined. No other mass or vehicle property is changed. Actual
canopy projected area is not necessarily `pi*D^2/4`, particularly for annular
canopies; the scaling is suitable only for rough screening.

| Official product / identifier | Laid-out size as stated | Published product mass; change vs 35 g estimate | Material and manufacturer drag/performance data | Manufacturer packed size | Listing snapshot; provisional full-growth speed* |
|---|---:|---:|---|---|---|
| [Apogee 36 in Printed Nylon Parachute](https://www.apogeerockets.com/index.php?cPath=42_309_80&main_page=product_supplies_info&products_id=2339), model **29095** | Octagon, 91.4 cm flat-side to flat-side (36 in); 36 in lines | 51.6 g; **+16.6 g**. Line inclusion in the published mass is not stated; page says lines are sewn on. | Ripstop nylon. Apogee says Cd is unknown and suggests **rough estimate Cd 0.75** pending drop tests/flight data; it does not publish descent performance. | Says it packs into small tubes and fits BT-60; no packed dimensions or volume published. | $18.69; listed **in stock (10+)**. **5.13 m/s*** |
| [Fruity Chutes Iris 36 in Ultralight](https://shop.fruitychutes.com/products/iris-36-ultra-light-parachute-4lbs-15fps), SKU **IFC-36-SUL-OB** | 36 in nominal size; page does not state a separate laid-flat measurement | 49 g; **+14 g**. Line/bridle inclusion in the published mass is not explicitly stated; page lists line and bridle materials. | 0.7 oz ripstop, Spectra loop bridle and 200 lb Spectra lines; toroidal/annular. Manufacturer publishes **Cd 2.2** and rating **4 lb at 15 fps**. | **1.8 in diameter × 3.6 in long; 9.2 in³** (manufacturer value). | $216.22; **currently sold out, request a quote**. **2.99 m/s conditional*** |
| [Rocketman High Performance CD 2.2, 36 in (3 ft)](https://www.the-rocketman.com/products/rocketman-high-performance-cd-2-2-parachutes) | 36 in (3 ft) product size | 4.8 oz = 136.1 g; **+101.1 g**. Line/bridle inclusion in the published mass is not explicitly stated; page lists swivel, lines and bridle. | 1.1 oz Mil-Spec nylon ripstop; 250 lb flat-braided nylon lines, 3/8 in nylon center bridle and 1,500 lb swivel; toroidal/annular/iris. Manufacturer publishes **Cd 2.2**, 4.2 lb at 15 fps, 5.4 lb at 17 fps, 7 lb at 20 fps. | **2.6 in diameter × 4.52 in long = 24.00 in³** (manufacturer value). | Manufacturer's detailed price list gives **$105.50** for the 36 in size; product listing currently exposes an Add to Cart control but its generic header shows $85.00 before size selection. Exact size-specific live price/order status is therefore **not resolved from the listing**. **3.16 m/s conditional*** |

\* Provisional drag-balance estimates only, derived from the 6.180 m/s,
736.069 g burnout anchor, listed nominal diameter, Cd and replacement masses
above. The Fruity Chutes and Rocketman estimates are conditional on Cd 2.2
using a reference area comparable to the flat-circle model, which the product
pages do not define. These are not advertised product descent data, flight
predictions, acceptance results, or a reason to lower the 6 m/s screen. The
anchor is the more useful comparison for growth allowance; nominal-mass descent
was already below the screen in the frozen run.

## What this screen establishes

- The published source suggests Apogee 29095 is a modest mass increase at a
  measured-flat-size near the requested 0.8–0.95 m range. Apogee's own Cd value
  remains a rough starting estimate, not a measured coefficient.
- Both annular Cd 2.2 products publish substantially higher drag coefficients,
  explicit packed dimensions, and payload/descent ratings. Their ratings use
  manufacturer conditions; they are not directly transferred to this vehicle.
- Relative to the placeholder 35 g estimate, the three published masses add
  14.0 g, 16.6 g, and 101.1 g respectively. The largest option creates a
  material same-package mass/CG/inertia and ascent/recovery revalidation burden.
- No product page supplies deployment reliability, opening-shock force for this
  deployment, extraction force in the G80 bay, actual folded pack dimensions for
  the Apogee canopy, temperature limits, or proof that the existing harness,
  anchor, ejection charge, and protection arrangement work with it. Do not
  infer packing volume from photographs.

**Disposition:** useful source options identified; **no option selected or
recommended for purchase**. Exact fit and packed extraction, dynamic opening
loads, anchor and harness capacity, materials/thermal exposure, deployment
reliability, changed mass/CG/inertia, and affected same-candidate ascent plus
recovery revalidation remain open. A chosen replacement must retain the 50 g
growth allowance and pass the existing 6 m/s screen before it can support
package closure. No vehicle configuration was changed.
