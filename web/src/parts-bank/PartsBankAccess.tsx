import { lazy, Suspense, useLayoutEffect, useRef, useState } from 'react';
import type { InspectionDocument } from '../types';
import { useWorkspaceLayout } from '../workspaces/workspaceLayoutContext';
import './partsBankAccess.css';
import './templateBank.css';

const PartsBankPanel = lazy(() => import('./PartsBankPanel'));
const TemplateBankPanel = lazy(() => import('./TemplateBankPanel'));

/** The source assembly stays mounted while its read-only bank is open. */
export function PartsBankAccess({
  vehicle,
  onInspect,
}: {
  vehicle: InspectionDocument;
  onInspect: (partId: string) => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const [opened, setOpened] = useState(false);
  const [error, setError] = useState('');
  const [section, setSection] = useState<'source' | 'templates'>('source');
  const layout = useWorkspaceLayout();
  const available = vehicle.id === 'G80-F2-RP1-AD1-definition-v2';
  useLayoutEffect(() => {
    dialog.current?.close();
    setOpened(false);
    setError('');
  }, [vehicle]);
  function close() {
    dialog.current?.close();
    setOpened(false);
    trigger.current?.focus();
  }
  function inspect(partId: string) {
    if (!vehicle.parts.some((part) => part.id === partId)) {
      setError('That installed part is unavailable in the selected source revision.');
      return;
    }
    onInspect(partId);
    layout?.openContext('details');
    close();
  }
  return (
    <div className="parts-bank-access">
      <button
        ref={trigger}
        type="button"
        disabled={!available}
        title={
          available
            ? 'Browse current RP1 part definitions, source detail and installed instances'
            : 'The first parts-bank slice uses current RP1; archived sources remain separate'
        }
        onClick={() => {
          setOpened(true);
          dialog.current?.showModal();
        }}
      >
        Parts bank
      </button>
      <dialog
        ref={dialog}
        className="parts-bank-dialog"
        aria-label="Source-owned parts bank"
        onCancel={() => setOpened(false)}
        onClose={() => setOpened(false)}
      >
        <header className="parts-bank-dialog-header">
          <div>
            <h2>Parts bank · current RP1 source</h2>
            <p>
              Browse and inspect definitions now. Separate-draft Add, Replace and Connect tools are
              planned in phase P5; this catalog does not change the rocket.
            </p>
          </div>
          <button type="button" onClick={close}>
            Return to rocket
          </button>
        </header>
        <div className="parts-bank-sections" role="group" aria-label="Parts bank sections">
          <button
            type="button"
            aria-pressed={section === 'source'}
            onClick={() => setSection('source')}
          >
            Installed source parts
          </button>
          <button
            type="button"
            aria-pressed={section === 'templates'}
            onClick={() => setSection('templates')}
          >
            Template recipes
          </button>
        </div>
        {error && <p role="alert">{error}</p>}
        {opened && available && (
          <Suspense fallback={<p role="status">Loading source-owned parts bank…</p>}>
            {section === 'source' ? (
              <PartsBankPanel vehicle={vehicle} onInspect={inspect} />
            ) : (
              <TemplateBankPanel vehicle={vehicle} onInspect={inspect} />
            )}
          </Suspense>
        )}
      </dialog>
    </div>
  );
}
