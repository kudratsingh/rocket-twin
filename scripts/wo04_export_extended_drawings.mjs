/** Offline export of the actual A–F React views. No browser, CAD or physics. */
import { createServer } from "../web/node_modules/vite/dist/node/index.js";
import postcss from "../web/node_modules/postcss/lib/postcss.mjs";
import React from "../web/node_modules/react/index.js";
import { renderToStaticMarkup } from "../web/node_modules/react-dom/server.node.js";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve, relative } from "node:path";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { performance } from "node:perf_hooks";
import assert from "node:assert/strict";
const ROOT = resolve(import.meta.dirname, "..");
const OUT = resolve(ROOT, "output/engineering-workbench-extended");
const recordArgIndex = process.argv.indexOf("--record-dir");
assert.ok(
  recordArgIndex < 0 || process.argv[recordArgIndex + 1],
  "--record-dir requires a path",
);
const RUN = resolve(
  ROOT,
  recordArgIndex < 0
    ? "build/wo04-extended-drawings"
    : process.argv[recordArgIndex + 1],
);
assert.ok(
  recordArgIndex < 0 || !existsSync(resolve(RUN, "record.json")),
  "Explicit archive record already exists; choose a new revision directory",
);
const LEGACY = "runs/wo04-walkthrough-export-20261102-v4/executed-script.mjs";
const LEGACY_SHA =
  "62085e1ce6eb0f1d21415ce34885cd0c4e6a2e850ae2147a7246bb5e20e698b3";
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
assert.equal(
  hash(readFileSync(resolve(ROOT, LEGACY))),
  LEGACY_SHA,
  "Archived V4 copied helper identity remains unchanged",
);
const basePath = "web/public/engineering-workbench/g80-c1.json";
const dataPath = "web/public/engineering-workbench/g80-extended.json";
const baseRaw = readFileSync(resolve(ROOT, basePath)),
  dataRaw = readFileSync(resolve(ROOT, dataPath));
const base = JSON.parse(baseRaw),
  extended = JSON.parse(dataRaw);
assert.equal(
  base.identity.specification_sha256,
  extended.identity.specification_sha256,
);
assert.equal(base.identity.cad_revision, null);
assert.equal(extended.identity.cad_revision, null);
for (const source of extended.generated_from)
  assert.equal(
    hash(readFileSync(resolve(ROOT, source.path))),
    source.sha256,
    source.path,
  );
mkdirSync(OUT, { recursive: true });
mkdirSync(RUN, { recursive: true });
const cssFiles = ["web/src/workbench/extensionViews.css"];
const esc = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
const unesc = (value) =>
  value.replace(
    /&#x([0-9a-f]+);|&#([0-9]+);|&(quot|apos|amp|lt|gt);/gi,
    (_, hex, dec, name) =>
      hex
        ? String.fromCodePoint(parseInt(hex, 16))
        : dec
          ? String.fromCodePoint(+dec)
          : { quot: '"', apos: "'", amp: "&", lt: "<", gt: ">" }[
              name.toLowerCase()
            ],
  );
