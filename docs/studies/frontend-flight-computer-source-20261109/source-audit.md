# Flight-computer detail source audit — November 9, 2026

**Decision: retain `flight_computer` as the frozen estimated envelope. Its exact
manufacturer/product/revision is unavailable.** The YAML does not name Teensy,
PJRC, a SKU, a board revision or a supplier citation. The existing November 8
inventory already records this identity gap. Cortex-M7 capability and a similar
outline are insufficient to identify purchased hardware. No current RP1 product
has been selected or changed by this audit.

The task's named **Teensy 4.1 lead** was checked only as an unadopted manufacturer
reference, not as the current flight computer. This bounded audit stops here:
no controlled manufacturer 3D assembly or explicit asset redistribution licence
was verified in the examined resources. No alternative board hunt follows.

## Frozen source and reused evidence

The actual local YAML bytes still hash to
`811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`.
Its `parts[id=flight_computer]` is a commercial estimated `purchased_envelope`:
61 × 18 × 6 mm, 12 g, station 85 mm, lateral offset (0, −11) mm,
CG offset 30.5 mm, 5 V/0.1 A and a $32 budget estimate. These are frozen source
values, not manufacturer measurements, a current quote or a qualified model.
The source defers exact component/datasheet/price/mass/mounting to WO-09.
[Actual source](../../../configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml).

This reuses the prior inventory's explicit unidentified disposition and the
component-depth packet's rule that planar source features and display offsets
cannot invent populated Z. It does not repeat the Adafruit audit or transfer its
CC BY-SA licence, board thickness, footprint or silicon identity to another board.
[Prior inventory](../frontend-hardware-detail-sources-20261108/report.md),
[component-depth scope](../frontend-component-depth-20261108/plan.md),
[PCB source limits](../frontend-component-depth-20261108/source-notes.md).

## Official lead evidence and exact limits

Five PJRC HTML resources and one referenced image endpoint were examined on
2026-11-09, within the six-resource bound. Only one asset download was attempted;
it failed before receiving bytes. Search snippets did not admit another product.

| Resource | Evidence established | Limit |
| --- | --- | --- |
| [PJRC Teensy 4.1 product](https://www.pjrc.com/store/teensy41.html) | Different Ethernet/lock variants; pinout PDFs, dimension/component-location images and design-change history are linked. Finished drill diameters are 0.965 mm at 59 locations and 0.762 mm at six. | Drill counts are not a mounting-fastener specification. The page directs 3D readers to contributed forum models, not a controlled manufacturer STEP assembly. No numeric component Z was extracted. |
| [PJRC dimensions index](https://www.pjrc.com/teensy/dimensions.html) | Official Teensy 4.1 dimension-image endpoint exists. | No numerical image transcription was possible through this packet's supported retrieval; no image-derived pin centres, heights or tolerance were invented. |
| [Dimension image endpoint](https://www.pjrc.com/teensy/dimensions_teensy41.png) | Exact official URL inventoried. | The sole download failed: curl exit 6, host resolution failure. No retained image, byte count or SHA-256 exists. |
| [PJRC Teensy 4.1 with pins](https://www.pjrc.com/store/teensy41_pins.html) | Describes a 2.4 × 0.7 inch form factor and distinguishes soldered-pin variants; USB-host and microSD features are documented. | Nominal XY is not a populated height, connector clearance or the unknown RP1 product's outline. |
| [PJRC Eagle library index](https://www.pjrc.com/teensy/eagle_lib.html) | Lists contributed libraries/footprints. | Manufacturer hosting/linking does not turn contributors' files into a manufacturer board-layout source or a verified redistribution grant. No linked contributor file was fetched. |
| [PJRC schematic index](https://www.pjrc.com/teensy/schematic.html) | Lists Teensy 4.1 schematic images. | Electrical connectivity references are not mechanical EDA placement/routing, package heights or installed-fit geometry. Images were not downloaded or transcribed. |

The product history records a changed SD socket in March 2023, and identifies
SparkFun manufacturing after March 2025. A future reference therefore needs an
actual manufacturing/board revision and population, not simply the family name.
These facts come from the [same official product history](https://www.pjrc.com/store/teensy41.html).
No board production revision is pinned by RP1. No photograph was used to infer
IC bodies, copper traces, solder, fasteners or package/connector dimensions.

## Differences that can and cannot be calculated

| Field | Frozen RP1 source | Teensy 4.1 lead | Difference / disposition |
| --- | --- | --- | --- |
| Product/revision | Unspecified | Family identified; variant/revision unselected | Identity correspondence unavailable; no installed model admitted |
| Nominal length | 61 mm estimate | 2.4 in = 60.96 mm | −0.04 mm, comparing stated nominals only |
| Nominal width | 18 mm estimate | 0.7 in = 17.78 mm | −0.22 mm, comparing stated nominals only |
| Populated height | 6 mm budget envelope | Not verified in retained numeric evidence | Difference unavailable, never zero |
| Mounting/headers | No exact interface or population | Soldered-pin variants and drill diameters documented | No screw-hole pattern or mounting method adopted |
| Frame/placement | Nose station/offset in RP1 | Manufacturer reference registration unestablished | No transformation, orientation or fit correspondence |
| Mass/current/CG | 12 g / 0.1 A / 30.5 mm, estimated | Not verified in this bounded mechanical-source audit | No numeric difference, mass credit or inertia substitution |
| microSD | Separate RP1 `micro_sd` accounting row exists | Lead has an integrated socket feature | Functional/accounting correspondence unresolved; no duplicate/removed-mass credit |

The inch conversion is exact arithmetic using 25.4 mm/in. It does not establish
manufacturing tolerance, complete connector bounds, installed orientation,
clearance or part identity. Those XY deltas are too small to identify a board.

## Reuse decision and next evidence

A linked, clearly unadopted **manufacturer dimensional/pin reference** is useful
for learning. A detailed populated, redistributable manufacturer reference mesh
is **not source-ready** from this packet: exact product correspondence, controlled
assembly/placement evidence, populated Z and an explicit applicable asset licence
remain missing. The reviewed EDA index is a contributor index; schematic and
component photographs cannot supply guessed physical trace/package geometry.
No official EDA/STEP/footprint bytes or licence were downloaded. This is a bounded
failure to verify a usable source, not a global claim that no such source exists.
Do not copy/rehost original drawings, contributed EDA or derived populated assets
as a licensed product until their applicable terms are actually established.

First resolve the exact product/variant/revision and supported mounting scheme in
source-controlled evidence. After any separately authorized procurement, the
smallest remaining physical evidence would be:

1. Record the actual supplied revision and populated headers, memory/card and
   connectors, with the complete assembled XY and top/bottom Z envelope.
2. Confirm the chosen carrier/mount interface and connector/cable/SD-card access
   envelope; measure only dimensions not resolved by controlled supplier data.
3. Weigh the complete counted assembly and establish its CG, accounting separately
   for any already-budgeted card, headers, cables, carrier or fasteners.

This is a later evidence list, **not an owner measurement request**. Hardware is
unbought; no immediate owner action is needed. No source/CAD adoption, geometry
or UI change, flight model, purchase, supplier/lab contact, physical execution,
WO-10 review or flight release is implied. All five inquiries remain UNSENT.

`source-manifest.json` records local input hashes, the resource URLs/retrieval
date, null remote file hashes where no original bytes were retained, the failed
single download and this exact stopped disposition. The output directory has no
manufacturer asset to publish.
