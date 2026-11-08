import assert from 'node:assert/strict';
import test from 'node:test';
import { replayFollowTarget } from '../src/experiments/replayFollowTarget.ts';
import { replayPose } from '../src/experiments/replayPose.ts';

const columns = (end, east) => ({
  time_s: [0, end],
  east_m: [east, east + 1],
  north_m: [0, 1],
  down_m: [0, -2],
  qw: [1, 1],
  qx: [0, 0],
  qy: [0, 0],
  qz: [0, 0],
  cg_station_m: [0.3, 0.3],
});
const a = columns(116.029, 10);
const b = columns(132.856, 30);
const at = (time, mode = 'follow') =>
  replayFollowTarget(mode, replayPose(a, 1, time), replayPose(b, 1, time));

test('auto prioritizes A through its exact endpoint, follows B at 125 and stops beyond B support', () => {
  for (const time of [0, 116.029]) assert.equal(at(time).source, 'A');
  for (const time of [116.03, 125, 132.856]) {
    const target = at(time);
    assert.equal(target.source, 'B');
    assert.deepEqual(target.position, replayPose(b, 1, time).position);
    assert.match(target.label, /Auto fallback; A: Outside recorded window/);
  }
  for (const time of [-1, 132.857, NaN]) {
    assert.equal(at(time).status, 'held');
    assert.equal(at(time).source, null);
    assert.equal(at(time).position, null);
  }
});

test('forced target never silently substitutes the other available run', () => {
  assert.equal(at(125, 'follow-a').status, 'held');
  assert.equal(at(125, 'follow-a').position, null);
  assert.match(at(125, 'follow-a').label, /A: Outside recorded window/);
  assert.equal(at(100, 'follow-b').source, 'B');
  const onlyA = replayFollowTarget('follow-b', replayPose(a, 1, 100), null);
  assert.equal(onlyA.status, 'held');
  assert.match(onlyA.label, /B: run not loaded/);
  assert.equal(replayFollowTarget('follow', null, replayPose(b, 1, 125)).source, 'B');
});

test('finite position markers remain valid camera targets while malformed positions do not', () => {
  const marker = Object.freeze({
    kind: 'marker',
    reason: 'Recorded attitude unavailable',
    position: Object.freeze([1, 2, 3]),
  });
  assert.equal(replayFollowTarget('follow', marker, replayPose(b, 1, 100)).source, 'A');
  assert.match(replayFollowTarget('follow', marker, null).label, /position marker/);
  const sparse = [1, 2, 3];
  delete sparse[1];
  for (const position of [[1, NaN, 3], [1, 2, Infinity], [1, 2], sparse, null, ['1', 2, 3]]) {
    const malformed = { kind: 'marker', reason: 'fixture', position };
    assert.equal(replayFollowTarget('follow-a', malformed, marker).status, 'held');
    assert.equal(replayFollowTarget('follow', malformed, marker).source, 'B');
  }
  assert.equal(
    replayFollowTarget(
      'follow',
      { kind: 'unavailable', reason: 'Recorded position unavailable' },
      null,
    ).position,
    null,
  );
});

test('pad and free return no target and retain the existing camera mode; selection cannot mutate poses', () => {
  const primary = replayPose(a, 1, 100);
  const comparison = replayPose(b, 1, 100);
  const before = JSON.stringify([primary, comparison, a, b]);
  for (const mode of ['pad', 'free']) {
    const target = replayFollowTarget(mode, primary, comparison);
    assert.equal(target.cameraMode, mode);
    assert.equal(target.position, null);
    assert.equal(target.source, null);
  }
  const target = replayFollowTarget('follow', primary, comparison);
  target.position[0] = 999;
  assert.equal(JSON.stringify([primary, comparison, a, b]), before);
});
