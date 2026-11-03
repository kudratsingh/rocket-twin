import { URL } from 'node:url';
import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import {
  drawingPart,
  orthographicModel,
  orthographicMetadata,
} from '../src/design/orthographicGeometry.ts';

const base = {
  id: 'source-part',
  type: 'body_tube',
  parent: null,
  material: 'paper',
  learn: 'Carry loads.',
  location: { position_m: 0.2, lateral_offset_m: [0, 0] },
  dimensions: { length_m: 0.8, radius_m: 0.033, inner_radius_m: 0.031 },
  representation: { role: 'manufactured', description: 'Nominal source CAD' },
  source: { spec_path: 'synthetic.yaml', shape_sha256: 'fixture-shape' },
};

test('source dimensions retain station, offsets and wall bands in display millimetres', () => {
  const body = drawingPart(base);
  assert.equal(body.layer, 'body');
  assert.deepEqual(body.bounds, [200, -33, 1000, 33]);
  assert.deepEqual(body.polygons[0], [
    [200, 31],
    [1000, 31],
    [1000, 33],
    [200, 33],
  ]);
  const box = drawingPart({
    ...base,
    type: 'commercial',
    location: { position_m: 0.4, lateral_offset_m: [0.01, 0.02] },
    dimensions: { bbox_m: [0.1, 0.02, 0.03] },
  });
  assert.deepEqual(box.bounds, [400, 0, 500, 20]);
  assert.equal(box.layer, 'envelopes');
  assert.equal(drawingPart({ ...base, type: 'motor' }).layer, 'motor');
  assert.equal(drawingPart({ ...base, type: 'centering_ring' }).layer, 'rings');
});

test('fin is explicitly one source radial planform; curved nose remains a bounding envelope', () => {
  const fin = drawingPart({
    ...base,
    type: 'fin_set',
    dimensions: {
      radius_m: 0.03,
      span_m: 0.06,
      root_chord_m: 0.12,
      tip_chord_m: 0.05,
      sweep_m: 0.04,
    },
  });
  assert.deepEqual(fin.polygons, [
    [
      [200, 30],
      [320, 30],
      [290, 90],
      [240, 90],
    ],
  ]);
  assert.match(fin.note, /not a projection of fin count/);
  const nose = drawingPart({
    ...base,
    type: 'nose_cone',
    dimensions: { length_m: 0.2, radius_m: 0.03, shape: 'ogive' },
  });
  assert.match(nose.note, /not the curved CAD surface/);
  assert.equal(nose.polygons[0].length, 4);
});

test('missing and invalid geometry stays unavailable; no mesh bounds or mass substitute', () => {
  for (const dimensions of [
    {},
    { length_m: null, radius_m: 0.03 },
    { length_m: 0.1, radius_m: -0.03 },
    { bbox_m: [0.1, 0, 0.3] },
    { length_m: 0.1, radius_m: 0.03, inner_radius_m: 0.04 },
  ]) {
    assert.equal(
      typeof drawingPart({ ...base, dimensions, mass_kg: 1, cad_bounding_size_mm: [100, 20, 20] }),
      'string',
    );
  }
  assert.equal(
    typeof drawingPart({ ...base, location: undefined, position_m: undefined }),
    'string',
  );
  assert.deepEqual(
    drawingPart({ ...base, location: { position_m: 0, lateral_offset_m: [0, 0] } }).bounds,
    [0, -33, 800, 33],
  );
});

test('SVG source identity and unavailable scope survive SSR without a different design label', async () => {
  const vehicle = {
    id: 'historical-source-fixture',
    label: 'Recorded source fixture',
    identity: { specification_sha256: 'fixture-hash' },
    summary: {},
    parts: [base, { ...base, id: 'unknown', dimensions: {} }],
  };
  assert.equal(orthographicModel(vehicle).unavailable.length, 1);
  assert.equal(orthographicMetadata(vehicle).identity.specification_sha256, 'fixture-hash');
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { OrthographicDesign } = await server.ssrLoadModule('/src/design/OrthographicDesign.tsx');
    const markup = renderToStaticMarkup(
      React.createElement(OrthographicDesign, {
        vehicle,
        selectedPartId: base.id,
        onSelectPart() {},
      }),
    );
    assert.match(markup, /historical-source-fixture/);
    assert.match(markup, /fixture-hash/);
    assert.match(markup, /source-part/);
    assert.match(markup, /200.00–1000.00 mm/);
    assert.match(markup, /Export SVG/);
    assert.match(markup, /Unavailable geometry \(1\)/);
    assert.match(markup, /not CAD projections/);
    assert.match(markup, /acceptance open/);
    assert.doesNotMatch(markup, /G80-F2|qualified geometry/);
  } finally {
    await server.close();
  }
});
