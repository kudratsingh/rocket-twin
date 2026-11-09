import { useEffect, useMemo, useState } from 'react';
import type { InspectionDocument, JsonValue } from '../types';
import { filteredBankDefinitions, loadPartsBank } from './partsBank';
import type { BankDefinition, BankFilters, BankLoad, PartsBankCatalog } from './partsBank';
import './partsBank.css';

type LoadState =
  | { status: 'loading' }
  | { status: 'ready'; value: BankLoad }
  | { status: 'error'; message: string };

const maturityNames: Record<string, string> = {
  source_dimensioned: 'Source dimensions',
  simplified_envelope: 'Envelope',
  mass_allowance: 'Mass allowance',
  missing_geometry: 'No geometry',
};
const maturityColors: Record<string, string> = {
  source_dimensioned: '#62cad9',
  simplified_envelope: '#a08ccf',
  mass_allowance: '#d7ac68',
  missing_geometry: '#9ca9b2',
};

function label(value: string): string {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function grams(value: number | null): string {
  return value === null ? 'Unavailable' : `${(value * 1000).toFixed(2)} g`;
}

function sourceValue(key: string, value: JsonValue): string {
  if (typeof value === 'number') {
    if (key.endsWith('_m')) return `${(value * 1000).toFixed(2)} mm`;
    if (key.endsWith('_kg')) return `${(value * 1000).toFixed(2)} g`;
    if (key.endsWith('_deg')) return `${value}°`;
    return String(value);
  }
  if (Array.isArray(value)) {
    const values = value.map((entry) =>
      typeof entry === 'number' && key.endsWith('_m') ? (entry * 1000).toFixed(2) : String(entry),
    );
    return `${values.join(' × ')}${key.endsWith('_m') ? ' mm' : ''}`;
  }
  if (value && typeof value === 'object')
    return Object.entries(value)
      .map(([name, entry]) => `${label(name)}: ${String(entry)}`)
      .join('; ');
  return value === null ? 'Unavailable' : String(value);
}

function SourceAxis({
  catalog,
  selectedId,
  visibleIds,
  onSelect,
}: {
  catalog: PartsBankCatalog;
  selectedId: string;
  visibleIds: Set<string>;
  onSelect: (id: string) => void;
}) {
  const lastStation = Math.max(0, ...catalog.instances.map((instance) => instance.position_m ?? 0));
  const length = Math.max(0.25, Math.ceil(lastStation / 0.25) * 0.25);
  const ticks = Array.from({ length: Math.round(length / 0.25) + 1 }, (_, index) => index * 0.25);
  const instances = catalog.instances.filter(
    (instance) =>
      visibleIds.has(instance.id) &&
      instance.position_m !== null &&
      instance.position_m >= 0 &&
      instance.position_m <= length,
  );
  return (
    <div className="parts-bank-axis-block">
      <div className="parts-bank-axis-heading">
        <strong>Installed axial station</strong>
        <span>Source placement from nose tip · not a CAD silhouette</span>
      </div>
      <svg
        viewBox="0 0 640 104"
        role="img"
        aria-label="Source axial stations from nose to aft, with selected part marked"
      >
        <line x1="30" y1="57" x2="610" y2="57" stroke="#7d9fb2" strokeWidth="2" />
        {ticks.map((station) => {
          const x = 30 + (station / length) * 580;
          return (
            <g key={station}>
              <line x1={x} x2={x} y1="50" y2="64" stroke="#8ca5b5" />
              <text x={x} y="84" textAnchor="middle" fill="#b9cfdb" fontSize="11">
                {(station * 1000).toFixed(0)}
              </text>
            </g>
          );
        })}
        {instances.map((instance, index) => {
          const definition = catalog.definitions.find(
            (part) => part.source_part_id === instance.id,
          );
          const selected = instance.id === selectedId;
          const x = 30 + (instance.position_m! / length) * 580;
          return (
            <circle
              key={instance.id}
              cx={x}
              cy={selected ? 36 : 46 + (index % 3) * 5}
              r={selected ? 7 : 2.7}
              fill={maturityColors[definition?.geometry.maturity ?? 'missing_geometry']}
              stroke={selected ? '#fff5cb' : 'none'}
              strokeWidth="2"
              onClick={() => onSelect(instance.id)}
            >
              <title>
                {definition?.name ?? instance.id} · {(instance.position_m! * 1000).toFixed(1)} mm
              </title>
            </circle>
          );
        })}
        <text x="30" y="99" fill="#b9cfdb" fontSize="11">
          Nose
        </text>
        <text x="610" y="99" textAnchor="end" fill="#b9cfdb" fontSize="11">
          Aft · mm
        </text>
      </svg>
    </div>
  );
}

function Detail({
  definition,
  catalog,
  vehicle,
  onInspect,
}: {
  definition: BankDefinition;
  catalog: PartsBankCatalog;
  vehicle: InspectionDocument;
  onInspect: (partId: string) => void;
}) {
  const instance = catalog.instances.find((item) => item.id === definition.source_part_id)!;
  const installedPart = vehicle.parts.find((part) => part.id === definition.source_part_id)!;
  const dimensions = Object.entries(definition.dimensions.values);
  return (
    <article className="parts-bank-detail" aria-label={`${definition.name} source definition`}>
      <div className="parts-bank-detail-head">
        <div>
          <span className="parts-bank-eyebrow">Source definition · {definition.id}</span>
          <h2>{definition.name}</h2>
          <p>{definition.function || 'Function unavailable in the source record.'}</p>
        </div>
        <span
          className="parts-bank-maturity"
          style={{ borderColor: maturityColors[definition.geometry.maturity] }}
        >
          {maturityNames[definition.geometry.maturity] ?? label(definition.geometry.maturity)}
        </span>
      </div>
      {definition.issues.length > 0 && (
        <aside className="parts-bank-issues" aria-label="Unresolved source issues">
          {definition.issues.map((issue) => (
            <p key={issue.id}>
              <strong>{label(issue.id)} · unresolved.</strong> {issue.message}
            </p>
          ))}
        </aside>
      )}
      <div className="parts-bank-primary-action">
        <button type="button" onClick={() => onInspect(instance.id)}>
          Inspect installed part and available CAD/evidence
        </button>
        <span>
          Opens current Design part <code>{instance.id}</code>; this definition is not a draft part.
        </span>
      </div>
      <div className="parts-bank-facts">
        <div>
          <span>Definition / revision</span>
          <strong>
            <code>{definition.id}</code>
          </strong>
          <small>{definition.revision_sha256.slice(0, 16)}…</small>
        </div>
        <div>
          <span>Installed occurrence</span>
          <strong>
            <code>{instance.id}</code>
          </strong>
          <small>
            One source record · {instance.group_count} grouped{' '}
            {instance.group_count === 1 ? 'item' : 'items'}
          </small>
        </div>
        <div>
          <span>Placement</span>
          <strong>
            {instance.position_m === null
              ? 'Unavailable'
              : `${(instance.position_m * 1000).toFixed(2)} mm aft`}
          </strong>
          <small>Source position; no mating fit inferred</small>
        </div>
        <div>
          <span>Mass</span>
          <strong>{grams(definition.mass_kg)}</strong>
          <small>{definition.mass_basis}</small>
        </div>
        <div>
          <span>Material</span>
          <strong>{definition.material}</strong>
          <small>{definition.source_cad_role.replaceAll('_', ' ')} role</small>
        </div>
        <div>
          <span>Price basis</span>
          <strong>
            {definition.price.amount_usd === null
              ? 'Unquoted'
              : definition.price.amount_usd === 0
                ? '$0 source budget · not free'
                : `$${definition.price.amount_usd.toFixed(2)} source budget`}
          </strong>
          <small>
            Not a current unit quote or owner stock credit; shared stock may be charged elsewhere
          </small>
        </div>
      </div>
      <div className="parts-bank-detail-grid">
        <section>
          <h3>Source dimensions</h3>
          <p className="parts-bank-note">
            Nominal source geometry. Metre fields display as millimetres; dimensionless counts and
            named angle units remain separate.
          </p>
          {dimensions.length ? (
            <dl className="parts-bank-dimensions">
              {dimensions.map(([key, value]) => (
                <div key={key}>
                  <dt>{label(key)}</dt>
                  <dd>{sourceValue(key, value)}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p>Dimensions unavailable in this source record.</p>
          )}
        </section>
        <section>
          <h3>Geometry and reuse</h3>
          <p>
            {definition.geometry.mesh_available
              ? 'Matching globally placed inspection GLB for this installed occurrence. It is not a local reusable part template.'
              : (definition.geometry.reason ?? 'No separate inspection geometry.')}
          </p>
          <dl className="parts-bank-dimensions">
            <div>
              <dt>Representation</dt>
              <dd>
                {maturityNames[definition.geometry.maturity] ?? label(definition.geometry.maturity)}
              </dd>
            </div>
            <div>
              <dt>Reuse</dt>
              <dd>{definition.reuse_status.replaceAll('_', ' ')}</dd>
            </div>
            <div>
              <dt>Mesh scope / frame</dt>
              <dd>
                {definition.geometry.mesh_scope === 'installed_reference'
                  ? `Installed occurrence ${definition.geometry.registered_instance_id} · ${definition.geometry.frame}`
                  : 'No registered inspection mesh'}
              </dd>
            </div>
            <div>
              <dt>Definition source</dt>
              <dd>{definition.provenance[0]?.path ?? 'Unavailable'}</dd>
            </div>
            <div>
              <dt>Installed parent</dt>
              <dd>{instance.source_parent_id ?? 'Whole assembly'}</dd>
            </div>
          </dl>
          {installedPart.mesh_url ? (
            <p className="parts-bank-note">
              The current inspector provides matching installed-reference viewer and scoped CAD
              actions.
            </p>
          ) : (
            <p className="parts-bank-note">
              This installed record has no selectable display solid; CAD actions may be unavailable.
            </p>
          )}
        </section>
      </div>
      <section className="parts-bank-source-section">
        <h3>Source references</h3>
        <ul>
          {definition.provenance.map((source) => (
            <li key={`${source.path}:${source.role}`}>
              <strong>{source.role}</strong> · <code>{source.path}</code> · SHA{' '}
              {source.sha256.slice(0, 12)}… · <code>{source.locator}</code>
            </li>
          ))}
        </ul>
        {!definition.issues.length && (
          <p className="parts-bank-note">
            No cataloged product-identity conflict for this record. Installed engineering and
            physical evidence remain separate.
          </p>
        )}
      </section>
    </article>
  );
}

export default function PartsBankPanel({
  vehicle,
  onInspect,
}: {
  vehicle: InspectionDocument;
  onInspect: (partId: string) => void;
}) {
  const [load, setLoad] = useState<LoadState>({ status: 'loading' });
  const [filters, setFilters] = useState<BankFilters>({
    query: '',
    kind: '',
    material: '',
    maturity: '',
  });
  const [selectedId, setSelectedId] = useState<string>('fin_set');
  useEffect(() => {
    const abort = new AbortController();
    setLoad({ status: 'loading' });
    loadPartsBank(vehicle, fetch, abort.signal)
      .then((value) => {
        if (!abort.signal.aborted) setLoad({ status: 'ready', value });
      })
      .catch((error: unknown) => {
        if (!abort.signal.aborted)
          setLoad({
            status: 'error',
            message: error instanceof Error ? error.message : 'Unknown source error.',
          });
      });
    return () => abort.abort();
  }, [vehicle]);
  const catalog = load.status === 'ready' ? load.value.catalog : null;
  const filtered = useMemo(
    () => (catalog ? filteredBankDefinitions(catalog, filters) : []),
    [catalog, filters],
  );
  const selected =
    filtered.find((definition) => definition.source_part_id === selectedId) ?? filtered[0];
  useEffect(() => {
    if (filtered.length && !filtered.some((definition) => definition.source_part_id === selectedId))
      setSelectedId(filtered[0].source_part_id);
  }, [filtered, selectedId]);
  const options = (field: 'kind' | 'material' | 'maturity') =>
    catalog
      ? [
          ...new Set(
            catalog.definitions.map((definition) =>
              field === 'maturity' ? definition.geometry.maturity : definition[field],
            ),
          ),
        ].sort()
      : [];
  return (
    <section className="parts-bank" aria-label="RP1 source-owned parts bank">
      <header className="parts-bank-header">
        <div>
          <span className="parts-bank-eyebrow">Design · Parts bank · read only</span>
          <h1>Explore the current RP1 source</h1>
          <p>
            Definitions explain a source record. Installed occurrences identify where that record
            belongs in this exact vehicle.
          </p>
        </div>
        <div className="parts-bank-header-meta">
          <strong>55 definitions · 55 occurrences</strong>
          <span>{load.status === 'ready' ? load.value.transport : 'Source admission pending'}</span>
          <small>Current RP1 / AD1 v2 · no draft editing in this slice</small>
        </div>
      </header>
      {load.status === 'loading' && (
        <p className="parts-bank-state" role="status">
          Loading and verifying the current source catalog…
        </p>
      )}
      {load.status === 'error' && (
        <p className="parts-bank-state parts-bank-error" role="alert">
          Parts bank unavailable: {load.message} Existing Design inspection remains available.
        </p>
      )}
      {catalog && (
        <>
          <div className="parts-bank-toolbar">
            <label>
              Search
              <input
                type="search"
                value={filters.query}
                onChange={(event) => setFilters({ ...filters, query: event.target.value })}
                placeholder="Part, material or function…"
              />
            </label>
            <label>
              Kind
              <select
                value={filters.kind}
                onChange={(event) => setFilters({ ...filters, kind: event.target.value })}
              >
                <option value="">All kinds</option>
                {options('kind').map((value) => (
                  <option key={value} value={value}>
                    {label(value)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Material
              <select
                value={filters.material}
                onChange={(event) => setFilters({ ...filters, material: event.target.value })}
              >
                <option value="">All materials</option>
                {options('material').map((value) => (
                  <option key={value} value={value}>
                    {label(value)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Geometry
              <select
                value={filters.maturity}
                onChange={(event) => setFilters({ ...filters, maturity: event.target.value })}
              >
                <option value="">All maturity</option>
                {options('maturity').map((value) => (
                  <option key={value} value={value}>
                    {maturityNames[value] ?? label(value)}
                  </option>
                ))}
              </select>
            </label>
            <span className="parts-bank-result-count">{filtered.length} of 55 records</span>
          </div>
          <SourceAxis
            catalog={catalog}
            selectedId={selected?.source_part_id ?? ''}
            visibleIds={new Set(filtered.map((part) => part.source_part_id))}
            onSelect={setSelectedId}
          />
          <div className="parts-bank-workarea">
            <nav className="parts-bank-list" aria-label="Source definitions">
              {filtered.length ? (
                filtered.map((definition) => (
                  <button
                    key={definition.id}
                    type="button"
                    aria-pressed={selected?.source_part_id === definition.source_part_id}
                    onClick={() => setSelectedId(definition.source_part_id)}
                  >
                    <span
                      className="parts-bank-list-dot"
                      style={{ background: maturityColors[definition.geometry.maturity] }}
                    />
                    <span>
                      <strong>{definition.name}</strong>
                      <small>
                        <code>{definition.source_part_id}</code> · {label(definition.kind)} ·{' '}
                        {definition.material}
                      </small>
                    </span>
                    {definition.issues.length > 0 && (
                      <em title="Unresolved source identity issue">Issue</em>
                    )}
                  </button>
                ))
              ) : (
                <p className="parts-bank-empty">
                  No matching source records. Adjust the filters to return to all 55.
                </p>
              )}
            </nav>
            {selected ? (
              <Detail
                key={selected.id}
                definition={selected}
                catalog={catalog}
                vehicle={vehicle}
                onInspect={onInspect}
              />
            ) : (
              <div className="parts-bank-detail parts-bank-empty">
                No source record matches these filters. The active part is not changed; clear a
                filter to inspect a record.
              </div>
            )}
          </div>
          <footer className="parts-bank-footer">
            Source budget and inspection geometry are not installed proof. No Add, Replace or
            Connect commands are available in this read-only catalog.
          </footer>
        </>
      )}
    </section>
  );
}
