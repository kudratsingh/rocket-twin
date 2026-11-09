import type { Vector3Tuple } from '../types';
import type { Rp1DetailAnnotation } from './rp1Detail';

export interface SourceDimensionPositionsInput {
  /** Must already have passed the exact active source/geometry admission in rp1Detail. */
  annotations: readonly Rp1DetailAnnotation[] | null | undefined;
  selectedIds: readonly string[];
  visibleIds: readonly string[];
  /** Final per-part display displacement, in viewer metres; never multiply by explode again. */
  displayOffsets: ReadonlyMap<string, Vector3Tuple | null | undefined>;
}

export interface SourceDimensionPosition {
  id: string;
  partId: string;
  from: Vector3Tuple;
  to: Vector3Tuple;
  midpoint: Vector3Tuple;
  label: string;
  title: string;
  annotationOnly: true;
  contributesGeometryBounds: false;
}

function finiteVector(value: unknown): value is Vector3Tuple {
  return (
    Array.isArray(value) &&
    value.length === 3 &&
    value.every((v) => typeof v === 'number' && Number.isFinite(v))
  );
}

/**
 * Move recorded guide endpoints with their own selected visible part exactly once.
 * Source admission is upstream; this helper checks display usability, not source identity.
 * No value is measured from a mesh, segment length, pixels or an exploded separation.
 */
export function sourceDimensionPositions({
  annotations,
  selectedIds,
  visibleIds,
  displayOffsets,
}: SourceDimensionPositionsInput): SourceDimensionPosition[] {
  if (!Array.isArray(annotations) || !selectedIds.length || !visibleIds.length) return [];
  const selected = new Set(selectedIds),
    visible = new Set(visibleIds);
  const result: SourceDimensionPosition[] = [];
  for (const annotation of annotations as readonly Rp1DetailAnnotation[]) {
    if (
      !annotation ||
      !selected.has(annotation.partId) ||
      !visible.has(annotation.partId) ||
      typeof annotation.id !== 'string' ||
      !annotation.id ||
      typeof annotation.label !== 'string' ||
      !annotation.label ||
      annotation.units !== 'mm' ||
      annotation.annotationOnly !== true ||
      typeof annotation.value !== 'number' ||
      !Number.isFinite(annotation.value) ||
      annotation.value <= 0 ||
      !finiteVector(annotation.from) ||
      !finiteVector(annotation.to) ||
      annotation.from.every((v, index) => v === annotation.to[index]) ||
      !annotation.source ||
      typeof annotation.source.path !== 'string' ||
      !annotation.source.path ||
      typeof annotation.source.locator !== 'string' ||
      !annotation.source.locator ||
      typeof annotation.source.sha256 !== 'string' ||
      !/^[a-f0-9]{64}$/.test(annotation.source.sha256)
    )
      continue;
    const offset = displayOffsets.get(annotation.partId) ?? [0, 0, 0];
    if (!finiteVector(offset)) continue;
    const from = annotation.from.map((v, index) => v + offset[index]) as Vector3Tuple;
    const to = annotation.to.map((v, index) => v + offset[index]) as Vector3Tuple;
    if (!finiteVector(from) || !finiteVector(to)) continue;
    const midpoint = from.map((v, index) => v / 2 + to[index] / 2) as Vector3Tuple;
    result.push({
      id: annotation.id,
      partId: annotation.partId,
      from,
      to,
      midpoint,
      label: `${annotation.label} · ${Number(annotation.value.toPrecision(12))} mm`,
      title: [
        `Part: ${annotation.partId}`,
        `Recorded nominal source dimension: ${Number(annotation.value.toPrecision(12))} mm`,
        `Source: ${annotation.source.path}`,
        `Locator: ${annotation.source.locator}`,
        `SHA-256: ${annotation.source.sha256}`,
        'Display guide; may remain visible across a section cut. Not an exposed solid or an installed measurement.',
      ].join('\n'),
      annotationOnly: true,
      contributesGeometryBounds: false,
    });
  }
  return result;
}
