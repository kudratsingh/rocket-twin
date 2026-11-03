import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { drawingPart } from '../src/design/orthographicGeometry.ts';
import { fitDrawing, selectionVisibility, visibleDrawingParts, sourceMaturity } from '../src/design/designPresentation.ts';

const part = { id: 'small-source-ring', name: 'Small source ring', type: 'centering_ring', parent: null,
  material: 'fixture', learn: 'Synthetic selection fixture.', location: { position_m: 0.9, lateral_offset_m: [0,0] },
  dimensions: { length_m: 0.0005, radius_m: 0.005, inner_radius_m: 0.004 },
  representation: { role: 'concept' } };

test('small-part focus fits real bounds without forcing the nose datum into the frame', () => {
  const projected = drawingPart(part);
  const before = JSON.stringify(projected.polygons);
  const view = fitDrawing([projected]);
  assert.equal(view.cx, 900.25);
  assert.equal(view.cy, 0);
  assert.equal(view.scale, 24);
  assert.equal((projected.bounds[3] - projected.bounds[1]) * view.scale, 240);
  assert.equal(JSON.stringify(projected.polygons), before);
  assert.match(sourceMaturity(projected), /simplified envelope; source role: concept/);
});

test('shared hiding, layer hiding and selection-only mode stay distinct and do not mutate source', () => {
  const projected = drawingPart(part);
  const second = drawingPart({ ...part, id: 'other-ring' });
  assert.equal(selectionVisibility(projected, ['rings'], []), 'visible');
  assert.equal(selectionVisibility(projected, [], []), 'hidden-layer');
  assert.equal(selectionVisibility(projected, ['rings'], [part.id]), 'hidden-part');
  assert.equal(selectionVisibility(undefined, ['rings'], []), 'unavailable');
  assert.deepEqual(visibleDrawingParts([projected,second], ['rings'], [part.id], false, part.id), [second]);
  assert.deepEqual(visibleDrawingParts([projected,second], ['rings'], [], true, part.id), [projected]);
  assert.deepEqual(visibleDrawingParts([projected,second], [], [], true, part.id), []);
  assert.equal(projected.part.id, part.id);
});

test('exported SVG includes legend, source maturity, visibility and unavailable details', async () => {
  const vehicle = { id: 'historical-fixture', label: 'Recorded fixture', identity: { resolved_spec_sha256: 'exact-source-hash' }, summary: {},
    parts: [part, { ...part, id: 'missing-geometry', name: 'Missing geometry', dimensions: {} }] };
  const server = await createServer({ configFile: false, root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' });
  try {
    const { OrthographicDesign } = await server.ssrLoadModule('/src/design/OrthographicDesign.tsx');
    const render = (props) => renderToStaticMarkup(React.createElement(OrthographicDesign, { vehicle, onSelectPart() {}, ...props }));
    const visible = render({ selectedPartId: part.id });
    const svg = visible.slice(visible.indexOf('<svg'), visible.indexOf('</svg>'));
    assert.match(svg, /Dashed: bounding envelope/);
    assert.match(svg, /source role: concept/);
    assert.match(svg, /exact-source-hash/);
    assert.match(svg, /highlight is an annotation/);
    assert.match(svg, /selected_visibility/);
    assert.match(visible, /aria-label="Select source component"/);
    const hidden = render({ selectedPartId: part.id, hiddenPartIds: [part.id], onRevealPart() {} });
    assert.match(hidden, /Reveal &amp; focus selection/);
    assert.match(hidden, /hidden by the shared parts visibility control/);
    assert.doesNotMatch(hidden, /<polygon/);
    const unavailable = render({ selectedPartId: 'missing-geometry' });
    assert.match(unavailable, /Drawing geometry unavailable; no replacement shape is inferred/);
    assert.match(unavailable.slice(unavailable.indexOf('<svg'), unavailable.indexOf('</svg>')), /missing-geometry: Positive source length and outer radius unavailable/);
    const foreign = render({ selectedPartId: 'part-from-another-source' });
    assert.match(foreign, /is not recorded in this source/);
    assert.match(foreign, /No geometry is mapped/);
    assert.doesNotMatch(svg, /G80-F2/);
  } finally { await server.close(); }
});
