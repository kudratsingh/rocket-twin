import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import {
  matchesRp1SystemMapSource,
  RP1_SYSTEM_MAP_CONFIGURATION,
  RP1_SYSTEM_MAP_SPEC_SHA256,
  SYSTEM_MAPS,
  systemMapNode,
} from '../src/workbench/rp1SystemMapData.ts';

test('system map admits only exact current RP1 configuration and specification', () => {
  assert.equal(
    matchesRp1SystemMapSource(RP1_SYSTEM_MAP_CONFIGURATION, RP1_SYSTEM_MAP_SPEC_SHA256),
    true,
  );
  assert.equal(
    matchesRp1SystemMapSource('G80-F2-RP1-AD1-definition-v1', RP1_SYSTEM_MAP_SPEC_SHA256),
    false,
  );
  assert.equal(matchesRp1SystemMapSource(RP1_SYSTEM_MAP_CONFIGURATION, null), false);
  assert.equal(matchesRp1SystemMapSource(RP1_SYSTEM_MAP_CONFIGURATION, '0'.repeat(64)), false);
});

test('every graph edge resolves to a displayed node and marks its maturity', () => {
  for (const graph of Object.values(SYSTEM_MAPS)) {
    const ids = new Set(graph.nodes.map((node) => node.id));
    assert.equal(ids.size, graph.nodes.length);
    for (const edge of graph.edges) {
      assert.ok(ids.has(edge.from));
      assert.ok(ids.has(edge.to));
      assert.ok(
        ['implemented model', 'source definition', 'planned', 'unavailable'].includes(edge.status),
      );
    }
    for (const node of graph.nodes) {
      assert.ok(node.source.every((path) => !path.startsWith('/') && !path.includes('..')));
      assert.ok(node.detail.length > 30);
      assert.ok(node.signal.length > 10);
    }
  }
});

test('current G80 cannot be read as an active control or completed RP1 flight path', () => {
  assert.equal(systemMapNode('g80', 'inputs').status, 'unavailable');
  assert.match(systemMapNode('g80', 'inputs').detail, /missing complete flight\/inertia/);
  assert.match(systemMapNode('g80', 'plant').detail, /gimbal locked/);
  assert.equal(systemMapNode('g80', 'recovery').status, 'source definition');
  assert.equal(systemMapNode('g80', 'control'), null);
  assert.ok(
    SYSTEM_MAPS.g80.edges.some((edge) => edge.from === 'inputs' && edge.to === 'environment'),
  );
  assert.ok(
    SYSTEM_MAPS.g80.edges.some(
      (edge) =>
        edge.from === 'inputs' &&
        edge.to === 'forces' &&
        edge.label === 'motor curve' &&
        edge.status === 'unavailable',
    ),
  );
  assert.ok(
    SYSTEM_MAPS.g80.edges.some(
      (edge) =>
        edge.from === 'inputs' &&
        edge.to === 'plant' &&
        edge.label === 'mass / CG / inertia' &&
        edge.status === 'unavailable',
    ),
  );
});

test('future G12 chain has no implemented controller gains or adopted hardware', () => {
  assert.equal(systemMapNode('g12', 'estimate').status, 'planned');
  assert.equal(systemMapNode('g12', 'guide').status, 'planned');
  assert.equal(systemMapNode('g12', 'control').status, 'planned');
  assert.match(systemMapNode('g12', 'control').detail, /gains are null/);
  assert.match(systemMapNode('g12', 'actuator').detail, /current G80 gimbal is locked/);
  assert.ok(
    SYSTEM_MAPS.g12.edges.some((edge) => edge.from === 'actuator' && edge.to === 'vehicle'),
  );
});

test('rendered map exposes selectable source blocks and refuses a foreign source', async () => {
  const vite = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
    logLevel: 'silent',
  });
  try {
    const { default: Rp1SystemMap } = await vite.ssrLoadModule('/src/workbench/Rp1SystemMap.tsx');
    const valid = renderToStaticMarkup(
      React.createElement(Rp1SystemMap, {
        configurationId: RP1_SYSTEM_MAP_CONFIGURATION,
        specificationSha256: RP1_SYSTEM_MAP_SPEC_SHA256,
      }),
    );
    assert.match(valid, /Current G80 · unguided/);
    assert.match(valid, /role="button" tabindex="0"/);
    assert.match(valid, /source-bound rocket system map/i);
    assert.match(valid, /Complete RP1 flight\/inertia inputs are unavailable/);
    const foreign = renderToStaticMarkup(
      React.createElement(Rp1SystemMap, {
        configurationId: 'other',
        specificationSha256: RP1_SYSTEM_MAP_SPEC_SHA256,
      }),
    );
    assert.match(foreign, /System map unavailable for this source/);
    assert.doesNotMatch(foreign, /6DOF \/ RK4 plant/);
  } finally {
    await vite.close();
  }
});
