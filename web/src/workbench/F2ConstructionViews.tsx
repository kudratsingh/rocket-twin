import { useRef, useState } from 'react';
import type { ReactNode, RefObject } from 'react';
import type { F2Joint, F2Snapshot } from './f2Types';
import { f2Number } from './f2Types';
import './f2Construction.css';

type Props = {
  snapshot: F2Snapshot;
  svgRef?: RefObject<SVGSVGElement | null>;
  onSelect?: (id: string) => void;
};
const c = {
  bg: '#12202a',
  panel: '#1c3441',
  line: '#759faf',
  pale: '#eef8fa',
  soft: '#c3dbe4',
  amber: '#efc78b',
  blue: '#8bcbe0',
  red: '#eba7a0',
  green: '#b2d9b8',
  purple: '#b9b5e3',
};
function wrap(value: string, width: number): string[] {
  const out: string[] = [];
  for (const word of value.split(/\s+/)) {
    if (!out.length || out[out.length - 1].length + word.length + 1 > width) out.push(word);
    else out[out.length - 1] += ` ${word}`;
  }
  return out;
}
function Lines({
  value,
  x,
  y,
  width = 120,
  size = 12,
  fill = c.soft,
}: {
  value: string;
  x: number;
  y: number;
  width?: number;
  size?: number;
  fill?: string;
}) {
  return (
    <>
      {wrap(value, width).map((line, i) => (
        <text key={i} x={x} y={y + i * 16} fill={fill} fontSize={size}>
          {line}
        </text>
      ))}
    </>
  );
}
function Base({
  title,
  subtitle,
  height,
  children,
  svgRef,
}: {
  title: string;
  subtitle: string;
  height: number;
  children: ReactNode;
  svgRef?: RefObject<SVGSVGElement | null>;
}) {
  return (
    <svg
      ref={svgRef}
      className="g80-f2-drawing"
      viewBox={`0 0 1080 ${height}`}
      width="1080"
      height={height}
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={title}
      fontFamily="Helvetica,Arial,sans-serif"
    >
      <rect width="1080" height={height} fill={c.bg} />
      <text x="30" y="42" fill={c.pale} fontSize="23" fontWeight="700">
        {title}
      </text>
      <text x="30" y="68" fill={c.amber} fontSize="13">
        {subtitle}
      </text>
      {children}
    </svg>
  );
}
function footer(snapshot: F2Snapshot, y: number) {
  return (
    <>
      <path d={`M30 ${y - 25}H1050`} stroke={c.line} />
      <text x="30" y={y} fill={c.soft} fontSize="12">
        G80-F2 · {snapshot.identity.source_identity} · {snapshot.identity.frame} ·{' '}
        {snapshot.identity.units}
      </text>
      <text x="30" y={y + 18} fill={c.amber} fontSize="12">
        Source projection only · no F2 CAD, manufactured fit or physical acceptance.
      </text>
    </>
  );
}
const categoryColor: Record<string, string> = {
  airframe: c.blue,
  fin: c.amber,
  motor: c.purple,
  recovery: c.green,
  avionics: '#abbbe6',
  hardware: '#d9b991',
  thermal: '#e6a18e',
  unknown: c.line,
};

