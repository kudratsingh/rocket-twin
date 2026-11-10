import { useState } from 'react';
import {
  matchesRp1SystemMapSource,
  SYSTEM_MAPS,
  systemMapNode,
  type SystemMapEdge,
  type SystemMapMode,
  type SystemMapNode,
} from './rp1SystemMapData';
import './rp1SystemMap.css';

export type Rp1SystemMapProps = {
  configurationId: string;
  specificationSha256: string | null;
};

const NODE_WIDTH = 205;
const NODE_HEIGHT = 114;
const SOURCE_BASE =
  'https://github.com/kudratsingh/rocket-twin/blob/07552bd1425dce4cf0b47af56c70b44a9500625e/';

function edgePath(edge: SystemMapEdge, nodes: SystemMapNode[]) {
  const from = nodes.find((node) => node.id === edge.from)!;
  const to = nodes.find((node) => node.id === edge.to)!;
  // Configuration dependencies run above the row, clear of unrelated model blocks.
  if (edge.from === 'inputs' && edge.to === 'forces') {
    return `M ${from.x + 72} ${from.y} V -10 H ${to.x + 61} V ${to.y - 8}`;
  }
  if (edge.from === 'inputs' && edge.to === 'plant') {
    return `M ${from.x + 142} ${from.y} V -29 H ${to.x + 61} V ${to.y - 8}`;
  }
  if (edge.from === 'actuator' && edge.to === 'vehicle') {
    return `M ${from.x + NODE_WIDTH / 2} ${from.y + NODE_HEIGHT} V 339 H 9 V ${to.y + NODE_HEIGHT / 2} H ${to.x - 2}`;
  }
  if (from.y === to.y) {
    const direction = Math.sign(to.x - from.x);
    return `M ${from.x + (direction > 0 ? NODE_WIDTH : 0)} ${from.y + 57} H ${to.x + (direction > 0 ? -8 : NODE_WIDTH + 8)}`;
  }
  return `M ${from.x + NODE_WIDTH / 2} ${from.y + NODE_HEIGHT} V ${to.y - 8} H ${to.x + NODE_WIDTH / 2}`;
}

function edgeMarkerPosition(edge: SystemMapEdge, nodes: SystemMapNode[]) {
  const from = nodes.find((node) => node.id === edge.from)!;
  const to = nodes.find((node) => node.id === edge.to)!;
  if (edge.from === 'inputs' && edge.to === 'forces') return { x: 310, y: -10 };
  if (edge.from === 'inputs' && edge.to === 'plant') return { x: 500, y: -29 };
  if (edge.from === 'actuator' && edge.to === 'vehicle') return { x: 350, y: 331 };
  if (from.y === to.y) return { x: (from.x + to.x + NODE_WIDTH) / 2, y: from.y + 51 };
  return { x: from.x + NODE_WIDTH / 2, y: from.y + NODE_HEIGHT + 15 };
}

