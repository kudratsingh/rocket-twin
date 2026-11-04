import { useId } from 'react';
import type { RefObject } from 'react';
import type { InspectionDocument, JsonValue } from '../types';
import {
  componentEvidence,
  evidenceEndpoints,
  evidenceStrings,
  evidenceText,
  selectEvidenceEndpoint,
} from './inspectionEvidenceModel';

export function ComponentEvidence({
  vehicle,
  selectedId,
  onSelect,
  hiddenIds = [],
  disclosureRef,
}: {
  vehicle: InspectionDocument;
  selectedId: string | null;
  onSelect: (id: string) => void;
  hiddenIds?: string[];
  disclosureRef?: RefObject<HTMLDetailsElement | null>;
}) {
  const id = useId();
  const model = componentEvidence(vehicle, selectedId);
  if (!model)
    return (
      <section
        className="research-component-evidence"
        data-inspection-evidence="true"
        aria-label="Component evidence"
      >
        {selectedId
          ? `Component ${selectedId} is not mapped in source ${vehicle.id}. Select a component from this source.`
          : 'Select a component to inspect its recorded connections, failures and verification.'}
      </section>
    );
  const endpoints = (value: JsonValue | undefined) => {
    const items = evidenceEndpoints(vehicle, value);
    return items.length ? (
      <ul className="research-evidence-endpoints">
        {items.map((item) => (
          <li key={item.id}>
            {item.mapped ? (
              <button
                type="button"
                aria-current={selectedId === item.id ? 'true' : undefined}
                onClick={() => selectEvidenceEndpoint(vehicle, item.id, onSelect)}
              >
                {item.label}
                {hiddenIds.includes(item.id) ? ' · hidden in drawing' : ''}
              </button>
            ) : (
              <span>{item.label} · endpoint not mapped in this source</span>
            )}
          </li>
        ))}
      </ul>
    ) : (
      <p className="research-evidence-muted">Component endpoints not supplied.</p>
    );
  };
  const renderRecords = (records: Record<string, JsonValue>[], kind: string) =>
    records.length ? (
      records.map((record, index) => (
        <details className="research-evidence-record" key={`${evidenceText(record.id)}-${index}`}>
          <summary>
            <strong>{evidenceText(record.id)}</strong> ·{' '}
            {evidenceText(record.name ?? record.failure_mode ?? record.acceptance)}
            <span className="research-evidence-state">
              {evidenceText(record.status ?? record.applicability_status)}
              {record.severity ? ` · ${evidenceText(record.severity)}` : ''}
            </span>
          </summary>
          {(record.spec_parts || record.related_parts) &&
            endpoints(record.spec_parts ?? record.related_parts)}
          <dl>
            {Object.entries(record)
              .filter(
                ([key]) =>
                  !['id', 'name', 'failure_mode', 'spec_parts', 'related_parts'].includes(key),
              )
              .map(([key, value]) => (
                <div key={key}>
                  <dt>{key.replaceAll('_', ' ')}</dt>
                  <dd>
                    {Array.isArray(value) ? (
                      <ul>
                        {value.map((entry, i) => (
                          <li key={i}>{evidenceText(entry)}</li>
                        ))}
                      </ul>
                    ) : (
                      evidenceText(value)
                    )}
                  </dd>
                </div>
              ))}
          </dl>
        </details>
      ))
    ) : (
      <p className="research-evidence-muted">
        No {kind} records supplied for this component. This does not establish that none exist.
      </p>
    );
  const verification = [
    ...new Set([
      ...evidenceStrings(model.statuses?.required_physical_tests),
      ...(model.part.engineering?.required_physical_verification || []),
    ]),
  ];
  return (
    <details
      ref={disclosureRef}
      className="research-component-evidence"
      data-inspection-evidence="true"
    >
      <summary>
        <strong>Connections & evidence</strong> · {model.part.name || model.part.id}
        <span>
          {model.interfaces.length} interfaces · {model.failures.length} failure records ·{' '}
          {model.requirements.length} requirements
        </span>
      </summary>
      <p>
        Source: <code>{vehicle.id}</code>. Links select components only in this loaded source.
        Hidden components stay hidden; use the drawing or component tree to reveal them. Assembly
        hierarchy does not establish a qualified load path.
      </p>
      <nav aria-label="Component evidence sections" className="research-evidence-nav">
        <a href={`#${id}-connections`}>Connections</a>
        <a href={`#${id}-failures`}>Failures</a>
        <a href={`#${id}-verification`}>Verification</a>
      </nav>
      <section id={`${id}-connections`} aria-label="Recorded connections">
        <h3>Recorded connections</h3>
        <h4>Parent assembly</h4>
        {model.parent.length ? (
          endpoints(model.parent.map((part) => part.id))
        ) : (
          <p>No parent declared.</p>
        )}
        <h4>Child components</h4>
        {model.children.length ? (
          endpoints(model.children.map((part) => part.id))
        ) : (
          <p>No children declared.</p>
        )}
        <h4>Source interfaces</h4>
        {renderRecords(model.interfaces, 'interface')}
        <h4>Electrical metadata</h4>
        {model.part.electrical ? (
          <dl>
            {Object.entries(model.part.electrical).map(([key, value]) => (
              <div key={key}>
                <dt>{key.replaceAll('_', ' ')}</dt>
                <dd>{evidenceText(value)}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="research-evidence-muted">
            Electrical connection metadata is not supplied for this component; no wiring route is
            inferred.
          </p>
        )}
      </section>
      <section id={`${id}-failures`} aria-label="Recorded failures">
        <h3>Failures & unresolved risks</h3>
        {renderRecords(model.failures, 'failure')}
        {!model.failures.length && !!model.part.failure_modes?.length && (
          <ul>
            {model.part.failure_modes.map((failure) => (
              <li key={failure}>{failure}</li>
            ))}
          </ul>
        )}
      </section>
      <section id={`${id}-verification`} aria-label="Recorded verification">
        <h3>Evidence & verification</h3>
        {model.statuses ? (
          <dl>
            {Object.entries(model.statuses)
              .filter(([key]) => key !== 'required_physical_tests')
              .map(([key, value]) => (
                <div key={key}>
                  <dt>{key.replaceAll('_', ' ')}</dt>
                  <dd>{evidenceText(value)}</dd>
                </div>
              ))}
          </dl>
        ) : (
          <p className="research-evidence-muted">
            Evidence status not supplied. Geometry alone does not establish verification.
          </p>
        )}
        <h4>Required physical verification</h4>
        {verification.length ? (
          <ul>
            {verification.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="research-evidence-muted">
            No physical verification list supplied; qualification remains unavailable.
          </p>
        )}
        <h4>Source requirements</h4>
        {renderRecords(model.requirements, 'requirement')}
      </section>
    </details>
  );
}
