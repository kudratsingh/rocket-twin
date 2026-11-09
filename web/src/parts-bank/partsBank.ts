import featureMap from '../../../docs/studies/frontend-component-depth-20261108/mechanical-feature-map.json';
import geometryManifest from '../../../docs/studies/rp1-inspection-geometry-20261107/manifest.json';
import type { InspectionDocument, JsonValue, Part } from '../types';

export const RP1_BANK_ID = 'rp1-parts-bank-v1';
export const RP1_BANK_CONFIGURATION = 'G80-F2-RP1-AD1-definition-v2';
export const RP1_BANK_SPEC = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
export const RP1_BANK_DEFINITION =
  'e9db49f2cafc89b1f77bf9d7396434297bc8bb8754085fdcf74d3b0242012555';
export const RP1_BANK_RECORD = 'bc349a24fe1cfaa4d883b9e00dc5b75387638a7be5cd4b05d9f32112ee8bd95b';
export const RP1_BANK_GEOMETRY = '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608';
export const RP1_BANK_PREPARED_URL = '/engineering-workbench/rp1-parts-bank.json';
export const RP1_BANK_API_URL = '/api/parts-bank';
export const RP1_BANK_REVISIONS = new Set([
  'bd69971e461251b843e24b4f2ec93c8d56e693bcbfa2d121697399a4510761cc', // pinned source-only export
  '7508b1f4361d3bada13ad23d11f6e997cda4aa3a476d33d847898425b2367e36', // admitted 26-mesh export
]);

export interface BankDefinition {
  id: string;
  revision_sha256: string;
  source_part_id: string;
  name: string;
  kind: string;
  material: string;
  function: string;
  dimensions: { units: 'm'; values: Record<string, JsonValue>; basis: string };
  mass_kg: number | null;
  mass_basis: string;
  manufacturing: {
    method: string | null;
    generator: string | null;
    notes: string | null;
    status: string;
  };
  geometry: {
    maturity: string;
    mesh_available: boolean;
    mesh: { path: string; sha256: string; units: 'm' } | null;
    reason: string | null;
    mesh_scope: 'installed_reference' | null;
    frame: string | null;
    reusable_local_geometry: false;
    registered_instance_id: string;
  };
  price: {
    amount_usd: number | null;
    basis: 'source_budget';
    current_verified: false;
    counting_basis: 'source_record';
    owner_stock_credit: false;
    notes: string;
  };
  provenance: { path: string; sha256: string; locator: string; role: string }[];
  issues: {
    id: string;
    severity: 'warning';
    status: 'unresolved';
    message: string;
    locators: string[];
  }[];
  reuse_status: string;
  source_cad_role: string;
  source_estimate: boolean;
  physical_verification: 'open';
  interfaces: null;
  interfaces_status: string;
}

export interface BankInstance {
  id: string;
  definition_id: string;
  definition_revision_sha256: string;
  configuration_id: string;
  position_m: number | null;
  lateral_offset_m: [number, number] | null;
  source_parent_id: string | null;
  quantity: 1;
  counting_basis: 'source_record';
  group_count: number;
  group_count_basis: string;
}

export interface PartsBankCatalog {
  schema_version: 1;
  id: typeof RP1_BANK_ID;
  revision_sha256: string;
  configuration_id: typeof RP1_BANK_CONFIGURATION;
  identity: {
    configuration_id: string;
    specification_path: string;
    specification_sha256: string;
    definition_path: string;
    definition_sha256: string;
    record_path: string;
    record_sha256: string;
    inspection_geometry_sha256: string | null;
  };
  definitions: BankDefinition[];
  instances: BankInstance[];
  summary: Record<string, JsonValue>;
  capabilities: { editable: false; draft_builder: false };
  module_sources: Record<string, string>;
}

