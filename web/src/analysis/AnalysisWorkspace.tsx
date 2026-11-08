import RecordedCaseComparison from './RecordedCaseComparison';
import Rp1RecordedAnalysis from './Rp1RecordedAnalysis';
import { useEffect, useMemo, useState } from 'react';
import { getJson } from '../api';
import { Icon } from '../components/Icons';
import { PartsTree } from '../components/PartsTree';
import { Viewer } from '../components/Viewer';
import { title } from '../format';
import { useInspection } from '../store';
import type { InspectionDocument } from '../types';
import { AnalysisEvidencePanel } from './AnalysisEvidencePanel';
import { AnalysisSurface } from './AnalysisSurface';
import {
  displayScalar,
  displayUnit,
  fieldColor,
  fieldBlockReason,
  fixedRange,
  identityMismatch,
  quantityName,
  validatePayload,
} from './display';
import type { AnalysisCatalog, AnalysisManifest, AnalysisPayload } from './types';
import './analysis.css';
import { analysisArtifactUrl, parseAnalysisCatalog, parseAnalysisManifest } from './responseGuard';

function RegisteredAnalysisWorkspace({
  vehicle,
  candidateMessage,
}: {
  vehicle: InspectionDocument;
  candidateMessage?: string;
}) {
  const [loadedCatalog, setCatalog] = useState<AnalysisCatalog | null>(null);
  const catalog = loadedCatalog?.vehicle_id === vehicle.id ? loadedCatalog : null;
  const [runId, setRunId] = useState('');
  const [loadedManifest, setManifest] = useState<AnalysisManifest | null>(null);
  const manifest =
    loadedManifest?.api_id === runId && loadedManifest.identity.configuration_id === vehicle.id
      ? loadedManifest
      : null;
  const [caseId, setCaseId] = useState('');
  const [fieldId, setFieldId] = useState('');
  const [payloadResult, setPayload] = useState<{ key: string; value: AnalysisPayload } | null>(
    null,
  );
  const [catalogError, setCatalogError] = useState('');
  const [manifestError, setManifestError] = useState('');
  const [payloadError, setPayloadError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sample, setSample] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [comparisonFieldId, setComparisonFieldId] = useState('');
  const [comparisonResult, setComparisonPayload] = useState<{
    key: string;
    value: AnalysisPayload;
  } | null>(null);
  const [comparisonError, setComparisonError] = useState('');
  const [autoRange, setAutoRange] = useState(false);
  const [minimum, setMinimum] = useState(0);
  const [maximum, setMaximum] = useState(300);
  const [outline, setOutline] = useState(false);
  const [catalogRetry, setCatalogRetry] = useState(0);
  const [manifestRetry, setManifestRetry] = useState(0);
  const [payloadRetry, setPayloadRetry] = useState(0);
  const [comparisonRetry, setComparisonRetry] = useState(0);
  const field = manifest?.fields.find((entry) => entry.id === fieldId && entry.case_id === caseId);
  const payloadKey = JSON.stringify([manifest?.api_id, field?.id, field?.artifact_sha256]);
  const payload = payloadResult?.key === payloadKey ? payloadResult.value : null;
  const quantity = field?.quantity;
  const mismatch = manifest ? identityMismatch(manifest, vehicle.id, vehicle.identity) : null;
  const fieldUnavailable = fieldBlockReason(field);

  useEffect(() => {
    useInspection.getState().setExploded(0);
    setCatalog(null);
    setCatalogError('');
    setRunId('');
    const controller = new AbortController();
    void getJson<unknown>(
      `/api/vehicles/${encodeURIComponent(vehicle.id)}/analyses`,
      controller.signal,
    )
      .then((value) => {
        if (controller.signal.aborted) return;
        const data = parseAnalysisCatalog(value, vehicle.id);
        setCatalog(data);
        setRunId((data.analyses.find((entry) => entry.compatible) || data.analyses[0])?.id || '');
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted)
          setCatalogError(error instanceof Error ? error.message : 'Analysis catalog unavailable.');
      });
    return () => controller.abort();
  }, [vehicle.id, catalogRetry]);

  useEffect(() => {
    setManifest(null);
    setManifestError('');
    setPayload(null);
    setPayloadError('');
    setSample(0);
    setPlaying(false);
    const selectedRun = catalog?.analyses.find((entry) => entry.id === runId);
    if (!runId || !selectedRun) return;
    const controller = new AbortController();
    void getJson<unknown>(`/api/analyses/${encodeURIComponent(runId)}`, controller.signal)
      .then((value) => {
        if (controller.signal.aborted) return;
        const data = parseAnalysisManifest(value, runId, selectedRun.run_id, vehicle.id);
        setManifest(data);
        const initial =
          data.fields.find((entry) => entry.evidence.provenance !== 'unavailable') ||
          data.fields[0];
        setCaseId(initial?.case_id || Object.keys(data.cases)[0] || '');
        setFieldId(initial?.id || '');
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted)
          setManifestError(
            error instanceof Error ? error.message : 'Recorded manifest unavailable.',
          );
      });
    return () => controller.abort();
  }, [runId, catalog, manifestRetry, vehicle.id]);

  useEffect(() => {
    setPayload(null);
    setPayloadError('');
    setSample(0);
    setPlaying(false);
    if (!manifest || !field || mismatch || fieldUnavailable) return;
    let url: string;
    try {
      url = analysisArtifactUrl(manifest, field);
    } catch (reason) {
      setPayloadError(reason instanceof Error ? reason.message : 'Recorded artifact unavailable.');
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    void getJson<AnalysisPayload>(url, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        validatePayload(field, data);
        setPayload({ key: payloadKey, value: data });
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted)
          setPayloadError(error instanceof Error ? error.message : 'Recorded field unavailable.');
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => {
      controller.abort();
      setLoading(false);
    };
  }, [manifest, field, mismatch, fieldUnavailable, payloadKey, payloadRetry]);

  const comparisonField = manifest?.fields.find((item) => item.id === comparisonFieldId);
  const comparisonKey = JSON.stringify([
    manifest?.api_id,
    comparisonField?.id,
    comparisonField?.artifact_sha256,
  ]);
  const comparisonPayload = comparisonResult?.key === comparisonKey ? comparisonResult.value : null;
  useEffect(() => {
    setComparisonPayload(null);
    setComparisonError('');
    if (!manifest || !comparisonField || mismatch) return;
    const blocked = fieldBlockReason(comparisonField);
    if (blocked) {
      setComparisonError(blocked);
      return;
    }
    let url: string;
    try {
      url = analysisArtifactUrl(manifest, comparisonField);
    } catch (reason) {
      setComparisonError(
        reason instanceof Error ? reason.message : 'Comparison artifact unavailable.',
      );
      return;
    }
    const controller = new AbortController();
    void getJson<AnalysisPayload>(url, controller.signal)
      .then((value) => {
        if (controller.signal.aborted) return;
        validatePayload(comparisonField, value);
        setComparisonPayload({ key: comparisonKey, value });
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted)
          setComparisonError(reason instanceof Error ? reason.message : 'Comparison unavailable.');
      });
    return () => controller.abort();
  }, [manifest, comparisonField, mismatch, comparisonKey, comparisonRetry]);

  useEffect(() => {
    if (quantity) {
      const range = fixedRange[quantity];
      setMinimum(range[0]);
      setMaximum(range[1]);
    }
  }, [quantity]);

  useEffect(() => {
    if (!playing || !field?.times_s) return;
    const total = field.times_s.length;
    const interval = window.setInterval(
      () =>
        setSample((current) => {
          if (current >= total - 1) {
            setPlaying(false);
            return current;
          }
          return current + 1;
        }),
      125,
    );
    return () => window.clearInterval(interval);
  }, [playing, field]);

  const range = useMemo<[number, number]>(() => {
    if (!autoRange || !field || !payload) return [minimum, maximum];
    let low = Infinity,
      high = -Infinity;
    for (const frame of payload.values)
      for (const value of frame)
        if (value != null) {
          const converted = displayScalar(value, field.quantity);
          low = Math.min(low, converted);
          high = Math.max(high, converted);
        }
    return Number.isFinite(low) ? [low, high === low ? high + 1 : high] : [minimum, maximum];
  }, [autoRange, field, payload, minimum, maximum]);
  const validRange = Number.isFinite(range[0]) && Number.isFinite(range[1]) && range[1] > range[0];
  const error =
    catalogError ||
    manifestError ||
    mismatch ||
    fieldUnavailable ||
    payloadError ||
    (!validRange ? 'Display maximum must exceed display minimum.' : '');
  const attachable = !!field && !!payload && !error;
  const colors = useMemo(() => {
    const entries: Record<string, string | null> = Object.fromEntries(
      vehicle.parts.map((part) => [part.id, null]),
    );
    if (attachable && field?.association === 'part' && payload)
      for (const [index, id] of field.part_ids.entries()) {
        const value = payload.values[sample]?.[index];
        if (value != null)
          entries[id] = fieldColor(displayScalar(value, field.quantity), range[0], range[1]);
      }
    return entries;
  }, [vehicle.parts, attachable, field, payload, sample, range]);
  const isSpatial = attachable && field?.association !== 'part';
  const missing = Object.values(colors).filter((color) => color == null).length;
  const currentTime = field?.times_s?.[sample];
  const fieldsForCase = manifest?.fields.filter((entry) => entry.case_id === caseId) || [];
  function changeCase(id: string) {
    setCaseId(id);
    setFieldId(manifest?.fields.find((entry) => entry.case_id === id)?.id || '');
  }

  return (
    <main className="inspection-workspace analysis-workspace">
      <PartsTree parts={vehicle.parts} candidateMessage={candidateMessage} />
      <section className="analysis-center">
        <div className="analysis-toolbar">
          <label>
            Recorded analysis run
            <select
              aria-label="Recorded analysis run"
              value={runId}
              onChange={(event) => setRunId(event.target.value)}
              disabled={!catalog?.analyses.length}
            >
              {!catalog?.analyses.length && <option value="">No recorded runs available</option>}
              {catalog?.analyses.map((entry) => (
                <option key={entry.id} value={entry.id}>
                  {entry.compatible ? '' : 'Incompatible · '}
                  {entry.engineering_notice ? 'Superseded · ' : ''}
                  {entry.run_id}
                </option>
              ))}
            </select>
          </label>
          <label>
            Load / thermal case
            <select
              aria-label="Analysis load or thermal case"
              value={caseId}
              onChange={(event) => changeCase(event.target.value)}
              disabled={!manifest}
            >
              {Object.keys(manifest?.cases || {}).map((id) => (
                <option key={id} value={id}>
                  {title(id)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Quantity / component
            <select
              aria-label="Analysis quantity"
              value={fieldId}
              onChange={(event) => setFieldId(event.target.value)}
              disabled={!fieldsForCase.length}
            >
              {fieldsForCase.map((entry) => (
                <option key={entry.id} value={entry.id}>
                  {quantityName[entry.quantity]} · {entry.association}
                  {entry.evidence.provenance === 'unavailable' ? ' · unavailable' : ''}
                </option>
              ))}
            </select>
          </label>
        </div>
        {(catalogError || manifestError || payloadError) && (
          <div className="analysis-status">
            {catalogError && (
              <button type="button" onClick={() => setCatalogRetry((value) => value + 1)}>
                Retry analysis catalog
              </button>
            )}
            {manifestError && (
              <button type="button" onClick={() => setManifestRetry((value) => value + 1)}>
                Retry selected manifest
              </button>
            )}
            {payloadError && (
              <button type="button" onClick={() => setPayloadRetry((value) => value + 1)}>
                Retry recorded field
              </button>
            )}
            <small>
              Retries load existing recorded evidence only; no solver or flight run is started.
            </small>
          </div>
        )}
        <div className={`analysis-status ${error ? 'analysis-error' : ''}`} role="status">
          <Icon name={error ? 'warning' : 'layers'} size={14} />
          {error ||
            (loading
              ? 'Loading identity-checked recorded artifact…'
              : !catalog
                ? 'Loading recorded analysis catalog…'
                : !catalog.analyses.length
                  ? 'No recorded analysis exists for this exact configuration. Geometry remains neutral.'
                  : attachable
                    ? `${title(field!.evidence.provenance)} · ${title(field!.evidence.validation)} · ${field!.association === 'part' ? 'uniform part means; no spatial temperature gradient' : 'registered single-fin analysis mesh; other fin instances unavailable'}`
                    : 'Select an available, compatible recorded field.')}
        </div>
        {manifest?.engineering_notice && (
          <div className="analysis-status analysis-error" role="status">
            {manifest.engineering_notice}
          </div>
        )}
        <Viewer
          vehicle={vehicle}
          mass={null}
          burn={0}
          onBurnChange={() => undefined}
          overlay={{
            partColors: colors,
            baseOpacity: isSpatial ? 0.2 : 1,
            surface:
              isSpatial && field && payload ? (
                <AnalysisSurface
                  field={field}
                  payload={payload}
                  frame={sample}
                  minimum={range[0]}
                  maximum={range[1]}
                  outline={outline}
                />
              ) : undefined,
            caption: attachable
              ? `${quantityName[field!.quantity]} · ${field!.association === 'part' ? 'uniform part-level field' : `${field!.association} field on one fin`}`
              : 'Unavailable — no overlay attached',
            legend:
              attachable && validRange
                ? {
                    minimum: Number(range[0].toFixed(2)),
                    maximum: Number(range[1].toFixed(2)),
                    unit: displayUnit[field!.quantity],
                  }
                : undefined,
          }}
        />
        <div className="analysis-display-controls">
          <div className="analysis-range">
            <label>
              Color range min
              <input
                aria-label="Color range minimum"
                type="number"
                value={minimum}
                onChange={(event) => setMinimum(Number(event.target.value))}
                disabled={autoRange}
              />
            </label>
            <label>
              Max ({field ? displayUnit[field.quantity] : 'display units'})
              <input
                aria-label="Color range maximum"
                type="number"
                value={maximum}
                onChange={(event) => setMaximum(Number(event.target.value))}
                disabled={autoRange}
              />
            </label>
            <label className="analysis-check">
              <input
                type="checkbox"
                checked={autoRange}
                onChange={(event) => setAutoRange(event.target.checked)}
              />
              Auto-range
            </label>
            {isSpatial && (
              <label className="analysis-check">
                <input
                  type="checkbox"
                  checked={outline}
                  onChange={(event) => setOutline(event.target.checked)}
                />
                Mesh outline
              </label>
            )}
          </div>
          <p>
            {autoRange
              ? 'Auto-range uses all recorded frames of this field for display only.'
              : 'Fixed display limits stay constant across cases and time. Colors are not pass/fail criteria.'}{' '}
            {isSpatial
              ? 'Scalar values only; no deformed geometry or displacement amplification is inferred.'
              : `${missing} of ${vehicle.parts.length} parts have unavailable field coverage.`}
          </p>
        </div>
        <section className="rp1-recorded-findings">
          <label>
            Compare recorded case / quantity
            <select
              value={comparisonFieldId}
              onChange={(event) => setComparisonFieldId(event.target.value)}
              disabled={!manifest}
            >
              <option value="">No comparison selected</option>
              {manifest?.fields.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.case_id} · {quantityName[item.quantity]} · {item.component}
                </option>
              ))}
            </select>
          </label>
          {comparisonError && (
            <p role="alert">
              {comparisonError}{' '}
              <button type="button" onClick={() => setComparisonRetry((value) => value + 1)}>
                Retry comparison artifact
              </button>
            </p>
          )}
          <RecordedCaseComparison
            left={manifest && field && payload && !error ? { manifest, field, payload } : null}
            right={
              manifest && comparisonField && comparisonPayload && !comparisonError
                ? { manifest, field: comparisonField, payload: comparisonPayload }
                : null
            }
          />
        </section>
        <div className="analysis-time">
          <button
            onClick={() => {
              if (field?.times_s && sample >= field.times_s.length - 1) setSample(0);
              setPlaying(!playing);
            }}
            disabled={!attachable || !field?.times_s}
          >
            {playing ? 'Pause' : 'Play samples'}
          </button>
          {field?.times_s ? (
            <>
              <input
                aria-label="Recorded analysis sample"
                type="range"
                min="0"
                max={field.times_s.length - 1}
                step="1"
                value={sample}
                onChange={(event) => {
                  setPlaying(false);
                  setSample(Number(event.target.value));
                }}
              />
              <span>
                {currentTime?.toFixed(2)} s
                <small>
                  Exact solver time · sample {sample + 1}/{field.times_s.length}
                </small>
              </span>
            </>
          ) : (
            <span>
              Static load case<small>No time axis is fabricated</small>
            </span>
          )}
          <small className="sample-rate">
            {field?.times_s
              ? 'Playback: 8 samples/s · exact solver timestamps · no flight mapping'
              : 'Recorded static result'}
          </small>
        </div>
      </section>
      <AnalysisEvidencePanel
        vehicle={vehicle}
        manifest={manifest}
        field={field}
        payload={attachable ? payload : null}
        sample={sample}
        error={error}
        onSample={setSample}
      />
    </main>
  );
}

export default function AnalysisWorkspace(props: {
  vehicle: InspectionDocument;
  candidateMessage?: string;
}) {
  return props.vehicle.id === 'G80-F2-RP1-AD1-definition-v2' ? (
    <Rp1RecordedAnalysis {...props} />
  ) : (
    <RegisteredAnalysisWorkspace {...props} />
  );
}
