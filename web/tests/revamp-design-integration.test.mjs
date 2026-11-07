import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { useInspection } from '../src/store.ts';
import {
  inspectionSourceContext,
  requireInspectionSource,
} from '../src/workspaces/inspectionWorkflow.ts';
import { drawingPart } from '../src/design/orthographicGeometry.ts';

const AD1 = 'G80-F2-RP1-AD1-definition-v2';
// Deliberately synthetic display fixtures: these values are not engineering records.
const cases = [
  {
    case: 'nominal',
    nylon_mass_probe_g: 55,
    total_mass_g: 900.123,
    guide_mps: { 1.5: 15.111111 },
    formal_speed_margin_mps: 0.111111,
    planning_speed_margin_mps: -0.388889,
  },
  {
    case: 'adverse',
    nylon_mass_probe_g: 55,
    total_mass_g: 920.456,
    guide_mps: { 1.5: 14.999999 },
    formal_speed_margin_mps: -0.000001,
    planning_speed_margin_mps: -0.500001,
  },
  {
    case: 'nominal',
    nylon_mass_probe_g: 68,
    total_mass_g: 913.789,
    guide_mps: { 1.5: 15.012345 },
    formal_speed_margin_mps: 0.012345,
    planning_speed_margin_mps: -0.487655,
  },
  {
    case: 'adverse',
    nylon_mass_probe_g: 68,
    total_mass_g: 933.012,
    guide_mps: { 1.5: 14.812345 },
    formal_speed_margin_mps: -0.187655,
    planning_speed_margin_mps: -0.687655,
  },
];
const sourcePart = {
  id: 'synthetic_body',
  name: 'Synthetic source tube',
  type: 'tube',
  parent: null,
  material: 'fixture paper',
  learn: 'Synthetic fixture only',
  location: { position_m: 0.1, lateral_offset_m: [0, 0] },
  dimensions: { length_m: 0.45, radius_m: 0.03 },
  representation: { role: 'source envelope / concept' },
  mesh_url: null,
};
const unknownPart = {
  id: 'synthetic_unknown',
  type: 'unknown',
  parent: null,
  material: '',
  learn: 'Dimensions intentionally absent',
  mesh_url: null,
};
const ad1 = () => ({
  id: AD1,
  label: 'Synthetic AD1 display fixture — not engineering evidence',
  snapshot_only: true,
  identity: { specification_sha256: 'synthetic-ad1-fingerprint', cad_revision_sha256: null },
  summary: {
    mass_cases: structuredClone(cases),
    physical_inertia: null,
    inertia_status: 'unavailable',
  },
  parts: [structuredClone(sourcePart), structuredClone(unknownPart)],
});
const archived = () => ({
  id: 'modular-performance-v1',
  label: 'Synthetic archived CAD reference fixture',
  identity: {
    resolved_spec_sha256: 'synthetic-archived-fingerprint',
    cad_revision_sha256: 'synthetic-archived-cad',
  },
  summary: {},
  parts: Array.from({ length: 42 }, (_, index) => ({
    ...structuredClone(sourcePart),
    id: `archived_fixture_${index}`,
    mesh_url: `/synthetic-fixtures/${index}.glb`,
    representation: { role: 'manufactured' },
  })),
});

async function withModules(run) {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const modules = await Promise.all([
      server.ssrLoadModule('/src/workspaces/DesignVisual.tsx'),
      server.ssrLoadModule('/src/workspaces/WorkspaceChrome.tsx'),
      server.ssrLoadModule('/src/workspaces/InspectionWorkspace.tsx'),
      server.ssrLoadModule('/src/workspaces/layoutPreferences.ts'),
      server.ssrLoadModule('/src/components/InspectionPanel.tsx'),
      server.ssrLoadModule('/src/workspaces/PartDimensions.tsx'),
    ]);
    const api = Object.assign({}, ...modules);
    const renderDesign = (vehicle, representation = 'auto') => {
      api.writeLayout('design', { ...api.defaultLayout(), representation });
      return renderToStaticMarkup(
        React.createElement(api.WorkspaceFrame, {
          workspace: 'design',
          header: 'Source picker fixture',
          navigation: null,
          identity: React.createElement('p', null, vehicle.id),
          children: React.createElement(api.InspectionWorkspace, {
            tree: 'Source parts fixture',
            inspector: React.createElement(api.InspectionPanel, { vehicle, mass: null }),
            visual: React.createElement(api.DesignVisual, {
              vehicle,
              meshView: React.createElement(
                'div',
                { 'data-mesh-source': vehicle.id },
                'Renderer boundary fixture; no WebGL executed',
              ),
            }),
          }),
        }),
      );
    };
    await run({ ...api, renderDesign });
  } finally {
    await server.close();
  }
}

