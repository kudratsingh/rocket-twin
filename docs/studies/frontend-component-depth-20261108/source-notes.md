# Manufacturer PCB layer detail

`high-g-pcb-layout.json` now contains actual Adafruit PID 5374 Eagle source layers for a detailed close-up: **26 placements, 68 SMD pads, 14 through pads/drills, 208 routed signal segments, 26 vias, 14 nets / 71 contact references**, plus real top/bottom silkscreen. Silk includes **4,876 manufacturer artwork rectangles**, 51 line features, nine circles, two polygons and 19 source text labels. This is new usable source geometry data, not another block envelope or a status-only inventory.

The extraction script is `scripts/wo04_high_g_pcb_detail_export.py`. It reads only cached source data and reproduces a compact versioned JSON packet. There is no CAD kernel, network request, installation or physics execution. Original manufacturer source SHA-256 is `7c089eb8cc0756b7dc5e30abd240978dc272113d93f602b497f8f442d532d68c`, immutable git blob `4a768fc9f113ba6f95c6e930a3fac436d066f82a`. The full **CC BY-SA 3.0** notice and Limor Fried/Adafruit attribution are retained in the JSON. The source is [Adafruit's exact board file](https://github.com/adafruit/Adafruit_ADXL375_PCB/blob/main/Adafruit%20ADXL375.brd); no new fetch occurred.

## Viewer-ready representation

- All coordinates are **manufacturer board XY millimetres**, +Y up. They have no installed vehicle registration. Outline segments preserve the source rounded corners; size is **25.4 × 17.78 mm**. This differs from the nominal product envelope **25.6 × 17.7 × 4.6 mm**; no scale correction is made.
- Four mounting drills retain exact centres **(2.54, 15.24), (22.86, 15.24), (2.54, 2.54), (22.86, 2.54) mm**, all Ø2.5 mm.
- `pads` retain refdes/pad names, net, layer, XY centre/corners, dimensions, source rotation and SMD roundness. Through-pad drill and explicitly supplied copper diameters remain separate.
- `traces` retain actual net/layer, sampled source wire path and source width. Layers 1/16 contain **151/57** routed features. `nets.contacts` connects these nets to actual component/pad references; a trace has no invented single refdes.
- `vias` retain drill centres, diameters and source extent. The board file leaves their copper diameter implicit; `diameter_mm=null` prevents a guessed annulus.
- Real silkscreen artwork is grouped by refdes/layer as flattened four-corner XY arrays. Lines, circles, polygons and text positions are also supplied. Mirrored packages are reflected in local X, rotated and placed, with top/bottom layer pairs exchanged. The actual bottom SJ1 pad is checked against its routed net endpoint.
- The two `copper_polygon_boundaries` are GND **pour boundaries only**. The source does not contain a computed final fill in this extraction: do not render a solid full-board copper pour or invent clearances, thermal spokes or islands.
- `documentation` separates source component/placement/name/value drawing features from physical copper and silk. Text retains content, placement, size, font metadata and orientation, but has no extracted glyph outline. Browser-font text is a labelled rendering aid rather than exact Eagle lettering geometry.

## Strict geometry boundary

**PCB thickness and every component height remain unavailable.** Pads are footprints, not complete package bodies. No headers, solder joints, sensor internals or component Z was invented. U1 remains the official file's **ADXL343** value; neither the ADXL375 product title nor package shape proves incoming silicon identity. Current frozen RP1 mass/inertia and all 55 source IDs remain unchanged.

A source-layer viewer may separate the planar layers using explicitly labelled **display offsets**. Those offsets must not be presented as material thickness, component height or a physical assembly. Existing core/optional inspection geometry and the original 2D PCB drawing are not overwritten. Engineering, installed-fit, manufacturing/build and flight acceptance remain open; all inquiries stay UNSENT.

The extraction ran in approximately **0.050 CPU seconds**, below the 60-second cap. Four focused tests cover pinned identity/unknown heights, net/pad/route/artwork coverage, mirrored bottom-jumper alignment and optional exact-source reproduction. No browser-rendering or visual acceptance is claimed by these source checks.