export default function Rp1SystemMap({ configurationId, specificationSha256 }: Rp1SystemMapProps) {
  const [mode, setMode] = useState<SystemMapMode>('g80');
  const [selectedId, setSelectedId] = useState('plant');
  if (!matchesRp1SystemMapSource(configurationId, specificationSha256)) {
    return (
      <section
        className="rp1-system-map rp1-system-map-unavailable"
        aria-label="RP1 system map unavailable"
      >
        <h2>System map unavailable for this source</h2>
        <p>
          Open the exact current G80-F2-RP1-AD1 v2 design and specification. No cross-configuration
          diagram is inferred.
        </p>
      </section>
    );
  }
  const graph = SYSTEM_MAPS[mode];
  const selected = systemMapNode(mode, selectedId) ?? graph.nodes[0];
  const changeMode = (next: SystemMapMode) => {
    setMode(next);
    setSelectedId(next === 'g80' ? 'plant' : 'control');
  };
  return (
    <section className="rp1-system-map" aria-label="Source-bound rocket system map">
      <header className="rp1-system-map-header">
        <div>
          <p className="rp1-system-map-eyebrow">RP1 / source-bound engineering graphic</p>
          <h2>System and control paths</h2>
          <p>
            Choose a block for units, source and limits. Arrows show model or proposed interfaces;
            they do not certify installed wiring.
          </p>
        </div>
        <div className="rp1-system-map-tabs" role="group" aria-label="System map configuration">
          <button type="button" aria-pressed={mode === 'g80'} onClick={() => changeMode('g80')}>
            Current G80 · unguided
          </button>
          <button type="button" aria-pressed={mode === 'g12'} onClick={() => changeMode('g12')}>
            Future G12 · PID → RL
          </button>
        </div>
      </header>
      <p className="rp1-system-map-warning">
        {mode === 'g80'
          ? 'Shared 6DOF code exists. Complete RP1 flight/inertia inputs are unavailable; the fixed G80 has no active gimbal or ascent controller.'
          : 'Control chain is a future G12 work order. Model components do not establish a wired vehicle, gains, policy, abort behavior or flight readiness.'}
      </p>
      <div className="rp1-system-map-legend" aria-label="Block status legend">
        <span data-status="implemented model">Implemented model</span>
        <span data-status="source definition">Source definition</span>
        <span data-status="planned">Planned</span>
        <span data-status="unavailable">Unavailable</span>
      </div>
      <div className="rp1-system-map-main">
        <div className="rp1-system-map-flow">
          <div className="rp1-system-map-graphic">
            <svg
              viewBox={mode === 'g80' ? '0 -45 1150 400' : '0 0 1150 355'}
              role="group"
              aria-label={
                mode === 'g80'
                  ? 'Current G80 simulation, instrumentation and recovery map'
                  : 'Future G12 feedback and control concept map'
              }
            >
              <defs>
                <marker
                  id="rp1-system-arrow"
                  viewBox="0 0 10 10"
                  refX="9"
                  refY="5"
                  markerWidth="7"
                  markerHeight="7"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" />
                </marker>
              </defs>
              {graph.edges.map((edge, index) => {
                const marker = edgeMarkerPosition(edge, graph.nodes);
                return (
                  <g key={`${edge.from}-${edge.to}`}>
                    <path
                      d={edgePath(edge, graph.nodes)}
                      className={`rp1-system-edge ${edge.status === 'planned' ? 'planned' : ''} ${edge.status === 'unavailable' ? 'unavailable' : ''}`}
                      markerEnd="url(#rp1-system-arrow)"
                    >
                      <title>{`${edge.from} → ${edge.to}: ${edge.label} (${edge.status})`}</title>
                    </path>
                    <circle cx={marker.x} cy={marker.y} r="10" className="rp1-system-edge-marker" />
                    <text
                      x={marker.x}
                      y={marker.y}
                      textAnchor="middle"
                      dominantBaseline="central"
                      className="rp1-system-edge-number"
                    >
                      {`E${index + 1}`}
                    </text>
                  </g>
                );
              })}
              {graph.nodes.map((node) => (
                <g
                  key={node.id}
                  className="rp1-system-node"
                  data-status={node.status}
                  data-selected={selected.id === node.id}
                  role="button"
                  tabIndex={0}
                  aria-label={`${node.title}; ${node.status}; ${node.subtitle}`}
                  aria-pressed={selected.id === node.id}
                  onClick={() => setSelectedId(node.id)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      setSelectedId(node.id);
                    }
                  }}
                >
                  <rect x={node.x} y={node.y} width={NODE_WIDTH} height={NODE_HEIGHT} rx="10" />
                  <text x={node.x + 12} y={node.y + 29} className="rp1-system-node-title">
                    {node.title}
                  </text>
                  <text x={node.x + 12} y={node.y + 55} className="rp1-system-node-subtitle">
                    {node.subtitle}
                  </text>
                  <text x={node.x + 12} y={node.y + 92} className="rp1-system-node-status">
                    {node.status}
                  </text>
                </g>
              ))}
            </svg>
          </div>
          <div className="rp1-system-map-edge-key">
            <h3>Flow key</h3>
            <ol>
              {graph.edges.map((edge, index) => (
                <li key={`${edge.from}-${edge.to}`}>
                  <span className="rp1-system-map-flow-marker">{`E${index + 1}`}</span>
                  <span>
                    <strong>
                      {systemMapNode(mode, edge.from)?.title} →{' '}
                      {systemMapNode(mode, edge.to)?.title}
                    </strong>
                    <br />
                    {edge.label} · {edge.status}
                  </span>
                </li>
              ))}
            </ol>
            <p>
              Current model uses NED world and body axes with SI units. Future arrows are proposed
              interfaces. Independent recovery is outside the ascent-control loop.
            </p>
          </div>
        </div>
        <aside className="rp1-system-map-detail" aria-live="polite">
          <div>
            <h3>{selected.title}</h3>
            <span data-status={selected.status}>{selected.status}</span>
          </div>
          <p>{selected.detail}</p>
          <p>
            <strong>Signal / frame:</strong> {selected.signal}
          </p>
          <p>
            <strong>Source:</strong>
          </p>
          <ul>
            {selected.source.map((path) => (
              <li key={path}>
                <a href={`${SOURCE_BASE}${path}`} target="_blank" rel="noreferrer">
                  {path}
                </a>
              </li>
            ))}
          </ul>
        </aside>
      </div>
      <p className="rp1-system-map-provenance">
        Pinned view: {configurationId} · specification SHA-256 {specificationSha256}. Source paths
        refer to the fixed merged source checkpoint 07552bd1425dce4cf0b47af56c70b44a9500625e.
      </p>
    </section>
  );
}
