# Organized inspection controls — bounded follow-up

Owner screenshot shows a crowded mixed control strip and camera actions floating
at its right edge. This increment reorganizes those controls without changing the
frozen RP1 geometry, physics, evidence or work-order/physical gates.

Sol HIGH desktop_source_next_sol owns DesignVisual/InteriorWorkbench markup and
styles plus grouped-control tests. Primary owns Viewer camera groups, common
inspectionToolbar.css, precise-camera entry point, integration and publication.
Only browser_access_sol owns native verification in the permitted Chrome window.

Controls use normal layout flow, wrap within available width and keep readable
keyboard focus/targets. View, Inspect, Source and Alternatives are the top design
groups. Mouse, Frame, Zoom, Display and Views are the 3D navigation groups.
Detailed display/section/dimension/breakdown controls retain the existing Scene
tools drawer, reachable by Display tools and Adjust section cut. The Camera menu
links directly to exact angles/keyboard pan. Whole rocket remains the obvious
recovery action. Redundant Reset view is removed from the primary row; camera
reset remains in the Camera menu. No renderer is moved through conditional roots.

One implementation and one diagnosed correction precede publication. Relevant
web checks then one native packet (at most180seconds input); a second bounded
packet is allowed only for a specific uncovered or corrected path, not blind
retries. Stop on source mismatch, clipped/unreachable controls, a blank/remounted
scene or runtime/ownership rejection; preserve failure and replan explicitly.
Native checks cover actual group/menu accessibility, open/collapsed sidebars,
move/rotate/zoom/fit, display and source/section entry points. Viewport/zoom and
layout performance are reported only where observed. No mobile completion,
frame-rate or engineering acceptance is inferred from CSS/SSR/build checks.

Standing supplier/lab, purchase, physical-work, paid-run, WO-10 and flight gates
stay unchanged. All five inquiries remain UNSENT. Publish a focused PR and merge
after the exact final head's required checks pass.
