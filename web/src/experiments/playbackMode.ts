/** Explicit data-profile selection; this never changes a run or its physics. */
export type PlaybackMode = 'bounded' | 'full-rate-benchmark';
export const benchmarkBounds = { maxRows: 150000, maxRawChannels: 64, maxReturnedChannels: 73 };
export function telemetryUrl(id: string, mode: PlaybackMode): string {
  return `/api/runs/${encodeURIComponent(id)}/telemetry${mode === 'full-rate-benchmark' ? '?playback=full-rate-benchmark' : ''}`;
}
export function validatePlaybackProfile(
  telemetry: {
    full_sample_count?: number;
    returned_sample_count?: number;
    sampling?: { mode?: string };
    columns: Record<string, number[]>;
  },
  mode: PlaybackMode,
): void {
  if (mode !== 'full-rate-benchmark') return;
  const rows = telemetry.columns.time_s?.length;
  if (
    telemetry.sampling?.mode !== mode ||
    !rows ||
    rows > benchmarkBounds.maxRows ||
    rows !== telemetry.full_sample_count ||
    rows !== telemetry.returned_sample_count ||
    Object.keys(telemetry.columns).length > benchmarkBounds.maxReturnedChannels ||
    !Object.values(telemetry.columns).every((values) => values.length === rows)
  )
    throw new Error(
      'Full-rate benchmark response is incomplete, decimated or exceeds its declared row/channel bounds. No actor is attached.',
    );
}
export function browserHeap(
  source: unknown,
): { used: number; total: number; limit: number } | null {
  const memory = (
    source as {
      memory?: { usedJSHeapSize?: number; totalJSHeapSize?: number; jsHeapSizeLimit?: number };
    } | null
  )?.memory;
  if (
    !memory ||
    ![memory.usedJSHeapSize, memory.totalJSHeapSize, memory.jsHeapSizeLimit].every(
      (value) => typeof value === 'number' && Number.isFinite(value) && value >= 0,
    )
  )
    return null;
  return {
    used: memory.usedJSHeapSize!,
    total: memory.totalJSHeapSize!,
    limit: memory.jsHeapSizeLimit!,
  };
}
