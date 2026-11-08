import assert from 'node:assert/strict';
import test from 'node:test';
import { readdir } from 'node:fs/promises';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { exactReplayTime } from '../src/experiments/replayTimeValue.ts';

test('exact saved T+11.150 is reachable independently of slider min/step and preserved without rounding', () => {
  assert.deepEqual(exactReplayTime('11.150', 0.001, 132.856), { ok: true, time: 11.15 });
  assert.deepEqual(exactReplayTime('0.001', 0.001, 132.856), { ok: true, time: 0.001 });
  assert.deepEqual(exactReplayTime('132.856', 0.001, 132.856), { ok: true, time: 132.856 });
  assert.deepEqual(exactReplayTime('11.150123', 0.001, 132.856), { ok: true, time: 11.150123 });
  assert.deepEqual(exactReplayTime('-2.125', -10, 40), { ok: true, time: -2.125 });
});

test('invalid or outside-window drafts are rejected with clear errors and cannot change a cursor', () => {
  for (const value of ['', ' ', 'not a number', 'Infinity', '-Infinity', 'NaN']) {
    const result = exactReplayTime(value, 0.001, 132.856);
    assert.equal(result.ok, false);
    assert.match(result.reason, /finite time in seconds/);
  }
  for (const value of ['0', '132.857', '-3']) {
    const result = exactReplayTime(value, 0.001, 132.856);
    assert.equal(result.ok, false);
    assert.match(result.reason, /recorded replay window/);
  }
  assert.match(exactReplayTime('11.150', NaN, 132.856).reason, /unavailable/);
  assert.match(exactReplayTime('11.150', 10, 1).reason, /unavailable/);
});

test('exact-time control exposes seconds, inclusive clock context, any decimal step and keyboard submission', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { ExactReplayTime } = await server.ssrLoadModule('/src/experiments/ExactReplayTime.tsx');
    const { default: Experiment } = await server.ssrLoadModule('/src/experiments/Experiment.tsx');
    assert.equal(typeof Experiment, 'function');
    const render = (aligned) =>
      renderToStaticMarkup(
        React.createElement(ExactReplayTime, {
          time: 11.15,
          start: 0.001,
          end: 132.856,
          aligned,
          onApply: () => {},
        }),
      );
    const html = render(false);
    assert.match(html, /Exact replay time \(seconds, elapsed clock\)/);
    assert.match(html, /type="number"/);
    assert.match(html, /step="any"/);
    assert.match(html, /type="submit"/);
    assert.match(html, /Go to exact time/);
    assert.match(html, /Enter\/Go pauses at the exact value/);
    assert.match(html, /Escape resets the draft/);
    assert.match(html, /aria-describedby=/);
    assert.match(html, /aria-invalid="false"/);
    assert.match(render(true), /aligned clock/);
  } finally {
    await server.close();
  }
});

test('actual component/helper paths stay distinct ignoring case and extension', async () => {
  const names = await readdir(new URL('../src/experiments/', import.meta.url));
  const relevant = names.filter((name) =>
    /^(ExactReplayTime|exactReplayTime|replayTimeValue)\.(ts|tsx)$/.test(name),
  );
  assert.ok(relevant.includes('ExactReplayTime.tsx'));
  assert.ok(relevant.includes('replayTimeValue.ts'));
  const stems = relevant.map((name) => name.replace(/\.[^.]+$/, '').toLowerCase());
  assert.equal(
    new Set(stems).size,
    relevant.length,
    'No .ts helper can shadow the .tsx component on macOS',
  );
});
