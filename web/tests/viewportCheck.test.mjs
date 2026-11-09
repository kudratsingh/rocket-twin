import assert from 'node:assert/strict';
import test from 'node:test';
import {
  VIEWPORT_PRESETS,
  allowedFixtureUrl,
  applyPreset,
  fixedAppUrl,
  presetFor,
  readActualViewport,
} from '../src/dev/viewportCheck.ts';

test('only the three declared CSS presets are accepted', () => {
  assert.deepEqual(VIEWPORT_PRESETS.map((p) => [p.width, p.height]), [
    [1440, 900],
    [1280, 720],
    [900, 720],
  ]);
  assert.equal(presetFor(1440, 900), VIEWPORT_PRESETS[0]);
  assert.equal(presetFor(901, 720), null);
  assert.equal(presetFor(900, 900), null);
});

test('fixture requires exact loopback DEV path and pins a same-origin RP1 app URL', () => {
  const fixture = 'http://127.0.0.1:5173/viewport-check.html';
  assert.equal(allowedFixtureUrl(fixture, true), true);
  assert.equal(allowedFixtureUrl(fixture, false), false);
  const app = new URL(fixedAppUrl(fixture, true));
  assert.equal(app.origin, new URL(fixture).origin);
  assert.equal(app.pathname, '/');
  assert.equal(app.searchParams.get('workspace'), 'design');
  assert.equal(app.searchParams.get('design'), 'G80-F2-RP1-AD1-definition-v2');
  assert.equal(
    app.searchParams.get('spec'),
    '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660',
  );
  for (const bad of [
    'https://127.0.0.1:5173/viewport-check.html',
    'http://localhost.evil:5173/viewport-check.html',
    'http://127.0.0.1:8000/viewport-check.html',
    'http://127.0.0.1:5173/viewport-check.html?src=%2Fviewport-check.html',
    'http://127.0.0.1:5173/viewport-check.html#nested',
    'http://127.0.0.1:5173/?workspace=design',
  ]) {
    assert.equal(allowedFixtureUrl(bad, true), false, bad);
    assert.equal(fixedAppUrl(bad, true), null, bad);
  }
});

test('applying a size changes only the existing iframe CSS box', () => {
  const originalWindow = {};
  const frame = {
    style: { width: '', height: '' },
    contentWindow: originalWindow,
    get src() { return '/?workspace=design'; },
    set src(_) { throw new Error('preset must not reload the iframe'); },
  };
  applyPreset(frame, VIEWPORT_PRESETS[0]);
  assert.equal(frame.style.width, '1440px');
  assert.equal(frame.style.height, '900px');
  applyPreset(frame, VIEWPORT_PRESETS[2]);
  assert.equal(frame.style.width, '900px');
  assert.equal(frame.style.height, '720px');
  assert.equal(frame.contentWindow, originalWindow);
  assert.equal(frame.src, '/?workspace=design');
  assert.throws(() => applyPreset(frame, { width: 200, height: 300 }), /Unsupported/);
});

test('actual readout distinguishes exact match, mismatch and unavailable without zero', () => {
  const frame = {
    contentWindow: { innerWidth: 1440, innerHeight: 900, devicePixelRatio: 2 },
    contentDocument: { documentElement: { clientWidth: 1425, clientHeight: 900 } },
    getBoundingClientRect: () => ({ width: 1440, height: 900 }),
  };
  const exact = readActualViewport(frame, VIEWPORT_PRESETS[0], true);
  assert.equal(exact.requested_matches_actual, true);
  assert.equal(exact.document_client_width, 1425, 'client size is reported, not forced to match');
  frame.contentWindow.innerWidth = 1400;
  assert.equal(readActualViewport(frame, VIEWPORT_PRESETS[0], true).requested_matches_actual, false);
  frame.contentWindow.innerWidth = 1440;
  frame.contentDocument.documentElement.clientWidth = 0;
  assert.equal(
    readActualViewport(frame, VIEWPORT_PRESETS[0], true).requested_matches_actual,
    null,
    'missing document measurement must not report a size match',
  );
  assert.equal(readActualViewport(frame, VIEWPORT_PRESETS[0], false).inner_width, null);
  assert.equal(readActualViewport(frame, VIEWPORT_PRESETS[0], false).requested_matches_actual, null);
  const crossOrigin = {
    get contentWindow() { throw new Error('SecurityError'); },
    get contentDocument() { throw new Error('SecurityError'); },
    getBoundingClientRect: frame.getBoundingClientRect,
  };
  assert.equal(readActualViewport(crossOrigin, VIEWPORT_PRESETS[0], true).inner_width, null);
});
