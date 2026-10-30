# WO-04 — API and frontend v1 (Inspect mode)

Branch: `wo-04-frontend`. Tier: Mac. Spec: `docs/UI.md` — implement, do not redesign.

## Deliverables

1. `src/api/`: FastAPI app with the vehicle, mass, mesh and motor endpoints from `docs/UI.md`;
   meshes served from `build/` with cache headers; `uv run scripts/wo04_api.py` starts it.
2. `web/`: Vite + React + TypeScript + react-three-fiber + zustand scaffold; top bar, parts
   tree, 3D viewport (orbit, exploded slider, section cut, CG/CP markers, burn slider), part
   inspector, vehicle summary with limit checks, thrust-curve plot, mass budget table.
3. Hover/select linkage between tree and 3D; keyboard: `E` explode, `S` section, `R` reset.
4. `web/README.md`: run, build, where each panel's code lives.

## Benchmark

`npm run dev` against the API shows all three modular physical configurations assembled and exploded; clicking any part
shows its specs and `learn:` text; CG/CP markers move with the burn slider and match the WO-01
numbers; preliminary model checks and outstanding hardware/flight gates are shown distinctly;
invalid overrides render red; TypeScript strict and ESLint clean.

## Notes

- If this exceeds one week, split: 04a (API + viewer + tree) and 04b (inspector + summary).
- No physics in the browser: CG at a burn fraction comes from `/api/vehicles/{id}/mass`.
- One accent colour, system font, dark theme, no component library.

Load the complete resolved mode and its hashes. Physical fins, motor hardware,
shared versus aft parts, build method, mass provenance and `learn` remain inspectable.
A finless negative static margin is explicit, not a green stability approval.

## Engineering evidence in Inspect

Start only after expanded WO-03 acceptance (ADR-0007). Link each configuration's
structural, thermal and tolerance report and display evidence status/remaining
physical gates alongside mass provenance. Do not equate a rendered mesh, analysis
pass or numerical RocketPy agreement with a qualified physical vehicle. No browser
structural/thermal/flight solver or new screen is required.
