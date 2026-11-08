# Direct manipulation and rendering correction

The gesture controller retains the tested camera angle/basis math. This packet fixes specific interaction defects: a3px drag threshold separates click jitter from orbit; capture-phase drag routing avoids hover/raycast interception; a drag returning to its initial point cannot accidentally select a component. Wheel input normalizes pixel/line/page units and trackpad pinch. Zoom in/out, Fit, Frame selection and Reset are labelled and visible.

All26 RP1 source GLB primitives lack NORMAL attributes. Missing normals are generated on private render-only geometry clones; source positions, indices, bounds and GLBs are unchanged. Lighting/highlight intensity is reduced and declared material families determine roughness/metalness. Admitted optional detail meshes retain their layer colours. More accurate shading is distinct from source-supported additional geometry; a bounding box remains a bounding box.

Manual views outside all loaded bounds retain a conservative tight near plane; the tiny adaptive near plane is reserved for intersecting/interior views. Far clipping still encloses the recorded bounds. No polygon offset, hidden connection or source-geometry movement is used to disguise intersections.

Seventeen focused source tests cover gestures, drag-loop picking, pinch/wheel normalization, cleanup, clipping, normal generation, source vertex/index preservation, detail colours and existing pole/roll/projection behavior. Lint/format/typecheck pass. These checks do not establish browser feel or manufactured geometry. See the separate baseline and integrated browser records for actual observations. No physics, material allowable, CAD adoption or engineering/physical/flight gate changes.
