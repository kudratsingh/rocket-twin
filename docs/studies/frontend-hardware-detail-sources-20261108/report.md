# Manufacturer-source detail readiness — bounded research

**Preferred next target: `high_g_accel`, Adafruit PID 5374 / ADXL375.** Its
official product dimensions match the frozen 25.6×17.7×4.6 mm envelope, and
Adafruit publishes the corresponding Eagle PCB/schematic repository under
CC BY-SA 3.0. This is a credible next source for a separately identified PCB
outline/hole/layout presentation. It is not a verified complete 3D assembly or
installed-fit model. [Official product](https://www.adafruit.com/product/5374),
[official PCB repository](https://github.com/adafruit/Adafruit_ADXL375_PCB),
[license](https://github.com/adafruit/Adafruit_ADXL375_PCB/blob/main/license.txt).

This packet assesses three recorded products within six logical official
resources, including two inaccessible requests. Research stopped at that bound.
It does not alter the current UI, core/detail producer, frozen geometry, source
specification or publication packet. No contact, purchase, owner measurement,
installation, shell/Python execution, CAD conversion or downloaded-code execution
was performed. No STEP/VRML/DXF or dimension-drawing asset was downloaded.

## Identity gate before searching

The frozen specification names no exact supplier SKU/revision for
`flight_computer` (only Cortex-M7 capabilities), `imu`, `baro`, `micro_sd`, the
main `battery`, `nose_recovery_eye`, generic `recovery_connectors` or
`recovery_protection`. A generic 750 mm parachute is also not an exact product.
These records must not acquire a random manufacturer's board/eye/canopy CAD
merely because its function or rough envelope resembles the current estimate.
The source explicitly defers exact electronics mounting/component definitions.
[Frozen source](https://github.com/kudratsingh/rocket-twin/blob/main/configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml).

Other recorded leads were screened but not added to the three-product research:
`shock_cord` identifies LOC NW-12 variant 39778657730751, while its sewn ends,
finished geometry and packing remain unresolved; `recovery_battery` cites a
120 mAh shop URL but describes a 110 mAh starter-pack cell. The latter identity
needs reconciliation before selecting a supplier model. No substitute product
or new source revision was selected.

## Three-product assessment

| Exact source part / identity | Current frozen display dimensions | Official CAD/drawing result | Correspondence and fit uncertainty | Next action |
| --- | --- | --- | --- | --- |
| `high_g_accel` — Adafruit PID **5374**, ADXL375 ±200 g breakout | **25.6×17.7×4.6 mm** box | Official `Adafruit_ADXL375_PCB` repository lists `Adafruit ADXL375.brd` and `.sch`; README identifies PID 5374 and EagleCAD. CC BY-SA 3.0 license verified. No ready STEP/VRML/DXF assembly verified. | Product dimensions match exactly. Product page identifies four 2.5 mm mounting holes and describes a May 2023 silkscreen revision. RP1 does not pin a purchased board revision or connector/header population. A PCB layout is not proof of every assembled component height or installed clearance. | **Preferred next detail target:** pin the board artifact/revision, inspect its exact outline/holes/layout, reconcile with the 4.6 mm envelope, then prepare a separately identified PCB-only presentation. Keep unverified component heights/connector population explicit. |
| `independent_recovery` — **Eggtimer Apogee** single-apogee kit; no board revision pinned | **44.45×22.86×8 mm**; source says the 8 mm height is a budget | The bounded manufacturer page request was inaccessible; no official mechanical CAD file, drawing revision or redistribution license was verified in this packet. | Current dimensions are repository evidence, not newly verified manufacturer geometry. Kit assembly, component population and power-interface details remain unconfirmed. No claim that manufacturer CAD does not exist. | Retain the envelope. A later bounded source check must establish the exact Apogee board revision, assembly drawing and reusable mechanical data before any detailed representation. |
| `motor_retainer` — **AeroTech 19002**, intended with provisional 78010 motor / 12912 tube family | Nominal historical envelope **Ø44.4×45 mm**, inner-radius placeholder 14 mm; source explicitly says sleeve/cap are schematic | No exact controlled manufacturer 19002 mating/CAD resource was established by the bounded request. No reusable CAD or licensing evidence verified. | Frozen source already withholds current shoulder/cap/nozzle mating geometry. The annular envelope is not a literal assembled contact body or proof of motor/tube fit. | Retain the current envelope. Seek an exact manufacturer drawing/revision for 19002 and its specified mating parts before showing cap, threads, seat or closure contacts. No generic retainer substitution. |

The Adafruit dimensions, mounting-hole fact and revision note come from its
exact PID page; they do not transfer to generic `imu` or `baro` records.
[Adafruit PID 5374 technical details](https://www.adafruit.com/product/5374).
Eggtimer and AeroTech rows deliberately distinguish an unverified bounded fetch
from a global assertion that no CAD exists.

## Pinned evidence for the preferred target

The official directory listing exposes these immutable Git blob identities:

| Artifact | Git blob SHA | Listed bytes | Status in this packet |
| --- | --- | ---: | --- |
| `Adafruit ADXL375.brd` | `4a768fc9f113ba6f95c6e930a3fac436d066f82a` | 269,123 | Inventoried only; not downloaded, parsed, converted or executed |
| `Adafruit ADXL375.sch` | `d96b4274f5074944088ed732eb5591b8a4d3993e` | 429,426 | Inventoried only; not downloaded or executed |
| `README.md` | `6f889a95b7c812182e1c430f1dca4f56f56ccc69` | 1,994 | Product/repository association and format identified |
| `license.txt` | `1d1e1d6e88579dd32086b23e95723a0f4864c22a` | 22,239 | License text read; identifies Attribution-ShareAlike 3.0 Unported |

These are Git object identifiers, **not SHA-256 file digests**. The repository
listing is linked directly from the official manufacturer account.
[Official source directory](https://github.com/adafruit/Adafruit_ADXL375_PCB).
The frozen RP1 specification's recorded SHA-256 pin is
`811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`;
this packet read its published contents for identities but did not independently
rehash those remote bytes.

Before a later import, retain the exact board artifact bytes, their SHA-256,
the immutable revision and the manufacturer's attribution/license notice.
The product page says the 2023 update changes silkscreen; that helps relate
published board variants, but does not establish the owner's future supplied
batch or an as-installed connector/header configuration. Only features
actually described by the source files may become geometry. Missing component
heights remain missing rather than being filled with generic packages.

This packet therefore changes the earlier broad missingness conclusion:
manufacturer source data **does exist for one exact recorded electronics
product**, so its plain box need not remain the final presentation forever.
It does not authorize importing/adopting that geometry now. Any next layer
must have its own source/asset identity, preserve the current source/core
tuple and estimates, and make manufacturer design intent distinct from
installed verification. No engineering, physical-build or flight gate closes.
