# Extended workbench offline drawings

Run `node scripts/wo04_export_extended_drawings.mjs` from the repository root. The script checks saved source identity, renders the actual six React modes into11SVGs, resolves portable styles, and uses the existing AppKit image-document helper for one bounded native raster pass.

Open `output/engineering-workbench-extended/index.html` for local SVG/PNG/metadata links and a contact sheet. Generated drawings stay local; the script, small record and source manifest can be published separately.

The saved extension JSON is227355bytes; the six topology graphs are55605bytes. SSR and native elapsed times are recorded CPU/presentation measurements, not browser FPS.

Representative candidate, recovery and electrical images were inspected. Their labels and source states are visible; crossing graph edges still need the numbered source legend. Thermal scalar summaries are not curves. No full current CAD, pin guesses, inertia tensor, browser acceptance or engineering qualification is implied.
