import assert from 'node:assert/strict';
import test from 'node:test';
import { createServer } from '../node_modules/vite/dist/node/index.js';

test('panel dismissal selects a rendered enabled focus target after responsive layout commits', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  const previousWindow = globalThis.window;
  const previousDocument = globalThis.document;
  try {
    const { restorePanelFocus } = await server.ssrLoadModule('/src/workspaces/workspaceLayoutContext.tsx');
    const queued = [];
    const focused = [];
    const element = (name, patch = {}) => ({
      isConnected: true,
      tabIndex: 0,
      closest: () => null,
      matches: () => false,
      getClientRects: () => [{}],
      visibility: 'visible',
      focus: () => focused.push(name),
      ...patch,
    });
    let toggle = element('toggle');
    globalThis.window = {
      requestAnimationFrame: callback => queued.push(callback),
      getComputedStyle: target => ({ visibility: target.visibility }),
    };
    globalThis.document = { getElementById: () => toggle };
    const opener = element('opener');
    restorePanelFocus('toggle', opener);
    assert.deepEqual(focused, [], 'no focus movement before commit');
    queued.shift()();
    assert.deepEqual(focused, ['opener']);

    // A resize can hide an opener between dismissal and the next frame.
    restorePanelFocus('toggle', opener);
    opener.getClientRects = () => [];
    queued.shift()();
    assert.equal(focused.at(-1), 'toggle');
    for (const patch of [
      { isConnected: false },
      { tabIndex: -1 },
      { closest: selector => selector.includes('[inert]') ? {} : null },
      { closest: selector => selector.includes('[hidden]') ? {} : null },
      { matches: selector => selector === ':disabled' },
      { visibility: 'hidden' },
      { visibility: 'collapse' },
    ]) {
      const count = focused.length;
      restorePanelFocus('toggle', element('unusable', patch));
      queued.shift()();
      assert.equal(focused.length, count + 1);
      assert.equal(focused.at(-1), 'toggle');
    }
    for (const fallback of [null, element('hidden-toggle', { getClientRects: () => [] })]) {
      toggle = fallback;
      const count = focused.length;
      restorePanelFocus('toggle', null);
      queued.shift()();
      assert.equal(focused.length, count, 'unmounted or hidden fallback is not focused');
    }
  } finally {
    if (previousWindow === undefined) delete globalThis.window; else globalThis.window = previousWindow;
    if (previousDocument === undefined) delete globalThis.document; else globalThis.document = previousDocument;
    await server.close();
  }
});
