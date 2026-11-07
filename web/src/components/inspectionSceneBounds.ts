import { Box3, Vector3 } from 'three';
import type { Vector3Tuple } from '../types';

export type RecordedMeshBounds = { bounds: Box3; explodeOffset: Vector3Tuple };

/** Actual loaded mesh bounds only, including explicitly labeled inspection envelopes.
 * Source records without meshes never contribute inferred bounds or placeholder solids.
 */
export function inspectionSceneBounds(
  records: ReadonlyMap<string, RecordedMeshBounds>,
  partIds: readonly string[],
  exploded: number,
) {
  const bounds = new Box3();
  let available = 0;
  if (!Number.isFinite(exploded)) return { bounds, requested: partIds.length, available };
  for (const id of partIds) {
    const record = records.get(id);
    if (
      !record ||
      record.bounds.isEmpty() ||
      ![
        ...record.bounds.min.toArray(),
        ...record.bounds.max.toArray(),
        ...record.explodeOffset,
      ].every(Number.isFinite)
    )
      continue;
    bounds.union(
      record.bounds
        .clone()
        .translate(new Vector3(...record.explodeOffset).multiplyScalar(exploded)),
    );
    available += 1;
  }
  return { bounds, requested: partIds.length, available };
}
