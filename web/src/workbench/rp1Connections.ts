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
// The exact recorded route membership and source fingerprints are pinned separately
// from the broad connection-document shape validator. A changed payload cannot add
// an apparently valid relationship to an otherwise correctly named AD1 record.
const RECORDED_CONNECTIONS = [
  {
    id: 'fin-root',
    label: 'Fin root and body',
    partIds: [
      'fin_set',
      'fin_tabs',
      'outer_fin_fillets',
      'root_gussets',
      'root_extra_bond_finish',
      'fin_internal_bonds',
      'motor_tube',
      'ring_bonds',
      'aft_ring',
      'body',
      'forward_ring',
    ],
  },
  {
    id: 'recovery',
    label: 'Recovery leader and load path',
    partIds: [
      'parachute',
      'recovery_connectors',
      'shock_cord',
      'rp1_kevlar_wrap',
      'forward_ring',
      'rp1_notch_sealer',
      'ad1_cord_sleeve',
      'motor_tube',
      'ring_bonds',
      'body',
      'upper_body',
      'nose_recovery_eye',
      'nose_anchor_plate',
    ],
  },
] as const;
const RECORDED_SOURCES = [
  ['spec', 'configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml', RP1_CONNECTIONS_SHA256],
  [
    'definition',
    'configs/studies/rp1-attachment-definition-v2.yaml',
    'e9db49f2cafc89b1f77bf9d7396434297bc8bb8754085fdcf74d3b0242012555',
  ],
  [
    'ad1-record',
    'runs/wo03-rp1-attachment-definition-20261103-v2/record.json',
    'bc349a24fe1cfaa4d883b9e00dc5b75387638a7be5cd4b05d9f32112ee8bd95b',
  ],
  [
    'd1-record',
    'runs/wo03-rp1-d1-20261104-v1/record.json',
    '7bd208322dc8d866b56e4422d369d06d1a06b8966b7cc614a22c086bef1aa6a4',
  ],
  [
    'ad1-decision',
    'docs/wo03-rp1-attachment-definition.md',
    '012cd168e03807460debd5bb9dbc543f058d02597f87bd83945a769794a1aa4a',
  ],
  [
    'd1-decision',
    'docs/wo03-rp1-load-attachment-decision.md',
    'af6eabd641063d262d0190ee46f5bbc847e54af5c7a3a1f1c442f0a57740bb47',
  ],
  [
    'drawing-manifest',
    'output/rp1-attachment-definition/manifest.json',
    '948d26808de0290e210aec28e03cc29a31d3c84cd65a8d73635c3973e935b8d7',
  ],
] as const;
const RECORDED_STATUS =
  'Source-linked unadopted concepts; no physical qualification or flight release';

export function exactRp1EvidenceRouteSource(document: Rp1ConnectionsDocument): boolean {
  return (
    document.status === RECORDED_STATUS &&
    document.sources.length === RECORDED_SOURCES.length &&
    RECORDED_SOURCES.every(
      ([id, path, sha256], index) =>
        document.sources[index].id === id &&
        document.sources[index].path === path &&
        document.sources[index].sha256 === sha256,
    ) &&
    document.connections.length === RECORDED_CONNECTIONS.length &&
    RECORDED_CONNECTIONS.every(
      (expected, index) =>
        document.connections[index].id === expected.id &&
        document.connections[index].label === expected.label &&
        JSON.stringify(document.connections[index].part_ids) === JSON.stringify(expected.partIds),
    )
  );
}

export function rp1ConnectionDesignHref(
  partId: string,
  context?: { connectionId: string; document: Rp1ConnectionsDocument },
) {
  if (!(RP1_CONNECTION_PART_IDS as readonly string[]).includes(partId))
    throw new Error('Design link unavailable: part is not in the frozen AD1 source.');
  if (context) {
    const document = validateRp1Connections(context.document);
    if (!exactRp1EvidenceRouteSource(document))
      throw new Error('Design link unavailable: source fingerprints or route membership changed.');
    const connection = document.connections.find((item) => item.id === context.connectionId);
    if (!connection?.part_ids.includes(partId))
      throw new Error('Design link unavailable: connection does not contain this source part.');
  }
  const params = new URLSearchParams({
    workspace: 'design',
    design: RP1_CONNECTIONS_CONFIGURATION,
    part: partId,
    spec: RP1_CONNECTIONS_SHA256,
  });
  if (context) params.set('connection', context.connectionId);
  return `/?${params}`;
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
