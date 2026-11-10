import {
  admitReferenceDefinition,
  cadPointToViewer,
  type DatumPoint,
  type ReferenceDefinition,
} from './referenceDatumGeometry';

export interface DisplayInstance {
  id: string;
  definition: ReferenceDefinition;
  translation_mm: DatumPoint;
}
export interface ArrangementBounds {
  min: DatumPoint;
  max: DatumPoint;
}
export const ARRANGEMENT_DISPLAY_FRAME = 'uninstalled-local-reference-arrangement';
function object(raw: unknown): raw is Record<string, unknown> {
  return raw !== null && typeof raw === 'object' && !Array.isArray(raw);
}
/** Display validation only; backend command/hash admission remains independent. */
export function admitArrangementDisplay(raw: unknown): DisplayInstance[] {
  if (!Array.isArray(raw) || raw.length > 2)
    throw new Error('Reference arrangement requires at most two exact local planning instances.');
  const ids = new Set<string>();
  const definitions = new Set<string>();
  for (const row of raw) {
    if (
      !object(row) ||
      Object.keys(row).length !== 3 ||
      typeof row.id !== 'string' ||
      !/^[a-zA-Z0-9:_-]{1,100}$/.test(row.id) ||
      ids.has(row.id) ||
      !admitReferenceDefinition(row.definition) ||
      !Array.isArray(row.translation_mm) ||
      row.translation_mm.length !== 3 ||
      row.translation_mm.some(
        (value) =>
          typeof value !== 'number' ||
          !Number.isFinite(value) ||
          Math.abs(value) > 500 ||
          Number(value.toFixed(3)) !== value,
      )
    )
      throw new Error(
        'Reference arrangement source, frame, identity or bounded translation differs; no geometry admitted.',
      );
    const definition = row.definition as unknown as ReferenceDefinition;
    if (definitions.has(definition.id))
      throw new Error('Only one planning instance of each exact local reference is supported.');
    ids.add(row.id);
    definitions.add(definition.id);
  }
  return raw as DisplayInstance[];
}
/** Millimetre planning translation only: fixed orientation and unit scale. */
export function arrangementTranslation(instance: DisplayInstance): DatumPoint {
  admitArrangementDisplay([instance]);
  return cadPointToViewer(instance.translation_mm);
}
export function arrangementInstanceBounds(instance: DisplayInstance): ArrangementBounds {
  const translation = arrangementTranslation(instance);
  const source = instance.definition.representation.bounds_m;
  return {
    min: source.min.map((value, axis) => value + translation[axis]) as DatumPoint,
    max: source.max.map((value, axis) => value + translation[axis]) as DatumPoint,
  };
}
/** Source-bound display bounds for framing/selection, never a physical fit result. */
export function arrangementDisplayBounds(raw: unknown): ArrangementBounds | null {
  const instances = admitArrangementDisplay(raw);
  if (!instances.length) return null;
  const bounds = instances.map(arrangementInstanceBounds);
  return {
    min: [0, 1, 2].map((axis) => Math.min(...bounds.map((row) => row.min[axis]))) as DatumPoint,
    max: [0, 1, 2].map((axis) => Math.max(...bounds.map((row) => row.max[axis]))) as DatumPoint,
  };
}
/** Excludes translation and selection so pose edits do not imply a camera reset. */
export function arrangementFramingIdentity(raw: unknown): string {
  return JSON.stringify(
    admitArrangementDisplay(raw)
      .map((row) => `${row.id}:${row.definition.id}:${row.definition.revision_sha256}`)
      .sort(),
  );
}
