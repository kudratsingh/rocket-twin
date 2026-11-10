import { Html, Line } from '@react-three/drei';
import { DoubleSide } from 'three';
import {
  admitReferenceDefinition,
  DATUM_FEATURE_IDS,
  DATUM_LABELS,
  referenceDatumGeometry,
  type DatumFeatureId,
  type ReferenceDefinition,
} from './referenceDatumGeometry';
import './referenceDatumGuide.css';

export interface ReferenceDatumProps {
  definition: ReferenceDefinition;
  selectedFeature: DatumFeatureId | null;
  onSelect: (feature: DatumFeatureId | null) => void;
}
function featureDescription(definition: ReferenceDefinition, id: DatumFeatureId): string {
  const feature = definition.analytic_features.find((row) => row.id === id)!;
  if (feature.kind === 'analytic_axis')
    return `+CAD Z, ${feature.axial_range_mm[0]}–${feature.axial_range_mm[1]} mm from front center`;
  if (feature.kind === 'analytic_cylinder')
    return `Radius ${feature.radius_mm} mm; axial range ${feature.axial_range_mm[0]}–${feature.axial_range_mm[1]} mm`;
  return `CAD Z=${feature.origin_mm[2]} mm; annular radii ${feature.radial_range_mm[0]}–${feature.radial_range_mm[1]} mm`;
}
/** Standalone DOM list. The parent owns definition loading and selection state. */
export default function ReferenceDatumGuide({
  definition: raw,
  selectedFeature,
  onSelect,
}: ReferenceDatumProps) {
  const definition = admitReferenceDefinition(raw);
  if (!definition)
    return (
      <p role="alert" className="reference-datum-guide">
        Analytic datum guides unavailable: reference source, revision or frame differs.
      </p>
    );
  const selected = referenceDatumGeometry(definition, selectedFeature);
  return (
    <section className="reference-datum-guide" aria-label="Analytic nominal reference datums">
      <h4>Analytic nominal datums</h4>
      <div
        className="reference-datum-guide__choices"
        role="group"
        aria-label="Select analytic reference feature"
      >
        {DATUM_FEATURE_IDS.map((id) => (
          <button
            type="button"
            key={id}
            aria-pressed={selected?.feature.id === id}
            onClick={() => onSelect(id)}
          >
            {DATUM_LABELS[id]}
          </button>
        ))}
        <button type="button" disabled={selectedFeature === null} onClick={() => onSelect(null)}>
          Clear datum guide
        </button>
      </div>
      {selected ? (
        <p role="status">
          <strong>{DATUM_LABELS[selected.feature.id]}:</strong>{' '}
          {featureDescription(definition, selected.feature.id)}.
        </p>
      ) : (
        <p role="status">No known analytic datum selected.</p>
      )}
      <details>
        <summary>Source, coordinate frame and limits</summary>
        <p>
          Parameter-derived guides for {definition.name}. These are analytic references, not
          extracted kernel faces or mesh triangle IDs. Selection changes the guide only.
        </p>
        <p>
          STEP: millimetres, local front center, +Z aft. Viewer: metres; [X,Y,Z] = [cadX/1000,
          −cadZ/1000, cadY/1000]. Both plane normals use the arbitrary positive local-axis
          convention, not kernel or outward face normals.
        </p>
        <p className="reference-datum-guide__notice">{definition.identity_limit}</p>
        <p>
          No installed transform, physical mating, accepted tolerance or strength is available. Face
          IDs, triangle IDs, tolerance, mass, cost and inertia remain unavailable (null).
          Add-instance, Connect, simulation, engineering, physical and flight readiness remain
          false.
        </p>
      </details>
    </section>
  );
}

/** Optional child of the parent's existing R3F Canvas, beside verified local CAD.
 * No Canvas, loader, camera, controls, model/material edits or automatic actions.
 * Geometry ignores raycasting; only the selected HTML callout accepts clicks.
 */
export function ReferenceDatumOverlay({
  definition,
  selectedFeature,
  onSelect,
}: ReferenceDatumProps) {
  const guide = referenceDatumGeometry(definition, selectedFeature);
  if (!guide) return null;
  return (
    <group name={`analytic-datum:${definition.id}:${guide.feature.id}`}>
      {guide.lines.map((points, index) => (
        <Line
          key={index}
          points={points}
          color="#8fc8ff"
          lineWidth={1.5}
          transparent
          opacity={0.9}
          depthWrite={false}
          raycast={() => undefined}
        />
      ))}
      {guide.annulus && (
        <mesh
          position={guide.annulus.center}
          rotation={[Math.PI / 2, 0, 0]}
          raycast={() => undefined}
        >
          <ringGeometry args={[guide.annulus.innerRadiusM, guide.annulus.outerRadiusM, 96]} />
          <meshBasicMaterial
            color="#8fc8ff"
            transparent
            opacity={0.18}
            depthWrite={false}
            side={DoubleSide}
          />
        </mesh>
      )}
      <Html position={guide.callout} style={{ pointerEvents: 'none' }}>
        <button
          type="button"
          className="reference-datum-callout"
          aria-pressed="true"
          onPointerDown={(event) => event.stopPropagation()}
          onClick={(event) => {
            event.stopPropagation();
            onSelect(guide.feature.id);
          }}
          title="Analytic nominal reference only; use the datum list to select another guide"
        >
          {DATUM_LABELS[guide.feature.id]} · analytic
        </button>
      </Html>
    </group>
  );
}
