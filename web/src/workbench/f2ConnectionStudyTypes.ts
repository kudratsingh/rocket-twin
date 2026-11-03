export interface ConnectionPart {
  id: string;
  label: string;
  function: string;
  material: string;
  mass_g: number | null;
  z_mm: number | null;
  dimensions: Record<string, unknown>;
  parameters?: Record<string, unknown>;
  state: string;
  notes: string | string[];
}
export interface ConnectionCase {
  identity: string;
  variant: string;
  case: string;
  total_mass_kg: number | null;
  parts_mass_kg: number | null;
  growth_kg: number | null;
  extra_aft_kg: number | null;
  cg_m: number | null;
  margin_cal: number | null;
  burnout_cg_m?: number | null;
  burnout_margin_cal?: number | null;
  guide_mps: Record<string, number | null>;
  formal_mass_headroom_g: number | null;
  planning_mass_headroom_g: number | null;
  required_whole_mean_proxy_N: number | null;
  common_acceleration_partition_N: Record<string, number | null>;
  [key: string]: unknown;
}
export interface ConnectionFit {
  id: string;
  minimum_mm: number | null;
  nominal_mm: number | null;
  maximum_mm: number | null;
  criterion_mm: number | null;
  conditional_screen_pass: boolean;
  basis: string;
  measured: boolean;
  environmental_bounds_verified: boolean;
}
export interface ConnectionNode {
  id: string;
  part_ids: string[];
  label: string;
  note: string;
  state: string;
}
export interface ConnectionEdge {
  from: string;
  to: string;
  label: string;
  note: string;
  state: string;
}

/** Diagram coordinates only: topology is supplied by source edges, not inferred here. */
export function connectionGraphLayout(nodes: ConnectionNode[]) {
  const semantic: Record<string, { x: number; y: number }> = {
    harness: { x: 470, y: 130 },
    eyes: { x: 470, y: 310 },
    ring: { x: 470, y: 490 },
    nose: { x: 80, y: 310 },
    outer: { x: 80, y: 700 },
    inner: { x: 470, y: 700 },
    tabs: { x: 860, y: 700 },
    motor: { x: 470, y: 900 },
    fins: { x: 860, y: 900 },
  };
  const known =
    Object.keys(semantic).every((id) => nodes.some((node) => node.id === id)) &&
    nodes.every((node) => Object.hasOwn(semantic, node.id));
  return {
    height: known ? 1080 : 190 + Math.ceil(nodes.length / 3) * 180,
    positions: new Map(
      nodes.map((node, index) => [
        node.id,
        known
          ? semantic[node.id]
          : { x: 100 + (index % 3) * 380, y: 130 + Math.floor(index / 3) * 180 },
      ]),
    ),
  };
}

/** Ports and explicit arrowheads remain visible in native SVG renderers without markers. */
export function connectionEdgeDisplay(
  from: { x: number; y: number },
  to: { x: number; y: number },
) {
  const dx = to.x - from.x,
    dy = to.y - from.y;
  const horizontal = Math.abs(dx) > Math.abs(dy);
  const sign = horizontal ? Math.sign(dx) || 1 : Math.sign(dy) || 1;
  const start = horizontal
    ? [from.x + (sign > 0 ? 260 : 0), from.y + 47]
    : [from.x + 130, from.y + (sign > 0 ? 94 : 0)];
  const end = horizontal
    ? [to.x + (sign > 0 ? 0 : 260) - sign * 4, to.y + 47]
    : [to.x + 130, to.y + (sign > 0 ? 0 : 94) - sign * 4];
  const middle = horizontal ? (start[0] + end[0]) / 2 : (start[1] + end[1]) / 2;
  const path = horizontal
    ? `M${start[0]} ${start[1]} H${middle} V${end[1]} H${end[0]}`
    : `M${start[0]} ${start[1]} V${middle} H${end[0]} V${end[1]}`;
  const arrow = horizontal
    ? [
        [end[0], end[1]],
        [end[0] - sign * 12, end[1] - 6],
        [end[0] - sign * 12, end[1] + 6],
      ]
    : [
        [end[0], end[1]],
        [end[0] - 6, end[1] - sign * 12],
        [end[0] + 6, end[1] - sign * 12],
      ];
  return {
    path,
    arrow: arrow.map((point) => point.join(',')).join(' '),
    labelX: horizontal ? middle : (start[0] + end[0]) / 2,
    labelY: horizontal ? (start[1] + end[1]) / 2 : middle,
  };
}
export interface ConnectionFinding {
  id: string;
  label: string;
  state: string;
  note: string;
  part_ids: string[];
}
export interface F2ConnectionSnapshot {
  schema_version: '1.0.0' | 1;
  id: 'G80-F2-C1-fit-proposal-v2';
  status: string;
  identity: {
    candidate_id: 'G80-F2-C1';
    source_identity: string;
    specification_sha256: string;
    cad_revision: null;
  };
  sources: { id: string; path: string; sha256: string }[];
  parts: ConnectionPart[];
  cases: ConnectionCase[];
  fits: ConnectionFit[];
  audit: Record<string, unknown> & { source_variant: 'frozen_F2' };
  numerical: {
    completed_grids: number;
    required_grids: number;
    status: 'stopped_node_budget';
    fine_nodes: number;
    node_limit: number;
    installed_strength_accepted: false;
  };
  field_export: { active_compatible: false; three_grid_convergence: false; [key: string]: unknown };
  graph: { nodes: ConnectionNode[]; edges: ConnectionEdge[] };
  findings: ConnectionFinding[];
}
const object = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === 'object' && !Array.isArray(value);
const text = (value: unknown): value is string => typeof value === 'string' && value.length > 0;
const strings = (value: unknown): value is string[] => Array.isArray(value) && value.every(text);
const numberOrNull = (value: unknown) =>
  value === null || (typeof value === 'number' && Number.isFinite(value));
