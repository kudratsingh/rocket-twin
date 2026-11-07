type ComparableRun = {
  configuration?: string;
  random_seed?: number;
  controller?: string;
  settings?: Record<string, unknown>;
  case?: Record<string, number | boolean | null | undefined>;
  code_sha256?: string;
  resolved_sha256?: string;
  cad_revision_sha256?: string;
  input_sha256?: Record<string, string | null | undefined>;
};

type Row = [string, unknown, unknown];

function missing(value: unknown) {
  return value == null || (typeof value === 'string' && !value.trim());
}

export function comparisonValue(value: unknown): string {
  return missing(value) ? 'unavailable' : String(value);
}

function objectRows(
  label: string,
  a: Record<string, unknown> | undefined,
  b: Record<string, unknown> | undefined,
  required: string[] = [],
): Row[] {
  const keys = [...new Set([...required, ...Object.keys(a ?? {}), ...Object.keys(b ?? {})])].sort();
  if (!keys.length) return [[label, undefined, undefined]];
  return keys.map((key) => [`${label}: ${key}`, a?.[key], b?.[key]]);
}

/** Missing evidence is a difference even when both records omit it. */
export function comparisonDifferences(a: ComparableRun, b: ComparableRun): Row[] {
  const rows: Row[] = [
    ['Configuration', a.configuration, b.configuration],
    ...(a.random_seed !== undefined || b.random_seed !== undefined
      ? [['Recorded random seed', a.random_seed, b.random_seed] as Row]
      : []),
    ...(a.controller !== undefined || b.controller !== undefined
      ? [['Controller', a.controller, b.controller] as Row]
      : []),
    ...objectRows('setting', a.settings, b.settings, [
      'wind_mps',
      'wind_direction_deg',
      'gust_mps',
    ]),
    ...objectRows('case', a.case, b.case),
    ['Simulation code SHA-256', a.code_sha256, b.code_sha256],
    ['Resolved specification SHA-256', a.resolved_sha256, b.resolved_sha256],
    ['CAD generator SHA-256', a.cad_revision_sha256, b.cad_revision_sha256],
    ...objectRows('input', a.input_sha256, b.input_sha256),
  ];
  return rows.filter(([, left, right]) => left !== right || missing(left) || missing(right));
}
