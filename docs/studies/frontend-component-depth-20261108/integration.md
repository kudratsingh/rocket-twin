# Source-based component detail

The component-depth increment extends the current RP1 inspector with two separate
source-bound close-ups. It preserves frozen `G80-F2-RP1-AD1-definition-v2`, its
55 part IDs and its existing vehicle model, mass, inertia and experiments.

## Open the views

Start `make preview` from the repository root and open
<http://127.0.0.1:5173/>. Select **G80 RP1 / AD1 v2** in Design, then select a part
and open **Details → Inside the component**.

- **High g accel → Explore PCB structure in 3D:** inspect actual manufacturer
  mounting holes, pads, routed copper, component footprints and silkscreen.
  Select a footprint or electrical net, choose Top or Bottom, and use Fit,
  orbit, pan and zoom. This is planar manufacturer artwork in a 3D viewer;
  lifted layers are illustrative spacing. It is not populated electronics CAD.
- **Fin tabs, fins, root gussets, body, motor tube or either ring → Explore fin
  and motor-mount construction:** select individual panels, tabs, gussets, the
  slotted body, tube wall and existing ring layers. Use body cutaway/visibility,
  source-piece metadata, illustrative separation and Fit piece. The panel/tab
  pieces explain a continuous plywood cut, not a newly invented physical joint.

Both close-ups use their own camera and selection; closing returns to the parent
part. Other parts explicitly report unavailable deeper geometry rather than
receiving decorative invented features.

## What the detail represents

| View | Source detail | Still unavailable or unqualified |
|---|---|---|
| Adafruit 5374 board | Pinned official Eagle XY layout: 26 placements, 82 pads, 208 width-preserved routed segments, 26 via drills, 14 nets, mounting holes and silk artwork | Board thickness, package/connector heights, via copper diameter, filled copper pours, installed mounting and incoming silicon identity. The source's U1 ADXL343 value conflicts with its ADXL375 artwork; both are retained. |
| Mechanical construction | 18 child assets from seven existing source records, preserving every oriented triangle and source-world coordinate | Qualified adhesive geometry, manufactured tolerances, installed stiffness/strength, new retainer hardware detail, recovery knot shape and missing physical dimensions. The middle ring layer is a display-only bond reservation. |

The manufacturer board is 25.4 × 17.78 mm. The frozen packaging envelope is
25.6 × 17.7 × 4.6 mm; that envelope is not silently used as board thickness or
populated height. The board reference is not placed inside the vehicle as a
new mass or fit model. Its upstream attribution and CC BY-SA 3.0 notice are shown
in the viewer and retained in the extracted record.

The mechanical child meshes are representation features of existing parent IDs,
not extra bill-of-material entries. Source assembly geometry, full rotational
inertia and fin qualification are unchanged. CAD-derived inspection geometry
remains distinct from hardware that can be manufactured or has passed tests.

## Execution and verification

The initial source export completed within its declared bound and is immutable.
`make component-detail` now verifies/copies the same registered child assets. If
its cache is absent it can reconstruct only those exact bytes from matching
existing parent meshes, through checked temporary staging. It does not generate
CAD or relax source pins. `make preview` includes this optional preparation;
missing/incompatible source remains unavailable without breaking the base viewer.

Local checks passed: 329 web cases (four preserved unrelated A2 cases are outside
this publication; 325 cases in scope), 12 focused Python cases, TypeScript,
ESLint, formatting and the packaged build. After the scoped label/lifecycle
corrections, 11 affected web cases and type/lint/format/build passed again. The
existing bundle-size warning remains; no frame-rate claim follows from a build.

The first native PCB attempt, P56, failed because labels covered the graphic.
Removing the two orthographic label-scale multipliers corrected that defect;
coordinates and source data were unchanged. P57 then passed on actual images:
whole-board Fit, Top/Bottom, GND highlighting and C1 footprint details were
recognizable and readable. Unknown heights and source discrepancies remained
visible. Optional layer-spacing controls were not exercised in that packet.

- [Failed P56, preserved](../frontend-pcb-depth-native-20261109/browser.md)
- [Corrected P57 native evidence](../frontend-pcb-depth-corrected-native-20261109/browser.md)
- [Mechanical source identity and exact-triangle checks](mechanical-export.md)
- [Repeatable preparation and its limits](prepare-notes.md)

P58 stopped before entry because the verifier had not established search-field
focus; the failure is retained. P59 used a supported focused field replacement
and reached the mechanical view. Actual images show the source assembly, tab02
selection and metadata, illustrative separation at 0.5, and a selected-piece Fit
that frames the displaced orange tab. The half-shell control changed the graphic,
but the current angle did not independently show both cut edges/open end; that
visual criterion remains partial. Other child picks and layer controls were not
all exercised. RV-29 therefore remains partial rather than claiming all controls
or detailed geometry are accepted.

[Mechanical native observations and limits](../frontend-mechanical-depth-corrected-native-20261109/browser.md)
record the exact branch. Closing left the parent `fin_tabs` selected in Details,
with the parts filter `fin_tabs` and the normal Fins and roots context; it did not
restore the owner's earlier Recovery group. No global reset or visibility action
was used, and the final visible count was not reread. The camera angle readout
remained H −290.1° / Tilt 51°; that is not a full numerical camera-pose proof.

Test counts, visible geometry and a successful process exit never establish
physical joint, thermal, recovery or flutter acceptance.

All five supplier/lab drafts remain UNSENT. No purchase, physical work, new solver,
engineering requirement change or flight release is authorized by this increment.
G80 custom construction and practical performance remain first; G54 and G12
PID-to-RL retain their separate committed tracks. WO-03 and the full WO-04/05,
WO-10 and physical/flight gates remain open.
