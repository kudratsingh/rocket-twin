import featureMap from '../../../docs/studies/frontend-component-depth-20261108/mechanical-feature-map.json';

export type BoundsM = [[number, number, number], [number, number, number]];
export type MechanicalParent = {
  id: string;
  material: string;
  function: string;
  maturity: string;
  core_mesh_sha256: string;
  source_mesh_sha256: string;
  source_kind: string;
  source_path: string;
  bounds_m: BoundsM;
  child_count: number;
};
export type MechanicalChild = {
  id: string;
  parent_part_id: string;
  sub_id: string;
  label: string;
  url: string;
  sha256: string;
  bounds_m: BoundsM;
  source_kind: string;
  material: string;
  maturity: string;
  source_mesh_sha256: string;
  source_parent_material?: string;
  visual_bond_reservation_only?: boolean;
};
export type MechanicalLayout = {
  schema_version: number;
  id: string;
  configuration_id: string;
  specification_sha256: string;
  inspection_geometry_sha256: string;
  all55_part_ids: string[];
  units: 'm';
  viewer_frame: string;
  parents: MechanicalParent[];
  children: MechanicalChild[];
  engineering_accepted: boolean;
  mass_or_inertia_generated: boolean;
  canonical_vehicle_geometry_changed: boolean;
};
export type MechanicalIdentity = {
  configurationId: string;
  specificationSha256: string;
  inspectionGeometrySha256: string;
};
export type MechanicalAdmission =
  { ok: true; layout: MechanicalLayout } | { ok: false; reason: string };

const expectedParentIds = new Set([
  'body',
  'fin_set',
  'fin_tabs',
  'root_gussets',
  'motor_tube',
  'forward_ring',
  'aft_ring',
]);
const expectedChildIds = new Set([
  'fin_set:panel-01',
  'fin_set:panel-02',
  'fin_set:panel-03',
  'fin_tabs:tab-01',
  'fin_tabs:tab-02',
  'fin_tabs:tab-03',
  'root_gussets:gusset-01',
  'root_gussets:gusset-02',
  'root_gussets:gusset-03',
  'root_gussets:gusset-04',
  'root_gussets:gusset-05',
  'root_gussets:gusset-06',
  'body:source-01',
  'motor_tube:source-01',
  'aft_ring:source-01',
  'forward_ring:stock_front',
  'forward_ring:bond_reservation',
  'forward_ring:stock_aft',
]);
const assetPrefix = '/engineering-workbench/rp1-component-detail/';
const shaPattern = /^[a-f0-9]{64}$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function isBounds(value: unknown): value is BoundsM {
  return (
    Array.isArray(value) &&
    value.length === 2 &&
    value.every(
      (corner) =>
        Array.isArray(corner) &&
        corner.length === 3 &&
        corner.every((n) => typeof n === 'number' && Number.isFinite(n)),
    ) &&
    [0, 1, 2].every((axis) => value[0][axis] <= value[1][axis])
  );
}

function isSha(value: unknown): value is string {
  return typeof value === 'string' && shaPattern.test(value);
}

function sameIds(actual: unknown, expected: string[]): boolean {
  return (
    Array.isArray(actual) &&
    actual.length === expected.length &&
    actual.every((id) => typeof id === 'string') &&
    new Set(actual).size === expected.length &&
    [...actual].sort().every((id, i) => id === [...expected].sort()[i])
  );
}

