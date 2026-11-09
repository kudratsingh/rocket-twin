import assert from 'node:assert/strict';
import test from 'node:test';
import { registerMainCamera, captureMainCamera, consumeMainCamera, clearMainCamera, mainCameraCommand } from '../src/fin-attachment/mainCameraCheckpoint.ts';

test('rocket camera checkpoint captures actual pose once and cannot cross source identities', () => {
  const pose = {position: [1, 2, 3], up: [0, 1, 0], target: [0.1, 0.2, 0.3]};
  const release = registerMainCamera('rp1:spec', () => pose);
  captureMainCamera('rp1:spec');
  assert.equal(consumeMainCamera('archive:spec'), undefined);
  assert.deepEqual(consumeMainCamera('rp1:spec'), pose);
  assert.equal(consumeMainCamera('rp1:spec'), undefined);
  captureMainCamera('rp1:spec'); clearMainCamera('rp1:spec');
  assert.equal(consumeMainCamera('rp1:spec'), undefined);
  release(); captureMainCamera('rp1:spec');
  assert.equal(consumeMainCamera('rp1:spec'), undefined);
});

test('camera capture rejects unavailable and nonfinite poses', () => {
  const release = registerMainCamera('bad', () => ({position:[NaN,0,0],up:[0,1,0],target:[0,0,0]}));
  captureMainCamera('bad'); assert.equal(consumeMainCamera('bad'), undefined); release();
});
test('a restored main pose survives effect replay while a new user command still frames', () => {
  assert.equal(mainCameraCommand(null, 7, true), 'restore');
  assert.equal(mainCameraCommand(7, 7, true), 'skip');
  assert.equal(mainCameraCommand(7, 8, true), 'frame');
  assert.equal(mainCameraCommand(null, 7, false), 'frame');
  assert.equal(mainCameraCommand(7, 7, false), 'skip');
});
