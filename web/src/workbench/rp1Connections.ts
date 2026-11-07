import { loadRecordedSource } from './workbenchRouting.ts';
export const RP1_CONNECTIONS_ID = 'RP1-AD1-connections-v1';
export const RP1_CONNECTIONS_CONFIGURATION = 'G80-F2-RP1-AD1-definition-v2';
export const RP1_CONNECTIONS_SHA256 =
  '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
export const RP1_CONNECTION_PART_IDS = [
  'nose',
  'body',
  'fin_set',
  'fin_tabs',
  'motor_tube',
  'forward_ring',
  'aft_ring',
  'fin_internal_bonds',
  'ring_bonds',
  'outer_fin_fillets',
  'motor',
  'motor_retainer',
  'retainer_adhesive',
  'mount_external_shield',
  'nose_anchor_plate',
  'nose_recovery_eye',
  'shock_cord',
  'recovery_connectors',
  'parachute',
  'recovery_protection',
  'flight_computer',
  'imu',
  'baro',
  'high_g_accel',
  'micro_sd',
  'battery',
  'independent_recovery',
  'recovery_battery',
  'avionics_sled',
  'logger_power_switch',
  'logger_regulator',
  'recovery_carrier',
  'electrical_harness',
  'recovery_harness_wiring',
  'recovery_output_mount',
  'rail_buttons',
  'rail_backers',
  'finish',
  'service_allowance',
  'upper_body',
  'body_splice',
  'splice_seam_patch',
  'splice_adhesive',
  'root_gussets',
  'root_extra_bond_finish',
  'nose_service_hardware',
  'c1_forward_root_bond_fill',
  'c1_aft_bond_fill',
  'c1_nose_bond_fill',
  'rp1_kevlar_wrap',
  'rp1_wrap_lock_bond',
  'rp1_notch_sealer',
  'rp1_lip_guard',
  'ad1_cord_sleeve',
  'ad1_slot_fill',
] as const;
export const RP1_DRAWING_HASHES: Record<string, string> = {
  '01-local-attachment': 'cf1569a1044c48c5465189bb03666f7af00d143ef9f8e307ce9a33e9450c2af7',
  '02-load-paths': '07ed71f1889fb0f851487b66617c79b65cb25f05d0795097fc3254e7c3770afa',
  '03-test-article': '74c82a34bf60396fa9105c65081afed74e7eaa496c7d7e2f78b1e3be56daaeef',
  '04-coupled-cases': 'ec837f0342953a33b2db73f9082ba4577bacee3581ca94c6173f39dbb87a4b80',
};
export interface Rp1ConnectionSource {
  id: string;
  path: string;
  sha256: string;
}
export interface Rp1ConnectionDrawing {
  id: string;
  label: string;
  path: string;
  sha256: string;
  status: string;
}
export interface Rp1ConnectionNode {
  id: string;
  label: string;
  part_ids: string[];
  note: string;
}
export interface Rp1Connection {
  id: 'fin-root' | 'recovery';
  label: string;
  summary: string;
  part_ids: string[];
  nodes: Rp1ConnectionNode[];
  edges: { id: string; from: string; to: string; label: string; note: string }[];
  dimensions: {
    id: string;
    label: string;
    value: number | string | number[] | null;
    unit: string;
    source_id: string;
    note: string;
  }[];
  findings: {
    id: string;
    label: string;
    status: 'failed-screen' | 'unknown' | 'requirement';
    detail: string;
    source_id: string;
    measurement_needed: string;
  }[];
  drawing_ids: string[];
}
export interface Rp1ConnectionsDocument {
  schema_version: 1;
  id: string;
  configuration: { id: string; path: string; sha256: string };
  status: string;
  part_ids: string[];
  sources: Rp1ConnectionSource[];
  drawings: Rp1ConnectionDrawing[];
  connections: Rp1Connection[];
}
const record = (v: unknown): v is Record<string, unknown> =>
  !!v && typeof v === 'object' && !Array.isArray(v);
const text = (v: unknown): v is string => typeof v === 'string' && !!v.trim();
const slug = (v: unknown): v is string => text(v) && /^[a-zA-Z0-9_-]+$/.test(v);
const strings = (v: unknown): v is string[] =>
  Array.isArray(v) && v.every(text) && new Set(v).size === v.length;
const hash = (v: unknown) => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
const quantity = (v: unknown): boolean =>
  v === null ||
  text(v) ||
  (typeof v === 'number' && Number.isFinite(v)) ||
  (Array.isArray(v) && v.length > 0 && v.every((n) => typeof n === 'number' && Number.isFinite(n)));
const unique = (rows: unknown[]) =>
  rows.every(record) &&
  new Set(rows.map((row) => (row as Record<string, unknown>).id)).size === rows.length;

