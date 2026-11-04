/** Offline export of the actual RP1 React relationship graphs; no engineering calculations. */
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { resolve, relative } from "node:path";
import { performance } from "node:perf_hooks";
import React from "../web/node_modules/react/index.js";
import { renderToStaticMarkup } from "../web/node_modules/react-dom/server.node.js";
import { createServer } from "../web/node_modules/vite/dist/node/index.js";

const root = resolve(import.meta.dirname, "..");
const out = resolve(root, "output/rp1-integrated-walkthrough");
const preparedPath = "web/public/engineering-workbench/rp1-studies.json";
const helperPath =
  "runs/wo04-offline-render-feasibility-20261102-v4/native_image_document.swift";
const codePaths = [
  "web/src/workbench/Rp1StudyComparison.tsx",
  "web/src/workbench/rp1Studies.ts",
  "web/src/workbench/rp1StudyComparison.css",
  "scripts/wo04_rp1_studies_drawings.mjs",
];
const hash = (value) => createHash("sha256").update(value).digest("hex");
const fileHash = (path) => hash(readFileSync(resolve(root, path)));
const source = (path) => ({ path, sha256: fileHash(path) });
const esc = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
const number = (value, digits = 3) =>
  value === null ? "Unavailable" : Number(value).toFixed(digits);
const svgStyle = "<style>text{font-family:Arial,Helvetica,sans-serif}</style>";

function packageOut() {
  const zipPath = resolve(out, "rp1-studies-offline.zip");
  rmSync(zipPath, { force: true });
  const files = [
    "index.html",
    "view.html",
    "README.md",
    "manifest.json",
    "fp1-graph.svg",
    "fp1-graph.png",
    "fr1-graph.svg",
    "fr1-graph.png",
  ];
  execFileSync(
    "/usr/bin/zip",
    ["-q", "-j", zipPath, ...files.map((file) => resolve(out, file))],
    { timeout: 15000 },
  );
  return {
    path: relative(root, zipPath),
    sha256: fileHash(relative(root, zipPath)),
    members: files,
  };
}

