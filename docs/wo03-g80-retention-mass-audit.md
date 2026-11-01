# G80 retention and keeper mass audit

**Status: bookkeeping audit only.** This records the mismatch between the saved
52-part G80 package and the later nominal keeper-service study. It does not
revise either artifact, establish a complete replacement mass, or qualify the
hardware. The saved 52-part candidate has identity
`62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009`; the
keeper-service record names that same source identity and says
`full_vehicle_regenerated: false`, `net_vehicle_mass_change_g: null`,
`acceptance: false`, and `flight_ready: false`.

## Old to candidate ledger

| Item / role | Saved 52-part package | Later candidate evidence | Accounting treatment now |
|---|---:|---:|---|
| Existing aft retention hardware | `retention_hardware` = **7.000 g** lump, already included in the 52-part mass. The record describes three M3 socket-cap screw envelopes and says the estimate includes screws, nuts/washers where used, and locking provision. It does not itemize those contents. | Proposed three M3 through-bolt stacks in [`wo03-g80-retention-hardware.md`](wo03-g80-retention-hardware.md) and its study YAML: listed average **2.84 g each**, **8.52 g total** (3 × 2.11 g screw + 0.38 g nut + 0.35 g washer). Variants remain candidates; source lists note discontinued/offline status and current orderability, screw-length tolerance, washer OD tolerance, and strength classes are unresolved. | Do not silently replace 7 g with 8.52 g or add 8.52 g as a final delta. If, and only if, the full 7 g represents exactly the old fastener set being replaced, the arithmetic set-to-set difference is **+1.52 g**. If the old lump must be retained pending itemization and all three new stacks are then booked separately, the provisional additional line is **+8.52 g**, with possible overlap against old screws/nuts/washers/locking still unresolved. Neither scenario is an accepted package update. |
| Mechanical keeper body | No separately identified keeper body in the saved 52-part package. | Keeper-service solid mass **15.409675 g** using the recorded nominal geometry/density. Its three G11 pads are machined as integral keeper features and are included in this body mass (`integral_g11_pads_in_keeper_mass: true`). | This is a nominal candidate body mass, not yet integrated into the 52-part candidate. Count the keeper body once if adopted; do not add a separate loose-pad mass for its three integral pads. |
| Keeper closure fasteners | No separately identified M2 closure set in the saved package. | Keeper-service output separately reports three M2 screw/nut pairs at **1.32 g total** (0.30 g listed-average screw + 0.14 g listed-average nut, ×3). The study source gives these as supplier-listing averages, not weighed pieces. | This line is reported separately from the keeper and modified mount/guide BRep masses by the service script. If carried into a future package, add it once as a separate nominal hardware allowance; it is not inside the 15.409675 g keeper BRep mass. Availability, actual unit weights, property class and length tolerance remain unresolved. |
| M2 washers and proposed 0.1 mm ring shims | None separately identified in the saved package. | Executed service geometry records `m2_washer_mass_g: 0.0`; the geometry config says `m2_washers: none`. The hardware study's OD4/ID2.2 × 0.1 mm ring spacer has null material and mass and is explicitly only a concept. | Count neither M2 washers nor ring shims as installed mass in this geometry. Do not convert the proposed spacer into a physical part or estimated mass without a material, density, tolerance and actual geometry decision. |
| Mount/guide geometry change | Current package is the 52-part integrated candidate geometry. | The service study reports `modified_mount_and_guides_g: 40.448195 g`, `source_replan_mount_and_guides_g: 44.507487 g`, and `removed_old_ring_contribution_g: 4.059293 g`. The generated service geometry is nominal and unaccepted. | These are subset BRep mass outputs, not complete-vehicle replacements or an independently reconciled delta. Do not add the modified mount/guide figure to the package or subtract the old-ring value independently; the full candidate difference is null. |
| Bridge | Not a separate adopted mass line in the saved package. | `bridge_after_holes_g: 10.176847 g` in the service record. | Keep as a study output only until the bridge is represented in a full candidate and exact replacement boundary is established. |

