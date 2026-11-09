import assert from 'node:assert/strict';
import test from 'node:test';

test('browser-size information cannot masquerade as an operating resize control or acceptance result', async () => {
  const { createServer } = await import('vite');
  const { default: React } = await import('react');
  const { renderToStaticMarkup } = await import('react-dom/server');
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { ViewportVerificationPanel } = await server.ssrLoadModule(
      '/src/workspaces/ViewportVerification.tsx',
    );
    const render = (width, height) =>
      renderToStaticMarkup(
        React.createElement(ViewportVerificationPanel, {
          observation: { width, height, dpr: 2 },
          onClose: () => {},
        }),
      );
    const different = render(1965, 1074);
    const same = render(1440, 900);
    assert.match(different, /1965.*1074.*CSS px/);
    assert.doesNotMatch(different, /matches current dimensions/);
    assert.match(same, /matches current dimensions; layout acceptance is still separate/);
    for (const html of [same, different]) {
      assert.doesNotMatch(html, /<select|<input/);
      assert.match(html, /cannot resize Chrome or change page zoom/);
      assert.match(html, /not resize controls/);
      assert.match(html, /Exact-size cases remain pending/);
      assert.match(html, /Hide size information/);
      assert.match(html, /does not by itself.*establish page zoom/);
    }
  } finally {
    await server.close();
  }
});
