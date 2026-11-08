import { replayWindow } from './replayWindow.ts';
import { measureReplayWork } from './replayWorkProfile.ts';

export type ReplayDrawingOptions = {
  maxVertices?: number;
  events?: Record<string, number | null>;
  window?: { start: number; end: number };
  offset?: number;
};
export type ReplayDrawing = {
  status: 'ready' | 'withheld';
  reason: string | null;
  segments: number[][];
  source_samples: number;
  valid_samples: number;
  drawn_samples: number;
  max_vertices: number;
  mandatory_samples: number;
  unavailable_events: string[];
  event_indices: number[];
  preparation_ms: number;
  policy: string;
};
const policy =
  'Display-only native-index selection: native segment endpoints/extrema and drawable recorded-event neighbours retained; explicit missing/nonfinite channel values split segments, but irregular timestamp spacing alone does not; no synthetic samples, gap joining or raw-data replacement';

/** Bound only drawing geometry. Pose, readouts, event clocks, metrics and exports keep raw arrays. */
export function selectReplayDrawing(
  times: readonly number[],
  channels: readonly (readonly number[])[],
  options: ReplayDrawingOptions = {},
): ReplayDrawing {
  const measured = measureReplayWork('bounded replay drawing index selection', () => {
    const max = options.maxVertices ?? 3000,
      offset = options.offset ?? 0,
      support = replayWindow(times);
    const base = {
      source_samples: Array.isArray(times) ? times.length : 0,
      valid_samples: 0,
      drawn_samples: 0,
      max_vertices: max,
      mandatory_samples: 0,
      unavailable_events: [] as string[],
      event_indices: [] as number[],
      policy,
    };
    const withheld = (reason: string): Omit<ReplayDrawing, 'preparation_ms'> => ({
      ...base,
      status: 'withheld',
      reason,
      segments: [],
    });
    if (
      !support ||
      !Number.isInteger(max) ||
      max < 2 ||
      max > 10000 ||
      !Number.isFinite(offset) ||
      !channels.length ||
      channels.some((values) => !Array.isArray(values) || values.length !== times.length)
    )
      return withheld(
        'Drawing unavailable: invalid native coverage, channel lengths or vertex budget.',
      );
    const window = options.window ?? { start: support.start - offset, end: support.end - offset };
    if (!Number.isFinite(window.start) || !Number.isFinite(window.end) || window.end < window.start)
      return withheld('Drawing unavailable: invalid display range.');
    type Range = { start: number; end: number; min: number[]; max: number[] };
    const ranges: Range[] = [];
    let current: Range | null = null;
    for (let i = 0; i < times.length; i++) {
      const display = times[i] - offset;
      if (
        display < window.start ||
        display > window.end ||
        channels.some((values) => !Number.isFinite(values[i]))
      ) {
        if (current) ranges.push(current);
        current = null;
        continue;
      }
      base.valid_samples++;
      if (!current)
        current = { start: i, end: i, min: channels.map(() => i), max: channels.map(() => i) };
      else {
        current.end = i;
        channels.forEach((values, k) => {
          if (values[i] < values[current!.min[k]]) current!.min[k] = i;
          if (values[i] > values[current!.max[k]]) current!.max[k] = i;
        });
      }
    }
    if (current) ranges.push(current);
    if (!ranges.length)
      return withheld('No valid native samples in this drawing range; missing data is not zero.');
    if (ranges.length > 128)
      return withheld(
        'Drawing withheld: more than 128 disconnected native segments exceeds the draw-call budget. Gaps are not joined; raw telemetry remains available.',
      );
    const mandatory = new Set<number>();
    for (const range of ranges)
      for (const i of [range.start, range.end, ...range.min, ...range.max]) mandatory.add(i);
    const inRange = (index: number) => {
      let left = 0,
        right = ranges.length - 1;
      while (left <= right) {
        const middle = (left + right) >> 1,
          range = ranges[middle];
        if (index < range.start) right = middle - 1;
        else if (index > range.end) left = middle + 1;
        else return true;
      }
      return false;
    };
    const eventIndices = new Set<number>();
    for (const [name, event] of Object.entries(options.events ?? {})) {
      if (
        typeof event !== 'number' ||
        !Number.isFinite(event) ||
        event < support.start ||
        event > support.end
      ) {
        base.unavailable_events.push(name);
        continue;
      }
      if (event - offset < window.start || event - offset > window.end) continue;
      let left = 0,
        right = times.length - 1;
      while (left < right) {
        const middle = (left + right) >> 1;
        if (times[middle] < event) left = middle + 1;
        else right = middle;
      }
      let drawable = false;
      for (const index of [left - 1, left, ...(times[left] === event ? [left + 1] : [])])
        if (index >= 0 && index < times.length && inRange(index)) {
          mandatory.add(index);
          eventIndices.add(index);
          drawable = true;
        }
      if (!drawable) base.unavailable_events.push(name);
    }
    base.mandatory_samples = mandatory.size;
    base.event_indices = [...eventIndices].sort((a, b) => a - b);
    if (mandatory.size > max)
      return withheld(
        'Drawing withheld: preserving all gap boundaries, extrema and event neighbours exceeds the declared vertex budget. Raw telemetry remains available.',
      );
    const chosen = new Set(mandatory);
    if (base.valid_samples <= max)
      for (const range of ranges) for (let i = range.start; i <= range.end; i++) chosen.add(i);
    else {
      const buckets = Math.floor((max - mandatory.size) / (2 * channels.length));
      if (buckets > 0) {
        const first = ranges[0].start,
          last = ranges.at(-1)!.end;
        const minima = Array.from({ length: buckets }, () => channels.map(() => -1)),
          maxima = Array.from({ length: buckets }, () => channels.map(() => -1));
        for (const range of ranges)
          for (let i = range.start; i <= range.end; i++) {
            const b = Math.min(
              buckets - 1,
              Math.floor(((i - first) / Math.max(1, last - first)) * buckets),
            );
            channels.forEach((values, k) => {
              if (minima[b][k] < 0 || values[i] < values[minima[b][k]]) minima[b][k] = i;
              if (maxima[b][k] < 0 || values[i] > values[maxima[b][k]]) maxima[b][k] = i;
            });
          }
        for (let b = 0; b < buckets; b++)
          for (let k = 0; k < channels.length; k++)
            for (const index of [minima[b][k], maxima[b][k]]) if (index >= 0) chosen.add(index);
      }
    }
    const indices = [...chosen].sort((a, b) => a - b);
    let cursor = 0;
    const segments = ranges
      .map((range) => {
        const segment: number[] = [];
        while (cursor < indices.length && indices[cursor] <= range.end)
          segment.push(indices[cursor++]);
        return segment;
      })
      .filter((segment) => segment.length);
    return {
      ...base,
      status: 'ready' as const,
      reason: null,
      segments,
      drawn_samples: indices.length,
    };
  });
  return { ...measured.value, preparation_ms: measured.timing.elapsed_ms };
}

export function replayDrawingDiagnostics(drawing: ReplayDrawing) {
  return {
    status: drawing.status,
    reason: drawing.reason,
    source_samples: drawing.source_samples,
    valid_samples: drawing.valid_samples,
    drawn_samples: drawing.drawn_samples,
    max_vertices: drawing.max_vertices,
    segments: drawing.segments.length,
    mandatory_samples: drawing.mandatory_samples,
    event_neighbours: drawing.event_indices.length,
    unavailable_events: drawing.unavailable_events,
    preparation_ms: drawing.preparation_ms,
    policy: drawing.policy,
  };
}
