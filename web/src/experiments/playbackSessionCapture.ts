/** Bounded, app-observed RAF session evidence. This does not certify the 60 fps benchmark. */
export type PlaybackSessionSource = {
  run_id: string;
  code_sha256?: string;
  resolved_sha256?: string;
  cad_revision_sha256?: string;
};

export type PlaybackSessionContext = {
  primary: PlaybackSessionSource;
  comparison?: PlaybackSessionSource | null;
  profileMode: string;
  speed: number;
  firstObservedCursorS: number | null;
  startedWallMs: number | null;
  alignment?: { event: string | null; offsetAS: number | null; offsetBS: number | null };
};

export type PlaybackVisibility = 'visible' | 'hidden' | 'prerender' | null;
export type PlaybackFrameObservation = {
  deltaMs: number;
  observedCursorS?: number | null;
  documentVisibility?: PlaybackVisibility;
  windowFocused?: boolean | null;
  canvasIntersectionFraction?: number | null;
};

export type PlaybackSessionEvent = Omit<PlaybackFrameObservation, 'deltaMs'> & {
  kind: 'visibility' | 'focus' | 'resize' | 'intersection';
};

const MAX_FRAMES = 24000;
const TARGET_INTERVAL_MS = 1000 / 60;

function finiteOrNull(value: number | null | undefined): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function fractionOrNull(value: number | null | undefined): number | null {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1
    ? value
    : null;
}

function observedState(value: PlaybackFrameObservation | PlaybackSessionEvent) {
  return {
    observed_cursor_s: finiteOrNull(value.observedCursorS),
    document_visibility: value.documentVisibility ?? null,
    window_focused: typeof value.windowFocused === 'boolean' ? value.windowFocused : null,
    canvas_intersection_fraction: fractionOrNull(value.canvasIntersectionFraction),
  };
}

function percentile(sorted: readonly number[], proportion: number): number {
  return sorted[Math.min(sorted.length - 1, Math.ceil(sorted.length * proportion) - 1)];
}

