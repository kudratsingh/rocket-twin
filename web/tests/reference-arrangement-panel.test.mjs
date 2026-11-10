import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

test('optional arrangement begins with explicit preparation and makes no automatic request', async () => {
  const vite = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
    logLevel: 'silent',
  });
  const original = globalThis.fetch;
  let requests = 0;
  globalThis.fetch = async () => {
    requests++;
    throw new Error('No automatic preparation');
  };
  try {
    const { default: Panel } = await vite.ssrLoadModule(
      '/src/parts-bank/ReferenceArrangementPanel.tsx',
    );
    const html = renderToStaticMarkup(React.createElement(Panel));
    assert.match(html, /Unsaved local reference arrangement/);
    assert.match(html, /Prepare empty arrangement/);
    assert.match(html, /leaving this panel resets the arrangement/);
    assert.match(html, /No fit, connection, mass/);
    assert.doesNotMatch(html, /<canvas|<form|Apply translation|Saved draft UUID/);
    assert.equal(requests, 0);
  } finally {
    globalThis.fetch = original;
    await vite.close();
  }
});
