import { useEffect, useState } from 'react';
import { GeometryViews } from './GeometryViews';
import { LoadPathViews } from './LoadPathViews';
import { MassLaunchViews } from './MassLaunchViews';
import { ExtensionViews } from './ExtensionViews';
import { A1ConnectionViews } from './A1ConnectionViews';
import { ConventionalG80Views } from './ConventionalG80Views';
import { F2ConstructionViews } from './F2ConstructionViews';
import type { A1Snapshot } from './a1Types';
import { validateA1Snapshot } from './a1Types';
import type { ConventionalSnapshot } from './conventionalG80Types';
import { validateConventionalSnapshot } from './conventionalG80Types';
import type { F2Snapshot } from './f2Types';
import { validateF2Snapshot } from './f2Types';
import type { ExtendedDocument, ExtensionMode } from './extendedTypes';
import { compatibleExtension } from './extendedTypes';
import type { WorkbenchDocument } from './types';
import './workbench.css';

import {
  engineeringTopics,
  engineeringRoute,
  engineeringHref,
  isConstructionTopic,
  loadRecordedSource,
} from './workbenchRouting';
import type { EngineeringTopic as View } from './workbenchRouting';

const extensionModes: ExtensionMode[] = [
  'comparison',
  'recovery',
  'thermal',
  'electrical',
  'assembly',
  'requirements',
];

