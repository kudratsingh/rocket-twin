import assert from 'node:assert/strict';
import test from 'node:test';
import { useInspection } from '../src/store.ts';

test('focusing a hidden part restores just that part and retains the viewing angle', () => {
  const state = () => useInspection.getState();
  state().resetVehicle();
  state().setCameraView('aft');
  state().hideParts(['shell', 'motor', 'battery']);
  state().focusPart('motor');
  assert.equal(state().selectedId, 'motor');
  assert.equal(state().focusId, 'motor');
  assert.equal(state().cameraAction, 'focus');
  assert.equal(state().cameraView, 'aft');
  assert.deepEqual(state().hiddenIds, ['shell', 'battery']);
  state().fitVisible();
  assert.equal(state().focusId, null);
  assert.equal(state().cameraAction, 'fit');
  assert.equal(state().cameraView, 'aft');
  assert.deepEqual(state().hiddenIds, ['shell', 'battery']);
});

test('switching designs clears display modes and focus so candidate settings do not leak', () => {
  const state = () => useInspection.getState();
  state().resetVehicle();
  state().focusPart('old-candidate-part');
  state().setCameraView('side');
  state().toggleGhostShell();
  state().toggleWireframe();
  state().togglePartLabels();
  state().toggleMarkers();
  state().setExploded(1);
  state().resetVehicle();
  assert.equal(state().selectedId, null);
  assert.equal(state().focusId, null);
  assert.equal(state().cameraView, 'overview');
  assert.equal(state().cameraAction, 'reset');
  assert.equal(state().ghostShell, false);
  assert.equal(state().wireframe, false);
  assert.equal(state().partLabels, true);
  assert.equal(state().markers, true);
  assert.equal(state().exploded, 0);
});

test('meshless selection cannot isolate or frame away all source solids', () => {
  const state = () => useInspection.getState();
  state().resetVehicle();
  state().setAvailableMeshes(['tube', 'motor']);
  state().hideParts(['tube']);
  state().select('kevlar_allowance');
  const token = state().resetToken;
  state().isolate('kevlar_allowance', ['tube', 'motor', 'kevlar_allowance']);
  state().focusPart('kevlar_allowance');
  assert.equal(state().selectedId, 'kevlar_allowance');
  assert.deepEqual(state().hiddenIds, ['tube']);
  assert.equal(state().isolatedFrom, null);
  assert.equal(state().resetToken, token);
});

test('group isolation preserves and restores previous visibility, meshless group is a no-op', () => {
  const state = () => useInspection.getState();
  state().resetVehicle();
  state().setAvailableMeshes(['tube', 'motor', 'ring']);
  state().hideParts(['ring']);
  state().selectGroup('motor_retention', ['motor', 'ring', 'adhesive']);
  state().isolateGroup(['motor', 'ring', 'adhesive']);
  assert.deepEqual(state().hiddenIds, ['tube']);
  state().exitIsolate();
  assert.deepEqual(state().hiddenIds, ['ring']);
  state().isolateGroup(['adhesive']);
  assert.deepEqual(state().hiddenIds, ['ring']);
  assert.equal(state().isolatedFrom, null);
});
