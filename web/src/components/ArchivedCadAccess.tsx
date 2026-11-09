import { useLayoutEffect, useRef, useState } from 'react';
import type { InspectionDocument, Part } from '../types';
import {
  archivedCadAccess,
  fetchArchivedCad,
  fetchArchivedCadProvenance,
} from './archivedCadDownload';
import type { ArchivedCadDownload } from './archivedCadDownload';

function save(bytes: ArrayBuffer, filename: string, type: string) {
  const url = URL.createObjectURL(new Blob([bytes], { type }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Import this component lazily: the four-configuration registry is not needed for RP1. */
export function ArchivedCadAccess({
  vehicle,
  selectedPart = null,
}: {
  vehicle: InspectionDocument;
  selectedPart?: Part | null;
}) {
  const access = archivedCadAccess(vehicle, selectedPart);
  const request = useRef<AbortController | null>(null);
  const [feedback, setFeedback] = useState<{
    vehicle: InspectionDocument;
    selectedPart: Part | null;
    text: string;
    busy: boolean;
  } | null>(null);
  useLayoutEffect(
    () => () => {
      request.current?.abort();
      request.current = null;
    },
    [vehicle, selectedPart],
  );
  const current =
    feedback?.vehicle === vehicle && feedback.selectedPart === selectedPart ? feedback : null;
  async function download(file: ArchivedCadDownload | null) {
    if (!access.available) return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setFeedback({ vehicle, selectedPart, text: 'Checking recorded asset bytes…', busy: true });
    try {
      const bytes = file
        ? await fetchArchivedCad(file, controller.signal)
        : await fetchArchivedCadProvenance(access, controller.signal);
      if (controller.signal.aborted || request.current !== controller) return;
      save(
        bytes,
        file?.filename ?? access.provenanceFilename,
        file
          ? file.format === 'glb'
            ? 'model/gltf-binary'
            : file.format === 'step'
              ? 'application/step'
              : 'model/stl'
          : 'application/json',
      );
      setFeedback({
        vehicle,
        selectedPart,
        text: 'Recorded hash verified; browser download requested.',
        busy: false,
      });
    } catch (error) {
      if (controller.signal.aborted || request.current !== controller) return;
      setFeedback({
        vehicle,
        selectedPart,
        text: `Download unavailable: ${String(error)}`,
        busy: false,
      });
    }
  }
  return (
    <section aria-label="Archived CAD downloads">
      <h3>Recorded configuration files</h3>
      {access.available ? (
        <>
          <p>
            <strong>{access.label}</strong> · Source role: {access.sourceRole.replaceAll('_', ' ')}
          </p>
          <p>
            {access.designStatus}. {access.description}
          </p>
          <ul>
            {access.files.map((file) => (
              <li key={file.format}>
                <button type="button" disabled={current?.busy} onClick={() => void download(file)}>
                  Download recorded {file.format.toUpperCase()}
                </button>
                <p>
                  {file.units === 'm'
                    ? 'Metres'
                    : file.format === 'stl'
                      ? 'Recorded producer: millimetres'
                      : 'Millimetres'}{' '}
                  · {file.frame}
                </p>
              </li>
            ))}
          </ul>
          <button type="button" disabled={current?.busy} onClick={() => void download(null)}>
            Download recorded CAD provenance JSON
          </button>
          <details>
            <summary>File formats, coordinates and model limits</summary>
            <p>
              Existing archived or preliminary model files; manufactured is a source-role label, not
              proof of built hardware. Byte identity is checked; geometry has not received a new CAD
              readback or engineering qualification. Downloads do not authorize manufacturing,
              physical work or flight.
            </p>
            <p>
              GLB is a 3D viewing mesh. STEP exchanges solid geometry with computer-aided design
              (CAD) tools. STL stores surface triangles for printing tools; it does not record
              units.
            </p>
            {selectedPart ? (
              <p>
                Part STEP is local CAD, before assembly placement; it differs from RP1’s placed
                STEP. STL does not encode units; its recorded producer used CAD millimetres. It may
                be print-oriented or bed-packed and is not installed assembly geometry.
              </p>
            ) : (
              <p>
                Assembly STEP retains placed CAD coordinates in millimetres. Assembly STL is
                unavailable in the recorded export.
              </p>
            )}
          </details>
        </>
      ) : (
        <p>Unavailable: {access.reason}</p>
      )}
      {current && <p role="status">{current.text}</p>}
    </section>
  );
}

export default ArchivedCadAccess;
