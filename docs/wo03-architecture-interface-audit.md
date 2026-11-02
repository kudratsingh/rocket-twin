# Retained upper interface: calculated cold-fit blocker

Traceability: **IF-UPPER-AFT-001 / RT-FIT-001**; candidate G80 A/B scope only.

The separate [read-only audit](../runs/wo03-architecture-interface-audit-20261102-v1/record.json)
finds a further A/B admission blocker. It changes neither architecture, mass,
material nor requirement and repeats no stopped calculation. One1-CPU/5-wall-
second audit used0.013 CPU seconds, with no CAD, FEA, thermal or flight work.

The frozen C1 **model** coupler has64.0 mm outer diameter and envelope geometry.
Both proposed structural cans have64.4 mm bores. Using the declared screening
bound±0.1 mm per radial surface:

`minimum radial gap =32.2 −32.0 −0.1 −0.1 =0 mm`.

The unchanged minimum is0.1 mm, so the screen fails by0.1 mm. Nominal0.2 mm
radial clearance is not the worst-case result. Neither diameter/tolerance is
claimed as a measured supplier/as-built property; hot/moisture behavior and
actual manufacturing bounds remain unavailable.

For the same proposed bore and tolerance bounds, the dimensional limit would
be **coupler nominal OD≤63.8 mm**. This is a requirement inversion, not a new
selected coupler, third architecture, mass saving or strength qualification.
Actual part selection or tighter justified manufacturing control needs explicit
geometry, strength, insertion, retention, temperature/moisture and all-mode
interface checks. No current part is silently resized or adopted.

The retained printed stop/key envelope spans station918–947 with outer
radius33.2 mm. It cannot be treated as a full solid ring to claim an actual
collision: its detailed key/stop geometry needs examination before a mating
design is admitted. Both architectures already remain not admitted for guide,
connection, thermal and supplier-data reasons; this adds a concrete cold-fit
finding without altering their frozen results.

The same bookkeeping preserves the source A/B drawing generator. Its exact
executed version is archived, and only the maintained default record directory
moves to `build/wo03-architecture-drawings`. Regenerating presentation images
therefore preserves the actual historical image-observation record. No native
or engineering rerun accompanies that output-path maintenance.

**Next bounded interface action:** define a compatible retained-upper/can mating
specification using the actual coupler/stop/key geometry and source tolerances,
with at least0.1 mm minimum clearance and verified finite retention/load path.
Keep the≈29.9 g adverse baseline mass deficit separate; clearing this fit does
not clear guide departure, strength or temperature. Shared G54/G12 interfaces
must receive their own checks before any shared-part change is adopted.
