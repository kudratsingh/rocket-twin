import manifest from '../../../docs/studies/frontend-template-bank-20261109/geometry.json';

export type DatumFeatureId = 'axis' | 'bore' | 'outer_cylinder' | 'start_plane' | 'end_plane';
export type DatumPoint = [number, number, number];
interface FeatureBase {
  id: DatumFeatureId;
  scope: 'analytic_nominal_datum';
  frame: 'local_cad_mm';
  cad_face_ids: null;
  mesh_triangle_ids: null;
  tolerance_mm: null;
  mating_admitted: false;
}
export type ReferenceFeature = FeatureBase &
  (
    | {
        id: 'axis';
        kind: 'analytic_axis';
        origin_mm: DatumPoint;
        direction: DatumPoint;
        axial_range_mm: [number, number];
      }
    | {
        id: 'bore' | 'outer_cylinder';
        kind: 'analytic_cylinder';
        axis: 'axis';
        radius_mm: number;
        axial_range_mm: [number, number];
      }
    | {
        id: 'start_plane' | 'end_plane';
        kind: 'analytic_annular_plane';
        origin_mm: DatumPoint;
        normal: DatumPoint;
        radial_range_mm: [number, number];
        normal_basis: string;
      }
  );
interface ReferenceAsset {
  path: string;
  url: string;
  sha256: string;
  bytes: number;
}
export interface ReferenceDefinition {
  id: string;
  revision_sha256: string;
  name: string;
  family: string;
  source_part_id: string;
  source_template_id: string;
  source_template_revision_sha256: string;
  parameters_mm: { outer_radius_mm: number; inner_radius_mm: number; length_mm: number };
  exact_product: null;
  stock_adoption: false;
  installed_geometry_adoption: false;
  identity_limit: string;
  scope: 'geometry_only_planning';
  unknown_properties: Record<string, null>;
  readiness: Record<string, false>;
  frames: {
    local_cad_mm: { units: 'mm'; origin: 'front_center'; axes: string };
    viewer: { units: 'm'; mapping: string };
  };
  analytic_features: ReferenceFeature[];
  interfaces: null;
  interfaces_status: string;
  representation: {
    scope: 'local_nominal_reference_only';
    installed_transform: null;
    assets: { step: ReferenceAsset; glb: ReferenceAsset };
    recorded_readback: (typeof manifest.representations)[number]['readback'];
    bounds_m: { min: number[]; max: number[] };
    frame_source: string;
    kernel_execution_performed: false;
  };
  provenance: {
    configuration_id: string;
    specification_sha256: string;
    source_part_id: string;
    source_locator: string;
    source_mass_policy: string;
    geometry_manifest_sha256: string;
    generator: typeof manifest.cad_generator;
    source_registry: typeof manifest.registry;
  };
}
export const DATUM_FEATURE_IDS: readonly DatumFeatureId[] = [
  'axis',
  'bore',
  'outer_cylinder',
  'start_plane',
  'end_plane',
];
export const DATUM_LABELS: Record<DatumFeatureId, string> = {
  axis: 'Local axis',
  bore: 'Nominal bore cylinder',
  outer_cylinder: 'Nominal outer cylinder',
  start_plane: 'Start annular datum',
  end_plane: 'End annular datum',
};
const cases = [
  {
    id: 'reference-local-v1:motor-tube-nominal',
    slug: 'motor-tube-cut',
    source: 'motor_tube',
    revision: 'fd6c666dfed5d79ed44ed126b85d1de7dca87c1210165808b44f270e2ce2a42c',
    templateRevision: '7f3d7dd2ce09293d787aac7343138c1f8a9a44f40f07ff63f4c58d0eae5690e3',
    name: 'Nominal tube-cut geometry reference',
    family: 'tube_cut',
    outer: 15.6845,
    inner: 14.5845,
    length: 165,
    identityLimit:
      'Current source geometry conflicts with AeroTech12912 stock/legacy mount-kit notes. This is nominal geometry, not exact purchased tube or motor/liner/retainer fit.',
    assets: {
      step: {
        bytes: 9654,
        sha256: '339faa3de20f1e0fef905831403de7450af78dedeb743ed8d5b32d946d69953f',
      },
      glb: {
        bytes: 19864,
        sha256: 'f90c129bc300767b228e0195a6a528bc9e19bdd5a1f8d7752ab2f6eac4114336',
      },
    },
  },
  {
    id: 'reference-local-v1:aft-annulus-nominal',
    slug: 'aft-annular-ring',
    source: 'aft_ring',
    revision: '158150615a9c291ce12b3320d535c11151a564d7ad176dda9ca9693025a5d710',
    templateRevision: 'f720488a173d91f936666c160e0bc9c912eb4bb0e2a5b18e188857d40637db8e',
    name: 'Plain aft-annulus geometry reference',
    family: 'annular_ring',
    outer: 32.2,
    inner: 15.95,
    length: 6,
    identityLimit:
      'Plain nominal annulus only; the complete installed ring proposal, stock/process tolerances, bonds and joint response remain unavailable or unverified.',
    assets: {
      step: {
        bytes: 9599,
        sha256: 'c006c932f7353b82cef9e7cc280bb0d46839b7442af141bcc81c39df40910c33',
      },
      glb: {
        bytes: 19860,
        sha256: 'ca2a1f86438ea079d6b3433df9e9d275a4911639a1a6aaa5e9be408a4535e6b3',
      },
    },
  },
];
const frameSource = 'docs/studies/frontend-template-bank-20261109/geometry.json';
const configuration = 'G80-F2-RP1-AD1-definition-v2';
const specification = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
const manifestSha = '6316ccef56c168e14d8a14a6570d162f35eb43bcadf4bd6132226b51d91799d2';
function object(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
function same(left: unknown, right: unknown): boolean {
  if (left === right) return true;
  if (Array.isArray(left) || Array.isArray(right))
    return (
      Array.isArray(left) &&
      Array.isArray(right) &&
      left.length === right.length &&
      left.every((item, i) => same(item, right[i]))
    );
  return (
    object(left) &&
    object(right) &&
    Object.keys(left).length === Object.keys(right).length &&
    Object.keys(left).every((key) => Object.hasOwn(right, key) && same(left[key], right[key]))
  );
}
function expectedFeatures(outer: number, inner: number, length: number): unknown[] {
  const common = {
    scope: 'analytic_nominal_datum',
    frame: 'local_cad_mm',
    cad_face_ids: null,
    mesh_triangle_ids: null,
    tolerance_mm: null,
    mating_admitted: false,
  };
  return [
    {
      ...common,
      id: 'axis',
      kind: 'analytic_axis',
      origin_mm: [0, 0, 0],
      direction: [0, 0, 1],
      axial_range_mm: [0, length],
    },
    ...(
      [
        ['bore', inner],
        ['outer_cylinder', outer],
      ] as const
    ).map(([id, radius]) => ({
      ...common,
      id,
      kind: 'analytic_cylinder',
      axis: 'axis',
      radius_mm: radius,
      axial_range_mm: [0, length],
    })),
    ...(
      [
        ['start_plane', 0],
        ['end_plane', length],
      ] as const
    ).map(([id, z]) => ({
      ...common,
      id,
      kind: 'analytic_annular_plane',
      origin_mm: [0, 0, z],
      normal: [0, 0, 1],
      radial_range_mm: [inner, outer],
      normal_basis: 'Positive local axis convention; not a kernel face orientation',
    })),
  ];
}
/** Admit the complete frozen definition DTO; runtime availability is separate.
 * Hashes are Python identities, not JS rehashes of floating-point source JSON.
 */
export function admitReferenceDefinition(raw: unknown): ReferenceDefinition | null {
  if (!object(raw)) return null;
  const source = cases.find((row) => row.id === raw.id);
  if (!source) return null;
  const representation = manifest.representations.find(
    (row) => row.template_id === `rp1-template:${source.slug}`,
  );
  if (
    !representation ||
    manifest.schema_version !== 1 ||
    manifest.id !== 'rp1-template-geometry-v1' ||
    manifest.configuration_id !== configuration ||
    manifest.specification_sha256 !== specification ||
    manifest.viewer_mapping !== 'viewer[X,Y,Z]=[cadX/1000,-cadZ/1000,cadY/1000]' ||
    manifest.local_cad_frame_mm !== 'front center; X=body+y, Y=body-z, Z=aft along part' ||
    manifest.step_units !== 'mm' ||
    manifest.viewer_units !== 'm' ||
    representation.template_revision_sha256 !== source.templateRevision
  )
    return null;
  const assets = Object.fromEntries(
    (['step', 'glb'] as const).map((format) => [
      format,
      {
        path: `output/rp1-template-geometry-v1/${source.slug}.${format}`,
        url: `/engineering-workbench/rp1-part-templates-geometry/${source.slug}.${format}`,
        ...source.assets[format],
      },
    ]),
  );
  if (!same(assets.step, representation.step) || !same(assets.glb, representation.glb)) return null;
  const expected = {
    id: source.id,
    revision_sha256: source.revision,
    name: source.name,
    family: source.family,
    source_part_id: source.source,
    source_template_id: `rp1-template:${source.slug}`,
    source_template_revision_sha256: source.templateRevision,
    parameters_mm: {
      outer_radius_mm: source.outer,
      inner_radius_mm: source.inner,
      length_mm: source.length,
    },
    exact_product: null,
    stock_adoption: false,
    installed_geometry_adoption: false,
    identity_limit: source.identityLimit,
    scope: 'geometry_only_planning',
    unknown_properties: {
      mass_kg: null,
      procurement_cost_usd: null,
      inertia_kg_m2: null,
      stock_tolerances_mm: null,
      strength_allowables: null,
      thermal_capability: null,
      qualified_material: null,
    },
    readiness: {
      add_instance_api: false,
      connect_api: false,
      resolved_candidate: false,
      simulation_eligible: false,
      engineering_accepted: false,
      physically_verified: false,
      flight_ready: false,
    },
    frames: {
      local_cad_mm: {
        units: 'mm',
        origin: 'front_center',
        axes: 'X=body+y, Y=body-z, Z=aft along part',
      },
      viewer: { units: 'm', mapping: 'viewer[X,Y,Z]=[cadX/1000,-cadZ/1000,cadY/1000]' },
    },
    analytic_features: expectedFeatures(source.outer, source.inner, source.length),
    interfaces: null,
    interfaces_status: 'Analytic datums only; no contact or connection contract admitted',
    representation: {
      scope: 'local_nominal_reference_only',
      installed_transform: null,
      assets,
      recorded_readback: representation.readback,
      bounds_m: representation.bounds_m,
      frame_source: frameSource,
      kernel_execution_performed: false,
    },
    provenance: {
      configuration_id: configuration,
      specification_sha256: specification,
      source_part_id: source.source,
      source_locator: `parts[id=${source.source}].geometry`,
      source_mass_policy:
        'Original source budget estimates are not new installed reference mass; no mass/cost credit or charge is generated',
      geometry_manifest_sha256: manifestSha,
      generator: manifest.cad_generator,
      source_registry: manifest.registry,
    },
  };
  return same(raw, expected) ? (raw as unknown as ReferenceDefinition) : null;
}
function finiteTuple(value: DatumPoint): void {
  if (value.length !== 3 || value.some((coordinate) => !Number.isFinite(coordinate)))
    throw new Error('A finite three-coordinate datum is required.');
}
const positiveZero = (value: number) => (value === 0 ? 0 : value);
/** Recorded local CAD millimetres to local viewer metres; no installation transform. */
export function cadPointToViewer(point: DatumPoint): DatumPoint {
  finiteTuple(point);
  return [point[0] / 1000, positiveZero(-point[2] / 1000), point[1] / 1000];
}
/** Direction is dimensionless: rotate axes without applying the mm-to-m scale. */
export function cadDirectionToViewer(direction: DatumPoint): DatumPoint {
  finiteTuple(direction);
  return [direction[0], positiveZero(-direction[2]), direction[1]];
}
export interface DatumGuideGeometry {
  feature: ReferenceFeature;
  lines: DatumPoint[][];
  annulus: {
    center: DatumPoint;
    innerRadiusM: number;
    outerRadiusM: number;
    normal: DatumPoint;
  } | null;
  callout: DatumPoint;
}
function circle(radius: number, z: number): DatumPoint[] {
  return Array.from({ length: 97 }, (_, index) => {
    const angle = (index / 96) * 2 * Math.PI;
    return cadPointToViewer([radius * Math.cos(angle), radius * Math.sin(angle), z]);
  });
}
/** Selected analytic geometry only; never a mesh feature, part or physical result. */
export function referenceDatumGeometry(
  raw: unknown,
  selectedFeature: string | null,
): DatumGuideGeometry | null {
  const definition = admitReferenceDefinition(raw);
  const feature = definition?.analytic_features.find((row) => row.id === selectedFeature);
  if (!definition || !feature) return null;
  const { outer_radius_mm: outer } = definition.parameters_mm;
  if (feature.kind === 'analytic_axis') {
    const endpoints = feature.axial_range_mm.map((distance) =>
      cadPointToViewer(
        feature.origin_mm.map((value, i) => value + feature.direction[i] * distance) as DatumPoint,
      ),
    );
    return {
      feature,
      lines: [endpoints],
      annulus: null,
      callout: cadPointToViewer([
        outer * 1.15,
        0,
        (feature.axial_range_mm[0] + feature.axial_range_mm[1]) / 2,
      ]),
    };
  }
  if (feature.kind === 'analytic_cylinder') {
    const [start, end] = feature.axial_range_mm;
    const radius = feature.radius_mm;
    const lines = [circle(radius, start), circle(radius, end)];
    for (let index = 0; index < 4; index++) {
      const angle = (index * Math.PI) / 2;
      lines.push([
        cadPointToViewer([radius * Math.cos(angle), radius * Math.sin(angle), start]),
        cadPointToViewer([radius * Math.cos(angle), radius * Math.sin(angle), end]),
      ]);
    }
    return {
      feature,
      lines,
      annulus: null,
      callout: cadPointToViewer([radius, 0, (start + end) / 2]),
    };
  }
  const center = cadPointToViewer(feature.origin_mm);
  const [inner, outside] = feature.radial_range_mm;
  return {
    feature,
    lines: [circle(inner, feature.origin_mm[2]), circle(outside, feature.origin_mm[2])],
    annulus: {
      center,
      innerRadiusM: inner / 1000,
      outerRadiusM: outside / 1000,
      normal: cadDirectionToViewer(feature.normal),
    },
    callout: cadPointToViewer([outside, 0, feature.origin_mm[2]]),
  };
}
