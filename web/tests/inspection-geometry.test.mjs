import assert from 'node:assert/strict';
import test from 'node:test';
import { cameraFrame, CAMERA_VIEWS } from '../src/components/inspectionGeometry.ts';

const box = { min: [-2, -8, -1], max: [2, 8, 1] };

function dot(a, b) {
  return a.reduce((sum, value, index) => sum + value * b[index], 0);
}

function cross(a, b) {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

function unit(vector) {
  const length = Math.hypot(...vector);
  return vector.map((value) => value / length);
}

function assertFits(bounds, aspect, view) {
  const fov = 35;
  const frame = cameraFrame(bounds, aspect, fov, view);
  const forward = unit(frame.target.map((value, index) => value - frame.position[index]));
  const right = unit(cross(forward, frame.up));
  const screenUp = unit(cross(right, forward));
  const tanV = Math.tan((fov * Math.PI) / 360);
  const tanH = tanV * aspect;
  for (const x of [bounds.min[0], bounds.max[0]]) {
    for (const y of [bounds.min[1], bounds.max[1]]) {
      for (const z of [bounds.min[2], bounds.max[2]]) {
        const relative = [x - frame.position[0], y - frame.position[1], z - frame.position[2]];
        const depth = dot(relative, forward);
        assert.ok(
          depth > frame.near,
          `corner depth ${depth} must be beyond near clip ${frame.near}`,
        );
        assert.ok(
          Math.abs(dot(relative, right)) / depth <= tanH + 1e-9,
          'corner must fit horizontal FOV',
        );
        assert.ok(
          Math.abs(dot(relative, screenUp)) / depth <= tanV + 1e-9,
          'corner must fit vertical FOV',
        );
      }
    }
  }
  return frame;
}

test('fits all box corners in portrait and wide frames', () => {
  for (const aspect of [0.55, 2.2]) {
    for (const view of ['overview', 'front', 'side', 'aft']) assertFits(box, aspect, view);
  }
});

test('aft camera looks from the motor end with Z as screen up', () => {
  const frame = cameraFrame(box, 1.5, 35, 'aft');
  assert.ok(frame.position[1] < frame.target[1]);
  assert.deepEqual(frame.up, [0, 0, 1]);
  assert.ok(frame.near > 0 && frame.far > frame.near);
});

test('tiny valid bounds produce a finite nonzero camera frame', () => {
  const frame = cameraFrame({ min: [0, 0, 0], max: [1e-8, 2e-8, 1e-8] }, 1.2);
  for (const value of [...frame.target, ...frame.position, ...frame.up, frame.near, frame.far])
    assert.ok(Number.isFinite(value));
  assert.ok(Math.hypot(...frame.position.map((value, index) => value - frame.target[index])) > 0);
});

test('end-on framing leaves positive camera clearance for a line-like unloaded bounds fallback', () => {
  assertFits({ min: [0, 0, 0], max: [0, 1.212, 0] }, 1.5, 'aft');
});

test('invalid bounds and camera parameters fail with RangeError', () => {
  assert.throws(() => cameraFrame({ min: [1, 0, 0], max: [0, 1, 1] }, 1), RangeError);
  assert.throws(() => cameraFrame({ min: [0, 0, NaN], max: [1, 1, 1] }, 1), RangeError);
  assert.throws(() => cameraFrame(box, 0), RangeError);
  assert.throws(() => cameraFrame(box, 1, 180), RangeError);
  assert.throws(() => cameraFrame(box, 1, 35, 'diagonal'), RangeError);
});

test('camera view choices have stable IDs and plain-language labels', () => {
  assert.deepEqual(
    CAMERA_VIEWS.map(({ id }) => id),
    ['overview', 'front', 'side', 'aft'],
  );
  assert.ok(
    CAMERA_VIEWS.every(({ label, description }) => label.length > 0 && description.length > 0),
  );
});
