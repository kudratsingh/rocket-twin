import { useState } from 'react';
import type { ReactNode } from 'react';
import { OrthographicDesign } from '../design/OrthographicDesign';
import { useInspection } from '../store';
import type { InspectionDocument } from '../types';

/** Representation changes preserve shared selection and the mounted 3D camera. */
export function DesignVisual({
  vehicle,
  meshView,
}: {
  vehicle: InspectionDocument;
  meshView: ReactNode;
}) {
  const [representation, setRepresentation] = useState<'3d' | '2d'>('3d');
  const selected = useInspection((s) => s.selectedId);
  const hiddenIds = useInspection((s) => s.hiddenIds);
  const select = useInspection((s) => s.select);
  return (
    <section
      className="research-design-visual"
      aria-label="Design representations"
      onKeyDown={(event) => {
        // Drawing controls own these keys; do not command the retained, hidden 3D camera.
        if (representation === '2d' && ['f', 'r', 'e', 's'].includes(event.key.toLowerCase()))
          event.stopPropagation();
      }}
    >
      <div className="research-representation-controls" aria-label="Drawing representation">
        <button
          type="button"
          aria-pressed={representation === '3d'}
          onClick={() => setRepresentation('3d')}
        >
          3D recorded geometry
        </button>
        <button
          type="button"
          aria-pressed={representation === '2d'}
          onClick={() => setRepresentation('2d')}
        >
          2D source dimensions
        </button>
        <span>Same selected configuration; drawing maturity stays explicit.</span>
      </div>
      <div className="research-representation" hidden={representation !== '3d'}>
        {meshView}
      </div>
      <div className="research-representation" hidden={representation !== '2d'}>
        <OrthographicDesign
          vehicle={vehicle}
          selectedPartId={selected}
          onSelectPart={select}
          hiddenPartIds={hiddenIds}
          onRevealPart={(id) => {
            const state = useInspection.getState();
            if (state.hiddenIds.includes(id)) state.togglePart(id);
          }}
        />
      </div>
    </section>
  );
}
