import { useEffect, useId, useState } from 'react';
import {
  loadRp1Connections,
  rp1ConnectionDesignHref,
  rp1ConnectionDrawingHref,
  rp1ConnectionQuantity,
  validateRp1Connections,
} from './rp1Connections';
import type {
  Rp1Connection,
  Rp1ConnectionDrawing,
  Rp1ConnectionNode,
  Rp1ConnectionsDocument,
} from './rp1Connections';
import './rp1Connections.css';

function lines(text: string, width: number) {
  const result = [''];
  for (const word of text.split(/\s+/)) {
    const index = result.length - 1;
    if (result[index] && result[index].length + word.length + 1 > width) result.push(word);
    else result[index] += `${result[index] ? ' ' : ''}${word}`;
  }
  return result;
}

/** Box positions and connector lanes are reading layout, not physical coordinates or force shares. */
export function Rp1ConnectionGraph({
  connection,
  selectedNodeId,
  selectedPartId,
  onSelectNode,
}: {
  connection: Rp1Connection;
  selectedNodeId?: string | null;
  selectedPartId?: string | null;
  onSelectNode: (node: Rp1ConnectionNode) => void;
}) {
  const title = useId();
  let nextY = 84;
  const nodes = connection.nodes.map((node) => {
    const label = lines(node.label, 42);
    const note = lines(node.note, 59);
    const height = 34 + label.length * 21 + Math.min(note.length, 3) * 17 + 25;
    const result = { node, label, note, y: nextY, height };
    nextY += height + 24;
    return result;
  });
  const width = Math.max(650, 546 + connection.edges.length * 14);
  const middle = (id: string) => {
    const item = nodes.find((n) => n.node.id === id)!;
    return item.y + item.height / 2;
  };
  return (
    <svg
      className="rp1-connections-graph"
      xmlns="http://www.w3.org/2000/svg"
      viewBox={`0 0 ${width} ${nextY + 30}`}
      role="group"
      aria-labelledby={title}
    >
      <title id={title}>{`${connection.label} — concept relationship diagram, not CAD`}</title>
      <desc>
        Arrows are proposed connection routes with unknown sharing and finite compliance. Select a
        node for full notes and exact source parts.
      </desc>
      <rect width={width} height={nextY + 30} rx="8" fill="#101e29" />
      <text x="20" y="30" fill="#e5f1f6" fontSize="19" fontFamily="sans-serif">
        {connection.label}
      </text>
      <text x="20" y="55" fill="#f2c27c" fontSize="13" fontFamily="sans-serif">
        CONCEPT · NOT CAD · no accepted load sharing
      </text>
      {connection.edges.map((edge, index) => {
        const start = middle(edge.from),
          end = middle(edge.to),
          lane = 530 + index * 14;
        return (
          <g key={edge.id}>
            <title>{`${index + 1}. ${edge.label}: ${edge.note}`}</title>
            <path
              d={`M 506 ${start} H ${lane} V ${end} H 516`}
              fill="none"
              stroke="#819eaf"
              strokeWidth="1.5"
            />
            <polygon points={`506,${end} 518,${end - 5} 518,${end + 5}`} fill="#b6d5e5" />
            <circle cx={lane} cy={(start + end) / 2} r="9" fill="#152b3a" stroke="#8daebf" />
            <text
              x={lane}
              y={(start + end) / 2 + 4}
              textAnchor="middle"
              fill="#e5f1f6"
              fontSize="11"
              fontFamily="sans-serif"
            >
              {index + 1}
            </text>
          </g>
        );
      })}
      {nodes.map(({ node, label, note, y, height }) => {
        const selected =
          node.id === selectedNodeId ||
          (!!selectedPartId && node.part_ids.includes(selectedPartId));
        return (
          <g
            key={node.id}
            role="button"
            tabIndex={0}
            aria-pressed={selected}
            aria-label={`${node.label}: source relationship`}
            onClick={() => onSelectNode(node)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                onSelectNode(node);
              }
            }}
          >
            <title>{node.note}</title>
            <rect
              x="18"
              y={y}
              width="488"
              height={height}
              rx="6"
              fill={selected ? '#24485b' : '#192d3c'}
              stroke={selected ? '#a2e5ff' : '#688494'}
              strokeWidth={selected ? 3 : 1.5}
            />
            {label.map((line, index) => (
              <text
                key={`label-${index}`}
                x="32"
                y={y + 28 + index * 21}
                fill="#edf7fc"
                fontSize="16"
                fontFamily="sans-serif"
              >
                {line}
              </text>
            ))}
            {note.slice(0, 3).map((line, index) => (
              <text
                key={`note-${index}`}
                x="32"
                y={y + 37 + label.length * 21 + index * 17}
                fill="#b8cdda"
                fontSize="12"
                fontFamily="sans-serif"
              >
                {line}
                {index === 2 && note.length > 3 ? '…' : ''}
              </text>
            ))}
            <text x="32" y={y + height - 10} fill="#a2e5ff" fontSize="11" fontFamily="sans-serif">
              {node.part_ids.length
                ? `${node.part_ids.length} linked source part${node.part_ids.length === 1 ? '' : 's'} · select for detail`
                : 'Conceptual input / junction · no source part assigned'}
            </text>
          </g>
        );
      })}
      <text x="20" y={nextY + 10} fill="#a9c0ce" fontSize="12" fontFamily="sans-serif">
        Numbered routes are explained in the key. Boxes are not dimensioned geometry.
      </text>
    </svg>
  );
}

