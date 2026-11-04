export const RP1_COMPARISON_ID = 'G80-F2-RP1-FP1-FR1-comparison-v1';
export const RP1_SOURCE_ID = 'G80-F2-RP1-AD1-definition-v2';
export const RP1_SOURCE_SHA256 = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
export const RP1_STUDY_IDS = [
  'G80-F2-RP1-FP1-carbon-faced-plywood-screen-v1',
  'RP1-FR1-monolithic-carbon-v1',
] as const;
export interface Rp1Study {
  id: string;
  label: string;
  status: string;
  adopted: false;
  installed_accepted: false;
  source: { path: string; sha256: string };
  maturity: string;
  displacement: {
    reported_mm: number | null;
    attachment_budget_mm: number | null;
    limit_mm: number;
    note: string;
  };
  mass: { conditional_credit_g: number | null; note: string };
  nodes: { id: string; label: string; note: string; status: string }[];
  edges: { from: string; to: string; label: string }[];
  unknowns: string[];
  sources: { path: string; sha256?: string }[];
}
export interface Rp1Studies {
  schema_version: 1;
  id: string;
  status: string;
  source_configuration: { id: string; path: string; sha256: string };
  load_definition: {
    required_moment_Nm: number;
    proposed_moment_Nm: number;
    proposal_adopted: false;
    note: string;
  };
  studies: Rp1Study[];
}
const record = (v: unknown): v is Record<string, unknown> =>
  !!v && typeof v === 'object' && !Array.isArray(v);
const text = (v: unknown): v is string => typeof v === 'string' && !!v.trim();
const hash = (v: unknown) => typeof v === 'string' && /^[a-f0-9]{64}$/i.test(v);
const number = (v: unknown) => typeof v === 'number' && Number.isFinite(v) && v >= 0;
const nullable = (v: unknown) => v === null || number(v);

/** Fail closed on incomplete records, unknown acceptance, missing identity or graph endpoints. */
export function validateRp1Studies(value: unknown): Rp1Studies {
  const invalid = () => {
    throw new Error(
      'RP1 studies source is invalid or incompatible: identity, unaccepted status, quantities or graph endpoints are missing.',
    );
  };
  if (
    !record(value) ||
    value.schema_version !== 1 ||
    value.id !== RP1_COMPARISON_ID ||
    !text(value.status)
  )
    return invalid();
  const configuration = value.source_configuration;
  const load = value.load_definition;
  if (
    !record(configuration) ||
    configuration.id !== RP1_SOURCE_ID ||
    configuration.path !== 'configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml' ||
    configuration.sha256 !== RP1_SOURCE_SHA256 ||
    !record(load) ||
    load.required_moment_Nm !== 8.83 ||
    !number(load.proposed_moment_Nm) ||
    load.proposal_adopted !== false ||
    !text(load.note) ||
    !Array.isArray(value.studies)
  )
    return invalid();
  const ids = new Set<string>();
  for (const s of value.studies) {
    if (
      !record(s) ||
      !text(s.id) ||
      ids.has(s.id) ||
      !text(s.label) ||
      !text(s.status) ||
      !text(s.maturity) ||
      s.adopted !== false ||
      s.installed_accepted !== false ||
      !record(s.source) ||
      !text(s.source.path) ||
      !hash(s.source.sha256)
    )
      return invalid();
    ids.add(s.id);
    if (
      !record(s.displacement) ||
      !nullable(s.displacement.reported_mm) ||
      !nullable(s.displacement.attachment_budget_mm) ||
      s.displacement.limit_mm !== 1 ||
      !text(s.displacement.note) ||
      !record(s.mass) ||
      !nullable(s.mass.conditional_credit_g) ||
      !text(s.mass.note) ||
      !Array.isArray(s.unknowns) ||
      !s.unknowns.every(text) ||
      !Array.isArray(s.nodes) ||
      !Array.isArray(s.edges) ||
      !Array.isArray(s.sources)
    )
      return invalid();
    if (s.id === RP1_STUDY_IDS[0] && s.displacement.attachment_budget_mm !== 0.1) return invalid();
    const nodes = new Set<string>();
    for (const n of s.nodes) {
      if (
        !record(n) ||
        !text(n.id) ||
        nodes.has(n.id) ||
        !text(n.label) ||
        !text(n.note) ||
        !text(n.status)
      )
        return invalid();
      nodes.add(n.id);
    }
    if (
      !s.edges.every(
        (e) =>
          record(e) &&
          typeof e.from === 'string' &&
          typeof e.to === 'string' &&
          nodes.has(e.from) &&
          nodes.has(e.to) &&
          e.from !== e.to &&
          text(e.label),
      )
    )
      return invalid();
    if (
      !s.sources.every(
        (source) =>
          record(source) &&
          text(source.path) &&
          (source.sha256 === undefined || hash(source.sha256)),
      )
    )
      return invalid();
  }
  if (ids.size && (ids.size !== RP1_STUDY_IDS.length || RP1_STUDY_IDS.some((id) => !ids.has(id))))
    return invalid();
  return value as unknown as Rp1Studies;
}

export async function loadRp1Studies(signal: AbortSignal, request: typeof fetch = fetch) {
  const response = await request('/engineering-workbench/rp1-studies.json', {
    signal,
    headers: { Accept: 'application/json' },
  });
  if (!response.ok)
    throw new Error(`Prepared RP1 studies unavailable: ${response.status} ${response.statusText}`);
  return validateRp1Studies(await response.json());
}

export function rp1Quantity(value: number | null, unit: string): string {
  return value === null || !Number.isFinite(value) ? 'Unavailable' : `${value.toFixed(3)} ${unit}`;
}
