import { useEffect, useRef, useState } from 'react';
import ReferenceArrangementScene from './ReferenceArrangementScene';
import {
  createReferenceArrangementClient,
  parseTranslationText,
  type ArrangementEnvelope,
} from './referenceArrangementClient';
import './referenceArrangementPanel.css';

const AXES = ['X', 'Y', 'Z'] as const;
type TextPosition = [string, string, string];

/** Separate ephemeral display state; never opens a saved source-draft UUID. */
export default function ReferenceArrangementPanel() {
  const [state, setState] = useState<ArrangementEnvelope | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [choice, setChoice] = useState('reference-local-v1:motor-tube-nominal');
  const [text, setText] = useState<Record<string, TextPosition>>({});
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const request = useRef<AbortController | null>(null);
  const admitted = useRef<ArrangementEnvelope | null>(null);
  useEffect(() => () => request.current?.abort(), []);

  async function perform(
    operation: (
      client: ReturnType<typeof createReferenceArrangementClient>,
      signal: AbortSignal,
    ) => Promise<ArrangementEnvelope>,
    action: 'clear' | 'add' | 'translate',
  ) {
    if (request.current) return;
    const abort = new AbortController();
    const base = admitted.current;
    request.current = abort;
    setPending(true);
    setError('');
    setNotice('');
    try {
      const next = await operation(createReferenceArrangementClient(), abort.signal);
      if (abort.signal.aborted) return;
      if (admitted.current !== base)
        throw new Error(
          'The local plan changed while that request was pending. No response was applied.',
        );
      admitted.current = next;
      setState(next);
      if (action === 'clear') {
        setSelected(null);
        setText({});
        setNotice(
          'Empty unsaved arrangement prepared. The source rocket and saved drafts are unchanged.',
        );
      } else if (action === 'add') {
        const added = next.plan.instances.find(
          (row) => !base?.plan.instances.some((old) => old.id === row.id),
        );
        if (added) {
          setSelected(added.id);
          setText((old) => ({
            ...old,
            [added.id]: added.translation_mm.map(String) as TextPosition,
          }));
        }
        setNotice(
          'Reference added to this display arrangement only. No physical inventory or mass result was created.',
        );
      } else
        setNotice(
          'Translation applied to the display arrangement. Use Fit arrangement if it moved outside the current camera view.',
        );
    } catch (reason: unknown) {
      if (!abort.signal.aborted)
        setError(
          reason instanceof Error
            ? reason.message
            : 'Arrangement unavailable. Previous admitted state is retained.',
        );
    } finally {
      if (request.current === abort) request.current = null;
      if (!abort.signal.aborted) setPending(false);
    }
  }

  const instances = state?.plan.instances ?? [];
  const definitions = state?.catalog.definitions ?? [];
  const chosen = definitions.find((row) => row.id === choice);
  const alreadyAdded = instances.some((row) => row.reference_id === choice);
  const cacheAvailable = Boolean(
    chosen && state?.catalog.availability[chosen.id].geometry_available,
  );
  const instance = instances.find((row) => row.id === selected);
  const position = instance
    ? (text[instance.id] ?? (instance.translation_mm.map(String) as TextPosition))
    : null;
  const displayInstances = instances.map((row) => ({
    id: row.id,
    definition: definitions.find((definition) => definition.id === row.reference_id)!,
    translation_mm: row.translation_mm,
  }));

  return (
    <section
      className="reference-arrangement-panel"
      aria-label="Unsaved local reference arrangement"
    >
      <header>
        <span className="parts-bank-eyebrow">Geometry planning · separate from installed RP1</span>
        <h1>Arrange two source references</h1>
        <p>
          Add the nominal tube and plain ring, then position them in a shared local frame. Unsaved:
          leaving this panel resets the arrangement. No fit, connection, mass, engineering or
          simulation result is calculated.
        </p>
      </header>
      <div className="reference-arrangement-actions">
        <button
          type="button"
          disabled={pending}
          onClick={() => void perform((client, signal) => client.prepare(signal), 'clear')}
        >
          {state ? 'Clear arrangement' : 'Prepare empty arrangement'}
        </button>
        {pending && <span role="status">Checking the explicit arrangement command…</span>}
      </div>
      {error && (
        <p role="alert">
          {error} The previous admitted arrangement and unapplied inputs are retained.
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      {state && (
        <>
          <div className="reference-arrangement-layout">
            <aside aria-label="Reference arrangement controls">
              <label>
                Exact nominal reference
                <select
                  value={choice}
                  disabled={pending}
                  onChange={(event) => setChoice(event.target.value)}
                >
                  {definitions.map((definition) => (
                    <option key={definition.id} value={definition.id}>
                      {definition.name}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                disabled={pending || alreadyAdded || !cacheAvailable}
                onClick={() => {
                  if (!chosen || !state) return;
                  void perform(
                    (client, signal) =>
                      client.command(
                        state,
                        {
                          type: 'add-reference',
                          reference_id: chosen.id,
                          definition_revision_sha256: chosen.revision_sha256,
                          base_plan_revision: state.plan.revision_sha256,
                        },
                        signal,
                      ),
                    'add',
                  );
                }}
              >
                Add reference instance
              </button>
              {alreadyAdded && (
                <p>One display instance per reference. This reference is already added.</p>
              )}
              {!cacheAvailable && (
                <p role="status">
                  Registered local geometry cache unavailable. No substitute model or generation is
                  used.
                </p>
              )}
              <nav aria-label="Arrangement display instances">
                {instances.map((row) => (
                  <button
                    key={row.id}
                    type="button"
                    aria-pressed={selected === row.id}
                    onClick={() => setSelected(row.id)}
                  >
                    {definitions.find((definition) => definition.id === row.reference_id)?.name}
                    <small>{row.translation_mm.join(', ')} mm · local X, Y, Z</small>
                  </button>
                ))}
              </nav>
              {instance && position && (
                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    try {
                      const translation_mm = position.map(parseTranslationText) as [
                        number,
                        number,
                        number,
                      ];
                      void perform(
                        (client, signal) =>
                          client.command(
                            state,
                            {
                              type: 'translate-reference',
                              instance_id: instance.id,
                              translation_mm,
                              base_plan_revision: state.plan.revision_sha256,
                            },
                            signal,
                          ),
                        'translate',
                      );
                    } catch (reason: unknown) {
                      setError(
                        reason instanceof Error ? reason.message : 'Translation input is invalid.',
                      );
                    }
                  }}
                >
                  {AXES.map((axis, index) => (
                    <label key={axis}>
                      Local {axis} translation (mm)
                      <input
                        type="text"
                        inputMode="decimal"
                        value={position[index]}
                        disabled={pending}
                        onChange={(event) =>
                          setText((old) => {
                            const next = [...position] as TextPosition;
                            next[index] = event.target.value;
                            return { ...old, [instance.id]: next };
                          })
                        }
                      />
                    </label>
                  ))}
                  <button type="submit" disabled={pending}>
                    Apply translation
                  </button>
                  <p>
                    ±500 mm per axis; at most three decimal places. Input granularity is not a
                    manufacturing tolerance. Unapplied entries do not move the model.
                  </p>
                </form>
              )}
            </aside>
            <ReferenceArrangementScene
              instances={displayInstances}
              selectedInstanceId={selected}
              onSelect={setSelected}
            />
          </div>
          <details>
            <summary>Source identity, frame and unavailable results</summary>
            <p>
              Catalog {state.catalog.id} · revision {state.catalog.revision_sha256}. Plan content
              guard {state.plan.revision_sha256}.
            </p>
            <p>
              Uninstalled arrangement in millimetres, parallel to local CAD axes, +Z along the part.
              Viewer metres map [X,Y,Z] = [cadX/1000, −cadZ/1000, cadY/1000]. Orientation, scale and
              quantity are fixed. No snap or mating is inferred from overlapping surfaces.
            </p>
            <p>
              No saved history, cross-tab server head or undo. The content hash validates submitted
              state only. Original source flags remain unchanged; the 55-record RP1 inventory and
              its separate 50 g growth and 20 g adverse policies are not altered.
            </p>
            <p>
              Mass, mass credit, CG, inertia, cost and physical checks are unavailable. Resolved
              candidate, simulation, engineering, physical, mating and flight readiness remain
              false. Existing D1/recovery/thermal/flutter/WO-10 gates and UNSENT inquiries stay
              open.
            </p>
            {definitions.map((definition) => (
              <p key={definition.id}>
                {definition.name}: {definition.identity_limit}
              </p>
            ))}
          </details>
        </>
      )}
    </section>
  );
}
