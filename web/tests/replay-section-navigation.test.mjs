import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { jumpToReplaySection } from '../src/experiments/replaySectionTarget.ts';

function workspace() {
  const root = { isConnected: true, targets: [] };
  root.querySelectorAll = (selector) =>
    root.targets.filter((target) => selector === `[data-replay-section='${target.section}']`);
  return root;
}
function node(root, section, tagName = 'SECTION') {
  const calls = [];
  return {
    section,
    tagName,
    isConnected: true,
    open: false,
    calls,
    closest: () => root,
    focus: (options) => calls.push(['focus', options]),
    scrollIntoView: (options) => calls.push(['scroll', options]),
  };
}

test('section jump is scoped to the originating workspace and focuses before scrolling', () => {
  const a = workspace(),
    b = workspace();
  const origin = node(a),
    own = node(a, 'telemetry'),
    foreign = node(b, 'telemetry');
  // A nested/foreign match can precede the real local target; it is never borrowed.
  a.targets = [foreign, own];
  b.targets = [foreign];
  assert.equal(jumpToReplaySection(origin, 'telemetry'), true);
  assert.deepEqual(own.calls, [
    ['focus', { preventScroll: true }],
    ['scroll', { behavior: 'auto', block: 'start', inline: 'nearest' }],
  ]);
  assert.deepEqual(foreign.calls, []);
  assert.equal(own.open, false);
});

test('missing/disconnected/unsupported destinations cause no unrelated focus or fallback', () => {
  const root = workspace(),
    other = workspace();
  const origin = node(root),
    unrelated = node(other, 'events');
  root.targets = [unrelated];
  for (const section of ['events', 'unknown'])
    assert.equal(jumpToReplaySection(origin, section), false);
  assert.equal(jumpToReplaySection(null, 'events'), false);
  origin.isConnected = false;
  assert.equal(jumpToReplaySection(origin, 'events'), false);
  origin.isConnected = true;
  root.isConnected = false;
  assert.equal(jumpToReplaySection(origin, 'events'), false);
  root.isConnected = true;
  const target = node(root, 'events');
  target.isConnected = false;
  root.targets = [target];
  assert.equal(jumpToReplaySection(origin, 'events'), false);
  assert.equal(jumpToReplaySection(node(null), 'events'), false);
  assert.deepEqual(unrelated.calls, []);
  assert.deepEqual(target.calls, []);
});

test('jump opens only the genuine target details before exposing and focusing its controls', () => {
  const root = workspace(),
    other = workspace();
  const origin = node(root),
    details = node(root, 'details', 'DETAILS');
  const foreign = node(other, 'details', 'DETAILS'),
    unrelated = node(root, 'events', 'DETAILS');
  details.focus = (options) => {
    assert.equal(details.open, true);
    details.calls.push(['focus', options]);
  };
  root.targets = [foreign, unrelated, details];
  assert.equal(jumpToReplaySection(origin, 'details'), true);
  assert.equal(details.open, true);
  assert.equal(foreign.open, false);
  assert.equal(unrelated.open, false);
  assert.deepEqual(foreign.calls, []);
  assert.deepEqual(unrelated.calls, []);
});

test('SSR presents five ordered semantic keyboard buttons without links or form submission', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { ReplaySectionNavigation } = await server.ssrLoadModule(
      '/src/experiments/ReplaySectionNavigation.tsx',
    );
    const html = renderToStaticMarkup(React.createElement(ReplaySectionNavigation));
    assert.match(html, /<nav[^>]*aria-label="Replay sections"/);
    assert.deepEqual(
      [...html.matchAll(/<button type="button">([^<]+)<\/button>/g)].map((match) => match[1]),
      ['Scene', 'Graphs', 'Events', 'Validity', 'Data &amp; limits'],
    );
    assert.ok(!html.includes('<a '));
    assert.ok(!html.includes('tabindex="-1"'));
  } finally {
    await server.close();
  }
});
