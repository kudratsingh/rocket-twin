import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import ts from '../node_modules/typescript/lib/typescript.js';
function target() {
  const listeners = new Map();
  return {
    addEventListener: (n, f) => {
      if (!listeners.has(n)) listeners.set(n, new Set());
      listeners.get(n).add(f);
    },
    removeEventListener: (n, f) => listeners.get(n)?.delete(f),
    emit: (n) => listeners.get(n)?.forEach((f) => f()),
    count: () => [...listeners.values()].reduce((n, s) => n + s.size, 0),
  };
}
test('session adapter records cursor and cached visibility; stopped epochs clean up and freeze independently', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { beginReplaySessionObservation } = await server.ssrLoadModule(
      '/src/experiments/useReplaySessionCapture.ts',
    );
    const document = { ...target(), visibilityState: 'visible', hasFocus: () => true },
      window = target(),
      intersections = [],
      resizes = [];
    const observer = (list) =>
      class {
        constructor(callback) {
          this.callback = callback;
          list.push(this);
        }
        observe(element) {
          this.element = element;
        }
        disconnect() {
          this.disconnected = true;
        }
      };
    let cursor = 0,
      now = 10;
    const canvas = {
      getBoundingClientRect() {
        throw Error('layout read forbidden');
      },
    };
    const environment = {
      document,
      window,
      IntersectionObserver: observer(intersections),
      ResizeObserver: observer(resizes),
      now: () => now,
    };
    const context = {
      primary: { run_id: 'A', code_sha256: 'source-a' },
      comparison: { run_id: 'B' },
      profileMode: 'full-rate-benchmark',
      speed: 1,
    };
    const session = beginReplaySessionObservation(context, () => cursor, canvas, environment);
    assert.equal(intersections[0].element, canvas);
    session.observe(16);
    assert.equal(session.snapshot().raf.raw_frames[0].canvas_intersection_fraction, null);
    intersections[0].callback([{ target: canvas, intersectionRatio: 1 }]);
    cursor = 125;
    session.observe(17);
    assert.equal(session.snapshot().raf.raw_frames[1].observed_cursor_s, 125);
    assert.equal(session.snapshot().raf.raw_frames[1].canvas_intersection_fraction, 1);
    document.visibilityState = 'hidden';
    document.emit('visibilitychange');
    document.hasFocus = () => false;
    window.emit('blur');
    window.emit('resize');
    resizes[0].callback([{ target: canvas, contentRect: { width: 400, height: 300 } }]);
    assert.equal(
      session.snapshot().events.raw.filter((e) => e.kind === 'resize').length,
      1,
      'initial ResizeObserver delivery is not a resize',
    );
    resizes[0].callback([{ target: canvas, contentRect: { width: 401, height: 300 } }]);
    assert.deepEqual(
      session.snapshot().events.raw.map((e) => e.kind),
      ['intersection', 'visibility', 'focus', 'resize', 'resize'],
    );
    now = 50;
    session.stop();
    assert.equal(document.count() + window.count(), 0);
    assert.ok(intersections[0].disconnected && resizes[0].disconnected);
    const stopped = session.snapshot();
    cursor = 9;
    session.observe(100);
    intersections[0].callback([{ target: canvas, intersectionRatio: 0 }]);
    session.stop();
    assert.deepEqual(session.snapshot(), stopped);
    assert.equal(stopped.context.last_observed_cursor_s, 125);
    assert.equal(stopped.environment.ended_wall_ms, 50);
    const next = beginReplaySessionObservation({ ...context, speed: 2 }, () => cursor, null, {
      document,
      window,
      now: () => now,
    });
    next.observe(20);
    next.stop();
    assert.equal(next.snapshot().context.first_observed_cursor_s, 9);
    assert.equal(next.snapshot().context.speed, 2);
    assert.equal(next.snapshot().raf.stored_interval_count, 1);
    assert.equal(next.snapshot().raf.raw_frames[0].canvas_intersection_fraction, null);
    assert.equal(session.snapshot().raf.stored_interval_count, 2);
  } finally {
    await server.close();
  }
});
test('hook observes cursor after commit without putting time in epoch dependencies', async () => {
  const source = await readFile(
    new URL('../src/experiments/useReplaySessionCapture.ts', import.meta.url),
    'utf8',
  );
  const tree = ts.createSourceFile(
      'hook.ts',
      source,
      ts.ScriptTarget.Latest,
      true,
      ts.ScriptKind.TS,
    ),
    effects = [];
  function visit(n) {
    if (
      ts.isCallExpression(n) &&
      ['useEffect', 'useLayoutEffect', 'useCallback'].includes(n.expression.getText(tree))
    )
      effects.push(n);
    ts.forEachChild(n, visit);
  }
  visit(tree);
  const layout = effects.find((n) => n.expression.getText(tree) === 'useLayoutEffect');
  assert.ok(layout.arguments[0].getText(tree).includes('cursor.current ='));
  const lifecycle = effects.find(
    (n) =>
      n.expression.getText(tree) === 'useEffect' &&
      n.arguments[0].getText(tree).includes('observation.stop()'),
  );
  assert.equal(lifecycle.arguments[1].getText(tree), '[playing, contextKey, hostRef]');
  assert.ok(lifecycle.arguments[0].getText(tree).includes('observation.stop()'));
  assert.ok(
    lifecycle.arguments[0].getText(tree).includes('previousContextKey.current !== contextKey'),
  );
  for (const callback of effects.filter((n) => n.expression.getText(tree) === 'useCallback'))
    assert.equal(callback.arguments[1].getText(tree), '[]');
  assert.ok(!source.includes('requestAnimationFrame('));
  assert.ok(!source.includes('getBoundingClientRect('));
});

