/** Static export of actual G80-F2 React drawings and bounded installed AppKit PNG render. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, relative } from 'node:path';
import { performance } from 'node:perf_hooks';
import React from '../web/node_modules/react/index.js';
import { renderToStaticMarkup } from '../web/node_modules/react-dom/server.node.js';
import { createServer } from '../web/node_modules/vite/dist/node/index.js';

const root = resolve(import.meta.dirname, '..');
const dataPath = 'web/public/engineering-workbench/preparedg80-fixed-f2.json';
const out = resolve(root, 'output/engineering-g80-f2');
const recordDir = resolve(root, 'build/wo04-g80-f2-drawings');
const helper = resolve(root, 'runs/wo04-offline-render-feasibility-20261102-v4/native_image_document.swift');
const hash = data => createHash('sha256').update(data).digest('hex');
const esc = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const renderedSourcePaths = [
  'web/src/workbench/F2ConstructionViews.tsx', 'web/src/workbench/f2Types.ts',
  'web/src/workbench/f2Construction.css', 'scripts/wo04_export_f2_drawings.mjs',
];
assert.ok(existsSync(resolve(root, dataPath)), `Prepared G80-F2 export missing: ${dataPath}`);
assert.ok(existsSync(helper), 'Installed AppKit image helper missing');
const dataRaw = readFileSync(resolve(root, dataPath));
const snapshot = JSON.parse(dataRaw);
assert.equal(snapshot.schema_version, '1.0.0');
assert.equal(snapshot.identity.candidate_id, 'G80-F2');
for (const source of snapshot.generated_from) {
  assert.ok(existsSync(resolve(root, source.path)), `Source missing: ${source.path}`);
  assert.equal(hash(readFileSync(resolve(root, source.path))), source.sha256, `Source changed: ${source.id}`);
}
assert.equal(snapshot.cad_manifest, null);
assert.equal(snapshot.identity.cad_revision, null);
mkdirSync(out, { recursive: true });
mkdirSync(recordDir, { recursive: true });
mkdirSync(resolve(recordDir, 'swift-module-cache'), { recursive: true });
let server;
const warnings = [];
const originalError = console.error;
let views;
try {
  console.error = (...args) => warnings.push(args.map(String).join(' '));
  server = await createServer({ configFile: false, root: resolve(root, 'web'),
    server: { middlewareMode: true, hmr: false }, appType: 'custom' });
  const { F2ArrangementDrawing, F2JointDrawing, F2RecoveryLedgerDrawing } =
    await server.ssrLoadModule('/src/workbench/F2ConstructionViews.tsx');
  views = [
    { id: 'g80-f2-stock-arrangement', title: 'G80-F2 source stock, splice and forward equipment arrangement', component: F2ArrangementDrawing },
    { id: 'g80-f2-joints', title: 'G80-F2 source layer sections for permanent splice and notched fin/ring', component: F2JointDrawing },
    { id: 'g80-f2-recovery-ledger', title: 'G80-F2 recovery paths and complete mass ledger', component: F2RecoveryLedgerDrawing },
  ].map(view => ({ ...view, markup: renderToStaticMarkup(React.createElement(view.component, { snapshot })) }));
} finally {
  console.error = originalError;
  if (server) await server.close();
}
const metadata = {
  document_id: snapshot.id, schema_version: snapshot.schema_version, identity: snapshot.identity,
  status: snapshot.status, sources: snapshot.generated_from, cad_manifest: snapshot.cad_manifest,
  input: { path: dataPath, sha256: hash(dataRaw) },
  rendered_sources: renderedSourcePaths.map(path => ({ path, sha256: hash(readFileSync(resolve(root, path))) })),
  representation: 'React source projection; stock, joint and connection dimensions are not a same-design CAD assembly.',
  browser_verified: false, engineering_accepted: false,
};
const started = performance.now();
const artifacts = [];
for (const view of views) {
  assert.match(view.markup, /^<svg\b[\s\S]*<\/svg>$/);
  assert.doesNotMatch(view.markup, /(?:="(?:NaN|Infinity|undefined)"|<script\b|<foreignObject\b)/);
  const standalone = view.markup.replace(/<svg\b([^>]*)>/,
    (full, attrs) => `<svg${attrs}><metadata>${esc(JSON.stringify({ ...metadata, title: view.title }))}</metadata>`);
  const svgPath = resolve(out, `${view.id}.svg`);
  const pngPath = resolve(out, `${view.id}.png`);
  writeFileSync(svgPath, standalone + '\n');
  const remaining = 120000 - (performance.now() - started);
  assert.ok(remaining > 1000, 'G80-F2 native batch exceeded 120 seconds before next image');
  execFileSync('/usr/bin/swift', ['-module-cache-path', resolve(recordDir, 'swift-module-cache'),
    helper, svgPath, pngPath], { timeout: Math.floor(remaining), stdio: 'pipe' });
  const artifact = { id: view.id, title: view.title, svg: relative(root, svgPath),
    svg_sha256: hash(readFileSync(svgPath)), png: relative(root, pngPath),
    png_sha256: hash(readFileSync(pngPath)) };
  artifacts.push(artifact);
  writeFileSync(resolve(out, `${view.id}.metadata.json`), JSON.stringify({ ...metadata, artifact }, null, 2) + '\n');
}
assert.ok(performance.now() - started <= 120000, 'G80-F2 native batch exceeded 120 seconds');
const record = {
  result: 'native_render_complete_pending_visual_inspection',
  source_count: snapshot.generated_from.length,
  prepared_data: { path: dataPath, sha256: hash(dataRaw) },
  rendered_sources: metadata.rendered_sources, artifacts,
  native_elapsed_seconds: (performance.now() - started) / 1000, warnings,
  helper: { path: relative(root, helper), sha256: hash(readFileSync(helper)) },
  limits: ['Offline SVG and native PNG only; browser interaction and downloads remain unverified.',
    'No fit, CAD, structural, thermal or flight computation performed in the exporter.'],
};
writeFileSync(resolve(recordDir, 'record.json'), JSON.stringify(record, null, 2) + '\n');
let index = '<!doctype html><html lang="en"><meta charset="utf-8"><title>G80-F2 construction candidate · offline</title>' +
  '<style>body{font:16px/1.5 system-ui;background:#101e29;color:#e3eef4;max-width:1150px;margin:auto;padding:25px}a{color:#9bd3e8}img{width:100%;height:auto;background:#12202a;border:1px solid #486579}article{margin:30px 0}</style>' +
  '<h1>G80-F2 fixed-motor construction study</h1><p>Source projection; no browser or engineering acceptance.</p>';
for (const artifact of artifacts) index += `<article><h2>${esc(artifact.title)}</h2><p><a href="${artifact.id}.svg">Standalone SVG</a> · <a href="${artifact.id}.png">PNG</a> · <a href="${artifact.id}.metadata.json">Source metadata</a></p><img src="${artifact.id}.png" alt="Offline ${esc(artifact.title)} preview"></article>`;
index += '</html>\n';
writeFileSync(resolve(out, 'index.html'), index);
console.log(JSON.stringify({ result: record.result, artifacts: artifacts.map(item => item.id),
  native_elapsed_seconds: record.native_elapsed_seconds, record: relative(root, resolve(recordDir, 'record.json')) }));
