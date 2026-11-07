import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { Matrix4, Vector3 } from 'three';
import { replayPose } from '../src/experiments/replayPose.ts';

const fixture = JSON.parse(readFileSync(new URL('../../docs/studies/replay-pose-20261107/reference.json', import.meta.url), 'utf8'));
const columns = (samples) => Object.fromEntries(Object.keys(samples[0]).map((key) => [key, samples.map((x) => x[key])]));
const near = (actual, expected, tolerance = 1e-9) => {
  assert.equal(actual.length, expected.length);
  actual.forEach((value, i) => assert.ok(Math.abs(value - expected[i]) < tolerance, `${value} != ${expected[i]} at ${i}`));
};
const matrix = (q) => {
  const e = new Matrix4().makeRotationFromQuaternion(q).elements;
  return [[e[0], e[4], e[8]], [e[1], e[5], e[9]], [e[2], e[6], e[10]]];
};
const synthetic = (q, cg = 0.4) => ({ time_s: [1, 2], north_m: [3, 3], east_m: [4, 4], down_m: [-5, -5], qw: [q[0], q[0]], qx: [q[1], q[1]], qy: [q[2], q[2]], qz: [q[3], q[3]], cg_station_m: [cg, cg] });

test('actual production pose matches independent scalar reference at descent and event brackets', () => {
  for (const [name, example] of Object.entries(fixture.cases)) {
    // Exact-event brackets may be a single saved sample; use one sample in that case.
    const samples = example.samples[0].time_s === example.samples[1].time_s ? [example.samples[0]] : example.samples;
    const pose = replayPose(columns(samples), fixture.length_m, example.requested_time_s);
    assert.equal(pose.kind, 'pose', name);
    near(pose.position, example.expected.position_scene_m);
    near(pose.pivot, example.expected.pivot_cad_m);
    matrix(pose.quaternion).forEach((row, i) => near(row, example.expected.cad_to_scene_matrix[i], 2e-8));
    near(new Vector3(0, 1, 0).applyQuaternion(pose.quaternion).toArray(), example.expected.nose_scene, 2e-8);
    assert.ok(Math.abs(pose.fraction - example.fraction) < 1e-9);
  }
  const raw = fixture.raw_nearest_11_15;
  assert.ok(Math.abs(raw.vd_mps - 5.4560388118) < 1e-9);
  const nose = fixture.cases.descent.expected.nose_scene;
  assert.ok(Math.abs(Math.acos(nose[1]) * 180 / Math.PI - 4.0763031) < 0.001);
});

test('identity, launch-up, sideways, CG pivot and sign-equivalent rotations', () => {
  const half = Math.SQRT1_2;
  for (const [q, expected] of [
    [[1, 0, 0, 0], [0, 0, -1]],
    [[half, 0, half, 0], [0, 1, 0]],
    [[half, 0, 0, half], [1, 0, 0]],
  ]) {
    const pose = replayPose(synthetic(q), 1.2, 1.5);
    assert.equal(pose.kind, 'pose');
    near(pose.position, [4, 5, -3]);
    near(pose.pivot, [0, -0.8, 0]);
    near(new Vector3(0, 1, 0).applyQuaternion(pose.quaternion).toArray(), expected);
  }
  const input = synthetic([half, 0, half, 0]);
  for (const key of ['qw', 'qx', 'qy', 'qz']) input[key][1] *= -1;
  const pose = replayPose(input, 1.2, 1.5);
  assert.equal(pose.kind, 'pose');
  near(new Vector3(0, 1, 0).applyQuaternion(pose.quaternion).toArray(), [0, 1, 0]);
});

test('missing or invalid pose preserves valid position; invalid position or coverage yields no actor', () => {
  for (const q of [[0, 0, 0, 0], [NaN, 0, 0, 1], [Infinity, 0, 0, 1]]) {
    const pose = replayPose(synthetic(q), 1.2, 1.5);
    assert.equal(pose.kind, 'marker');
    near(pose.position, [4, 5, -3]);
  }
  const missing = synthetic([1, 0, 0, 0]); delete missing.qw;
  assert.equal(replayPose(missing, 1.2, 1.5).kind, 'marker');
  const badPosition = synthetic([1, 0, 0, 0]); badPosition.north_m[1] = NaN;
  assert.equal(replayPose(badPosition, 1.2, 1.5).kind, 'unavailable');
  assert.equal(replayPose(synthetic([1, 0, 0, 0]), 1.2, 0).kind, 'unavailable');
  assert.equal(replayPose(synthetic([1, 0, 0, 0]), 1.2, 3).kind, 'unavailable');
  assert.equal(replayPose(synthetic([1, 0, 0, 0]), 1.2, 1.5, 0.2).reason, 'Interpolation gap unsupported');
  assert.equal(replayPose(synthetic([1, 0, 0, 0]), 1.2, 1, 0.2).kind, 'pose');
  assert.equal(replayPose(synthetic([1, 0, 0, 0]), 1.2, 2, 0.2).kind, 'pose');
  const other = synthetic([1, 0, 0, 0]); other.time_s = [1, 4];
  assert.equal(replayPose(other, 1.2, 3).kind, 'pose');
  assert.equal(replayPose(synthetic([1, 0, 0, 0]), 1.2, 3).kind, 'unavailable');
});

test('event boundary pose is continuous within the saved recorded brackets', () => {
  for (const [name, example] of Object.entries(fixture.cases)) {
    if (name === 'descent') continue;
    const [a, b] = example.samples;
    if (a.time_s === b.time_s) continue;
    const c = columns([a, b]);
    const t = example.requested_time_s;
    const event = replayPose(c, fixture.length_m, t);
    assert.equal(event.kind, 'pose');
    for (const candidate of [Math.max(a.time_s, t - 1e-7), Math.min(b.time_s, t + 1e-7)]) {
      const nearby = replayPose(c, fixture.length_m, candidate);
      assert.equal(nearby.kind, 'pose');
      assert.ok(event.quaternion.angleTo(nearby.quaternion) < 1e-5, name);
      near(event.position, nearby.position, 1e-3);
    }
  }
});
