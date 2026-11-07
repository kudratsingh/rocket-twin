/** Display coordinates only: preserve each run's native clock and missing samples. */
export type PlotWindow = { start: number; end: number };
export type Alignment = { event: string | null; a: number; b: number; reason: string | null };

export function recordedAlignment(
  event: string,
  a?: Record<string, number | null>,
  b?: Record<string, number | null>,
): Alignment {
  if (event === 'absolute') return { event: null, a: 0, b: 0, reason: null };
  const left = a?.[event],
    right = b?.[event];
  if (
    typeof left !== 'number' ||
    !Number.isFinite(left) ||
    left < 0 ||
    typeof right !== 'number' ||
    !Number.isFinite(right) ||
    right < 0
  )
    return {
      event: null,
      a: 0,
      b: 0,
      reason: `Recorded ${event} unavailable in one or both runs; absolute time retained.`,
    };
  return { event, a: left, b: right, reason: null };
}

export function plotSegments(
  times: readonly number[],
  values: readonly number[] | undefined,
  offset: number,
  window: PlotWindow,
): [number, number][][] {
  if (
    !values ||
    times.length !== values.length ||
    !Number.isFinite(offset) ||
    !Number.isFinite(window.start) ||
    !Number.isFinite(window.end) ||
    window.end <= window.start ||
    !times.every((t, i) => Number.isFinite(t) && (i === 0 || t > times[i - 1]))
  )
    return [];
  const segments: [number, number][][] = [];
  let segment: [number, number][] = [];
  times.forEach((raw, index) => {
    const time = raw - offset,
      value = values[index];
    if (!Number.isFinite(value) || time < window.start || time > window.end) {
      if (segment.length) segments.push(segment);
      segment = [];
    } else segment.push([time, value]);
  });
  if (segment.length) segments.push(segment);
  return segments;
}

export function adjustPlotWindow(
  current: PlotWindow,
  full: PlotWindow,
  action: 'in' | 'out' | 'left' | 'right',
): PlotWindow {
  const span = current.end - current.start;
  const total = full.end - full.start;
  const nextSpan = Math.min(
    total,
    Math.max(Math.min(0.01, total), span * (action === 'in' ? 0.5 : action === 'out' ? 2 : 1)),
  );
  const center =
    (current.start + current.end) / 2 +
    (action === 'left' ? -span * 0.25 : action === 'right' ? span * 0.25 : 0);
  const start = Math.max(full.start, Math.min(full.end - nextSpan, center - nextSpan / 2));
  return { start, end: start + nextSpan };
}