/** Axial/radial source envelopes and complete component roles, without a CAD profile. */
export function F2ArrangementDrawing({ snapshot, svgRef, onSelect }: Props) {
  const valid = snapshot.components.filter(
    (item) => item.z_start_mm !== null && item.z_end_mm !== null && item.z_end_mm > item.z_start_mm,
  );
  const lo = valid.length ? Math.min(...valid.map((item) => item.z_start_mm!)) : null;
  const hi = valid.length ? Math.max(...valid.map((item) => item.z_end_mm!)) : null;
  const span = lo !== null && hi !== null && hi > lo ? hi - lo : null;
  const sx = (z: number) => 340 + ((z - lo!) / span!) * 650;
  const rows = snapshot.components.map((part) => ({
    part,
    h: Math.max(88, 65 + wrap(part.function, 105).length * 16),
  }));
  const height = 430 + rows.reduce((sum, row) => sum + row.h, 0);
  let y = 114;
  const stock = snapshot.components.filter(
    (part) =>
      /body|tube|splice/i.test(`${part.id} ${part.label}`) &&
      part.z_start_mm !== null &&
      part.z_end_mm !== null &&
      part.outer_radius_mm !== null,
  );
  return (
    <Base
      title="G80-F2 · actual stock and fixed construction arrangement"
      subtitle="Source z/R envelopes and part functions; permanent bonds are intent, not installed qualification"
      height={height}
      svgRef={svgRef}
    >
      <text x="30" y={y} fill={c.blue} fontSize="16" fontWeight="700">
        Longitudinal stock envelopes and splice station
      </text>
      <rect x="30" y="134" width="1020" height="150" rx="8" fill={c.panel} stroke={c.line} />
      {span !== null && (
        <>
          <text x="45" y="153" fill={c.soft} fontSize="11">
            Recorded cylindrical z/R bands
          </text>
          <path d="M340 210H990" stroke={c.line} strokeDasharray="7 5" />
          {stock.map((part, i) => (
            <g
              key={part.id}
              onClick={() => onSelect?.(part.id)}
              style={{ cursor: onSelect ? 'pointer' : undefined }}
            >
              {[1, -1].map((side) => {
                const outer = part.outer_radius_mm!;
                const inner = part.inner_radius_mm;
                if (inner === null)
                  return side === 1 ? (
                    <rect
                      key={side}
                      x={sx(part.z_start_mm!)}
                      y={210 - outer * 1.25}
                      width={Math.max(2, sx(part.z_end_mm!) - sx(part.z_start_mm!))}
                      height={outer * 2.5}
                      fill="none"
                      stroke={c.amber}
                      strokeDasharray="4 3"
                    />
                  ) : null;
                const top = side === 1 ? 210 - outer * 1.25 : 210 + inner * 1.25;
                return (
                  <rect
                    key={side}
                    x={sx(part.z_start_mm!)}
                    y={top}
                    width={Math.max(2, sx(part.z_end_mm!) - sx(part.z_start_mm!))}
                    height={Math.max(2, (outer - inner) * 1.25)}
                    fill={categoryColor[part.category] ?? c.line}
                    opacity={part.id.toLowerCase().includes('splice') ? 0.9 : 0.65}
                    stroke={c.pale}
                    strokeWidth="0.5"
                  />
                );
              })}
              {i < 5 && (
                <text x="45" y={171 + i * 17} fill={c.pale} fontSize="11">
                  {part.label}
                </text>
              )}
            </g>
          ))}
          {snapshot.joints
            .filter(
              (joint) => /splice/i.test(`${joint.id} ${joint.kind}`) && joint.station_mm !== null,
            )
            .map((joint) => (
              <g key={joint.id}>
                <path
                  d={`M${sx(joint.station_mm!)} 142v125`}
                  stroke={c.amber}
                  strokeWidth="2"
                  strokeDasharray="5 4"
                />
                <text
                  x={Math.min(940, sx(joint.station_mm!) + 5)}
                  y="151"
                  fill={c.amber}
                  fontSize="11"
                >
                  {joint.label}
                </text>
              </g>
            ))}
          <text x="340" y="268" fill={c.soft} fontSize="11">
            z {f2Number(lo, 'mm')}
          </text>
          <text x="922" y="268" fill={c.soft} fontSize="11">
            z {f2Number(hi, 'mm')}
          </text>
          <text x="750" y="157" fill={c.soft} fontSize="10">
            Axis dashed · source outer/inner radii, no CAD contour
          </text>
        </>
      )}
      {(() => {
        y = 316;
        return (
          <text x="30" y={y} fill={c.blue} fontSize="16" fontWeight="700">
            Source component distribution and functions
          </text>
        );
      })()}
      {rows.map(({ part, h }) => {
        const rowY = y + 20;
        y += h;
        return (
          <g
            key={part.id}
            onClick={() => onSelect?.(part.id)}
            style={{ cursor: onSelect ? 'pointer' : undefined }}
          >
            <rect
              x="30"
              y={rowY}
              width="1020"
              height={h - 5}
              rx="6"
              fill={c.panel}
              stroke={c.line}
            />
            <text x="48" y={rowY + 24} fill={c.pale} fontSize="14" fontWeight="700">
              {part.label}
            </text>
            <text x="48" y={rowY + 44} fill={c.soft} fontSize="11">
              {part.category} · {part.maturity} · {f2Number(part.mass_g, 'g')}
            </text>
            {span !== null &&
              part.z_start_mm !== null &&
              part.z_end_mm !== null &&
              part.z_end_mm > part.z_start_mm && (
                <rect
                  x={sx(part.z_start_mm)}
                  y={rowY + 10}
                  width={Math.max(2, sx(part.z_end_mm) - sx(part.z_start_mm))}
                  height="18"
                  fill={categoryColor[part.category] ?? c.line}
                />
              )}
            <text x="340" y={rowY + 48} fill={c.amber} fontSize="11">
              z {f2Number(part.z_start_mm, 'mm')}–{f2Number(part.z_end_mm, 'mm')} · R{' '}
              {f2Number(part.inner_radius_mm, 'mm')}–{f2Number(part.outer_radius_mm, 'mm')}
            </text>
            <Lines value={part.function} x={340} y={rowY + 68} width={110} size={11} />
          </g>
        );
      })}
      {footer(snapshot, height - 57)}
    </Base>
  );
}

