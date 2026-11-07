import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { useInspection } from '../src/store.ts';
import {
  inspectionDisplayModel,
  restoreAssembledInspection,
} from '../src/components/inspectionDisplay.ts';

const vehicle = {
  id: 'recorded-source-fixture',
  summary: {},
  parts: [
    {
      id: 'shell',
      type: 'tube',
      parent: null,
      material: 'paper',
      learn: '',
      mesh_url: '/fixture/shell.glb',
      dimensions: { length_m: 0.778, wall_m: 0.0005 },
      representation: { role: 'manufactured' },
    },
    { id: 'unknown', type: 'unknown', parent: null, material: '', learn: '', mesh_url: null },
  ],
};
const display = {
  selectedId: 'shell',
  hiddenIds: ['shell'],
  exploded: 0.75,
  section: true,
  ghostShell: true,
  wireframe: true,
};

test('restoring assembly removes display transformations while retaining selected component and viewing angle', () => {
  const state = () => useInspection.getState();
  state().resetVehicle();
  state().setCameraView('aft');
  state().select('shell');
  state().hideParts(['shell', 'unknown']);
  state().setExploded(0.75);
  state().toggleSection();
  state().toggleGhostShell();
  state().toggleWireframe();
  state().toggleMarkers();
  state().togglePartLabels();
  const before = state();
  const originalSource = JSON.stringify(vehicle);
  restoreAssembledInspection(before);
  assert.deepEqual(state().hiddenIds, []);
  assert.equal(state().exploded, 0);
  for (const field of ['section', 'ghostShell', 'wireframe']) assert.equal(state()[field], false);
  for (const field of ['selectedId', 'cameraView', 'markers', 'partLabels'])
    assert.equal(state()[field], before[field], field);
  assert.equal(state().cameraAction, 'fit');
  assert.equal(state().focusId, null);
  assert.equal(state().resetToken, before.resetToken + 1);
  assert.equal(JSON.stringify(vehicle), originalSource);
  assert.equal(inspectionDisplayModel(vehicle, state()).altered, false);
  restoreAssembledInspection(state());
  for (const field of ['section', 'ghostShell', 'wireframe'])
    assert.equal(state()[field], false, 'second restore must not toggle modes back on');
  state().resetVehicle();
});

test('display status scopes hidden and selected parts to the exact supplied source and never substitutes missing mesh data', () => {
  const model = inspectionDisplayModel(vehicle, display);
  assert.equal(model.hiddenCount, 1);
  assert.equal(model.selected.id, 'shell');
  assert.equal(model.selectedHidden, true);
  assert.equal(model.meshCount, 1);
  const foreign = inspectionDisplayModel(vehicle, {
    ...display,
    selectedId: 'foreign-candidate',
    hiddenIds: ['foreign-candidate'],
  });
  assert.equal(foreign.hiddenCount, 0);
  assert.equal(foreign.selected, null);
  assert.equal(foreign.selectedHidden, false);
  assert.equal(
    inspectionDisplayModel({ ...vehicle, parts: [vehicle.parts[1]] }, display).meshCount,
    0,
  );
});

test('SSR keeps source dimensions unchanged by display modes and exposes explicit missing-source and no-mesh states', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { InspectionDisplayReadoutView } = await server.ssrLoadModule(
      '/src/components/InspectionDisplayReadout.tsx',
    );
    const render = (state, source = vehicle) =>
      renderToStaticMarkup(
        React.createElement(InspectionDisplayReadoutView, {
          vehicle: source,
          state,
          onRestore: () => {},
        }),
      );
    const altered = render(display);
    for (const text of [
      'Section clipping on',
      'Exploded display 75%',
      '1 of 2 source parts hidden',
      'currently hidden',
      'positive-X half is hidden',
      'not dimensions',
      'recorded-source-fixture',
      '0.778 m (778 mm)',
      '0.0005 m (0.5 mm)',
      'not as-built verification',
    ])
      assert.ok(altered.includes(text), text);
    assert.match(altered, /aria-live="polite"/);
    const explanation = altered.match(
      /<details class="inspection-display-explanation">([\s\S]*?)<\/details>/,
    );
    assert.ok(explanation, 'native explanation disclosure is collapsed by default');
    for (const text of [
      'How this display works',
      'Restore shows all parts',
      'positive-X',
      'Explode separates parts',
      'Source:',
    ])
      assert.ok(explanation[1].includes(text), text);
    assert.ok(
      altered.indexOf('Section clipping on') < altered.indexOf('<details'),
      'status remains outside collapsed content',
    );
    assert.ok(
      altered.indexOf('Restore assembled inspection') < altered.indexOf('<details'),
      'restore action remains visible',
    );
    const assembled = render({
      ...display,
      hiddenIds: [],
      exploded: 0,
      section: false,
      ghostShell: false,
      wireframe: false,
    });
    assert.match(assembled, /disabled=""/);
    assert.match(assembled, /Section clipping off/);
    assert.match(assembled, /Assembled display/);
    for (const text of ['0.778 m (778 mm)', '0.0005 m (0.5 mm)'])
      assert.ok(assembled.includes(text), text);
    const missing = render(
      { ...display, selectedId: 'unknown' },
      { ...vehicle, parts: [vehicle.parts[1]] },
    );
    assert.match(missing, /3D section and explode unavailable/);
    assert.match(missing, /Dimensions unavailable/);
    assert.match(missing, /disabled=""/);
    assert.ok(
      missing.indexOf('3D section and explode unavailable') < missing.indexOf('<details'),
      'missing mesh state remains visible',
    );
    const foreign = render({ ...display, selectedId: 'another-source' });
    assert.match(foreign, /not mapped in source recorded-source-fixture/);
    assert.doesNotMatch(foreign, /0.778 m/);
    assert.match(render({ ...display, selectedId: null }), /Select a component in this source/);
  } finally {
    await server.close();
  }
});
