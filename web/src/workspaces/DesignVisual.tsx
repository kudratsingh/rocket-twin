import { useId, useState } from 'react';
import type { ReactNode } from 'react';
import { OrthographicDesign } from '../design/OrthographicDesign';
import { useInspection } from '../store';
import type { InspectionDocument } from '../types';
import { useOpenInspectionDetails } from './InspectionWorkspace';
import { drawingShortcut } from './inspectionWorkflow';

/** Representation changes preserve shared selection and the mounted 3D camera. */
export function DesignVisual({
  vehicle,
  meshView,
}: {
  vehicle: InspectionDocument;
  meshView: ReactNode;
}) {
  const id = useId();
  const [representation, setRepresentation] = useState<'3d' | '2d'>(() =>
    vehicle.parts.some((part) => part.mesh_url) ? '3d' : '2d',
  );
  const selected = useInspection((s) => s.selectedId);
  const hiddenIds = useInspection((s) => s.hiddenIds);
  const select = useInspection((s) => s.select);
  const openDetails = useOpenInspectionDetails();
  const selectedPart = vehicle.parts.find((part) => part.id === selected);
  const availableMeshes = vehicle.parts.filter((part) => !!part.mesh_url).length;
  return (
    <section
      className="research-design-visual"
      data-representation={representation}
      aria-label="Design representations"
      onKeyDown={(event) => {
        // Drawing controls own these keys; do not command the retained, hidden 3D camera.
        if (representation !== '2d' || event.ctrlKey || event.metaKey || event.altKey) return;
        if (
          event.target instanceof HTMLElement &&
          (['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target.tagName) ||
            event.target.isContentEditable)
        )
          return;
        const action = drawingShortcut(event.key);
        if (!action) return;
        event.preventDefault();
        event.stopPropagation();
        if (action !== 'unsupported')
          event.currentTarget
            .querySelector<HTMLButtonElement>(`[data-inspection-action="${action}"]`)
            ?.click();
      }}
    >
      <div className="research-representation-controls" aria-label="Drawing representation">
        <button
          type="button"
          aria-controls={`${id}-3d`}
          aria-pressed={representation === '3d'}
          onClick={() => setRepresentation('3d')}
        >
          3D recorded geometry
        </button>
        <button
          type="button"
          aria-controls={`${id}-2d`}
          aria-pressed={representation === '2d'}
          onClick={() => setRepresentation('2d')}
        >
          2D source dimensions
        </button>
        <span>
          {vehicle.label || vehicle.name || vehicle.id} ·{' '}
          {availableMeshes
            ? `${availableMeshes} recorded component meshes`
            : 'No recorded component meshes'}
        </span>
      </div>
      {selectedPart && (
        <div className="research-selection-summary" aria-live="polite">
          <div>
            <strong>{selectedPart.name || selectedPart.id}</strong>
            <p>
              {selectedPart.function || selectedPart.engineering?.function || selectedPart.learn}
            </p>
            <span>
              {selectedPart.material} ·{' '}
              {selectedPart.mesh_url
                ? 'Recorded component mesh'
                : 'No recorded 3D mesh for this component'}
              {hiddenIds.includes(selectedPart.id) ? ' · currently hidden' : ''}
            </span>
          </div>
          {openDetails && (
            <button type="button" onClick={openDetails}>
              Open selected component details
            </button>
          )}
        </div>
      )}
      <div id={`${id}-3d`} className="research-representation" hidden={representation !== '3d'}>
        {meshView}
      </div>
      <div id={`${id}-2d`} className="research-representation" hidden={representation !== '2d'}>
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
