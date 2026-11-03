# G80-F2 — fixed construction follow-up budget

Declared before numerical execution. F1 v1/v2 specifications, run records and
its frontend snapshot are frozen. F2 keeps the dedicated conventional architecture
(ADR0013); no new platform/removable-aft/gimbal architecture is authorized here.

Selected stock before geometry: LOC BT-2.56,66.802mm OD/65.024mm ID/762mm;
Aircraft Spruce02-20850 nominal6mm twelve-ply Finnish birch; AeroTech12912
305mm mount stock plus19002 retainer, with current78010 contact dimensions
explicitly held. Use two LOC blanks for762+298mm body and a custom permanent
split sleeve made from the same offcut (no uncharacterized bought coupler).
Sleeve100mm,50mm overlap each side; fitted OD64.45mm,0.889mm nominal wall,
internal15mm-wide seam patch. This is a new dimensioned fabrication operation,
not a supplier tolerance or an invisible shrink. Count sleeve, patch, epoxy.
Supplier/receiving dimensions and environmental bounds remain distinct.

One integrated F2 layout: existing logger/battery in a serviceable nose carrier;
independent Eggtimer Apogee single-apogee kit/1S starter-package hypothesis,
controller and cell retained with the nose, no recovery power cross-connection.
Its $34 package is charged, not presumed owner stock; live supply confirmation
is still needed. Keep body extraction bore clear. Preserve a separately
calculated secured-ballast comparator, with carrier/wires/attachment charged.
Source seller6mm plywood has no published thickness tolerance: use a declared
incoming acceptance window5.8–6.2mm, verify before cutting, not a claimed
supplier tolerance. Cold/hot properties remain existing conservative estimates.

Fin geometry stays130/65/60/45mm,6mm nominal; two triangular15mm-span ×6mm-base
root wedges per fin. Forward ring two6mm plies plus.2mm laminate glue; three
blind axial fin-tab notches have.2mm front end gap. Aft tab terminates.2mm
before aft ring. Motor case/retainer/nozzle undefined contacts stay held.
Recovery eyes are two opposed anchors at30/210deg, with unequal70/30 and
single-branch/full-force sensitivities; no capacity credit from equal sharing.

Numerical packet: one CPU,30CPU/60wall s for initial complete ledger/static/
guide/recovery and two placement/ballast comparators; at most one declared
coupled correction30CPU/60wall if a defined failure has a specific remedy.
Full50g and additional20g aft/motor-CG probe remain separate. Preserve1cal,
1.5m usable reference,15m/s formal,15.5 planning. Longer guides conditional.
No new full flight campaign while static/connection admission fails.

Local CAD packet: at most two joint models (splice and notched fin/ring),
60CPU/120wall s total; checks remove material and verify contact/clearance,
not whole-vehicle adoption. Local ring structural diagnostic if its strip screen
controls: reuse pinned Gmsh/CalculiX, three mesh sizes at most,60CPU/120wall each,
180CPU/300wall aggregate; finite support stiffness/force balance required.
A rigid-support result alone cannot close installed strength. Stop on invalid
mesh, one timeout or unresolved force-path/BC; no new structural solver project.
No stopped/custom heat-solver restart. Geometry heat paths and existing45°C
required matrix remain explicit; no invented accepted temperature.

Suppliers Sol HIGH: closed15URLs/15min + explicitly declared4URL/5min controller
amendment. Bookkeeping Sol HIGH:15min local cost/placement audit. Graphics Sol HIGH:
30min active implementation +one correction; waiting for sources does not count
as implementation. Native batch<=120s, no browser/computer-use retry. Primary
owns geometry, structural decisions, integration and admission. Required checks/
focused PR/merge stay separate from engineering/prototype/physical/flight gates.

## Single coupled correction declaration

V1 initial stock layout failed static and adverse15.5 planning:913.326g,
.388cal,15.410m/s. Recovery packing moved aft had cancelled nose electronics
benefit. Preserve v1. One correction: chute280--360mm, cord340--440mm,
connectors350--375mm, protector365--375mm; increase fin span60→65mm while
retaining root/tip/sweep and root wedges. Account source areal mass. Replace
the extra3g bridle with two0.3m branches using the existing0.6m/8g heat leader
and already-counted connectors; no lost function or free knot. Correct splice
adhesive5→8g from full nominal.287mm annular film/seam/fillet volume.
Compute a separate retained steel-washer ballast comparator for60mm fins,
including a7g captive capsule/bolt support at55mm and useful1.1cal target.
No further geometry revision follows automatically if a critical check fails.

## Comparator selection and final reconciliation

The declared60mm-fin/retained-ballast comparator is preferred for further
connection verification: its minimum-thickness panel leaves0.401mm root-movement
allowance versus0.059mm for the65mm-span alternative. Twelve source-defined M5
washers give17.816g plus7g capture/fastener budget. The two alternatives remain
separate and neither is a whole-vehicle acceptance. Planning15.5m/s is missed
on1.5m by the preferred package; formal15m/s remains in force. No longer
equipment is adopted.

Within the already declared local CAD packet, final detail refinement sets the
flat tab inneredge.2mm outside the tube, subtracts the two defined eye holes
from wood mass and states25mm minimum/30mm proposed usable eye thread. A final
coupled reconciliation of those completed joint details is included in the
same30CPU/60wall numerical allowance (not another architecture/correction loop).
Preserve all prior v1/v2 and comparator records. Exact purchased eye remains a hold.
