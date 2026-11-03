import { useEffect, useRef, useState } from 'react';
import {
  connectionAxialStations,
  connectionGraphLayout,
  connectionEdgeDisplay,
  connectionNumber as number,
  loadF2ConnectionSnapshot,
} from './f2ConnectionStudyTypes';
import type { F2ConnectionSnapshot } from './f2ConnectionStudyTypes';
import './f2ConnectionStudy.css';

function lines(label: string, limit = 28): string[] {
  const result = [''];
  for (const word of label.split(/\s+/)) {
    const index = result.length - 1;
    if (result[index].length + word.length > limit && result[index]) result.push(word);
    else result[index] += `${result[index] ? ' ' : ''}${word}`;
  }
  return result;
}

export function F2ConnectionGraph({
  snapshot,
  selectedNodeId,
  onSelectNode,
}: {
  snapshot: F2ConnectionSnapshot;
  selectedNodeId: string | null;
  onSelectNode: (id: string) => void;
}) {
  const { positions, height } = connectionGraphLayout(snapshot.graph.nodes);
  return (
    <svg
      viewBox={`0 0 1200 ${height}`}
      role="group"
      aria-label="Recorded F2-C1 connection graph"
      className="f2c-graph"
    >
      <title>G80-F2-C1 proposed force routes — no equal branch sharing implied</title>
      <metadata>
        {JSON.stringify({
          identity: snapshot.identity,
          sources: snapshot.sources,
          graph: snapshot.graph,
          status: snapshot.status,
        })}
      </metadata>
      <rect width="1200" height={height} fill="#12202a" />
      <g fontFamily="system-ui, sans-serif" fill="#dfedf3">
        <text x="26" y="30" fontSize="20">
          G80-F2-C1 · proposed recovery / joint route
        </text>
        <text x="26" y="53" fontSize="13">
          Arrow = recorded connection direction, not force magnitude or equal load allocation.
          Select a node for source parts.
        </text>
        <text x="26" y="75" fontSize="12">
          Concept topology, not CAD · installed strength unaccepted · exact contacts / branch
          allocation unavailable
        </text>
        {snapshot.graph.edges.map((edge, index) => {
          const from = positions.get(edge.from)!;
          const to = positions.get(edge.to)!;
          const display = connectionEdgeDisplay(from, to);
          const labelLines = lines(edge.label, 24);
          const labelHeight = labelLines.length * 15 + 8;
          return (
            <g key={`${edge.from}-${edge.to}-${index}`}>
              <title>{`${edge.label}: ${edge.note} (${edge.state})`}</title>
              <path d={display.path} fill="none" stroke="#dfb77e" strokeWidth="2" />
              <polygon points={display.arrow} fill="#dfb77e" />
              <rect
                x={display.labelX - 95}
                y={display.labelY - labelHeight / 2}
                width="190"
                height={labelHeight}
                rx="3"
                fill="#12202a"
                stroke="#3f4b4e"
              />
              {labelLines.map((line, lineIndex) => (
                <text
                  key={lineIndex}
                  x={display.labelX}
                  y={display.labelY - labelHeight / 2 + 15 + lineIndex * 15}
                  fontSize="12"
                  textAnchor="middle"
                  fill="#efcc99"
                >
                  {line}
                </text>
              ))}
            </g>
          );
        })}
        {snapshot.graph.nodes.map((node) => {
          const p = positions.get(node.id)!;
          const selected = selectedNodeId === node.id;
          return (
            <g
              key={node.id}
              role="button"
              tabIndex={0}
              aria-label={`${node.label}: ${node.note}`}
              aria-pressed={selected}
              onClick={() => onSelectNode(node.id)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  onSelectNode(node.id);
                }
              }}
            >
              <title>{`${node.label}: ${node.note}`}</title>
              <rect
                x={p.x}
                y={p.y}
                width="260"
                height="94"
                rx="7"
                fill={selected ? '#364343' : '#1e3442'}
                stroke={selected ? '#fff2a5' : '#729bad'}
                strokeWidth={selected ? 3 : 1.5}
              />
              {lines(node.label)
                .slice(0, 2)
                .map((line, i) => (
                  <text key={i} x={p.x + 12} y={p.y + 25 + i * 18} fontSize="14">
                    {line}
                  </text>
                ))}
              <text x={p.x + 12} y={p.y + 68} fontSize="11" fill="#efc78b">
                {node.state === 'unavailable' ? 'Capacity unavailable' : node.state} ·{' '}
                {node.part_ids.length} source rows
              </text>
              <text x={p.x + 12} y={p.y + 85} fontSize="10" fill="#adc5d2">
                {node.id}
              </text>
            </g>
          );
        })}
        <text x="26" y={height - 35} fontSize="12">
          {snapshot.id} · source {snapshot.identity.source_identity.slice(0, 48)}
        </text>
        <text x="26" y={height - 15} fontSize="12">
          Unadopted fit proposal. Old 32.3 mm ring diagnostic fields do not apply to the proposed
          32.2 mm ring.
        </text>
      </g>
    </svg>
  );
}

