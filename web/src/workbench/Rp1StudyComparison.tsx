import { useEffect, useId, useRef, useState } from 'react';
import { loadRp1Studies, rp1Quantity } from './rp1Studies';
import type { Rp1Studies, Rp1Study } from './rp1Studies';
import './rp1StudyComparison.css';
import { downloadRp1StudySvg } from './rp1StudyExport';

function wrap(text: string, length = 32) {
  const lines = [''];
  for (const word of text.split(/\s+/)) {
    const index = lines.length - 1;
    if (lines[index] && lines[index].length + word.length > length) lines.push(word);
    else lines[index] += `${lines[index] ? ' ' : ''}${word}`;
  }
  return lines;
}

/** Source relationships only. Box coordinates and arrows are presentation, not physical geometry. */
export function Rp1StudyGraph({
  study,
  selected,
  onSelect,
}: {
  study: Rp1Study;
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  const titleId = useId();
  if (!study.nodes.length)
    return <p>Source relationship graphic unavailable — no nodes supplied.</p>;
  const y = (id: string) => 32 + study.nodes.findIndex((node) => node.id === id) * 140;
  return (
    <svg
      className="rp1-study-graph"
      viewBox={`0 0 600 ${study.nodes.length * 140 + 20}`}
      role="group"
      aria-labelledby={titleId}
    >
      <title id={titleId}>{`${study.label}: source relationships, unaccepted study`}</title>
      <metadata>
        {JSON.stringify({
          id: study.id,
          source: study.source,
          status: study.status,
          adopted: false,
          installed_accepted: false,
        })}
      </metadata>
      {study.edges.map((edge, index) => {
        const start = y(edge.from) + 36,
          end = y(edge.to) + 36;
        const lane = 450 + index * 20;
        return (
          <g key={`${edge.from}-${edge.to}-${index}`}>
            <path
              d={`M 430 ${start} H ${lane} V ${end} H 440`}
              fill="none"
              stroke="#8fa6b9"
              strokeWidth="2"
            />
            <polygon points={`430,${end} 442,${end - 5} 442,${end + 5}`} fill="#b7ccda" />
            <title>{edge.label}</title>
            <circle cx={lane} cy={(start + end) / 2} r="9" fill="#121e2b" stroke="#8fa6b9" />
            <text
              x={lane}
              y={(start + end) / 2 + 4}
              textAnchor="middle"
              fill="#dbe7ef"
              fontSize="11"
            >
              {index + 1}
            </text>
          </g>
        );
      })}
      {study.nodes.map((node) => (
        <g
          key={node.id}
          role="button"
          tabIndex={0}
          aria-pressed={selected === node.id}
          aria-label={`${node.label}: ${node.status}`}
          onClick={() => onSelect(node.id)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              onSelect(node.id);
            }
          }}
          className="rp1-graph-node"
        >
          <rect
            x="18"
            y={y(node.id)}
            width="412"
            height="86"
            rx="6"
            fill={selected === node.id ? '#244358' : '#1c2c3b'}
            stroke={selected === node.id ? '#94ddff' : '#6b859a'}
          />
          {wrap(node.label, 43).map((line, index) => (
            <text key={index} x="32" y={y(node.id) + 24 + index * 18} fill="#f1f6fa" fontSize="15">
              {line}
            </text>
          ))}
          <text x="32" y={y(node.id) + 73} fill="#f4c87a" fontSize="12">
            {node.status}
          </text>
        </g>
      ))}
    </svg>
  );
}

