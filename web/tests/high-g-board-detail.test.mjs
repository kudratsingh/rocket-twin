import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

test('manufacturer PCB detail requires exact source and preserves drawing limitations', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { default: HighGBoardDetail, matchesHighGBoardSource } = await server.ssrLoadModule(
      '/src/components/HighGBoardDetail.tsx',
    );
    const props = {
      partId: 'high_g_accel',
      configurationId: 'G80-F2-RP1-AD1-definition-v2',
      specificationSha256: '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660',
    };
    const render = (values) => renderToStaticMarkup(React.createElement(HighGBoardDetail, values));
    assert.equal(matchesHighGBoardSource(props), true);
    for (const override of [
      { partId: 'imu' },
      { configurationId: 'historical' },
      { specificationSha256: null },
      { specificationSha256: 'wrong' },
    ]) {
      assert.equal(render({ ...props, ...override }), '');
    }
    const html = render(props);
    assert.match(html, /26 source placements/);
    assert.match(html, /25.4 × 17.78 mm/);
    assert.match(html, /25.6 × 17.7 × 4.6 mm/);
    assert.match(html, /ADXL343/);
    assert.match(html, /height undefined/);
    assert.match(html, /CC BY-SA 3.0/);
    assert.match(html, /7c089eb8cc0756b7dc5e30abd240978dc272113d93f602b497f8f442d532d68c/);
    assert.equal((html.match(/role="button"/g) ?? []).length, 26);
    assert.equal((html.match(/r="1.25"/g) ?? []).length, 4);
    assert.match(html, /Export SVG with provenance/);
  } finally {
    await server.close();
  }
});
