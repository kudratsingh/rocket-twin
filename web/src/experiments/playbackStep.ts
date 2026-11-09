/** Capture one measured frame interval before React may defer a state updater. */
export function playbackStep(
  elapsedMs: number,
  speed: number,
  end: number,
): (time: number) => number {
  if (
    !Number.isFinite(elapsedMs) ||
    elapsedMs <= 0 ||
    !Number.isFinite(speed) ||
    speed <= 0 ||
    !Number.isFinite(end)
  )
    return (time: number) => time;
  const advanceSeconds = (elapsedMs / 1000) * speed;
  return (time: number) => Math.min(end, time + advanceSeconds);
}
