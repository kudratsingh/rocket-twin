/** A run's recorded playback support; invalid time axes never imply coverage. */
export type ReplayWindow = { start: number; end: number } | null;
export type ReplayWindowStatus = 'inside' | 'outside' | 'unavailable';

export function replayWindow(times: readonly number[] | undefined): ReplayWindow {
  if (
    !Array.isArray(times) ||
    times.length === 0 ||
    !times.every((time, index) => Number.isFinite(time) && (index === 0 || time > times[index - 1]))
  )
    return null;
  return { start: times[0], end: times[times.length - 1] };
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
