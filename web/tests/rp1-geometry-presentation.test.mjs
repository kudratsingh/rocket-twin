import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { Box3, Vector3 } from 'three';
import {
  inspectionGeometryPresentation,
  inspectionPartRepresentation,
  inspectionSourceContext,
  requireInspectionSource,
} from '../src/workspaces/inspectionWorkflow.ts';
import { inspectionSceneBounds } from '../src/components/inspectionSceneBounds.ts';
import { fitOrbitFrame } from '../src/components/inspectionCamera.ts';
import { restoreAssembledInspection } from '../src/components/inspectionDisplay.ts';
import { useInspection } from '../src/store.ts';

// Synthetic presentation fixture, not RP1 dimensional or engineering evidence.
const kinds = ['source_dimensioned', 'simplified_envelope', 'mass_allowance', 'missing_geometry'];
const fixture = () => ({
  id: 'G80-F2-RP1-AD1-definition-v2',
  label: 'Synthetic RP1 inspection presentation',
  snapshot_only: true,
  identity: {
    specification_sha256: 'fixture-source',
    resolved_spec_sha256: null,
    cad_revision_sha256: null,
    inspection_geometry_sha256: 'fixture-inspection-geometry',
  },
  summary: { inspection_geometry: { complete_installed_geometry: false }, physical_inertia: null },
  parts: Array.from({ length: 55 }, (_, index) => ({
    id: `source_${index}`,
    name: `Source record ${index}`,
    parent: null,
    type: 'unknown',
    material: 'source fixture',
    learn: 'Synthetic presentation fixture only',
    representation: { role: kinds[index % 4], description: `Fixture maturity ${kinds[index % 4]}` },
    mesh_url: index % 4 < 2 ? `/fixture/inspection/source_${index}.glb` : null,
  })),
});

test('inspection maturity never promotes source geometry into canonical CAD or borrows a foreign identity', () => {
  const document = fixture();
  const before = JSON.stringify(document);
  const model = inspectionGeometryPresentation(document);
  assert.equal(model.sourceDerived, true);
  assert.equal(model.meshCount, 28);
  assert.deepEqual(model.counts, {
    source_dimensioned: 14,
    simplified_envelope: 14,
    mass_allowance: 14,
    missing_geometry: 13,
  });
  assert.match(model.coverage, /28\/55/);
  assert.match(model.coverage, /14 mass allowances without solids/);
  const context = inspectionSourceContext(document.id, document);
  assert.equal(context.cadRevision, null);
  assert.equal(context.inspectionGeometry, 'fixture-inspection-geometry');
  assert.match(context.maturity, /Complete manufacturing CAD.*unavailable/);
  const foreign = inspectionSourceContext('foreign-design', document);
  assert.equal(foreign.inspectionGeometry, null);
  assert.equal(foreign.meshCount, 0);
  assert.equal(JSON.stringify(document), before);
  assert.equal(inspectionGeometryPresentation({ ...document, identity: {} }).sourceDerived, false);
  assert.equal(inspectionGeometryPresentation({ ...document, summary: {} }).sourceDerived, false);
  for (const index of [2, 3]) {
    const invalid = fixture();
    invalid.parts[index].mesh_url = '/invented-solid.glb';
    assert.throws(() => requireInspectionSource(invalid, invalid.id), /unsupported solid/);
    assert.match(
      inspectionPartRepresentation(document.parts[index]).label,
      /no separate solid|no solid modeled/,
    );
  }
});

