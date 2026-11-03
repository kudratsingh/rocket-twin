# F2-C1 pressure-footprint mesh replan

Declared after the first packet stopped, before the replacement execution.
The first run completed3mm/2mm grids in10.906/52.378CPU seconds,30,144/80,858
nodes, and stopped before the1.4mm solver because the mesh exceeded100000nodes.
The exact over-cap count was not saved; it is unavailable. No invalid cell or
solver failure is inferred from a node-budget stop. The original producer,
known answers, both completed grids and stopped record are frozen under
`runs/wo03-g80-f2-c1-method-20261103-v1/`.

The volume-fragment construction extruded each pressure-footprint circle through
12.2mm of uniform wood. That creates internal partition columns and a narrow
0.1155mm region between the14mm footprint's inner edge and the ring bore.
These are meshing subdivisions, not real material boundaries. The pressure acts
on one external face. A boundary-only planar-disk fragment should retain that
load boundary without imposing full-height cylindrical partitions.

**Selected correction:** one replacement1.4mm grid,69 circle nodes, same exact
STEP material/holes/notches, same quadratic affine elements, contact footprint,
loads, scalar material and finite component springs. The only changed choice is
mesh topology. Check unchangedCAD volume and exact analytic footprint area/first
moment. Keep100000nodes,60CPU/120wall seconds and the overall180CPU/300wall caps.
The unused original allowance covers this one correction; resources are not
raised. Source-hash both implementation files. Stop on any invalid geometry,
missing boundary, resource/force/work failure or failed refinement; no next retry.

The valid3/2mm grids may be compared with the replacement1.4mm grid only because
all represent the same PDE/material/loads/supports with decreasing bulk size and
increasing curved-boundary resolution. Non-nested unstructured meshes need not
share internal partitions. Report their separate construction methods and node
counts; no claim of uniformly nested refinement. If critical results do not
stabilize to the unchanged5%/10% criteria, convergence stays unavailable.

This replan neither selects the unfinished eye/washer assembly nor establishes
its contact law, orthotropic/hot wood properties, global inertial force route or
installed capacity. Even a passing numerical method does not admit the vehicle.
No active F2 geometry/mass or motor/thermal assumption is changed.
