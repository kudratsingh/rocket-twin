/** Capture one measured frame interval before React may defer a state updater. */
export function playbackStep(
  elapsedMs: number,
  speed: number,
  end: number,
): (time: number) => number {
  const advanceSeconds = (elapsedMs / 1000) * speed;
  return (time: number) => Math.min(end, time + advanceSeconds);
}
