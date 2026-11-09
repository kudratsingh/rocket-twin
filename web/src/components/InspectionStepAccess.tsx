import { useLayoutEffect, useRef, useState } from 'react';
import type { InspectionDocument, Part } from '../types';
import {
  fetchInspectionStep,
  fetchInspectionStepProvenance,
  inspectionStepAccess,
} from './inspectionStepDownload';

function save(bytes: ArrayBuffer, filename: string, type: string) {
  const url = URL.createObjectURL(new Blob([bytes], { type }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Registered existing source reconstruction only; static bytes require explicit preparation. */
export function InspectionStepAccess({
  vehicle,
  selectedPart = null,
}: {
  vehicle: InspectionDocument;
  selectedPart?: Part | null;
}) {
  const access = inspectionStepAccess(vehicle, selectedPart);
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
  async function download(kind: 'step' | 'provenance') {
    if (!access.available) return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setFeedback({
      vehicle,
      selectedPart,
      text: 'Checking registered inspection STEP/provenance bytes…',
      busy: true,
    });
    try {
      const bytes = await (kind === 'step' ? fetchInspectionStep : fetchInspectionStepProvenance)(
        access,
        controller.signal,
      );
      if (controller.signal.aborted || request.current !== controller) return;
      save(
        bytes,
        kind === 'step' ? access.filename : access.provenanceFilename,
        kind === 'step' ? 'application/step' : 'application/json',
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
    <section aria-label="Inspection STEP downloads">
      <h3>Inspection CAD · STEP</h3>
      {access.available ? (
        <>
          <p>
            {access.label} · {access.maturity.replaceAll('_', ' ')}
          </p>
          <p>
            STEP is a solid-geometry exchange file for CAD tools. This source reconstruction uses
            CAD millimetres. Origin at nose tip; Z increases aft. Source assembly placement is
            retained, without display separation.
          </p>
          <p>
            Inspection geometry and envelopes are not manufacturing-ready or installed-qualified.
            Missing hardware details and all engineering/flight gates remain open.
          </p>
          <button type="button" disabled={current?.busy} onClick={() => void download('step')}>
            Download inspection STEP
          </button>{' '}
          <button
            type="button"
            disabled={current?.busy}
            onClick={() => void download('provenance')}
          >
            Download STEP provenance JSON
          </button>
          <details>
            <summary>STEP frame and source limits</summary>
            <p>{access.cadFrame}</p>
            <p>{access.viewerMapping}</p>
            <ul>
              {access.limitations.map((limit) => (
                <li key={limit}>{limit}</li>
              ))}
            </ul>
            <p>
              Expected STEP SHA-256:{' '}
              <code style={{ overflowWrap: 'anywhere' }}>{access.assetSha256}</code>
            </p>
          </details>
        </>
      ) : (
        <p>Unavailable: {access.reason}</p>
      )}
      {current && <p role="status">{current.text}</p>}
    </section>
  );
}
