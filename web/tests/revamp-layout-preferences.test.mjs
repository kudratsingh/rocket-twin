import assert from 'node:assert/strict';
import test from 'node:test';
import {
  defaultLayout,
  normalizeLayout,
  parseLayout,
  readLayout,
  writeLayout,
  layoutStorageKey,
  layoutReducer,
  resizeLayoutValue,
  compactEntryLayout,
} from '../src/workspaces/layoutPreferences.ts';

test('versioned layout input validates types, clamps sizes and never admits source or camera identity', () => {
  assert.deepEqual(parseLayout(null, 'design'), defaultLayout());
  for (const value of [
    '{broken',
    'null',
    '[]',
    JSON.stringify({ version: 2, workspace: 'design', preferences: { contextOpen: false } }),
    JSON.stringify({ version: 1, workspace: 'replay', preferences: { contextOpen: false } }),
  ])
    assert.deepEqual(parseLayout(value, 'design'), defaultLayout());
  const value = normalizeLayout({
    railOpen: false,
    contextOpen: 'false',
    contextWidth: 99999,
    toolsHeight: -999,
    toolsOpen: true,
    representation: '2d',
    contextTab: 'details',
    selectedId: 'borrowed-part',
    camera: [1, 2, 3],
    design: 'other-source',
  });
  assert.deepEqual(value, {
    railOpen: false,
    contextOpen: true,
    contextWidth: 440,
    toolsHeight: 140,
    toolsOpen: true,
    representation: '2d',
    contextTab: 'details',
  });
  assert.equal(normalizeLayout({ contextWidth: NaN, toolsHeight: Infinity }).contextWidth, 264);
  assert.equal(normalizeLayout({ contextWidth: NaN, toolsHeight: Infinity }).toolsHeight, 240);
  assert.equal(normalizeLayout({ representation: 'unknown' }).representation, 'auto');
});

test('storage writes safe per-workspace records and blocked storage has persistent in-memory fallback', () => {
  const values = new Map();
  const storage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  };
  const design = { ...defaultLayout(), contextTab: 'details', railOpen: false, toolsHeight: 320 };
  const replay = { ...defaultLayout(), toolsOpen: true };
  assert.equal(writeLayout('design', { ...design, selectedId: 'must-not-store' }, storage), true);
  assert.equal(writeLayout('replay', replay, storage), true);
  assert.deepEqual(readLayout('design', storage), design);
  assert.deepEqual(readLayout('replay', storage), replay);
  assert.notEqual(layoutStorageKey('design'), layoutStorageKey('replay'));
  assert.ok(!values.get(layoutStorageKey('design')).includes('must-not-store'));
  const blocked = {
    getItem() {
      throw Error('denied');
    },
    setItem() {
      throw Error('quota');
    },
  };
  const changed = { ...design, contextWidth: 308 };
  assert.equal(writeLayout('design', changed, blocked), false);
  assert.deepEqual(readLayout('design', blocked), changed);
  assert.deepEqual(readLayout('design', null), changed);
  assert.deepEqual(
    readLayout('design', storage),
    changed,
    'older stored record cannot erase a newer session choice after a failed write',
  );
  assert.deepEqual(readLayout('replay', storage), replay);
});

test('compact entry uses an on-demand context drawer while retaining sizes and independent rail choice', () => {
  const prefs = { ...defaultLayout(), railOpen: false, contextWidth: 336, toolsHeight: 300 };
  const compact = compactEntryLayout(prefs, 900);
  assert.equal(compact.contextOpen, false);
  assert.equal(compact.contextWidth, 336);
  assert.equal(compact.toolsHeight, 300);
  assert.equal(compact.railOpen, false);
  assert.equal(prefs.contextOpen, true);
  assert.equal(compactEntryLayout(prefs, 1280), prefs);
  assert.equal(compactEntryLayout(prefs, Infinity), prefs);
});