const finite = (value: unknown): value is number =>
  typeof value === 'number' && Number.isFinite(value);
function requireValue(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(`F2-C1 source incompatible: ${message}`);
}

/** This drawing admits only the named unadopted packet, never historical field geometry. */
export function validateF2ConnectionSnapshot(value: unknown): F2ConnectionSnapshot {
  requireValue(object(value), 'expected a record');
  requireValue(value.schema_version === '1.0.0' || value.schema_version === 1, 'schema version');
  requireValue(
    value.id === 'G80-F2-C1-fit-proposal-v2' && text(value.status),
    'proposal identity/status',
  );
  const identity = value.identity;
  requireValue(
    object(identity) &&
      identity.candidate_id === 'G80-F2-C1' &&
      identity.cad_revision === null &&
      text(identity.source_identity) &&
      text(identity.specification_sha256),
    'source identity or CAD association',
  );
  requireValue(
    Array.isArray(value.sources) &&
      value.sources.length > 0 &&
      value.sources.every((s) => object(s) && text(s.id) && text(s.path) && text(s.sha256)),
    'source records',
  );
  requireValue(
    Array.isArray(value.parts) &&
      value.parts.length > 0 &&
      value.parts.every(
        (p) =>
          object(p) &&
          text(p.id) &&
          text(p.label) &&
          text(p.function) &&
          text(p.material) &&
          numberOrNull(p.mass_g) &&
          numberOrNull(p.z_mm) &&
          object(p.dimensions) &&
          (p.parameters === undefined || object(p.parameters)) &&
          text(p.state) &&
          (typeof p.notes === 'string' || strings(p.notes)),
      ),
    'allocation rows',
  );
  const partIds = new Set(value.parts.map((p) => p.id));
  requireValue(partIds.size === value.parts.length, 'duplicate allocation IDs');
  requireValue(
    Array.isArray(value.cases) &&
      value.cases.length > 0 &&
      value.cases.every(
        (c) =>
          object(c) &&
          text(c.identity) &&
          text(c.variant) &&
          text(c.case) &&
          [
            'total_mass_kg',
            'parts_mass_kg',
            'growth_kg',
            'extra_aft_kg',
            'cg_m',
            'margin_cal',
            'formal_mass_headroom_g',
            'planning_mass_headroom_g',
            'required_whole_mean_proxy_N',
          ].every((key) => numberOrNull(c[key])) &&
          object(c.guide_mps) &&
          Object.values(c.guide_mps).every(numberOrNull) &&
          object(c.common_acceleration_partition_N) &&
          Object.values(c.common_acceleration_partition_N).every(numberOrNull),
      ),
    'recorded cases',
  );
  requireValue(
    Array.isArray(value.fits) &&
      value.fits.every(
        (f) =>
          object(f) &&
          text(f.id) &&
          ['minimum_mm', 'nominal_mm', 'maximum_mm', 'criterion_mm'].every((key) =>
            numberOrNull(f[key]),
          ) &&
          typeof f.conditional_screen_pass === 'boolean' &&
          text(f.basis) &&
          typeof f.measured === 'boolean' &&
          typeof f.environmental_bounds_verified === 'boolean',
      ),
    'conditional fit records',
  );
  requireValue(
    object(value.audit) && value.audit.source_variant === 'frozen_F2',
    'audit source variant',
  );
  const numerical = value.numerical;
  requireValue(
    object(numerical) &&
      numerical.status === 'stopped_node_budget' &&
      numerical.installed_strength_accepted === false &&
      finite(numerical.completed_grids) &&
      finite(numerical.required_grids) &&
      numerical.completed_grids < numerical.required_grids &&
      finite(numerical.fine_nodes) &&
      finite(numerical.node_limit),
    'stopped numerical evidence',
  );
  requireValue(
    object(value.field_export) &&
      value.field_export.active_compatible === false &&
      value.field_export.three_grid_convergence === false,
    'field cannot attach to this proposal',
  );
  requireValue(
    object(value.graph) &&
      Array.isArray(value.graph.nodes) &&
      value.graph.nodes.length > 0 &&
      value.graph.nodes.every(
        (n) =>
          object(n) &&
          text(n.id) &&
          text(n.label) &&
          text(n.note) &&
          text(n.state) &&
          strings(n.part_ids) &&
          n.part_ids.every((id) => partIds.has(id)),
      ),
    'graph nodes or source mapping',
  );
  const nodeIds = new Set(value.graph.nodes.map((n) => n.id));
  requireValue(
    nodeIds.size === value.graph.nodes.length &&
      Array.isArray(value.graph.edges) &&
      value.graph.edges.every(
        (e) =>
          object(e) &&
          nodeIds.has(e.from) &&
          nodeIds.has(e.to) &&
          text(e.label) &&
          text(e.note) &&
          text(e.state),
      ),
    'graph edges',
  );
  requireValue(
    Array.isArray(value.findings) &&
      value.findings.every(
        (f) =>
          object(f) &&
          text(f.id) &&
          text(f.label) &&
          text(f.state) &&
          text(f.note) &&
          strings(f.part_ids) &&
          f.part_ids.every((id) => partIds.has(id)),
      ),
    'findings mapping',
  );
  return value as unknown as F2ConnectionSnapshot;
}

