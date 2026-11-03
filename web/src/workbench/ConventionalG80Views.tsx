import { useRef, useState } from 'react';
import type { RefObject, ReactNode } from 'react';
import type { ConventionalSnapshot } from './conventionalG80Types';
import { conventionalNumber } from './conventionalG80Types';
import './conventionalG80.css';

type DrawingProps = { snapshot: ConventionalSnapshot; svgRef?: RefObject<SVGSVGElement | null> };
type SelectableDrawingProps = DrawingProps & { onSelectComponent?: (id: string) => void };
const color = {
  bg: '#12202a',
  panel: '#1d3542',
  line: '#7299aa',
  pale: '#ecf6f8',
  soft: '#bed5de',
  amber: '#efc88e',
  blue: '#8bccdf',
  red: '#e9aaa3',
  airframe: '#8bc7d9',
  fin: '#d5ad85',
  motor: '#d0a1be',
  recovery: '#afd6b7',
  avionics: '#aeb9e4',
  hardware: '#e0bf8c',
  thermal: '#e8a390',
  unknown: '#839ba8',
};
function wrap(value: string, width: number): string[] {
  const result: string[] = [];
  for (const word of value.split(/\s+/)) {
    if (!result.length || result[result.length - 1].length + word.length + 1 > width)
      result.push(word);
    else result[result.length - 1] += ` ${word}`;
  }
  return result;
}
function Lines({
  value,
  x,
  y,
  width = 120,
  size = 12,
  step = 16,
  fill = color.soft,
}: {
  value: string;
  x: number;
  y: number;
  width?: number;
  size?: number;
  step?: number;
  fill?: string;
}) {
  return (
    <>
      {wrap(value, width).map((line, i) => (
        <text key={i} x={x} y={y + i * step} fontSize={size} fill={fill}>
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
      className="g80-fixed-drawing"
      viewBox={`0 0 1080 ${height}`}
      width="1080"
      height={height}
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={title}
      fontFamily="Helvetica,Arial,sans-serif"
    >
      <rect width="1080" height={height} fill={color.bg} />
      <text x="30" y="42" fill={color.pale} fontSize="23" fontWeight="700">
        {title}
      </text>
      <text x="30" y="68" fill={color.amber} fontSize="13">
        {subtitle}
      </text>
      {children}
    </svg>
  );
}
function footer(snapshot: ConventionalSnapshot, y: number) {
  return (
    <>
      <path d={`M30 ${y - 25}H1050`} stroke={color.line} />
      <text x="30" y={y} fill={color.soft} fontSize="12">
        G80-F1 · {snapshot.identity.source_identity} · {snapshot.identity.frame} ·{' '}
        {snapshot.identity.units}
      </text>
      <text x="30" y={y + 18} fill={color.amber} fontSize="12">
        {snapshot.cad_manifest
          ? `Exact CAD ${snapshot.cad_manifest.revision}; inspect its listed part identities.`
          : 'Source projection only; no same-design detailed CAD or physical acceptance.'}
      </text>
    </>
  );
}

/** Source-scaled axial envelope; the fin is one projected member of three. */
export function ConventionalRocketDrawing({
  snapshot,
  svgRef,
  onSelectComponent,
}: SelectableDrawingProps) {
  const part = (id: string) => snapshot.components.find((item) => item.id === id);
  const nose = part('nose');
  const body = part('body');
  const fin = part('fin_set');
  const tube = part('motor_tube');
  const motor = part('motor');
  const fore = part('forward_ring');
  const tabs = part('fin_tabs');
  const aft = part('aft_ring');
  const shield = part('mount_external_shield');
  const pack = part('parachute');
  const logger = part('flight_computer');
  const recovery = part('independent_recovery');
  const finSpan = fin?.dimensions?.span_mm ?? null;
  const finSweep = fin?.dimensions?.sweep_mm ?? null;
  const finTip = fin?.dimensions?.tip_chord_mm ?? null;
  const x = (z: number) => 75 + z * 0.73;
  const axis = 310;
  const radial = (r: number) => r * 2;
  const outer = body?.outer_radius_mm ?? null;
  const width =
    body?.z_start_mm !== null && body?.z_end_mm !== null
      ? x(body!.z_end_mm!) - x(body!.z_start_mm!)
      : 0;
  const feature = (item: typeof body, y: number, h: number, fill: string, opacity = 1) =>
    item?.z_start_mm !== null &&
    item?.z_end_mm !== null &&
    item?.z_start_mm !== undefined &&
    item?.z_end_mm !== undefined ? (
      <rect
        x={x(item.z_start_mm)}
        y={y}
        width={Math.max(2, x(item.z_end_mm) - x(item.z_start_mm))}
        height={h}
        fill={fill}
        opacity={opacity}
        stroke={color.line}
        onClick={() => onSelectComponent?.(item.id)}
        style={{ cursor: onSelectComponent ? 'pointer' : undefined }}
      />
    ) : null;
  const ring = (item: typeof fore) =>
    item &&
    item.z_start_mm !== null &&
    item.z_end_mm !== null &&
    item.inner_radius_mm !== null &&
    item.outer_radius_mm !== null ? (
      <g
        onClick={() => onSelectComponent?.(item.id)}
        style={{ cursor: onSelectComponent ? 'pointer' : undefined }}
      >
        <rect
          x={x(item.z_start_mm)}
          y={axis - radial(item.outer_radius_mm)}
          width={Math.max(2, x(item.z_end_mm) - x(item.z_start_mm))}
          height={radial(item.outer_radius_mm - item.inner_radius_mm)}
          fill={color.hardware}
        />
        <rect
          x={x(item.z_start_mm)}
          y={axis + radial(item.inner_radius_mm)}
          width={Math.max(2, x(item.z_end_mm) - x(item.z_start_mm))}
          height={radial(item.outer_radius_mm - item.inner_radius_mm)}
          fill={color.hardware}
        />
      </g>
    ) : null;
  const finShape =
    fin &&
    fin.z_start_mm !== null &&
    fin.z_end_mm !== null &&
    outer !== null &&
    finSpan !== null &&
    finSweep !== null &&
    finTip !== null
      ? `${x(fin.z_start_mm)},${axis + radial(outer)} ${x(fin.z_start_mm + finSweep)},${axis + radial(outer + finSpan)} ` +
        `${x(fin.z_start_mm + finSweep + finTip)},${axis + radial(outer + finSpan)} ` +
        `${x(fin.z_end_mm)},${axis + radial(outer)}`
      : null;
  const zoomMin = 1055;
  const zoomMax = 1110;
  const zx = (z: number) => 475 + ((z - zoomMin) / (zoomMax - zoomMin)) * 540;
  const ry = (radius: number) => 758 - (radius - 14) * 4.5;
  const overlapStart = Math.max(fore?.z_start_mm ?? Infinity, tabs?.z_start_mm ?? Infinity);
  const overlapEnd = Math.min(fore?.z_end_mm ?? -Infinity, tabs?.z_end_mm ?? -Infinity);
  const radialOverlapStart = Math.max(
    fore?.inner_radius_mm ?? Infinity,
    tabs?.inner_radius_mm ?? Infinity,
  );
  const radialOverlapEnd = Math.min(
    fore?.outer_radius_mm ?? -Infinity,
    tabs?.outer_radius_mm ?? -Infinity,
  );
  const knownRadialOverlap = radialOverlapEnd > radialOverlapStart;
  return (
    <Base
      title="G80-F1 · single-body source envelope and critical section"
      subtitle="Axial dimensions from F1 source; schematic material fills, no CAD, fit or stiffness acceptance"
      height={890}
      svgRef={svgRef}
    >
      <text x="30" y="114" fill={color.blue} fontSize="16" fontWeight="700">
        Longitudinal source envelope and one projected fin of three
      </text>
      <text x="30" y="137" fill={color.soft} fontSize="12">
        Axial stations scaled; radial sizes exaggerated. Packed goods are axial envelopes, not
        verified fits.
      </text>
      <path d={`M75 ${axis}H1030`} stroke={color.line} strokeDasharray="7 5" />
      {nose && nose.z_start_mm !== null && nose.z_end_mm !== null && outer !== null && (
        <g
          onClick={() => onSelectComponent?.(nose.id)}
          style={{ cursor: onSelectComponent ? 'pointer' : undefined }}
        >
          <rect
            x={x(nose.z_start_mm)}
            y={axis - radial(outer)}
            width={x(nose.z_end_mm) - x(nose.z_start_mm)}
            height={radial(outer) * 2}
            fill={color.airframe}
            opacity="0.18"
            stroke={color.airframe}
            strokeDasharray="7 5"
          />
          <text x={x(nose.z_start_mm) + 16} y={axis - 15} fill={color.pale} fontSize="12">
            Ogive envelope
          </text>
          <text x={x(nose.z_start_mm) + 16} y={axis + 3} fill={color.soft} fontSize="10">
            profile unavailable
          </text>
        </g>
      )}
      {body && outer !== null && body.inner_radius_mm !== null && width > 0 && (
        <g
          onClick={() => onSelectComponent?.(body.id)}
          style={{ cursor: onSelectComponent ? 'pointer' : undefined }}
        >
          <rect
            x={x(body.z_start_mm!)}
            y={axis - radial(outer)}
            width={width}
            height={radial(outer) * 2}
            fill="#263d49"
            stroke={color.airframe}
            strokeWidth="2"
          />
          <rect
            x={x(body.z_start_mm!)}
            y={axis - radial(body.inner_radius_mm)}
            width={width}
            height={radial(body.inner_radius_mm) * 2}
            fill={color.bg}
          />
        </g>
      )}
      {feature(pack, axis - 27, 18, color.recovery, 0.75)}
      {feature(logger, axis - 3, 17, color.avionics, 0.75)}
      {feature(recovery, axis + 19, 16, color.avionics, 0.75)}
      {tube &&
        tube.inner_radius_mm !== null &&
        tube.outer_radius_mm !== null &&
        tube.z_start_mm !== null &&
        tube.z_end_mm !== null && (
          <g
            onClick={() => onSelectComponent?.(tube.id)}
            style={{ cursor: onSelectComponent ? 'pointer' : undefined }}
          >
            <rect
              x={x(tube.z_start_mm)}
              y={axis - radial(tube.outer_radius_mm)}
              width={x(tube.z_end_mm) - x(tube.z_start_mm)}
              height={radial(tube.outer_radius_mm) * 2}
              fill="none"
              stroke={color.motor}
              strokeWidth="3"
            />
            <text x={x(tube.z_start_mm) - 8} y="222" fill={color.motor} fontSize="11">
              Fixed mount tube
            </text>
          </g>
        )}
      {shield &&
        shield.z_start_mm !== null &&
        shield.z_end_mm !== null &&
        shield.outer_radius_mm !== null && (
          <rect
            x={x(shield.z_start_mm)}
            y={axis - radial(shield.outer_radius_mm) - 3}
            width={x(shield.z_end_mm) - x(shield.z_start_mm)}
            height={radial(shield.outer_radius_mm) * 2 + 6}
            fill="none"
            stroke={color.thermal}
            strokeDasharray="5 4"
            strokeWidth="2"
            onClick={() => onSelectComponent?.(shield.id)}
          />
        )}
      {feature(motor, axis - 26, 52, color.motor, 0.68)}
      {ring(fore)}
      {ring(aft)}
      {finShape && (
        <polygon
          points={finShape}
          fill={color.fin}
          opacity="0.8"
          stroke={color.amber}
          onClick={() => onSelectComponent?.(fin!.id)}
          style={{ cursor: onSelectComponent ? 'pointer' : undefined }}
        />
      )}
      <text x="35" y="518" fill={color.soft} fontSize="12">
        Nose envelope · {conventionalNumber(nose?.z_end_mm ?? null, 'mm')} long
      </text>
      <text x="320" y="518" fill={color.soft} fontSize="12">
        Continuous body · {conventionalNumber(body?.dimensions?.length_mm ?? null, 'mm')}
      </text>
      <text x="720" y="518" fill={color.amber} fontSize="12">
        Fin span {conventionalNumber(finSpan, 'mm')} · thickness{' '}
        {conventionalNumber(fin?.dimensions?.thickness_mm ?? null, 'mm')}
      </text>
      <text x="35" y="545" fill={color.soft} fontSize="11">
        Pack, electronics and thermal shield are source envelopes; radial clearances, installation
        and heating unverified.
      </text>
      <path d="M30 573H1050" stroke={color.line} />
      <text x="30" y="602" fill={color.blue} fontSize="16" fontWeight="700">
        Forward ring / through-wall tab axial closeup
      </text>
      <text x="30" y="625" fill={color.soft} fontSize="12">
        Source z and R bands; both overlap in the unrelieved envelopes. Actual notch/contact fit
        remains unavailable.
      </text>
      <rect
        x={zx(zoomMin)}
        y="655"
        width={zx(zoomMax) - zx(zoomMin)}
        height="112"
        fill={color.panel}
        stroke={color.line}
      />
      {fore?.z_start_mm !== null &&
        fore?.z_end_mm !== null &&
        fore?.inner_radius_mm !== null &&
        fore?.outer_radius_mm !== null &&
        fore?.z_start_mm !== undefined &&
        fore?.z_end_mm !== undefined &&
        fore?.inner_radius_mm !== undefined &&
        fore?.outer_radius_mm !== undefined && (
          <rect
            x={zx(fore.z_start_mm)}
            y={ry(fore.outer_radius_mm)}
            width={zx(fore.z_end_mm) - zx(fore.z_start_mm)}
            height={ry(fore.inner_radius_mm) - ry(fore.outer_radius_mm)}
            fill={color.hardware}
            opacity="0.72"
          />
        )}
      {tabs?.z_start_mm !== null &&
        tabs?.z_end_mm !== null &&
        tabs?.inner_radius_mm !== null &&
        tabs?.outer_radius_mm !== null &&
        tabs?.z_start_mm !== undefined &&
        tabs?.inner_radius_mm !== undefined &&
        tabs?.outer_radius_mm !== undefined && (
          <rect
            x={zx(tabs.z_start_mm)}
            y={ry(tabs.outer_radius_mm)}
            width={zx(zoomMax) - zx(tabs.z_start_mm)}
            height={ry(tabs.inner_radius_mm) - ry(tabs.outer_radius_mm)}
            fill="none"
            stroke={color.fin}
            strokeWidth="2"
            strokeDasharray="6 4"
          />
        )}
      {overlapEnd > overlapStart && knownRadialOverlap && (
        <>
          <rect
            x={zx(overlapStart)}
            y={ry(radialOverlapEnd)}
            width={zx(overlapEnd) - zx(overlapStart)}
            height={ry(radialOverlapStart) - ry(radialOverlapEnd)}
            fill={color.red}
            opacity="0.35"
            stroke={color.red}
            strokeWidth="2"
          />
          <text x="48" y="686" fill={color.red} fontSize="13" fontWeight="700">
            Source envelope overlap: z {conventionalNumber(overlapEnd - overlapStart, 'mm')}
          </text>
          <text x="48" y="706" fill={color.soft} fontSize="11">
            Ring and tab R bands intersect; notch/relief unavailable
          </text>
        </>
      )}
      <text x="48" y="735" fill={color.soft} fontSize="11">
        Forward ring z {conventionalNumber(fore?.z_start_mm ?? null, 'mm')}–
        {conventionalNumber(fore?.z_end_mm ?? null, 'mm')}
      </text>
      <text x="48" y="753" fill={color.fin} fontSize="11">
        Integral tab begins z {conventionalNumber(tabs?.z_start_mm ?? null, 'mm')}
      </text>
      <text x="48" y="786" fill={color.soft} fontSize="11">
        Tab z to {conventionalNumber(tabs?.z_end_mm ?? null, 'mm')}; R{' '}
        {conventionalNumber(tabs?.inner_radius_mm ?? null, 'mm')}–
        {conventionalNumber(tabs?.outer_radius_mm ?? null, 'mm')}.
      </text>
      <text x="475" y="786" fill={color.soft} fontSize="11">
        Motor tube R {conventionalNumber(tube?.inner_radius_mm ?? null, 'mm')}–
        {conventionalNumber(tube?.outer_radius_mm ?? null, 'mm')}
      </text>
      <text x="475" y="804" fill={color.soft} fontSize="11">
        Ring R {conventionalNumber(fore?.inner_radius_mm ?? null, 'mm')}–
        {conventionalNumber(fore?.outer_radius_mm ?? null, 'mm')}
      </text>
      {footer(snapshot, 843)}
    </Base>
  );
}

/** Source edge graph. Layout is symbolic; each arrow is an actual recorded connection. */
export function ConventionalConnectionDrawing({
  snapshot,
  svgRef,
  onSelectComponent,
}: SelectableDrawingProps) {
  type Point = [number, number];
  const recovery: Record<string, Point> = {
    parachute: [105, 195],
    shock_cord: [285, 195],
    heat_leader: [465, 195],
    body_recovery_eye: [645, 195],
    forward_ring: [825, 195],
    body: [980, 195],
    nose_recovery_eye: [465, 290],
    nose_anchor_plate: [645, 290],
    nose: [825, 290],
  };
  const structure: Record<string, Point> = {
    fin_set: [105, 485],
    fin_tabs: [285, 485],
    motor_tube: [645, 485],
    forward_ring: [465, 405],
    aft_ring: [825, 485],
    body: [980, 485],
    motor: [105, 595],
    motor_retainer: [285, 595],
    rail_buttons: [825, 595],
  };
  const nodes = (positions: Record<string, Point>) =>
    Object.entries(positions).map(([id, [cx, cy]]) => {
      const item = snapshot.components.find((component) => component.id === id);
      return (
        <g
          key={id}
          onClick={() => onSelectComponent?.(id)}
          style={{ cursor: onSelectComponent ? 'pointer' : undefined }}
        >
          <rect
            x={cx - 67}
            y={cy - 22}
            width="134"
            height="44"
            rx="6"
            fill={color.panel}
            stroke={color.line}
            strokeWidth="2"
          />
          <text x={cx} y={cy + 4} textAnchor="middle" fill={color.pale} fontSize="11">
            {item?.label ?? id}
          </text>
        </g>
      );
    });
  const edges = (positions: Record<string, Point>) =>
    snapshot.connections
      .filter((edge) => positions[edge.from_id] && positions[edge.to_id])
      .map((edge) => {
        const [x1, y1] = positions[edge.from_id];
        const [x2, y2] = positions[edge.to_id];
        const dx = x2 - x1,
          dy = y2 - y1,
          length = Math.hypot(dx, dy);
        const ux = dx / length,
          uy = dy / length;
        const ex = x2 - 71 * ux,
          ey = y2 - 27 * uy;
        const sx = x1 + 71 * ux,
          sy = y1 + 27 * uy;
        const fill = edge.state === 'failed' ? color.red : color.blue;
        const px = -uy,
          py = ux;
        const points = `${ex},${ey} ${ex - 10 * ux + 5 * px},${ey - 10 * uy + 5 * py} ${ex - 10 * ux - 5 * px},${ey - 10 * uy - 5 * py}`;
        return (
          <g key={edge.id}>
            <path
              d={`M${sx} ${sy}L${ex} ${ey}`}
              stroke={fill}
              strokeWidth="2.5"
              fill="none"
              strokeDasharray={edge.state === 'unavailable' ? '6 4' : undefined}
            />
            <polygon points={points} fill={fill} />
          </g>
        );
      });
  const legend = snapshot.connections.filter(
    (edge) =>
      (recovery[edge.from_id] && recovery[edge.to_id]) ||
      (structure[edge.from_id] && structure[edge.to_id]),
  );
  const height = 780 + legend.length * 22;
  return (
    <Base
      title="G80-F1 · recorded connection graph"
      subtitle="Arrows are source connection records; dashed means unavailable, red means failed. No equal sharing or capacity inferred."
      height={height}
      svgRef={svgRef}
    >
      <text x="30" y="113" fill={color.blue} fontSize="16" fontWeight="700">
        Proposed canopy/body and nose branches
      </text>
      <rect x="30" y="132" width="1020" height="205" rx="8" fill="#172c38" stroke={color.line} />
      {edges(recovery)}
      {nodes(recovery)}
      <text x="30" y="374" fill={color.blue} fontSize="16" fontWeight="700">
        Fin, fixed mount and motor paths
      </text>
      <rect x="30" y="390" width="1020" height="240" rx="8" fill="#172c38" stroke={color.line} />
      {edges(structure)}
      {nodes(structure)}
      <text x="30" y="662" fill={color.blue} fontSize="15" fontWeight="700">
        Recorded edge states
      </text>
      {legend.map((edge, i) => (
        <g key={edge.id}>
          <circle
            cx="42"
            cy={685 + i * 22}
            r="4"
            fill={edge.state === 'failed' ? color.red : color.blue}
          />
          <text x="55" y={689 + i * 22} fill={color.soft} fontSize="11">
            {edge.label} · {edge.kind} · {edge.state}
          </text>
        </g>
      ))}
      {footer(snapshot, height - 57)}
    </Base>
  );
}

/** An axial station plot of recorded component envelopes, not a fabricated CAD side view. */
export function ConventionalArrangementDrawing({ snapshot, svgRef }: DrawingProps) {
  const intervals = snapshot.components.filter(
    (part) => part.z_start_mm !== null && part.z_end_mm !== null && part.z_end_mm > part.z_start_mm,
  );
  const bounds = intervals.flatMap((part) => [part.z_start_mm!, part.z_end_mm!]);
  const min = bounds.length ? Math.min(...bounds) : null;
  const max = bounds.length ? Math.max(...bounds) : null;
  const span = min !== null && max !== null && max > min ? max - min : null;
  const x = (station: number) => 350 + ((station - min!) / span!) * 650;
  const rows = snapshot.components.map((part) => ({
    part,
    h: Math.max(95, 74 + wrap(part.function, 105).length * 16),
  }));
  const height = 230 + rows.reduce((sum, row) => sum + row.h, 0) + 80;
  let y = 126;
  return (
    <Base
      title="G80-F1 · conventional fixed-motor arrangement"
      subtitle="ONE continuous body · fixed commercial 29 mm motor · source envelopes, not CAD"
      height={height}
      svgRef={svgRef}
    >
      <text x="30" y={y} fill={color.blue} fontSize="15" fontWeight="700">
        Component function and axial source placement
      </text>
      {span !== null && (
        <>
          <path d={`M350 ${y + 30}H1000`} stroke={color.line} />
          <text x="350" y={y + 25} fill={color.amber} fontSize="11">
            z {conventionalNumber(min, 'mm')}
          </text>
          <text x="912" y={y + 25} fill={color.amber} fontSize="11">
            z {conventionalNumber(max, 'mm')}
          </text>
        </>
      )}
      {rows.map(({ part, h }) => {
        const rowY = y + 46;
        y += h;
        return (
          <g key={part.id}>
            <rect
              x="30"
              y={rowY}
              width="1020"
              height={h - 5}
              rx="7"
              fill={color.panel}
              stroke={color.line}
            />
            <text x="48" y={rowY + 23} fill={color.pale} fontSize="14" fontWeight="700">
              {part.label}
            </text>
            <text x="48" y={rowY + 42} fill={color.soft} fontSize="11">
              {part.category} · {part.maturity} · {conventionalNumber(part.mass_g, 'g')}
            </text>
            {span !== null &&
              part.z_start_mm !== null &&
              part.z_end_mm !== null &&
              part.z_end_mm > part.z_start_mm && (
                <rect
                  x={x(part.z_start_mm)}
                  y={rowY + 12}
                  width={Math.max(2, x(part.z_end_mm) - x(part.z_start_mm))}
                  height="18"
                  fill={color[part.category]}
                />
              )}
            <text x="350" y={rowY + 48} fill={color.amber} fontSize="11">
              z {conventionalNumber(part.z_start_mm, 'mm')} to{' '}
              {conventionalNumber(part.z_end_mm, 'mm')}
              {' · '}R {conventionalNumber(part.inner_radius_mm, 'mm')} to{' '}
              {conventionalNumber(part.outer_radius_mm, 'mm')}
            </text>
            <Lines value={part.function} x={350} y={rowY + 66} width={108} size={11} />
          </g>
        );
      })}
      {footer(snapshot, height - 57)}
    </Base>
  );
}

/** Connection/sequence cards preserve independent source steps and evidence state. */
export function ConventionalConstructionDrawing({ snapshot, svgRef }: DrawingProps) {
  const sectionH = snapshot.sections.reduce(
    (sum, item) => sum + Math.max(94, 62 + wrap(item.note, 125).length * 16),
    0,
  );
  const connectionH = snapshot.connections.reduce(
    (sum, item) => sum + Math.max(100, 70 + wrap(item.note, 125).length * 16),
    0,
  );
  const assemblyH = snapshot.sequences.assembly.reduce(
    (sum, item) => sum + Math.max(86, 57 + wrap(item.note, 125).length * 16),
    0,
  );
  const recoveryH = snapshot.sequences.recovery.reduce(
    (sum, item) => sum + Math.max(86, 57 + wrap(item.note, 125).length * 16),
    0,
  );
  const height = 280 + sectionH + connectionH + assemblyH + recoveryH + 95;
  let y = 112;
  return (
    <Base
      title="G80-F1 · sections, construction and recovery"
      subtitle="Source-connected parts and recorded sequence; deployment and joint capacity remain open"
      height={height}
      svgRef={svgRef}
    >
      <text x="30" y={y} fill={color.blue} fontSize="16" fontWeight="700">
        Sections through the single fixed body
      </text>
      {snapshot.sections.map((item) => {
        const rowY = y + 22;
        const h = Math.max(94, 62 + wrap(item.note, 125).length * 16);
        y += h;
        return (
          <g key={item.id}>
            <rect
              x="30"
              y={rowY}
              width="1020"
              height={h - 5}
              rx="7"
              fill={color.panel}
              stroke={color.line}
            />
            <text x="48" y={rowY + 25} fill={color.pale} fontSize="15" fontWeight="700">
              {item.label}
            </text>
            <text x="730" y={rowY + 25} fill={color.amber} fontSize="12">
              z {conventionalNumber(item.station_mm, 'mm')}
            </text>
            <text x="48" y={rowY + 47} fill={color.blue} fontSize="12">
              {item.component_ids.join(' · ') || 'Components unavailable'}
            </text>
            <Lines value={item.note} x={48} y={rowY + 67} width={125} size={11} />
          </g>
        );
      })}
      {(() => {
        y += 37;
        return (
          <text x="30" y={y} fill={color.blue} fontSize="16" fontWeight="700">
            Source-defined connections
          </text>
        );
      })()}
      {snapshot.connections.map((item) => {
        const rowY = y + 22;
        const h = Math.max(100, 70 + wrap(item.note, 125).length * 16);
        y += h;
        return (
          <g key={item.id}>
            <rect
              x="30"
              y={rowY}
              width="1020"
              height={h - 5}
              rx="7"
              fill={color.panel}
              stroke={color.line}
            />
            <text x="48" y={rowY + 25} fill={color.pale} fontSize="15" fontWeight="700">
              {item.label}
            </text>
            <text
              x="807"
              y={rowY + 25}
              fill={item.state === 'failed' ? color.red : color.amber}
              fontSize="12"
            >
              {item.state}
            </text>
            <path
              d={`M48 ${rowY + 48}H95m-8-6 8 6-8 6`}
              stroke={color.blue}
              fill="none"
              strokeWidth="2"
            />
            <text x="107" y={rowY + 52} fill={color.blue} fontSize="12">
              {item.from_id} → {item.to_id} · {item.kind}
            </text>
            <Lines value={item.note} x={48} y={rowY + 75} width={125} size={11} />
          </g>
        );
      })}
      {(() => {
        y += 37;
        return (
          <text x="30" y={y} fill={color.blue} fontSize="16" fontWeight="700">
            Construction sequence · illustration, not a procedure approval
          </text>
        );
      })()}
      {snapshot.sequences.assembly.map((item, i) => {
        const rowY = y + 22;
        const h = Math.max(86, 57 + wrap(item.note, 125).length * 16);
        y += h;
        return (
          <g key={item.id}>
            <rect
              x="30"
              y={rowY}
              width="1020"
              height={h - 5}
              rx="7"
              fill={color.panel}
              stroke={color.line}
            />
            <circle cx="59" cy={rowY + 29} r="15" fill={color.amber} />
            <text x="54" y={rowY + 34} fill={color.bg} fontSize="13" fontWeight="700">
              {i + 1}
            </text>
            <text x="87" y={rowY + 26} fill={color.pale} fontSize="14" fontWeight="700">
              {item.label}
            </text>
            <text x="87" y={rowY + 47} fill={color.blue} fontSize="11">
              {item.acts_on_ids.join(' · ')}
            </text>
            <Lines value={item.note} x={48} y={rowY + 67} width={125} size={11} />
          </g>
        );
      })}
      {(() => {
        y += 37;
        return (
          <text x="30" y={y} fill={color.blue} fontSize="16" fontWeight="700">
            Recovery sequence · illustrative, not deployed-motion validation
          </text>
        );
      })()}
      {snapshot.sequences.recovery.map((item, i) => {
        const rowY = y + 22;
        const h = Math.max(86, 57 + wrap(item.note, 125).length * 16);
        y += h;
        return (
          <g key={item.id}>
            <rect
              x="30"
              y={rowY}
              width="1020"
              height={h - 5}
              rx="7"
              fill={color.panel}
              stroke={color.line}
            />
            <circle cx="59" cy={rowY + 29} r="15" fill={color.recovery} />
            <text x="54" y={rowY + 34} fill={color.bg} fontSize="13" fontWeight="700">
              {i + 1}
            </text>
            <text x="87" y={rowY + 26} fill={color.pale} fontSize="14" fontWeight="700">
              {item.label}
            </text>
            <text x="87" y={rowY + 47} fill={color.blue} fontSize="11">
              {item.acts_on_ids.join(' · ')}
            </text>
            <Lines value={item.note} x={48} y={rowY + 67} width={125} size={11} />
          </g>
        );
      })}
      {footer(snapshot, height - 57)}
    </Base>
  );
}

export function ConventionalMassDrawing({ snapshot, svgRef }: DrawingProps) {
  const casesH = snapshot.cases.reduce(
    (sum, item) => sum + Math.max(160, 130 + wrap(item.note, 120).length * 16),
    0,
  );
  const findingsH = snapshot.uncertainties.reduce(
    (sum, item) => sum + Math.max(86, 55 + wrap(item.note, 120).length * 16),
    0,
  );
  const height = 205 + casesH + findingsH + 100;
  let y = 112;
  return (
    <Base
      title="G80-F1 · mass, guide and uncertainty record"
      subtitle="Complete recorded cases only · full allowance and separate formal/planning checks"
      height={height}
      svgRef={svgRef}
    >
      <text x="30" y={y} fill={color.blue} fontSize="16" fontWeight="700">
        Source-calculated case values
      </text>
      {snapshot.cases.map((item) => {
        const rowY = y + 23;
        const h = Math.max(160, 130 + wrap(item.note, 120).length * 16);
        y += h;
        return (
          <g key={item.id}>
            <rect
              x="30"
              y={rowY}
              width="1020"
              height={h - 6}
              rx="8"
              fill={color.panel}
              stroke={color.line}
            />
            <text x="48" y={rowY + 27} fill={color.pale} fontSize="16" fontWeight="700">
              {item.label}
            </text>
            <text x="48" y={rowY + 51} fill={color.amber} fontSize="13">
              Mass {conventionalNumber(item.total_mass_g, 'g')} · loaded CG{' '}
              {conventionalNumber(item.loaded_cg_mm, 'mm')}
              {' · '}reference CP {conventionalNumber(item.reference_cp_mm, 'mm')}
            </text>
            <text x="48" y={rowY + 74} fill={color.blue} fontSize="13">
              Margin {conventionalNumber(item.margin_cal, 'cal')} · guide{' '}
              {conventionalNumber(item.guide_speed_mps, 'm/s')}
              {' at '}
              {conventionalNumber(item.usable_guide_m, 'm')} usable
            </text>
            <text x="48" y={rowY + 96} fill={color.red} fontSize="12">
              Formal 15 m/s headroom {conventionalNumber(item.formal_headroom_g, 'g')}
              {' · '}separate 15.5 planning {conventionalNumber(item.planning_headroom_g, 'g')}
            </text>
            <Lines value={item.note} x={48} y={rowY + 117} width={120} size={11} />
          </g>
        );
      })}
      {(() => {
        y += 38;
        return (
          <text x="30" y={y} fill={color.blue} fontSize="16" fontWeight="700">
            Unresolved design and evidence
          </text>
        );
      })()}
      {snapshot.uncertainties.map((item) => {
        const rowY = y + 22;
        const h = Math.max(86, 55 + wrap(item.note, 120).length * 16);
        y += h;
        return (
          <g key={item.id}>
            <rect
              x="30"
              y={rowY}
              width="1020"
              height={h - 5}
              rx="7"
              fill={color.panel}
              stroke={color.line}
            />
            <text x="48" y={rowY + 25} fill={color.pale} fontSize="14" fontWeight="700">
              {item.label}
            </text>
            <text
              x="870"
              y={rowY + 25}
              fill={item.state === 'failed' ? color.red : color.amber}
              fontSize="12"
            >
              {item.state}
            </text>
            <Lines value={item.note} x={48} y={rowY + 48} width={120} size={11} />
          </g>
        );
      })}
      {footer(snapshot, height - 57)}
    </Base>
  );
}

function saveSvg(svg: SVGSVGElement | null, snapshot: ConventionalSnapshot, name: string) {
  if (!svg) return;
  const clone = svg.cloneNode(true) as SVGSVGElement;
  const metadata = document.createElementNS('http://www.w3.org/2000/svg', 'metadata');
  metadata.textContent = JSON.stringify({
    title: name,
    identity: snapshot.identity,
    sources: snapshot.generated_from,
    cad_manifest: snapshot.cad_manifest,
    representation:
      'Source projection; exact CAD only when the manifest identifies this candidate.',
  });
  clone.prepend(metadata);
  const url = URL.createObjectURL(
    new Blob([new XMLSerializer().serializeToString(clone)], { type: 'image/svg+xml' }),
  );
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `g80-f1-${name}.svg`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function ConventionalG80Views({
  snapshot,
  prepared = false,
}: {
  snapshot: ConventionalSnapshot;
  prepared?: boolean;
}) {
  const rocket = useRef<SVGSVGElement>(null);
  const graph = useRef<SVGSVGElement>(null);
  const arrangement = useRef<SVGSVGElement>(null);
  const construction = useRef<SVGSVGElement>(null);
  const mass = useRef<SVGSVGElement>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = snapshot.components.find((part) => part.id === selectedId);
  return (
    <div className="g80-fixed-view">
      <section className="g80-fixed-header">
        <span className="g80-fixed-kicker">
          Separate G80-F1 conventional candidate · {snapshot.identity.source_identity}
        </span>
        <h2>{snapshot.label}</h2>
        <p>{snapshot.status}</p>
        {prepared && (
          <p className="g80-fixed-banner">
            Prepared offline export because the current API has no G80-F1 route.
          </p>
        )}
        <p className="g80-fixed-banner">
          This is a source projection of one fixed-motor body. Detailed CAD appears only with a
          matching G80-F1 manifest; construction, recovery and flight acceptance remain open.
        </p>
      </section>
      <section className="g80-fixed-inspector" aria-live="polite">
        <h3>{selected ? selected.label : 'Select a component in the drawings'}</h3>
        {selected ? (
          <>
            <p>{selected.function}</p>
            <p>
              {selected.construction} · {selected.material} ·{' '}
              {conventionalNumber(selected.mass_g, 'g')}
            </p>
            <p>
              z {conventionalNumber(selected.z_start_mm, 'mm')} to{' '}
              {conventionalNumber(selected.z_end_mm, 'mm')} · {selected.maturity} / {selected.state}
            </p>
            <p>{selected.note}</p>
            <small>Source IDs: {selected.source_ids.join(', ')}</small>
          </>
        ) : (
          <p>
            Source stations are scaled in the rocket envelope; radial fit and capacity remain open.
          </p>
        )}
      </section>
      <section>
        <div className="g80-fixed-heading">
          <h3>Single-body rocket and critical section</h3>
          <button type="button" onClick={() => saveSvg(rocket.current, snapshot, 'rocket-section')}>
            Download SVG
          </button>
        </div>
        <div className="g80-fixed-figure">
          <ConventionalRocketDrawing
            snapshot={snapshot}
            svgRef={rocket}
            onSelectComponent={setSelectedId}
          />
        </div>
      </section>
      <section>
        <div className="g80-fixed-heading">
          <h3>Recorded connection graph</h3>
          <button
            type="button"
            onClick={() => saveSvg(graph.current, snapshot, 'connection-graph')}
          >
            Download SVG
          </button>
        </div>
        <div className="g80-fixed-figure">
          <ConventionalConnectionDrawing
            snapshot={snapshot}
            svgRef={graph}
            onSelectComponent={setSelectedId}
          />
        </div>
      </section>
      {(
        [
          [
            'Arrangement and component functions',
            arrangement,
            'arrangement',
            ConventionalArrangementDrawing,
          ],
          [
            'Sections and sequences',
            construction,
            'construction-recovery',
            ConventionalConstructionDrawing,
          ],
          ['Mass and uncertainties', mass, 'mass-uncertainty', ConventionalMassDrawing],
        ] as const
      ).map(([title, ref, id, Drawing]) => (
        <section key={id}>
          <div className="g80-fixed-heading">
            <h3>{title}</h3>
            <button type="button" onClick={() => saveSvg(ref.current, snapshot, id)}>
              Download SVG
            </button>
          </div>
          {id === 'mass-uncertainty' ? (
            <div className="g80-fixed-figure">
              <Drawing snapshot={snapshot} svgRef={ref} />
            </div>
          ) : (
            <details className="g80-fixed-source-rows">
              <summary>Open complete source rows</summary>
              <div className="g80-fixed-figure">
                <Drawing snapshot={snapshot} svgRef={ref} />
              </div>
            </details>
          )}
        </section>
      ))}
      <section>
        <h3>Component source record</h3>
        <div className="g80-fixed-parts">
          {snapshot.components.map((part) => (
            <article key={part.id}>
              <h4>{part.label}</h4>
              <p>{part.function}</p>
              <p>
                {part.construction} · {part.material}
              </p>
              <small>
                {part.maturity} · {part.state} · {part.source_ids.join(', ')}
              </small>
              <p>{part.note}</p>
            </article>
          ))}
        </div>
      </section>
      <section>
        <h3>CAD identity</h3>
        <p>
          {snapshot.cad_manifest
            ? `Exact G80-F1 manifest ${snapshot.cad_manifest.revision}; ${snapshot.cad_manifest.parts.length} listed parts.`
            : 'No same-design detailed CAD manifest is available for G80-F1.'}
        </p>
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
