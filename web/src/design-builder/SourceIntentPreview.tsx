import { useId, useState } from 'react';
import type { InspectionDocument } from '../types';
import { matchesDraftSource, type DraftRevision } from './draftLibraryClient';
import {
  createSourceIntentClient,
  SourceIntentError,
  type SourceIntentOverlay,
  type SourceIntentType,
} from './sourceIntentClient';
import './sourceIntentPreview.css';

interface Props {
  vehicle: InspectionDocument;
  snapshot: DraftRevision;
}
// A new saved parent revision gets an independent unsaved state. Unmounting this
// page also discards intents; no effect performs a request or a command.
export default function SourceIntentPreview({ vehicle, snapshot }: Props) {
  if (!matchesDraftSource(vehicle))
    return <p className="source-intent-preview">Intent preview unavailable for this source.</p>;
  return (
    <SourceIntentPanel
      key={`${snapshot.draft_id}:${snapshot.revision_sha256}:${snapshot.source_sha256}`}
      vehicle={vehicle}
      snapshot={snapshot}
    />
  );
}
function SourceIntentPanel({ vehicle, snapshot }: Props) {
  const controlId = useId();
  const [overlay, setOverlay] = useState<SourceIntentOverlay | null>(null);
  const [selectedId, setSelectedId] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stale, setStale] = useState<'metadata' | 'overlay' | null>(null);
  const definition = overlay?.base.source.parts_bank.definitions.find(
    (row) => row.source_part_id === selectedId,
  );
  const excluded = overlay?.excluded_occurrence_ids.includes(selectedId) ?? false;
  async function run(type?: SourceIntentType) {
    setBusy(true);
    setError(null);
    try {
      const client = createSourceIntentClient(vehicle, snapshot);
      const next =
        type && overlay ? await client.apply(overlay, type, selectedId) : await client.prepare();
      setOverlay(next);
      if (!selectedId) setSelectedId(next.base.source.parts_bank.instances[0].id);
      setStale(null);
    } catch (failure) {
      // Preserve the current admitted overlay, selection and all exclusion IDs.
      setError(
        failure instanceof Error
          ? failure.message
          : 'Intent preview unavailable. Current intents are preserved.',
      );
      if (failure instanceof SourceIntentError) {
        if (failure.code === 'stale_draft_revision') setStale('metadata');
        else if (failure.code === 'stale_overlay_revision') setStale('overlay');
        if (failure.currentDraftRevision || failure.currentOverlayRevision)
          setError(
            `${failure.message} Current server revision: ${failure.currentDraftRevision ?? failure.currentOverlayRevision}`,
          );
      }
    } finally {
      setBusy(false);
    }
  }
  return (
    <details className="source-intent-preview">
      <summary>Unsaved source planning intents</summary>
      <p>
        Saved parent: <strong>{snapshot.label}</strong> · metadata revision {snapshot.sequence}.
        This preview records exclusion intent only; all 55 source accounting occurrences remain.
      </p>
      <p className="source-intent-preview__notice">
        Unsaved intents reset when the parent metadata revision or page changes. Preparing a fresh
        preview explicitly discards current intents. Source Design stays unchanged.
      </p>
      <p>
        No physical removal or replacement, effective candidate, mass credit or CAD change is
        produced. Mass, CG and inertia checks are unavailable (null). Simulation eligibility: false;
        engineering acceptance: false; flight readiness: false.
      </p>
      <button type="button" disabled={busy || stale === 'metadata'} onClick={() => void run()}>
        {busy
          ? 'Preparing intent preview…'
          : overlay
            ? 'Prepare fresh preview (discard unsaved intents)'
            : 'Prepare intent preview'}
      </button>
      {stale === 'metadata' && (
        <p role="status">
          Reload the saved metadata in the draft library before preparing another preview.
        </p>
      )}
      {error && (
        <p role="alert" className="source-intent-preview__error">
          {error}
        </p>
      )}
      {!overlay && (
        <p>
          No intent preview has been admitted. Prepare explicitly to read the current saved parent.
        </p>
      )}
      {overlay && (
        <>
          <p role="status">
            UNSAVED · {overlay.preview.exclusion_intents} exclusion intents · 55 original source
            occurrences preserved · effective inventory: unavailable (null).
          </p>
          <label htmlFor={`${controlId}-part`}>Source accounting occurrence</label>
          <select
            id={`${controlId}-part`}
            value={selectedId}
            disabled={busy}
            onChange={(event) => setSelectedId(event.target.value)}
          >
            {overlay.base.source.parts_bank.definitions.map((row) => (
              <option key={row.source_part_id} value={row.source_part_id}>
                {row.name} ({row.source_part_id})
                {overlay.excluded_occurrence_ids.includes(row.source_part_id)
                  ? ' — exclusion intent'
                  : ''}
              </option>
            ))}
          </select>
          <div className="source-intent-preview__actions">
            <button
              type="button"
              disabled={busy || stale !== null || !definition || excluded}
              onClick={() => void run('exclude-source-occurrence')}
            >
              Mark exclusion intent
            </button>
            <button
              type="button"
              disabled={busy || stale !== null || !definition || !excluded}
              onClick={() => void run('restore-source-occurrence')}
            >
              Restore source occurrence intent
            </button>
          </div>
          {definition && (
            <section aria-label="Selected source function and evidence">
              <h4>{definition.name}</h4>
              <p>{definition.function}</p>
              <p>
                {excluded
                  ? 'Exclusion intent: source function unresolved.'
                  : 'No exclusion intent for this occurrence.'}{' '}
                Physical verification: {definition.physical_verification}; interfaces:{' '}
                {definition.interfaces_status}.
              </p>
              <p>Geometry: {definition.geometry.maturity}; reusable local geometry: false.</p>
              <ul>
                {definition.issues.map((issue) => (
                  <li key={issue.id}>
                    {issue.status}: {issue.message}
                  </li>
                ))}
              </ul>
              <details>
                <summary>Source provenance retained</summary>
                <ul>
                  {definition.provenance.map((ref) => (
                    <li key={`${ref.path}:${ref.locator}:${ref.role}`}>
                      <code>{ref.path}</code> · {ref.locator} · {ref.role} · SHA256{' '}
                      <code>{ref.sha256}</code>
                    </li>
                  ))}
                </ul>
              </details>
            </section>
          )}
          <section aria-label="Excluded source functions remain blockers">
            <h4>Excluded source functions remain blockers</h4>
            {overlay.preview.removed_functions.length === 0 && (
              <p>No exclusion intents. Source conflicts and physical gates remain open.</p>
            )}
            <ul>
              {overlay.preview.removed_functions.map((row) => (
                <li key={row.occurrence_id}>
                  <button type="button" onClick={() => setSelectedId(row.occurrence_id)}>
                    {row.occurrence_id}
                  </button>
                  <p>{row.function}</p>
                  <p>{row.blocker}</p>
                  <p>
                    Original source occurrence retained; physical verification:{' '}
                    {row.source_evidence.physical_verification}; interfaces:{' '}
                    {row.source_evidence.interfaces_status}.
                  </p>
                  <ul>
                    {row.source_evidence.issues.map((issue) => (
                      <li key={issue.id}>
                        {issue.status}: {issue.message}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </section>
          <ul>
            {overlay.readiness.blockers.map((blocker) => (
              <li key={blocker}>{blocker}</li>
            ))}
          </ul>
          <p>
            Intent identity: <code>{overlay.revision_sha256}</code>
          </p>
        </>
      )}
    </details>
  );
}
