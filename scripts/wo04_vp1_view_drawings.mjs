/** Export the actual VP1 React view offline; never generates engineering geometry. */
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { resolve, relative } from "node:path";
import React from "../web/node_modules/react/index.js";
import { renderToStaticMarkup } from "../web/node_modules/react-dom/server.node.js";
import { createServer } from "../web/node_modules/vite/dist/node/index.js";

const root = resolve(import.meta.dirname, "..");
const out = resolve(root, "output/vp1-workbench-20261106");
const input = "web/public/engineering-workbench/rp1-validation.json";
const helper =
  "runs/wo04-offline-render-feasibility-20261102-v4/native_image_document.swift";
const attemptPath =
  "docs/studies/vp1-workbench-20261106/native-render-attempt.json";
const attempt = JSON.parse(readFileSync(resolve(root, attemptPath), "utf8"));
assert.equal(attempt.remaining_native_attempts, 0);
assert.ok(
  !process.argv.includes("--native"),
  "Native packet stopped; this exporter only produces SVG/HTML.",
);
const code = [
  "web/src/workbench/Vp1ValidationView.tsx",
  "web/src/workbench/vp1Validation.ts",
  "web/src/workbench/vp1Validation.css",
  "scripts/wo04_vp1_view_drawings.mjs",
];
const sha = (data) => createHash("sha256").update(data).digest("hex");
const fileSha = (path) => sha(readFileSync(resolve(root, path)));
const source = (path) => ({ path, sha256: fileSha(path) });
const esc = (v) =>
  String(v)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
const packet = JSON.parse(readFileSync(resolve(root, input), "utf8"));
assert.equal(packet.id, "RP1-VP1-inspection-preview-v1");
assert.equal(packet.parts.length, 9);
assert.equal(packet.messages.length, 5);
assert.ok(packet.stages.every((x) => x.status === "not-authorized"));
assert.ok(packet.parts.every((x) => x.status === "unverified"));
assert.deepEqual(packet.costs.all_in_usd, null);
for (const item of packet.sources)
  assert.equal(fileSha(item.path), item.sha256, item.path);
for (const message of packet.messages)
  assert.equal(
    readFileSync(resolve(root, message.source.path), "utf8"),
    message.text,
    message.source.path,
  );
mkdirSync(out, { recursive: true });
let server;
let markup;
try {
  server = await createServer({
    configFile: false,
    root: resolve(root, "web"),
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: "custom",
  });
  const view = await server.ssrLoadModule(
    "/src/workbench/Vp1ValidationView.tsx",
  );
  const types = await server.ssrLoadModule("/src/workbench/vp1Validation.ts");
  markup = renderToStaticMarkup(
    React.createElement(view.Vp1ValidationView, {
      snapshot: types.validateVp1Validation(packet),
    }),
  );
} finally {
  if (server) await server.close();
}
assert.match(markup, /VP1 validation package review/);
assert.doesNotMatch(markup, /VP1 review unavailable/);
const css = readFileSync(
  resolve(root, "web/src/workbench/vp1Validation.css"),
  "utf8",
);
writeFileSync(
  resolve(out, "view.html"),
  `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VP1 offline React view</title><style>body{font:16px/1.5 system-ui;background:#0c1620;color:#e1eaf0}a{color:#9edcff}${css}</style></head><body><p>OFFLINE static React snapshot. Controls are inert; browser interaction is unverified.</p>${markup}</body></html>\n`,
);
// Extract only SVGs emitted by the actual view. No replacement graph is constructed.
const svgs = [...markup.matchAll(/<svg\b[\s\S]*?<\/svg>/g)].map((m) => m[0]);
const artifacts = [];
// The bounded native attempt is stopped. Regeneration never retries it.
for (const [index, raw] of svgs.entries()) {
  assert.doesNotMatch(
    raw,
    /<script\b|<foreignObject\b|(?:NaN|Infinity|undefined)/,
  );
  const name = `vp1-graph-${index + 1}`;
  const svg = /<svg\b[^>]*\sxmlns=/.test(raw)
    ? raw
    : raw.replace(/^<svg\b/, '<svg xmlns="http://www.w3.org/2000/svg"');
  writeFileSync(resolve(out, `${name}.svg`), svg + "\n");
  artifacts.push({
    svg: source(`output/vp1-workbench-20261106/${name}.svg`),
    png: null,
  });
}
const skipNative = true;
const nativeSeconds = null;
const cards = artifacts
  .map(
    (item, i) =>
      `<section><h2>Actual React graphic ${i + 1}</h2><p><a href="${esc(item.svg.path.split("/").at(-1))}">Portable SVG</a> · PNG unavailable; source/XML checks only</p><img src="${esc(item.svg.path.split("/").at(-1))}" alt="Actual React VP1 source graphic; not visually verified"></section>`,
  )
  .join("");
