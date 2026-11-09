import assert from 'node:assert/strict';
import test from 'node:test';
import { createRafIntervalClock } from '../src/experiments/rafIntervalClock.ts';
import { playbackStep } from '../src/experiments/playbackStep.ts';

test('first actual RAF anchors without borrowing a later performance.now event clock', () => {
  const clock = createRafIntervalClock();
  const wallStart = 1000;
  let cursor = 0.001;
  const first = clock.sample(991.7);
  assert.equal(first, null);
  assert.equal(cursor, 0.001, 'first RAF makes no playback step even when earlier than wall start');
  const next = clock.sample(1008.4);
  assert.ok(Math.abs(next - 16.7) < 1e-10);
  cursor = playbackStep(next, 1, 132.856)(cursor);
  assert.ok(Math.abs(cursor - 0.0177) < 1e-10);
  assert.equal(wallStart > 991.7, true, 'the reproduction contains the original negative offset');
});

test('irregular intervals retain speed factor and natural endpoint clamp', () => {
  const clock = createRafIntervalClock();
  assert.equal(clock.sample(100), null);
  let cursor = 0.001;
  cursor = playbackStep(clock.sample(116.7), 2, 1)(cursor);
  cursor = playbackStep(clock.sample(143.2), 2, 1)(cursor);
  assert.ok(Math.abs(cursor - 0.0874) < 1e-10);
  cursor = playbackStep(clock.sample(1643.2), 2, 1)(cursor);
  assert.equal(cursor, 1);
});

test('zero, backward and nonfinite timestamps forward invalid deltas without double advance', () => {
  const clock = createRafIntervalClock();
  assert.ok(Number.isNaN(clock.sample(NaN)));
  assert.equal(clock.sample(1000), null, 'first finite RAF establishes the anchor');
  let cursor = 0.5;
  const zero = clock.sample(1000);
  const backward = clock.sample(991.7);
  const nonfinite = clock.sample(Infinity);
  assert.equal(zero, 0);
  assert.ok(backward < 0);
  assert.ok(Number.isNaN(nonfinite));
  for (const invalid of [zero, backward, nonfinite]) {
    assert.equal(playbackStep(invalid, 1, 2)(cursor), cursor);
  }
  const recovered = clock.sample(1016.7);
  assert.ok(Math.abs(recovered - 16.7) < 1e-10);
  cursor = playbackStep(recovered, 1, 2)(cursor);
  assert.ok(Math.abs(cursor - 0.5167) < 1e-10);
  clock.reset();
  assert.equal(clock.sample(2000), null);
});

test('invalid speed or endpoint preserves cursor without fabricating a reset', () => {
  for (const speed of [0, -1, NaN, Infinity]) {
    assert.equal(playbackStep(16, speed, 2)(0.5), 0.5);
  }
  for (const end of [NaN, Infinity]) {
    assert.equal(playbackStep(16, 1, end)(0.5), 0.5);
  }
  assert.equal(playbackStep(16, 1, 2)(NaN), NaN);
});

test('valid negative event-relative clock preserves advancement and finite end clamp', () => {
  assert.equal(playbackStep(100, 1, -2)(-5), -4.9);
  assert.equal(playbackStep(4000, 1, -2)(-5), -2);
});
