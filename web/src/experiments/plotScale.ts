/** Display bounds use only the plotted samples; this does not change telemetry. */
export function plotScale(values: number[]): { min: number; max: number } {
  let min = Infinity;
  let max = -Infinity;
  for (const value of values) {
    min = Math.min(min, value);
    max = Math.max(max, value);
  }
  if (min === max) {
    const padding = Math.abs(min) * 0.05 || 0.001;
    return { min: min - padding, max: max + padding };
  }
  return { min, max };
}

/** Keep distinct bounds distinct in the labels, including small recorded changes. */
export function scaleLabels(min: number, max: number): [string, string] {
  for (let precision = 4; precision <= 17; precision++) {
    const low = Number(min.toPrecision(precision)).toString();
    const high = Number(max.toPrecision(precision)).toString();
    if (low !== high) return [low, high];
  }
  return [min.toString(), max.toString()];
}