const wrap = (value, count = 120) => {
  const lines = [];
  for (const word of String(value).split(/\s+/)) {
    if (!lines.length || lines.at(-1).length + word.length + 1 > count)
      lines.push(word);
    else lines[lines.length - 1] += ` ${word}`;
  }
  return lines;
};
// Adapted trusted markup/CSS helper from pinned V4 exporter; exact source hash above.
// Tiny tree/parser for trusted React static markup. No browser DOM or script evaluation.
function parseMarkup(markup) {
  const root = { tag: "#root", attrs: {}, children: [], parent: null };
  let current = root;
  const token = /<\/?[A-Za-z][^>]*>|[^<]+/g;
  for (const match of markup.matchAll(token)) {
    const value = match[0];
    if (!value.startsWith("<")) {
      current.children.push({ text: value });
      continue;
    }
    if (value.startsWith("</")) {
      current = current.parent ?? root;
      continue;
    }
    const name = /^<([^\s/>]+)/.exec(value)[1];
    const attrs = {};
    for (const entry of value.matchAll(/([\w:-]+)="([^"]*)"/g))
      attrs[entry[1]] = unesc(entry[2]);
    const node = { tag: name, attrs, children: [], parent: current };
    current.children.push(node);
    if (
      !value.endsWith("/>") &&
      !["input", "br", "img", "meta", "link", "hr"].includes(name)
    )
      current = node;
  }
  return root;
}
function allNodes(node) {
  return [
    node,
    ...(node.children?.filter((child) => child.tag).flatMap(allNodes) ?? []),
  ];
}
const inherited = [
  "color",
  "fill",
  "fill-opacity",
  "stroke",
  "stroke-opacity",
  "stroke-width",
  "stroke-dasharray",
  "stroke-linecap",
  "stroke-linejoin",
  "font-family",
  "font-size",
  "font-weight",
  "font-style",
  "text-anchor",
  "letter-spacing",
];
const portable = new Set([
  ...inherited,
  "opacity",
  "vector-effect",
  "paint-order",
]);
const defaults = {
  color: "#dce8ee",
  fill: "#000000",
  stroke: "none",
  "fill-opacity": "1",
  "stroke-opacity": "1",
  "stroke-width": "1",
  "font-family": "Helvetica, Arial, sans-serif",
  "font-size": "13px",
  "font-weight": "400",
  "text-anchor": "start",
};
const rules = [];
for (const path of cssFiles) {
  postcss.parse(readFileSync(resolve(ROOT, path), "utf8")).walkRules((rule) => {
    if (rule.parent.type !== "root") return; // Responsive layout rules are unrelated to SVG content.
    for (const selector of rule.selectors) {
      if (/:(?:hover|focus|first|last|nth|not|has)/.test(selector)) continue;
      const specificity =
        (selector.match(/#[\w-]+/g)?.length ?? 0) * 100 +
        (selector.match(/\.[\w-]+|\[[^\]]+\]/g)?.length ?? 0) * 10 +
        (selector.match(/(?:^|[\s>])[a-z]+/g)?.length ?? 0);
      const declarations = {};
      for (const child of rule.nodes)
        if (child.type === "decl") declarations[child.prop] = child.value;
      rules.push({
        selector: selector
          .replace(/\s*>\s*/g, " > ")
          .trim()
          .split(/\s+/),
        specificity,
        declarations,
        order: rules.length,
      });
    }
  });
}
rules.sort((a, b) => a.specificity - b.specificity || a.order - b.order);
function compound(node, token) {
  if (!node?.tag) return false;
  const tag = /^[a-zA-Z][\w-]*/.exec(token)?.[0];
  if (tag && node.tag !== tag) return false;
  const classes = (node.attrs.class ?? "").split(/\s+/);
  for (const entry of token.matchAll(/\.([\w-]+)/g))
    if (!classes.includes(entry[1])) return false;
  for (const entry of token.matchAll(/#([\w-]+)/g))
    if (node.attrs.id !== entry[1]) return false;
  for (const entry of token.matchAll(/\[([\w-]+)(?:=["']?([^\]"']+)["']?)?\]/g))
    if (
      !(entry[1] in node.attrs) ||
      (entry[2] != null && node.attrs[entry[1]] !== entry[2])
    )
      return false;
  return true;
}
function matches(node, tokens, index = tokens.length - 1) {
  if (!compound(node, tokens[index])) return false;
  if (!index) return true;
  if (tokens[index - 1] === ">") return matches(node.parent, tokens, index - 2);
  for (let parent = node.parent; parent; parent = parent.parent)
    if (matches(parent, tokens, index - 1)) return true;
  return false;
}
function styleTree(root) {
  function visit(node, parentStyle = defaults) {
    if (!node.tag) return;
    const style = { ...defaults };
    for (const [key, value] of Object.entries(parentStyle))
      if (inherited.includes(key) || key.startsWith("--")) style[key] = value;
    for (const [key, value] of Object.entries(node.attrs))
      if (portable.has(key)) style[key] = value;
    for (const rule of rules)
      if (matches(node, rule.selector)) Object.assign(style, rule.declarations);
    if (node.attrs.style)
      for (const decl of node.attrs.style.split(";")) {
        const pos = decl.indexOf(":");
        if (pos > 0)
          style[decl.slice(0, pos).trim()] = decl.slice(pos + 1).trim();
      }
    for (const [key, value] of Object.entries(style)) {
      let resolved = value;
      for (
        let iteration = 0;
        iteration < 5 && resolved.includes("var(");
        iteration++
      )
        resolved = resolved.replace(
          /var\((--[\w-]+)(?:,\s*([^)]*))?\)/g,
          (_, name, fallback) => style[name] ?? fallback ?? "",
        );
      if (resolved === "currentColor") resolved = style.color;
      if (portable.has(key) && resolved !== "inherit")
        node.attrs[key] = resolved;
    }
    delete node.attrs.style;
    for (const child of node.children ?? []) visit(child, style);
  }
  visit(root);
}
function serialize(node) {
  if (!node.tag) return node.text;
  return `<${node.tag}${Object.entries(node.attrs)
    .map(([key, value]) => ` ${key}="${esc(value)}"`)
    .join("")}>${(node.children ?? []).map(serialize).join("")}</${node.tag}>`;
}
function extract(markup) {
  const root = parseMarkup(markup);
  styleTree(root);
  return allNodes(root).filter(
    (node) => node.tag === "svg" && !hasSvgAncestor(node),
  );
}
function hasSvgAncestor(node) {
  for (let parent = node.parent; parent; parent = parent.parent)
    if (parent.tag === "svg") return true;
  return false;
}
function normalizeIds(svg) {
  const replacements = new Map();
  for (const node of allNodes(svg))
    if (node.attrs.id) {
      const old = node.attrs.id;
      const id = old.replace(/[^a-zA-Z0-9_.-]/g, "_");
      replacements.set(old, id);
      node.attrs.id = id;
    }
  for (const node of allNodes(svg)) {
    for (const [key, value] of Object.entries(node.attrs)) {
      let normalized = value;
      for (const [before, after] of replacements)
        normalized = normalized
          .replaceAll(`url(#${before})`, `url(#${after})`)
          .replaceAll(`#${before}`, `#${after}`);
      node.attrs[key] = normalized;
    }
  }
}
// This component's exact marker template and cubic source edge are recognized;
// any different pattern stops instead of guessing a direction or marker scale.
function flattenExtensionMarkers(svg) {
  const markers = new Map(
    allNodes(svg)
      .filter((node) => node.tag === "marker")
      .map((node) => [node.attrs.id, node]),
  );
  let count = 0;
  for (const parent of allNodes(svg))
    for (const node of [...(parent.children ?? [])]) {
      if (node.tag !== "path" || !node.attrs["marker-end"]) continue;
      const ref = /^url\(#([^)]*)\)$/.exec(node.attrs["marker-end"]);
      const marker = ref && markers.get(ref[1]);
      const template = marker?.children.find((child) => child.tag === "path");
      const tokens = node.attrs.d.match(
        /[A-Za-z]|[-+]?(?:\d*\.)?\d+(?:e[-+]?\d+)?/gi,
      );
      if (
        !marker ||
        !ref[1].startsWith("ext-") ||
        marker.attrs.orient !== "auto" ||
        marker.attrs.viewBox !== "0 0 10 10" ||
        marker.attrs.markerWidth !== "7" ||
        marker.attrs.markerHeight !== "7" ||
        marker.attrs.refX !== "9" ||
        marker.attrs.refY !== "5" ||
        (marker.attrs.markerUnits ?? "strokeWidth") !== "strokeWidth" ||
        template?.attrs.d !== "M0,0L10,5L0,10Z" ||
        tokens?.length !== 10 ||
        tokens[0] !== "M" ||
        tokens[3] !== "C"
      ) {
        const issue = {
          result: "stopped_unsupported_svg_pattern",
          path: node.attrs,
          marker: marker?.attrs ?? null,
        };
        writeFileSync(
          resolve(RUN, "portability-stop.json"),
          JSON.stringify(issue, null, 2) + "\n",
        );
        throw new Error(
          "Unsupported extension marker/path; no direction approximated",
        );
      }
      const end = [+tokens[8], +tokens[9]],
        tangent = [end[0] - +tokens[6], end[1] - +tokens[7]];
      const factor = 0.7 * Number(node.attrs["stroke-width"]);
      assert.ok(
        Number.isFinite(factor) && factor > 0 && Math.hypot(...tangent) > 0,
      );
      const head = {
        tag: "path",
        attrs: {
          ...template.attrs,
          transform: `translate(${end[0]} ${end[1]}) rotate(${(Math.atan2(tangent[1], tangent[0]) * 180) / Math.PI}) scale(${factor}) translate(-9 -5)`,
          "data-offline-marker-head": "true",
          "data-source-marker-id": ref[1],
        },
        children: [],
        parent,
      };
      parent.children.splice(parent.children.indexOf(node) + 1, 0, head);
      delete node.attrs["marker-end"];
      count++;
    }
  return count;
}
const text = (x, y, value, size = 13, color = "#d2e4ef", extra = "") =>
  `<text x="${x}" y="${y}" font-family="Helvetica,Arial,sans-serif" font-size="${size}" fill="${color}" ${extra}>${esc(value)}</text>`;
const artifacts = [];
const warnings = [];
const ssr = [];
const modes = [
  "comparison",
  "recovery",
  "thermal",
  "electrical",
  "assembly",
  "requirements",
];
const notes = {
  comparison: [
    "C1 is frozen and preliminary. All other supplied candidates are separate stopped comparisons. A/B architectures are concept / NOT ADMITTED; no replacement C1 recovery geometry, detailed solids or full intrinsic inertia is supplied.",
    "Mass/margin positions use saved cases only. Linked selections refer to existing source components, not adoption of changed candidates.",
  ],
  recovery: [
    "Recovery topology and packing/extraction steps are source illustrations, not qualified finished loops, equal load sharing or verified swept access.",
    "Spacing and arrow length are schematic; actual packing, extraction, chafe, hot strength and upper endpoint remain unresolved.",
  ],
  thermal: [
    "Current interface temperatures and compatible C1 spatial fields are unavailable. Historical thermal records are incompatible scalar metrics, not current C1 temperature predictions.",
    "No time-series samples exist in this export; no interpolated histories or spatial fields are fabricated.",
  ],
  electrical: [
    "Only recorded nets are connected. Exact unavailable pins and hardware details remain null; planned control blocks do not imply implemented or flight-qualified PID/RL.",
    "Independent recovery power is a recorded design feature; its full installed wiring, arming, retention and test requirements remain open.",
  ],
  assembly: [
    "Layer separation and sequence spacing are illustrative. Mating contact, tool access, nozzle passage, packed extraction and actual removal paths remain unverified.",
  ],
  requirements: [
    "Read-only requirement-to-part/evidence topology. Required physical verification remains owner work; this map records no new test completion or release.",
  ],
};
function outputSvg(svg, mode, index) {
  normalizeIds(svg);
  const heads = flattenExtensionMarkers(svg);
  const viewBox = svg.attrs.viewBox.split(/\s+/).map(Number);
  const width = Math.max(1100, viewBox[2]);
  const sourceHeight = viewBox[3];
  const titleNode = svg.children.find((node) => node.tag === "title");
  const title = unesc(
    titleNode?.children.map((child) => child.text ?? "").join("") ??
      `${mode} drawing ${index + 1}`,
  );
  const id = `${mode}-${String(index + 1).padStart(2, "0")}`;
  const lines = [];
  let y = 31;
  for (const [value, size, color] of [
    [title, 21, "#eef8ff"],
    [
      `${extended.label} · OFFLINE DRAWING · preliminary / acceptance open`,
      12,
      "#e2bf8c",
    ],
    [
      `Configuration: ${extended.identity.configuration_id} · complete C1 CAD: unavailable`,
      12,
      "#c7d9e5",
    ],
    [
      `Specification SHA-256: ${extended.identity.specification_sha256}`,
      10,
      "#b1ccdd",
    ],
    [`Frame: ${extended.identity.frame}`, 11, "#b1ccdd"],
    [`Units: ${extended.identity.units}`, 11, "#b1ccdd"],
  ]) {
    const limit = Math.min(120, Math.floor((width - 48) / (size * 0.7)));
    for (const line of wrap(value, limit)) {
      assert.ok(line.length <= limit);
      lines.push({ value: line, size, color, y });
      y += size + 7;
    }
    y += 3;
  }
  const drawingY = y + 18;
  const scale = (width - 40) / viewBox[2];
  const drawingHeight = sourceHeight * scale;
  const footerNotes = [
    ...notes[mode],
    "Offline rendering is not browser acceptance, physical qualification, construction release or flight acceptance.",
  ];
  const footerLines = footerNotes.flatMap((note) => wrap(note, 125));
  let footerY = drawingY + drawingHeight + 25;
  const sourceLines = extended.generated_from.flatMap((source) => [
    `${source.id}: ${source.path}`,
    `SHA-256 ${source.sha256}`,
  ]);
  const height =
    footerY + footerLines.length * 17 + sourceLines.length * 14 + 90;
  const selection = {
    selected_part_id: null,
    candidate_id:
      mode === "comparison" ? extended.candidate_comparison[0]?.id : null,
    assembly_joint_id:
      mode === "assembly" ? extended.assembly.joints[0]?.id : null,
    thermal_view:
      mode === "thermal" ? "current_interfaces_and_scalar_history" : null,
  };
  const metadata = {
    id,
    title,
    mode,
    schema_version: extended.schema_version,
    document_id: extended.id,
    identity: extended.identity,
    status: extended.status,
    source_count: extended.generated_from.length,
    sources: extended.generated_from,
    inputs: [
      { path: basePath, sha256: hash(baseRaw) },
      { path: dataPath, sha256: hash(dataRaw) },
    ],
    selection_state: selection,
    representation:
      "Actual saved React SVG in offline static selection state; portable styles and exact source marker templates flattened to explicit paths",
    explicit_arrowhead_count: heads,
    browser_verified: false,
    engineering_accepted: false,
    exporter_sha256: hash(readFileSync(import.meta.filename)),
    helper_source: { path: LEGACY, sha256: LEGACY_SHA },
  };
  let out = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="export-title export-desc"><title id="export-title">${esc(title)}</title><desc id="export-desc">${esc(footerNotes.join(" "))}</desc><metadata>${esc(JSON.stringify(metadata))}</metadata><rect width="${width}" height="${height}" fill="#101e29"/>`;
  for (const line of lines)
    out += text(
      24,
      line.y,
      line.value,
      line.size,
      line.color,
      'data-export-header="true"',
    );
  svg.attrs.x = "20";
  svg.attrs.y = String(drawingY);
  svg.attrs.width = String(width - 40);
  svg.attrs.height = String(drawingHeight);
  svg.attrs.xmlns = "http://www.w3.org/2000/svg";
  out += serialize(svg);
  for (const line of footerLines) {
    out += text(24, footerY, line, 12);
    footerY += 17;
  }
  footerY += 22;
  out += text(
    24,
    footerY,
    "Frozen source identity · full metadata preserved in every SVG and PNG sidecar",
    12,
    "#8fc8e3",
  );
  footerY += 20;
  for (const line of sourceLines) {
    out += text(24, footerY, line, 9, "#a8c3d4");
    footerY += 14;
  }
  out += "</svg>\n";
  assert.ok(
    !/var\(|currentColor|marker-end=|<script\b|<foreignObject\b/.test(out),
  );
  assert.ok(!/="(?:NaN|Infinity|undefined)"/.test(out));
  writeFileSync(resolve(OUT, `${id}.svg`), out);
  artifacts.push({
    id,
    title,
    mode,
    path: relative(ROOT, resolve(OUT, `${id}.svg`)),
    sha256: hash(out),
    width,
    height,
    svg_bytes: Buffer.byteLength(out),
    explicit_arrowhead_count: heads,
    selection_state: selection,
  });
}
const originalError = console.error;
console.error = (...args) => warnings.push(args.map(String).join(" "));
let server;
try {
  server = await createServer({
    configFile: false,
    root: resolve(ROOT, "web"),
    server: { middlewareMode: true, hmr: false },
    appType: "custom",
  });
  const { ExtensionViews } = await server.ssrLoadModule(
    "/src/workbench/ExtensionViews.tsx",
  );
  for (const mode of modes) {
    const started = performance.now();
    const html = renderToStaticMarkup(
      React.createElement(ExtensionViews, {
        document: base,
        extended,
        mode,
        selectedPartId: null,
        onSelectPart: () => {},
        onOpenJoint: () => {},
      }),
    );
    const elapsed = performance.now() - started;
    const graphics = extract(html);
    ssr.push({
      mode,
      elapsed_ms: elapsed,
      markup_bytes: Buffer.byteLength(html),
      svg_count: graphics.length,
    });
    graphics.forEach((svg, index) => outputSvg(svg, mode, index));
  }
} finally {
  console.error = originalError;
  if (server) await server.close();
}
assert.equal(artifacts.length, 11);
assert.equal(hash(readFileSync(resolve(ROOT, LEGACY))), LEGACY_SHA);
const sourceCode = [
  "scripts/wo04_export_extended_drawings.mjs",
  "web/src/workbench/ExtensionViews.tsx",
  "web/src/workbench/extensionViews.css",
  "web/src/workbench/extendedTypes.ts",
];
const graphs = [
  extended.recovery.topology,
  extended.thermal.topology,
  extended.thermal.current_interfaces,
  extended.electrical.topology,
  extended.electrical.control_blocks,
  extended.requirements,
];
const manifest = {
  schema_version: "1.0.0",
  created_at_utc: new Date().toISOString(),
  id: extended.id,
  identity: extended.identity,
  sources: extended.generated_from,
  inputs: [
    { path: basePath, sha256: hash(baseRaw), bytes: baseRaw.length },
    { path: dataPath, sha256: hash(dataRaw), bytes: dataRaw.length },
  ],
  graph_data_bytes: Buffer.byteLength(JSON.stringify(graphs)),
  graph_node_count: graphs.reduce((sum, graph) => sum + graph.nodes.length, 0),
  graph_edge_count: graphs.reduce((sum, graph) => sum + graph.edges.length, 0),
  implementation: sourceCode.map((path) => ({
    path,
    sha256: hash(readFileSync(resolve(ROOT, path))),
  })),
  copied_helper_source: { path: LEGACY, sha256: LEGACY_SHA },
  ssr,
  artifacts,
};
writeFileSync(
  resolve(OUT, "source-manifest.json"),
  JSON.stringify(manifest, null, 2) + "\n",
);
writeFileSync(
  resolve(RUN, "source-manifest.json"),
  JSON.stringify(manifest, null, 2) + "\n",
);
const nativeHelper =
  "runs/wo04-offline-render-feasibility-20261102-v4/native_image_document.swift";
const nativeCache = relative(ROOT, resolve(RUN, "swift-module-cache"));
const wrapper = String.raw`import json,sys,time,subprocess,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image,ImageDraw
root=Path(sys.argv[1]);output=Path(sys.argv[2]);run=Path(sys.argv[3]);manifest=json.loads((output/'source-manifest.json').read_text());ns={'s':'http://www.w3.org/2000/svg'}
for artifact in manifest['artifacts']:
 raw=(root/artifact['path']).read_bytes();tree=ET.fromstring(raw)
 assert hashlib.sha256(raw).hexdigest()==artifact['sha256']
 assert tree.find('s:title',ns).text and tree.find('s:desc',ns).text
 meta=json.loads(tree.find('s:metadata',ns).text);assert len(meta['sources'])==len(manifest['sources']) and meta['identity']['cad_revision'] is None and not meta['browser_verified']
 assert all(len(''.join(t.itertext()))<=120 for t in tree.findall('s:text',ns) if t.get('data-export-header')=='true')
 assert 'marker-end=' not in raw.decode() and 'var(' not in raw.decode() and 'currentColor' not in raw.decode()
start=time.monotonic();rendered=[]
for artifact in manifest['artifacts']:
 remaining=120-(time.monotonic()-start)
 if remaining<=0: raise TimeoutError('Full native render120s budget exhausted')
 svg=root/artifact['path'];png=output/(artifact['id']+'.png')
 command=['/usr/bin/swift','-module-cache-path',str(root/sys.argv[5]),str(root/sys.argv[4]),str(svg),str(png)]
 result=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=remaining,check=False)
 if result.returncode: raise RuntimeError(json.dumps({'id':artifact['id'],'exit_code':result.returncode,'stderr':result.stderr}))
 digest=hashlib.sha256(png.read_bytes()).hexdigest();image=Image.open(png)
 sidecar={'source_svg':artifact['path'],'source_svg_sha256':artifact['sha256'],'png_sha256':digest,'identity':manifest['identity'],'sources':manifest['sources'],'selection_state':artifact['selection_state'],'browser_verified':False,'engineering_accepted':False}
 png.with_suffix('.metadata.json').write_text(json.dumps(sidecar,indent=2)+'\n')
 rendered.append({'id':artifact['id'],'path':str(png.relative_to(root)),'sha256':digest,'dimensions':list(image.size),'stdout':result.stdout})
render_elapsed=time.monotonic()-start
thumbs=[]
for artifact in rendered:
 image=Image.open(root/artifact['path']).convert('RGB');image.thumbnail((420,480));tile=Image.new('RGB',(450,525),'#101e29');tile.paste(image,((450-image.width)//2,35));ImageDraw.Draw(tile).text((12,10),artifact['id'],fill='#dcebf5');thumbs.append(tile)
sheet=Image.new('RGB',(450*3,525*((len(thumbs)+2)//3)),'#101e29')
for index,tile in enumerate(thumbs):sheet.paste(tile,((index%3)*450,(index//3)*525))
sheet.save(output/'contact-sheet.png')
record={'result':'native_render_complete_pending_visual_inspection','render_elapsed_seconds':render_elapsed,'maximum_full_render_seconds':120,'renderer':'Existing documented AppKit image-document snapshot helper','renderer_helper_path':sys.argv[4],'renderer_helper_sha256':hashlib.sha256((root/sys.argv[4]).read_bytes()).hexdigest(),'renderer_attempts':1,'rendered':rendered,'xml_and_portability_checks':'passed11SVGs','visual_inspection':[],'browser_used':False,'physics_run':False}
(run/'native-render.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'result':record['result'],'rendered':len(rendered),'elapsed_seconds':render_elapsed}))`;
let native;
try {
  native = JSON.parse(
    execFileSync(
      resolve(ROOT, ".venv/bin/python"),
      ["-c", wrapper, ROOT, OUT, RUN, nativeHelper, nativeCache],
      { encoding: "utf8", timeout: 125000 },
    ),
  );
} catch (error) {
  writeFileSync(
    resolve(RUN, "native-render-stop.json"),
    JSON.stringify(
      {
        result: "stopped_native_render",
        message: error.message,
        stderr: String(error.stderr ?? ""),
        budget_seconds: 120,
        browser_used: false,
      },
      null,
      2,
    ) + "\n",
  );
  throw error;
}
let index = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Extended engineering drawings · offline review</title><style>body{font:16px/1.6 system-ui;background:#101e29;color:#deebf4;max-width:1250px;margin:auto;padding:25px}a{color:#92d5ee}.notice{border-left:3px solid #d9b47e;background:#2c281f;padding:15px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}article{border:1px solid #486579;background:#182d3c;padding:15px;border-radius:7px}img{display:block;width:100%;height:260px;object-fit:contain;background:#101e29}code{font-size:12px;overflow-wrap:anywhere}</style><h1>Extended engineering views · offline review</h1><p class="notice">Actual saved React drawings, statically exported and rasterized with installed AppKit. C1 remains preliminary and frozen; stopped candidates remain separate. These are not browser screenshots or engineering acceptance. All unavailable pins, inertia and current thermal results remain unavailable.</p><p>Specification <code>${esc(extended.identity.specification_sha256)}</code> · ${extended.generated_from.length} source hashes. <a href="source-manifest.json">Source/artifact manifest</a> · <a href="contact-sheet.png">Contact sheet</a></p><div class="grid">`;
for (const artifact of artifacts)
  index += `<article><h2>${esc(artifact.title)}</h2><a href="${artifact.id}.png"><img src="${artifact.id}.png" alt="Offline ${esc(artifact.title)} preview; open for full resolution"></a><p><a href="${artifact.id}.svg">Standalone SVG</a> · <a href="${artifact.id}.png">Full PNG</a> · <a href="${artifact.id}.metadata.json">PNG source metadata</a></p></article>`;
index += "</div></html>\n";
writeFileSync(resolve(OUT, "index.html"), index);
const record = {
  schema_version: "1.0.0",
  result: "exports_and_native_render_complete_pending_visual_inspection",
  command: "node scripts/wo04_export_extended_drawings.mjs",
  artifact_count: artifacts.length,
  source_count: extended.generated_from.length,
  data_bytes: dataRaw.length,
  graph_data_bytes: manifest.graph_data_bytes,
  graph_node_count: manifest.graph_node_count,
  graph_edge_count: manifest.graph_edge_count,
  ssr,
  ssr_elapsed_total_ms: ssr.reduce((sum, item) => sum + item.elapsed_ms, 0),
  native,
  archived_v4_helper_unchanged:
    hash(readFileSync(resolve(ROOT, LEGACY))) === LEGACY_SHA,
  archived_v4_sha256: LEGACY_SHA,
  warnings,
  visual_inspection: [],
  limits: [
    "Static offline selection states only, not browser runtime/interaction/FPS measurements.",
    "No physical calculations, current temperature curves or fields, guessed pins or new inertia tensors.",
    "Known extension triangle/cubic pattern only; unsupported patterns stop explicitly.",
    "Contact sheet is an overview; representative full-size image observations are recorded separately.",
  ],
};
writeFileSync(
  resolve(RUN, "record.json"),
  JSON.stringify(record, null, 2) + "\n",
);
console.log(
  JSON.stringify({
    result: record.result,
    svgs: artifacts.length,
    data_bytes: record.data_bytes,
    graph_data_bytes: record.graph_data_bytes,
    ssr_ms: record.ssr_elapsed_total_ms,
    render_seconds: native.elapsed_seconds,
    record: relative(ROOT, resolve(RUN, "record.json")),
  }),
);