function SourceRef({ document, id }: { document: Rp1ConnectionsDocument; id: string }) {
  const source = document.sources.find((item) => item.id === id);
  return source ? (
    <small className="rp1-connections-source">
      <a
        href={`https://github.com/kudratsingh/rocket-twin/blob/37e0cc8745f7b5397c2e07145db00791a84f79f7/${source.path}`}
        target="_blank"
        rel="noreferrer"
      >
        <code>{source.path}</code>
      </a>
      <span>SHA-256 {source.sha256}</span>
    </small>
  ) : (
    <p>Source unavailable.</p>
  );
}
function SavedDrawing({ drawing }: { drawing: Rp1ConnectionDrawing }) {
  const [failed, setFailed] = useState(false);
  const url = rp1ConnectionDrawingHref(drawing);
  return (
    <details className="rp1-connections-drawing">
      <summary>{drawing.label} · saved concept drawing</summary>
      <p>{drawing.status}</p>
      <p>Recorded artifact; no new CAD or spatial analysis is generated here.</p>
      {failed ? (
        <p role="status">
          Saved drawing unavailable: the pinned artifact could not be loaded. No alternative drawing
          is substituted.
        </p>
      ) : (
        <img
          src={url}
          alt={`${drawing.label}; saved AD1 dimensioned concept, not manufacturing CAD`}
          loading="lazy"
          onError={() => setFailed(true)}
        />
      )}
      <a href={url} target="_blank" rel="noreferrer">
        Open source-pinned SVG
      </a>
      <small className="rp1-connections-source">
        <code>{drawing.path}</code>
        <span>SHA-256 {drawing.sha256}</span>
      </small>
    </details>
  );
}

