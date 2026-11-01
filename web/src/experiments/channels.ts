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
