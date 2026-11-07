/** Actual-source React/SVG artifacts only; no browser, image renderer, CAD or physics. */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import React from "../web/node_modules/react/index.js";
import { renderToStaticMarkup } from "../web/node_modules/react-dom/server.node.js";
import { createServer } from "../web/node_modules/vite/dist/node/index.js";

const input = "web/public/engineering-workbench/rp1-ad1-inspection.json";
const bytes = fs.readFileSync(input);
const vehicle = JSON.parse(bytes);
if (
  vehicle.id !== "G80-F2-RP1-AD1-definition-v2" ||
  vehicle.parts.length !== 55 ||
  vehicle.parts.some((p) => p.mesh_url) ||
  vehicle.identity.specification_sha256 !==
    "811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660"
)
  throw Error("Wrong current inspection source");
const output = "output/frontend-revamp-20261107";
fs.mkdirSync(output, { recursive: true });
const server = await createServer({
  configFile: false,
  root: path.resolve("web"),
  server: { middlewareMode: true, hmr: false, ws: false },
  appType: "custom",
});
try {
  const { OrthographicDesign } = await server.ssrLoadModule(
    "/src/design/OrthographicDesign.tsx",
  );
  const { WorkspaceFrame, WorkspaceNavigation, WorkspaceIdentityStrip } =
    await server.ssrLoadModule("/src/workspaces/WorkspaceChrome.tsx");
  const { InspectionWorkspace } = await server.ssrLoadModule(
    "/src/workspaces/InspectionWorkspace.tsx",
  );
  const { DesignVisual } = await server.ssrLoadModule(
    "/src/workspaces/DesignVisual.tsx",
  );
  const { PartsTree } = await server.ssrLoadModule(
    "/src/components/PartsTree.tsx",
  );
  const { InspectionPanel } = await server.ssrLoadModule(
    "/src/components/InspectionPanel.tsx",
  );
  const e = React.createElement;
  const drawing = renderToStaticMarkup(
    e(OrthographicDesign, {
      vehicle,
      selectedPartId: "fin_set",
      onSelectPart: () => {},
    }),
  );
  const match = drawing.match(/<svg\b[\s\S]*?<\/svg>/);
  if (!match) throw Error("Actual component produced no SVG");
  const svg = match[0].replace(
    "<svg ",
    '<svg xmlns="http://www.w3.org/2000/svg" ',
  );
  fs.writeFileSync(output + "/ad1-arrangement.svg", svg);
  const rendered = renderToStaticMarkup(
    e(
      WorkspaceFrame,
      {
        workspace: "design",
        header: e(
          "header",
          { className: "topbar" },
          e("strong", null, "G80 RP1 / AD1 v2 — static fixture header"),
        ),
        navigation: e(WorkspaceNavigation, {
          active: "design",
          href: "/?workspace=design",
          onNavigate: () => {},
        }),
        identity: e(WorkspaceIdentityStrip, {
          name: vehicle.label,
          maturity: "Current source concept, not complete CAD",
        }),
        footer: e("small", null, "Preliminary; engineering acceptance open"),
      },
      e(InspectionWorkspace, {
        tree: e(PartsTree, { parts: vehicle.parts }),
        visual: e(DesignVisual, {
          vehicle,
          meshView: e("p", null, "Matching AD1 3D CAD unavailable"),
        }),
        inspector: e(InspectionPanel, { vehicle, mass: null }),
      }),
    ),
  );
  const cssDir = "web/dist/assets";
  const css = fs.existsSync(cssDir)
    ? fs
        .readdirSync(cssDir)
        .filter((f) => f.endsWith(".css"))
        .map((f) => fs.readFileSync(path.join(cssDir, f), "utf8"))
        .join("\n")
    : "";
  fs.writeFileSync(
    output + "/index.html",
    '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>RP1 actual-source static React fixture</title><style>' +
      css +
      '</style><p style="padding:8px;background:#273b44;color:white">Actual React/source fixture with a fixture header. Static buttons are inert; this is not a screenshot or browser acceptance. <a href="ad1-arrangement.svg">Open standalone source drawing</a>.</p>' +
      rendered +
      "</html>",
  );
  fs.writeFileSync(
    output + "/manifest.json",
    JSON.stringify(
      {
        configuration: vehicle.id,
        source: input,
        source_sha256: crypto.createHash("sha256").update(bytes).digest("hex"),
        implementation_sources_sha256: Object.fromEntries(
          [
            "web/src/workspaces/WorkspaceChrome.tsx",
            "web/src/workspaces/InspectionWorkspace.tsx",
            "web/src/workspaces/DesignVisual.tsx",
            "web/src/components/InspectionPanel.tsx",
            "web/src/components/Viewer.tsx",
            "web/src/components/inspectionCamera.ts",
            "scripts/wo04_revamp_inspection_artifacts.mjs",
          ].map((file) => [
            file,
            crypto
              .createHash("sha256")
              .update(fs.readFileSync(file))
              .digest("hex"),
          ]),
        ),
        css_sha256: crypto.createHash("sha256").update(css).digest("hex"),
        raw_spec_sha256: vehicle.identity.specification_sha256,
        parts: 55,
        representation: "source envelopes / concept, not CAD",
        browser_verified: false,
        image_rendered: false,
        engineering_accepted: false,
        artifact:
          "actual React server rendering; fixture header, inert buttons",
      },
      null,
      2,
    ) + "\n",
  );
  console.log(
    "Wrote actual-source HTML, SVG and provenance manifest; no image/browser verification.",
  );
} finally {
  await server.close();
}
