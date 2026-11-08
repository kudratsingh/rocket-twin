import type { InspectionDocument } from '../types';
export interface InteriorSnapshot {
  hiddenIds: string[];
  exploded: number;
  section: boolean;
  ghostShell: boolean;
}
export function interiorShellIds(vehicle: InspectionDocument): string[] {
  return vehicle.parts.filter((p) => p.outer_body || p.nose || p.type === 'nose').map((p) => p.id);
}
/** Recorded display visibility only; not a removal or structural-clearance calculation. */
export function interiorHiddenIds(
  vehicle: InspectionDocument,
  before: InteriorSnapshot,
  revealIds: string[] = [],
): string[] {
  const shells = interiorShellIds(vehicle);
  const reveal = new Set(revealIds);
  return [...new Set([...before.hiddenIds.filter((id) => !reveal.has(id)), ...shells])];
}
