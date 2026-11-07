/** Actual React exports. This does not render images or exercise a browser. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import React from '../web/node_modules/react/index.js';
import { renderToStaticMarkup } from '../web/node_modules/react-dom/server.node.js';
import { createServer } from '../web/node_modules/vite/dist/node/index.js';

const output = 'output/rp1-connections-20261107';
const input = 'web/public/engineering-workbench/rp1-connections.json';
const document = JSON.parse(fs.readFileSync(input, 'utf8'));
fs.mkdirSync(output, { recursive: true });
const server = await createServer({ configFile: false, root: path.resolve('web'), server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' });
const hash = (data) => crypto.createHash('sha256').update(data).digest('hex');
const files = [];
const write = (name, data) => { fs.writeFileSync(`${output}/${name}`, data); files.push({ name, sha256: hash(data) }); };
try {
  const { Rp1ConnectionsView, Rp1ConnectionGraph } = await server.ssrLoadModule('/src/workbench/Rp1ConnectionsView.tsx');
  const { validateRp1Connections } = await server.ssrLoadModule('/src/workbench/rp1Connections.ts');
  validateRp1Connections(document);
  for (const drawing of document.drawings) {
    const data = fs.readFileSync(drawing.path);
    if (hash(data) !== drawing.sha256) throw Error('Incompatible saved drawing');
    write(`${drawing.id}.svg`, data);
  }
  const css = `body{margin:0;background:#101923;color:#edf7fc;font:16px system-ui}main{max-width:1200px;margin:auto;padding:24px}a{color:#a2e5ff}code{overflow-wrap:anywhere}button{padding:8px}img,svg{max-width:100%;height:auto}details{margin:12px 0}` + fs.readFileSync('web/src/workbench/rp1Connections.css', 'utf8');
  for (const [id, part] of [['fin-root', 'fin_tabs'], ['recovery', 'rp1_kevlar_wrap']]) {
    let html = renderToStaticMarkup(React.createElement(Rp1ConnectionsView, { document, connectionId: id, requestedPartId: part }));
    // Portable artifact copies only: app URLs and original source hashes stay in the manifest.
    html = html.replaceAll(/\/api\/engineering\/rp1-connections\/drawings\/([a-z0-9-]+)\?[^" ]+/g, '$1.svg');
    html = html.replaceAll('href="/?', 'href="http://127.0.0.1:5173/?');
    write(`${id}.html`, `<!doctype html><html lang="en"><meta charset="utf-8"><title>RP1 ${id} source artifact</title><style>${css}</style><main><p>Offline React export — selection buttons are inert. This is not browser interaction evidence. <a href="index.html">Artifact index</a></p>${html}</main></html>`);
    const connection = document.connections.find((c) => c.id === id);
    write(`${id}.svg`, renderToStaticMarkup(React.createElement(Rp1ConnectionGraph, { connection, selectedPartId: part, onSelectNode: () => {} })));
  }
  write('index.html', '<!doctype html><html lang="en"><meta charset="utf-8"><title>RP1 connection exports</title><h1>Frozen RP1 / AD1 v2 connection exports</h1><p>Source-defined concept diagrams and recorded evidence. Not CAD, accepted design, browser screenshots or interaction proof.</p><ul><li><a href="fin-root.html">Fin-root connection and evidence</a></li><li><a href="recovery.html">Recovery attachment and evidence</a></li><li><a href="fin-root.svg">Fin relationship SVG</a></li><li><a href="recovery.svg">Recovery relationship SVG</a></li></ul>');
  fs.writeFileSync(`${output}/manifest.json`, JSON.stringify({ configuration: document.configuration, input, input_sha256: hash(fs.readFileSync(input)), sources: document.sources, drawings: document.drawings, files, browser_verified: false, interactions_verified: false, scope: 'Actual React/SVG markup export only; no image rendering, browser, CAD or calculation.' }, null, 2) + '\n');
  console.log(`${output}/index.html (${files.length} hashed artifacts)`);
} finally { await server.close(); }