/** Only the frozen AD1 concept is admitted. No foreign geometry or inferred relation is substituted. */
export function validateRp1Connections(value: unknown): Rp1ConnectionsDocument {
  const invalid = (reason: string): never => {
    throw new Error(
      `RP1 connections unavailable: invalid or incompatible ${reason}. No historical source is substituted.`,
    );
  };
  if (
    !record(value) ||
    value.schema_version !== 1 ||
    value.id !== RP1_CONNECTIONS_ID ||
    !text(value.status)
  )
    return invalid('document');
  const config = value.configuration;
  if (
    !record(config) ||
    config.id !== RP1_CONNECTIONS_CONFIGURATION ||
    config.path !== 'configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml' ||
    config.sha256 !== RP1_CONNECTIONS_SHA256
  )
    return invalid('configuration identity');
  if (
    !strings(value.part_ids) ||
    value.part_ids.length !== RP1_CONNECTION_PART_IDS.length ||
    RP1_CONNECTION_PART_IDS.some((id) => !(value.part_ids as string[]).includes(id))
  )
    return invalid('55-part source membership');
  const partIds = new Set(value.part_ids);
  if (
    !Array.isArray(value.sources) ||
    !value.sources.length ||
    !value.sources.every((s) => record(s) && slug(s.id) && text(s.path) && hash(s.sha256)) ||
    !unique(value.sources)
  )
    return invalid('source fingerprints');
  const sourceIds = new Set(value.sources.map((s) => s.id));
  if (
    !Array.isArray(value.drawings) ||
    !value.drawings.every(
      (d) =>
        record(d) &&
        text(d.id) &&
        Object.hasOwn(RP1_DRAWING_HASHES, d.id) &&
        d.path === `output/rp1-attachment-definition/${d.id}.svg` &&
        d.sha256 === RP1_DRAWING_HASHES[d.id] &&
        text(d.label) &&
        text(d.status),
    ) ||
    !unique(value.drawings)
  )
    return invalid('saved drawing identity');
  if (
    !Array.isArray(value.connections) ||
    value.connections.length !== 2 ||
    !unique(value.connections)
  )
    return invalid('connection set');
  for (const c of value.connections) {
    if (
      !record(c) ||
      !['fin-root', 'recovery'].includes(String(c.id)) ||
      !text(c.label) ||
      !text(c.summary) ||
      !strings(c.part_ids) ||
      !c.part_ids.length ||
      !c.part_ids.every((id) => partIds.has(id)) ||
      !Array.isArray(c.nodes) ||
      !c.nodes.length ||
      !Array.isArray(c.edges) ||
      !Array.isArray(c.dimensions) ||
      !c.dimensions.length ||
      !Array.isArray(c.findings) ||
      !c.findings.length ||
      !strings(c.drawing_ids) ||
      !c.drawing_ids.every((id) => Object.hasOwn(RP1_DRAWING_HASHES, id))
    )
      return invalid('connection records');
    const connectionParts = new Set(c.part_ids);
    if (
      !c.nodes.every(
        (n) =>
          record(n) &&
          slug(n.id) &&
          text(n.label) &&
          text(n.note) &&
          strings(n.part_ids) &&
          n.part_ids.every((id) => connectionParts.has(id)),
      ) ||
      !unique(c.nodes)
    )
      return invalid('diagram node membership');
    const nodeIds = new Set(c.nodes.map((n) => n.id));
    const nodes = c.nodes as Rp1ConnectionNode[];
    if (!c.part_ids.every((id) => nodes.some((n) => n.part_ids.includes(id))))
      return invalid('unmapped connection part');
    if (
      !c.edges.every(
        (e) =>
          record(e) &&
          slug(e.id) &&
          nodeIds.has(e.from) &&
          nodeIds.has(e.to) &&
          e.from !== e.to &&
          text(e.label) &&
          text(e.note),
      ) ||
      !unique(c.edges)
    )
      return invalid('diagram edge');
    if (
      !c.dimensions.every(
        (d) =>
          record(d) &&
          slug(d.id) &&
          text(d.label) &&
          quantity(d.value) &&
          typeof d.unit === 'string' &&
          sourceIds.has(d.source_id) &&
          text(d.note),
      ) ||
      !unique(c.dimensions)
    )
      return invalid('recorded dimensions');
    if (
      !c.findings.every(
        (f) =>
          record(f) &&
          slug(f.id) &&
          text(f.label) &&
          ['failed-screen', 'unknown', 'requirement'].includes(String(f.status)) &&
          text(f.detail) &&
          sourceIds.has(f.source_id) &&
          text(f.measurement_needed),
      ) ||
      !unique(c.findings)
    )
      return invalid('finding evidence');
  }
  return value as unknown as Rp1ConnectionsDocument;
}
export async function loadRp1Connections(signal: AbortSignal, request: typeof fetch = fetch) {
  const { value } = await loadRecordedSource(
    '/api/engineering/rp1-connections',
    '/engineering-workbench/rp1-connections.json',
    signal,
    request,
  );
  return validateRp1Connections(value);
}
export function rp1ConnectionDesignHref(partId: string) {
  if (!(RP1_CONNECTION_PART_IDS as readonly string[]).includes(partId))
    throw new Error('Design link unavailable: part is not in the frozen AD1 source.');
  return `/?${new URLSearchParams({ workspace: 'design', design: RP1_CONNECTIONS_CONFIGURATION, part: partId, spec: RP1_CONNECTIONS_SHA256 })}`;
}
export function rp1ConnectionDrawingHref(drawing: Rp1ConnectionDrawing) {
  if (
    !Object.hasOwn(RP1_DRAWING_HASHES, drawing.id) ||
    drawing.sha256 !== RP1_DRAWING_HASHES[drawing.id] ||
    drawing.path !== `output/rp1-attachment-definition/${drawing.id}.svg`
  )
    throw new Error('Saved drawing unavailable: revision mismatch.');
  return `/api/engineering/rp1-connections/drawings/${encodeURIComponent(drawing.id)}?${new URLSearchParams({ spec: RP1_CONNECTIONS_SHA256, sha256: drawing.sha256 })}`;
}
export function rp1ConnectionQuantity(
  value: Rp1Connection['dimensions'][number]['value'],
  unit: string,
): string {
  if (value === null) return 'Unavailable';
  return `${Array.isArray(value) ? `[${value.join(', ')}]` : value}${unit ? ` ${unit}` : ''}${Array.isArray(value) ? ' (source order)' : ''}`;
}
