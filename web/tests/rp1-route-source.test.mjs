import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import {
  RP1_CONNECTIONS_CONFIGURATION,
  RP1_CONNECTIONS_SHA256,
} from '../src/workbench/rp1Connections.ts';

const base = {
  workspace: 'engineering',
  view: 'rp1-connections',
  design: RP1_CONNECTIONS_CONFIGURATION,
  spec: RP1_CONNECTIONS_SHA256,
  part: 'fin_tabs',
  connection: 'fin-root',
};
const query = (entries) => `?${new URLSearchParams(entries)}`;

test('actual Engineering route admits exact AD1 context and blocks incompatible or ambiguous source links before its loader', async () => {
  const previousWindow = Object.getOwnPropertyDescriptor(globalThis, 'window');
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { default: EngineeringWorkbench } = await server.ssrLoadModule(
      '/src/workbench/EngineeringWorkbench.tsx',
    );
    function render(search) {
      // Location data only, not a browser, DOM or event implementation. SSR does not run effects.
      Object.defineProperty(globalThis, 'window', {
        configurable: true,
        writable: true,
        value: { location: { search, href: `http://local.test/${search}` } },
      });
      return renderToStaticMarkup(React.createElement(EngineeringWorkbench));
    }
    for (const search of [
      query(base),
      query({ ...base, part: 'rp1_kevlar_wrap', connection: 'recovery' }),
      '?workspace=engineering&view=rp1-connections',
    ]) {
      const html = render(search);
      assert.match(html, /Loading source-pinned AD1 connections/);
      assert.match(html, /class="rp1-connections" role="status"/);
      assert.doesNotMatch(html, /this link has an incompatible/);
      assert.doesNotMatch(html, /Loading.*C1/);
    }

    const invalid = [
      ['archived design', query({ ...base, design: 'modular-performance-v1' })],
      ['wrong specification', query({ ...base, spec: 'b'.repeat(64) })],
      ['stale CAD identity', query({ ...base, cad: 'archived-cad-fingerprint' })],
      ['empty CAD identity', query({ ...base, cad: '' })],
      ['unknown part', query({ ...base, part: 'archived-fixture-part' })],
      ['empty part', query({ ...base, part: '' })],
      ['unknown connection', query({ ...base, connection: 'old-c1' })],
      ['empty connection', query({ ...base, connection: '' })],
      [
        'part without either context field',
        '?workspace=engineering&view=rp1-connections&part=fin_tabs',
      ],
    ];
    for (const key of ['design', 'spec']) {
      const missing = { ...base };
      delete missing[key];
      invalid.push([`missing ${key}`, query(missing)]);
    }
    for (const key of ['design', 'spec', 'part', 'connection']) {
      for (const duplicate of [base[key], 'foreign-value']) {
        const params = new URLSearchParams(base);
        params.append(key, duplicate);
        invalid.push([`duplicate ${key}: ${duplicate}`, `?${params}`]);
      }
    }
    for (const [reason, search] of invalid) {
      const html = render(search);
      assert.match(html, /role="alert"/, reason);
      assert.match(
        html,
        /RP1 connections unavailable: this link has an incompatible design, revision, part or connection/,
        reason,
      );
      assert.match(html, /No historical evidence is substituted/, reason);
      assert.doesNotMatch(html, /Loading source-pinned AD1 connections/, reason);
      assert.doesNotMatch(html, /class="rp1-connections" role="status"/, reason);
    }
  } finally {
    if (previousWindow) Object.defineProperty(globalThis, 'window', previousWindow);
    else delete globalThis.window;
    await server.close();
  }
  assert.deepEqual(
    Object.getOwnPropertyDescriptor(globalThis, 'window'),
    previousWindow,
    'temporary location fixture must not leak into other tests',
  );
});
