import assert from 'node:assert/strict';
import test from 'node:test';
import { Box3, Vector3 } from 'three';
import { inspectionSceneBounds } from '../src/components/inspectionSceneBounds.ts';
import { useInspection } from '../src/store.ts';

test('assembly, visible and part scopes use only their own loaded mesh bounds and display placement', () => {
  const source = new Box3(new Vector3(-0.001, 0.2, -0.001), new Vector3(0.001, 0.202, 0.001));
  const records = new Map([
    ['ring', { bounds: source, explodeOffset: [0, 0.1, 0] }],
    [
      'body',
      {
        bounds: new Box3(new Vector3(-0.03, 0, -0.03), new Vector3(0.03, 1.2, 0.03)),
        explodeOffset: [0, 0, 0],
      },
    ],
  ]);
  const initial = source.clone();
  const part = inspectionSceneBounds(records, ['ring'], 0.5);
  assert.equal(part.available, 1);
  assert.equal(part.requested, 1);
  assert.ok(Math.abs(part.bounds.min.y - 0.25) < 1e-12);
  assert.ok(source.equals(initial), 'a display change must not mutate cached source bounds');
  const assembly = inspectionSceneBounds(records, ['ring', 'body', 'missing'], 0);
  assert.equal(assembly.available, 2);
  assert.equal(assembly.requested, 3);
  assert.equal(assembly.bounds.max.y, 1.2);
  const unavailable = inspectionSceneBounds(records, ['foreign-part'], 0);
  assert.equal(unavailable.available, 0);
  assert.ok(unavailable.bounds.isEmpty(), 'never invent an assembly-sized box');
});

test('exit isolate restores previous visibility and full restore clears its snapshot', () => {
  const state = () => useInspection.getState();
  state().resetVehicle();
  state().hideParts(['body']);
  state().select('ring');
  state().isolate('ring', ['body', 'ring', 'motor']);
  state().isolate('motor', ['body', 'ring', 'motor']);
  state().exitIsolate();
  assert.deepEqual(state().hiddenIds, ['body']);
  assert.equal(state().selectedId, 'ring');
  state().isolate('ring', ['body', 'ring', 'motor']);
  state().showAll();
  assert.deepEqual(state().hiddenIds, []);
  assert.equal(state().isolatedFrom, null);
  state().exitIsolate();
  assert.deepEqual(state().hiddenIds, []);
  state().resetVehicle();
});
