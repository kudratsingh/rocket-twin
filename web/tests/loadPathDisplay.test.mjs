import assert from 'node:assert/strict';
import test from 'node:test';
import { layoutLoadPath, recordedValue } from '../src/workbench/loadPathDisplay.ts';

test('load-path display retains branch nodes and the convergence joint', () => {
  const nodes = ['harness', 'fore', 'aft', 'body'].map((id) => ({ id, label: id }));
  const edges = [
    ['harness', 'fore'],
    ['harness', 'aft'],
    ['fore', 'body'],
    ['aft', 'body'],
  ].map(([from, to]) => ({ from, to }));
  const layout = layoutLoadPath({ nodes, edges });
  assert.equal(layout.hasCycle, false);
  assert.equal(layout.positions.size, 4);
  assert.equal(layout.positions.get('fore').y, layout.positions.get('aft').y);
  assert.notEqual(layout.positions.get('fore').x, layout.positions.get('aft').x);
  assert.ok(layout.positions.get('body').y > layout.positions.get('fore').y);
});

test('cyclic evidence stays visible and absent values never become zero', () => {
  const layout = layoutLoadPath({
    nodes: [
      { id: 'a', label: 'A' },
      { id: 'b', label: 'B' },
    ],
    edges: [
      { from: 'a', to: 'b' },
      { from: 'b', to: 'a' },
    ],
  });
  assert.equal(layout.hasCycle, true);
  assert.equal(layout.positions.size, 2);
  assert.equal(recordedValue(null, 'N'), 'Unavailable (N)');
  assert.equal(recordedValue(0, 'N'), '0 N');
  assert.equal(recordedValue(15.00025187, 'm/s'), '15.00025187 m/s');
});
