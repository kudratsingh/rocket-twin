/** App-owned preparation timings, never GPU/browser FPS or scientific acceptance. */
export type ReplayWorkTiming = { phase: string; elapsed_ms: number; scope: string };
export function measureReplayWork<T>(
  phase: string,
  work: () => T,
): { value: T; timing: ReplayWorkTiming } {
  const started = performance.now();
  const value = work();
  return {
    value,
    timing: {
      phase,
      elapsed_ms: performance.now() - started,
      scope:
        'Synchronous JavaScript data preparation only; excludes browser layout/paint, GPU and frame completion',
    },
  };
}
