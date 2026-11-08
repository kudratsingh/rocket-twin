/** A run's recorded playback support; invalid time axes never imply coverage. */
export type ReplayWindow = Readonly<{ start: number; end: number }> | null;
export type ReplayWindowStatus = 'inside' | 'outside' | 'unavailable';

// Frozen data arrays cannot change after admission. Mutable/accessor arrays are
// always inspected again; neither a previous pass nor a previous failure is trusted.
const frozenWindows = new WeakMap<readonly number[], ReplayWindow>();

export function replayWindow(times: readonly number[] | undefined): ReplayWindow {
  if (!Array.isArray(times)) return null;
  const cached = frozenWindows.get(times);
  if (cached !== undefined) return cached;
  const frozen = Object.isFrozen(times);
  let cacheable = frozen;
  let valid = times.length > 0;
  let previous = -Infinity;
  let first = NaN;
  for (let index = 0; index < times.length; index++) {
    if (frozen) {
      const descriptor = Object.getOwnPropertyDescriptor(times, index);
      // A frozen getter can still read mutable external state; it is not immutable data.
      if (!descriptor || !('value' in descriptor)) cacheable = false;
    }
    const time = times[index];
    if (index === 0) first = time;
    if (!Number.isFinite(time) || (index > 0 && time <= previous)) valid = false;
    previous = time;
  }
  const window = valid ? Object.freeze({ start: first, end: previous }) : null;
  if (cacheable) frozenWindows.set(times, window);
  return window;
}

export function replayWindowStatus(window: ReplayWindow, time: number): ReplayWindowStatus {
  if (!window || !Number.isFinite(time)) return 'unavailable';
  return time >= window.start && time <= window.end ? 'inside' : 'outside';
}

/** Start paused playback at real recorded data, not an extrapolated ignition pose. */
export function firstRecordedTime(...windows: ReplayWindow[]): number {
  const starts = windows.flatMap((window) => (window ? [window.start] : []));
  return starts.length ? Math.min(...starts) : 0;
}
