import { lazy, Suspense, useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import type { InspectionDocument } from '../types';
import { displayValue, label } from '../format';
import { Rp1StudyComparisonView } from '../workbench/Rp1StudyComparison';
import {
  loadRp1Studies,
  RP1_SOURCE_ID,
  RP1_SOURCE_SHA256,
  type Rp1Studies,
} from '../workbench/rp1Studies';
import './designInspection.css';
const FinConstructionPreview = lazy(() => import('./FinConstructionPreview'));

/** Read-only evidence comparison. The mounted Design scene and inspection state never change. */
export function FinAlternatives({
  design,
  compact = false,
}: {
  design: InspectionDocument;
  compact?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [snapshot, setSnapshot] = useState<Rp1Studies | null>(null);
  const [error, setError] = useState('');
  const opener = useRef<HTMLButtonElement>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const title = useId();
  useEffect(() => {
    if (!open) return;
    const node = dialog.current;
    const returnTo = opener.current;
    node?.showModal();
    const controller = new AbortController();
    void loadRp1Studies(controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setSnapshot(value);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted)
          setError(reason instanceof Error ? reason.message : 'Alternative records unavailable.');
      });
    return () => {
      controller.abort();
      node?.close();
      returnTo?.focus();
    };
  }, [open]);
  if (design.id !== RP1_SOURCE_ID || design.identity?.specification_sha256 !== RP1_SOURCE_SHA256)
    return <p className="small muted">Fin alternatives unavailable for this exact design.</p>;
  const fin = design.parts.find((part) => part.id === 'fin_set');
  return (
    <>
      <button
        ref={opener}
        className="compare-fin-alternatives"
        onClick={() => {
          setError('');
          setOpen(true);
        }}
      >
        {compact ? 'Fin alternatives' : 'Compare fin alternatives'}
      </button>
      {open &&
        createPortal(
          <dialog
            ref={dialog}
            className="fin-alternatives-dialog"
            aria-labelledby={title}
            onCancel={(event) => {
              event.preventDefault();
              setOpen(false);
            }}
          >
            <header>
              <h2 id={title}>Fin alternatives — recorded studies</h2>
              <button onClick={() => setOpen(false)}>Return to the same Design selection</button>
            </header>
            <p>
              Read-only comparison. Your active RP1 source, selection, camera and visibility remain
              unchanged. None of these records is an approved installed fin construction.
            </p>
            {snapshot && !error && (
              <Suspense fallback={<p>Loading fin construction preview…</p>}>
                <FinConstructionPreview snapshot={snapshot} />
              </Suspense>
            )}
            <details className="fin-source-details">
              <summary>Current AD1 dimensions and recorded findings</summary>
              <section>
                <h3>Current AD1 v2 source definition</h3>
                <p>
                  <code>{RP1_SOURCE_ID}</code>
                </p>
                <p>
                  Frozen preliminary definition. Failed recorded fin-panel calculation; installed
                  joint movement, bond strength and flutter still need evidence. The display model
                  is not proof of strength.
                </p>
                {fin && (
                  <dl className="data-list">
                    {Object.entries(fin.dimensions || fin.geometry || {}).map(([key, value]) => (
                      <div key={key}>
                        <dt>{label(key)}</dt>
                        <dd>{displayValue(key, value)}</dd>
                      </div>
                    ))}
                  </dl>
                )}
                <p>
                  Specification mass:{' '}
                  {fin?.mass_kg == null
                    ? 'Unavailable'
                    : `${(fin.mass_kg * 1000).toFixed(3)} g (estimated)`}
                  . Source: <code>configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml</code> ·{' '}
                  <code>{RP1_SOURCE_SHA256}</code>.
                </p>
              </section>
            </details>
            <p>
              <strong>FP1 and FR1: finished 3D assemblies unavailable.</strong> The optional fin
              preview above is a separate source-dimensioned schematic. Relationship graphics are
              not spatial stress maps. Carbon-faced plywood FP1 and solid-carbon FR1 remain
              separate, unadopted studies.
            </p>
            {error ? (
              <p role="alert">{error} No alternative geometry or result is substituted.</p>
            ) : snapshot ? (
              <>
                <Rp1StudyComparisonView snapshot={snapshot} />
              </>
            ) : (
              <p role="status">Loading exact-source alternative records…</p>
            )}
          </dialog>,
          document.body,
        )}
    </>
  );
}
