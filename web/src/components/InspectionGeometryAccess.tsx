import { useLayoutEffect, useRef, useState } from 'react';
import type { InspectionDocument, Part } from '../types';
import { fetchInspectionGeometry, inspectionGeometryAccess } from './inspectionGeometryDownload.ts';

function save(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** A selected source part, or null for the registered whole inspection assembly. */
export function InspectionGeometryAccess({
  vehicle,
  selectedPart = null,
}: {
  vehicle: InspectionDocument;
  selectedPart?: Part | null;
}) {
  const access = inspectionGeometryAccess(vehicle, selectedPart);
  const request = useRef<AbortController | null>(null);
  const [feedback, setFeedback] = useState<{
    key: string;
    text: string;
    busy: boolean;
    vehicle: InspectionDocument;
    selectedPart: Part | null;
  } | null>(null);
  const key = access.available
    ? access.filename
    : `${vehicle.id}:${selectedPart?.id}:${access.reason}`;
  useLayoutEffect(
    () => () => {
      request.current?.abort();
      request.current = null;
    },
    [vehicle, selectedPart],
  );
  const current =
    feedback?.key === key && feedback.vehicle === vehicle && feedback.selectedPart === selectedPart
      ? feedback
      : null;
  async function downloadMesh() {
    if (!access.available) return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setFeedback({
      key,
      vehicle,
      selectedPart,
      text: 'Checking the recorded mesh bytes…',
      busy: true,
    });
    try {
      const bytes = await fetchInspectionGeometry(access, controller.signal);
      if (controller.signal.aborted || request.current !== controller) return;
      save(new Blob([bytes], { type: 'model/gltf-binary' }), access.filename);
      setFeedback({
        key,
        vehicle,
        selectedPart,
        text: 'Mesh hash verified; browser download requested.',
        busy: false,
      });
    } catch (error) {
      if (controller.signal.aborted || request.current !== controller) return;
      setFeedback({
        key,
        vehicle,
        selectedPart,
        text: `Download unavailable: ${String(error)}`,
        busy: false,
      });
    }
  }
  return (
    <section aria-label="Inspection geometry downloads">
      <h3>Inspection geometry files</h3>
      {access.available ? (
        <>
          <p>
            {access.label} · {access.maturity.replaceAll('_', ' ')}
          </p>
          <p>
            GLB is a 3D mesh file for viewing. This frozen inspection mesh uses metres and is
            already placed in recorded assembly coordinates. Ideal solids and envelopes are not
            manufacturing CAD or installed-fit approval. Manufacturing STL is unavailable;
            separately registered inspection STEP files are listed below when available. Optional
            detail and current display transforms are excluded.
          </p>
          <button type="button" disabled={current?.busy} onClick={() => void downloadMesh()}>
            Download inspection GLB
          </button>{' '}
          <button
            type="button"
            onClick={() =>
              save(
                new Blob([JSON.stringify(access.provenance, null, 2) + '\n'], {
                  type: 'application/json',
                }),
                access.filename.replace(/\.glb$/, '.provenance.json'),
              )
            }
          >
            Download geometry provenance JSON
          </button>
          <p>
            <small>
              Expected mesh SHA-256:{' '}
              <code style={{ overflowWrap: 'anywhere' }}>{access.assetSha256}</code>
            </small>
          </p>
        </>
      ) : (
        <p>Unavailable: {access.reason}</p>
      )}
      {current && <p role="status">{current.text}</p>}
    </section>
  );
}
