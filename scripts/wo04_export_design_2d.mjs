/** One bounded offline render of a supplied inspection document; never a browser check. */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, relative } from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { performance } from 'node:perf_hooks';
import assert from 'node:assert/strict';
import React from '../web/node_modules/react/index.js';
import { renderToStaticMarkup } from '../web/node_modules/react-dom/server.node.js';
import { createServer } from '../web/node_modules/vite/dist/node/index.js';

const root = resolve(import.meta.dirname, '..');
const input = resolve(root, process.argv[2] || 'build/wo04-focused-2d-v1/inspection.json');
const out = resolve(root, 'output/focused-design-2d');
const recordDir = resolve(root, 'build/wo04-focused-2d-v1');
const helper = resolve(root, 'runs/wo04-offline-render-feasibility-20261102-v4/native_image_document.swift');
const sha = (data) => createHash('sha256').update(data).digest('hex');
const raw = readFileSync(input);
const vehicle = JSON.parse(raw);
assert.equal(typeof vehicle.id, 'string');
assert.ok(Array.isArray(vehicle.parts));
mkdirSync(out, { recursive: true });
mkdirSync(recordDir, { recursive: true });
const started = performance.now();
const server = await createServer({ configFile: false, root: resolve(root, 'web'), server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' });
let markup;
try {
  const { OrthographicDesign } = await server.ssrLoadModule('/src/design/OrthographicDesign.tsx');
  markup = renderToStaticMarkup(React.createElement(OrthographicDesign, { vehicle, selectedPartId: 'fin_set', onSelectPart() {} }));
} finally {
  await server.close();
}
const svg = markup.match(/<svg\b[\s\S]*?<\/svg>/)?.[0];
assert.ok(svg, 'Actual React drawing absent');
assert.doesNotMatch(svg, /(?:="(?:NaN|Infinity|undefined)"|<script\b|<foreignObject\b)/);
const svgPath = resolve(out, 'g80-reference-source-dimensions.svg');
const pngPath = resolve(out, 'g80-reference-source-dimensions.png');
writeFileSync(svgPath, svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="520" ') + '\n');
const remaining = 120000 - (performance.now() - started);
assert.ok(remaining > 1000);
const result = execFileSync('/usr/bin/swift', ['-module-cache-path', resolve(recordDir, 'swift-module-cache'), helper, svgPath, pngPath], { timeout: Math.floor(remaining), encoding: 'utf8' });
const paths = ['web/src/design/OrthographicDesign.tsx', 'web/src/design/orthographicGeometry.ts', 'scripts/wo04_export_design_2d.mjs'];
const record = { status: 'offline_render_complete_pending_visual_inspection', configuration: vehicle.id, identity: vehicle.identity, source_input: { path: relative(root, input), sha256: sha(raw) }, rendered_sources: paths.map(path => ({ path, sha256: sha(readFileSync(resolve(root, path))) })), svg: { path: relative(root, svgPath), sha256: sha(readFileSync(svgPath)) }, png: { path: relative(root, pngPath), sha256: sha(readFileSync(pngPath)) }, runtime_s: (performance.now() - started) / 1000, budget: { attempts: 1, wall_limit_s: 120, installation: false }, renderer_output: result, browser_verified: false, engineering_accepted: false };
writeFileSync(resolve(recordDir, 'record.json'), JSON.stringify(record, null, 2) + '\n');
console.log(JSON.stringify({ configuration: record.configuration, runtime_s: record.runtime_s, result }));
