import { DataList } from '../components/InspectionPanel';
import { Icon } from '../components/Icons';
import { displayValue, partName, title } from '../format';
import { useInspection } from '../store';
import type { InspectionDocument, JsonValue } from '../types';
import { displayUnit, quantityName, scalarText } from './display';
import { HistoryPlot } from './HistoryPlot';
import type { AnalysisField, AnalysisManifest, AnalysisPayload } from './types';

function records(value: JsonValue | undefined): Record<string, JsonValue>[] {
  return Array.isArray(value)
    ? value.filter(
        (item): item is Record<string, JsonValue> =>
          !!item && typeof item === 'object' && !Array.isArray(item),
      )
    : [];
}
function List({ values }: { values: string[] }) {
  return (
    <ul className="plain-list small">
      {values.map((value, index) => (
        <li key={index}>{value}</li>
      ))}
    </ul>
  );
}

export function AnalysisEvidencePanel({
  vehicle,
  manifest,
  field,
  payload,
  sample,
  error,
  onSample,
}: {
  vehicle: InspectionDocument;
  manifest: AnalysisManifest | null;
  field: AnalysisField | undefined;
  payload: AnalysisPayload | null;
  sample: number;
  error: string;
  onSample: (index: number) => void;
}) {
  const selectedId = useInspection((s) => s.selectedId);
  const select = useInspection((s) => s.select);
  const part = vehicle.parts.find((entry) => entry.id === selectedId);
  const partIndex = field && part ? field.part_ids.indexOf(part.id) : -1;
  const partScalar =
    field?.association === 'part' && partIndex >= 0 ? payload?.values[sample]?.[partIndex] : null;
  const peaks = field
    ? records(field.reported_extrema.part_mean_peaks || field.reported_extrema.parts).find(
        (entry) => entry.part_id === part?.id,
      )
    : undefined;
  return (
    <aside className="inspection-panel analysis-evidence">
      <div className="inspector-scroll">
        <div className="panel-heading">
          <span className="eyebrow">Analysis evidence</span>
          {part && (
            <button
              className="icon-button"
              onClick={() => select(null)}
              aria-label="Clear selected part"
            >
              <Icon name="close" />
            </button>
          )}
        </div>
        <h2>{part ? partName(part) : 'Recorded field & coverage'}</h2>
        <p className="summary-description">
          {part
            ? part.function || part.engineering?.function
            : 'Select a part in the tree or viewport to inspect its field coverage, history and reported peaks.'}
        </p>
        {error && (
          <div className="notice negative small">
            <Icon name="warning" />
            {error}
          </div>
        )}
        {!field ? (
          <div className="notice small">
            No field is attached. Neutral geometry remains available for part inspection.
          </div>
        ) : (
          <>
            <div className="analysis-provenance">
              <span className={`provenance-${field.evidence.provenance}`}>
                {title(field.evidence.provenance)}
              </span>
              <span>{title(field.evidence.validation)}</span>
            </div>
            <section className="detail-section">
              <h3>{quantityName[field.quantity]}</h3>
              <p className="body-copy">{field.component}</p>
              <DataList
                data={{
                  field_resolution:
                    field.association === 'part'
                      ? 'Uniform part mean / part-level scalar'
                      : field.association === 'node'
                        ? 'Analysis mesh node values; color interpolation is display only'
                        : field.association === 'element'
                          ? 'Element values; discontinuities retained'
                          : field.association,
                  units: `${field.units} (source); ${displayUnit[field.quantity]} (display)`,
                  current_analysis_time: field.times_s
                    ? `${field.times_s[sample]} s — exact solver sample`
                    : 'Static load case; no time axis',
                }}
              />
              <p className="small muted">{field.coverage_notes}</p>
              {part && (
                <div
                  className={`coverage-state ${partIndex < 0 || (partScalar == null && field.association === 'part') ? 'no-coverage' : ''}`}
                >
                  {partIndex < 0
                    ? 'Unavailable for this part — outside recorded coverage.'
                    : field.association === 'part'
                      ? `Recorded value: ${scalarText(partScalar, field.quantity)}`
                      : 'This part contains the one registered analysis-mesh instance. Other physical fin instances are not colored by this field.'}
                </div>
              )}
              {part && field.association === 'part' && payload && (
                <HistoryPlot
                  field={field}
                  payload={payload}
                  partId={part.id}
                  sample={sample}
                  onSample={onSample}
                />
              )}
            </section>
            <section className="detail-section">
              <h3>Reported solver peaks & limits</h3>
              <p className="small muted">
                These are the recorded extrema and screening decisions. The browser does not
                recompute engineering peaks or margins.
              </p>
              {peaks ? (
                <DataList data={peaks} />
              ) : typeof field.reported_extrema.maximum === 'number' ? (
                <DataList
                  data={{
                    reported_maximum: scalarText(field.reported_extrema.maximum, field.quantity),
                    reported_minimum:
                      typeof field.reported_extrema.minimum === 'number'
                        ? scalarText(field.reported_extrema.minimum, field.quantity)
                        : undefined,
                  }}
                />
              ) : (
                <p className="small muted">
                  {part
                    ? 'No separate part peak record is available for this selection.'
                    : 'Select a covered part to read its recorded peak and limit.'}
                </p>
              )}
              {field.margin_definition && (
                <p className="body-copy">Margin definition: {field.margin_definition}</p>
              )}
              <details className="print-details">
                <summary>All raw recorded extrema</summary>
                <DataList data={field.reported_extrema} />
              </details>
            </section>
            <section className="detail-section">
              <h3>Validation & uncertainty</h3>
              <div className="notice small">
                Calculated or numerically verified results do not establish physical validation.
                Engineering acceptance remains open.
              </div>
              <DataList
                data={{
                  known_case_verified: field.evidence.known_case_verified,
                  mesh_converged: field.evidence.mesh_converged,
                  uncertainty: field.evidence.uncertainty,
                }}
              />
              <h4>Assumptions</h4>
              <List values={field.evidence.assumptions} />
              <h4>Limits & excluded regions</h4>
              <List values={field.evidence.limits} />
            </section>
            <section className="detail-section">
              <h3>Required physical tests</h3>
              <List values={field.evidence.required_physical_tests} />
            </section>
            <section className="detail-section">
              <h3>Sources & artifacts</h3>
              <List values={field.evidence.sources} />
              {field.evidence.report && (
                <p className="small muted">Report: {field.evidence.report}</p>
              )}
              {field.artifact && manifest?.artifacts[field.artifact] && (
                <a
                  className="source-link"
                  href={manifest.artifacts[field.artifact]}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open original recorded field artifact <Icon name="external" size={11} />
                </a>
              )}
              {manifest && <DataList data={manifest.tools} />}
              <div className="hash-block">
                <span>Field artifact SHA-256</span>
                <code title={field.artifact_sha256 || ''}>
                  {field.artifact_sha256 || 'Unavailable'}
                </code>
              </div>
              {field.mesh_sha256 && (
                <div className="hash-block">
                  <span>Analysis mesh SHA-256 — separate from CAD display mesh</span>
                  <code title={field.mesh_sha256}>{field.mesh_sha256}</code>
                </div>
              )}
            </section>
            {manifest && (
              <section className="detail-section">
                <h3>Recorded load / boundary case</h3>
                <details className="print-details">
                  <summary>{field.case_id}</summary>
                  <DataList data={manifest.cases[field.case_id] || {}} />
                </details>
              </section>
            )}
          </>
        )}
        {part?.requirements?.length ? (
          <section className="detail-section">
            <h3>Linked requirement identities</h3>
            {records(part.requirements).map((requirement) => (
              <div className="requirement-summary" key={String(requirement.id)}>
                <strong>
                  {String(requirement.id)} · {String(requirement.status || 'open')}
                </strong>
                <p>{String(requirement.acceptance || '')}</p>
                <small>
                  {displayValue(
                    'verification_method',
                    requirement.verification_method || 'Unavailable',
                  )}
                </small>
              </div>
            ))}
          </section>
        ) : null}
        {manifest && (
          <section className="detail-section source-section">
            <h3>Exact configuration identity</h3>
            <div className="hash-block">
              <span>Resolved specification SHA-256</span>
              <code>{manifest.identity.resolved_spec_sha256}</code>
            </div>
            <div className="hash-block">
              <span>CAD revision SHA-256</span>
              <code>{manifest.identity.cad_revision_sha256}</code>
            </div>
            <p className="small muted">Run: {manifest.run_id}</p>
          </section>
        )}
      </div>
      <div className="inspector-footer">
        Recorded engineering time · no browser solver · no flight release
      </div>
    </aside>
  );
}
