# Reviewable walkthrough drawings

The first walkthrough now has **25 standalone SVG exports** and a local HTML
index at `output/engineering-walkthrough/index.html`. These are presentation
exports of the existing source-linked React graphics, with recorded dimensions,
units, configuration/status, source hashes and explanatory captions. They add
no engineering calculation and do not imply a complete C1 CAD assembly.

From the repository root, regenerate them without a browser:

```sh
make workbench-drawings
```

Then open the local index or individual SVGs. The drawings are self-contained:
no scripts, external fonts/stylesheets, unresolved CSS variables or external
SVG dependencies. Local generated drawings remain excluded from Git; the
exporter, small evidence records and manifests are published. The source JSON
is reproducible with `make workbench` from its frozen inputs.

| Open this export | What it explains |
| --- | --- |
| `01-arrangement-side.svg` and `04-internal-section.svg` | Overall C1 concept/envelopes, axial stations from the nose and internal subsystem placement |
| `joint-fin_root-section.svg` and `joint-fin_root-layers.svg` | Source-defined tab, shims and socket layers; details that remain undefined |
| `joint-receiver_end-section.svg` | Receiver/cap/windowed-skirt construction and unqualified connections |
| `load-fin_bending.svg`, `load-motor_reverse.svg`, `load-recovery.svg` | Actual recorded force-transfer topology and failed/missing connection evidence |
| Matching `fbd-*.svg` | Isolated component forces and moments; a moment is a force's turning/bending effect |
| `mass-c1-r1-case-comparison.svg`, `mass-r1-additions.svg` | Complete saved C1/R1 cases and where rejected R1 adds mass |
| `mass-c1-balance.svg`, `mass-c1-distribution.svg` | Recorded balance/aerodynamic-force locations and counted mass by station |
| `launch-guide-speed.svg`, `launch-overall-usable.svg` | Conditional departure samples and why overall rail length is not usable travel |

The app remains at `http://127.0.0.1:5173/?workspace=engineering`, with
`&view=forces`, `&view=mass` and `&view=evidence`. Start it with `make preview`.
These URLs describe the saved implementation; this agent has not verified host
browser reachability. No existing inspection, experiment, simulator or replay
source was replaced by the offline-export increment.

## Exact identity and limits

Configuration: `C1_closed_receiver_mass_balance`; specification SHA-256
`d76c34c69c64b9281d0e945643b95d79385393ab7d40156c7cdbc6a601f15228`.
The C1 CAD revision is **unavailable**. The135 component/allocation rows are
not135 detailed CAD solids or a manufacturing-ready assembly. The archived
72-part candidate remains separate. R1 and C2 remain rejected; C3's new stop is
reported separately and is not substituted into this frozen C1 drawing set.

All25 exports parse as XML and retain accessible titles/descriptions, metadata,
explicit portable styles and the15 frozen source hashes. A source-observed
header-overflow risk was corrected by wrapping title/status/configuration/frame/
units and deriving drawing/footer positions from header height. All175 header
lines meet their width-based limits; the longest has117 characters. These are
**markup and identity checks, not a visual-layout pass**.

V1 evidence and its exact exporter are preserved under
`runs/wo04-walkthrough-export-20261102-v1`; V2's record/manifest/README identify
the corrected presentation. No PNG, app screenshot or visual observation is
claimed. The installed native `sips` SVG renderer returned exit13, “Cannot
extract image from file.” One QuickLook fallback returned exit255 with sandbox
initialization/path-filter permission errors. CairoSVG/resvg/ImageMagick and
the checked bundled/system Python rendering packages were unavailable. Those
attempts stopped; no dependency upgrade, headless browser or workaround followed.

Browser acceptance remains separately blocked: automatic approval review rejected
the designated frontend agent's computer-use continuation because runtime
ownership was unresolved. No supported ownership handoff has been established.
No other agent/window or bypass is used. Actual click/keyboard selection,
responsive layout, download behavior, WebGL, simulation/replay interaction and
screenshots remain pending that authorized path. Preserve these open checks in
WO-04/05; offline exports do not complete them or expanded WO-03 acceptance.