export type BankAdmission = { ok: true; catalog: PartsBankCatalog } | { ok: false; reason: string };
export type BankTransport = 'live API' | 'prepared source snapshot';
export type BankLoad = { catalog: PartsBankCatalog; transport: BankTransport };
export type BankFilters = { query: string; kind: string; material: string; maturity: string };

const sha = /^[a-f0-9]{64}$/;
const expectedIds = featureMap.stable_part_ids;
const expectedGeometry = new Map(geometryManifest.parts.map((part) => [part.id, part]));
const sourceFiles = new Map([
  ['configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml', RP1_BANK_SPEC],
  ['configs/studies/rp1-attachment-definition-v2.yaml', RP1_BANK_DEFINITION],
  ['runs/wo03-rp1-attachment-definition-20261103-v2/record.json', RP1_BANK_RECORD],
]);
const moduleFiles = new Map([
  ['src/api/parts_bank.py', '5515a6adc6b62ea7d6ed8490ed832590de8cef1b52db44ae6a42611104cc48e1'],
  ['src/api/rp1_inspection.py', '6271dffccd8cd411f2e8e255c9a9e67bee8067dd2e5512d5481cd9c2b850aa8c'],
  ['src/api/rp1_geometry.py', '333e18a683f9d5bf95943ad60fbed8c086ae6e09c2e9f1fbbeabecd0b6654a59'],
  [
    'src/inspection/rp1_geometry.py',
    'd79db74c6285f9c45d7ffade4bb4e8e95279cf64cc7a3c4f0253c09baedf90d3',
  ],
]);
const requiredIssues = new Map([
  ['motor_retainer', 'retainer_product_conflict'],
  ['motor_tube', 'tube_dimension_conflict'],
  ['independent_recovery', 'recovery_product_conflict'],
  ['high_g_accel', 'board_reference_limits'],
]);
const reuseStates = new Set([
  'allowance_only',
  'geometry_unavailable',
  'identity_unresolved',
  'source_reference_only',
]);