export function F2ConnectionAxialCut({ snapshot }: { snapshot: F2ConnectionSnapshot }) {
  const stations = connectionAxialStations(snapshot);
  if (!stations)
    return (
      <p role="status">
        Axial floor/tab sketch unavailable: forward-ring web or tab-front source parameters are
        missing.
      </p>
    );
  const gap = snapshot.fits.find((fit) => fit.id === 'front_tab_end');
  const x = (station: number) =>
    110 +
    ((station - stations.ringFront) / Math.max(stations.tabFront - stations.ringFront, 0.001)) *
      720;
  return (
    <svg
      viewBox="0 0 1200 430"
      role="img"
      aria-label="Source-defined axial floor and tab-front direction sketch"
      className="f2c-cut"
    >
      <title>Blind notch floor opens under noseward recovery-ring pull</title>
      <metadata>
        {JSON.stringify({
          identity: snapshot.identity,
          stations,
          fit: gap,
          scope: 'Axial station schematic only; radial extent and adhesive shape not represented.',
        })}
      </metadata>
      <rect width="1200" height="430" fill="#12202a" />
      <g fontFamily="system-ui, sans-serif" fill="#e1edf3">
        <text x="25" y="32" fontSize="20">
          Recovery direction: the blind floor is not a tension capture
        </text>
        <text x="25" y="56" fontSize="13">
          Axial station schematic (mm), not a solid section. Vertical thickness and arrow length are
          illustrative.
        </text>
        <text x="70" y="100" fontSize="14">
          ← noseward ring pull
        </text>
        <path
          d={`M${x(stations.floor)} 120 H80 l20 -10 M80 120 l20 10`}
          stroke="#efc78b"
          strokeWidth="3"
          fill="none"
        />
        <rect
          x={x(stations.ringFront)}
          y="180"
          width={Math.max(1, x(stations.floor) - x(stations.ringFront))}
          height="75"
          fill="#638a82"
          stroke="#b7d9bd"
        />
        <rect
          x={x(stations.tabFront)}
          y="180"
          width="220"
          height="75"
          fill="#8b7352"
          stroke="#e4bf88"
        />
        <path d="M1030 180 l-8 18 16 18 -16 18 8 21" stroke="#12202a" strokeWidth="6" fill="none" />
        <text x="160" y="222" fontSize="16">
          Ring front web
        </text>
        <text x={x(stations.tabFront) + 12} y="222" fontSize="14">
          Tab continues aft
        </text>
        {[
          ['Ring front', stations.ringFront],
          ['Notch floor', stations.floor],
          ['Tab front', stations.tabFront],
        ].map(([label, station], index) => (
          <g key={String(label)}>
            <line
              x1={x(Number(station))}
              y1="260"
              x2={x(Number(station))}
              y2={280 + index * 24}
              stroke="#aac3d0"
            />
            <text
              x={x(Number(station))}
              y={298 + index * 24}
              textAnchor={index === 2 ? 'start' : 'middle'}
              fontSize="13"
            >
              {label}: {number(Number(station), 'mm')}
            </text>
          </g>
        ))}
        <text x="25" y="375" fontSize="13">
          Recorded nominal end gap: {number(gap?.nominal_mm, 'mm')} · proposed receiving/setup
          bounds are unverified.
        </text>
        <text x="25" y="400" fontSize="13">
          Noseward ring motion opens this gap. Adhesive tension/shear carries recovery; the floor
          supplies no direct compression capture.
        </text>
      </g>
    </svg>
  );
}