function StudyCard({ study, snapshot }: { study: Rp1Study; snapshot: Rp1Studies }) {
  const graphRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1);
  const [exportStatus, setExportStatus] = useState('');
  const [selected, setSelected] = useState<string | null>(study.nodes[0]?.id ?? null);
  const node = study.nodes.find((item) => item.id === selected);
  return (
    <article className="rp1-study-card">
      <h2>{study.label}</h2>
      <p className="rp1-unaccepted">UNACCEPTED · not adopted · installed acceptance false</p>
      <p>
        <code>{study.id}</code>
      </p>
      <p>{study.status}</p>
      <p>{study.maturity}</p>
      <dl className="rp1-study-metrics">
        <div>
          <dt>Reported tip movement</dt>
          <dd>{rp1Quantity(study.displacement.reported_mm, 'mm')}</dd>
        </div>
        <div>
          <dt>Recorded movement limit</dt>
          <dd>{rp1Quantity(study.displacement.limit_mm, 'mm')}</dd>
        </div>
        <div>
          <dt>Unverified attachment budget</dt>
          <dd>{rp1Quantity(study.displacement.attachment_budget_mm, 'mm')}</dd>
        </div>
        <div>
          <dt>Conditional mass credit — not adopted</dt>
          <dd>{rp1Quantity(study.mass.conditional_credit_g, 'g')}</dd>
        </div>
      </dl>
      <p>{study.displacement.note}</p>
      {study.id === 'G80-F2-RP1-FP1-carbon-faced-plywood-screen-v1' && (
        <p>
          The reported FP1 movement already includes the 0.100 mm unverified attachment budget; do
          not add it again. This is not an installed pass.
        </p>
      )}
      <p>{study.mass.note}</p>
      <div className="rp1-graph-controls" aria-label={`${study.label} graph controls`}>
        <button
          type="button"
          disabled={zoom <= 0.75}
          onClick={() => setZoom((value) => Math.max(0.75, value - 0.25))}
        >
          Zoom out
        </button>
        <button
          type="button"
          disabled={zoom >= 2}
          onClick={() => setZoom((value) => Math.min(2, value + 0.25))}
        >
          Zoom in
        </button>
        <button
          type="button"
          onClick={() => {
            setZoom(1);
            graphRef.current?.scrollTo({ top: 0, left: 0 });
          }}
        >
          Fit width / reset graph
        </button>
        <span aria-live="polite">{Math.round(zoom * 100)}%</span>
        <button
          type="button"
          disabled={!study.nodes.length}
          onClick={() => {
            try {
              downloadRp1StudySvg(
                graphRef.current?.querySelector('svg') ?? null,
                snapshot,
                study.id,
              );
              setExportStatus(
                'SVG download requested with source identity, relationship key and unaccepted scope.',
              );
            } catch (reason) {
              setExportStatus(reason instanceof Error ? reason.message : 'SVG export unavailable.');
            }
          }}
        >
          Export study SVG
        </button>
      </div>
      <p role="status">{exportStatus}</p>
      <div
        ref={graphRef}
        className="rp1-graph-scroll"
        role="region"
        aria-label={`${study.label} zoomable relationship graph`}
        tabIndex={0}
      >
        <div style={{ width: `${zoom * 100}%` }}>
          <Rp1StudyGraph study={study} selected={selected} onSelect={setSelected} />
        </div>
      </div>
      <ol className="rp1-relationship-key" aria-label={`${study.label} graphic relationship key`}>
        {study.edges.map((edge, index) => (
          <li key={index}>
            {study.nodes.find((node) => node.id === edge.from)?.label} →{' '}
            {study.nodes.find((node) => node.id === edge.to)?.label}: {edge.label}
          </li>
        ))}
      </ol>
      <div className="rp1-node-buttons" aria-label={`${study.label} relationship selection`}>
        {study.nodes.map((item) => (
          <button
            key={item.id}
            type="button"
            aria-pressed={selected === item.id}
            onClick={() => setSelected(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <section
        className="rp1-node-detail"
        aria-live="polite"
        aria-label={`${study.label} selected relationship`}
      >
        {node ? (
          <>
            <h3>{node.label}</h3>
            <p>{node.status}</p>
            <p>{node.note}</p>
          </>
        ) : (
          <p>No relationship selected.</p>
        )}
      </section>
      <h3>Material and joint unknowns</h3>
      {study.unknowns.length ? (
        <ul>
          {study.unknowns.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>No unknowns list supplied; acceptance is not established.</p>
      )}
      <details>
        <summary>Exact record and source identity</summary>
        <p>{study.source.path}</p>
        <code>{study.source.sha256}</code>
        <ul>
          {study.sources.map((source, index) => (
            <li key={index}>
              {source.path}
              {source.sha256 && <code>{source.sha256}</code>}
            </li>
          ))}
        </ul>
      </details>
    </article>
  );
}

export function Rp1StudyComparisonView({ snapshot }: { snapshot: Rp1Studies }) {
  return (
    <section className="rp1-study-comparison">
      <header>
        <span>Separate recorded engineering studies</span>
        <h1>RP1 fin replacement studies</h1>
        <p className="rp1-unaccepted">
          FP1 and FR1 remain unaccepted. Neither replaces the frozen configuration or establishes
          installed strength.
        </p>
        <p>{snapshot.status}</p>
        <p>
          Source configuration: <code>{snapshot.source_configuration.id}</code>
        </p>
        <details>
          <summary>Configuration and comparison identity</summary>
          <p>{snapshot.id}</p>
          <p>{snapshot.source_configuration.path}</p>
          <code>{snapshot.source_configuration.sha256}</code>
        </details>
      </header>
      <section className="rp1-load-definition">
        <h2>Required load remains unchanged</h2>
        <p>
          <strong>{rp1Quantity(snapshot.load_definition.required_moment_Nm, 'N·m')}</strong>{' '}
          retained legacy envelope ·{' '}
          <strong>{rp1Quantity(snapshot.load_definition.proposed_moment_Nm, 'N·m')}</strong>{' '}
          proposed current-planform case — not adopted.
        </p>
        <p>{snapshot.load_definition.note}</p>
        <p>
          A moment is a turning load. Millimetres describe movement, grams describe conditional mass
          credits. Different study assumptions are not interchangeable; no installed pass is
          inferred from a number below the movement limit.
        </p>
      </section>
      <p>
        Graphics link recorded relationships to their notes. Selection is local to each study, with
        no CAD association. They are schematic, not CAD, measured contact geometry or stress maps.
        Select a box or its matching button for details.
      </p>
      {snapshot.studies.length ? (
        <div className="rp1-study-grid">
          {snapshot.studies.map((study) => (
            <StudyCard key={study.id} study={study} snapshot={snapshot} />
          ))}
        </div>
      ) : (
        <p role="status">No study records supplied. FP1/FR1 comparison is unavailable.</p>
      )}
    </section>
  );
}

export default function Rp1StudyComparison() {
  const [snapshot, setSnapshot] = useState<Rp1Studies | null>(null);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    void loadRp1Studies(controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setSnapshot(value);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted)
          setError(reason instanceof Error ? reason.message : 'Prepared study unavailable.');
      });
    return () => controller.abort();
  }, [retry]);
  if (error)
    return (
      <section className="rp1-study-comparison" role="alert">
        <h1>RP1 study comparison unavailable</h1>
        <p>{error}</p>
        <p>No previous configuration or numerical result is substituted.</p>
        <button
          type="button"
          onClick={() => {
            setSnapshot(null);
            setError('');
            setRetry((value) => value + 1);
          }}
        >
          Retry prepared source
        </button>
      </section>
    );
  return snapshot ? (
    <Rp1StudyComparisonView snapshot={snapshot} />
  ) : (
    <section className="rp1-study-comparison" role="status">
      Loading separately identified, unaccepted RP1 studies…
    </section>
  );
}