export interface Rp1ConnectionsRouteProps {
  requestedPartId?: string | null;
  connectionId?: string | null;
  onSelectPart?: (partId: string) => void;
  onSelectConnection?: (connectionId: string) => void;
}
function ConnectionContent({
  document,
  requestedPartId,
  connectionId,
  onSelectPart,
  onSelectConnection,
}: Rp1ConnectionsRouteProps & { document: Rp1ConnectionsDocument }) {
  const initialConnection =
    document.connections.find((c) => c.id === connectionId) ??
    document.connections.find((c) => requestedPartId && c.part_ids.includes(requestedPartId)) ??
    document.connections[0];
  const [activeId, setActiveId] = useState(initialConnection.id);
  const [partId, setPartId] = useState<string | null>(requestedPartId ?? null);
  const [nodeId, setNodeId] = useState<string | null>(null);
  const active = document.connections.find((c) => c.id === activeId)!;
  const selectedNode = active.nodes.find((node) => node.id === nodeId);
  const relatedNodes = active.nodes.filter((node) => partId && node.part_ids.includes(partId));
  const linkedPart = !!partId && active.part_ids.includes(partId);
  function selectPart(id: string) {
    setPartId(id);
    onSelectPart?.(id);
  }
  return (
    <section className="rp1-connections" aria-label="AD1 connection inspection">
      <header>
        <p className="rp1-connections-eyebrow">Engineering · frozen AD1 v2</p>
        <h1>Fin root and recovery connections</h1>
        <p className="rp1-connections-warning">
          CONCEPT / SOURCE ESTIMATES · NOT ADOPTED · engineering acceptance remains open
        </p>
        <p>{document.status}</p>
        <p>
          Explore the intended routes, recorded gaps and evidence behind this 55-part definition.
          The diagrams are relationships, not CAD, manufactured fit, stress maps or accepted force
          sharing.
        </p>
        <details>
          <summary>Exact configuration and source identity</summary>
          <p>
            <code>{document.configuration.id}</code>
          </p>
          <p>
            <code>{document.configuration.path}</code>
          </p>
          <code>{document.configuration.sha256}</code>
          <p>
            Millimetres (mm) describe source sizes or stations; newtons (N) describe force;
            newton-metres (N·m) describe turning load. A requirement is not a passing result.
          </p>
        </details>
      </header>
      <div className="rp1-connections-tabs" role="group" aria-label="Connection detail selection">
        {document.connections.map((connection) => (
          <button
            type="button"
            key={connection.id}
            aria-pressed={active.id === connection.id}
            onClick={() => {
              setActiveId(connection.id);
              setNodeId(null);
              onSelectConnection?.(connection.id);
            }}
          >
            {connection.label}
          </button>
        ))}
      </div>
      <div className="rp1-connections-graphs">
        {document.connections.map((connection) => (
          <article
            key={connection.id}
            hidden={connection.id !== active.id}
            className={connection.id === active.id ? 'is-active' : ''}
          >
            <Rp1ConnectionGraph
              connection={connection}
              selectedNodeId={connection.id === active.id ? nodeId : null}
              selectedPartId={partId}
              onSelectNode={(node) => {
                setActiveId(connection.id);
                setNodeId(node.id);
                if (node.part_ids.length) selectPart(node.part_ids[0]);
                else setPartId(null);
              }}
            />
            <details>
              <summary>{connection.label}: full route key</summary>
              <ol>
                {connection.edges.map((edge) => (
                  <li key={edge.id}>
                    <strong>{edge.label}</strong>
                    <p>{edge.note}</p>
                    <small>
                      {connection.nodes.find((n) => n.id === edge.from)?.label} →{' '}
                      {connection.nodes.find((n) => n.id === edge.to)?.label}
                    </small>
                  </li>
                ))}
              </ol>
            </details>
          </article>
        ))}
      </div>
      <section
        className="rp1-connections-selection"
        aria-live="polite"
        aria-label="Selected connection and part"
      >
        <h2>{active.label}</h2>
        <p>{active.summary}</p>
        {selectedNode && (
          <>
            <h3>{selectedNode.label}</h3>
            <p>{selectedNode.note}</p>
            {!selectedNode.part_ids.length && (
              <p>
                This input or junction has no physical source part assigned. No Design part link is
                invented.
              </p>
            )}
          </>
        )}
        <div className="rp1-connections-part-buttons" aria-label={`${active.label} source parts`}>
          {active.part_ids.map((id) => (
            <button
              key={id}
              type="button"
              aria-pressed={partId === id}
              onClick={() => {
                setNodeId(null);
                selectPart(id);
              }}
            >
              {id.replaceAll('_', ' ')}
            </button>
          ))}
        </div>
        {partId ? (
          <>
            <h3>
              Selected source part: <code>{partId}</code>
            </h3>
            {linkedPart ? (
              relatedNodes
                .filter((node) => node.id !== selectedNode?.id)
                .map((node) => (
                  <p key={node.id}>
                    <strong>{node.label}:</strong> {node.note}
                  </p>
                ))
            ) : (
              <p role="status">
                Connection evidence unavailable for this part in {active.label}. No relationship is
                inferred.
              </p>
            )}
            <a className="rp1-connections-design-link" href={rp1ConnectionDesignHref(partId)}>
              Inspect this exact AD1 part in Design
            </a>
            <p className="rp1-connections-muted">
              The link pins both configuration and specification hash. Detailed dimensions or
              missing geometry remain owned by that source.
            </p>
          </>
        ) : (
          <p>Select a graph node or a source-part button to inspect its connection context.</p>
        )}
      </section>
      <section aria-labelledby="rp1-connection-dimensions">
        <h2 id="rp1-connection-dimensions">{active.label}: recorded dimensions and contact</h2>
        <p>
          Values are copied from the named source. Nominal gaps, reservations and estimated inputs
          are not measured clearances or qualified material properties.
        </p>
        <dl className="rp1-connections-dimensions">
          {active.dimensions.map((dimension) => (
            <div key={dimension.id}>
              <dt>{dimension.label}</dt>
              <dd>
                <strong>{rp1ConnectionQuantity(dimension.value, dimension.unit)}</strong>
                <p>{dimension.note}</p>
                <SourceRef document={document} id={dimension.source_id} />
              </dd>
            </div>
          ))}
        </dl>
      </section>
      <section aria-labelledby="rp1-connection-findings">
        <h2 id="rp1-connection-findings">{active.label}: findings and remaining evidence</h2>
        <p>
          These findings apply to the connection or stated model scope. Selecting a part does not
          make them a part-specific qualification.
        </p>
        <div className="rp1-connections-findings">
          {active.findings.map((finding) => (
            <article key={finding.id} data-status={finding.status}>
              <h3>{finding.label}</h3>
              <strong className="rp1-connections-finding-status">
                {finding.status === 'failed-screen'
                  ? 'FAILED SCREEN'
                  : finding.status === 'unknown'
                    ? 'UNKNOWN / UNVERIFIED'
                    : 'RETAINED REQUIREMENT'}
              </strong>
              <p>{finding.detail}</p>
              <p>
                <strong>Evidence needed later:</strong> {finding.measurement_needed}
              </p>
              <SourceRef document={document} id={finding.source_id} />
            </article>
          ))}
        </div>
      </section>
      <section>
        <h2>Saved source drawings</h2>
        {active.drawing_ids.length ? (
          active.drawing_ids.map((id) => {
            const drawing = document.drawings.find((item) => item.id === id);
            return drawing ? (
              <SavedDrawing key={id} drawing={drawing} />
            ) : (
              <p key={id} role="status">
                Saved drawing {id} unavailable in this prepared package. No replacement is
                substituted.
              </p>
            );
          })
        ) : (
          <p>Saved drawings unavailable for this connection.</p>
        )}
      </section>
      <footer>
        <p>
          Retain 8.83 N·m / 331.125 N with factor 3 already applied once, and the 1 mm total
          movement limit. No perfectly rigid attachment or equal force split is assumed.
        </p>
        <p>
          Continue from recorded evidence; supplier and lab drafts remain UNSENT. Later measurements
          or tests need their separate authorization. This view changes no engineering, physical or
          flight gate.
        </p>
      </footer>
    </section>
  );
}

