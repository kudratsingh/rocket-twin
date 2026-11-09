# Detailed CAD and engineering graphics

## What “intricate” means for this workbench

Use actual engineering features: bores, holes, slots, shoulders, wall thicknesses,
stock layers, tabs, clearances, connector patterns, pivots, fasteners and defined
interfaces. A flat plywood plate may correctly have simple surfaces. Decorative
textures, arbitrary screws, threads or electronics packages cannot fill a missing
source dimension. Improving lighting or triangle count does not add design detail.

Maintain separate maturity for each feature: **source-dimensioned ideal geometry**,
**manufacturer reference**, **simplified envelope**, **concept/reservation**,
**allowance without solid**, or **missing**. Also record calculated/estimated/
measured basis and engineering status. Detailed inspection CAD is distinct from
qualified manufacturing geometry. Imported geometry requires revision/licence,
units, native frame and explicit installation transform.

## Required coverage and deliverables

| View | Required usable graphic and interaction | Source/acceptance limit |
|---|---|---|
| General arrangement |Side/front/motor-end and annotated3D, overall dimensions, datum/stations, subsystem boundaries; select a feature/part |Use exact candidate geometry/revision; undefined features conspicuous |
| Longitudinal/section |Full-length internals plus along/across adjustable cuts; cut-face view and visibility/isolation for tiny parts |Render clipping is uncapped unless real section geometry is exported; no invented solid faces |
| Joint details |Fin/root/slot/tube/rings, recovery passage/anchor, motor seat/retainer/liner, fixed splice, electronics mounts |Show named contact/bond/fastener features, engagement and actual recorded tolerances; undefined joints stay undefined |
| Component internals |Product subcomponents, layers, board holes/pads/traces/footprints, bearings/pivots where sourced |PCB XY is not a populated product; no borrowed heights or qualified stiffness |
| Manufacturing drawings |Dimensions, stock thickness/orientation, datums, tolerances, mating features, scale/revision/status |Image bounds are not manufacturing dimensions; no final drawing claims while critical inputs absent |
| Structural paths |Selectable thrust, reverse retention, fin, guide and recovery arrows through actual joints; free-body views |A moment is a force's turning effect. No guessed rigid supports/equal sharing; link every demand to its source |
| Mass/stability |Axial/subsystem/part mass, separate allowance, CG/CP/calibre, loaded/burnout and adverse comparisons |Backend values only; missing inertia null; current CP/aero validity follows geometry |
| Launch/aero |Guide fittings, nominal rail versus usable travel, speed/targets/wind; fin-planform comparisons |1.5m reference;15 formal/15.5planning; longer equipment unconfirmed; schematic airflow explicitly labelled |
| Strength/vibration |Compatible stress/deformation/margins, case/material direction/temperature, modes/flutter evidence |No scalar-to-spatial conversion; exaggerated deformation shows multiplier; normalized modes are not actual displacement |
| Thermal |Motor boundaries, real material paths/contacts/openings, shielding, burn/soak histories and limits |Part mean versus local hotspot; required45°C screen and failed/stopped cases retained; no new custom heat solver |
| Recovery |Harness topology/branches, anchors, packing/extraction/separation, slack and opening assumptions |Storyboard unless validated deployment model; no invented knot/end capacity or contact shape |
| Electrical/control |Source-netlist power/signal graph, cells/switches/sensors/computer/servos, independent recovery; PID/RL block diagram |Unknown pin assignments undefined; planned controller/hardware qualification remains later WOs |
| Assembly/service |Labeled exploded stages, fastener/bond access, motor replacement, electronics service, packing/arming |Illustration unless motion/clearance checks support it; no unverified extraction animation sold as proof |
| Requirements/test map |Click requirement/risk → affected joint/part → case/result → remaining test |PR/test counts are supporting evidence, not physical acceptance |

Every graphic needs configuration/revision, source references, units/frame, legend,
status and applicable validity. Selection should synchronize drawing, model, part
inspector and evidence wherever a real mapping exists. Export retains these labels.
Missing topics are an explicit unavailable view, never an empty success panel.

## Geometry production and useful quality

1. Reuse frozen source assets and backend generators. Improve detail only where
   current source dimensions support it. Keep parent/feature mapping and a
   separate geometry hash. Do not edit generated meshes by hand.
2. Use parametric template inputs for actual holes, bores, slots, wall/layer
   definitions and assembly features. Preserve continuous stock functions and
   connection evidence. CAD placements/constraints establish geometric intent,
   not installed strength or a continuous motion proof.
3. Keep B-rep/STEP for engineering exchange, GLB for inspection, SVG/DXF/PDF for
   drawings, STL only for its appropriate fabrication scope, and JSON manifest
   for identity/units/status. STL has no embedded unit guarantee.
4. Pickable low/medium/high representations may share one source definition.
   Record tessellation tolerance, bounds, scale and triangle counts. Selection
   targets must match visible geometry. Load subcomponent detail on demand;
   disposal and caching must survive React lifecycle changes.
5. Use edge/section cues, restrained colors, readable lighting and fixed-screen
   labels. Measure current loads and interaction performance on actual hardware;
   do not claim60fps from a build or static image. Keep the existing failed
   benchmark until a separately declared method/fixture passes it.

## First supported additions

Start with the existing18 mechanical child assets and manufacturer PCB source;
finish reliable body cut-face/isolate/feature selection and dimensional context.
Add AD1 recovery-passage datum guides: forward ring1060–1072.2mm, wrap1072.2–1077mm,
sleeve980–1060mm, knot reservation1077–1127mm, and actual60° notch registration.
These are source guides, not a dressed cord/knot solid or a thermal/strength pass.
Exact pins, axis conversion and conflicts are in the
[source packet](../studies/frontend-component-depth-next-20261109/source-opportunities.md).

Next resolve source-ready features by criticality: body/splice and fin/root,
recovery, exact motor support/retention and heat interfaces, avionics mounting,
then purchased subcomponents. Source conflicts prevent a particular detailed
hardware claim but do not delay independent library/navigation work.

## CAD completeness gate

All required physical parts and critical joints in the chosen candidate must have
an explicit representation decision. Allowances do not need fake solids. Every
critical mating/contact/retention feature needs supported geometry or a visible
blocker. Full detailed-CAD completion is **not** achieved by counting55 entries
or26 meshes; missing critical motor/recovery/product details remain open until
source or later authorized measurements resolve them. A prototype-ready pack and
flight-ready hardware additionally require their separate engineering/test gates.