function jointPanelHeight(joint: F2Joint) {
  return Math.max(170, 125 + joint.layers.length * 38 + wrap(joint.note, 125).length * 16);
}
/** Each layer uses its own recorded z/R interval; missing bounds stay text-only. */
export function F2JointDrawing({ snapshot, svgRef, onSelect }: Props) {
  const height =
    190 + snapshot.joints.reduce((sum, joint) => sum + jointPanelHeight(joint) + 24, 0) + 90;
  let y = 112;
  return (
    <Base
      title="G80-F2 · splice and notched fin/ring sections"
      subtitle="Recorded local layers and clearances; geometry is schematic where a coordinate is unavailable"
      height={height}
      svgRef={svgRef}
    >
      <text x="30" y={y} fill={c.blue} fontSize="16" fontWeight="700">
        Source sections and construction holds
      </text>
      {snapshot.joints.map((joint) => {
        const rowY = y + 24;
        const h = jointPanelHeight(joint);
        y += h + 24;
        const placed = joint.layers.filter(
          (layer) =>
            layer.z_start_mm !== null &&
            layer.z_end_mm !== null &&
            layer.inner_radius_mm !== null &&
            layer.outer_radius_mm !== null,
        );
        const zs = placed.flatMap((layer) => [layer.z_start_mm!, layer.z_end_mm!]);
        const rs = placed.flatMap((layer) => [layer.inner_radius_mm!, layer.outer_radius_mm!]);
        const zmin = zs.length ? Math.min(...zs) : null,
          zmax = zs.length ? Math.max(...zs) : null;
        const rmin = rs.length ? Math.min(...rs) : null,
          rmax = rs.length ? Math.max(...rs) : null;
        const zspan = zmin !== null && zmax !== null && zmax > zmin ? zmax - zmin : null;
        const rspan = rmin !== null && rmax !== null && rmax > rmin ? rmax - rmin : null;
        const zx = (z: number) => 530 + ((z - zmin!) / zspan!) * 480;
        const ry = (r: number) => rowY + 104 - ((r - rmin!) / rspan!) * 62;
        return (
          <g key={joint.id}>
            <rect
              x="30"
              y={rowY}
              width="1020"
              height={h + 10}
              rx="8"
              fill={c.panel}
              stroke={c.line}
            />
            <text x="48" y={rowY + 25} fill={c.pale} fontSize="17" fontWeight="700">
              {joint.label}
            </text>
            <text
              x="760"
              y={rowY + 25}
              fill={joint.state === 'failed' ? c.red : c.amber}
              fontSize="12"
            >
              {joint.state} · z {f2Number(joint.station_mm, 'mm')}
            </text>
            <text x="48" y={rowY + 50} fill={c.amber} fontSize="12">
              Clearance {f2Number(joint.clearance_mm, 'mm')}
            </text>
            <Lines value={joint.note} x={48} y={rowY + 72} width={55} size={11} />
            {zspan !== null && rspan !== null && (
              <rect x="520" y={rowY + 36} width="500" height="84" fill={c.bg} stroke={c.line} />
            )}
            {joint.layers.map((layer, i) => (
              <g
                key={`${joint.id}-${layer.component_id}-${i}`}
                onClick={() => onSelect?.(layer.component_id)}
                style={{ cursor: onSelect ? 'pointer' : undefined }}
              >
                {zspan !== null &&
                  rspan !== null &&
                  layer.z_start_mm !== null &&
                  layer.z_end_mm !== null &&
                  layer.inner_radius_mm !== null &&
                  layer.outer_radius_mm !== null && (
                    <rect
                      x={zx(layer.z_start_mm)}
                      y={ry(layer.outer_radius_mm)}
                      width={Math.max(2, zx(layer.z_end_mm) - zx(layer.z_start_mm))}
                      height={Math.max(2, ry(layer.inner_radius_mm) - ry(layer.outer_radius_mm))}
                      fill={layer.state === 'failed' ? c.red : i % 2 ? c.blue : c.amber}
                      opacity="0.55"
                      stroke={c.pale}
                    />
                  )}
                <text x="530" y={rowY + 143 + i * 38} fill={c.pale} fontSize="12">
                  {layer.label} · z {f2Number(layer.z_start_mm, 'mm')}–
                  {f2Number(layer.z_end_mm, 'mm')} · R {f2Number(layer.inner_radius_mm, 'mm')}–
                  {f2Number(layer.outer_radius_mm, 'mm')}
                </text>
                <text x="530" y={rowY + 159 + i * 38} fill={c.soft} fontSize="11">
                  {layer.state} · {layer.note}
                </text>
              </g>
            ))}
          </g>
        );
      })}
      {footer(snapshot, height - 57)}
    </Base>
  );
}