The service script computes `keeper_g` and `modified_mount_and_guides_g` from
their CAD solid volumes, then writes `m2_screws_and_nuts_nominal_g` as a separate
constant and reports zero washer mass. Thus, for a prospective bookkeeping
scenario that includes all named new items, the known nominal line items are
8.52 g M3 stacks + 15.409675 g keeper + 1.32 g M2 pairs = **25.249675 g**.
That is **not** the incremental vehicle mass: it excludes unresolved locking,
adhesive and finish, does not net any removed baseline solids, and may overlap
the old 7 g hardware lump. It also must not be combined with the 40.448195 g
modified-mount-and-guides subtotal as if all were disjoint vehicle pieces.

## Adhesive, locking and finish allocations

The saved package has three distinct, unitemized entries that must stay distinct
until a component-level allocation is approved:

- `adhesive_finish`: **12.000 g**, a distributed sealant/finish/joint allowance;
- `fin_bonds`: **8.000 g**, assigned to the fin-tab/root bond allowance;
- `incremental_mount_gap_epoxy_upper_budget`: **4.620026 g**, a separate upper
  allowance for the incremental R32.2–R32.3 annulus over the full 190 mm.

The mount-fabrication note suggests an illustrative 2.161 g allocation from the
12 g lump for proposed local adhesive joints, leaving 9.839 g for other uses,
but says the physical basis and sufficiency are unproved. The 4.620026 g annulus
is not a complete mount-shell bond mass or measured wet quantity. None of these
entries resolves adhesive required by the keeper, bridge, new M3 stack, or
assembly process. Likewise, the old 7 g hardware description mentions a
“locking provision” without identifying whether that means threadlocker,
mechanical locking, or a counted piece. Preserve the existing budgets in the
baseline and assign no new adhesive, locking or finish mass to them until an
exact-once scope and amount is documented.

## Geometry and prose mismatches to resolve before reconciliation

1. The mount-fabrication prose says to retain the old 7 g and add the full new
   longer-screw/nut/washer/keeper set mass until an exact-once ledger exists.
   The later keeper-service record has actual nominal body and M2 pair values,
   but it has not regenerated the complete candidate or resolved the old 7 g
   overlap. Treat the prose as the conservative bookkeeping instruction, not as
   evidence that a complete mass delta has already been calculated.
2. The old mount-study YAML contains placeholder M3 washer (8 × 3.4 × 1 mm) and
   square-nut (6.6 × 6.6 × 3 mm) geometry. The later documented M3 candidate is
   a 9 mm OD DIN 9021 washer and a DIN 934 hex nut; these are not the same
   envelopes and remain unselected. Do not carry the old placeholders as the
   new purchased-part definition.
3. The keeper geometry/configuration uses **integral G11 pads**, **no M2
   washers**, and no 0.1 mm shim. Any prose or future ledger that lists separate
   loose pads, washers or shims for this executed nominal geometry would
   double-count or describe a different geometry.
4. The service record's `net_vehicle_mass_change_g` is explicitly null and
   `full_vehicle_regenerated` is false. The 52-part package's published mass,
   CG, inertia and guide/flight results therefore remain tied to that exact
   older candidate identity; they do not transfer to the keeper-service design.

## Proposed ledger corrections for primary decision

- Keep the 7.000 g baseline line visible but label its physical contents
  unitemized. When exact old and replacement sets are mapped, reallocate the
  old line to those parts once; until then show the +1.52 g set comparison and
  the conservative +8.52 g gross-addition scenario as separate conditional
  arithmetic, not as an accepted mass change.
- Carry the M3 8.52 g as a supplier-listing candidate total, subject to variant
  selection and measured/verified set mass. Track the M2 1.32 g pair allowance
  separately from the keeper body and explicitly exclude M2 washers/shims for
  this saved geometry.
- Count the 15.409675 g keeper body once, including its integral G11 pads.
  Determine replacement/deletion boundaries for the old mount ring, guides,
  bridge and other affected solids from a full regenerated candidate before
  publishing a net mass, CG or inertia change.
- Retain the 12 g finish lump, 8 g fin-bond allowance, 4.620026 g gap-epoxy
  bound and old 7 g retention lump as separate baseline entries until each is
  itemized. Allocate keeper bond/locking/finish needs only once and record any
  shortfall or extra mass explicitly.

No manufacturing, load-path, material, hardware-strength, dimensional-tolerance
or flight acceptance follows from this mass bookkeeping. A complete mass, CG
and inertia result requires a new exact candidate with a component ledger and
regenerated CAD/mass reconciliation.