test('actual loaded inspection bounds exclude allowances, foreign records and nonfinite geometry', () => {
  const original = new Box3(new Vector3(-0.04, 0.2, -0.04), new Vector3(0.04, 0.8, 0.04));
  const records = new Map([
    ['source_0', { bounds: original.clone(), explodeOffset: [0.05, 0.1, 0] }],
    [
      'foreign',
      {
        bounds: new Box3(new Vector3(-100, -100, -100), new Vector3(100, 100, 100)),
        explodeOffset: [0, 0, 0],
      },
    ],
    [
      'invalid',
      { bounds: new Box3(new Vector3(NaN, 0, 0), new Vector3(1, 1, 1)), explodeOffset: [0, 0, 0] },
    ],
  ]);
  const assembled = inspectionSceneBounds(
    records,
    ['source_0', 'source_2', 'source_3', 'invalid'],
    0,
  );
  assert.equal(assembled.available, 1);
  assert.ok(assembled.bounds.equals(original));
  const exploded = inspectionSceneBounds(records, ['source_0'], 1);
  assert.ok(exploded.bounds.equals(original.clone().translate(new Vector3(0.05, 0.1, 0))));
  assert.ok(records.get('source_0').bounds.equals(original));
  assert.ok(inspectionSceneBounds(records, ['source_2'], 0).bounds.isEmpty());
  assert.ok(inspectionSceneBounds(records, ['source_0'], NaN).bounds.isEmpty());
  for (const bounds of [assembled.bounds, exploded.bounds]) {
    const position = new Vector3(1, 2, 3);
    const target = new Vector3(0, 0.5, 0);
    const frame = fitOrbitFrame(bounds, 1280 / 720, 35, position, target, new Vector3(0, 1, 0));
    assert.ok([...frame.position, ...frame.target, frame.near, frame.far].every(Number.isFinite));
    const direction = new Vector3(...frame.position).sub(new Vector3(...frame.target)).normalize();
    assert.ok(direction.distanceTo(position.clone().sub(target).normalize()) < 1e-12);
  }
  const state = useInspection.getState();
  state.resetVehicle();
  state.select('source_2');
  state.setExploded(1);
  state.hideParts(['source_0']);
  state.toggleSection();
  restoreAssembledInspection(useInspection.getState());
  assert.equal(useInspection.getState().selectedId, 'source_2');
  assert.equal(useInspection.getState().exploded, 0);
  assert.equal(useInspection.getState().section, false);
  assert.deepEqual(useInspection.getState().hiddenIds, []);
  state.resetVehicle();
});

test('RP1 SSR exposes inspection maturity and all 55 source selections without generating placeholder solids', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { DesignVisual } = await server.ssrLoadModule('/src/workspaces/DesignVisual.tsx');
    const { PartsTree } = await server.ssrLoadModule('/src/components/PartsTree.tsx');
    const { InspectionDisplayReadoutView } = await server.ssrLoadModule(
      '/src/components/InspectionDisplayReadout.tsx',
    );
    const document = fixture();
    const before = JSON.stringify(document);
    const html = renderToStaticMarkup(
      React.createElement(DesignVisual, {
        vehicle: document,
        meshView: React.createElement('div', null, 'Renderer boundary; no WebGL'),
      }),
    );
    assert.match(html, /data-representation="3d"/);
    assert.match(html, />3D inspection model<\/button>/);
    assert.match(html, /complete manufacturing CAD unavailable/);
    assert.match(html, /28\/55 source records/);
    assert.match(html, /Mass allowances and missing geometry have no solid/);
    const tree = renderToStaticMarkup(React.createElement(PartsTree, { parts: document.parts }));
    assert.equal((tree.match(/class="tree-select"/g) ?? []).length, 55);
    for (const part of document.parts) assert.ok(tree.includes(`title="${part.id}"`));
    const readout = renderToStaticMarkup(
      React.createElement(InspectionDisplayReadoutView, {
        vehicle: document,
        state: {
          selectedId: 'source_2',
          hiddenIds: [],
          exploded: 0,
          section: false,
          ghostShell: false,
          wireframe: false,
        },
        onRestore() {},
      }),
    );
    assert.match(readout, /allowances and missing geometry add no placeholder solids or bounds/);
    assert.match(readout, /source_2/);
    assert.equal(JSON.stringify(document), before);
  } finally {
    await server.close();
  }
});