export default function EngineeringWorkbench() {
  const [document, setDocument] = useState<WorkbenchDocument | null>(null);
  const [error, setError] = useState('');
  const [extended, setExtended] = useState<ExtendedDocument | null>(null);
  const [extensionError, setExtensionError] = useState('');
  const [extensionPrepared, setExtensionPrepared] = useState(false);
  const [a1, setA1] = useState<A1Snapshot | null>(null);
  const [a1Error, setA1Error] = useState('');
  const [a1Prepared, setA1Prepared] = useState(false);
  const [fixed, setFixed] = useState<ConventionalSnapshot | null>(null);
  const [fixedError, setFixedError] = useState('');
  const [fixedPrepared, setFixedPrepared] = useState(false);
  const [f2, setF2] = useState<F2Snapshot | null>(null);
  const [f2Error, setF2Error] = useState('');
  const [f2Prepared, setF2Prepared] = useState(false);
  const [selectedJointId, setSelectedJointId] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const [route, setRoute] = useState(() =>
    engineeringRoute(typeof window === 'undefined' ? '' : window.location.search),
  );
  const view = route.view;
  const construction = isConstructionTopic(view);
  const needsExtension = extensionModes.includes(view as ExtensionMode);
  useEffect(() => {
    const changed = () => setRoute(engineeringRoute(window.location.search));
    window.addEventListener('popstate', changed);
    return () => window.removeEventListener('popstate', changed);
  }, []);
  const setView = (next: View) => {
    const href = engineeringHref(window.location.href, next);
    window.history.pushState(null, '', href);
    window.dispatchEvent(new PopStateEvent('popstate'));
  };
  const [prepared, setPrepared] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  useEffect(() => {
    if (construction) return;
    const controller = new AbortController();
    setDocument(null);
    setError('');
    setPrepared(false);
    void loadRecordedSource(
      '/api/engineering/workbench',
      '/engineering-workbench/g80-c1.json',
      controller.signal,
    )
      .then(({ value, prepared }) => {
        if (controller.signal.aborted) return;
        setDocument(value as WorkbenchDocument);
        setPrepared(prepared);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted)
          setError(reason instanceof Error ? reason.message : 'Recorded source unavailable.');
      });
    return () => controller.abort();
  }, [retry, construction]);
  useEffect(() => {
    if (view !== 'g80-fixed') return;
    const controller = new AbortController();
    setFixed(null);
    setFixedError('');
    setFixedPrepared(false);
    void loadRecordedSource(
      '/api/engineering/workbench-g80-fixed',
      '/engineering-workbench/preparedg80-fixed-f1.json',
      controller.signal,
    )
      .then(({ value, prepared }) => {
        if (controller.signal.aborted) return;
        setFixed(validateConventionalSnapshot(value));
        setFixedPrepared(prepared);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted)
          setFixedError(reason instanceof Error ? reason.message : 'Recorded source unavailable.');
      });
    return () => controller.abort();
  }, [retry, view]);
  useEffect(() => {
    if (view !== 'g80-f2') return;
    const controller = new AbortController();
    setF2(null);
    setF2Error('');
    setF2Prepared(false);
    void loadRecordedSource(
      '/api/engineering/workbench-g80-f2',
      '/engineering-workbench/preparedg80-fixed-f2.json',
      controller.signal,
    )
      .then(({ value, prepared }) => {
        if (controller.signal.aborted) return;
        setF2(validateF2Snapshot(value));
        setF2Prepared(prepared);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted)
          setF2Error(reason instanceof Error ? reason.message : 'Recorded source unavailable.');
      });
    return () => controller.abort();
  }, [retry, view]);
  useEffect(() => {
    if (view !== 'a1') return;
    const controller = new AbortController();
    setA1(null);
    setA1Error('');
    setA1Prepared(false);
    void loadRecordedSource(
      '/api/engineering/workbench-a1',
      '/engineering-workbench/g80-a1.json',
      controller.signal,
    )
      .then(({ value, prepared }) => {
        if (controller.signal.aborted) return;
        setA1(validateA1Snapshot(value));
        setA1Prepared(prepared);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted)
          setA1Error(reason instanceof Error ? reason.message : 'Recorded source unavailable.');
      });
    return () => controller.abort();
  }, [retry, view]);
  useEffect(() => {
    if (!needsExtension) return;
    const controller = new AbortController();
    setExtended(null);
    setExtensionError('');
    setExtensionPrepared(false);
    void loadRecordedSource(
      '/api/engineering/workbench-extended',
      '/engineering-workbench/g80-extended.json',
      controller.signal,
    )
      .then(({ value, prepared }) => {
        if (controller.signal.aborted) return;
        setExtended(value as ExtendedDocument);
        setExtensionPrepared(prepared);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted)
          setExtensionError(
            reason instanceof Error ? reason.message : 'Recorded source unavailable.',
          );
      });
    return () => controller.abort();
  }, [retry, needsExtension]);
  const topicNavigation = (
    <>
      {route.notice && (
        <p className="wb-notice" role="status">
          {route.notice}
        </p>
      )}
      <nav className="wb-tabs" aria-label="Engineering views">
        {engineeringTopics.map(([id, label]) => (
          <button
            key={id}
            aria-current={view === id ? 'page' : undefined}
            className={view === id ? 'active' : ''}
            onClick={() => setView(id)}
          >
            {label}
          </button>
        ))}
      </nav>
    </>
  );
  if (construction) {
    const snapshot = view === 'a1' ? a1 : view === 'g80-fixed' ? fixed : f2;
    const sourceError = view === 'a1' ? a1Error : view === 'g80-fixed' ? fixedError : f2Error;
    const label = engineeringTopics.find(([id]) => id === view)![1];
    return (
      <main className="engineering-workbench">
        {topicNavigation}
        <section className="wb-introduction">
          <div>
            <span className="wb-eyebrow">Independent recorded construction snapshot</span>
            <h1>{snapshot?.label ?? label}</h1>
            <p>
              {sourceError
                ? 'Requested source unavailable'
                : (snapshot?.status ?? 'Loading requested source')}
            </p>
          </div>
          {snapshot && !sourceError && (
            <div className="wb-identity">
              <strong>{snapshot.identity.candidate_id}</strong>
              <span>Source {snapshot.identity.source_identity}</span>
              <span>
                CAD: {snapshot.identity.cad_revision ?? 'No same-design detailed assembly'}
              </span>
            </div>
          )}
        </section>
        <div className="wb-notice">
          Separate concept snapshot. Engineering acceptance and physical qualification remain open;
          historical records and archived CAD are distinct.
        </div>
        {sourceError ? (
          <section className="wb-ext-loading">
            <h2>{label} source unavailable</h2>
            <p>{sourceError}</p>
            <button onClick={() => setRetry((value) => value + 1)}>Retry requested source</button>
          </section>
        ) : view === 'a1' && a1 ? (
          <A1ConnectionViews snapshot={a1} prepared={a1Prepared} />
        ) : view === 'g80-fixed' && fixed ? (
          <ConventionalG80Views snapshot={fixed} prepared={fixedPrepared} />
        ) : view === 'g80-f2' && f2 ? (
          <F2ConstructionViews snapshot={f2} prepared={f2Prepared} />
        ) : (
          <p className="wb-ext-loading" role="status">
            Loading {label} source snapshot.
          </p>
        )}
      </main>
    );
  }
  if (error)
    return (
      <main className="engineering-workbench">
        {topicNavigation}
        <h1>Engineering source data unavailable</h1>
        <p>{error}</p>
        <p>
          Restart the Python API after updating its code. Missing source evidence stays unavailable.
        </p>
        <button onClick={() => setRetry(retry + 1)}>Retry walkthrough</button>
      </main>
    );
  if (!document)
    return (
      <main className="engineering-workbench">
        {topicNavigation}
        <span className="spinner" />
        <h1>Loading the recorded engineering walkthrough</h1>
      </main>
    );
  const part = document.parts.find((item) => item.id === selected);
  const selectedJoint = document.joints.find((joint) => joint.id === selectedJointId);
  const drawingDocument = selectedJoint
    ? {
        ...document,
        joints: [selectedJoint, ...document.joints.filter((joint) => joint.id !== selectedJointId)],
      }
    : document;
  const props = { document: drawingDocument, selectedPartId: selected, onSelectPart: setSelected };
  const extendedCompatible = extended
    ? compatibleExtension(document.identity, extended.identity)
    : false;
  const openJoint = (id: string) => {
    const joint = document.joints.find((item) => item.id === id);
    if (!joint) return;
    setSelectedJointId(id);
    const linked = joint.part_ids.find((partId) =>
      document.parts.some((part) => part.id === partId),
    );
    if (linked) setSelected(linked);
    setView('geometry');
  };
  const visible = document.parts.filter((item) =>
    `${item.id} ${item.label} ${item.material} ${item.subsystem}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  return (
    <main className="engineering-workbench">
      {topicNavigation}
      <section className="wb-introduction">
        <div>
          <span className="wb-eyebrow">Historical engineering walkthrough</span>
          <h1>{document.label}</h1>
          <p>{document.status}</p>
        </div>
        <div className="wb-identity">
          <strong>{document.identity.configuration_id}</strong>
          <span>Source {document.identity.specification_sha256.slice(0, 16)}</span>
          <span>
            CAD: {document.identity.cad_revision ?? 'No complete C1 assembly — concept drawings'}
          </span>
        </div>
      </section>
      <div className="wb-notice">
        Frozen historical C1 study. The archived 72-part retention CAD is a different candidate.
        Drawings explain recorded design evidence; engineering and physical-flight acceptance remain
        open.
      </div>
      {prepared && (
        <div className="wb-notice">
          Displaying the prepared offline export with the source identity below. The current API
          does not have the workbench route; restart it to use its source-checked live export.
        </div>
      )}
      <div className="wb-layout">
        <aside className="wb-part-list">
          <h2>Linked components</h2>
          <p>Select here or in a drawing. Selection follows you between views.</p>
          <input
            aria-label="Search engineering components"
            placeholder="Find a part or material…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="wb-clear" onClick={() => setSelected(null)}>
            Clear selection
          </button>
          {visible.map((item) => (
            <button
              key={item.id}
              className={`wb-part ${selected === item.id ? 'selected' : ''}`}
              onClick={() => setSelected(item.id)}
            >
              <strong>{item.label}</strong>
              <span>
                {item.subsystem} · {item.geometry_maturity.replaceAll('_', ' ')}
              </span>
            </button>
          ))}
        </aside>
        <section className="wb-graphics" aria-label="Engineering graphics">
          {view === 'geometry' ? (
            <GeometryViews {...props} />
          ) : view === 'forces' ? (
            <LoadPathViews {...props} />
          ) : view === 'mass' ? (
            <MassLaunchViews {...props} />
          ) : extensionModes.includes(view as ExtensionMode) ? (
            extensionError || (extended && !extendedCompatible) ? (
              <div className="wb-extension">
                <div className="wb-ext-loading">
                  <h2>Extended source records unavailable</h2>
                  <p>
                    {extensionError ||
                      'Extended configuration, specification hash or CAD identity differs from the frozen C1 document. Graphics are not attached.'}
                  </p>
                  <button type="button" onClick={() => setRetry(retry + 1)}>
                    Retry source records
                  </button>
                </div>
              </div>
            ) : extended ? (
              <>
                <div className="wb-notice">
                  {extensionPrepared
                    ? 'Prepared offline extension export; source identity is shown in each evidence record.'
                    : 'Source-checked extension records.'}{' '}
                  C1 stays frozen; stopped revisions remain separate.
                </div>
                <ExtensionViews
                  {...props}
                  extended={extended}
                  mode={view as ExtensionMode}
                  onOpenJoint={openJoint}
                />
              </>
            ) : (
              <div className="wb-extension">
                <p className="wb-ext-loading" role="status">
                  Loading extended source records. Existing geometry, forces and experiment views
                  remain available.
                </p>
              </div>
            )
          ) : (
            <>
              <h2>What exists, and what evidence is missing</h2>
              <p>
                Code implementation and browser-observed behavior are recorded separately. A
                selected input range is not a statistical confidence interval.
              </p>
              <div className="wb-inventory">
                {document.inventory.map((item) => (
                  <article key={item.id}>
                    <strong>{item.label}</strong>
                    <span className={`wb-state ${item.category}`}>
                      {item.category.replaceAll('_', ' ')}
                    </span>
                    <p>{item.note}</p>
                    <small>
                      {item.browser_verified
                        ? 'Recorded browser evidence available for this item'
                        : 'Not browser verified in this increment'}
                    </small>
                  </article>
                ))}
              </div>
              <h2>Sources and interpretation</h2>
              <p>
                {document.identity.frame} · {document.identity.units}. Calculated values come from
                saved Python results. Estimated dimensions and unknown joints remain labeled. No
                stress, airflow or temperature field is invented for these drawings.
              </p>
              {document.generated_from.map((source) => (
                <details key={source.id}>
                  <summary>{source.description}</summary>
                  <p>{source.path}</p>
                  <code>{source.sha256}</code>
                </details>
              ))}
            </>
          )}
        </section>
        <aside className="wb-inspector" aria-label="Engineering part inspector">
          {part ? (
            <>
              <span className={`wb-state ${part.state}`}>
                {part.state} · {part.geometry_maturity.replaceAll('_', ' ')}
              </span>
              <h2>{part.label}</h2>
              <p>{part.function}</p>
              <dl>
                <dt>Material</dt>
                <dd>{part.material}</dd>
                <dt>Manufacturing</dt>
                <dd>{part.manufacturing}</dd>
                <dt>Mass</dt>
                <dd>{part.mass_g === null ? 'Unavailable' : `${part.mass_g.toFixed(3)} g`}</dd>
                <dt>Mass basis</dt>
                <dd>{part.mass_basis}</dd>
                <dt>Position from nose tip</dt>
                <dd>{part.start_mm === null ? 'Undefined' : `${part.start_mm} mm`}</dd>
                <dt>Length</dt>
                <dd>{part.length_mm === null ? 'Undefined' : `${part.length_mm} mm`}</dd>
                <dt>Source part identities</dt>
                <dd>{part.source_part_ids.join(', ') || 'No detailed-CAD identity'}</dd>
              </dl>
              <h3>Connections</h3>
              {part.connections.map((text, i) => (
                <p key={i}>{text}</p>
              ))}
              <h3>Open findings / failure modes</h3>
              {part.findings.map((text, i) => (
                <p className="wb-finding" key={i}>
                  {text}
                </p>
              ))}
              <h3>Evidence</h3>
              {part.source_ids.map((id) => (
                <p key={id}>
                  {document.generated_from.find((s) => s.id === id)?.description ?? id}
                </p>
              ))}
            </>
          ) : (
            <>
              <h2>Explore the construction</h2>
              <p>
                Click a colored component or connection in a drawing to inspect its function,
                material, source and open findings.
              </p>
              <h3>Representation key</h3>
              <p>
                <b>Detailed CAD:</b> existing engineering solid.
              </p>
              <p>
                <b>Envelope:</b> a simplified space reservation.
              </p>
              <p>
                <b>Concept:</b> a sourced preliminary arrangement.
              </p>
              <p>
                <b>Undefined:</b> geometry or a connection still needs design evidence.
              </p>
              <p>
                Blue is calculated evidence, amber is estimated or unresolved, red identifies failed
                screens. None of these colors grants build or flight approval.
              </p>
            </>
          )}
        </aside>
      </div>
    </main>
  );
}
