import assert from 'node:assert/strict';
import test from 'node:test';
import {
  firstRecordedTime,
  replayWindow,
  replayWindowStatus,
} from '../src/experiments/replayWindow.ts';

const coverage = (times, time) => replayWindowStatus(replayWindow(times), time);

test('each run independently follows the longer shared cursor through either end', () => {
  for (const [a, b] of [
    [
      [0, 1, 2],
      [0, 1, 4],
    ],
    [
      [0, 1, 4],
      [0, 1, 2],
    ],
  ]) {
    assert.equal(coverage(a, 2), 'inside');
    assert.equal(coverage(b, 2), 'inside');
    assert.deepEqual([coverage(a, 3), coverage(b, 3)].sort(), ['inside', 'outside']);
    assert.deepEqual([coverage(a, 4), coverage(b, 4)].sort(), ['inside', 'outside']);
    assert.equal(coverage(a, 4.01), 'outside');
    assert.equal(coverage(b, 4.01), 'outside');
  }
});

test('nonzero starts and exact endpoints are inclusive without extrapolation', () => {
  assert.deepEqual(replayWindow([0.001, 1, 2]), { start: 0.001, end: 2 });
  assert.equal(coverage([0.001, 1, 2], 0), 'outside');
  assert.equal(coverage([0.001, 1, 2], 0.001), 'inside');
  assert.equal(coverage([0.001, 1, 2], 2), 'inside');
  assert.equal(coverage([1], 1), 'inside');
  assert.equal(coverage([1], 1.01), 'outside');
  assert.equal(firstRecordedTime(replayWindow([0.001, 1, 2])), 0.001);
  assert.equal(firstRecordedTime(replayWindow([1, 2]), replayWindow([0.25, 3])), 0.25);
  assert.equal(firstRecordedTime(null, replayWindow([0.001, 1])), 0.001);
  assert.equal(firstRecordedTime(null), 0);
});

test('missing, nonfinite, repeated, and unordered times cannot establish a window', () => {
  for (const times of [undefined, [], [0, NaN], [0, Infinity], [1, 1], [2, 1]]) {
    assert.equal(replayWindow(times), null);
    assert.equal(coverage(times, 0), 'unavailable');
  }
  assert.equal(coverage([0, 1], NaN), 'unavailable');
  assert.equal(coverage([0, 1], Infinity), 'unavailable');
});

test('coverage queries leave the recorded samples and shared requested time unchanged', () => {
  const samples = Object.freeze([0.25, 1, 2]);
  const sharedTime = 3;
  const window = replayWindow(samples);
  assert.equal(replayWindowStatus(window, sharedTime), 'outside');
  assert.equal(sharedTime, 3);
  assert.deepEqual(samples, [0.25, 1, 2]);
  assert.deepEqual(window, { start: 0.25, end: 2 });
  assert.equal(replayWindowStatus(window, 0), 'outside');
  assert.equal(replayWindowStatus(window, 1.5), 'inside');
});