test('AD1 drawing-only entry rejects a persisted 3D preference without borrowing archived CAD', async () => {
  await withModules(({ renderDesign }) => {
    for (const preference of ['auto', '3d']) {
      const document = ad1();
      const before = JSON.stringify(document);
      const html = renderDesign(document, preference);
      assert.match(html, /data-representation="2d"/);
      assert.match(html, /<button[^>]*disabled=""[^>]*>3D recorded geometry<\/button>/);
      assert.match(html, /No matching 3D assembly exists for this source/);
      assert.match(html, /No recorded component meshes/);
      assert.ok(html.includes(AD1));
      assert.doesNotMatch(
        html,
        /synthetic-archived-cad|modular-performance-v1|42 recorded component meshes/,
      );
      assert.equal(
        JSON.stringify(document),
        before,
        'rendering must not add geometry or mutate source',
      );
      assert.equal(
        typeof drawingPart(document.parts[1]),
        'string',
        'missing source geometry yields an unavailable reason rather than a polygon',
      );
    }
  });
});

test('separate archived 42-mesh reference keeps its own selectable 3D representation and identity', async () => {
  await withModules(({ renderDesign }) => {
    const document = archived();
    const html = renderDesign(document);
    assert.match(html, /data-representation="3d"/);
    assert.match(html, /42 recorded component meshes/);
    const button = html.match(/<button[^>]*>3D recorded geometry<\/button>/)?.[0];
    assert.ok(button);
    assert.doesNotMatch(button, /disabled=/);
    assert.match(button, /aria-pressed="true"/);
    assert.ok(html.includes(document.id));
    assert.ok(html.includes('synthetic-archived-cad'));
    assert.doesNotMatch(html, /Recorded AD1 mass and launch cases/);
    const mismatch = inspectionSourceContext(AD1, document);
    assert.equal(mismatch.current, null);
    assert.equal(mismatch.meshCount, 0);
    assert.equal(mismatch.cadRevision, null);
    assert.throws(() => requireInspectionSource(document, AD1), /does not match/);
  });
});

test('source transition clears temporary selection; foreign or missing dimensions remain unavailable', async () => {
  await withModules(({ PartDimensions }) => {
    const state = () => useInspection.getState();
    try {
      state().resetVehicle();
      state().select('archived_fixture_0');
      state().setExploded(1);
      state().hideParts(['archived_fixture_0']);
      const current = requireInspectionSource(ad1(), AD1);
      const foreign = renderToStaticMarkup(
        React.createElement(PartDimensions, { vehicle: current, partId: state().selectedId }),
      );
      assert.match(foreign, /not mapped in source G80-F2-RP1-AD1-definition-v2/);
      assert.doesNotMatch(foreign, /450 mm/);
      state().resetVehicle();
      assert.equal(state().selectedId, null);
      assert.equal(state().exploded, 0);
      assert.deepEqual(state().hiddenIds, []);
      state().select('synthetic_unknown');
      const missing = renderToStaticMarkup(
        React.createElement(PartDimensions, { vehicle: current, partId: state().selectedId }),
      );
      assert.match(missing, /Dimensions unavailable/);
      assert.match(missing, /Wall thickness unavailable/);
      assert.match(missing, /Recorded CAD mesh unavailable/);
      assert.doesNotMatch(missing, /0 m \(0 mm\)/);
      state().select('synthetic_body');
      const supplied = renderToStaticMarkup(
        React.createElement(PartDimensions, { vehicle: current, partId: state().selectedId }),
      );
      assert.match(supplied, /0.45 m \(450 mm\)/);
      assert.match(supplied, /Wall thickness unavailable/);
    } finally {
      state().resetVehicle();
    }
  });
});

