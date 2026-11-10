import { useEffect, useId, useMemo, useRef, useState } from 'react';
import type { InspectionDocument } from '../types';
import {
  createDraftClient,
  DraftServiceError,
  editDraft,
  hasDraftChanges,
  matchesDraftSource,
  retainDraftConflict,
} from './draftLibraryClient';
import type { DraftEditor, DraftPage, DraftRevision } from './draftLibraryClient';
import './draftLibrary.css';

/** Embedded normal-flow library; the parent owns any enclosing dialog and return. */
export default function DraftLibrary({
  vehicle,
  onInspectSource,
}: {
  vehicle: InspectionDocument;
  onInspectSource: (partId?: string) => void;
}) {
  const prefix = useId();
  const client = useMemo(
    () => (matchesDraftSource(vehicle) ? createDraftClient(vehicle) : null),
    [vehicle],
  );
  const [page, setPage] = useState<DraftPage | null>(null);
  const [editor, setEditor] = useState<DraftEditor | null>(null);
  const [history, setHistory] = useState<DraftRevision | null>(null);
  const [forkLabel, setForkLabel] = useState('RP1 source study');
  const [forkNotes, setForkNotes] = useState('');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const generation = useRef(0);
  const lifetime = useRef<AbortController | null>(null);
  const dirty = editor !== null && hasDraftChanges(editor);

  useEffect(() => {
    const token = ++generation.current;
    const controller = new AbortController();
    lifetime.current = controller;
    setPage(null);
    setEditor(null);
    setHistory(null);
    setError('');
    setNotice('');
    if (client) {
      setBusy('Loading saved drafts');
      client
        .list(undefined, controller.signal)
        .then((value) => {
          if (generation.current === token && !controller.signal.aborted) setPage(value);
        })
        .catch((cause: unknown) => {
          if (generation.current === token && !controller.signal.aborted)
            setError(cause instanceof Error ? cause.message : 'Draft list could not be loaded.');
        })
        .finally(() => {
          if (generation.current === token && !controller.signal.aborted) setBusy('');
        });
    }
    return () => {
      controller.abort();
      generation.current = token + 1;
    };
  }, [client]);

  async function run(label: string, action: (signal?: AbortSignal) => Promise<void>) {
    if (!client || busy) return;
    const token = generation.current;
    setBusy(label);
    setError('');
    setNotice('');
    try {
      await action(lifetime.current?.signal);
    } catch (cause) {
      if (generation.current === token && !lifetime.current?.signal.aborted) {
        setError(cause instanceof Error ? cause.message : 'Draft operation failed.');
        if (cause instanceof DraftServiceError && cause.code === 'stale_revision')
          setEditor((value) => (value ? retainDraftConflict(value, cause) : null));
      }
    } finally {
      if (generation.current === token && !lifetime.current?.signal.aborted) setBusy('');
    }
  }
  function current(token: number) {
    return generation.current === token && !lifetime.current?.signal.aborted;
  }
  function load(id: string, discard = false) {
    if (!client || (dirty && !discard)) return;
    const token = generation.current;
    void run('Loading draft', async (signal) => {
      const value = await client.read(id, undefined, signal);
      if (current(token)) {
        setEditor(editDraft(value));
        setHistory(null);
        setNotice(
          discard
            ? 'Latest saved revision loaded. Unsaved text was discarded.'
            : 'Saved draft loaded.',
        );
      }
    });
  }
  function refresh(after?: string) {
    if (!client) return;
    const token = generation.current;
    void run('Loading saved drafts', async (signal) => {
      const value = await client.list(after, signal);
      if (current(token)) setPage(value);
    });
  }
  if (!client)
    return (
      <section className="draft-library" aria-label="Local design drafts">
        <h3>Draft library unavailable for this source</h3>
        <p>
          The exact frozen RP1 source and all 55 records are required. No draft request was sent.
        </p>
      </section>
    );

  const shown = history ?? editor?.snapshot;
  return (
    <section className="draft-library" aria-label="Local design drafts" aria-busy={Boolean(busy)}>
      <header>
        <h3>Local design drafts</h3>
        <p>
          Fork the frozen RP1 source into a separate local identity, then save labels and notes.
          Drafts retain the original 55 source accounting occurrences and their estimates, conflicts
          and missingness.
        </p>
        <p>
          Engineering acceptance: open. Simulation eligibility: false. Flight readiness: false.
          Physical and flight gates remain open; inquiries remain UNSENT.
        </p>
        <button type="button" onClick={() => onInspectSource()}>
          Inspect frozen parent rocket
        </button>
      </header>
      <p className="draft-library-status" role="status" aria-live="polite">
        {busy
          ? `${busy}…`
          : notice || 'Changes save only through the explicit Fork or Save buttons.'}
      </p>
      {error && (
        <p className="draft-library-error" role="alert">
          {error}
        </p>
      )}
      <div className="draft-library-layout">
        <div>
          <form
            aria-label="Fork frozen RP1 source"
            onSubmit={(event) => {
              event.preventDefault();
              if (dirty) return;
              const token = generation.current;
              void run('Forking RP1 source', async (signal) => {
                const value = await client.fork(forkLabel, forkNotes, signal);
                if (current(token)) {
                  setEditor(editDraft(value));
                  setHistory(null);
                  setNotice(
                    'Separate draft created. Frozen RP1 and saved runs are unchanged. Refresh the library to update its list.',
                  );
                }
              });
            }}
          >
            <h4>Fork current source</h4>
            <p>G80-F2-RP1-AD1-definition-v2</p>
            <label htmlFor={`${prefix}-fork-label`}>New draft label</label>
            <input
              id={`${prefix}-fork-label`}
              value={forkLabel}
              maxLength={160}
              required
              disabled={Boolean(busy)}
              onChange={(event) => setForkLabel(event.target.value)}
            />
            <label htmlFor={`${prefix}-fork-notes`}>New draft notes</label>
            <textarea
              id={`${prefix}-fork-notes`}
              value={forkNotes}
              maxLength={8000}
              rows={3}
              disabled={Boolean(busy)}
              onChange={(event) => setForkNotes(event.target.value)}
            />
            <button type="submit" disabled={Boolean(busy) || dirty || !forkLabel.trim()}>
              Fork RP1 as separate draft
            </button>
            {dirty && (
              <p>
                Save or explicitly discard the current unsaved metadata before opening another
                draft.
              </p>
            )}
          </form>
          <section aria-label="Saved local drafts">
            <h4>Saved drafts</h4>
            <button type="button" disabled={Boolean(busy)} onClick={() => refresh()}>
              {page ? 'Refresh library from first page' : 'Retry loading draft library'}
            </button>
            {page === null ? (
              <p>No draft list has been admitted yet.</p>
            ) : (
              <>
                {page.drafts.length === 0 ? (
                  <p>The draft service reports no saved drafts on this page.</p>
                ) : (
                  <ul className="draft-library-list">
                    {page.drafts.map((row) => (
                      <li key={row.draft_id}>
                        <button
                          type="button"
                          disabled={Boolean(busy) || dirty}
                          aria-pressed={editor?.snapshot.draft_id === row.draft_id}
                          onClick={() => load(row.draft_id)}
                        >
                          {row.label}
                        </button>
                        <small>
                          Revision {row.sequence} · {row.created_at}
                        </small>
                        <code>{row.draft_id}</code>
                      </li>
                    ))}
                  </ul>
                )}
                {page.next_after && (
                  <button
                    type="button"
                    disabled={Boolean(busy)}
                    onClick={() => refresh(page.next_after ?? undefined)}
                  >
                    Next saved drafts page
                  </button>
                )}
              </>
            )}
          </section>
        </div>
        <div>
          {!editor ? (
            <p>
              Open a saved draft or explicitly fork RP1 to inspect its separate identity and edit
              metadata.
            </p>
          ) : (
            <>
              <form
                aria-label="Save draft metadata"
                onSubmit={(event) => {
                  event.preventDefault();
                  if (editor.conflict) return;
                  const token = generation.current;
                  void run('Saving draft metadata', async (signal) => {
                    const value = await client.save(editor, signal);
                    if (current(token)) {
                      setEditor(editDraft(value));
                      setHistory(null);
                      setNotice(
                        'Metadata revision saved. Source accounting and readiness are unchanged.',
                      );
                    }
                  });
                }}
              >
                <h4>Metadata · current loaded revision {editor.snapshot.sequence}</h4>
                <label htmlFor={`${prefix}-label`}>Draft label</label>
                <input
                  id={`${prefix}-label`}
                  required
                  maxLength={160}
                  value={editor.label}
                  disabled={Boolean(busy)}
                  onChange={(event) => setEditor({ ...editor, label: event.target.value })}
                />
                <label htmlFor={`${prefix}-notes`}>Draft notes</label>
                <textarea
                  id={`${prefix}-notes`}
                  maxLength={8000}
                  rows={6}
                  value={editor.notes}
                  disabled={Boolean(busy)}
                  onChange={(event) => setEditor({ ...editor, notes: event.target.value })}
                />
                <p>
                  {dirty ? 'Unsaved metadata changes' : 'Metadata matches this loaded revision'}
                </p>
                {editor.conflict && (
                  <p className="draft-library-error">
                    A newer revision exists: <code>{editor.conflict}</code>. Your unsaved text
                    remains in these fields.
                  </p>
                )}
                <div className="draft-library-actions">
                  <button
                    type="submit"
                    disabled={
                      Boolean(busy) || !dirty || Boolean(editor.conflict) || !editor.label.trim()
                    }
                  >
                    Save metadata revision
                  </button>
                  <button
                    type="button"
                    disabled={Boolean(busy)}
                    onClick={() => load(editor.snapshot.draft_id, true)}
                  >
                    {dirty || editor.conflict
                      ? 'Reload latest and discard unsaved text'
                      : 'Reload latest saved revision'}
                  </button>
                </div>
              </form>
              <section aria-label="Immutable draft history">
                <h4>Saved identity and history</h4>
                {shown && (
                  <>
                    <p>
                      {history
                        ? 'Historical revision · read only'
                        : 'Current loaded saved revision'}{' '}
                      {shown.sequence} · {shown.label}
                    </p>
                    <dl className="draft-library-identity">
                      <dt>Draft ID</dt>
                      <dd>
                        <code>{shown.draft_id}</code>
                      </dd>
                      <dt>Revision SHA-256</dt>
                      <dd>
                        <code>{shown.revision_sha256}</code>
                      </dd>
                      <dt>Source snapshot SHA-256</dt>
                      <dd>
                        <code>{shown.source_sha256}</code>
                      </dd>
                      <dt>Frozen base configuration</dt>
                      <dd>{shown.base_configuration_id}</dd>
                      <dt>Frozen specification SHA-256</dt>
                      <dd>
                        <code>{String(shown.source.parts_bank.identity.specification_sha256)}</code>
                      </dd>
                      <dt>Accounting</dt>
                      <dd>
                        55 source definitions · 55 source accounting occurrences. Quantity 1 per
                        source group; geometry children add no mass charge.
                      </dd>
                      <dt>Readiness</dt>
                      <dd>
                        Engineering accepted: false · Simulation eligible: false · Flight ready:
                        false
                      </dd>
                    </dl>
                    {history && (
                      <p className="draft-library-history-notes">
                        Saved notes: {history.notes || '(No notes saved)'}
                      </p>
                    )}
                    <div className="draft-library-actions">
                      {shown.parent_revision_sha256 && (
                        <button
                          type="button"
                          disabled={Boolean(busy)}
                          onClick={() => {
                            const token = generation.current;
                            void run('Loading parent revision', async (signal) => {
                              const value = await client.read(
                                shown.draft_id,
                                shown.parent_revision_sha256 ?? undefined,
                                signal,
                              );
                              if (current(token)) {
                                setHistory(value);
                                setNotice(
                                  'Historical snapshot loaded; current unsaved metadata is preserved.',
                                );
                              }
                            });
                          }}
                        >
                          Load parent saved revision
                        </button>
                      )}
                      {history && (
                        <button type="button" onClick={() => setHistory(null)}>
                          Return to current metadata revision
                        </button>
                      )}
                    </div>
                    <details>
                      <summary>Source conflicts and unavailable geometry</summary>
                      <ul>
                        {shown.source.parts_bank.definitions
                          .filter(
                            (part) =>
                              part.issues.length > 0 ||
                              part.geometry.maturity === 'missing_geometry',
                          )
                          .map((part) => (
                            <li key={part.id}>
                              <button
                                type="button"
                                onClick={() => onInspectSource(part.source_part_id)}
                              >
                                Inspect frozen source: {part.name}
                              </button>
                              {part.issues.map((issue) => (
                                <p key={issue.id}>{issue.message}</p>
                              ))}
                              {part.geometry.maturity === 'missing_geometry' && (
                                <p>
                                  Geometry unavailable:{' '}
                                  {part.geometry.reason ?? 'No source geometry recorded.'}
                                </p>
                              )}
                            </li>
                          ))}
                      </ul>
                    </details>
                  </>
                )}
              </section>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
