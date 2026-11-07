import { Box3, Vector3 } from 'three';
import type { Vector3Tuple } from '../types';

export type RecordedMeshBounds = { bounds: Box3; explodeOffset: Vector3Tuple };

/** Actual loaded GLB bounds only. Never substitute YAML envelopes for absent meshes. */
export function inspectionSceneBounds(
  records: ReadonlyMap<string, RecordedMeshBounds>,
  partIds: readonly string[],
  exploded: number,
) {
  const bounds = new Box3();
  let available = 0;
  for (const id of partIds) {
    const record = records.get(id);
    if (!record || record.bounds.isEmpty()) continue;
    bounds.union(
      record.bounds
        .clone()
        .translate(new Vector3(...record.explodeOffset).multiplyScalar(exploded)),
    );
    available += 1;
  }
  return { bounds, requested: partIds.length, available };
}