test('Inspector renders four saved case records verbatim with growth, probes and unavailable inertia boundaries', async () => {
  await withModules(({ InspectionPanel }) => {
    const document = ad1();
    const before = JSON.stringify(document);
    const html = renderToStaticMarkup(
      React.createElement(InspectionPanel, { vehicle: document, mass: null }),
    );
    const table = html.match(/<table>([\s\S]*?)<\/table>/)?.[1];
    assert.ok(table);
    assert.equal((table.match(/<tr>/g) ?? []).length, 5);
    for (const row of cases) {
      assert.ok(table.includes(`${row.case} / ${row.nylon_mass_probe_g} g`));
      assert.ok(
        table.includes(row.total_mass_g.toLocaleString(undefined, { maximumFractionDigits: 3 })),
      );
      assert.ok(
        table.includes(
          row.planning_speed_margin_mps.toLocaleString(undefined, { maximumFractionDigits: 6 }),
        ),
      );
    }
    assert.match(table, /Unavailable/); // no CG/margin numbers were supplied in this fixture
    for (const text of [
      'full 50 g',
      '55 g and 68 g',
      'unverified probes',
      '20 g aft',
      'Source estimates, not measurements',
      'Full rotational inertia',
      'complete 3D CAD remain unavailable',
      'Saved cases below; no compatible burn-state model',
    ])
      assert.ok(html.includes(text), text);
    assert.doesNotMatch(html, /0% propellant consumed/);
    assert.equal(JSON.stringify(document), before, 'table must not recalculate the source cases');
  });
});

const actualPath = new URL(
  '../public/engineering-workbench/rp1-ad1-inspection.json',
  import.meta.url,
);
test('selected fin inspector uses its supplied evidence and retains a failed screen without inventing installed movement', async () => {
  await withModules(({ PartInspector }) => {
    const part = { ...structuredClone(sourcePart), id: 'synthetic_fin', type: 'fin_set' };
    const evidence = {
      fin: {
        bonded_panel_stress_screen_pass_only: false,
        factored_moment_Nm: 8.83,
        factored_force_N: 331.125,
        ideal_composite_strip_lower_deflection_only: [],
        installed_displacement: null,
      },
    };
    const html = renderToStaticMarkup(
      React.createElement(PartInspector, { part, parts: [part], evidence }),
    );
    assert.match(html, /Failed recorded panel strength screen/);
    assert.match(html, /excludes the flexible installed attachment/);
    assert.match(html, /Installed movement, peel capacity/);
    const absent = renderToStaticMarkup(
      React.createElement(PartInspector, { part, parts: [part] }),
    );
    assert.doesNotMatch(absent, /Recorded AD1 fin finding/);
  });
});
test(
  'optional actual prepared AD1 source retains 55 parts, four saved cases, no CAD and frozen identity in SSR',
  {
    skip: !existsSync(actualPath)
      ? 'Prepared AD1 export absent; synthetic regression remains active'
      : false,
  },
  async () => {
    await withModules(({ renderDesign, InspectionPanel }) => {
      const document = JSON.parse(readFileSync(actualPath, 'utf8'));
      requireInspectionSource(document, AD1);
      assert.equal(document.parts.length, 55);
      assert.ok(document.parts.every((part) => !part.mesh_url));
      assert.equal(document.summary.mass_cases.length, 4);
      assert.equal(
        document.identity.specification_sha256,
        '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660',
      );
      assert.equal(document.identity.cad_revision_sha256, null);
      assert.equal(document.summary.physical_inertia, null);
      const html = renderDesign(document, '3d');
      assert.match(html, /data-representation="2d"/);
      assert.match(html, /No recorded component meshes/);
      const panel = renderToStaticMarkup(
        React.createElement(InspectionPanel, { vehicle: document, mass: null }),
      );
      for (const row of document.summary.mass_cases)
        assert.ok(
          panel.includes(row.total_mass_g.toLocaleString(undefined, { maximumFractionDigits: 3 })),
        );
      assert.match(panel, /complete 3D CAD remain unavailable/);
    });
  },
);
