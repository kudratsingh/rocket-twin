/** Static export of the actual A1 React SVG, followed by installed AppKit rendering. No browser or analysis. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, relative } from 'node:path';
import React from '../web/node_modules/react/index.js';
import { renderToStaticMarkup } from '../web/node_modules/react-dom/server.node.js';
import { createServer } from '../web/node_modules/vite/dist/node/index.js';
import { performance } from 'node:perf_hooks';

const root = resolve(import.meta.dirname, '..');
const dataPath = 'web/public/engineering-workbench/g80-a1.json';
const out = resolve(root, 'output/engineering-a1-connection');
const recordDir = resolve(root, 'build/wo04-a1-drawings');
const helper = resolve(root, 'runs/wo04-offline-render-feasibility-20261102-v4/native_image_document.swift');
const hash = data => createHash('sha256').update(data).digest('hex');
const renderedSourcePaths = [
  'web/src/workbench/A1ConnectionViews.tsx',
  'web/src/workbench/a1Types.ts',
  'web/src/workbench/a1ConnectionViews.css',
  'scripts/wo04_export_a1_drawings.mjs',
];
const esc = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
assert.ok(existsSync(resolve(root, dataPath)), `Prepared A1 export missing: ${dataPath}`);
assert.ok(existsSync(helper), 'Installed AppKit image helper missing');
const dataRaw = readFileSync(resolve(root, dataPath));
const snapshot = JSON.parse(dataRaw);
assert.equal(snapshot.schema_version, '1.0.0');
assert.equal(snapshot.identity.candidate_id, 'A1');
assert.equal(snapshot.identity.cad_revision, null);
for (const source of snapshot.generated_from) {
  assert.ok(existsSync(resolve(root, source.path)), `Source missing: ${source.path}`);
  assert.equal(hash(readFileSync(resolve(root, source.path))), source.sha256, `Source changed: ${source.id}`);
}
mkdirSync(out, { recursive: true });
mkdirSync(recordDir, { recursive: true });
mkdirSync(resolve(recordDir, 'swift-module-cache'), { recursive: true });
let server;
const warnings = [];
const originalError = console.error;
let views;
try {
  console.error = (...args) => warnings.push(args.map(String).join(' '));
  server = await createServer({ configFile: false, root: resolve(root, 'web'), server: { middlewareMode: true, hmr: false }, appType: 'custom' });
  const { A1ConnectionDrawing, A1JointDetailDrawing, A1MassScreenDrawing } = await server.ssrLoadModule('/src/workbench/A1ConnectionViews.tsx');
  views = [
    { id: 'a1-upper-connection', title: 'A1 upper sleeve, stop, index and force paths', component: A1ConnectionDrawing },
    ...(snapshot.joint_detail ? [{ id: 'a1-joint-detail', title: 'A1 radial M5 stack, upper lap and fin root', component: A1JointDetailDrawing }] : []),
    { id: 'a1-fit-mass-screens', title: 'A1 recorded fit and complete mass screens', component: A1MassScreenDrawing },
  ].map(view => ({ ...view, markup: renderToStaticMarkup(React.createElement(view.component, { snapshot })) }));
} finally {
  console.error = originalError;
  if (server) await server.close();
}
const metadata = {
  document_id: snapshot.id,
  schema_version: snapshot.schema_version,
  identity: snapshot.identity,
  status: snapshot.status,
  sources: snapshot.generated_from,
  input: { path: dataPath, sha256: hash(dataRaw) },
  rendered_sources: renderedSourcePaths.map(path => ({ path, sha256: hash(readFileSync(resolve(root, path))) })),
  representation: 'Actual saved React SVG, schematic and not to scale. No A1 CAD, fit or joint capacity acceptance.',
  browser_verified: false,
  engineering_accepted: false,
};
const started = performance.now();
const artifacts = [];
for (const view of views) {
  assert.match(view.markup, /^<svg\b[\s\S]*<\/svg>$/);
  assert.doesNotMatch(view.markup, /(?:="(?:NaN|Infinity|undefined)"|<script\b|<foreignObject\b)/);
  const standalone = view.markup.replace(/<svg\b([^>]*)>/, (full, attrs) => `<svg${attrs}><metadata>${esc(JSON.stringify({ ...metadata, title: view.title }))}</metadata>`);
  const svgPath = resolve(out, `${view.id}.svg`);
  const pngPath = resolve(out, `${view.id}.png`);
  writeFileSync(svgPath, standalone + '\n');
  const remaining = 120000 - (performance.now() - started);
  assert.ok(remaining > 1000, 'A1 native batch exceeded 120 seconds before next image');
  execFileSync('/usr/bin/swift', ['-module-cache-path', resolve(recordDir, 'swift-module-cache'), helper, svgPath, pngPath], { timeout: Math.floor(remaining), stdio: 'pipe' });
  const artifact = { id: view.id, title: view.title, svg: relative(root, svgPath), svg_sha256: hash(readFileSync(svgPath)), png: relative(root, pngPath), png_sha256: hash(readFileSync(pngPath)) };
  artifacts.push(artifact);
  writeFileSync(resolve(out, `${view.id}.metadata.json`), JSON.stringify({ ...metadata, artifact }, null, 2) + '\n');
}
assert.ok(performance.now() - started <= 120000, 'A1 native batch exceeded 120 seconds');
const record = {
  result: 'native_render_complete_pending_visual_inspection',
  source_count: snapshot.generated_from.length,
  prepared_data: { path: dataPath, sha256: hash(dataRaw) },
  rendered_sources: metadata.rendered_sources,
  artifacts,
  native_elapsed_seconds: (performance.now() - started) / 1000,
  warnings,
  helper: { path: relative(root, helper), sha256: hash(readFileSync(helper)) },
  limits: ['Offline static SVG and native PNG only; browser interaction and download remain unverified.', 'No geometric fit, CAD, structural or flight computation performed.'],
};
writeFileSync(resolve(recordDir, 'record.json'), JSON.stringify(record, null, 2) + '\n');
let index = `<!doctype html><html lang="en"><meta charset="utf-8"><title>A1 connection concept · offline</title><style>body{font:16px/1.5 system-ui;background:#101e29;color:#e3eef4;max-width:1150px;margin:auto;padding:25px}a{color:#9bd3e8}img{width:100%;height:auto;background:#12202a;border:1px solid #486579}article{margin:30px 0}</style><h1>A1 upper connection concept</h1><p>Separate version · concept / not admitted · not to scale. Offline React SVG and native images, not browser or engineering acceptance.</p>`;
for (const artifact of artifacts) index += `<article><h2>${esc(artifact.title)}</h2><p><a href="${artifact.id}.svg">Standalone SVG</a> · <a href="${artifact.id}.png">PNG</a> · <a href="${artifact.id}.metadata.json">Source metadata</a></p><img src="${artifact.id}.png" alt="Offline ${esc(artifact.title)} preview"></article>`;
index += `</html>\n`;
writeFileSync(resolve(out, 'index.html'), index);
console.log(JSON.stringify({ result: record.result, artifacts: artifacts.map(item => item.id), native_elapsed_seconds: record.native_elapsed_seconds, record: relative(root, resolve(recordDir, 'record.json')) }));
