import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const spec = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
const part = (id, mesh) => ({
  id,
  name: id,
  type: 'source_reference',
  parent: null,
  material: 'recorded material',
  learn: 'Source display fixture',
  mesh_url: mesh ? `/fixture/${id}.glb` : null,
  geometry: { length_m: 0.1 },
});

async function withDesign(run) {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { DesignVisual } = await server.ssrLoadModule('/src/workspaces/DesignVisual.tsx');
    const render = (vehicle) =>
      renderToStaticMarkup(
        React.createElement(DesignVisual, {
          vehicle,
          meshView: React.createElement(
            'div',
            { id: 'existing-canvas-fixture' },
            '3D stays mounted',
          ),
        }),
      );
    await run(render);
  } finally {
    await server.close();
  }
}

test('RP1 Design exposes grouped View, Inspect, Source and Alternatives controls in normal header flow', async () => {
  await withDesign((render) => {
    const vehicle = {
      id: 'G80-F2-RP1-AD1-definition-v2',
      label: 'RP1 source fixture',
      identity: {
        specification_sha256: spec,
        inspection_geometry_sha256:
          '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608',
      },
      parts: [part('body', true), part('fin_set', true), part('fin_tabs', true)],
      summary: { inspection_geometry: { status: 'synthetic display fixture' } },
    };
    const html = render(vehicle);
    for (const group of [
      'View representation',
      'Inspect assembly',
      'Source detail',
      'Alternatives',
    ])
      assert.match(html, new RegExp(`role="group" aria-label="${group}"`));
    for (const control of [
      '3D model',
      '2D dimensions',
      'Inspect interior',
      'Inspect subsystem',
      'Adjust section cut',
      'Detail coverage',
      'Fin alternatives',
      'Preliminary source',
    ])
      assert.ok(html.includes(control), control);
    assert.match(html, /class="research-source-context"/);
    assert.match(html, /id="existing-canvas-fixture"/);
    assert.match(html, /<details[^>]*class="interior-coverage"/);
    assert.doesNotMatch(html, /Add part|Replace part|Connect parts/);
  });
});

test('a source without matching 3D or RP1 alternatives retains the drawing and explicit unavailable controls', async () => {
  await withDesign((render) => {
    const vehicle = {
      id: 'separate-source-fixture',
      label: 'Separate source fixture',
      identity: { specification_sha256: 'not-rp1' },
      parts: [part('only_part', false)],
      summary: {},
    };
    const html = render(vehicle);
    assert.match(html, /data-representation="2d"/);
    assert.match(html, /<button[^>]*disabled=""[^>]*>3D recorded geometry<\/button>/);
    assert.match(html, /2D dimensions/);
    assert.match(html, /Detail coverage/);
    assert.match(html, /Loading optional source-detail catalog/);
    assert.doesNotMatch(html, /Fin alternatives/);
    assert.match(html, /Source drawing \/ concept · matching 3D assembly unavailable/);
  });
});
