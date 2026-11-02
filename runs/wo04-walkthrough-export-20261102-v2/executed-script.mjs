/** Offline presentation export only. Reuses saved React SVGs; never runs CAD/physics/browser. */
import { createServer } from "../web/node_modules/vite/dist/node/index.js";
import postcss from "../web/node_modules/postcss/lib/postcss.mjs";
import React from "../web/node_modules/react/index.js";
import { renderToStaticMarkup } from "../web/node_modules/react-dom/server.node.js";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { resolve, relative } from "node:path";
import { createHash } from "node:crypto";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";

const ROOT = resolve(import.meta.dirname, "..");
const OUT = resolve(ROOT, "output/engineering-walkthrough");
const RUN = resolve(ROOT, "runs/wo04-walkthrough-export-20261102-v2");
const PREVIOUS_RUN = "runs/wo04-walkthrough-export-20261102-v1";
const INPUT = "web/public/engineering-workbench/g80-c1.json";
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const raw = readFileSync(resolve(ROOT, INPUT));
const document = JSON.parse(raw);
const esc = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
const unesc = (value) =>
  value.replace(
    /&#x([0-9a-f]+);|&#([0-9]+);|&(quot|apos|amp|lt|gt);/gi,
    (_, hex, decimal, named) =>
      hex
        ? String.fromCodePoint(parseInt(hex, 16))
        : decimal
          ? String.fromCodePoint(+decimal)
          : { quot: '"', apos: "'", amp: "&", lt: "<", gt: ">" }[
              named.toLowerCase()
            ],
  );
const number = (value, digits = 6) =>
  new Intl.NumberFormat("en", { maximumFractionDigits: digits }).format(value);
const wrap = (value, count = 120) => {
  const result = [];
  for (const word of String(value).split(/\s+/)) {
    if (!result.length || result.at(-1).length + word.length + 1 > count)
      result.push(word);
    else result[result.length - 1] += ` ${word}`;
  }
  return result;
};
const cssFiles = [
  "geometryViews.css",
  "massLaunchViews.css",
  "loadPathViews.css",
].map((name) => `web/src/workbench/${name}`);
const codeFiles = [
  ...cssFiles,
  ...[
    "GeometryViews.tsx",
    "MassLaunchViews.tsx",
    "LoadPathViews.tsx",
    "loadPathDisplay.ts",
    "types.ts",
    "exportSvg.ts",
  ].map((name) => `web/src/workbench/${name}`),
  "web/package-lock.json",
  "scripts/wo04_export_walkthrough_drawings.mjs",
];
for (const source of document.generated_from)
  assert.equal(
    hash(readFileSync(resolve(ROOT, source.path))),
    source.sha256,
    `Frozen source changed: ${source.path}`,
  );
