import assert from 'node:assert/strict';
import test from 'node:test';
import { useInspection } from '../src/store.ts';
import { readPartLink } from '../src/workspaces/partLinks.ts';
import { inspectionSelectionHref } from '../src/workspaces/selectionWriteback.ts';

const AD1 = 'G80-F2-RP1-AD1-definition-v2';
const SPEC = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
const source = () => ({
  id: AD1,
  summary: {},
  identity: { specification_sha256: SPEC },
  parts: [{ id: 'forward_ring' }, { id: 'fin_tabs' }, { id: 'body' }],
});
const route = `/?workspace=design&design=${AD1}&part=forward_ring&spec=${SPEC}&connection=recovery`;
const state = () => useInspection.getState();
const selection = () => ({
  selectedId: state().selectedId,
  selectionIntent: state().selectionIntent,
});
const query = (href) => new URL(href, 'http://local.test').searchParams;

test('internal vehicle reset cannot erase a valid pending part route; later explicit clear can', () => {
  state().resetVehicle();
  state().select('forward_ring');
  const beforeReset = selection();
  state().resetVehicle();
  const afterReset = selection();
  assert.equal(afterReset.selectedId, null);
  assert.equal(afterReset.selectionIntent, beforeReset.selectionIntent);
  assert.equal(inspectionSelectionHref(route, source(), afterReset, beforeReset, 'design'), null);

  const verifiedSource = source();
  assert.deepEqual(readPartLink(query(route).toString(), verifiedSource), {
    part: 'forward_ring',
    notice: null,
  });
  state().select('forward_ring'); // Route hydration precedes writeback subscription.
  assert.equal(state().selectedId, 'forward_ring');
  let href = route;
  const unsubscribe = useInspection.subscribe((current, previous) => {
    const next = inspectionSelectionHref(href, verifiedSource, current, previous, 'design');
    if (next !== null) href = next;
  });
  try {
    state().select(null); // The visible Clear or Escape action is an intent.
    assert.equal(query(href).has('part'), false);
    assert.equal(query(href).get('design'), AD1);
    assert.equal(query(href).get('spec'), SPEC);
    assert.equal(query(href).get('connection'), 'recovery');
  } finally {
    unsubscribe();
    state().resetVehicle();
  }
});

test('explicit other-part, group clear, and successful focus write selection with source context', () => {
  state().resetVehicle();
  state().select('forward_ring');
  let previous = selection();
  state().select('fin_tabs');
  let next = inspectionSelectionHref(route, source(), selection(), previous, 'design');
  assert.equal(query(next).get('part'), 'fin_tabs');
  assert.equal(query(next).get('connection'), 'recovery');

  previous = selection();
  state().selectGroup('fins', ['fin_tabs']);
  next = inspectionSelectionHref(next, source(), selection(), previous, 'design');
  assert.equal(query(next).has('part'), false);
  assert.equal(query(next).get('connection'), 'recovery');

  state().setAvailableMeshes(['forward_ring', 'fin_tabs']);
  previous = selection();
  state().focusPart('forward_ring');
  next = inspectionSelectionHref(next, source(), selection(), previous, 'design');
  assert.equal(query(next).get('part'), 'forward_ring');
  assert.equal(query(next).get('spec'), SPEC);

  previous = selection();
  state().focusPart('body'); // Mesh availability rejects this focus.
  assert.equal(inspectionSelectionHref(next, source(), selection(), previous, 'design'), null);
  state().resetVehicle();
});

test('foreign selection, stale link, invalid link, and unchanged intent never rewrite the URL', () => {
  state().resetVehicle();
  state().select('forward_ring');
  let previous = selection();
  state().select('foreign');
  assert.equal(inspectionSelectionHref(route, source(), selection(), previous, 'design'), null);

  previous = selection();
  state().select('fin_tabs');
  const stale = route.replace(SPEC, 'b'.repeat(64));
  assert.match(readPartLink(query(stale).toString(), source()).notice, /unavailable/);
  assert.equal(inspectionSelectionHref(stale, source(), selection(), previous, 'design'), null);
  const foreignPart = route.replace('part=forward_ring', 'part=other');
  assert.match(readPartLink(query(foreignPart).toString(), source()).notice, /unavailable/);
  assert.equal(
    inspectionSelectionHref(foreignPart, source(), selection(), previous, 'design'),
    null,
  );

  previous = selection();
  state().resetVehicle();
  assert.equal(inspectionSelectionHref(route, source(), selection(), previous, 'design'), null);
  state().resetVehicle();
});