export function Rp1ConnectionsView(
  props: Rp1ConnectionsRouteProps & { document: Rp1ConnectionsDocument },
) {
  try {
    validateRp1Connections(props.document);
  } catch (error) {
    return (
      <Unavailable message={error instanceof Error ? error.message : 'Source validation failed.'} />
    );
  }
  if (props.requestedPartId && !props.document.part_ids.includes(props.requestedPartId))
    return (
      <Unavailable
        message={`Requested part ${props.requestedPartId} is unavailable in the frozen AD1 source. No archived or foreign part is substituted.`}
      />
    );
  if (props.connectionId && !props.document.connections.some((c) => c.id === props.connectionId))
    return (
      <Unavailable
        message={`Requested connection ${props.connectionId} is unavailable. Choose a recorded fin-root or recovery route.`}
      />
    );
  return (
    <ConnectionContent
      key={`${props.connectionId ?? ''}:${props.requestedPartId ?? ''}`}
      {...props}
    />
  );
}
function Unavailable({ message }: { message: string }) {
  return (
    <section className="rp1-connections" role="alert">
      <h1>AD1 connections unavailable</h1>
      <p>{message}</p>
    </section>
  );
}
export default function Rp1Connections(props: Rp1ConnectionsRouteProps) {
  const [document, setDocument] = useState<Rp1ConnectionsDocument | null>(null);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    void loadRp1Connections(controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setDocument(value);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted)
          setError(reason instanceof Error ? reason.message : 'Prepared source unavailable.');
      });
    return () => controller.abort();
  }, [retry]);
  if (error)
    return (
      <>
        <Unavailable message={error} />
        <button
          type="button"
          onClick={() => {
            setDocument(null);
            setError('');
            setRetry((value) => value + 1);
          }}
        >
          Retry prepared AD1 connections
        </button>
      </>
    );
  return document ? (
    <Rp1ConnectionsView document={document} {...props} />
  ) : (
    <section className="rp1-connections" role="status">
      Loading source-pinned AD1 connections…
    </section>
  );
}
