import { lazy, Suspense, useLayoutEffect, useRef, useState } from 'react';
import type { InspectionDocument, Part } from '../types';
import { partName } from '../format';
import { componentDepthAccess } from './componentDepthAdmission';
import './componentDepthAccess.css';

const HighGPcbReference3D = lazy(() => import('./HighGPcbReference3D'));
const MechanicalReference = lazy(() =>
  import('./Rp1MechanicalReference3D').then((module) => ({
    default: module.Rp1MechanicalReference3D,
  })),
);

export default function ComponentDepthAccess({
  vehicle,
  part,
}: {
  vehicle: InspectionDocument;
  part: Part;
}) {
  const access = componentDepthAccess(vehicle, part);
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const [opened, setOpened] = useState(false);
  useLayoutEffect(() => {
    dialog.current?.close();
    setOpened(false);
  }, [vehicle, part]);
  function close() {
    dialog.current?.close();
    setOpened(false);
    trigger.current?.focus();
  }
  if (!access.available) return <p className="small muted">{access.reason}</p>;
  return (
    <section className="component-depth-access" aria-label="Detailed component structure">
      <h3>Inside the component</h3>
      <p>
        {access.kind === 'pcb'
          ? 'Explore the actual manufacturer pads, copper routes, holes and source footprints.'
          : 'Separate and select the existing fins, tabs, root gussets, slotted shell, tube and ring layers.'}
      </p>
      <button
        ref={trigger}
        type="button"
        onClick={() => {
          setOpened(true);
          dialog.current?.showModal();
        }}
      >
        {access.label}
      </button>
      <dialog
        ref={dialog}
        className="component-depth-dialog"
        onCancel={() => setOpened(false)}
        onClose={() => setOpened(false)}
        aria-label={`${partName(part)} detailed structure`}
      >
        <header>
          <div>
            <h2>{partName(part)} — detailed structure</h2>
            <p>
              {access.kind === 'pcb'
                ? 'Manufacturer XY layout · component heights remain unavailable'
                : 'Current source CAD · construction joints remain unqualified'}
            </p>
          </div>
          <button type="button" onClick={close}>
            Close component detail
          </button>
        </header>
        {opened && (
          <Suspense fallback={<p role="status">Loading component geometry and source layers…</p>}>
            {access.kind === 'pcb' ? (
              <HighGPcbReference3D
                partId={part.id}
                configurationId={vehicle.id}
                specificationSha256={String(vehicle.identity?.specification_sha256)}
              />
            ) : (
              <MechanicalReference
                configurationId={vehicle.id}
                specificationSha256={String(vehicle.identity?.specification_sha256)}
                inspectionGeometrySha256={String(vehicle.identity?.inspection_geometry_sha256)}
                initialPartId={part.id}
              />
            )}
          </Suspense>
        )}
      </dialog>
    </section>
  );
}
