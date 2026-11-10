import admission from '../../../docs/studies/frontend-template-bank-20261109/registry-admission.json';
import type { InspectionDocument } from '../types';
import { RP1_BANK_CONFIGURATION, RP1_BANK_GEOMETRY, RP1_BANK_SPEC } from './partsBank';

export interface TemplateSource {
  path: string;
  sha256: string;
  locator: string;
}
export interface TemplateParameter {
  key: string;
  value: number | number[] | string;
  unit: string;
  value_basis: string;
  source: TemplateSource;
  tolerance: { plus_minus: number; unit: string; basis: string; source: TemplateSource } | null;
}
export interface TemplateFeature {
  id: string;
  template_id: string;
  source_part_id: string;
  label: string;
  kind: string;
  parameter_keys: string[];
  source: TemplateSource;
  mating_part_ids: string[];
  status: string;
  installed_contact_status: string;
}
export interface PartTemplate {
  id: string;
  revision_sha256: string;
  label: string;
  family: string;
  source_part_ids: string[];
  material: string;
  parameters: TemplateParameter[];
  local_frame: { units: string; origin: string; axes: string };
  installed_references: {
    source_part_id: string;
    step: { path: string; sha256: string };
    cad_frame: string;
    front_station_mm: number;
  }[];
  geometry: {
    source_cad_generator: string;
    local_generator: string | null;
    local_recipe_supported: boolean;
    generated_asset: null;
    installed_step_is_local_template: false;
  };
  feature_ids: string[];
  interfaces: {
    feature_id: string;
    mates: string[];
    geometry_status: string;
    installed_contact_status: string;
  }[];
  reuse: { geometry: string; draft_admission: false; reason: string };
  mass_accounting: {
    source_part_ids: string[];
    template_mass_kg: null;
    incremental_charge: false;
  };
}
export interface TemplateRegistry {
  schema_version: 1;
  id: string;
  revision_sha256: string;
  configuration_id: string;
  identity: { specification: { path: string; sha256: string }; [key: string]: unknown };
  all55_part_ids: string[];
  templates: PartTemplate[];
  feature_sources: TemplateFeature[];
  dispositions: {
    source_part_id: string;
    template_id: string | null;
    reason: string;
    [key: string]: unknown;
  }[];
  capabilities: {
    browse: true;
    inspect: true;
    draft_admission: false;
    cad_job_execution: false;
  };
}

/** Prepared contracts are immutable source data, not a substitute live API. */
export async function loadTemplateRegistry(
  vehicle: InspectionDocument,
  request: typeof fetch = fetch,
  signal?: AbortSignal,
): Promise<TemplateRegistry> {
  if (
    vehicle.id !== RP1_BANK_CONFIGURATION ||
    vehicle.identity?.specification_sha256 !== RP1_BANK_SPEC ||
    vehicle.identity?.inspection_geometry_sha256 !== RP1_BANK_GEOMETRY
  )
    throw new Error(
      'Template recipes require the exact current RP1 design and inspection revision.',
    );
  const response = await request(admission.prepared_path, {
    signal,
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw new Error(`Prepared template contract unavailable (${response.status}).`);
  const bytes = await response.arrayBuffer();
  const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
    .map((n) => n.toString(16).padStart(2, '0'))
    .join('');
  if (digest !== admission.prepared_sha256)
    throw new Error('Template contract bytes differ from the admitted source revision.');
  const registry = JSON.parse(new TextDecoder().decode(bytes)) as TemplateRegistry;
  if (
    registry.schema_version !== admission.schema_version ||
    registry.id !== admission.id ||
    registry.configuration_id !== admission.configuration_id ||
    registry.revision_sha256 !== admission.revision_sha256 ||
    registry.identity.specification.sha256 !== admission.specification_sha256 ||
    registry.capabilities.draft_admission !== false ||
    registry.capabilities.cad_job_execution !== false ||
    registry.all55_part_ids.length !== 55 ||
    new Set(registry.all55_part_ids).size !== 55 ||
    vehicle.parts.length !== 55 ||
    new Set(vehicle.parts.map((part) => part.id)).size !== 55 ||
    vehicle.parts.some((part) => !registry.all55_part_ids.includes(part.id))
  )
    throw new Error('Template contract identity or source-part coverage differs.');
  return registry;
}

export function templateLabel(value: string): string {
  return value
    .replace(/_(mm|deg)$/, '')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function templateValue(value: TemplateParameter): string {
  return `${Array.isArray(value.value) ? value.value.join(' × ') : String(value.value)} ${value.unit}`;
}

export function sourceLink(source: TemplateSource): string {
  // All input records used here predate this exact published source checkpoint.
  return `https://github.com/kudratsingh/rocket-twin/blob/07552bd1425dce4cf0b47af56c70b44a9500625e/${source.path}`;
}
