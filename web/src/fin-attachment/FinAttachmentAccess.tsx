import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import type { InspectionDocument, Part } from '../types';
import {
  inspectionJointStepAccess,
  fetchInspectionStep,
  fetchInspectionStepProvenance,
} from '../components/inspectionStepDownload';
import { captureMainCamera, clearMainCamera, mainCameraKey } from './mainCameraCheckpoint';
import {
  finAttachmentHref,
  initialFinAttachmentState,
  openFinDrawingHref,
  parseFinAttachmentHref,
  finAttachmentSessionKey,
  parseFinAttachmentCameraSnapshot,
} from './finAttachmentState';
import type { FinAttachmentState, FinAttachmentRoute } from './finAttachmentState';
import './finAttachmentAccess.css';

const Inspector = lazy(() => import('./FinAttachmentInspector'));
export function navigateFinAttachment(next: string, replace = false) {
  if (next === `${location.pathname}${location.search}${location.hash}`) return;
  window.history[replace ? 'replaceState' : 'pushState'](null, '', next);
  window.dispatchEvent(new PopStateEvent('popstate'));
}
export function FinAttachmentTrigger({
  vehicle,
  part,
}: {
  vehicle: InspectionDocument;
  part: Part;
}) {
  if (!['fin_set', 'fin_tabs'].includes(part.id) || !inspectionJointStepAccess(vehicle).available)
    return null;
  return (
    <section aria-label="Fin attachment close-up">
      <button
        type="button"
        className="primary-button"
        onClick={() => {
          captureMainCamera(mainCameraKey(vehicle.id, vehicle.identity?.specification_sha256));
          const id = part.id as 'fin_set' | 'fin_tabs';
          navigateFinAttachment(
            finAttachmentHref(
              location.href,
              { ...initialFinAttachmentState, selectedPieceId: id },
              id,
            ),
          );
        }}
      >
        Inspect fin attachment
      </button>
      <p className="small">
        Open the same source CAD joint, real cut faces and recorded dimensions.
      </p>
    </section>
  );
}
function restoreState(route: FinAttachmentRoute): FinAttachmentState {
  try {
    const saved = JSON.parse(
      sessionStorage.getItem(finAttachmentSessionKey(route.originPartId)) || 'null',
    );
    return { ...route.state, camera: parseFinAttachmentCameraSnapshot(saved?.camera) };
  } catch {
    return route.state;
  }
}
function Opened({ vehicle, route }: { vehicle: InspectionDocument; route: FinAttachmentRoute }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [state, setState] = useState(() => restoreState(route));
  const latest = useRef(state);
  const [feedback, setFeedback] = useState('');
  const request = useRef<AbortController | null>(null);
  useEffect(() => {
    dialog.current?.showModal();
    return () => {
      request.current?.abort();
      const next = parseFinAttachmentHref(location.href);
      if (!next) clearMainCamera(mainCameraKey(vehicle.id, vehicle.identity?.specification_sha256));
    };
    // Preserve the actual main-scene checkpoint only for the exact Engineering round trip.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  function change(next: FinAttachmentState) {
    latest.current = next;
    setState(next);
    try {
      sessionStorage.setItem(
        finAttachmentSessionKey(route.originPartId),
        JSON.stringify({ camera: next.camera }),
      );
    } catch {
      /* Camera remains in memory if browser storage is disabled. */
    }
    navigateFinAttachment(finAttachmentHref(location.href, next, route.originPartId), true);
  }
  function close() {
    clearMainCamera(mainCameraKey(vehicle.id, vehicle.identity?.specification_sha256));
    const url = new URL(location.href);
    for (const key of [...url.searchParams.keys()])
      if (key === 'finJoint' || key.startsWith('joint')) url.searchParams.delete(key);
    url.searchParams.set('part', route.originPartId);
    navigateFinAttachment(`${url.pathname}${url.search}${url.hash}`);
  }
  async function download(provenance: boolean) {
    const access = inspectionJointStepAccess(vehicle);
    if (!access.available) {
      setFeedback(access.reason);
      return;
    }
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setFeedback('Verifying registered CAD bytes…');
    try {
      const bytes = await (provenance ? fetchInspectionStepProvenance : fetchInspectionStep)(
        access,
        controller.signal,
      );
      const url = URL.createObjectURL(
        new Blob([bytes], { type: provenance ? 'application/json' : 'application/step' }),
      );
      const a = document.createElement('a');
      a.href = url;
      a.download = provenance ? access.provenanceFilename : access.filename;
      a.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      setFeedback(
        provenance
          ? 'Registered provenance downloaded.'
          : 'Joint STEP downloaded: assembled CAD coordinates, millimetres; camera, cuts and visibility do not alter the file.',
      );
    } catch (reason) {
      if (!controller.signal.aborted)
        setFeedback(reason instanceof Error ? reason.message : 'Download unavailable.');
    }
  }
  return (
    <dialog
      ref={dialog}
      className="fin-attachment-dialog"
      aria-label="RP1 fin attachment inspector"
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
    >
      <header>
        <div>
          <h2>RP1 fin attachment</h2>
          <p>Frozen AD1 v2 · read-only inspection · engineering acceptance remains open</p>
        </div>
        <button type="button" onClick={close}>
          Return to rocket
        </button>
      </header>
      <Suspense fallback={<p role="status">Loading registered joint CAD…</p>}>
        <Inspector
          vehicle={vehicle}
          state={state}
          onChange={change}
          onOpenDrawing={(drawing) =>
            navigateFinAttachment(
              openFinDrawingHref(location.href, latest.current, route.originPartId, drawing),
            )
          }
          onDownloadStep={() => void download(false)}
          onDownloadProvenance={() => void download(true)}
        />
      </Suspense>
      {feedback && (
        <p className="fin-attachment-download-status" role="status">
          {feedback}
        </p>
      )}
    </dialog>
  );
}
export default function FinAttachmentAccess({
  vehicle,
  href,
}: {
  vehicle: InspectionDocument;
  href: string;
}) {
  const route = parseFinAttachmentHref(href);
  if (!route || !inspectionJointStepAccess(vehicle).available) return null;
  return <Opened key={`${vehicle.id}:${route.originPartId}`} vehicle={vehicle} route={route} />;
}
