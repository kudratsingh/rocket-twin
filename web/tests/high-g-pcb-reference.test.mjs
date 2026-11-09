import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

async function withSource(run) {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const data = await server.ssrLoadModule('/src/components/highGPcbReference.ts');
    await run(server, data);
  } finally {
    await server.close();
  }
}

const exact = {
  partId: 'high_g_accel',
  configurationId: 'G80-F2-RP1-AD1-definition-v2',
  specificationSha256: '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660',
  boardLayoutId: 'adafruit-5374-source-xy-layers-4a768fc9-v1',
  boardSourceSha256: '7c089eb8cc0756b7dc5e30abd240978dc272113d93f602b497f8f442d532d68c',
};

test('exact manufacturer layer data admits only the frozen RP1 board and retains unknown Z', async () => {
  await withSource(async (_, data) => {
    const board = data.highGPcbReference(exact);
    assert.ok(board);
    assert.equal(
      board.frame,
      'Manufacturer board XY,+Yup; no vehicle registration; all features are planar source data',
    );
    assert.deepEqual(board.pcb_size_mm, [25.4, 17.78]);
    assert.equal(board.pcb_thickness_mm, null);
    assert.equal(board.component_heights_available, false);
    assert.deepEqual(
      [
        board.placements.length,
        board.pads.length,
        board.traces.length,
        board.vias.length,
        board.nets.length,
      ],
      [26, 82, 208, 26, 14],
    );
    assert.deepEqual(
      board.mounting_holes.map((h) => [h.ref, h.center_mm, h.radius_mm]),
      [
        ['U$1', [2.54, 15.24], 1.25],
        ['U$17', [22.86, 15.24], 1.25],
        ['U$19', [2.54, 2.54], 1.25],
        ['U$21', [22.86, 2.54], 1.25],
      ],
    );
    assert.equal(board.license.spdx, 'CC-BY-SA-3.0');
    assert.equal(board.placements.find((p) => p.ref === 'U1').value, 'ADXL343');
    assert.ok(board.placements.every((p) => p.height_mm === null));
    assert.ok(board.vias.every((v) => v.diameter_mm === null));
    assert.ok(board.copper_polygon_boundaries.every((p) => p.poured_fill_available === false));
    assert.equal(data.highGPcbReference({ ...exact, boardSourceSha256: 'wrong' }), null);
    assert.equal(data.highGPcbReference({ ...exact, specificationSha256: 'wrong' }), null);
    assert.equal(
      data.highGPcbReference({ ...exact, configurationId: 'modular-performance-v1' }),
      null,
    );
  });
});

test('source-width XY traces, mirrored bottom pads, silk artwork and nets survive conversion', async () => {
  await withSource(async (_, data) => {
    const board = data.highGPcbReference(exact);
    assert.deepEqual(
      data.lineTriangles(
        [
          [0, 0],
          [2, 0],
        ],
        0.4,
      ),
      [0, 0.2, 2, 0.2, 2, -0.2, 0, 0.2, 2, -0.2, 0, -0.2],
    );
    assert.deepEqual(
      data.quadTriangles([0, 0, 1, 0, 1, 1, 0, 1]),
      [0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1],
    );
    assert.ok(
      data.sourceLinePoints(
        [
          [1, 0],
          [0, 1],
        ],
        90,
      ).length > 2,
    );
    assert.equal(board.traces.filter((t) => t.layer === 1).length, 151);
    assert.equal(board.traces.filter((t) => t.layer === 16).length, 57);
    assert.ok(board.traces.every((t) => t.width_mm > 0 && t.points_mm.length === 2));
    const mirroredPad = board.pads.find((p) => p.ref === 'SJ1' && p.name === '1');
    assert.deepEqual(mirroredPad.center_mm, [5.842, 12.7]);
    assert.equal(mirroredPad.layer, 16);
    assert.equal(mirroredPad.net, 'N$2');
    assert.equal(
      board.silkscreen.rectangle_groups.reduce((n, g) => n + g.corners_mm.length, 0),
      4876,
    );
    assert.ok(board.silkscreen.texts.some((t) => t.text === 'VIN' && t.position_mm[0] === 6.35));
    const ground = data.netContactSummary('GND');
    assert.ok(ground.traceCount > 0 && ground.padCount > 0);
    assert.ok(ground.refs.includes('U1'));
    assert.equal(data.netContactSummary('not-a-net'), null);
    assert.deepEqual(data.pcbAxisTicks(25.4), [0, 5, 10, 15, 20, 25, 25.4]);
    assert.deepEqual(data.pcbAxisTicks(17.78), [0, 5, 10, 15, 17.78]);
    assert.deepEqual(data.pcbAxisTicks(0), []);
    assert.deepEqual(data.pcbAxisLabelTicks(25.4), [0, 5, 10, 15, 20, 25.4]);
    assert.deepEqual(data.pcbAxisLabelTicks(17.78), [0, 5, 10, 15, 17.78]);
    assert.deepEqual(data.pcbAxisLabelTicks(20), [0, 5, 10, 15, 20]);
    assert.deepEqual(data.pcbAxisLabelTicks(0), []);
    assert.deepEqual(data.footprintConnectionSummary('U1'), {
      padCount: 14,
      unassignedPadCount: 3,
      nets: ['3.3V', 'CS_3V', 'GND', 'INT1', 'INT2', 'SCL_3V', 'SDA/SDIO_3V', 'SDO'],
    });
    assert.equal(data.footprintConnectionSummary('not-a-ref'), null);
  });
});

test('component controls disclose planar-only meaning and refuse a foreign source', async () => {
  await withSource(async (server) => {
    const { default: HighGPcbReference3D } = await server.ssrLoadModule(
      '/src/components/HighGPcbReference3D.tsx',
    );
    const html = renderToStaticMarkup(React.createElement(HighGPcbReference3D, exact));
    assert.match(html, /source layer explorer/);
    assert.match(html, /Fit board/);
    assert.match(html, /Zoom to selected/);
    assert.match(html, /View top \(camera\)/);
    assert.match(html, /View bottom \(camera\)/);
    assert.match(html, /Show top layers only/);
    assert.match(html, /Show bottom layers only/);
    assert.match(html, /Restore both layers/);
    assert.match(html, /Reset reference view/);
    assert.match(html, /Top source layers/);
    assert.match(html, /Bottom source layers/);
    assert.match(html, /Source XY rulers use millimetres with 5 mm ticks/);
    assert.match(html, /U1 source pads: 14; unassigned source pads: 3/);
    assert.match(html, /Fine silk artwork/);
    assert.match(html, /Highlight source net/);
    assert.match(html, /display spacing only, not actual Z or PCB thickness/);
    assert.match(html, /Board thickness and component\/package heights are unknown/);
    assert.match(html, /Official Eagle U1 value is ADXL343/);
    assert.match(html, /Via copper outer diameters and ground pour fill are unavailable/);
    assert.match(html, /CC BY-SA 3\.0 upstream notice/);
    const denied = renderToStaticMarkup(
      React.createElement(HighGPcbReference3D, { ...exact, partId: 'baro' }),
    );
    assert.match(denied, /Manufacturer PCB layers unavailable/);
    assert.doesNotMatch(denied, /source layer explorer/);
  });
});
