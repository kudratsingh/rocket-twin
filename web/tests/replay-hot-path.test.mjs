import assert from 'node:assert/strict';
import test from 'node:test';
import { replayWindow, replayWindowStatus } from '../src/experiments/replayWindow.ts';
import { playbackStep } from '../src/experiments/playbackStep.ts';

function observedFrozen(values) {
  let reads = 0;
  const times = new Proxy(Object.freeze(values), {
    get(target, key, receiver) {
      if (typeof key === 'string' && /^\d+$/.test(key)) reads++;
      return Reflect.get(target, key, receiver);
    },
  });
  return { times, reads: () => reads };
}

test('frozen valid arrays reuse validated immutable bounds without rescanning native samples', () => {
  const observed = observedFrozen([0.001, 0.002, 0.003]);
  const first = replayWindow(observed.times);
  const reads = observed.reads();
  assert.deepEqual(first, { start: 0.001, end: 0.003 });
  assert.equal(Object.isFrozen(first), true);
  for (let i = 0; i < 600; i++) assert.equal(replayWindow(observed.times), first);
  assert.equal(observed.reads(), reads, 'cached lookups must not reread any native sample');
  assert.throws(() => {
    first.start = -100;
  }, TypeError);
  assert.throws(() => {
    first.end = Infinity;
  }, TypeError);
  assert.equal(replayWindowStatus(replayWindow(observed.times), 0), 'outside');
});

test('frozen invalid arrays stay unavailable and safely reuse a cached failure', () => {
  for (const values of [[], [0, NaN], [0, Infinity], [1, 1], [2, 1]]) {
    const observed = observedFrozen(values);
    assert.equal(replayWindow(observed.times), null);
    const reads = observed.reads();
    assert.equal(replayWindow(observed.times), null);
    assert.equal(observed.reads(), reads);
    assert.equal(replayWindowStatus(replayWindow(observed.times), 1), 'unavailable');
  }
});

test('mutable and sealed arrays are fully revalidated after every source mutation', () => {
  const times = [0, 1, 2];
  assert.deepEqual(replayWindow(times), { start: 0, end: 2 });
  times[1] = NaN;
  assert.equal(replayWindow(times), null);
  times[1] = 3;
  assert.equal(replayWindow(times), null);
  times[1] = 1;
  times.push(4);
  assert.deepEqual(replayWindow(times), { start: 0, end: 4 });
  delete times[3];
  assert.equal(replayWindow(times), null, 'sparse trailing values remain invalid');
  const sealed = Object.seal([0, 1, 2]);
  assert.notEqual(replayWindow(sealed), null);
  sealed[1] = 3;
  assert.equal(replayWindow(sealed), null);
});

test('frozen accessors cannot disguise mutable data as a cacheable time axis', () => {
  let middle = 1;
  const times = [0, 1, 2];
  Object.defineProperty(times, '1', { get: () => middle, enumerable: true, configurable: true });
  Object.freeze(times);
  assert.notEqual(replayWindow(times), null);
  middle = 3;
  assert.equal(replayWindow(times), null);
  middle = NaN;
  assert.equal(replayWindow(times), null);
  middle = 1;
  assert.deepEqual(replayWindow(times), { start: 0, end: 2 });
});

test('deferred playback state updates retain every captured interval at the selected speed', () => {
  let last = 0;
  const deferred = [];
  for (let frame = 1; frame <= 600; frame++) {
    const now = frame * 16.7;
    const elapsedMs = now - last;
    deferred.push(playbackStep(elapsedMs, 1, 132.856));
    last = now;
  }
  // React may evaluate the queued updaters after the tick's mutable timestamp advances.
  last = 999999;
  const cursor = deferred.reduce((time, advance) => advance(time), 0.131);
  assert.ok(Math.abs(cursor - (0.131 + 600 * 0.0167)) < 1e-10);
  assert.equal(last, 999999);
  const twice = playbackStep(250, 2, 100);
  assert.equal(twice(3), 3.5);
  assert.equal(twice(3), 3.5, 'updater is pure if React evaluates it twice');
  assert.equal(playbackStep(1000, 4, 5)(4.5), 5, 'existing endpoint clamp is retained');
  assert.equal(playbackStep(0, 1, 5)(4.5), 4.5);
});
