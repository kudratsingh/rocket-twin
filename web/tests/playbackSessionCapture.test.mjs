import assert from 'node:assert/strict';
import test from 'node:test';
import { createPlaybackSessionCapture } from '../src/experiments/playbackSessionCapture.ts';

function context() {
  return {
    primary: { run_id: 'A', code_sha256: 'code-a', resolved_sha256: 'spec-a' },
    comparison: { run_id: 'B', cad_revision_sha256: 'cad-b' },
    profileMode: 'full-rate-benchmark',
    speed: 1,
    firstObservedCursorS: 0.001,
    startedWallMs: 100,
    alignment: { event: null, offsetAS: 0, offsetBS: 0 },
  };
}

function frame(deltaMs, overrides = {}) {
  return {
    deltaMs,
    observedCursorS: 0.001,
    documentVisibility: 'visible',
    windowFocused: true,
    canvasIntersectionFraction: 1,
    ...overrides,
  };
}

function snapshot(capture) {
  return capture.snapshot({ lastObservedCursorS: 1.001, endedWallMs: 1100 });
}

test('constant 16 ms meets strict unrounded target over all captured frames', () => {
  const capture = createPlaybackSessionCapture(context());
  for (let i = 0; i < 1000; i++) capture.appendFrame(frame(16));
  const result = snapshot(capture);
  assert.deepEqual(result.raf.stats, {
    samples: 1000,
    mean_ms: 16,
    p50_ms: 16,
    p95_ms: 16,
    max_ms: 16,
  });
  assert.equal(result.raf.mean_interval_target_met, true);
  assert.equal(result.raf.observed_raf_duration_ms, 16000);
  assert.equal(result.environment.observed_wall_duration_ms, 1000);
  assert.deepEqual(result.condition_failures, []);
});

test('16.7 and 17.5 ms distributions fail without rounding or rolling 600 slicing', () => {
  for (const value of [16.7, 17.5]) {
    const capture = createPlaybackSessionCapture(context());
    for (let i = 0; i < 601; i++) capture.appendFrame(frame(value));
    const result = snapshot(capture);
    assert.equal(result.raf.stats.samples, 601);
    assert.equal(result.raf.mean_interval_target_met, false);
    assert.equal(result.raf.stats.p95_ms, value);
  }
});

test('large gap remains in complete session mean and p95', () => {
  const capture = createPlaybackSessionCapture(context());
  for (let i = 0; i < 19; i++) capture.appendFrame(frame(16));
  capture.appendFrame(frame(100));
  const result = snapshot(capture);
  assert.equal(result.raf.stats.max_ms, 100);
  assert.equal(result.raf.stats.mean_ms, 20.2);
  assert.equal(result.raf.mean_interval_target_met, false);
});

test('unknown visibility stays null rather than zero or visible', () => {
  const capture = createPlaybackSessionCapture(context());
  capture.appendFrame({ deltaMs: 16, observedCursorS: 0.5 });
  const result = snapshot(capture);
  assert.equal(result.raf.raw_frames[0].document_visibility, null);
  assert.equal(result.raf.raw_frames[0].window_focused, null);
  assert.equal(result.raf.raw_frames[0].canvas_intersection_fraction, null);
  assert(result.condition_failures.includes('canvas_intersection_unknown'));
  assert(result.condition_failures.includes('document_visibility_unknown'));
  assert(result.condition_failures.includes('window_focus_unknown'));
});

test('invalid delta is retained as null and cannot produce a passing mean', () => {
  const capture = createPlaybackSessionCapture(context());
  capture.appendFrame(frame(16));
  capture.appendFrame(frame(NaN, { canvasIntersectionFraction: 2 }));
  const result = snapshot(capture);
  assert.equal(result.raf.raw_frames[1].delta_ms, null);
  assert.equal(result.raf.invalid_interval_count, 1);
  assert.equal(result.raf.mean_interval_target_met, null);
  assert(result.condition_failures.includes('invalid_frame_intervals'));
  assert(result.condition_failures.includes('invalid_canvas_intersection'));
});

test('frame cap is explicit and ineligible, never silently truncated to pass', () => {
  const capture = createPlaybackSessionCapture(context());
  for (let i = 0; i < 24001; i++) capture.appendFrame(frame(16));
  const result = snapshot(capture);
  assert.equal(result.raf.observed_interval_count, 24001);
  assert.equal(result.raf.stored_interval_count, 24000);
  assert.equal(result.raf.overflow_interval_count, 1);
  assert.equal(result.raf.mean_interval_target_met, null);
  assert(result.condition_failures.includes('capture_cap_exceeded'));
});

test('source context and returned snapshot cannot be mutated through caller objects', () => {
  const input = context();
  const capture = createPlaybackSessionCapture(input);
  input.primary.run_id = 'foreign';
  input.alignment.offsetAS = 99;
  capture.appendFrame(frame(16));
  capture.observeEvent({ kind: 'intersection', canvasIntersectionFraction: 0.5 });
  const first = snapshot(capture);
  assert.equal(first.context.primary.run_id, 'A');
  assert.equal(first.context.alignment.offsetAS, 0);
  first.context.primary.run_id = 'changed';
  first.raf.raw_frames[0].delta_ms = 999;
  const second = snapshot(capture);
  assert.equal(second.context.primary.run_id, 'A');
  assert.equal(second.raf.raw_frames[0].delta_ms, 16);
  assert.equal(second.events.raw[0].canvas_intersection_fraction, 0.5);
});

test('hidden and focus-loss events between visible RAF frames remain condition failures', () => {
  const capture = createPlaybackSessionCapture(context());
  capture.appendFrame(frame(16));
  capture.observeEvent({
    kind: 'visibility',
    documentVisibility: 'hidden',
    windowFocused: false,
    canvasIntersectionFraction: 1,
  });
  capture.appendFrame(frame(16));
  const result = snapshot(capture);
  assert.equal(result.raf.mean_interval_target_met, true, 'timing verdict remains separate');
  assert(result.condition_failures.includes('document_not_visible'));
  assert(result.condition_failures.includes('window_not_focused'));
});

test('zero canvas intersection is actual nonvisibility, distinct from unknown', () => {
  const capture = createPlaybackSessionCapture(context());
  capture.appendFrame(frame(16, { canvasIntersectionFraction: 0 }));
  const result = snapshot(capture);
  assert.equal(result.raf.raw_frames[0].canvas_intersection_fraction, 0);
  assert(result.condition_failures.includes('canvas_not_fully_visible'));
  assert(!result.condition_failures.includes('canvas_intersection_unknown'));
});

test('resize event and missing cursor endpoints remain explicit', () => {
  const input = context();
  input.firstObservedCursorS = null;
  const capture = createPlaybackSessionCapture(input);
  capture.appendFrame(frame(16));
  capture.observeEvent({
    kind: 'resize',
    documentVisibility: 'visible',
    windowFocused: true,
    canvasIntersectionFraction: 1,
  });
  const result = capture.snapshot({ lastObservedCursorS: null, endedWallMs: 1100 });
  assert(result.condition_failures.includes('resize_observed'));
  assert(result.condition_failures.includes('first_cursor_unknown'));
  assert(result.condition_failures.includes('last_cursor_unknown'));
  assert.equal(result.context.first_observed_cursor_s, null);
  assert.equal(result.context.last_observed_cursor_s, null);
});