function standaloneGraph(markup, study, preparedSha, renderedSources) {
  assert.match(markup, /^<svg\b[\s\S]*<\/svg>$/);
  assert.doesNotMatch(
    markup,
    /(?:="(?:NaN|Infinity|undefined)"|<script\b|<foreignObject\b)/,
  );
  const rootTag = markup.match(/^<svg([^>]*)>/);
  assert.ok(rootTag);
  const viewBox = rootTag[1].match(/viewBox="0 0 600 (\d+)"/);
  assert.ok(viewBox, "Actual React graph viewport changed");
  const attrs = rootTag[1]
    .replace(/\sviewBox="[^"]*"/, "")
    .replace(/\sclass="[^"]*"/, "");
  const graphChildren = markup.slice(rootTag[0].length, -6);
  const links = study.edges
    .map((edge, index) => {
      const y = 170 + index * 70;
      return `<g><circle cx="640" cy="${y - 5}" r="12" fill="#244358" stroke="#8fa6b9"/><text x="640" y="${y}" text-anchor="middle" font-size="13" fill="#e6eef5">${index + 1}</text><text x="665" y="${y - 1}" font-size="16" fill="#e6eef5">${esc(edge.from)} → ${esc(edge.to)}</text><text x="665" y="${y + 22}" font-size="14" fill="#abc0d0">${esc(edge.label)}</text></g>`;
    })
    .join("");
  const explanation = study.id.includes("FP1")
    ? `Reported ${number(study.displacement.reported_mm)} mm INCLUDES the unverified ${number(study.displacement.attachment_budget_mm)} mm attachment budget. No installed pass.`
    : `Reported ${number(study.displacement.reported_mm)} mm is a failed partial finite-support sensitivity. Complete installed movement unavailable.`;
  const metadata = {
    id: study.id,
    status: study.status,
    adopted: false,
    installed_accepted: false,
    source: study.source,
    prepared_sha256: preparedSha,
    rendered_sources: renderedSources,
    units: { movement: "mm", moment: "N m", mass: "g" },
    representation:
      "Actual React graph elements plus export-only source legend; relationship schematic, not CAD or stress map.",
    browser_verified: false,
    engineering_accepted: false,
  };
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="950" viewBox="0 0 1100 950" font-family="Arial,Helvetica,sans-serif"${attrs}>
<rect x="0" y="0" width="1100" height="950" fill="#101e29"/>${svgStyle}
${graphChildren}
<rect x="605" y="24" width="470" height="803" rx="8" fill="#14212e" stroke="#3d5367"/>
<text x="625" y="61" font-size="22" font-weight="bold" fill="#e6eef5">${esc(study.label)}</text>
<text x="625" y="91" font-size="15" font-weight="bold" fill="#f1c77e">UNACCEPTED · not adopted · installed acceptance false</text>
<text x="625" y="132" font-size="17" font-weight="bold" fill="#e6eef5">Relationship key from prepared packet</text>
${links}
<text x="625" y="707" font-size="16" font-weight="bold" fill="#f1c77e">Recorded movement: ${number(study.displacement.reported_mm)} mm</text>
<text x="625" y="736" font-size="15" fill="#abc0d0">Limit: ${number(study.displacement.limit_mm)} mm · mass credit ${number(study.mass.conditional_credit_g)} g conditional</text>
<text x="20" y="863" font-size="15" fill="#f1c77e">${esc(explanation)}</text>
<text x="20" y="896" font-size="13" fill="#abc0d0">Study ${esc(study.id)}</text>
<text x="20" y="923" font-size="12" fill="#abc0d0">Source SHA-256 ${esc(study.source.sha256)}</text>
<metadata>${esc(JSON.stringify(metadata))}</metadata>
</svg>\n`;
}

mkdirSync(out, { recursive: true });
if (process.argv.includes("--package-only")) {
  console.log(JSON.stringify(packageOut()));
  process.exit(0);
}
const preparedRaw = readFileSync(resolve(root, preparedPath));
const preparedSha = hash(preparedRaw);
const packet = JSON.parse(preparedRaw);
assert.equal(packet.schema_version, 1);
assert.equal(packet.id, "G80-F2-RP1-FP1-FR1-comparison-v1");
assert.equal(packet.source_configuration.id, "G80-F2-RP1-AD1-definition-v2");
assert.equal(
  fileHash(packet.source_configuration.path),
  packet.source_configuration.sha256,
);
assert.equal(packet.studies.length, 2);
for (const study of packet.studies) {
  assert.equal(study.adopted, false);
  assert.equal(study.installed_accepted, false);
  assert.equal(fileHash(study.source.path), study.source.sha256);
  for (const item of study.sources)
    if (item.sha256) assert.equal(fileHash(item.path), item.sha256, item.path);
}
const renderedSources = codePaths.map(source);
const warnings = [];
let server;
let rendered;
const originalError = console.error;
try {
  console.error = (...items) => warnings.push(items.map(String).join(" "));
  server = await createServer({
    configFile: false,
    root: resolve(root, "web"),
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: "custom",
  });
  const module = await server.ssrLoadModule(
    "/src/workbench/Rp1StudyComparison.tsx",
  );
  const types = await server.ssrLoadModule("/src/workbench/rp1Studies.ts");
  const snapshot = types.validateRp1Studies(packet);
  rendered = {
    graphs: snapshot.studies.map((study) => ({
      study,
      markup: renderToStaticMarkup(
        React.createElement(module.Rp1StudyGraph, {
          study,
          selected: study.nodes[0]?.id ?? null,
          onSelect() {},
        }),
      ),
    })),
    view: renderToStaticMarkup(
      React.createElement(module.Rp1StudyComparisonView, { snapshot }),
    ),
  };
} finally {
  console.error = originalError;
  if (server) await server.close();
}
const viewCss = readFileSync(
  resolve(root, "web/src/workbench/rp1StudyComparison.css"),
  "utf8",
);
writeFileSync(
  resolve(out, "view.html"),
  `<!doctype html><html lang="en"><meta charset="utf-8"><title>RP1 studies static workbench view</title><style>body{font:16px/1.5 system-ui;background:#101e29;color:#e6eef5;margin:20px auto;max-width:1400px}a{color:#9bd3e8}${viewCss}</style><p>Offline SSR snapshot of the actual React RP1 comparison view. Buttons and selection are static here; browser interaction is unverified.</p>${rendered.view}</html>\n`,
);
const nativeStart = performance.now();
mkdirSync(resolve(out, "swift-module-cache"), { recursive: true });
const artifacts = [];
for (let index = 0; index < rendered.graphs.length; index++) {
  const { study, markup } = rendered.graphs[index];
  const id = index === 0 ? "fp1-graph" : "fr1-graph";
  const svgPath = resolve(out, `${id}.svg`);
  const pngPath = resolve(out, `${id}.png`);
  const svg = standaloneGraph(markup, study, preparedSha, renderedSources);
  writeFileSync(svgPath, svg);
  const remaining = 120000 - (performance.now() - nativeStart);
  assert.ok(remaining > 1000, "RP1 native render batch exceeded 120 seconds");
  execFileSync(
    "/usr/bin/swift",
    [
      "-module-cache-path",
      resolve(out, "swift-module-cache"),
      resolve(root, helperPath),
      svgPath,
      pngPath,
    ],
    { timeout: Math.floor(remaining), stdio: "pipe" },
  );
  artifacts.push({
    id,
    study_id: study.id,
    source: study.source,
    svg: {
      path: relative(root, svgPath),
      sha256: fileHash(relative(root, svgPath)),
    },
    png: {
      path: relative(root, pngPath),
      sha256: fileHash(relative(root, pngPath)),
    },
  });
}
const nativeSeconds = (performance.now() - nativeStart) / 1000;
assert.ok(nativeSeconds <= 120);
const manifest = {
  result: "native_render_complete_pending_visual_inspection",
  identity: packet.id,
  status: packet.status,
  prepared_data: { path: preparedPath, sha256: preparedSha },
  source_configuration: packet.source_configuration,
  study_ids: packet.studies.map((study) => study.id),
  rendered_sources: renderedSources,
  helper: source(helperPath),
  artifacts,
  native_render_seconds: nativeSeconds,
  native_render_limit_seconds: 120,
  warnings,
  visual_inspection: [],
  browser_verified: false,
  engineering_accepted: false,
  limits: [
    "React SSR and AppKit native PNG only; no browser interaction or download acceptance.",
    "Graph arrows are source relationships, not CAD, stress maps, installed load sharing or physics.",
  ],
};
writeFileSync(
  resolve(out, "manifest.json"),
  JSON.stringify(manifest, null, 2) + "\n",
);
const cards = artifacts
  .map((item, index) => {
    const study = packet.studies[index];
    return `<article><h2>${esc(study.label)}</h2><p class="status">${esc(study.status)} · installed acceptance false</p><p>Reported ${number(study.displacement.reported_mm)} mm; recorded limit ${number(study.displacement.limit_mm)} mm; conditional mass credit ${number(study.mass.conditional_credit_g)} g. ${esc(study.displacement.note)}</p><p><code>${esc(study.id)}</code></p><p><a href="${item.id}.svg">Standalone SVG</a> · <a href="${item.id}.png">Native PNG</a></p><img src="${item.id}.png" alt="Offline actual React graph for ${esc(study.label)}"></article>`;
  })
  .join("");
writeFileSync(
  resolve(out, "index.html"),
  `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RP1 integrated study graphs</title><style>body{font:16px/1.5 system-ui;background:#101e29;color:#e6eef5;max-width:2200px;margin:auto;padding:24px}a{color:#9bd3e8}.status{color:#f1c77e;font-weight:bold}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}article{background:#14212e;border:1px solid #3d5367;border-radius:8px;padding:18px}img{width:100%;height:auto;border:1px solid #3d5367}code{overflow-wrap:anywhere}@media(max-width:1300px){.grid{grid-template-columns:1fr}}</style><h1>RP1 FP1 / FR1 actual workbench graphs</h1><p>Offline React SSR plus native AppKit images. Both studies remain unaccepted. The source labels and relationship graph come from the prepared RP1 packet; the legend and source footer are export annotations.</p><p><a href="view.html">Full static React view</a> · <a href="manifest.json">Source manifest</a> · <a href="README.md">Inspection notes</a> · <a href="rp1-studies-offline.zip">ZIP</a></p><div class="grid">${cards}</div></html>\n`,
);
writeFileSync(
  resolve(out, "README.md"),
  `# RP1 actual workbench graph export\n\nPrepared packet ${packet.id}; SHA-256 ${preparedSha}. React source, types and CSS hashes are in manifest.json.\n\nTwo actual Rp1StudyGraph React SVGs were rendered through Vite SSR. The standalones add only an export background, complete numbered edge key, source identity and quantitative caveat to the original graph elements. The full Rp1StudyComparisonView SSR markup is in view.html and is static.\n\nFP1 ${number(packet.studies[0].displacement.reported_mm)} mm includes the unverified ${number(packet.studies[0].displacement.attachment_budget_mm)} mm attachment budget. FR1 ${number(packet.studies[1].displacement.reported_mm)} mm is a failed partial finite-support sensitivity; complete installed movement is unavailable. Both are UNACCEPTED and neither mass credit is adopted.\n\nNative PNG visual inspection pending. This is offline evidence only, not browser/WebGL or installed engineering acceptance.\n`,
);
const archive = packageOut();
console.log(
  JSON.stringify({
    result: manifest.result,
    identity: packet.id,
    native_seconds: nativeSeconds,
    artifacts: artifacts.map((item) => item.id),
    archive,
  }),
);