assert.equal(
  document.identity.cad_revision,
  null,
  "This export is scoped to the preliminary C1 document, not complete detailed CAD",
);
mkdirSync(OUT, { recursive: true });
mkdirSync(RUN, { recursive: true });

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
  for (const node of allNodes(svg))
    for (const [key, value] of Object.entries(node.attrs))
      for (const [before, after] of replacements)
        node.attrs[key] = value
          .replaceAll(`url(#${before})`, `url(#${after})`)
          .replaceAll(`#${before}`, `#${after}`);
}
const artifacts = [];
const warnings = [];
function text(x, y, value, size = 13, color = "#c7d9e5", extra = "") {
  return `<text x="${x}" y="${y}" font-family="Helvetica,Arial,sans-serif" font-size="${size}" fill="${color}" ${extra}>${esc(value)}</text>`;
}
function writeDrawing(
  id,
  title,
  svg,
  notes = [],
  group = "Drawings",
  view = {},
) {
  normalizeIds(svg);
  const [, , width, height] = svg.attrs.viewBox.split(/\s+/).map(Number);
  assert.ok(
    Number.isFinite(width) && Number.isFinite(height),
    "Finite source viewBox",
  );
  const pageWidth = Math.max(width, 1100);
  const bodyScale = Math.min(1, (pageWidth - 40) / width);
  const headerFields = [
    [title, 22, "#edf7ff"],
    [
      `${document.label} · OFFLINE EXPORT · preliminary / engineering acceptance open`,
      13,
      "#e2bd86",
    ],
    [
      `Configuration: ${document.identity.configuration_id} · CAD revision: unavailable (not a complete detailed CAD assembly)`,
      12,
      "#c7d9e5",
    ],
    [
      `Specification SHA-256: ${document.identity.specification_sha256}`,
      11,
      "#c7d9e5",
    ],
    [`Frame: ${document.identity.frame}`, 11, "#c7d9e5"],
    [`Units: ${document.identity.units}`, 11, "#c7d9e5"],
  ];
  const headerLines = [];
  let headerY = 30;
  for (const [value, size, color] of headerFields) {
    const limit = Math.min(120, Math.floor((pageWidth - 48) / (size * 0.7)));
    for (const line of wrap(value, limit)) {
      assert.ok(
        line.length <= limit,
        "Every standalone header line fits its declared character bound",
      );
      headerLines.push({ value: line, size, color, y: headerY, limit });
      headerY += size + 7;
    }
    headerY += 3;
  }
  const bodyY = headerY + 16;
  const noteLines = notes.flatMap((note) =>
    wrap(note, Math.floor((pageWidth - 48) / 7)),
  );
  const footerY = bodyY + height * bodyScale + 26;
  const sources = document.generated_from.flatMap((source) => [
    `${source.id}: ${source.path}`,
    `SHA-256 ${source.sha256}`,
  ]);
  const pageHeight =
    footerY + noteLines.length * 18 + sources.length * 15 + 120;
  const metadata = {
    title,
    document_id: document.id,
    configuration_id: document.identity.configuration_id,
    specification_sha256: document.identity.specification_sha256,
    cad_revision: document.identity.cad_revision,
    status: document.status,
    frame: document.identity.frame,
    units: document.identity.units,
    representation:
      "Offline presentation drawing from saved React SVG/source data. Concept/envelope maturity; no complete C1 CAD or engineering acceptance.",
    view,
    input: { path: INPUT, sha256: hash(raw) },
    sources: document.generated_from,
    exporter_sha256: hash(readFileSync(import.meta.filename)),
    browser_verified: false,
    presentation_layout: {
      header_max_characters: 120,
      header_line_count: headerLines.length,
      drawing_y: bodyY,
      footer_y: footerY,
    },
  };
  let output = `<svg xmlns="http://www.w3.org/2000/svg" width="${pageWidth}" height="${pageHeight}" viewBox="0 0 ${pageWidth} ${pageHeight}" role="img" aria-labelledby="export-title export-description"><title id="export-title">${esc(title)}</title><desc id="export-description">${esc(`${document.label}. Preliminary concept/envelope drawing; engineering acceptance open. ${notes.join(" ")}`)}</desc><metadata>${esc(JSON.stringify(metadata))}</metadata><rect width="${pageWidth}" height="${pageHeight}" fill="#101e29"/>`;
  for (const line of headerLines)
    output += text(
      24,
      line.y,
      line.value,
      line.size,
      line.color,
      `data-export-header="true" data-character-limit="${line.limit}"`,
    );
  svg.attrs.x = String((pageWidth - width * bodyScale) / 2);
  svg.attrs.y = String(bodyY);
  svg.attrs.width = String(width * bodyScale);
  svg.attrs.height = String(height * bodyScale);
  svg.attrs.xmlns = "http://www.w3.org/2000/svg";
  output += serialize(svg);
  let py = footerY;
  for (const line of noteLines) {
    output += text(24, py, line, 12);
    py += 18;
  }
  py += 20;
  output += text(
    24,
    py,
    "Frozen source identity · full hashes also embedded in SVG metadata",
    13,
    "#98cde3",
  );
  py += 23;
  for (const line of sources) {
    output += text(24, py, line, 10, "#a6bfcd");
    py += 15;
  }
  output += text(
    24,
    py + 22,
    "Offline artifact export is not browser verification, physical qualification, construction release or flight acceptance.",
    12,
    "#dfbc8f",
  );
  output += "</svg>\n";
  assert.ok(
    !output.includes("var(") && !output.includes("currentColor"),
    "Portable colors fully resolved",
  );
  assert.ok(
    !/(?:="|,|\s)(?:NaN|Infinity)(?:[\s,"<]|$)/.test(output),
    "No non-finite output",
  );
  writeFileSync(resolve(OUT, `${id}.svg`), output);
  artifacts.push({
    id,
    title,
    group,
    path: relative(ROOT, resolve(OUT, `${id}.svg`)),
    width: pageWidth,
    height: pageHeight,
    sha256: hash(output),
    view,
    portable_style_attributes: true,
    browser_verified: false,
    header_line_count: headerLines.length,
    header_max_characters: Math.max(
      ...headerLines.map((line) => line.value.length),
    ),
    drawing_y: bodyY,
  });
}
const commonNotes = [
  "Concept outlines and component envelopes are sourced presentation graphics. Detailed C1 CAD is unavailable; the135 recorded parts/allocations are not135 CAD solids.",
  "Colors identify subsystems, not a solved stress/thermal/displacement field. Dashed/dotted outlines retain concept/envelope maturity. Contact, packing, clearances, joints, manufacturing and service remain unresolved.",
  "Subsystem colors follow source order: " +
    [...new Set(document.parts.map((part) => part.subsystem))]
      .map(
        (name, index) =>
          `${name} ${["#65c7df", "#b6a0ed", "#e9b86a", "#84c59a", "#e58f9c", "#91aee9"][index % 6]}`,
      )
      .join("; "),
];
const oldError = console.error;
console.error = (...args) => warnings.push(args.map(String).join(" "));
let server;
try {
  server = await createServer({
    configFile: false,
    root: resolve(ROOT, "web"),
    server: { middlewareMode: true, hmr: false },
    appType: "custom",
  });
  const components = {};
  for (const name of ["GeometryViews", "MassLaunchViews", "LoadPathViews"])
    components[name] = (
      await server.ssrLoadModule(`/src/workbench/${name}.tsx`)
    )[name];
  const render = (name, doc = document) =>
    extract(
      renderToStaticMarkup(
        React.createElement(components[name], {
          document: doc,
          selectedPartId: null,
          onSelectPart: () => {},
        }),
      ),
    );
  const geometry = render("GeometryViews");
  for (const [index, id, title, note] of [
    [
      0,
      "01-arrangement-side",
      "General arrangement · source-projected side",
      "Fins use source azimuth centerplanes projected onto axial /0° radial plane. Coincident far-fin projections overlap; panel thickness is unresolved. Nose outline is a simple envelope.",
    ],
    [
      1,
      "02-front-projection",
      "Front view · axial-station projection",
      "All source radii/fin azimuths projected looking aft; depth collapsed, not a nose rendering. Overlap does not establish contact.",
    ],
    [
      2,
      "03-motor-end-projection",
      "Motor-end view · aft projection",
      "Aft-joint, fin and motor envelopes projected looking forward. Depth collapsed; unrecorded openings omitted.",
    ],
    [
      3,
      "04-internal-section",
      "Full longitudinal internal section",
      "Shell walls are source section envelopes. Fin centerplanes are projected rather than a literal cut. Rectangles without inner radii are component envelopes, not confirmed solid stock.",
    ],
  ])
    writeDrawing(
      id,
      title,
      geometry[index],
      [note, ...commonNotes],
      "Arrangement",
      { component: "GeometryViews", svg_index: index },
    );
  for (const joint of document.joints.filter((joint) =>
    ["fin_root", "receiver_end"].includes(joint.kind),
  )) {
    const graphics = render("GeometryViews", {
      ...document,
      joints: [
        joint,
        ...document.joints.filter((entry) => entry.id !== joint.id),
      ],
    });
    const notes = [
      joint.description,
      ...joint.dimensions.map(
        (dimension) =>
          `${dimension.label}: ${dimension.value == null ? "Unavailable" : `${number(dimension.value, 9)} ${dimension.unit}`} · ${dimension.state}`,
      ),
      ...joint.findings,
      ...joint.assembly_steps.map(
        (step, index) =>
          `Recorded assembly step${index + 1} (illustration; service/clearance unverified): ${step}`,
      ),
      ...commonNotes,
    ];
    writeDrawing(
      `joint-${joint.id}-section`,
      `${joint.label} · focused section`,
      graphics[4],
      notes,
      "Construction sections",
      {
        component: "GeometryViews",
        joint_id: joint.id,
        representation: "concept/envelope axial section; interfaces unresolved",
      },
    );
    writeDrawing(
      `joint-${joint.id}-layers`,
      `${joint.label} · separated layers`,
      graphics[5],
      notes,
      "Construction sections",
      {
        component: "GeometryViews",
        joint_id: joint.id,
        representation:
          "schematic exploded layer illustration; gaps not physical clearances",
      },
    );
  }
  for (const path of document.load_paths) {
    const graphics = render("LoadPathViews", {
      ...document,
      load_paths: [
        path,
        ...document.load_paths.filter((entry) => entry.id !== path.id),
      ],
    });
    const notes = [
      `Recorded case: ${path.case_id} · state: ${path.state}. ${path.description}`,
      "Arrow lengths and layout are schematic, not scaled by force. Red: failed screen; dashed amber: unresolved/estimated; blue: calculated, not qualified. No equal sharing or rigid support is inferred.",
      ...path.assumptions,
      ...path.free_body.supports.map(
        (support) => `Recorded support/condition: ${support}`,
      ),
    ];
    writeDrawing(
      `load-${path.id}`,
      `${path.label} · load-transfer topology`,
      graphics[0],
      notes,
      "Force paths",
      { component: "LoadPathViews", path_id: path.id, case_id: path.case_id },
    );
    writeDrawing(
      `fbd-${path.id}`,
      `${path.label} · free-body diagram`,
      graphics[1],
      notes,
      "Free-body diagrams",
      { component: "LoadPathViews", path_id: path.id, case_id: path.case_id },
    );
  }
  const mass = render("MassLaunchViews");
  for (const [index, id, title, note] of [
    [
      0,
      "mass-c1-balance",
      "C1 loaded balance · recorded CG and CP",
      "CG is the supplied loaded balance point. CP is the recorded aerodynamic-force location. Positions are not recomputed; this static screen establishes no flight acceptance.",
    ],
    [
      1,
      "mass-c1-distribution",
      "C1 frozen ledger · mass by station",
      "Individual recorded C1 rows, including full separate growth allowance once. Rows at identical stations overlap. This is not the R1 distribution or a full inertia tensor.",
    ],
    [
      2,
      "mass-c1-groups",
      "C1 recorded group masses",
      "Group masses are supplied by the backend. No totals or physical properties are recomputed for these bars.",
    ],
    [
      3,
      "mass-r1-additions",
      "R1 estimated mass-addition ledger",
      "All14 additions are saved estimates for the stopped R1 comparison. C1 source distribution remains unchanged; station dots show supplied allocations, not detailed R1 geometry.",
    ],
    [
      4,
      "launch-guide-speed",
      "Conditional guide departure · recorded samples",
      "All four cases remain separate. Formal and separate planning targets are recorded. Lines join saved samples only; no new speed is solved. Equipment and usable travel are unconfirmed; the resolved1.5m baseline stays unchanged.",
    ],
    [
      5,
      "launch-overall-usable",
      "Illustrative overall guide versus usable travel",
      "Parallel rows compare supplied lengths only, not actual start/release alignment. Original rod lugs are not verified rail buttons. No club, date, support, attachment or usable-travel acceptance is established.",
    ],
  ]) {
    const cases = document.cases.map(
      (item, index) =>
        `${["#77cee5", "#b5a0ec", "#e1b276", "#ec9fa6"][index % 4]}: ${item.label} · ${item.state}`,
    );
    const guideDetails =
      index === 4
        ? document.cases.flatMap((item) =>
            item.guide_results.map(
              (point) =>
                `${item.label}: usable ${number(point.usable_m, 9)} m; departure ${number(point.speed_mps, 12)} m/s; formal margin ${number(point.formal_margin_mps, 12)} m/s; separate planning margin ${number(point.planning_margin_mps, 12)} m/s`,
            ),
          )
        : [];
    writeDrawing(
      id,
      title,
      mass[index],
      [
        note,
        ...cases,
        ...guideDetails,
        ...(index >= 4
          ? [document.launch.hardware_status, ...document.launch.assumptions]
          : []),
        "Values are preliminary scalar recorded results. No stress, airflow, thermal or displacement field is created.",
      ],
      index >= 4 ? "Conditional launch guide" : "Mass and balance",
      { component: "MassLaunchViews", svg_index: index },
    );
  }
  // The UI's four-case table converted to SVG text; values are direct source fields, no physical arithmetic.
  const tableHeight = 210 + document.cases.length * 130;
  let table = `<svg viewBox="0 0 1200 ${tableHeight}" role="img"><title>C1 and R1 complete recorded case comparison</title>`;
  for (const [index, item] of document.cases.entries()) {
    const y = 50 + index * 130;
    table += `<rect x="20" y="${y - 25}" width="1160" height="112" fill="${index % 2 ? "#1a2c39" : "#152531"}"/>`;
    table += text(
      35,
      y,
      item.label,
      18,
      ["#77cee5", "#b5a0ec", "#e1b276", "#ec9fa6"][index % 4],
    );
    table += text(
      35,
      y + 28,
      `Loaded ${number(item.total_g)} g · nominal subtotal ${number(item.nominal_g)} g · separate growth ${number(item.growth_g)} g · additional aft probe ${number(item.extra_aft_g)} g`,
      14,
    );
    table += text(
      35,
      y + 51,
      `Loaded / burnout CG ${number(item.cg_mm)} / ${number(item.burnout_cg_mm)} mm · CP ${number(item.cp_mm)} mm · static margin ${number(item.loaded_margin_cal)} / ${number(item.burnout_margin_cal)} cal`,
      14,
    );
    table += text(
      35,
      y + 74,
      `State ${item.state} · recovery mean demand ${number(item.recovery_force_n)} N · conditional formal / planning headroom ${number(item.formal_headroom_g)} / ${number(item.planning_headroom_g)} g`,
      13,
    );
  }
  table += text(
    30,
    tableHeight - 87,
    `Static minimum: ${number(document.criteria.minimum_static_margin_cal)} cal · formal ${number(document.launch.formal_mps)} m/s · separate planning ${number(document.launch.planning_mps)} m/s`,
    14,
  );
  table += text(
    30,
    tableHeight - 60,
    "Headroom is conditional on unconfirmed illustrative guide equipment. Subtotals may include the probe; browser/exporter does not sum them.",
    12,
  );
  table += text(
    30,
    tableHeight - 34,
    "R1 is stopped before detailed CAD/native analysis. Positive mass/static screens do not close any other engineering or flight gate.",
    13,
  );
  table += "</svg>";
  writeDrawing(
    "mass-c1-r1-case-comparison",
    "C1 versus stopped R1 · complete recorded cases",
    parseMarkup(table).children[0],
    document.cases.flatMap((item) =>
      item.findings.map((finding) => `${item.label}: ${finding}`),
    ),
    "Mass and balance",
    {
      representation:
        "SVG text table of the same saved case fields shown in the frontend",
    },
  );
} finally {
  console.error = oldError;
  if (server) await server.close();
}
for (const artifact of artifacts) {
  const svg = readFileSync(resolve(ROOT, artifact.path), "utf8");
  assert.ok(
    svg.includes("<metadata>") &&
      svg.includes(document.identity.specification_sha256),
  );
  assert.ok(!/var\(|currentColor|<script\b|<foreignObject\b/.test(svg));
}
const manifest = {
  schema_version: "1.0.0",
  created_at_utc: new Date().toISOString(),
  document_id: document.id,
  input: { path: INPUT, sha256: hash(raw) },
  identity: document.identity,
  source_count: document.generated_from.length,
  source_hashes_verified: true,
  sources: document.generated_from,
  export_implementation: codeFiles.map((path) => ({
    path,
    sha256: hash(readFileSync(resolve(ROOT, path))),
  })),
  artifacts,
};
writeFileSync(
  resolve(OUT, "source-manifest.json"),
  JSON.stringify(manifest, null, 2) + "\n",
);
writeFileSync(resolve(RUN, "source-document.json"), raw);
writeFileSync(
  resolve(RUN, "source-manifest.json"),
  JSON.stringify(manifest, null, 2) + "\n",
);
const groups = [...new Set(artifacts.map((item) => item.group))];
let index = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Rocket Twin offline engineering drawings</title><style>body{font:16px/1.6 system-ui,sans-serif;background:#101e29;color:#dfebf3;max-width:1200px;margin:auto;padding:28px}a{color:#8ed4ee}h1,h2{line-height:1.25}.notice{border-left:3px solid #d9b278;background:#28271f;padding:15px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:15px}article{background:#182b38;border:1px solid #405c6d;border-radius:7px;padding:16px}article h3{font-size:17px}code{font-size:12px;overflow-wrap:anywhere}img{width:100%;background:#101e29}.muted{color:#abc1cf;font-size:14px}</style><h1>Rocket Twin · offline engineering drawings</h1><p class="notice">Preliminary concept/envelope graphics. Engineering acceptance remains open. Offline SVG export is not browser verification, physical qualification, construction release or flight acceptance. C1 complete detailed CAD remains unavailable;135 recorded parts/allocations are not135 CAD solids.</p><p>Open each self-contained SVG to zoom and read its dimensions, explanation and full frozen source hashes. SVG colors are portable explicit attributes; no scripts, external fonts or stylesheets are required.</p><p>Configuration <code>${esc(document.identity.configuration_id)}</code><br>Specification SHA-256 <code>${esc(document.identity.specification_sha256)}</code></p><p><a href="source-manifest.json">Full source and artifact manifest</a></p>`;
for (const group of groups) {
  index += `<h2>${esc(group)}</h2><div class="grid">`;
  for (const item of artifacts.filter((artifact) => artifact.group === group))
    index += `<article><h3><a href="${item.id}.svg">${esc(item.title)}</a></h3><p class="muted">Standalone SVG · ${number(item.width, 0)}×${number(item.height, 0)} view units · preliminary</p><p><a href="${item.id}.svg" download>Download SVG</a></p></article>`;
  index += "</div>";
}
index +=
  "<h2>Rendering / verification limits</h2><p>SVG markup and frozen source identities were checked without a browser. Interactive click/keyboard behavior, responsive UI, canvas/WebGL and browser downloads were not exercised. PNG renderer availability and any actual image observations are recorded separately in the run record; no preview is implied by an SVG link.</p></html>\n";
writeFileSync(resolve(OUT, "index.html"), index);
const record = {
  schema_version: "1.0.0",
  created_at_utc: new Date().toISOString(),
  command: "node scripts/wo04_export_walkthrough_drawings.mjs",
  result: "portable_svg_exports_complete_png_rendering_blocked",
  artifact_count: artifacts.length,
  output_directory: relative(ROOT, OUT),
  manifest_path: relative(ROOT, resolve(OUT, "source-manifest.json")),
  sources_verified: document.generated_from.length,
  physical_calculations_performed: false,
  cad_generated: false,
  browser_used: false,
  browser_acceptance: false,
  visual_png_inspection: false,
  warnings,
  presentation_revision:
    "v2: source-observed header overflow correction; no visual inspection claim",
  previous_run: {
    path: PREVIOUS_RUN,
    record_sha256: hash(
      readFileSync(resolve(ROOT, PREVIOUS_RUN, "record.json")),
    ),
    manifest_sha256: hash(
      readFileSync(resolve(ROOT, PREVIOUS_RUN, "source-manifest.json")),
    ),
    archived_exporter_sha256: hash(
      readFileSync(resolve(ROOT, PREVIOUS_RUN, "executed-script.mjs")),
    ),
  },
  renderer_attempts: [],
  historical_v1_renderer_attempts: [
    {
      command:
        "sips -s format png output/engineering-walkthrough/renderer-check.svg --out output/engineering-walkthrough/renderer-check.png",
      exit_code: 13,
      error:
        "Cannot extract image from file. Error13: an unknown error occurred.",
    },
    {
      command:
        "qlmanage -t -s1800 -o output/engineering-walkthrough output/engineering-walkthrough/renderer-check.svg",
      exit_code: 255,
      error:
        "sandbox_extension_issue_file failed: Operation not permitted; sandbox initialization failed: invalid data type of path filter; expected pattern, got boolean",
    },
  ],
  historical_v1_renderer_dependency_check: {
    cairosvg: false,
    resvg: false,
    imagemagick: false,
    sips_svg_input_advertised_but_test_failed: true,
  },
  stop_condition:
    "One native renderer fallback exhausted. No installs, upgrades, browser, headless renderer or further native workaround attempted.",
  limitations: [
    "No PNG previews or image observations were produced by this script because available native rendering failed. SVG source/metadata checks are not visual acceptance.",
    "Figure styles are resolved from existing CSS using a small presentation-only matcher; hover/focus and responsive HTML layout are deliberately absent.",
    "Case-comparison SVG is a direct rendering of the UI saved case fields; no mass, balance, force, speed or margin is recomputed.",
    "All drawings retain preliminary, unresolved and failed statuses. C1 complete detailed CAD, installed joints/contact/thermal/fin/flutter, actual motor/guide/site and release gates remain open.",
  ],
};
function checkArtifacts() {
  const checker = String.raw`import json, hashlib, xml.etree.ElementTree as ET, sys
from pathlib import Path
root=Path(sys.argv[1]); manifest=json.loads(Path(sys.argv[2]).read_text()); ns={"s":"http://www.w3.org/2000/svg"}
header_count=0; max_header=0
for source in manifest["sources"]+manifest["export_implementation"]:
 assert hashlib.sha256((root/source["path"]).read_bytes()).hexdigest()==source["sha256"], source["path"]
for artifact in manifest["artifacts"]:
 raw=(root/artifact["path"]).read_bytes(); tree=ET.fromstring(raw)
 assert hashlib.sha256(raw).hexdigest()==artifact["sha256"], artifact["path"]
 assert tree.find("s:title",ns).text and tree.find("s:desc",ns).text
 metadata=json.loads(tree.find("s:metadata",ns).text)
 assert metadata["cad_revision"] is None and not metadata["browser_verified"]
 assert metadata["sources"]==manifest["sources"]
 assert "var(" not in raw.decode() and "currentColor" not in raw.decode()
 assert len(tree.findall(".//s:text",ns))>30
 assert not tree.findall(".//s:script",ns) and not tree.findall(".//s:foreignObject",ns)
 assert all("http" not in v for node in tree.iter() for k,v in node.attrib.items() if k.endswith("href"))
 headers=[node for node in tree.findall("s:text",ns) if node.get("data-export-header")=="true"]
 assert len(headers)==metadata["presentation_layout"]["header_line_count"]
 for node in headers:
  count=len("".join(node.itertext())); limit=int(node.get("data-character-limit"))
  assert count<=limit<=120
  assert float(node.get("y"))<metadata["presentation_layout"]["drawing_y"]
  header_count+=1; max_header=max(max_header,count)
 body=tree.find("s:svg",ns)
 assert float(body.get("y"))==metadata["presentation_layout"]["drawing_y"]
 assert float(body.get("y"))+float(body.get("height"))<metadata["presentation_layout"]["footer_y"]
assert len(manifest["artifacts"])==25
print(json.dumps({"result":"passed","svg_xml_parsed":len(manifest["artifacts"]),"accessible_title_description_metadata":True,"source_and_implementation_hashes_verified":True,"artifact_hashes_verified":True,"no_unresolved_css_vars_or_currentColor":True,"no_external_svg_dependencies":True,"width_bounded_header_lines_checked":header_count,"longest_header_characters":max_header,"drawing_and_footer_vertical_offsets_verified":True,"png_visual_inspection":False}))`;
  return JSON.parse(
    execFileSync(
      resolve(ROOT, ".venv/bin/python"),
      ["-c", checker, ROOT, resolve(OUT, "source-manifest.json")],
      { encoding: "utf8" },
    ),
  );
}
record.offline_artifact_checks = checkArtifacts();
writeFileSync(
  resolve(RUN, "README.md"),
  `# Offline walkthrough export v2\n\nRegenerate with: \`node scripts/wo04_export_walkthrough_drawings.mjs\`.\n\nLocal drawings and accessible index: \`output/engineering-walkthrough/index.html\`. Generated SVG bulk is a local artifact; publish the script, small record and source manifest instead.\n\nV2 wraps every standalone header to width-aware lines capped at120characters and derives drawing/footer vertical positions from the header height. This is a source-observed presentation correction, not a visual acceptance claim.\n\nThe preserved v1 record, manifest and exact exporter source are in \`${PREVIOUS_RUN}\`. V2 makes no native renderer attempts. Historical native PNG failures remain recorded; no PNG or browser observations are claimed.\n`,
);
writeFileSync(
  resolve(RUN, "record.json"),
  JSON.stringify(record, null, 2) + "\n",
);
console.log(
  JSON.stringify({
    result: record.result,
    artifact_count: artifacts.length,
    output: relative(ROOT, OUT),
    record: relative(ROOT, resolve(RUN, "record.json")),
    warnings: warnings.length,
  }),
);