export function connectionNumber(value: number | null | undefined, unit = ''): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return 'Unavailable';
  return `${new Intl.NumberFormat('en', { maximumFractionDigits: 3 }).format(value)} ${unit}`.trim();
}

export function connectionAxialStations(snapshot: F2ConnectionSnapshot) {
  const ring = snapshot.parts.find((part) => part.id === 'forward_ring');
  const tab = snapshot.parts.find((part) => part.id === 'fin_tabs');
  const web = ring?.parameters?.front_web_m;
  const front = tab?.parameters?.front_station_m;
  if (!finite(ring?.z_mm) || !finite(web) || web <= 0 || !finite(front)) return null;
  return { ringFront: ring.z_mm, floor: ring.z_mm + web * 1000, tabFront: front * 1000 };
}

export async function loadF2ConnectionSnapshot(signal: AbortSignal, request: typeof fetch = fetch) {
  const response = await request('/api/engineering/workbench-g80-f2-c1', {
    signal,
    headers: { Accept: 'application/json' },
  });
  if (response.ok)
    return { snapshot: validateF2ConnectionSnapshot(await response.json()), prepared: false };
  let detail = response.statusText;
  let apiDetail = false;
  try {
    const body: unknown = await response.json();
    if (object(body) && typeof body.detail === 'string') {
      detail = body.detail;
      apiDetail = true;
    }
  } catch {
    /* Preserve HTTP error; non-JSON is not missing-route evidence. */
  }
  if (response.status !== 404 || !apiDetail || detail !== 'Not Found')
    throw new Error(`${response.status} ${detail}`);
  signal.throwIfAborted();
  const saved = await request('/engineering-workbench/f2-c1.json', {
    signal,
    headers: { Accept: 'application/json' },
  });
  if (!saved.ok)
    throw new Error(`Prepared F2-C1 source unavailable: ${saved.status} ${saved.statusText}`);
  return { snapshot: validateF2ConnectionSnapshot(await saved.json()), prepared: true };
}
