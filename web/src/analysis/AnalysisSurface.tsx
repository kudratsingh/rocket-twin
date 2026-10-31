import { useEffect, useMemo } from 'react';
import {
  BufferGeometry,
  Color,
  DoubleSide,
  Float32BufferAttribute,
  Matrix4,
  Plane,
  Vector3,
} from 'three';
import { useInspection } from '../store';
import { displayScalar, fieldColor } from './display';
import type { AnalysisField, AnalysisPayload } from './types';

export function AnalysisSurface({
  field,
  payload,
  frame,
  minimum,
  maximum,
  outline,
}: {
  field: AnalysisField;
  payload: AnalysisPayload;
  frame: number;
  minimum: number;
  maximum: number;
  outline: boolean;
}) {
  const select = useInspection((s) => s.select);
  const hover = useInspection((s) => s.hover);
  const hidden = useInspection((s) => s.hiddenIds.includes(field.part_ids[0]));
  const section = useInspection((s) => s.section);
  const planes = useMemo(() => [new Plane(new Vector3(-1, 0, 0), 0)], []);
  const geometry = useMemo(() => {
    const mesh = payload.analysis_mesh!;
    const registration = new Matrix4().fromArray(field.registration!.matrix.flat()).transpose();
    const nodes = new Map(
      mesh.nodes.map((node, index) => [
        node.id,
        { index, point: new Vector3(...node.xyz_mm).applyMatrix4(registration) },
      ]),
    );
    const values = payload.values[frame];
    const positions: number[] = [],
      colors: number[] = [];
    // S6 midside nodes preserve the solver shell topology. Each element is
    // displayed as four triangles, without merging element discontinuities.
    for (const [elementIndex, element] of mesh.elements.entries()) {
      const triangles = [
        [0, 3, 5],
        [3, 1, 4],
        [5, 4, 2],
        [3, 4, 5],
      ];
      for (const triangle of triangles) {
        const vertices = triangle.map((i) => nodes.get(element.nodes[i]));
        if (vertices.some((vertex) => !vertex)) continue;
        for (const vertex of vertices) {
          const value = values[field.association === 'node' ? vertex!.index : elementIndex];
          const color = new Color(
            value == null
              ? '#4d5c63'
              : fieldColor(displayScalar(value, field.quantity), minimum, maximum),
          );
          positions.push(...vertex!.point.toArray());
          colors.push(color.r, color.g, color.b);
        }
      }
    }
    const result = new BufferGeometry();
    result.setAttribute('position', new Float32BufferAttribute(positions, 3));
    result.setAttribute('color', new Float32BufferAttribute(colors, 3));
    result.computeVertexNormals();
    return result;
  }, [field, payload, frame, minimum, maximum]);
  useEffect(() => () => geometry.dispose(), [geometry]);
  if (hidden) return null;
  return (
    <group
      onClick={(event) => {
        event.stopPropagation();
        select(field.part_ids[0]);
      }}
      onPointerOver={(event) => {
        event.stopPropagation();
        hover(field.part_ids[0]);
      }}
      onPointerOut={() => hover(null)}
    >
      <mesh geometry={geometry} renderOrder={5}>
        <meshBasicMaterial
          vertexColors
          side={DoubleSide}
          clippingPlanes={section ? planes : []}
          polygonOffset
          polygonOffsetFactor={-2}
        />
      </mesh>
      {outline && (
        <mesh geometry={geometry} renderOrder={6}>
          <meshBasicMaterial
            color="#d5e4e7"
            transparent
            opacity={0.25}
            wireframe
            side={DoubleSide}
            clippingPlanes={section ? planes : []}
          />
        </mesh>
      )}
    </group>
  );
}
