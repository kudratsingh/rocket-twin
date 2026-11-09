import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

test('manufacturer mounting centres and selected placement remain exact source data', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const data = await server.ssrLoadModule('/src/components/highGMountingData.ts');
    const { default: HighGMountingReference } = await server.ssrLoadModule(
      '/src/components/HighGMountingReference.tsx',
    );
    const props = {
      partId: 'high_g_accel',
      configurationId: 'G80-F2-RP1-AD1-definition-v2',
      specificationSha256: '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660',
      boardLayoutId: 'adafruit-5374-pcb-2d-4a768fc9-v1',
      boardSourceSha256: '7c089eb8cc0756b7dc5e30abd240978dc272113d93f602b497f8f442d532d68c',
    };
    assert.equal(data.matchesHighGMountingSource(props), true);
    const reference = data.highGMountingReference(props, 'U1');
    assert.equal(reference.units, 'mm');
    assert.match(reference.frame, /Manufacturer PCB XY, origin retained, \+Y up/);
    assert.deepEqual(
      reference.holes.map(({ ref, center_mm, diameter_mm }) => [ref, center_mm, diameter_mm]),
      [
        ['U$1', [2.54, 15.24], 2.5],
        ['U$17', [22.86, 15.24], 2.5],
        ['U$19', [2.54, 2.54], 2.5],
        ['U$21', [22.86, 2.54], 2.5],
      ],
    );
    assert.deepEqual(reference.pcb_size_mm, [25.4, 17.78]);
    assert.deepEqual(reference.nominal_product_envelope_mm, [25.6, 17.7, 4.6]);
    assert.equal(reference.mating_tolerance_mm, null);
    assert.equal(reference.selected_placement.ref, 'U1');
    assert.equal(reference.selected_placement.value, 'ADXL343');
    assert.deepEqual(reference.selected_placement.position_mm, [12.7, 8.636]);
    assert.equal(reference.selected_placement.height_mm, null);
    assert.equal(reference.license.spdx, 'CC-BY-SA-3.0');
    assert.match(reference.license.upstream_notice, /Creative Commons Attribution\/Share-Alike/);
    assert.equal(reference.engineering_accepted, false);

    const sourceJson = JSON.parse(data.highGBoardSourceJson(props));
    assert.equal(sourceJson.placements.length, 26);
    assert.equal(sourceJson.placements.find((item) => item.ref === 'U1').height_mm, null);
    assert.equal(sourceJson.source.sha256, props.boardSourceSha256);
    assert.equal(sourceJson.license.spdx, 'CC-BY-SA-3.0');

    const html = renderToStaticMarkup(React.createElement(HighGMountingReference, props));
    assert.match(html, /manufacturer mounting reference/);
    assert.match(html, /Source mounting-hole centres in manufacturer XY/);
    assert.match(html, /not a qualified drill template or build permission/);
    assert.match(html, /height unavailable/);
    assert.match(html, /Download selected placement and mounting JSON/);
    assert.match(html, /Download exact tracked board source JSON/);
    assert.equal((html.match(/<tbody><tr>/g) ?? []).length, 1);
    assert.equal((html.match(/<tr>/g) ?? []).length, 5);
  } finally {
    await server.close();
  }
});

test('foreign revision and unknown placement fail closed', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const data = await server.ssrLoadModule('/src/components/highGMountingData.ts');
    const { default: HighGMountingReference } = await server.ssrLoadModule(
      '/src/components/HighGMountingReference.tsx',
    );
    const props = {
      partId: 'high_g_accel',
      configurationId: 'G80-F2-RP1-AD1-definition-v2',
      specificationSha256: '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660',
    };
    for (const change of [
      { partId: 'imu' },
      { configurationId: 'other' },
      { specificationSha256: null },
      { boardLayoutId: 'stale' },
      { boardSourceSha256: 'foreign' },
    ]) {
      const stale = { ...props, ...change };
      assert.equal(data.matchesHighGMountingSource(stale), false);
      assert.equal(data.highGMountingReference(stale, 'U1'), null);
      assert.equal(data.highGBoardSourceJson(stale), null);
      const html = renderToStaticMarkup(React.createElement(HighGMountingReference, stale));
      assert.match(html, /Manufacturer mounting reference unavailable/);
      assert.doesNotMatch(html, /Download exact tracked board source JSON/);
    }
    assert.equal(data.highGMountingReference(props, 'unlisted'), null);
    const selected = data.highGMountingReference(props, 'U$1');
    assert.equal(selected.selected_placement.ref, 'U$1');
    assert.equal(selected.selected_placement.height_mm, null);
  } finally {
    await server.close();
  }
});