export function F2ConnectionStudyView({
  snapshot,
  prepared = false,
}: {
  snapshot: F2ConnectionSnapshot;
  prepared?: boolean;
}) {
  const [selectedId, setSelectedId] = useState(snapshot.graph.nodes[0]?.id ?? null);
  const [selectedPartId, setSelectedPartId] = useState<string | null>(null);
  const graphics = useRef<HTMLDivElement>(null);
  const [exportError, setExportError] = useState('');
  const node = snapshot.graph.nodes.find((item) => item.id === selectedId);
  const parts = snapshot.parts.filter((part) => node?.part_ids.includes(part.id));
  const selectedPart = parts.find((part) => part.id === selectedPartId) ?? parts[0];
  function selectNode(id: string) {
    setSelectedId(id);
    setSelectedPartId(null);
  }
  function exportGraph() {
    const svg = graphics.current?.querySelector('svg');
    if (!svg) return;
    try {
      const clone = svg.cloneNode(true) as SVGSVGElement;
      clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
      const url = URL.createObjectURL(
        new Blob([new XMLSerializer().serializeToString(clone)], {
          type: 'image/svg+xml;charset=utf-8',
        }),
      );
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${snapshot.id}-connection-graph.svg`;
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setExportError('');
    } catch (error) {
      setExportError(error instanceof Error ? error.message : 'SVG export unavailable.');
    }
  }
  return (
    <section className="f2c-study" aria-label="F2-C1 unadopted connection study">
      <header>
        <p className="f2c-kicker">Separate source packet · unadopted</p>
        <h1>G80-F2-C1 connection study</h1>
        <p>{snapshot.status}</p>
      </header>
      <p className="f2c-warning">
        {snapshot.parts.length} allocation rows, not qualified parts. No full CAD or
        installed-strength acceptance. Actual motor/retainer and finished joint contacts remain
        unknown.
      </p>
      {prepared && (
        <p className="f2c-warning">
          Prepared source export: the API route is absent. Exact source identity below remains
          attached; this is not a live engineering recalculation.
        </p>
      )}
      <details>
        <summary>Source identity and records</summary>
        <p>
          {snapshot.id} · {snapshot.identity.source_identity}
        </p>
        <p>Specification: {snapshot.identity.specification_sha256} · full CAD unavailable</p>
        {snapshot.sources.map((source) => (
          <p key={source.id}>
            <strong>{source.id}</strong> · {source.path}
            <br />
            <code>{source.sha256}</code>
          </p>
        ))}
      </details>
      <div className="f2c-actions">
        <label>
          Connection{' '}
          <select value={selectedId ?? ''} onChange={(event) => selectNode(event.target.value)}>
            {snapshot.graph.nodes.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <button onClick={exportGraph}>Export connection SVG</button>
      </div>
      {exportError && <p role="alert">{exportError}</p>}
      <div className="f2c-layout">
        <div ref={graphics} className="f2c-graphics">
          <F2ConnectionGraph
            snapshot={snapshot}
            selectedNodeId={selectedId}
            onSelectNode={selectNode}
          />
        </div>
        <aside className="f2c-inspector" aria-live="polite">
          <h2>{node?.label ?? 'Select a connection'}</h2>
          <p>{node?.note}</p>
          <p>Recorded state: {node?.state ?? 'Unavailable'}</p>
          {!parts.length && <p>No source allocation rows are mapped to this topology node.</p>}
          {parts.length > 1 && (
            <label>
              Source allocation{' '}
              <select
                value={selectedPart?.id ?? ''}
                onChange={(event) => setSelectedPartId(event.target.value)}
              >
                {parts.map((part) => (
                  <option key={part.id} value={part.id}>
                    {part.label}
                  </option>
                ))}
              </select>
            </label>
          )}
          {selectedPart && (
            <>
              <h3>{selectedPart.label}</h3>
              <p>{selectedPart.function}</p>
              <dl>
                <dt>Material</dt>
                <dd>{selectedPart.material}</dd>
                <dt>Allocated mass</dt>
                <dd>{number(selectedPart.mass_g, 'g')}</dd>
                <dt>Axial station</dt>
                <dd>{number(selectedPart.z_mm, 'mm')}</dd>
                <dt>State</dt>
                <dd>{selectedPart.state}</dd>
              </dl>
              <p>
                {Array.isArray(selectedPart.notes)
                  ? selectedPart.notes.join(' ')
                  : selectedPart.notes}
              </p>
              <details>
                <summary>Source dimensions and parameters</summary>
                <pre>
                  {JSON.stringify(
                    {
                      dimensions: selectedPart.dimensions,
                      parameters: selectedPart.parameters ?? null,
                    },
                    null,
                    2,
                  )}
                </pre>
              </details>
            </>
          )}
          {snapshot.findings
            .filter((finding) => finding.part_ids.some((id) => node?.part_ids.includes(id)))
            .map((finding) => (
              <p className="f2c-warning" key={finding.id}>
                <strong>
                  {finding.label} — {finding.state}
                </strong>
                <br />
                {finding.note}
              </p>
            ))}
        </aside>
      </div>
      <F2ConnectionAxialCut snapshot={snapshot} />
      <h2>Conditional fits — unverified receiving and environmental bounds</h2>
      <p>
        Clearances below are saved calculations, not measured finished-part fits. A conditional
        screen is separate from installed capacity.
      </p>
      <div className="f2c-table" role="region" aria-label="Recorded conditional fits" tabIndex={0}>
        <table>
          <thead>
            <tr>
              <th>Interface</th>
              <th>Minimum</th>
              <th>Nominal</th>
              <th>Maximum</th>
              <th>Criterion</th>
              <th>Recorded screen</th>
              <th>Evidence basis</th>
            </tr>
          </thead>
          <tbody>
            {snapshot.fits.map((fit) => (
              <tr key={fit.id}>
                <th>{fit.id.replaceAll('_', ' ')}</th>
                <td>{number(fit.minimum_mm, 'mm')}</td>
                <td>{number(fit.nominal_mm, 'mm')}</td>
                <td>{number(fit.maximum_mm, 'mm')}</td>
                <td>{number(fit.criterion_mm, 'mm')}</td>
                <td>{fit.conditional_screen_pass ? 'Conditional only' : 'Fails screen'}</td>
                <td>
                  {fit.basis}
                  <br />
                  Measured: {fit.measured ? 'yes' : 'no'} · environmental bounds verified:{' '}
                  {fit.environmental_bounds_verified ? 'yes' : 'no'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h2>Coupled complete-case comparison</h2>
      <p>
        Full separate 50 g growth and the adverse +20 g remain distinct ledger columns. The 1.5 m
        reference, formal 15 m/s and separate 15.5 m/s planning criteria stay unchanged. Recorded
        whole/branch demands are not summed again.
      </p>
      <div
        className="f2c-table"
        role="region"
        aria-label="Recorded mass and force cases"
        tabIndex={0}
      >
        <table>
          <thead>
            <tr>
              <th>Identity / case</th>
              <th>Parts g</th>
              <th>Growth allowance g</th>
              <th>Additional aft g</th>
              <th>Loaded total g</th>
              <th>Balance point mm</th>
              <th>Loaded margin cal</th>
              <th>Burnout balance mm</th>
              <th>Burnout margin cal</th>
              <th>1.5 m guide m/s</th>
              <th>Formal headroom g</th>
              <th>Planning headroom g</th>
              <th>Whole proxy N</th>
              <th>Body branch N</th>
            </tr>
          </thead>
          <tbody>
            {snapshot.cases.map((item) => (
              <tr key={`${item.variant}-${item.case}`}>
                <th>
                  {item.variant === 'frozen_F2' ? 'Working F2 reference' : 'F2-C1 fit proposal'}
                  <br />
                  {item.case === 'nominal'
                    ? 'Nominal + full growth'
                    : 'Adverse aft mass / motor-balance probe'}
                  <small>{item.identity}</small>
                </th>
                {[
                  item.parts_mass_kg == null ? null : item.parts_mass_kg * 1000,
                  item.growth_kg == null ? null : item.growth_kg * 1000,
                  item.extra_aft_kg == null ? null : item.extra_aft_kg * 1000,
                  item.total_mass_kg == null ? null : item.total_mass_kg * 1000,
                  item.cg_m == null ? null : item.cg_m * 1000,
                  item.margin_cal,
                  item.burnout_cg_m == null ? null : item.burnout_cg_m * 1000,
                  item.burnout_margin_cal,
                  item.guide_mps['1.5'],
                  item.formal_mass_headroom_g,
                  item.planning_mass_headroom_g,
                  item.required_whole_mean_proxy_N,
                  item.common_acceleration_partition_N.body,
                ].map((value, index) => (
                  <td key={index}>{number(value)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <details>
        <summary>All recorded case quantities and mechanism comparisons</summary>
        <pre>{JSON.stringify(snapshot.cases, null, 2)}</pre>
      </details>
      <h2>Stopped diagnostic evidence — not a field on this proposal</h2>
      <p className="f2c-warning">
        {snapshot.numerical.completed_grids} of {snapshot.numerical.required_grids} grids completed.
        Fine mesh: {number(snapshot.numerical.fine_nodes)} nodes versus declared{' '}
        {number(snapshot.numerical.node_limit)} limit. Status: {snapshot.numerical.status}. No
        three-grid convergence or installed strength acceptance.
      </p>
      <p>
        The diagnostic uses the old 32.3 mm ring; proposed 32.2 mm geometry has no compatible field.
        No stress or temperature colors are attached here.
      </p>
      <details>
        <summary>Historical audit — source variant {snapshot.audit.source_variant}</summary>
        <p>
          These audit numbers belong to frozen F2, not the fit proposal. Mean contact estimates do
          not establish actual contact pressure or allowable strength.
        </p>
        <pre>{JSON.stringify(snapshot.audit, null, 2)}</pre>
      </details>
      <h2>Open findings</h2>
      {snapshot.findings.map((finding) => (
        <details key={finding.id}>
          <summary>
            {finding.label} — {finding.state}
          </summary>
          <p>{finding.note}</p>
          <p>Source rows: {finding.part_ids.join(', ') || 'Packet-level finding'}</p>
        </details>
      ))}
    </section>
  );
}

export default function F2ConnectionStudy() {
  const [data, setData] = useState<{ snapshot: F2ConnectionSnapshot; prepared: boolean } | null>(
    null,
  );
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    setError('');
    void loadF2ConnectionSnapshot(controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setData(result);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted)
          setError(reason instanceof Error ? reason.message : 'F2-C1 source unavailable.');
      });
    return () => controller.abort();
  }, [retry]);
  if (error)
    return (
      <section className="f2c-study">
        <h1>F2-C1 connection source unavailable</h1>
        <p role="alert">{error}</p>
        <p>No historical candidate or diagnostic field is substituted.</p>
        <button onClick={() => setRetry((value) => value + 1)}>Retry F2-C1 source</button>
      </section>
    );
  if (!data)
    return (
      <section className="f2c-study" role="status">
        <h1>Loading separate F2-C1 connection packet</h1>
      </section>
    );
  return <F2ConnectionStudyView key={data.snapshot.identity.source_identity} {...data} />;
}
