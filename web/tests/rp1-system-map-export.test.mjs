import assert from 'node:assert/strict';
import test from 'node:test';
import {
  buildRp1SystemMapSvg,
  RP1_SYSTEM_MAP_SOURCE_COMMIT,
} from '../src/workbench/rp1SystemMapExport.ts';
import {
  RP1_SYSTEM_MAP_CONFIGURATION,
  RP1_SYSTEM_MAP_SPEC_SHA256,
  SYSTEM_MAPS,
} from '../src/workbench/rp1SystemMapData.ts';

const graphSvgMarkup =
  '<svg xmlns="http://www.w3.org/2000/svg" x="20" y="131" width="1150" height="400" viewBox="0 -45 1150 400"><path d="M 1 2 L 3 4" style="stroke:#80b8c7"/><text x="5" y="6" style="fill:#fff">E1</text></svg>';
const request = (overrides = {}) => ({
  configurationId: RP1_SYSTEM_MAP_CONFIGURATION,
  specificationSha256: RP1_SYSTEM_MAP_SPEC_SHA256,
  mode: 'g80',
  selectedId: 'plant',
  graphSvgMarkup,
  ...overrides,
});

test('portable current-mode sheet carries actual graph, every flow and selected source detail', () => {
  const exported = buildRp1SystemMapSvg(request());
  assert.equal(exported.filename, 'rp1-system-map-g80-811b3bed631f.svg');
  assert.match(
    exported.content,
    /<svg xmlns="http:\/\/www.w3.org\/2000\/svg" width="1600" height="980"/,
  );
  assert.match(exported.content, /<path d="M 1 2 L 3 4" style="stroke:#80b8c7"/);
  assert.match(exported.content, /Flow key/);
  assert.match(exported.content, /Current G80 · unguided/);
  assert.match(exported.content, /Signal \/ frame/);
  assert.match(exported.content, /src\/sim\/dynamics.py/);
  assert.match(exported.content, /complete RP1 flight\/inertia inputs unavailable/i);
  assert.match(exported.content, /Independent recovery is outside the ascent-control loop/);
  assert.match(exported.content, /physical and flight acceptance remain open/);
  assert.match(exported.content, new RegExp(RP1_SYSTEM_MAP_SPEC_SHA256));
  assert.match(exported.content, new RegExp(RP1_SYSTEM_MAP_SOURCE_COMMIT));
  assert.equal(exported.metadata.nodes.length, SYSTEM_MAPS.g80.nodes.length);
  assert.deepEqual(exported.metadata.edges, SYSTEM_MAPS.g80.edges);
  for (const [index, edge] of SYSTEM_MAPS.g80.edges.entries()) {
    assert.match(exported.content, new RegExp(`E${index + 1}`));
    assert.ok(exported.content.includes(`${edge.label} · ${edge.status}`));
  }
  assert.doesNotMatch(exported.content, /<script|<image|<foreignObject|@import|<link/);
});

test('future G12 sheet retains planned controller and distinct mode name', () => {
  const exported = buildRp1SystemMapSvg(request({ mode: 'g12', selectedId: 'control' }));
  assert.match(exported.filename, /rp1-system-map-g12-/);
  assert.match(exported.content, /Future G12 · PID → RL/);
  assert.match(
    exported.content,
    /gains, policy, installed actuator and safe abort remain unqualified/,
  );
  assert.match(exported.content, /configs\/control\/pid.yaml/);
  assert.equal(exported.metadata.selected_block.status, 'planned');
  assert.deepEqual(exported.metadata.edges, SYSTEM_MAPS.g12.edges);
});

test('foreign source, stale selection and nonportable graph markup are rejected', () => {
  assert.throws(
    () => buildRp1SystemMapSvg(request({ configurationId: 'foreign' })),
    /exact current RP1/,
  );
  assert.throws(
    () => buildRp1SystemMapSvg(request({ specificationSha256: '0'.repeat(64) })),
    /exact current RP1/,
  );
  assert.throws(
    () => buildRp1SystemMapSvg(request({ selectedId: 'missing' })),
    /Selected system-map block/,
  );
  assert.throws(
    () => buildRp1SystemMapSvg(request({ graphSvgMarkup: '<svg><script>alert(1)</script></svg>' })),
    /self-contained SVG/,
  );
  assert.throws(
    () =>
      buildRp1SystemMapSvg(
        request({ graphSvgMarkup: '<svg><image href="https://example.com/a.png"/></svg>' }),
      ),
    /self-contained SVG/,
  );
});
