export const VP1_ID = 'RP1-VP1-inspection-preview-v1';
export const VP1_PACKAGE_ID = 'RP1-VP1-plywood-validation-package-v1';
export const VP1_PACKAGE_SHA256 =
  '3bc7ef7a01d20599faec2fb7ad8ca6c225243f273fedf9dcc870aa1d2d98eff8';
export const VP1_CONFIG_ID = 'G80-F2-RP1-AD1-definition-v2';
export const VP1_CONFIG_SHA256 = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
export const VP1_PROTOCOL_SHA256 =
  '7941ee02b27255c760cbb9d59002452821596e3e30c86835e7b0ad805e31a2ac';
export const VP1_STAGE_IDS = ['S0', 'S1', 'S2a', 'S2b'] as const;
export interface Vp1Source {
  path: string;
  sha256: string;
}
export interface Vp1Stage {
  id: string;
  label: string;
  status: 'not-authorized';
  scope: string;
  entry: string;
  decision: string;
  part_ids: string[];
}
export interface Vp1Part {
  id: string;
  label: string;
  note: string;
  status: 'unverified';
}
export interface Vp1Message {
  id: string;
  label: string;
  recipient: string;
  channel: string;
  text: string;
  source: Vp1Source;
}
export interface Vp1Snapshot {
  schema_version: 1;
  id: string;
  package: Vp1Source & { id: string };
  configuration: { id: string; sha256: string };
  protocol: Vp1Source;
  status: string;
  approvals: {
    supplier_contact: false;
    purchases: false;
    physical_work: false;
    paid_service: false;
  };
  currency: 'USD';
  price_snapshot_date: string;
  costs: {
    room_materials_usd: string | null;
    full_materials_usd: string | null;
    all_in_usd: null;
    note: string;
  };
  limits: {
    fin_force_N: number;
    fin_moment_Nm: number;
    design_factor_already_applied: number;
    tip_limit_mm: number;
  };
  stages: Vp1Stage[];
  parts: Vp1Part[];
  links: { stage_id: string; part_id: string; label: string }[];
  messages: Vp1Message[];
  materials: {
    id: string;
    sku: string;
    quantity: number;
    unit: string;
    unit_usd: number | string | null;
    basis: string;
    availability: string;
    source: string;
  }[];
  limitations: string[];
  sources: Vp1Source[];
}
const record = (v: unknown): v is Record<string, unknown> =>
  !!v && typeof v === 'object' && !Array.isArray(v);
const text = (v: unknown): v is string => typeof v === 'string' && !!v.trim();
const slug = (v: unknown): v is string => text(v) && /^[A-Za-z0-9_-]+$/.test(v);
const source = (v: unknown): boolean =>
  record(v) && text(v.path) && typeof v.sha256 === 'string' && /^[a-f0-9]{64}$/.test(v.sha256);
const money = (v: unknown): boolean =>
  v === null || (typeof v === 'string' && /^\d+\.\d{2}$/.test(v));
const strings = (v: unknown): v is string[] => Array.isArray(v) && v.every(text);
const unique = (rows: Record<string, unknown>[]) =>
  new Set(rows.map((row) => row.id)).size === rows.length;

