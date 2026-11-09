import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { sourceDimensionPositions } from '../src/components/sourceDimensionPositions.ts';

// Recorded source data, not dimensions reverse-engineered from screen pixels or CAD bounds.
const manifest = JSON.parse(
  readFileSync(
    new URL('../public/engineering-workbench/rp1-detail/manifest.json', import.meta.url),
  ),
);
const recorded = manifest.annotations.find((annotation) => annotation.id === 'ring-bore');
const bore = {
  id: recorded.id,
  partId: recorded.part_id,
  label: recorded.label,
  value: recorded.value,
  units: recorded.units,
  from: recorded.from_m,
  to: recorded.to_m,
  source: recorded.source,
  annotationOnly: recorded.annotation_only,
};
function input(overrides = {}) {
  return {
    annotations: [bore],
    selectedIds: ['forward_ring'],
    visibleIds: ['forward_ring', 'motor_tube'],
    displayOffsets: new Map(),
    ...overrides,
  };
}

test('recorded 31.9 mm bore retains source endpoints and applies its own display offset once', () => {
  assert.equal(bore.value, 31.9);
  assert.deepEqual(bore.from, [-0.01595, 0.18390000000000017, 0]);
  assert.deepEqual(bore.to, [0.01595, 0.18390000000000017, 0]);
  const offset = Object.freeze([0.24, -0.1, 0.03]);
  const offsets = new Map([
    ['forward_ring', offset],
    ['motor_tube', [9, 8, 7]],
  ]);
  const raw = JSON.stringify(bore);
  const state = input({ displayOffsets: offsets });
  const [guide] = sourceDimensionPositions(state);
  assert.deepEqual(
    guide.from,
    bore.from.map((value, index) => value + offset[index]),
  );
  assert.deepEqual(
    guide.to,
    bore.to.map((value, index) => value + offset[index]),
  );
  assert.deepEqual(
    guide.midpoint,
    guide.from.map((value, index) => value / 2 + guide.to[index] / 2),
  );
  assert.equal(guide.label, 'Recorded ring bore · 31.9 mm');
  assert.match(guide.title, /configs\/vehicle\/candidates\/g80-f2-rp1-ad1-v2.yaml/);
  assert.ok(guide.title.includes(bore.source.sha256));
  assert.ok(guide.title.includes(bore.source.locator));
  assert.match(guide.title, /may remain visible across a section cut/);
  assert.equal(guide.contributesGeometryBounds, false);
  assert.equal(guide.annotationOnly, true);
  assert.notEqual(guide.from, bore.from);
  assert.notEqual(guide.to, bore.to);
  assert.equal(JSON.stringify(bore), raw);
  assert.deepEqual(
    sourceDimensionPositions(state)[0],
    guide,
    'repeated rendering does not accumulate offsets',
  );
  assert.deepEqual(offset, [0.24, -0.1, 0.03]);
});

test('no selection, hidden source, foreign part and missing annotations produce no guide', () => {
  for (const overrides of [
    { selectedIds: [] },
    { selectedIds: ['motor_tube'] },
    { visibleIds: ['motor_tube'] },
    { visibleIds: [] },
    { annotations: [] },
    { annotations: null },
    { annotations: undefined },
    { annotations: [{ ...bore, partId: 'foreign_part' }] },
  ])
    assert.deepEqual(sourceDimensionPositions(input(overrides)), []);
  assert.deepEqual(
    sourceDimensionPositions(input())[0].from,
    bore.from,
    'assembled state uses source positions',
  );
});

test('malformed/nonfinite endpoints, offsets and source dimensions are suppressed without altering input', () => {
  const raw = JSON.stringify(bore);
  for (const override of [
    { from: [NaN, 0, 0] },
    { to: [0, Infinity, 0] },
    { from: [0, 0] },
    { to: null },
    { from: bore.to },
    { value: NaN },
    { value: Infinity },
    { value: 0 },
    { value: -1 },
    { units: 'm' },
    { annotationOnly: false },
    { source: null },
    { source: { ...bore.source, sha256: 'unverified' } },
    { source: { ...bore.source, locator: '' } },
  ])
    assert.deepEqual(
      sourceDimensionPositions(input({ annotations: [{ ...bore, ...override }] })),
      [],
    );
  for (const offset of [
    [NaN, 0, 0],
    [0, Infinity, 0],
    [0, 0],
  ])
    assert.deepEqual(
      sourceDimensionPositions(input({ displayOffsets: new Map([['forward_ring', offset]]) })),
      [],
    );
  assert.equal(JSON.stringify(bore), raw);
});

test('rendered guide owns a line, two endpoint decorations and a midpoint label without fit registration', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { SourceDimensionOverlay } = await server.ssrLoadModule(
      '/src/components/SourceDimensionOverlay.tsx',
    );
    assert.equal(SourceDimensionOverlay(input({ selectedIds: [] })), null);
    const tree = SourceDimensionOverlay(input());
    assert.equal(tree.props.name, 'source-dimension-guides');
    assert.equal(tree.props.userData.contributesGeometryBounds, false);
    const [segment, endpoints, label] = tree.props.children[0].props.children;
    assert.deepEqual(segment.props.points, [bore.from, bore.to]);
    assert.equal(segment.props.depthTest, false);
    assert.deepEqual(segment.props.clippingPlanes, []);
    assert.equal(endpoints.length, 2);
    assert.deepEqual(
      endpoints.map((endpoint) => endpoint.props.position),
      [bore.from, bore.to],
    );
    assert.deepEqual(label.props.position, [0, bore.from[1], 0]);
    assert.equal(label.props.lines[0].text, 'Recorded ring bore · 31.9 mm');
    assert.equal(label.props.lines.length, 2);
    assert.match(label.props.lines[1].text, /Source nominal/);
    assert.match(label.props.title, /section cut/);
    assert.equal(label.props.pointerEvents, 'none');
    assert.equal(label.props.contentClassName, 'source-dimension-label');
    assert.ok(label.props.title.includes(bore.source.sha256));
    assert.equal(label.props.onLoaded, undefined);
  } finally {
    await server.close();
  }
});
