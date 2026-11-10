import { Mesh } from 'three';
import type { Group, Material } from 'three';

/** One local scene's display-only ghost state; exported asset bytes are untouched. */
export function applyLocalPreviewGhost(scene: Group): () => void {
  const originals = new Map<
    Material,
    { opacity: number; transparent: boolean; depthWrite: boolean }
  >();
  scene.traverse((object) => {
    if (!(object instanceof Mesh)) return;
    for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
      if (originals.has(material)) continue;
      originals.set(material, {
        opacity: material.opacity,
        transparent: material.transparent,
        depthWrite: material.depthWrite,
      });
      material.opacity = Math.min(material.opacity, 0.2);
      material.transparent = true;
      material.depthWrite = false;
      material.needsUpdate = true;
    }
  });
  let restored = false;
  return () => {
    if (restored) return;
    restored = true;
    for (const [material, original] of originals) {
      Object.assign(material, original);
      material.needsUpdate = true;
    }
  };
}
