import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

test('draft panel render/load failures have a source-return fallback without retry or raw markup', async () => {
  const vite = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
    logLevel: 'silent',
  });
  try {
    const { DraftLibraryBoundary } = await vite.ssrLoadModule(
      '/src/design-builder/DraftLibraryBoundary.tsx',
    );
    const boundary = new DraftLibraryBoundary({
      children: 'Original panel',
      onReturnToSource() {},
    });
    assert.equal(boundary.render(), 'Original panel');
    const message = '<script>not markup</script>' + 'x'.repeat(700);
    boundary.state = DraftLibraryBoundary.getDerivedStateFromError(new Error(message));
    assert.equal(boundary.state.diagnostic.length, 500);
    const html = renderToStaticMarkup(boundary.render());
    assert.match(html, /Draft library could not load/);
    assert.match(html, /Return to frozen rocket/);
    assert.match(html, /No draft save is/);
    assert.match(html, /&lt;script&gt;not markup&lt;\/script&gt;/);
    assert.doesNotMatch(html, /<script>/);
    assert.doesNotMatch(html, />Retry|>Fork|>Save/);
    assert.equal(
      DraftLibraryBoundary.getDerivedStateFromError(null).diagnostic,
      'Unknown client exception',
    );
    // This exercises fallback rendering/escaping. Actual browser exception capture
    // and preserved camera remain native checks, not SSR acceptance.
    assert.ok(React);
  } finally {
    await vite.close();
  }
});