test('paused actual IO measurement seeds first RAF; unmeasured, stale context and replaced canvas stay unknown', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { warmReplayCanvas, beginReplaySessionObservation } = await server.ssrLoadModule(
      '/src/experiments/useReplaySessionCapture.ts',
    );
    const io = [],
      mutations = [];
    const Observer = (list) =>
      class {
        constructor(callback) {
          this.callback = callback;
          list.push(this);
        }
        observe() {}
        disconnect() {
          this.disconnected = true;
        }
      };
    let canvas = {},
      cache = null;
    const host = { querySelector: () => canvas };
    const context = {
      primary: { run_id: 'A' },
      comparison: { run_id: 'B' },
      profileMode: 'full-rate-benchmark',
      speed: 1,
    };
    const environment = {
      document: { ...target(), visibilityState: 'visible', hasFocus: () => true },
      window: target(),
      IntersectionObserver: Observer(io),
      MutationObserver: Observer(mutations),
      now: () => 10,
    };
    const stop = warmReplayCanvas(JSON.stringify(context), host, environment, (value) => {
      cache = value;
    });
    assert.equal(cache, null);
    const first = (context) => {
      const capture = beginReplaySessionObservation(context, () => 0, canvas, environment, cache);
      capture.observe(16);
      capture.stop();
      return capture.snapshot().raf.raw_frames[0].canvas_intersection_fraction;
    };
    assert.equal(first(context), null, 'first RAF before any actual IO stays unknown');
    io[0].callback([{ target: canvas, intersectionRatio: 1 }]);
    assert.equal(
      first(context),
      1,
      'first RAF can use the actual paused IO value before its new observer callback',
    );
    assert.equal(first({ ...context, speed: 2 }), null);
    assert.equal(first({ ...context, comparison: { run_id: 'other-B' } }), null);
    assert.equal(first({ ...context, profileMode: 'bounded' }), null);
    const priorCanvas = canvas;
    canvas = {};
    assert.equal(first(context), null, 'canvas identity must match even before mutation delivery');
    mutations[0].callback();
    assert.equal(cache, null);
    io[0].callback([{ target: priorCanvas, intersectionRatio: 1 }]);
    assert.equal(cache, null, 'late delivery from replaced canvas ignored');
    io.at(-1).callback([{ target: canvas, intersectionRatio: 0.5 }]);
    assert.equal(
      first(context),
      0.5,
      'partial measured state is preserved, never upgraded to full',
    );
    stop();
    assert.equal(cache, null);
    assert.ok(mutations[0].disconnected);
  } finally {
    await server.close();
  }
});

test('host heap is read exactly at start and stop, copied and unavailable stays null', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { beginReplaySessionObservation } = await server.ssrLoadModule(
      '/src/experiments/useReplaySessionCapture.ts',
    );
    const context = { primary: { run_id: 'A' }, profileMode: 'bounded', speed: 1 };
    const environment = {
      document: { ...target(), visibilityState: 'visible', hasFocus: () => true },
      window: target(),
      now: () => 1,
    };
    let reads = 0;
    const heap = { used: 10, total: 20, limit: 30 };
    const session = beginReplaySessionObservation(context, () => 0, null, {
      ...environment,
      readHeap: () => {
        reads++;
        return heap;
      },
    });
    assert.equal(reads, 1);
    heap.used = 11;
    for (let i = 0; i < 3; i++) {
      session.observe(16);
      session.snapshot();
    }
    assert.equal(reads, 1);
    assert.equal(session.snapshot().host_javascript_heap.initial.used, 10);
    assert.equal(session.snapshot().host_javascript_heap.final, null);
    session.stop();
    session.stop();
    assert.equal(reads, 2);
    heap.used = 999;
    const snapshot = session.snapshot();
    assert.equal(snapshot.host_javascript_heap.final.used, 11);
    snapshot.host_javascript_heap.initial.used = 123;
    assert.equal(session.snapshot().host_javascript_heap.initial.used, 10);
    assert.equal(reads, 2);
    for (const readHeap of [
      undefined,
      () => null,
      () => {
        throw Error('unsupported');
      },
    ]) {
      const unsupported = beginReplaySessionObservation(context, () => 0, null, {
        ...environment,
        readHeap,
      });
      unsupported.stop();
      assert.equal(unsupported.snapshot().host_javascript_heap.initial, null);
      assert.equal(unsupported.snapshot().host_javascript_heap.final, null);
    }
  } finally {
    await server.close();
  }
});
