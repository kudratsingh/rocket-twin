import assert from 'node:assert/strict';
import test from 'node:test';
import { matchesPartSearch } from '../src/components/partSearch.ts';

test('finds exact recorded part IDs and existing display attributes', () => {
  const part = { id: 'frame_ring_aft_01', name: 'Aft frame', type: 'ring', material: 'G11' };
  assert.equal(matchesPartSearch('  RING_AFT_01 ', part), true);
  assert.equal(matchesPartSearch('aft frame', part), true);
  assert.equal(matchesPartSearch('aft frame ring', part), true);
  assert.equal(matchesPartSearch('ring', part), true);
  assert.equal(matchesPartSearch('g11', part), true);
  assert.equal(matchesPartSearch('frame_ring_aft_02', part), false);
});
