import assert from 'node:assert/strict';
import test from 'node:test';
import { replayTrajectoryBounds, replayFitDistance } from '../src/experiments/replayTrajectoryBounds.ts';

const a = {
  time_s: [0.001, 116.029],
  east_m: [-10, 30],
  down_m: [-2, -600],
  north_m: [-20, 40],
};
const b = {
  time_s: [0.001, 125, 132.856],
  east_m: [-50, 80, 100],
  down_m: [0, -800, -3],
  north_m: [80, -70, 60],
};

test('fits both complete recorded windows in east/up/south without clamping B to A', () => {
  assert.deepEqual(replayTrajectoryBounds(a, b), {
    min: [-50, -0, -80], max: [100, 800, 70], points: 5,
  });
  assert.deepEqual(replayTrajectoryBounds(a), {
    min: [-10, 2, -40], max: [30, 600, 20], points: 2,
  });
  const before = structuredClone([a, b]);
  replayTrajectoryBounds(a, b);
  assert.deepEqual([a, b], before);
});

test('never invents origin or fills missing position rows; finite zero remains real', () => {
  assert.deepEqual(replayTrajectoryBounds({ ...a, east_m: [NaN, 30] }), {
    min: [30, 600, -40], max: [30, 600, -40], points: 1,
  });
  const zero = { time_s: [0], east_m: [0], north_m: [0], down_m: [0] };
  const result = replayTrajectoryBounds(zero);
  assert.equal(result.points, 1);
  assert.ok([...result.min, ...result.max].every((value) => value === 0));
  assert.equal(replayTrajectoryBounds({ ...a, east_m: [NaN, NaN] }), null);
});

test('invalid time axes and inconsistent position columns cannot manufacture coverage', () => {
  for (const invalid of [
    { ...a, time_s: [0, 0] },
    { ...a, time_s: [0, NaN] },
    { ...a, north_m: [1] },
    { ...a, north_m: undefined },
  ]) {
    assert.equal(replayTrajectoryBounds(invalid), null);
    assert.deepEqual(replayTrajectoryBounds(invalid, b), replayTrajectoryBounds(b));
  }
  assert.equal(replayTrajectoryBounds(null, undefined), null);
});


test('fit contains the sphere through both vertical and horizontal frusta, including narrow canvases', () => {
  const radius = 20;
  for (const aspect of [0.4, 1, 2.5]) {
    const distance = replayFitDistance(radius, 45, aspect);
    const halfVertical = Math.PI / 8;
    const halfHorizontal = Math.atan(Math.tan(halfVertical) * aspect);
    // Independent plane-distance containment: all sphere points clear every plane.
    assert.ok(distance * Math.sin(halfVertical) >= radius * 1.099999);
    assert.ok(distance * Math.sin(halfHorizontal) >= radius * 1.099999);
  }
  assert.ok(Math.abs(replayFitDistance(20, 90, 1) - 20 * Math.sqrt(2) * 1.1) < 1e-12);
  for (const args of [[0,45,1],[1,0,1],[1,180,1],[1,45,0],[1,NaN,1],[Infinity,45,1]])
    assert.equal(replayFitDistance(...args), null);
});
