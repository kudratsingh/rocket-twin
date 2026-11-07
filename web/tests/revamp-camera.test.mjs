import assert from 'node:assert/strict';
import test from 'node:test';
import { Box3, Plane, Vector3 } from 'three';
import { clippedBoxBounds, fitOrbitFrame } from '../src/components/inspectionCamera.ts';

function project(bounds, frame, aspect, fov) {
  const camera = new Vector3(...frame.position);
  const direction = camera.clone().sub(new Vector3(...frame.target)).normalize();
  const right = new Vector3().crossVectors(direction, new Vector3(...frame.up)).normalize();
  const up = new Vector3().crossVectors(right, direction).normalize();
  const tanV = Math.tan(fov * Math.PI / 360);
  const result = [];
  for (const x of [bounds.min.x, bounds.max.x]) for (const y of [bounds.min.y, bounds.max.y]) for (const z of [bounds.min.z, bounds.max.z]) {
    const relative = new Vector3(x, y, z).sub(camera);
    const depth = -relative.dot(direction);
    assert.ok(depth > frame.near && depth < frame.far);
    result.push([relative.dot(right) / depth / (tanV * aspect), relative.dot(up) / depth / tanV]);
  }
  return result;
}

function check(bounds, aspect, position, options = { fill: 0.8 }) {
  const origin = new Vector3();
  const frame = fitOrbitFrame(bounds, aspect, 35, position, origin, new Vector3(0, 1, 0), options);
  const dir = new Vector3(...frame.position).sub(new Vector3(...frame.target)).normalize();
  assert.ok(dir.distanceTo(position.clone().normalize()) < 1e-10);
  const points = project(bounds, frame, aspect, 35);
  const insets = options.insets ?? {};
  const left = insets.left ?? 0, right = insets.right ?? 0, top = insets.top ?? 0, bottom = insets.bottom ?? 0;
  const fill = options.fill ?? 1 / 1.15;
  const cx = left - right, cy = bottom - top;
  const hx = (1 - left - right) * fill, hy = (1 - top - bottom) * fill;
  for (const [x, y] of points) {
    assert.ok(x >= cx - hx - 1e-9 && x <= cx + hx + 1e-9, `${x} outside horizontal safe fit`);
    assert.ok(y >= cy - hy - 1e-9 && y <= cy + hy + 1e-9, `${y} outside vertical safe fit`);
  }
  const xValues = points.map((p) => p[0]);
  const yValues = points.map((p) => p[1]);
  assert.ok(Math.abs((Math.min(...xValues) + Math.max(...xValues)) / 2 - cx) < 1e-8);
  assert.ok(Math.abs((Math.min(...yValues) + Math.max(...yValues)) / 2 - cy) < 1e-8);
  return { frame, points };
}

test('perspective corner fit respects insets for long, small, wide and end-on bounds', () => {
  const samples = [
    [new Box3(new Vector3(-0.04, -0.6, -0.04), new Vector3(0.04, 0.6, 0.04)), 1.8, new Vector3(1, 0, 0)],
    [new Box3(new Vector3(-0.00025, -0.00025, -0.00025), new Vector3(0.00025, 0.00025, 0.00025)), 0.45, new Vector3(2, 3, 4)],
    [new Box3(new Vector3(-2, -0.1, -0.2), new Vector3(2, 0.1, 0.2)), 3, new Vector3(0, 0, 1)],
    [new Box3(new Vector3(-0.04, -0.6, -0.04), new Vector3(0.04, 0.6, 0.04)), 1, new Vector3(0, 1, 0)],
    [new Box3(new Vector3(0, -0.6, 0), new Vector3(0, 0.6, 0)), 1, new Vector3(0, 1, 0)],
  ];
  for (const [bounds, aspect, camera] of samples) check(bounds, aspect, camera, { fill: 0.8, insets: {left: 0.25, right: 0.05, top: 0.1, bottom: 0.05} });
  const tiny = check(samples[1][0], 1, new Vector3(1, 1, 1)).frame;
  assert.ok(new Vector3(...tiny.position).distanceTo(new Vector3(...tiny.target)) < 0.01);
});

test('side-view conservative box spans target height, and component limiting axis spans target', () => {
  const box = new Box3(new Vector3(-0.04, -0.6, -0.04), new Vector3(0.04, 0.6, 0.04));
  const {points} = check(box, 1.8, new Vector3(1, 0, 0), {fill: 0.85});
  const ys = points.map((p) => p[1]);
  assert.ok((Math.max(...ys) - Math.min(...ys)) / 2 >= 0.84999);
  const part = new Box3(new Vector3(-0.003, -0.002, -0.001), new Vector3(0.003, 0.002, 0.001));
  const projected = check(part, 1.5, new Vector3(1, 2, 3), {fill: 0.75}).points;
  const xs = projected.map((p) => p[0]), partYs = projected.map((p) => p[1]);
  const limiting = Math.max((Math.max(...xs) - Math.min(...xs)) / 2, (Math.max(...partYs) - Math.min(...partYs)) / 2);
  assert.ok(limiting >= 0.74999 && limiting <= 0.75001);
});

test('degenerate points, parallel up and invalid input handled explicitly', () => {
  const point = new Box3(new Vector3(), new Vector3());
  const frame = fitOrbitFrame(point, 1, 35, new Vector3(0, 1, 0), new Vector3(), new Vector3(0, 1, 0));
  assert.ok([...frame.position, ...frame.up, frame.near, frame.far].every(Number.isFinite));
  assert.ok(frame.near > 0 && frame.far > frame.near);
  assert.throws(() => fitOrbitFrame(point, 1, 35, new Vector3(1, 0, 0), new Vector3(), new Vector3(0, 1, 0), { insets: {left: 0.6, right: 0.4} }), RangeError);
  assert.throws(() => fitOrbitFrame(new Box3(), 1, 35, new Vector3(1, 0, 0), new Vector3(), new Vector3(0, 1, 0)), RangeError);
});

test('clipped bounds enclose plane-box intersection, not actual mesh', () => {
  const box = new Box3(new Vector3(-1, -1, -1), new Vector3(1, 1, 1));
  const sliced = clippedBoxBounds(box, new Plane(new Vector3(1, 0, 0), -0.25));
  assert.deepEqual(sliced.min.toArray(), [0.25, -1, -1]);
  assert.deepEqual(sliced.max.toArray(), [1, 1, 1]);
  assert.equal(clippedBoxBounds(box, new Plane(new Vector3(1, 0, 0), -2)), null);
  const diagonal = clippedBoxBounds(box, new Plane(new Vector3(1, 1, 1).normalize(), -1 / Math.sqrt(3)));
  assert.ok(diagonal.min.distanceTo(new Vector3(-1, -1, -1)) < 1e-12);
  assert.ok(diagonal.max.distanceTo(new Vector3(1, 1, 1)) < 1e-12);
});
