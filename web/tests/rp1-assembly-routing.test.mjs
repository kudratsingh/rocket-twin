import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import {
  engineeringHref,
  engineeringRoute,
  isConstructionTopic,
} from '../src/workbench/workbenchRouting.ts';

const core = JSON.parse(
  readFileSync(
    new URL('../../docs/studies/rp1-inspection-geometry-20261107/manifest.json', import.meta.url),
  ),
);
const source = JSON.parse(
  readFileSync(new URL('./fixtures/rp1-draft-library.json', import.meta.url)),
).source.inspection;
// Actual source-only inspection plus the matching recorded geometry identity.
// No geometry/model/result is invented or generated for this route check.
const inspection = { ...source, identity: { ...core.identity } };
const route = `/?workspace=engineering&view=rp1-assembly&design=${core.id}&spec=${core.identity.specification_sha256}&part=aft_ring`;

test('RP1 assembly is a distinct source-bound Engineering topic', () => {
  assert.equal(
    engineeringRoute(new URL(route, 'http://local.invalid').search).view,
    'rp1-assembly',
  );
  assert.equal(isConstructionTopic('rp1-assembly'), true);
  assert.equal(engineeringRoute('?view=assembly').view, 'assembly');
  const next = new URL(engineeringHref(route, 'rp1-assembly'), 'http://local.invalid');
  assert.equal(next.searchParams.get('design'), core.id);
  assert.equal(next.searchParams.get('spec'), core.identity.specification_sha256);
  assert.equal(next.searchParams.get('part'), 'aft_ring');
});

test('integrated Engineering route admits current source and refuses missing, foreign or repeated identity', async () => {
  const previous = globalThis.window;
  const vite = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
    logLevel: 'silent',
  });
  try {
    globalThis.window = { location: new URL(route, 'http://local.invalid') };
    const { default: EngineeringWorkbench } = await vite.ssrLoadModule(
      '/src/workbench/EngineeringWorkbench.tsx',
    );
    const render = (vehicle) =>
      renderToStaticMarkup(React.createElement(EngineeringWorkbench, { inspection: vehicle }));
    const html = render(inspection);
    assert.match(html, /How the recorded attachment would be assembled and serviced/);
    assert.match(html, /Failed fin screen/);
    assert.match(html, /8\.83/);
    assert.doesNotMatch(html, /assembly source inspection is loading/);
    assert.match(render(null), /assembly source inspection is loading or unavailable/);
    assert.doesNotMatch(
      render({ ...inspection, id: 'historical' }),
      /How the recorded attachment would be assembled/,
    );
    globalThis.window = { location: new URL(`${route}&spec=foreign`, 'http://local.invalid') };
    const refused = render(inspection);
    assert.match(refused, /RP1 assembly unavailable/);
    assert.doesNotMatch(refused, /How the recorded attachment would be assembled/);
  } finally {
    if (previous === undefined) delete globalThis.window;
    else globalThis.window = previous;
    await vite.close();
  }
});
