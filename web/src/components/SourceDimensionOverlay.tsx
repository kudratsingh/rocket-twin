import { Line } from '@react-three/drei';
import { SceneLabel } from './SceneLabel';
import { sourceDimensionPositions } from './sourceDimensionPositions';
import type { SourceDimensionPositionsInput } from './sourceDimensionPositions';

const guideColor = '#9de8ec';
const guideMetadata = { annotationOnly: true, contributesGeometryBounds: false };

/**
 * Display-only guides from an upstream admitted RP1 detail packet.
 * Mount outside translated PartMesh groups: endpoints already include their display offset.
 * Never register these decorations with the viewer's loaded-part fit bounds.
 */
export function SourceDimensionOverlay(props: SourceDimensionPositionsInput) {
  const dimensions = sourceDimensionPositions(props);
  if (!dimensions.length) return null;
  return (
    <group name="source-dimension-guides" userData={guideMetadata}>
      {dimensions.map((dimension) => (
        <group key={`${dimension.partId}:${dimension.id}`} userData={guideMetadata}>
          <Line
            points={[dimension.from, dimension.to]}
            color={guideColor}
            lineWidth={1.5}
            depthTest={false}
            depthWrite={false}
            clippingPlanes={[]}
            renderOrder={20}
            raycast={() => {}}
            userData={guideMetadata}
          />
          {[dimension.from, dimension.to].map((position, index) => (
            <mesh
              key={index}
              position={position}
              renderOrder={21}
              raycast={() => {}}
              userData={guideMetadata}
            >
              {/* Fixed visual endpoint marks; their size does not encode a source dimension. */}
              <sphereGeometry args={[0.00055, 8, 6]} />
              <meshBasicMaterial
                color={guideColor}
                depthTest={false}
                depthWrite={false}
                clippingPlanes={[]}
              />
            </mesh>
          ))}
          <SceneLabel
            position={dimension.midpoint}
            center
            zIndexRange={[13, 0]}
            pointerEvents="none"
            contentClassName="source-dimension-label"
            title={dimension.title}
            lines={[
              { text: dimension.label, tag: 'strong' },
              { text: 'Source nominal · view guide' },
            ]}
          />
        </group>
      ))}
    </group>
  );
}
