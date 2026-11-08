/** Validate a requested display-clock cursor without rounding it to the slider step. */
export function exactReplayTime(
  draft: string,
  start: number,
  end: number,
): { ok: true; time: number } | { ok: false; reason: string } {
  if (!Number.isFinite(start) || !Number.isFinite(end) || end < start)
    return { ok: false, reason: 'Recorded replay window is unavailable.' };
  if (!draft.trim()) return { ok: false, reason: 'Enter a finite time in seconds.' };
  const time = Number(draft);
  if (!Number.isFinite(time)) return { ok: false, reason: 'Enter a finite time in seconds.' };
  if (time < start || time > end)
    return {
      ok: false,
      reason: `Time must be inside the recorded replay window ${start}–${end} seconds (inclusive).`,
    };
  return { ok: true, time: Math.max(start, Math.min(end, time)) };
}