/** This view admits only the frozen, unperformed package, never an approval or result. */
export function validateVp1Validation(value: unknown): Vp1Snapshot {
  const invalid = (): never => {
    throw new Error(
      'VP1 source is invalid or incompatible. Package revision, authorization state, costs or relationships could not be verified.',
    );
  };
  if (!record(value) || value.schema_version !== 1 || value.id !== VP1_ID || !text(value.status))
    return invalid();
  const pkg = value.package,
    config = value.configuration,
    protocol = value.protocol,
    approvals = value.approvals,
    costs = value.costs,
    limits = value.limits;
  if (
    !record(pkg) ||
    pkg.id !== VP1_PACKAGE_ID ||
    pkg.path !== 'configs/studies/rp1-validation-package.yaml' ||
    pkg.sha256 !== VP1_PACKAGE_SHA256 ||
    !record(config) ||
    config.id !== VP1_CONFIG_ID ||
    config.sha256 !== VP1_CONFIG_SHA256 ||
    !record(protocol) ||
    protocol.path !== 'docs/validation/rp1-vp1/protocol.md' ||
    protocol.sha256 !== VP1_PROTOCOL_SHA256 ||
    !record(approvals) ||
    ['supplier_contact', 'purchases', 'physical_work', 'paid_service'].some(
      (key) => approvals[key] !== false,
    ) ||
    value.currency !== 'USD' ||
    value.price_snapshot_date !== '2026-11-04' ||
    !record(costs) ||
    !money(costs.room_materials_usd) ||
    !money(costs.full_materials_usd) ||
    costs.all_in_usd !== null ||
    !text(costs.note) ||
    !record(limits) ||
    limits.fin_force_N !== 331.125 ||
    limits.fin_moment_Nm !== 8.83 ||
    limits.design_factor_already_applied !== 3 ||
    limits.tip_limit_mm !== 1
  )
    return invalid();
  const { stages, parts, links, messages, materials, sources, limitations } = value;
  if (
    !Array.isArray(stages) ||
    stages.length !== 4 ||
    !Array.isArray(parts) ||
    !parts.length ||
    !Array.isArray(links) ||
    !links.length ||
    !Array.isArray(messages) ||
    messages.length !== 5 ||
    !Array.isArray(materials) ||
    !materials.length ||
    !Array.isArray(sources) ||
    !sources.length ||
    !sources.every(source) ||
    !strings(limitations) ||
    !limitations.length
  )
    return invalid();
  if (
    !parts.every(
      (p) => record(p) && slug(p.id) && text(p.label) && text(p.note) && p.status === 'unverified',
    ) ||
    !unique(parts)
  )
    return invalid();
  const partIds = new Set(parts.map((p) => p.id));
  if (
    !stages.every(
      (s) =>
        record(s) &&
        text(s.id) &&
        VP1_STAGE_IDS.includes(s.id as (typeof VP1_STAGE_IDS)[number]) &&
        text(s.label) &&
        s.status === 'not-authorized' &&
        text(s.scope) &&
        text(s.entry) &&
        text(s.decision) &&
        strings(s.part_ids) &&
        new Set(s.part_ids).size === s.part_ids.length &&
        s.part_ids.every((id) => partIds.has(id)),
    ) ||
    !unique(stages)
  )
    return invalid();
  if (
    !links.every(
      (l) =>
        record(l) &&
        text(l.label) &&
        partIds.has(l.part_id) &&
        stages.some((s) => s.id === l.stage_id && s.part_ids.includes(l.part_id)),
    ) ||
    new Set(links.map((l) => `${l.stage_id}:${l.part_id}`)).size !== links.length ||
    stages.some((s) =>
      s.part_ids.some((id: string) => !links.some((l) => l.stage_id === s.id && l.part_id === id)),
    )
  )
    return invalid();
  if (
    !messages.every(
      (m) =>
        record(m) &&
        slug(m.id) &&
        text(m.label) &&
        text(m.recipient) &&
        text(m.channel) &&
        text(m.text) &&
        source(m.source),
    ) ||
    !unique(messages)
  )
    return invalid();
  if (
    !materials.every(
      (m) =>
        record(m) &&
        slug(m.id) &&
        text(m.sku) &&
        typeof m.quantity === 'number' &&
        Number.isInteger(m.quantity) &&
        m.quantity > 0 &&
        text(m.unit) &&
        (money(m.unit_usd) ||
          (typeof m.unit_usd === 'number' && Number.isFinite(m.unit_usd) && m.unit_usd >= 0)) &&
        text(m.basis) &&
        text(m.availability) &&
        text(m.source) &&
        /^https:\/\//.test(m.source),
    ) ||
    !unique(materials)
  )
    return invalid();
  return value as unknown as Vp1Snapshot;
}

export async function loadVp1Validation(signal: AbortSignal, request: typeof fetch = fetch) {
  const response = await request('/engineering-workbench/rp1-validation.json', {
    signal,
    headers: { Accept: 'application/json' },
  });
  if (!response.ok)
    throw new Error(`Prepared VP1 package unavailable: ${response.status} ${response.statusText}`);
  return validateVp1Validation(await response.json());
}

export function vp1Money(value: string | number | null): string {
  return value === null
    ? 'Unavailable'
    : `$${typeof value === 'number' ? value.toFixed(2) : value} USD`;
}

/** Encodes the source text verbatim; the link downloads locally and has no recipient action. */
export function vp1DraftDownload(message: Vp1Message) {
  return {
    href: `data:text/plain;charset=utf-8,${encodeURIComponent(message.text)}`,
    filename: `${message.id}-UNSENT.txt`,
  };
}