test('focus snapshots exact chrome and restores it without adding identity or camera state', () => {
  const previous = {
    ...defaultLayout(),
    railOpen: false,
    contextWidth: 336,
    contextTab: 'details',
    toolsOpen: true,
    toolsHeight: 288,
  };
  const state = { preferences: previous, focusSnapshot: null };
  const focused = layoutReducer(state, { type: 'focus' });
  assert.equal(focused.preferences.railOpen, false);
  assert.equal(focused.preferences.contextOpen, false);
  assert.equal(focused.preferences.toolsOpen, false);
  assert.deepEqual(focused.focusSnapshot, previous);
  assert.deepEqual(state.preferences, previous);
  assert.deepEqual(layoutReducer(focused, { type: 'exit-focus' }), state);
  assert.deepEqual(layoutReducer(focused, { type: 'focus' }), state);
  assert.deepEqual(Object.keys(focused).sort(), ['focusSnapshot', 'preferences']);
  const representation = layoutReducer(focused, {
    type: 'update',
    patch: { representation: '2d' },
  });
  assert.ok(representation.focusSnapshot);
  assert.equal(representation.preferences.contextOpen, false);
  assert.deepEqual(layoutReducer(representation, { type: 'exit-focus' }).preferences, {
    ...previous,
    representation: '2d',
  });
});

test('panel openers exit focus explicitly and independent column changes preserve other preferences', () => {
  let state = { preferences: defaultLayout(), focusSnapshot: null };
  state = layoutReducer(state, { type: 'update', patch: { railOpen: false } });
  assert.equal(state.preferences.contextOpen, true);
  state = layoutReducer(state, { type: 'update', patch: { contextOpen: false } });
  assert.equal(state.preferences.railOpen, false);
  state = layoutReducer(state, { type: 'focus' });
  state = layoutReducer(state, {
    type: 'update',
    patch: { contextOpen: true, contextTab: 'details' },
  });
  assert.equal(state.focusSnapshot, null);
  assert.equal(state.preferences.contextOpen, true);
  assert.equal(state.preferences.railOpen, false);
  assert.deepEqual(layoutReducer(state, { type: 'reset' }), {
    preferences: defaultLayout(),
    focusSnapshot: null,
  });
});

test('splitter keyboard directions, endpoints and clamps are predictable', () => {
  assert.equal(resizeLayoutValue('context', 264, 'ArrowRight'), 280);
  assert.equal(resizeLayoutValue('context', 264, 'ArrowLeft'), 248);
  assert.equal(resizeLayoutValue('context', 440, 'ArrowRight'), 440);
  assert.equal(resizeLayoutValue('context', 220, 'ArrowLeft'), 220);
  assert.equal(resizeLayoutValue('context', 264, 'Home'), 220);
  assert.equal(resizeLayoutValue('context', 264, 'End'), 440);
  assert.equal(resizeLayoutValue('tools', 240, 'ArrowUp'), 256);
  assert.equal(resizeLayoutValue('tools', 240, 'ArrowDown'), 224);
  assert.equal(resizeLayoutValue('tools', 420, 'ArrowUp'), 420);
  assert.equal(resizeLayoutValue('tools', 140, 'ArrowDown'), 140);
  assert.equal(resizeLayoutValue('tools', 240, 'Home'), 140);
  assert.equal(resizeLayoutValue('tools', 240, 'End'), 420);
  assert.equal(resizeLayoutValue('tools', 240, 'ArrowRight'), null);
});

test('both sidebar tabs and all column combinations retain widths across close, reopen and Focus', () => {
  for (const contextTab of ['parts', 'details']) {
    for (const railOpen of [false, true]) {
      for (const contextOpen of [false, true]) {
        const preferences = {
          ...defaultLayout(),
          contextTab,
          railOpen,
          contextOpen,
          contextWidth: 336,
          toolsHeight: 288,
        };
        let state = { preferences, focusSnapshot: null };
        state = layoutReducer(state, { type: 'focus' });
        state = layoutReducer(state, { type: 'exit-focus' });
        assert.deepEqual(state.preferences, preferences);
        state = layoutReducer(state, { type: 'update', patch: { contextOpen: false } });
        state = layoutReducer(state, { type: 'update', patch: { contextOpen: true } });
        assert.deepEqual(state.preferences, { ...preferences, contextOpen: true });
        state = layoutReducer(state, { type: 'update', patch: { railOpen: !railOpen } });
        state = layoutReducer(state, { type: 'update', patch: { railOpen } });
        assert.deepEqual(state.preferences, { ...preferences, contextOpen: true });
        assert.ok(!('selectedId' in state.preferences));
        assert.ok(!('camera' in state.preferences));
      }
    }
  }
});
