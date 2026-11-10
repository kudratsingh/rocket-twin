import manifest from '../../../docs/studies/frontend-template-bank-20261109/geometry.json';
import admission from '../../../docs/studies/frontend-template-bank-20261109/registry-admission.json';
import type { PartTemplate, TemplateRegistry } from './templateBank';

export interface TemplateAsset {
  url: string;
  sha256: string;
  bytes: number;
}
export interface TemplateRepresentation {
  template_id: string;
  template_revision_sha256: string;
  representation_status: string;
  bounds_m: { min: [number, number, number]; max: [number, number, number] };
  step: TemplateAsset;
  glb: TemplateAsset;
}

export function localTemplateRepresentation(
  recipe: PartTemplate,
  registry: TemplateRegistry,
): TemplateRepresentation | null {
  if (
    !recipe.geometry.local_recipe_supported ||
    manifest.configuration_id !== registry.configuration_id ||
    manifest.specification_sha256 !== registry.identity.specification.sha256 ||
    manifest.registry.revision_sha256 !== registry.revision_sha256 ||
    manifest.registry.prepared_sha256 !== admission.prepared_sha256
  )
    return null;
  const row = manifest.representations.find((item) => item.template_id === recipe.id);
  if (
    !row ||
    row.template_revision_sha256 !== recipe.revision_sha256 ||
    row.representation_status !== 'source_nominal_local_only'
  )
    return null;
  if (row.bounds_m.min.length !== 3 || row.bounds_m.max.length !== 3) return null;
  return {
    ...row,
    bounds_m: {
      min: [row.bounds_m.min[0], row.bounds_m.min[1], row.bounds_m.min[2]],
      max: [row.bounds_m.max[0], row.bounds_m.max[1], row.bounds_m.max[2]],
    },
  };
}

/** Download exactly the registered asset; camera and display transforms never enter this path. */
export async function verifiedTemplateAsset(
  asset: TemplateAsset,
  signal?: AbortSignal,
  request: typeof fetch = fetch,
): Promise<ArrayBuffer> {
  if (
    !/^\/engineering-workbench\/rp1-part-templates-geometry\/[a-z0-9-]+\.(glb|step)$/.test(
      asset.url,
    ) ||
    !/^[a-f0-9]{64}$/.test(asset.sha256) ||
    !Number.isSafeInteger(asset.bytes) ||
    asset.bytes <= 0
  )
    throw new Error('Local template asset registration is invalid.');
  const response = await request(asset.url, { signal });
  if (!response.ok) throw new Error(`Local template asset unavailable (${response.status}).`);
  const bytes = await response.arrayBuffer();
  const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
    .map((n) => n.toString(16).padStart(2, '0'))
    .join('');
  if (bytes.byteLength !== asset.bytes || digest !== asset.sha256)
    throw new Error('Local template asset bytes differ from the registered CAD.');
  return bytes;
}