const status = !artifacts.length
  ? "no_svg_in_actual_react_view"
  : skipNative
    ? "svg_only_native_render_unavailable"
    : "native_render_complete_pending_visual_inspection";
const manifest = {
  status,
  preview_id: packet.id,
  package: packet.package,
  configuration: packet.configuration,
  prepared_data: source(input),
  sources: packet.sources,
  rendered_sources: code.map(source),
  helper: source(helper),
  artifacts,
  native_render_seconds: skipNative ? null : nativeSeconds,
  native_render_limit_seconds: 90,
  native_render_attempt: source(attemptPath),
  native_render_note:
    "Reported initial 90-second stop produced no PNG; exact timing/output/cause unconfirmed. This export performs no native retry.",
  visual_inspection: [],
  browser_verified: false,
  engineering_accepted: false,
  note: "Offline SSR and SVG only; prior native attempt is recorded separately. Stages are not authorized, parts are conceptual and unverified, five drafts remain unsent.",
};
writeFileSync(
  resolve(out, "manifest.json"),
  JSON.stringify(manifest, null, 2) + "\n",
);
writeFileSync(
  resolve(out, "README.md"),
  `# VP1 offline React export\n\nIdentity: ${packet.id}. Actual React SSR snapshot; no browser interaction or engineering acceptance. All stages are not authorized; nine parts are conceptual and unverified, not current CAD. Five drafts remain UNSENT. Archived November 4 material prices: $236.75 room pilot and $269.49 conditional full reserve; all-in cost unavailable.\n\nGraphic export status: ${status}. ${skipNative ? "The bounded native attempt is preserved in its source record: no PNG, terminal output unavailable, exact time/cause unconfirmed. This export is SVG-only; no retry or visual acceptance." : `Native renderer time ${nativeSeconds.toFixed(3)} seconds of the 90-second aggregate limit.`} Inspect manifest.json for source hashes.\n`,
);
writeFileSync(
  resolve(out, "index.html"),
  `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VP1 offline gallery</title><style>body{font:16px/1.5 system-ui;background:#0c1620;color:#e1eaf0;margin:2rem auto;max-width:1100px;padding:0 1rem}a{color:#9edcff}img{max-width:100%;height:auto}</style></head><body><h1>VP1 offline React gallery</h1><p>OFFLINE — unperformed, not authorized and not adopted. Browser interaction and engineering acceptance remain unverified.</p><p><a href="view.html">Full static React view</a> · <a href="manifest.json">Source manifest</a> · <a href="README.md">Notes</a> · <a href="vp1-offline.zip">ZIP</a></p>${cards || "<p>The actual React view contains no SVG graphic; no substitute graphic has been fabricated.</p>"}</body></html>\n`,
);
const zip = resolve(out, "vp1-offline.zip");
rmSync(zip, { force: true });
const files = [
  "index.html",
  "view.html",
  "manifest.json",
  "README.md",
  ...artifacts.flatMap((x) => [
    x.svg.path.split("/").at(-1),
    ...(x.png ? [x.png.path.split("/").at(-1)] : []),
  ]),
];
execFileSync(
  "/usr/bin/zip",
  ["-q", "-j", zip, ...files.map((x) => resolve(out, x))],
  { timeout: 15000 },
);
execFileSync("/usr/bin/unzip", ["-t", zip], { timeout: 15000, stdio: "pipe" });
console.log(
  JSON.stringify({
    status,
    native_seconds: nativeSeconds,
    artifacts: artifacts.length,
    archive: {
      path: relative(root, zip),
      sha256: fileSha(relative(root, zip)),
      files,
    },
  }),
);
