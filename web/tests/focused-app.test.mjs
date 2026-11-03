import assert from 'node:assert/strict';
import test from 'node:test';
import { URL } from 'node:url';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

test('app mounts focused navigation without requiring a catalog to expose other workspaces', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { default: App } = await server.ssrLoadModule('/src/App.tsx');
    const html = renderToStaticMarkup(React.createElement(App));
    for (const workspace of ['design', 'engineering', 'experiments', 'replay', 'analysis'])
      assert.ok(html.includes(`workspace=${workspace}`));
    assert.match(html, /Preliminary design/);
    assert.match(html, /G80-F2/);
    assert.doesNotMatch(html, /class="app-shell"/);
    assert.doesNotMatch(html, /G80 \/ C1 engineering walkthrough/);
    assert.match(html, /Loading resolved configuration/);
  } finally {
    await server.close();
  }
});