function record(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function finiteOrNull(value: unknown): value is number | null {
  return value === null || (typeof value === 'number' && Number.isFinite(value));
}

function sameSourceValue(left: unknown, right: unknown): boolean {
  if (left === right) return true;
  if (Array.isArray(left) || Array.isArray(right))
    return (
      Array.isArray(left) &&
      Array.isArray(right) &&
      left.length === right.length &&
      left.every((value, index) => sameSourceValue(value, right[index]))
    );
  if (!record(left) || !record(right)) return false;
  const keys = Object.keys(left);
  return (
    keys.length === Object.keys(right).length &&
    keys.every((key) => Object.hasOwn(right, key) && sameSourceValue(left[key], right[key]))
  );
}

function sameIds(actual: string[], expected: string[]): boolean {
  return (
    actual.length === expected.length &&
    new Set(actual).size === expected.length &&
    actual.every((id) => expected.includes(id))
  );
}

function sourceVehicle(vehicle: InspectionDocument): boolean {
  return (
    vehicle.id === RP1_BANK_CONFIGURATION &&
    vehicle.identity?.specification_sha256 === RP1_BANK_SPEC &&
    vehicle.identity?.inspection_geometry_sha256 === RP1_BANK_GEOMETRY &&
    vehicle.parts.length === expectedIds.length &&
    sameIds(
      vehicle.parts.map((part) => part.id),
      expectedIds,
    )
  );
}

function validDefinition(
  value: unknown,
  part: Part,
  geometryAvailable: boolean,
): value is BankDefinition {
  if (
    !record(value) ||
    !record(value.dimensions) ||
    !record(value.geometry) ||
    !record(value.price) ||
    !record(value.manufacturing)
  )
    return false;
  const definition = value as unknown as BankDefinition;
  const sourceGeometry = expectedGeometry.get(part.id);
  const expectedMesh = geometryAvailable ? sourceGeometry?.mesh : null;
  return (
    value.id === `rp1:${part.id}` &&
    sha.test(String(value.revision_sha256)) &&
    value.source_part_id === part.id &&
    typeof value.name === 'string' &&
    value.kind === part.type &&
    value.material === part.material &&
    typeof value.function === 'string' &&
    value.dimensions.units === 'm' &&
    value.dimensions.basis ===
      'source_nominal; count is dimensionless and angles use named units' &&
    record(value.dimensions.values) &&
    sameSourceValue(value.dimensions.values, part.geometry) &&
    finiteOrNull(value.mass_kg) &&
    (part.mass_kg === undefined ? value.mass_kg === null : value.mass_kg === part.mass_kg) &&
    value.mass_basis ===
      (value.mass_kg === null
        ? 'unavailable'
        : 'Source-record group estimate/budget; not measured or per-piece mass') &&
    value.geometry.maturity === sourceGeometry?.maturity &&
    value.geometry.mesh_available === Boolean(expectedMesh) &&
    value.geometry.mesh_scope === (expectedMesh ? 'installed_reference' : null) &&
    value.geometry.frame === (expectedMesh ? geometryManifest.viewer_frame : null) &&
    value.geometry.reusable_local_geometry === false &&
    value.geometry.registered_instance_id === part.id &&
    (expectedMesh
      ? record(value.geometry.mesh) &&
        value.geometry.mesh.path === expectedMesh.path &&
        value.geometry.mesh.sha256 === expectedMesh.sha256 &&
        value.geometry.mesh.units === 'm'
      : value.geometry.mesh === null) &&
    (value.geometry.reason === null || typeof value.geometry.reason === 'string') &&
    value.price.basis === 'source_budget' &&
    value.price.current_verified === false &&
    value.price.counting_basis === 'source_record' &&
    value.price.owner_stock_credit === false &&
    value.price.notes === 'Dated source group budget; not a current unit price or quote' &&
    finiteOrNull(value.price.amount_usd) &&
    Number(value.price.amount_usd ?? 0) >= 0 &&
    value.price.amount_usd === (part.build?.cost_usd ?? null) &&
    (value.manufacturing.method === null || typeof value.manufacturing.method === 'string') &&
    (value.manufacturing.generator === null || typeof value.manufacturing.generator === 'string') &&
    (value.manufacturing.notes === null || typeof value.manufacturing.notes === 'string') &&
    value.manufacturing.status === 'source description; not manufacturing authorization' &&
    value.manufacturing.method === (part.build?.method ?? null) &&
    value.manufacturing.generator === (part.build?.generator ?? null) &&
    value.manufacturing.notes === (part.build?.notes ?? null) &&
    Array.isArray(value.provenance) &&
    value.provenance.length === 3 &&
    value.provenance.every(
      (row: unknown) =>
        record(row) &&
        typeof row.path === 'string' &&
        sourceFiles.get(row.path) === row.sha256 &&
        typeof row.locator === 'string' &&
        typeof row.role === 'string',
    ) &&
    Array.isArray(value.issues) &&
    value.issues.every(
      (issue: unknown) =>
        record(issue) &&
        typeof issue.id === 'string' &&
        issue.severity === 'warning' &&
        issue.status === 'unresolved' &&
        typeof issue.message === 'string' &&
        Array.isArray(issue.locators) &&
        issue.locators.every((locator: unknown) => typeof locator === 'string'),
    ) &&
    reuseStates.has(definition.reuse_status) &&
    typeof definition.source_cad_role === 'string' &&
    typeof definition.source_estimate === 'boolean' &&
    definition.physical_verification === 'open' &&
    definition.interfaces === null &&
    typeof definition.interfaces_status === 'string' &&
    definition.name === part.name &&
    definition.function === part.function &&
    definition.source_cad_role === part.cad?.role &&
    definition.source_estimate === (part.estimate ?? true) &&
    (!requiredIssues.has(part.id) ||
      definition.issues.some((issue) => issue.id === requiredIssues.get(part.id))) &&
    (definition.price.amount_usd !== 0 ||
      definition.issues.some(
        (issue) => issue.id === 'zero_source_budget' && issue.message.includes('not a free part'),
      ))
  );
}

function validInstance(
  value: unknown,
  definition: BankDefinition,
  part: Part,
): value is BankInstance {
  if (!record(value)) return false;
  const position = part.location?.position_m ?? part.position_m ?? null;
  const lateral = part.location?.lateral_offset_m ?? null;
  return (
    value.id === part.id &&
    value.definition_id === definition.id &&
    value.definition_revision_sha256 === definition.revision_sha256 &&
    value.configuration_id === RP1_BANK_CONFIGURATION &&
    finiteOrNull(value.position_m) &&
    value.position_m === position &&
    (lateral === null
      ? value.lateral_offset_m === null
      : Array.isArray(value.lateral_offset_m) &&
        value.lateral_offset_m.length === 2 &&
        value.lateral_offset_m.every((n: unknown) => typeof n === 'number' && Number.isFinite(n)) &&
        value.lateral_offset_m[0] === lateral[0] &&
        value.lateral_offset_m[1] === lateral[1]) &&
    value.source_parent_id === part.parent &&
    value.quantity === 1 &&
    value.counting_basis === 'source_record' &&
    Number.isInteger(value.group_count) &&
    value.group_count === (typeof part.geometry?.count === 'number' ? part.geometry.count : 1) &&
    Number(value.group_count) >= 1 &&
    typeof value.group_count_basis === 'string'
  );
}

/** Strict current-source admission; a catalog never changes the active vehicle. */
export function admitPartsBank(raw: unknown, vehicle: InspectionDocument): BankAdmission {
  if (!sourceVehicle(vehicle))
    return { ok: false, reason: 'Parts bank is only available for the frozen current RP1 source.' };
  if (
    !record(raw) ||
    !record(raw.identity) ||
    !record(raw.capabilities) ||
    !record(raw.module_sources)
  )
    return { ok: false, reason: 'Parts bank source record is malformed.' };
  const identity = raw.identity;
  const modules = raw.module_sources;
  if (
    raw.schema_version !== 1 ||
    raw.id !== RP1_BANK_ID ||
    !RP1_BANK_REVISIONS.has(String(raw.revision_sha256)) ||
    raw.configuration_id !== RP1_BANK_CONFIGURATION ||
    identity.configuration_id !== RP1_BANK_CONFIGURATION ||
    identity.specification_path !== 'configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml' ||
    identity.specification_sha256 !== RP1_BANK_SPEC ||
    identity.definition_path !== 'configs/studies/rp1-attachment-definition-v2.yaml' ||
    identity.definition_sha256 !== RP1_BANK_DEFINITION ||
    identity.record_path !== 'runs/wo03-rp1-attachment-definition-20261103-v2/record.json' ||
    identity.record_sha256 !== RP1_BANK_RECORD ||
    (identity.inspection_geometry_sha256 !== null &&
      identity.inspection_geometry_sha256 !== RP1_BANK_GEOMETRY) ||
    raw.capabilities.editable !== false ||
    raw.capabilities.draft_builder !== false ||
    Object.keys(modules).length !== moduleFiles.size ||
    [...moduleFiles].some(([path, hash]) => modules[path] !== hash)
  )
    return {
      ok: false,
      reason: 'Parts bank source identity, revision, or read-only contract differs.',
    };
  if (
    !Array.isArray(raw.definitions) ||
    !Array.isArray(raw.instances) ||
    raw.definitions.length !== 55 ||
    raw.instances.length !== 55 ||
    !record(raw.summary)
  )
    return { ok: false, reason: 'Parts bank does not contain all 55 source records.' };
  const geometryAvailable = identity.inspection_geometry_sha256 !== null;
  const maturityCount = geometryManifest.parts.reduce<Record<string, number>>((count, part) => {
    count[part.maturity] = (count[part.maturity] ?? 0) + 1;
    return count;
  }, {});
  if (
    raw.summary.source_records !== 55 ||
    raw.summary.definitions !== 55 ||
    raw.summary.installed_instances !== 55 ||
    raw.summary.mesh_available !== (geometryAvailable ? 26 : 0) ||
    !sameSourceValue(raw.summary.by_maturity, maturityCount) ||
    raw.summary.engineering_accepted !== false ||
    raw.summary.flight_ready !== false
  )
    return { ok: false, reason: 'Parts bank summary or source maturity coverage differs.' };
  const definitions = new Map<string, BankDefinition>();
  for (const value of raw.definitions) {
    if (
      !record(value) ||
      typeof value.source_part_id !== 'string' ||
      definitions.has(value.source_part_id)
    )
      return { ok: false, reason: 'Parts bank has a duplicate or malformed definition.' };
    const part = vehicle.parts.find((entry) => entry.id === value.source_part_id);
    if (!part || !validDefinition(value, part, geometryAvailable))
      return {
        ok: false,
        reason: `Parts bank definition differs from current source: ${value.source_part_id}.`,
      };
    definitions.set(part.id, value);
  }
  const instances = new Set<string>();
  for (const value of raw.instances) {
    if (!record(value) || typeof value.id !== 'string' || instances.has(value.id))
      return { ok: false, reason: 'Parts bank has a duplicate or malformed installed instance.' };
    const part = vehicle.parts.find((entry) => entry.id === value.id);
    const definition = definitions.get(value.id);
    if (!part || !definition || !validInstance(value, definition, part))
      return {
        ok: false,
        reason: `Parts bank installed link differs from current source: ${value.id}.`,
      };
    instances.add(value.id);
  }
  if (!sameIds([...definitions.keys()], expectedIds) || !sameIds([...instances], expectedIds))
    return { ok: false, reason: 'Parts bank source part coverage is incomplete.' };
  return { ok: true, catalog: raw as unknown as PartsBankCatalog };
}

export async function loadPartsBank(
  vehicle: InspectionDocument,
  fetcher: typeof fetch = fetch,
  signal?: AbortSignal,
): Promise<BankLoad> {
  if (!sourceVehicle(vehicle))
    throw new Error('Parts bank is only available for the frozen current RP1 source.');
  const first = await fetcher(RP1_BANK_API_URL, {
    signal,
    headers: { Accept: 'application/json' },
  });
  const fallback = first.status === 404;
  const response = fallback
    ? await fetcher(RP1_BANK_PREPARED_URL, { signal, headers: { Accept: 'application/json' } })
    : first;
  if (!response.ok)
    throw new Error(
      `${fallback ? 'Prepared source snapshot' : 'Parts bank API'} unavailable (${response.status}).`,
    );
  let raw: unknown;
  try {
    raw = await response.json();
  } catch {
    throw new Error(
      `${fallback ? 'Prepared source snapshot' : 'Parts bank API'} returned invalid JSON.`,
    );
  }
  const admitted = admitPartsBank(raw, vehicle);
  if (!admitted.ok) throw new Error(admitted.reason);
  return {
    catalog: admitted.catalog,
    transport: fallback ? 'prepared source snapshot' : 'live API',
  };
}

export function filteredBankDefinitions(
  catalog: PartsBankCatalog,
  filters: BankFilters,
): BankDefinition[] {
  const term = filters.query.trim().toLowerCase();
  return catalog.definitions.filter((definition) => {
    if (filters.kind && definition.kind !== filters.kind) return false;
    if (filters.material && definition.material !== filters.material) return false;
    if (filters.maturity && definition.geometry.maturity !== filters.maturity) return false;
    const text =
      `${definition.source_part_id} ${definition.name} ${definition.kind} ${definition.material} ${definition.function}`.toLowerCase();
    return !term || text.includes(term);
  });
}