/** Admit only the frozen RP1 source tuple and source-linked, exact child assets. */
export function admitRp1MechanicalLayout(
  raw: unknown,
  identity: MechanicalIdentity,
): MechanicalAdmission {
  const frozen = featureMap.frozen_identity;
  if (
    identity.configurationId !== frozen.configuration_id ||
    identity.specificationSha256 !== frozen.specification.sha256 ||
    identity.inspectionGeometrySha256 !== frozen.inspection_geometry_sha256
  ) {
    return { ok: false, reason: 'This vehicle is not the frozen RP1 mechanical source.' };
  }
  if (!isRecord(raw)) return { ok: false, reason: 'Mechanical source catalog is unavailable.' };
  if (
    raw.schema_version !== 1 ||
    raw.id !== 'rp1-existing-source-mechanical-components-v1' ||
    raw.configuration_id !== identity.configurationId ||
    raw.specification_sha256 !== identity.specificationSha256 ||
    raw.inspection_geometry_sha256 !== identity.inspectionGeometrySha256 ||
    raw.units !== 'm' ||
    raw.viewer_frame !== frozen.frame ||
    raw.engineering_accepted !== false ||
    raw.mass_or_inertia_generated !== false ||
    raw.canonical_vehicle_geometry_changed !== false ||
    !sameIds(raw.all55_part_ids, featureMap.stable_part_ids)
  ) {
    return { ok: false, reason: 'Mechanical catalog source identity or 55-part ledger differs.' };
  }
  if (!Array.isArray(raw.parents) || !Array.isArray(raw.children)) {
    return { ok: false, reason: 'Mechanical catalog has no validated pieces.' };
  }
  const parents = new Map<string, MechanicalParent>();
  for (const value of raw.parents) {
    if (!isRecord(value) || typeof value.id !== 'string' || !expectedParentIds.has(value.id))
      return { ok: false, reason: 'Mechanical parent is not an admitted RP1 part.' };
    const source = featureMap.relevant_parts.find((part) => part.part_id === value.id);
    if (
      !source ||
      parents.has(value.id) ||
      value.core_mesh_sha256 !== source.core_mesh?.sha256 ||
      !isSha(value.source_mesh_sha256) ||
      !isBounds(value.bounds_m) ||
      typeof value.material !== 'string' ||
      typeof value.function !== 'string' ||
      value.maturity !== source.maturity ||
      typeof value.source_kind !== 'string' ||
      typeof value.source_path !== 'string' ||
      !Number.isInteger(value.child_count) ||
      (value.child_count as number) < 1
    )
      return {
        ok: false,
        reason: 'Mechanical parent source or bounds differ from the frozen record.',
      };
    const sourceAsset =
      value.source_kind === 'frozen_core_glb'
        ? { path: source.core_mesh!.path, sha256: source.core_mesh!.sha256 }
        : 'optional_detail' in source &&
            source.optional_detail &&
            value.source_kind === 'existing_optional_detail'
          ? {
              path: source.optional_detail.asset_path.replace(/^\//, 'web/public/'),
              sha256: source.optional_detail.asset_sha256,
            }
          : null;
    if (
      !sourceAsset ||
      sourceAsset.path !== value.source_path ||
      sourceAsset.sha256 !== value.source_mesh_sha256
    )
      return { ok: false, reason: 'Mechanical parent uses an unknown source mesh.' };
    parents.set(value.id, value as MechanicalParent);
  }
  if (parents.size !== expectedParentIds.size)
    return { ok: false, reason: 'Mechanical source parents are incomplete.' };
  const seen = new Set<string>();
  for (const value of raw.children) {
    if (!isRecord(value)) return { ok: false, reason: 'Mechanical child entry is malformed.' };
    const parent = parents.get(String(value.parent_part_id));
    if (
      !parent ||
      typeof value.sub_id !== 'string' ||
      !/^[a-z0-9_-]+$/.test(value.sub_id) ||
      value.id !== `${parent.id}:${value.sub_id}` ||
      !expectedChildIds.has(value.id as string) ||
      seen.has(value.id as string) ||
      typeof value.label !== 'string' ||
      !value.label ||
      typeof value.url !== 'string' ||
      !value.url.startsWith(assetPrefix) ||
      !/^\/engineering-workbench\/rp1-component-detail\/[a-z0-9_/-]+\.glb$/.test(value.url) ||
      !isSha(value.sha256) ||
      !isBounds(value.bounds_m) ||
      value.source_mesh_sha256 !== parent.source_mesh_sha256 ||
      value.source_parent_material !== parent.material ||
      (value.id === 'forward_ring:bond_reservation') !==
        (value.visual_bond_reservation_only === true) ||
      (value.visual_bond_reservation_only === true
        ? value.id !== 'forward_ring:bond_reservation' ||
          value.material !== 'Unspecified bond reservation (display only)'
        : value.material !== parent.material) ||
      value.maturity !== parent.maturity ||
      value.source_kind !== parent.source_kind
    )
      return { ok: false, reason: 'Mechanical child asset or source fingerprint is invalid.' };
    seen.add(value.id as string);
  }
  const childRecords = raw.children as Record<string, unknown>[];
  if (
    seen.size !== expectedChildIds.size ||
    [...parents.values()].some((parent) => {
      const children = childRecords.filter((child) => child.parent_part_id === parent.id);
      if (children.length !== parent.child_count) return true;
      const union = boundsUnion(children.map((child) => child.bounds_m as BoundsM));
      return (
        !union ||
        !union.every((corner, i) =>
          corner.every((value, axis) => value === parent.bounds_m[i][axis]),
        )
      );
    })
  )
    return { ok: false, reason: 'Mechanical source has missing parent pieces.' };
  return { ok: true, layout: raw as MechanicalLayout };
}

export function boundsUnion(bounds: BoundsM[]): BoundsM | null {
  if (!bounds.length) return null;
  return [
    [0, 1, 2].map((axis) => Math.min(...bounds.map((item) => item[0][axis]))) as BoundsM[0],
    [0, 1, 2].map((axis) => Math.max(...bounds.map((item) => item[1][axis]))) as BoundsM[1],
  ];
}

/** Illustration offset only; its bounded translation never enters source bounds or fit claims. */
export function displayOffset(child: MechanicalChild, amount: number): [number, number, number] {
  const bounded = Math.max(0, Math.min(1, Number.isFinite(amount) ? amount : 0));
  if (bounded === 0) return [0, 0, 0];
  const radial =
    child.parent_part_id === 'fin_set' ||
    child.parent_part_id === 'fin_tabs' ||
    child.parent_part_id === 'root_gussets';
  if (!radial) return [0, 0, 0];
  const centerX = (child.bounds_m[0][0] + child.bounds_m[1][0]) / 2;
  const centerZ = (child.bounds_m[0][2] + child.bounds_m[1][2]) / 2;
  const length = Math.hypot(centerX, centerZ);
  if (length < 1e-9) return [0, 0, 0];
  return [(0.018 * bounded * centerX) / length, 0, (0.018 * bounded * centerZ) / length];
}

/** Camera scope in displayed coordinates; recorded source bounds remain unchanged. */
export function displayedChildBounds(child: MechanicalChild, amount: number): BoundsM {
  const offset = displayOffset(child, amount);
  return [
    child.bounds_m[0].map((value, axis) => value + offset[axis]) as BoundsM[0],
    child.bounds_m[1].map((value, axis) => value + offset[axis]) as BoundsM[1],
  ];
}

export function displayedChildrenBounds(
  children: MechanicalChild[],
  amount: number,
): BoundsM | null {
  return boundsUnion(children.map((child) => displayedChildBounds(child, amount)));
}

export async function verifiedMechanicalBlobUrl(
  child: MechanicalChild,
  fetcher: typeof fetch = fetch,
): Promise<string> {
  const response = await fetcher(child.url);
  if (!response.ok) throw new Error(`${child.label} asset unavailable (${response.status}).`);
  const bytes = await response.arrayBuffer();
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  const actual = [...new Uint8Array(digest)]
    .map((value) => value.toString(16).padStart(2, '0'))
    .join('');
  if (actual !== child.sha256)
    throw new Error(`${child.label} asset fingerprint differs from source catalog.`);
  return URL.createObjectURL(new Blob([bytes], { type: 'model/gltf-binary' }));
}