export function createPlaybackSessionCapture(input: PlaybackSessionContext) {
  // Copy caller-owned identity once. Later UI changes cannot relabel this observation.
  const initialCursorInvalid =
    input.firstObservedCursorS != null && finiteOrNull(input.firstObservedCursorS) === null;
  const context = {
    primary: { ...input.primary },
    comparison: input.comparison ? { ...input.comparison } : null,
    profile_mode: input.profileMode,
    speed: input.speed,
    first_observed_cursor_s: finiteOrNull(input.firstObservedCursorS),
    started_wall_ms: finiteOrNull(input.startedWallMs),
    alignment: input.alignment ? { ...input.alignment } : null,
  };
  const frames: Array<ReturnType<typeof observedState> & { delta_ms: number | null }> = [];
  const events: Array<ReturnType<typeof observedState> & { kind: PlaybackSessionEvent['kind'] }> =
    [];
  let observedFrameCount = 0;
  let overflowFrameCount = 0;
  let invalidIntervalCount = 0;
  let invalidCanvasFractionCount = 0;
  let invalidCursorCount = 0;
  let overflowEventCount = 0;

  function noteInvalidState(value: PlaybackFrameObservation | PlaybackSessionEvent) {
    if (
      value.canvasIntersectionFraction != null &&
      fractionOrNull(value.canvasIntersectionFraction) === null
    )
      invalidCanvasFractionCount += 1;
    if (value.observedCursorS != null && finiteOrNull(value.observedCursorS) === null)
      invalidCursorCount += 1;
  }

  return {
    appendFrame(value: PlaybackFrameObservation) {
      observedFrameCount += 1;
      if (frames.length >= MAX_FRAMES) {
        overflowFrameCount += 1;
        return;
      }
      const validDelta = Number.isFinite(value.deltaMs) && value.deltaMs > 0;
      if (!validDelta) invalidIntervalCount += 1;
      noteInvalidState(value);
      frames.push({ delta_ms: validDelta ? value.deltaMs : null, ...observedState(value) });
    },
    observeEvent(value: PlaybackSessionEvent) {
      noteInvalidState(value);
      // Event history is separately bounded by the same frame budget.
      if (events.length >= MAX_FRAMES) {
        overflowEventCount += 1;
        return;
      }
      events.push({ kind: value.kind, ...observedState(value) });
    },
    snapshot(end: { lastObservedCursorS: number | null; endedWallMs: number | null }) {
      const valid = frames
        .map((frame) => frame.delta_ms)
        .filter((value): value is number => value !== null);
      const ordered = [...valid].sort((a, b) => a - b);
      const sum = valid.reduce((total, delta) => total + delta, 0);
      const stats = ordered.length
        ? {
            samples: ordered.length,
            mean_ms: sum / ordered.length,
            p50_ms: percentile(ordered, 0.5),
            p95_ms: percentile(ordered, 0.95),
            max_ms: ordered.at(-1)!,
          }
        : null;
      const endedWallMs = finiteOrNull(end.endedWallMs);
      const wallDurationMs =
        context.started_wall_ms !== null &&
        endedWallMs !== null &&
        endedWallMs >= context.started_wall_ms
          ? endedWallMs - context.started_wall_ms
          : null;
      const failures: string[] = [];
      if (!frames.length) failures.push('no_frame_intervals');
      if (invalidIntervalCount) failures.push('invalid_frame_intervals');
      if (overflowFrameCount) failures.push('capture_cap_exceeded');
      if (overflowEventCount) failures.push('event_cap_exceeded');
      if (invalidCanvasFractionCount) failures.push('invalid_canvas_intersection');
      if (
        invalidCursorCount ||
        initialCursorInvalid ||
        (end.lastObservedCursorS != null && finiteOrNull(end.lastObservedCursorS) === null)
      )
        failures.push('invalid_observed_cursor');
      if (context.first_observed_cursor_s === null) failures.push('first_cursor_unknown');
      if (finiteOrNull(end.lastObservedCursorS) === null) failures.push('last_cursor_unknown');
      if (!Number.isFinite(context.speed) || context.speed <= 0) failures.push('invalid_speed');
      if (wallDurationMs === null) failures.push('wall_duration_unavailable_or_invalid');
      const observedStates = [...frames, ...events];
      if (observedStates.some((state) => state.document_visibility === null))
        failures.push('document_visibility_unknown');
      if (
        observedStates.some(
          (state) => state.document_visibility !== null && state.document_visibility !== 'visible',
        )
      )
        failures.push('document_not_visible');
      if (observedStates.some((state) => state.window_focused === null))
        failures.push('window_focus_unknown');
      if (observedStates.some((state) => state.window_focused === false))
        failures.push('window_not_focused');
      if (observedStates.some((state) => state.canvas_intersection_fraction === null))
        failures.push('canvas_intersection_unknown');
      if (
        observedStates.some(
          (state) =>
            state.canvas_intersection_fraction !== null && state.canvas_intersection_fraction < 1,
        )
      )
        failures.push('canvas_not_fully_visible');
      if (events.some((event) => event.kind === 'resize')) failures.push('resize_observed');
      const allIntervalsValid =
        frames.length > 0 && invalidIntervalCount === 0 && overflowFrameCount === 0;
      return {
        schema_version: 'rocket-twin.playback-session-observation.v1',
        context: {
          primary: { ...context.primary },
          comparison: context.comparison ? { ...context.comparison } : null,
          profile_mode: context.profile_mode,
          speed: context.speed,
          alignment: context.alignment ? { ...context.alignment } : null,
          first_observed_cursor_s: context.first_observed_cursor_s,
          last_observed_cursor_s: finiteOrNull(end.lastObservedCursorS),
        },
        raf: {
          observed_interval_count: observedFrameCount,
          stored_interval_count: frames.length,
          overflow_interval_count: overflowFrameCount,
          invalid_interval_count: invalidIntervalCount,
          cap_intervals: MAX_FRAMES,
          raw_frames: frames.map((frame) => ({ ...frame })),
          observed_raf_duration_ms: allIntervalsValid ? sum : null,
          stats,
          target_fps: 60,
          target_interval_ms: TARGET_INTERVAL_MS,
          mean_interval_target_met:
            allIntervalsValid && stats ? stats.mean_ms <= TARGET_INTERVAL_MS : null,
        },
        events: {
          raw: events.map((event) => ({ ...event })),
          overflow_event_count: overflowEventCount,
          cap_events: MAX_FRAMES,
        },
        environment: {
          started_wall_ms: context.started_wall_ms,
          ended_wall_ms: endedWallMs,
          observed_wall_duration_ms: wallDurationMs,
        },
        condition_failures: failures,
        acceptance:
          'No automatic full benchmark or frontend acceptance. RAF timing is not GPU completion; inspect exact data, visible scene, host, load, scrub and memory evidence separately.',
      };
    },
  };
}

export type PlaybackSessionSnapshot = ReturnType<
  ReturnType<typeof createPlaybackSessionCapture>['snapshot']
>;
