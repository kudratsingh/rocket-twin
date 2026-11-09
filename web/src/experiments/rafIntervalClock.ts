/** Measure playback intervals only between observed RAF timestamps. */
export function createRafIntervalClock() {
  let priorRaf: number | null = null;
  return {
    sample(now: number): number | null {
      if (!Number.isFinite(now)) return NaN;
      if (priorRaf === null) {
        priorRaf = now;
        return null;
      }
      const delta = now - priorRaf;
      // Preserve the last valid anchor after a zero/backward timestamp. The bad
      // interval still reaches the recorder and cannot be filtered into a pass.
      if (Number.isFinite(delta) && delta > 0) priorRaf = now;
      return delta;
    },
    reset() {
      priorRaf = null;
    },
  };
}