/** Recorded paths and complete cases remain distinct; no frontend force split or mass sum. */
export function F2RecoveryLedgerDrawing({ snapshot, svgRef }: Props) {
  const roots = snapshot.components
    .filter((part) => /parachute|canopy/i.test(part.id))
    .map((part) => part.id);
  const reached = new Set(roots);
  for (let pass = 0; pass < snapshot.connections.length; pass++)
    for (const edge of snapshot.connections) if (reached.has(edge.from_id)) reached.add(edge.to_id);
  const recovery = roots.length
    ? snapshot.connections.filter((edge) => reached.has(edge.from_id))
    : snapshot.connections.filter((edge) =>
        /recover|cord|canopy|nose|harness|anchor|eye|leader/i.test(
          `${edge.id} ${edge.label} ${edge.kind} ${edge.from_id} ${edge.to_id}`,
        ),
      );
  const nodeIds = [...new Set(recovery.flatMap((edge) => [edge.from_id, edge.to_id]))];
  const incoming = new Set(recovery.map((edge) => edge.to_id));
  const depths = new Map(nodeIds.map((id) => [id, incoming.has(id) ? 0 : 1]));
  for (let pass = 0; pass < nodeIds.length; pass++)
    for (const edge of recovery)
      depths.set(
        edge.to_id,
        Math.max(depths.get(edge.to_id) ?? 0, (depths.get(edge.from_id) ?? 0) + 1),
      );
  const maxDepth = Math.max(1, ...depths.values());
  const columns = new Map<number, string[]>();
  for (const id of nodeIds) {
    const column = depths.get(id) ?? 0;
    columns.set(column, [...(columns.get(column) ?? []), id]);
  }
  const graphHeight = Math.max(
    185,
    Math.max(0, ...[...columns.values()].map((ids) => ids.length)) * 66 + 45,
  );
  const positions = new Map(
    nodeIds.map((id) => {
      const column = depths.get(id) ?? 0;
      const ids = columns.get(column) ?? [];
      const index = ids.indexOf(id);
      return [id, { x: 103 + (column / maxDepth) * 860, y: 165 + index * 66 }] as const;
    }),
  );
  const pathRows = recovery.map((edge) => ({
    edge,
    h: Math.max(100, 74 + wrap(edge.note, 135).length * 16),
  }));
  const caseRows = snapshot.cases.map((item) => ({
    item,
    h: Math.max(148, 112 + wrap(item.note, 130).length * 16),
  }));
  const ledgerRows = snapshot.ledger.map((item) => ({
    item,
    h: Math.max(78, 56 + wrap(item.note, 145).length * 16),
  }));
  const failedRows = snapshot.uncertainties
    .filter((item) => item.state === 'failed')
    .map((item) => ({ item, h: Math.max(88, 55 + wrap(item.note, 135).length * 16) }));
  const caseHeight = caseRows.reduce((sum, row) => sum + row.h, 0);
  const pathHeight = pathRows.reduce((sum, row) => sum + row.h, 0);
  const ledgerHeight = ledgerRows.reduce((sum, row) => sum + row.h, 0);
  const failedHeight = failedRows.reduce((sum, row) => sum + row.h, 0);
  const height = 335 + graphHeight + caseHeight + pathHeight + ledgerHeight + failedHeight + 130;
  let y = 112;
  return (
    <Base
      title="G80-F2 · recovery path and coupled mass ledger"
      subtitle="Recorded branches, complete cases and signed rows; no equal sharing or frontend calculation"
      height={height}
      svgRef={svgRef}
    >
      <text x="30" y={y} fill={c.blue} fontSize="16" fontWeight="700">
        Source-defined recovery branch topology
      </text>
      <rect
        x="30"
        y="134"
        width="1020"
        height={graphHeight}
        rx="8"
        fill={c.panel}
        stroke={c.line}
      />
      {recovery.map((edge) => {
        const from = positions.get(edge.from_id);
        const to = positions.get(edge.to_id);
        if (!from || !to || (from.x === to.x && from.y === to.y)) return null;
        const dx = to.x - from.x;
        const dy = to.y - from.y;
        const length = Math.hypot(dx, dy);
        const ux = dx / length;
        const uy = dy / length;
        const x1 = from.x + ux * 48;
        const y1 = from.y + uy * 21;
        const x2 = to.x - ux * 50;
        const y2 = to.y - uy * 24;
        const stroke = edge.state === 'failed' ? c.red : c.blue;
        return (
          <g key={`graph-${edge.id}`}>
            <path
              d={`M${x1} ${y1}L${x2} ${y2}`}
              stroke={stroke}
              strokeWidth="2.5"
              strokeDasharray={edge.state === 'unavailable' ? '6 4' : undefined}
            />
            <circle cx={x2} cy={y2} r="3" fill={stroke} />
          </g>
        );
      })}
      {nodeIds.map((id) => {
        const point = positions.get(id)!;
        const label = snapshot.components.find((part) => part.id === id)?.label ?? id;
        return (
          <g key={`node-${id}`}>
            <title>{label}</title>
            <rect
              x={point.x - 46}
              y={point.y - 21}
              width="92"
              height="42"
              rx="6"
              fill={c.bg}
              stroke={c.line}
              strokeWidth="1.5"
            />
            <text x={point.x} y={point.y + 4} textAnchor="middle" fill={c.pale} fontSize="9">
              {label.length > 14 ? `${label.slice(0, 13)}…` : label}
            </text>
          </g>
        );
      })}
      <text x="45" y={134 + graphHeight - 13} fill={c.soft} fontSize="10">
        Solid = recorded state · dashed = unavailable · red = failed. Arrows follow source edges
        only.
      </text>
      {(() => {
        y = 164 + graphHeight;
        return (
          <text x="30" y={y} fill={c.blue} fontSize="16" fontWeight="700">
            Recorded edge evidence and open capacity
          </text>
        );
      })()}
      {pathRows.map(({ edge, h }) => {
        const rowY = y + 22;
        y += h;
        return (
          <g key={edge.id}>
            <rect
              x="30"
              y={rowY}
              width="1020"
              height={h - 6}
              rx="7"
              fill={c.panel}
              stroke={c.line}
            />
            <text x="48" y={rowY + 25} fill={c.pale} fontSize="14" fontWeight="700">
              {edge.label}
            </text>
            <text
              x="860"
              y={rowY + 25}
              fill={edge.state === 'failed' ? c.red : c.amber}
              fontSize="12"
            >
              {edge.state}
            </text>
            <path
              d={`M48 ${rowY + 47}H88m-8-6 8 6-8 6`}
              stroke={edge.state === 'failed' ? c.red : c.blue}
              strokeWidth="2"
              fill="none"
            />
            <text x="103" y={rowY + 52} fill={c.blue} fontSize="12">
              {edge.from_id} → {edge.to_id} · {edge.kind}
            </text>
            <Lines value={edge.note} x={48} y={rowY + 72} width={135} size={10} />
          </g>
        );
      })}
      {(() => {
        y += 40;
        return (
          <text x="30" y={y} fill={c.blue} fontSize="16" fontWeight="700">
            Selected and comparison nominal/adverse cases
          </text>
        );
      })()}
      {caseRows.map(({ item, h }) => {
        const rowY = y + 22;
        y += h;
        return (
          <g key={item.id}>
            <rect
              x="30"
              y={rowY}
              width="1020"
              height={h - 6}
              rx="7"
              fill={c.panel}
              stroke={c.line}
            />
            <text x="48" y={rowY + 25} fill={c.pale} fontSize="15" fontWeight="700">
              {item.label}
            </text>
            <text x="48" y={rowY + 49} fill={c.amber} fontSize="13">
              Mass {f2Number(item.total_mass_g, 'g')} · loaded CG{' '}
              {f2Number(item.loaded_cg_mm, 'mm')} · reference CP{' '}
              {f2Number(item.reference_cp_mm, 'mm')}
            </text>
            <text x="48" y={rowY + 72} fill={c.blue} fontSize="13">
              Margin {f2Number(item.margin_cal, 'cal')} · guide{' '}
              {f2Number(item.guide_speed_mps, 'm/s')} at {f2Number(item.usable_guide_m, 'm')} usable
            </text>
            <text x="48" y={rowY + 95} fill={c.red} fontSize="12">
              Formal15 headroom {f2Number(item.formal_headroom_g, 'g')} · separate15.5 planning{' '}
              {f2Number(item.planning_headroom_g, 'g')}
            </text>
            <Lines value={item.note} x={48} y={rowY + 117} width={130} size={11} />
          </g>
        );
      })}
      {(() => {
        y += 40;
        return (
          <text x="30" y={y} fill={c.blue} fontSize="16" fontWeight="700">
            Signed F1→F2 change ledger · recorded rows
          </text>
        );
      })()}
      {ledgerRows.map(({ item, h }) => {
        const rowY = y + 22;
        y += h;
        return (
          <g key={item.id}>
            <rect
              x="30"
              y={rowY}
              width="1020"
              height={h - 6}
              rx="5"
              fill={c.panel}
              stroke={c.line}
            />
            <text x="48" y={rowY + 20} fill={c.pale} fontSize="12" fontWeight="700">
              {item.label}
            </text>
            <text x="560" y={rowY + 20} fill={c.amber} fontSize="12">
              {f2Number(item.mass_g, 'g')} · z {f2Number(item.station_mm, 'mm')}
            </text>
            <text x="48" y={rowY + 39} fill={c.soft} fontSize="10">
              {item.role} ·{' '}
              {item.replaces_id ? `replaces ${item.replaces_id}` : 'additional/retained'} ·{' '}
              {item.state}
            </text>
            <Lines value={item.note} x={48} y={rowY + 57} width={145} size={10} />
          </g>
        );
      })}
      {(() => {
        y += 40;
        return (
          <text x="30" y={y} fill={c.red} fontSize="16" fontWeight="700">
            Recorded failed findings · source state, not inferred from rounded values
          </text>
        );
      })()}
      {failedRows.map(({ item, h }) => {
        const rowY = y + 22;
        y += h;
        return (
          <g key={item.id}>
            <rect
              x="30"
              y={rowY}
              width="1020"
              height={h - 6}
              rx="7"
              fill={c.panel}
              stroke={c.red}
            />
            <text x="48" y={rowY + 25} fill={c.red} fontSize="14" fontWeight="700">
              {item.label} · {item.state}
            </text>
            <Lines value={item.note} x={48} y={rowY + 48} width={135} size={11} />
          </g>
        );
      })}
      {footer(snapshot, height - 57)}
    </Base>
  );
}

