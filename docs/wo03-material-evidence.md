# WO-03 material evidence for follow-on design trades

Research note only. These primary sources help define candidate materials and test
plans after the 2 mm plywood-fin and hot ASA/adhesive screening failures. They are
not selected materials, design allowables, proof of compatibility, or a purchase
recommendation. Supplier values are typical/sample values unless the source explicitly
calls a value characteristic or minimum. Root owns design factors and trade decisions.

## Source-backed screening evidence

| Candidate / source | Published evidence and exact context | Limits for this design |
|---|---|---|
| **Birch aircraft plywood — B/BB, all birch** ([BROSZEIT product data](https://broszeit-group.com/produkt/birch-aircraft-plywood/?lang=en)) | Supplier identifies aircraft plywood “through and through,” B/BB quality to SFS 2413, TegoFilm bond, thickness tolerance to EN 315, density about **680–750 kg/m³**. | This aircraft-plywood page does not publish flexural modulus or strength, veneer schedule, adhesive temperature limit, or lot test certificate. Grain direction and actual sheet thickness must be tied to the ordered grade/specific sheet. Density is approximate, not a part mass measurement. |
| **Birch plywood sheet — non-aircraft comparison only** ([BirchPly technical sheet](https://www.eximcorp.co.in/amp/assets/files/birchply--exterior-special-technical-properties.pdf)) | Datasheet for general-purpose birch-face plywood, thickness 9–40 mm, density **640–700 kg/m³**; minimum static bending strength **60 MPa along** and **30 MPa across** outer-layer grain; minimum bending MOE **6,000 MPa along** and **3,000 MPa across**. | Not aircraft plywood and values do not establish properties for thin custom-cut fins, different veneer schedules, notches, edge conditions, or bond/joint strengths. It is explicitly made under a general-purpose specification. No extrapolation to 2 mm sheet. |
| **Balsa-core sandwich ingredient** ([XCell Duro-Balsa technical data](https://xcellcomposites.com/datasheets/datadurobalsa.pdf)) | End-grain balsa core, nominal density **155 kg/m³**; typical ASTM values: compression strength/modulus **13 MPa / 4.107 GPa** (C365), shear strength/modulus **3 MPa / 162 MPa** (C273), tensile strength **13.3 MPa** (C297). Sheet thickness listed **6.35–32 mm**, tolerance ±0.5 mm. | Values are average core-material tests, not a faced panel. A plywood-skin/balsa-core sandwich additionally depends on skin thickness and veneer orientation, adhesive, bond-line preparation, skin wrinkling, core shear/crushing, peel, edge closure and local load introduction. The cited core is far thicker than a thin fin; no sandwich panel result or uncertainty distribution supplied. |
| **G-10/FR-4 glass-epoxy laminate** ([Alro technical data sheet](https://www.alro.com/dataPDF/Plastics/TechnicalDataSheets/TDS_G10FR4.pdf)) | For its G-10/FR-4 column: specific gravity **1.85**; tensile strength **38 ksi**, compressive **66 ksi**, flexural **60 ksi**, shear **21.5 ksi**; maximum operating temperature **140 °C**; 24 h water absorption **0.10%**. Source says data are averages from test samples. | No thickness, orientation, temperature-conditioned strength, impact/fatigue, edge machining, fastener bearing, or actual grade certificate identified in the table. FR-4 fire classification does not mean it is thermally insulating; temperature rating is not a structural allowable. Verify exact grade/thickness and test the actual panel/joints. |
| **Ceramic-fiber paper thermal barrier ingredient** ([KT Refractories ceramic-fiber-paper sheet](https://ktrefractories.com/docs/KT_MY_ceramic_fiber_paper_11052015.pdf)) | Three paper grades list nominal densities **192–224 kg/m³**. HP grade lists conductivity **0.10 W/(m·K) at 600 °C**, **0.14 at 800 °C**, **0.19 at 1000 °C**; stated continuous-use limit **1150 °C**, with 3% linear shrinkage at 1100 °C for 24 h. | This is high-temperature furnace insulation data, not a qualified rocket liner or hot-gas seal. It says nothing here about this assembly’s erosion, gas permeability, binder burnout/handling, vibration, compression set, adhesive compatibility, or whether enough thickness/edge coverage fits. Ambient/low-temperature conductivity and short transient exposure are not given. |
| **Phenolic-paper laminate** ([Megatron HP 2061 / NEMA XXP sheet](https://megatron.ch/infocenter/Normwerkstoffe-HP_2061-ENG.pdf)) | Supplier sheet identifies paper-phenolic laminate; density minimum **1.4 g/cm³**, limit temperature minimum **120 °C** (IEC 216), room-temperature flexural strength minimum **135 MPa**, bending modulus minimum **7 GPa**. | This is a structural/electrical laminate sheet, not a low-density thermal blanket. Its 120 °C limit is not evidence of a loaded continuous-service allowable at that temperature, nor a thermal barrier rating. Specific thickness/grade, duration, property retention and bond details need clarification. |
| **Structural epoxy example — 3M Scotch-Weld DP420 off-white** ([3M technical data](https://multimedia.3m.com/mws/media/2365939O/3m-scotch-weld-epoxy-adhesive-dp420-off-white.pdf)) | Manufacturer reports **Tg = 80 °C** by DSC (second heat); overlap-shear test on aluminum drops from **28.2 MPa at 23 °C** to **14.9 MPa at 49 °C** and **2.7 MPa at 82 °C** under its stated surface preparation and test configuration. A room-temperature sample also reports 32.7 MPa after 200 °C for 30 min. | Tg is a transition, not a service-temperature limit; one brief post-exposure test at 200 °C does not establish service under load at 200 °C. Aluminum test coupons do not predict bond strength on ASA, plywood, paper tube, composites, porous substrates, thick bond lines or poorly controlled cures. The large reduction near Tg is a caution to evaluate transient peak and loaded dwell using the actual substrate/joint and cured process. |
| **Axial compression of rocket tubing — direct but nonmatching test** ([Apogee / MACH Rocketry report](https://www.apogeerockets.com/Peak-of-Flight/Newsletter510)) | Report describes compression-to-failure on 4 in (101.6 mm) diameter, 6 in long cardboard, blue-tube and fiberglass sections; cardboard reported **11.05 MPa**, density **0.689 g/cm³**. Cardboard/blue tube were tested with an Instron; fiberglass used a different concrete compression machine. | It is an actual rocket-tube test, but not the project’s thin kraft airframe: grade, wall build/winding, precise stock identity and result scatter are not established for transfer, and the article’s fiberglass method differed. The reported mean/capacity is not an allowable and not a substitute for imperfection-sensitive shell buckling or representative axial, bending, joint and humidity tests. |

## What is not established

- No source located in this pass reports traceable axial compression/buckling allowables
  for the exact small-diameter, thin-wall kraft model-rocket airframe material and
  geometry in this project. The 4-inch HPR tube test above is the closest direct
  rocket-tube compression evidence found, but it is not a valid property transfer.
- No aircraft-birch supplier datasheet located here publishes sufficient thin-sheet,
  directional flexure, interlaminar/bond and temperature data for a fin design. One
  aircraft-grade sheet gives density and grade only; the separate strength table is
  general-purpose, thicker birch plywood and is included solely as a comparison.
- No measured plywood-skin/balsa-core panel property is established. Ingredient
  data alone do not establish sandwich flexure, skin stability, edgewise strength or
  bonded joint performance.
- Ceramic fiber paper and phenolic paper laminate are distinct candidates. The former
  has high-temperature insulation data but handling/integration gaps; the latter has
  structural laminate data and a much lower stated limit temperature, without a
  corresponding thermal conductivity qualification in the cited sheet.
- Every candidate needs exact grade/thickness/orientation, supplier identity and
  revision, actual-part mass, representative coupon/joint tests, and the project’s
  bounded heat exposure before any margin or operating limit is claimed.

## Interpretation boundary

Do not turn typical or short-term lab values into design allowables by applying an
unjustified factor. Do not equate datasheet flexural strength with a ply/fin/joint
capacity, measured thermal limit with hot-soak survival, or supplier density with
finished-part mass. Structural calculations, selected safety factors, temperature
history and geometry-specific qualification remain with the WO-03 engineering
analysis and owner-performed physical verification stages.
