# WO-03 secondary shield radius trade

## Decision

The corrected G54 CAD geometry ran at both requested foil radii. Both candidates
still fail the unchanged 45 °C aft-shell screen in the required combined 300 °C
case / 35 °C ambient / degraded-foil ε=0.9 condition. No thermal promise was
shown, so the work stops at fixed-mount G54; no G12 modes were added.

## Executed trade

Run: `runs/wo03-secondary-shield-20261031T001841Z/record.json`.
Source: hash-identified `build/wo03-correction-package/latest/G54-0.075/resolved-candidate.yaml`.
The prior record `runs/wo03-secondary-shield-20261031T001448Z/record.json` was an
incomplete hypothesis: it treated radius plus 0.3 mm as the foil radius and left
the fixed mount bores unmodified. Do not use it as the executed geometry trade.

| Candidate | Physical foil radius | Mount bore radius | Actual axial foil coverage | Thermal result | Net mass change |
|---|---:|---:|---|---|---:|
| G54 R18 | 18 mm, 20 µm wall | 18.3 mm | 1.013–1.200 m (187 mm) | Aft shell 46.95 °C at 64 s; margin −1.95 K | −0.903 g |
| G54 R22 | 22 mm, 20 µm wall | 22.3 mm | 1.013–1.178 m (165 mm) | Aft shell 46.52 °C at 75 s; margin −1.52 K | −4.176 g |

For both cases the existing fixed-mount ring bores were enlarged in memory to
foil radius + 0.3 mm. Every ring's `ring_inner_radii_mm` was updated, rails and
fin-slot/channel dimensions were retained, and the normal mount CAD generator
recomputed ring/bond solids and CAD mass properties. All added solids were valid.
Placed assembly intersection checks reported no intersections involving either
candidate foil or its end collars. G54 R22's existing aft retainer blocks extend
inward over the final 20 mm; the foil and mica aft collar stop 2 mm ahead of that
region. The removed 22 mm axial coverage is recorded in the run, not modeled as
covered. The original foil spans 1.013–1.200 m.

The thermal model preserves opaque radial conduction, mica end collars and their
2 W/K low-contact bridges. It ran through burn and soak with the explicit
high-conductivity / low-heat-capacity corner and the required combined case.
Neither run passes; the closest case remains 1.52 K over the screen. Both net mass
changes are negative because the enlarged plywood ring bores remove more modeled
mass than the shield and collars add. These are rebuilt nominal CAD masses, not
measured masses.

The record carries SHA-256 hashes before and after for the resolved candidate,
latest package record, thermal acceptance config, engineering inputs and thermal
topology. The hashes match; only the in-memory study vehicle was changed. No active
spec or source CAD was edited.

## Limits

This rejects these two thermal design trades; it does not close WO-03. It does not
qualify ring strength after bore enlargement, bonds, materials, adhesives, dynamic
clearance or exact motor/foil histories. A structural revalidation would be
required before adopting either geometry. `flight_ready` remains false.
