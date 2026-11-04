import assert from 'node:assert/strict';
import test from 'node:test';
import { Box3, Plane, Vector3 } from 'three';
import { fitOrbitFrame, isPointClipped } from '../src/components/inspectionCamera.ts';

const bounds = new Box3(new Vector3(-0.2, 0, -0.1), new Vector3(0.2, 1.2, 0.1));

test('fit preserves a manually chosen orbit and contains every corner', () => {
  const position = new Vector3(2, 3, -4);
  const target = new Vector3(0.1, 0.4, 0.1);
  for (const aspect of [0.5, 2]) {
    const frame = fitOrbitFrame(bounds, aspect, 35, position, target, new Vector3(0, 1, 0));
    const origin = new Vector3(...frame.position);
    const center = new Vector3(...frame.target);
    const direction = origin.clone().sub(center).normalize();
    assert.ok(direction.distanceTo(position.clone().sub(target).normalize()) < 1e-12);
    const right = new Vector3().crossVectors(direction, new Vector3(...frame.up)).normalize();
    const up = new Vector3().crossVectors(right, direction).normalize();
    const tanV = Math.tan((35 * Math.PI) / 360);
    for (const x of [bounds.min.x, bounds.max.x]) {
      for (const y of [bounds.min.y, bounds.max.y]) {
        for (const z of [bounds.min.z, bounds.max.z]) {
          const relative = new Vector3(x, y, z).sub(origin);
          const depth = -relative.dot(direction);
          assert.ok(depth > frame.near && depth < frame.far);
          assert.ok(Math.abs(relative.dot(right)) / depth <= tanV * aspect);
          assert.ok(Math.abs(relative.dot(up)) / depth <= tanV);
        }
      }
    }
  }
});

test('end-on fit remains finite when the up hint is parallel to the orbit', () => {
  const frame = fitOrbitFrame(
    bounds,
    1,
    35,
    new Vector3(0, -1, 0),
    new Vector3(),
    new Vector3(0, 1, 0),
  );
  assert.ok([...frame.position, ...frame.up, frame.near, frame.far].every(Number.isFinite));
  assert.ok(frame.far > frame.near);
});

test('section picks pass through clipped world-space hits and retain visible and boundary hits', () => {
  const plane = new Plane(new Vector3(-1, 0, 0), 0);
  assert.equal(isPointClipped(new Vector3(0.1, 1, 0), plane, true), true);
  assert.equal(isPointClipped(new Vector3(-0.1, 1, 0), plane, true), false);
  assert.equal(isPointClipped(new Vector3(0, 1, 0), plane, true), false);
  assert.equal(isPointClipped(new Vector3(0.1, 1, 0), plane, false), false);
});
