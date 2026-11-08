import type { InspectionDocument, Part } from '../types';
import { getRp1Presentation } from './rp1Breakdown.ts';

export interface PresentationGroup {
  id: string;
  label: string;
  description: string;
  part_ids: string[];
}
const object = (value: unknown): Record<string, unknown> =>
  value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};

/** Presentation grouping is not a structural attachment claim. Refuse incomplete/foreign maps. */
export function presentationGroups(document?: InspectionDocument): PresentationGroup[] {
  if (!document) return [];
  const presentation = getRp1Presentation(document);
  if (!presentation) return [];
  if (presentation.groups.some((group) => typeof object(group).description !== 'string')) return [];
  return presentation.groups.map((group) => ({
    id: group.id,
    label: group.label,
    part_ids: group.part_ids,
    description: String(object(group).description),
  }));
}
export function partPresentation(part: Part) {
  return object(object(part.representation).presentation);
}
export function representationLabel(part: Part): string {
  const maturity = partPresentation(part).maturity ?? object(part.representation).maturity;
  const labels: Record<string, string> = {
    source_dimensioned: 'Dimensioned display shape',
    simplified_envelope: 'Simplified envelope',
    mass_allowance: 'Mass/process allowance — no separate solid',
    missing_geometry: 'Geometry unavailable',
  };
  return typeof maturity === 'string' && labels[maturity]
    ? labels[maturity]
    : part.mesh_url
      ? 'Display shape — see source basis'
      : 'No display solid';
}
export function recordedQuantity(part: Part): string | null {
  const quantity = object(partPresentation(part).quantity);
  return typeof quantity.value === 'number' && typeof quantity.unit === 'string'
    ? `${quantity.value} ${quantity.unit} (source recorded)`
    : null;
}
