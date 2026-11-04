/** Recorded columns plus backend-derived display columns; no flight physics is computed here. */
export const channelLabels: Record<string, string> = {
  height_m: 'Height above launch (m)',
  height_ft: 'Height above launch (ft)',
  speed_mps: 'Speed (m/s)',
  speed_mph: 'Speed (mph)',
  net_acceleration_mps2: 'Net acceleration (m/s²)',
  specific_force_mps2: 'Specific force (m/s²)',
  tilt_deg: 'Tilt from vertical (°)',
  downrange_m: 'Horizontal distance from launch (m)',
  downrange_ft: 'Horizontal distance from launch (ft)',
};

export const defaultChannels = ['height_m', 'speed_mps', 'net_acceleration_mps2', 'tilt_deg'];

export function channelOptions(a: Record<string, number[]>, b?: Record<string, number[]>) {
  return [...new Set([...Object.keys(a), ...Object.keys(b ?? {})])]
    .filter((name) => name !== 'time_s')
    .sort((left, right) => label(left).localeCompare(label(right)));
}

export function label(name: string) {
  // Unknown columns retain their exact schema name; do not guess their meaning or units.
  return channelLabels[name] ?? name;
}

export function series(columns: Record<string, number[]>, name: string): number[] | null {
  const values = columns[name];
  return Array.isArray(values) &&
    values.length === columns.time_s.length &&
    values.length > 0 &&
    values.every(Number.isFinite)
    ? values
    : null;
}

export type ChannelMeta = {
  source: string;
  unit: string | null;
  description: string;
  semantic_id: string | null;
};

/** Describe the displayed series, never metadata from a run without a displayed series. */
export function displayedMetadata(
  hasA: boolean,
  hasB: boolean,
  metaA: ChannelMeta | undefined,
  metaB: ChannelMeta | undefined,
): { run: 'A' | 'B'; meta: ChannelMeta | undefined } | null {
  if (hasA) return { run: 'A', meta: metaA };
  if (hasB) return { run: 'B', meta: metaB };
  return null;
}

export function comparisonReason(
  a: ChannelMeta | undefined,
  b: ChannelMeta | undefined,
  codeA?: string,
  codeB?: string,
): string | null {
  if (!a || !b || !a.semantic_id || !b.semantic_id || !a.unit || !b.unit)
    return 'Channel meaning or units are unavailable; comparison is withheld.';
  if (a.semantic_id !== b.semantic_id || a.unit !== b.unit || a.source !== b.source)
    return 'Channel semantics, units or source differ; comparison is withheld.';
  if (!codeA || !codeB || codeA !== codeB)
    return 'Simulation code identities differ or are unavailable; comparison is withheld.';
  return null;
}

export type SampleSeries = { times: number[]; values: number[] };

/** Validate the playback time axis once; missing values stay attached to their sample. */
export function prepareSamples(
  columns: Record<string, number[]>,
  name: string,
): SampleSeries | null {
  const times = columns.time_s;
  const values = columns[name];
  if (
    !Array.isArray(times) ||
    !Array.isArray(values) ||
    times.length === 0 ||
    values.length !== times.length ||
    !times.every((time, index) => Number.isFinite(time) && (index === 0 || time > times[index - 1]))
  )
    return null;
  return { times, values };
}

/** Return an actual nearest sample; never interpolate or extrapolate past recorded coverage. */
export function nearestSample(
  samples: SampleSeries | null,
  time: number,
): { time: number; value: number | null } | null {
  if (!samples || !Number.isFinite(time)) return null;
  const { times, values } = samples;
  if (time < times[0] || time > times[times.length - 1]) return null;
  let low = 0;
  let high = times.length - 1;
  while (low < high) {
    const mid = Math.floor((low + high) / 2);
    if (times[mid] < time) low = mid + 1;
    else high = mid;
  }
  const index = low > 0 && time - times[low - 1] <= times[low] - time ? low - 1 : low;
  return { time: times[index], value: Number.isFinite(values[index]) ? values[index] : null };
}
