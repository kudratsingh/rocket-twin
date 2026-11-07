/** Bounded browser instrumentation. Synthetic checks never establish playback acceptance. */
export function frameProfile(deltas: readonly number[]) {
  const sorted = deltas
    .filter((value) => Number.isFinite(value) && value > 0)
    .slice(-600)
    .sort((a, b) => a - b);
  if (!sorted.length) return null;
  const percentile = (p: number) =>
    sorted[Math.min(sorted.length - 1, Math.ceil(sorted.length * p) - 1)];
  return {
    samples: sorted.length,
    p50_ms: percentile(0.5),
    p95_ms: percentile(0.95),
    max_ms: sorted.at(-1)!,
    mean_ms: sorted.reduce((sum, value) => sum + value, 0) / sorted.length,
  };
}
export function filterRuns<
  T extends { run_id: string; configuration: string; status: string; batch_id?: string | null },
>(runs: readonly T[], query: string, status: string): T[] {
  const needle = query.trim().toLowerCase();
  return runs.filter(
    (run) =>
      (status === 'all' || run.status === status) &&
      `${run.run_id} ${run.configuration} ${run.batch_id ?? ''}`.toLowerCase().includes(needle),
  );
}