function saveSvg(svg: SVGSVGElement | null, snapshot: F2Snapshot, name: string) {
  if (!svg) return;
  const clone = svg.cloneNode(true) as SVGSVGElement;
  const metadata = document.createElementNS('http://www.w3.org/2000/svg', 'metadata');
  metadata.textContent = JSON.stringify({
    title: name,
    identity: snapshot.identity,
    sources: snapshot.generated_from,
    representation: 'F2 source projection; no CAD, installed fit or capacity acceptance.',
  });
  clone.prepend(metadata);
  const url = URL.createObjectURL(
    new Blob([new XMLSerializer().serializeToString(clone)], { type: 'image/svg+xml' }),
  );
  const link = document.createElement('a');
  link.href = url;
  link.download = `g80-f2-${name}.svg`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function F2ConstructionViews({
  snapshot,
  prepared = false,
}: {
  snapshot: F2Snapshot;
  prepared?: boolean;
}) {
  const arrangement = useRef<SVGSVGElement>(null),
    joints = useRef<SVGSVGElement>(null),
    recovery = useRef<SVGSVGElement>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = snapshot.components.find((part) => part.id === selectedId);
  return (
    <div className="g80-f2-view">
      <section>
        <span className="g80-f2-kicker">
          Separate G80-F2 construction snapshot · {snapshot.identity.source_identity}
        </span>
        <h2>{snapshot.label}</h2>
        <p>{snapshot.status}</p>
        {prepared && (
          <p className="g80-f2-banner">
            Prepared offline export because the current API has no F2 route.
          </p>
        )}
        <p className="g80-f2-banner">
          F1 remains frozen. These are source construction envelopes, not CAD or installed joint
          qualification.
        </p>
      </section>
      <section className="g80-f2-inspector" aria-live="polite">
        <h3>{selected?.label ?? 'Select an F2 component in a diagram'}</h3>
        {selected ? (
          <>
            <p>{selected.function}</p>
            <p>
              {selected.construction} · {selected.material} · {f2Number(selected.mass_g, 'g')}
            </p>
            <p>
              z {f2Number(selected.z_start_mm, 'mm')}–{f2Number(selected.z_end_mm, 'mm')} ·{' '}
              {selected.maturity} / {selected.state}
            </p>
            <p>{selected.note}</p>
            <small>Sources: {selected.source_ids.join(', ')}</small>
          </>
        ) : (
          <p>Selection stays within this F2 snapshot.</p>
        )}
      </section>
      {(
        [
          ['Stock, splice and forward equipment', arrangement, 'arrangement', F2ArrangementDrawing],
          ['Splice and fin/ring sections', joints, 'joints', F2JointDrawing],
          ['Recovery and mass ledger', recovery, 'recovery-ledger', F2RecoveryLedgerDrawing],
        ] as const
      ).map(([title, ref, id, Drawing]) => (
        <section key={id}>
          <div className="g80-f2-heading">
            <h3>{title}</h3>
            <button type="button" onClick={() => saveSvg(ref.current, snapshot, id)}>
              Download SVG
            </button>
          </div>
          <div className="g80-f2-figure">
            <Drawing snapshot={snapshot} svgRef={ref} onSelect={setSelectedId} />
          </div>
        </section>
      ))}
      <section>
        <h3>Open findings</h3>
        {snapshot.uncertainties.map((item) => (
          <article key={item.id}>
            <strong>{item.label}</strong> · {item.state}
            <p>{item.note}</p>
            <small>{item.source_ids.join(', ')}</small>
          </article>
        ))}
      </section>
      <section>
        <h3>Pinned sources</h3>
        {snapshot.generated_from.map((source) => (
          <details key={source.id}>
            <summary>{source.description}</summary>
            <p>{source.path}</p>
            <code>{source.sha256}</code>
          </details>
        ))}
      </section>
    </div>
  );
}
