import { useId, useRef, useState } from 'react';
import type { CSSProperties, KeyboardEvent, ReactNode, RefObject } from 'react';
import type { BudgetCase, WorkbenchDocument } from './types';
import { downloadWorkbenchSvg } from './exportSvg';
import './massLaunchViews.css';

type Props = {
  document: WorkbenchDocument;
  selectedPartId: string | null;
  onSelectPart: (id: string) => void;
};
const COLORS = ['#77cee5', '#b5a0ec', '#e1b276', '#ec9fa6'];
const n = (value: number, digits = 3) =>
  new Intl.NumberFormat('en', { maximumFractionDigits: digits }).format(value);
const finite = (value: number | undefined | null): value is number =>
  value != null && Number.isFinite(value);
function selectionHandlers(
  id: string | null,
  selectedPartId: string | null,
  onSelectPart: (id: string) => void,
  label: string,
) {
  if (!id) return { 'aria-label': label };
  return {
    role: 'button' as const,
    tabIndex: 0,
    'aria-label': `${label}. Select part`,
    'aria-pressed': selectedPartId === id,
    onClick: () => onSelectPart(id),
    onKeyDown: (event: KeyboardEvent<SVGGElement>) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        onSelectPart(id);
      }
    },
  };
}
function Figure({
  title,
  note,
  svgRef,
  document: doc,
  children,
}: {
  title: string;
  note: string;
  svgRef: RefObject<SVGSVGElement | null>;
  document: WorkbenchDocument;
  children: ReactNode;
}) {
  return (
    <section className="wb-mass-figure">
      <div className="wb-mass-heading">
        <h3>{title}</h3>
        <button type="button" onClick={() => downloadWorkbenchSvg(svgRef.current, doc, title)}>
          Export SVG
        </button>
      </div>
      <p>{note}</p>
      <div className="wb-mass-canvas">{children}</div>
      <div className="wb-mass-stamp">
        Recorded preliminary screen · engineering and flight acceptance open
      </div>
    </section>
  );
}
function SvgAxes({
  left,
  right,
  top,
  bottom,
  xLabel,
  yLabel,
}: {
  left: number;
  right: number;
  top: number;
  bottom: number;
  xLabel: string;
  yLabel: string;
}) {
  return (
    <g className="wb-mass-axis">
      <path d={`M${left},${top}V${bottom}H${right}`} />
      <text x={(left + right) / 2} y={bottom + 44} textAnchor="middle">
        {xLabel}
      </text>
      <text transform={`translate(20 ${(top + bottom) / 2}) rotate(-90)`} textAnchor="middle">
        {yLabel}
      </text>
    </g>
  );
}

function Balance({
  document: doc,
  activeCase,
  burnout,
}: {
  document: WorkbenchDocument;
  activeCase: BudgetCase;
  burnout: boolean;
}) {
  const x = (station: number) =>
    70 +
    (station /
      Math.max(
        doc.arrangement.overall_length_mm,
        activeCase.cp_mm,
        activeCase.cg_mm,
        activeCase.burnout_cg_mm,
        1,
      )) *
      930;
  const cg = burnout ? activeCase.burnout_cg_mm : activeCase.cg_mm;
  return (
    <svg
      viewBox="0 0 1100 205"
      role="img"
      aria-label={`${burnout ? 'Burnout' : 'Loaded'} balance: CG ${n(cg)} mm; CP ${n(activeCase.cp_mm)} mm`}
    >
      <title>Recorded balance positions · preliminary static model</title>
      <text x={70} y={27} className="wb-mass-kicker">
        {burnout ? 'BURNOUT' : 'LOADED'} · {activeCase.label}
      </text>
      <path className="wb-mass-reference" d="M70,95H1000" />
      <rect
        className="wb-mass-body"
        x={70}
        y={78}
        width={x(doc.arrangement.overall_length_mm) - 70}
        height={34}
        rx={4}
      />
      <path className="wb-mass-cg" d={`M${x(cg)},50v84`} />
      <circle className="wb-mass-cg" cx={x(cg)} cy={95} r={7} />
      <path className="wb-mass-cp" d={`M${x(activeCase.cp_mm)},70v95`} />
      <circle className="wb-mass-cp" cx={x(activeCase.cp_mm)} cy={95} r={9} />
      <text x={x(cg)} y={44} textAnchor="middle">
        CG {n(cg)} mm
      </text>
      <text x={x(activeCase.cp_mm)} y={184} textAnchor="middle">
        CP {n(activeCase.cp_mm)} mm
      </text>
      <text x={70} y={150} className="wb-mass-small">
        Nose · station 0
      </text>
      <text x={1000} y={150} textAnchor="end" className="wb-mass-small">
        Aft · {n(doc.arrangement.overall_length_mm)} mm
      </text>
      <text x={70} y={185} className="wb-mass-small">
        ● CG: balance point · ○ CP: aerodynamic-force location
      </text>
    </svg>
  );
}

function MassDistribution({ document: doc, selectedPartId, onSelectPart }: Props) {
  const left = 78;
  const right = 1025;
  const top = 58;
  const bottom = 295;
  const entries = doc.mass_distribution.filter(
    (entry) => finite(entry.mass_g) && finite(entry.station_mm),
  );
  const maxMass = Math.max(...entries.map((entry) => entry.mass_g), 1);
  const maxStation = Math.max(
    doc.arrangement.overall_length_mm,
    ...entries.map((entry) => entry.station_mm),
    1,
  );
  const groups = [...new Set(entries.map((entry) => entry.subsystem))];
  const x = (station: number) => left + (station / maxStation) * (right - left);
  const y = (mass: number) => bottom - (mass / maxMass) * (bottom - top);
  return (
    <g>
      <title>Frozen C1 point-mass ledger · individual recorded rows, not full inertia</title>
      <SvgAxes
        {...{ left, right, top, bottom }}
        xLabel="Axial station from nose (mm)"
        yLabel="Recorded row mass (g)"
      />
      {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
        <g key={fraction} className="wb-mass-grid">
          <path d={`M${left},${y(maxMass * fraction)}H${right}`} />
          <text x={left - 12} y={y(maxMass * fraction) + 4} textAnchor="end">
            {n(maxMass * fraction, 1)}
          </text>
          <text x={x(maxStation * fraction)} y={bottom + 20} textAnchor="middle">
            {n(maxStation * fraction, 1)}
          </text>
        </g>
      ))}
      {entries.map((entry) => (
        <g
          key={entry.id}
          {...selectionHandlers(
            entry.part_id,
            selectedPartId,
            onSelectPart,
            `${entry.label}: ${n(entry.mass_g)} g at ${n(entry.station_mm)} mm; ${entry.state}`,
          )}
          className={`wb-mass-point ${entry.part_id ? 'is-selectable' : ''} ${entry.part_id && selectedPartId === entry.part_id ? 'is-selected' : ''}`}
          style={
            {
              '--mass-color':
                entry.subsystem === 'allowance'
                  ? '#d6dce1'
                  : COLORS[groups.indexOf(entry.subsystem) % COLORS.length],
            } as CSSProperties
          }
        >
          <title>{`${entry.label} · ${n(entry.mass_g)} g · station ${n(entry.station_mm)} mm · ${entry.state}${entry.part_id ? '' : ' · allowance, no physical part'}`}</title>
          <path d={`M${x(entry.station_mm)},${bottom}V${y(entry.mass_g)}`} />
          <circle
            cx={x(entry.station_mm)}
            cy={y(entry.mass_g)}
            r={selectedPartId === entry.part_id ? 7 : 4.5}
          />
        </g>
      ))}
      <text x={left} y={377} className="wb-mass-small">
        Rows at the same station overlap. Select a point or use the ledger key below. This is not a
        full inertia model.
      </text>
    </g>
  );
}

function GroupBars({ document: doc, selectedPartId, onSelectPart }: Props) {
  const groups = doc.mass_groups;
  const max = Math.max(...groups.map((group) => group.mass_g), 1);
  return (
    <g>
      <title>Recorded C1 group masses · preliminary ledger</title>
      {groups.map((group, index) => {
        const selected = selectedPartId != null && group.part_ids.includes(selectedPartId);
        const targetId = selected ? selectedPartId : (group.part_ids[0] ?? null);
        const py = 25 + index * 53;
        return (
          <g
            key={group.id}
            {...selectionHandlers(
              targetId,
              selectedPartId,
              onSelectPart,
              `${group.label}: ${n(group.mass_g)} g; ${group.state}`,
            )}
            className={`wb-mass-group ${targetId ? 'is-selectable' : ''} ${selected ? 'is-selected' : ''}`}
            style={{ '--mass-color': COLORS[index % COLORS.length] } as CSSProperties}
          >
            <title>{`${group.label} · ${n(group.mass_g)} g · ${group.state}${targetId ? ' · activates associated part' : ''}`}</title>
            <text x={24} y={py + 18}>
              {group.label}
            </text>
            <rect x={350} y={py} width={(group.mass_g / max) * 545} height={26} rx={3} />
            <text x={915} y={py + 18}>
              {n(group.mass_g)} g
            </text>
            <text x={350} y={py + 42} className="wb-mass-small">
              {group.state} · {group.part_ids.length} associated parts
            </text>
          </g>
        );
      })}
    </g>
  );
}

function RevisionMassBars({ document: doc, selectedPartId, onSelectPart }: Props) {
  const rows = (doc.revision_mass_changes ?? []).filter((row) => row.revision === 'R1');
  const maxMass = Math.max(...rows.map((row) => row.mass_g).filter(finite), 1);
  const maxStation = Math.max(
    doc.arrangement.overall_length_mm,
    ...rows.map((row) => row.station_mm).filter(finite),
    1,
  );
  const stationX = (station: number) => 795 + (station / maxStation) * 235;
  const r1Case =
    doc.cases.find((item) => item.id === 'R1_nominal') ??
    doc.cases.find((item) => item.id.startsWith('R1'));
  return (
    <g>
      <title>
        R1 estimated mass additions by item and source station · stopped comparison, not active C1
      </title>
      <text x={24} y={27} className="wb-mass-kicker">
        R1 ADDITIONS ONLY · ESTIMATED · STOPPED BEFORE CAD / NATIVE ANALYSIS
      </text>
      <text x={24} y={53} className="wb-mass-small">
        C1 distribution is unchanged. Recorded R1 addition:{' '}
        {r1Case ? `+${n(r1Case.added_mass_g)} g` : 'unavailable'}; not recomputed from these bars.
      </text>
      <text x={24} y={88} className="wb-mass-small">
        Recorded added item
      </text>
      <text x={350} y={88} className="wb-mass-small">
        Added mass (g)
      </text>
      <text x={795} y={88} className="wb-mass-small">
        Source station from nose (mm)
      </text>
      {rows.map((row, index) => {
        const target = row.part_ids[0];
        const validTarget = target && doc.parts.some((part) => part.id === target) ? target : null;
        const selected = selectedPartId != null && row.part_ids.includes(selectedPartId);
        const py = 111 + index * 62;
        const massAvailable = finite(row.mass_g) && row.mass_g >= 0;
        return (
          <g
            key={row.id}
            {...selectionHandlers(
              validTarget,
              selectedPartId,
              onSelectPart,
              `${row.label}: added ${n(row.mass_g)} g at ${n(row.station_mm)} mm; ${row.state}`,
            )}
            className={`wb-mass-revision-row ${validTarget ? 'is-selectable' : ''} ${selected ? 'is-selected' : ''}`}
          >
            <title>{`${row.label} · R1 estimated addition ${n(row.mass_g)} g · station ${n(row.station_mm)} mm · ${row.state}${validTarget ? ' · select associated C1 component; no detailed R1 part geometry supplied' : ' · no selectable source part mapping'}`}</title>
            <text x={24} y={py + 18} className="wb-mass-revision-label">
              {row.label}
            </text>
            {massAvailable && (
              <rect x={350} y={py} width={(row.mass_g / maxMass) * 305} height={25} rx={3} />
            )}
            <text x={673} y={py + 18}>
              {massAvailable ? `+${n(row.mass_g)} g` : 'Unavailable'}
            </text>
            <path className="wb-mass-revision-station" d={`M795,${py + 12}H1030`} />
            {finite(row.station_mm) && <circle cx={stationX(row.station_mm)} cy={py + 12} r={5} />}
            <text
              x={finite(row.station_mm) ? stationX(row.station_mm) : 795}
              y={py + 43}
              textAnchor={finite(row.station_mm) ? 'middle' : 'start'}
              className="wb-mass-small"
            >
              {finite(row.station_mm) ? `${n(row.station_mm)} mm` : 'Station unavailable'}
            </text>
            <text x={350} y={py + 43} className="wb-mass-small">
              {row.state} ·{' '}
              {validTarget ? 'select associated source component' : 'part mapping unavailable'}
            </text>
          </g>
        );
      })}
      <text x={24} y={130 + rows.length * 62} className="wb-mass-small">
        Bar length shows each supplied addition; dots locate its recorded axial allocation. No
        material removal, fit or acceptance is implied.
      </text>
    </g>
  );
}

function GuideChart({
  document: doc,
  activeCase,
  onSelectCase,
}: {
  document: WorkbenchDocument;
  activeCase: BudgetCase;
  onSelectCase: (id: string) => void;
}) {
  const left = 80;
  const right = 1018;
  const top = 48;
  const bottom = 340;
  const all = doc.cases.flatMap((item) => item.guide_results);
  const minTravel = Math.min(doc.launch.baseline_usable_m, ...all.map((point) => point.usable_m));
  const maxTravel = Math.max(...all.map((point) => point.usable_m), minTravel + 0.01);
  const minSpeed = Math.min(
    ...all.map((point) => point.speed_mps),
    doc.launch.formal_mps,
    doc.launch.planning_mps,
  );
  const maxSpeed = Math.max(
    ...all.map((point) => point.speed_mps),
    doc.launch.formal_mps,
    doc.launch.planning_mps,
  );
  const yFloor = Math.floor(minSpeed);
  const yCeiling = Math.ceil(maxSpeed);
  const x = (travel: number) =>
    left + ((travel - minTravel) / (maxTravel - minTravel)) * (right - left);
  const y = (speed: number) =>
    bottom - ((speed - yFloor) / Math.max(yCeiling - yFloor, 1)) * (bottom - top);
  const travels = [
    ...new Set([doc.launch.baseline_usable_m, ...all.map((point) => point.usable_m)]),
  ].sort((a, b) => a - b);
  const speeds = [...new Set([yFloor, yCeiling, doc.launch.formal_mps, doc.launch.planning_mps])];
  return (
    <g>
      <title>Recorded guide-speed samples · conditional planning only · baseline unchanged</title>
      <SvgAxes
        {...{ left, right, top, bottom }}
        xLabel="Usable guide travel (m); equipment unconfirmed"
        yLabel="Recorded departure speed (m/s)"
      />
      {speeds.map((speed) => (
        <g key={speed} className="wb-mass-grid">
          <path d={`M${left},${y(speed)}H${right}`} />
          <text x={left - 10} y={y(speed) + 4} textAnchor="end">
            {n(speed)}
          </text>
        </g>
      ))}
      {travels.map((travel) => (
        <g key={travel} className="wb-mass-grid">
          <path d={`M${x(travel)},${top}V${bottom}`} />
          <text x={x(travel)} y={bottom + 22} textAnchor="middle">
            {n(travel)}
          </text>
        </g>
      ))}
      <g className="wb-mass-baseline">
        <path d={`M${x(doc.launch.baseline_usable_m)},${top}V${bottom}`} />
        <text x={x(doc.launch.baseline_usable_m) + 8} y={top - 17}>
          Baseline {n(doc.launch.baseline_usable_m)} m retained
        </text>
      </g>
      {[
        { speed: doc.launch.formal_mps, label: 'Formal', className: 'formal' },
        { speed: doc.launch.planning_mps, label: 'Separate planning', className: 'planning' },
      ].map((item) => (
        <g key={item.label} className={`wb-mass-target ${item.className}`}>
          <path d={`M${left},${y(item.speed)}H${right}`} />
          <text x={right - 8} y={y(item.speed) - 8} textAnchor="end">
            {item.label} {n(item.speed)} m/s
          </text>
        </g>
      ))}
      {doc.cases.map((item, index) => {
        const points = [...item.guide_results].sort((a, b) => a.usable_m - b.usable_m);
        const selected = item.id === activeCase.id;
        return (
          <g
            key={item.id}
            className={`wb-mass-guide-line ${selected ? 'is-active' : ''}`}
            style={{ '--mass-color': COLORS[index % COLORS.length] } as CSSProperties}
          >
            <path
              d={points
                .map((point, i) => `${i ? 'L' : 'M'}${x(point.usable_m)},${y(point.speed_mps)}`)
                .join(' ')}
            />
            {points.map((point) => (
              <g
                key={point.usable_m}
                role="button"
                tabIndex={0}
                className="wb-mass-guide-point"
                aria-label={`Select ${item.label}, ${n(point.usable_m)} m usable, ${n(point.speed_mps, 9)} m/s recorded`}
                aria-pressed={selected}
                onClick={() => onSelectCase(item.id)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    onSelectCase(item.id);
                  }
                }}
              >
                <title>{`${item.label} · ${n(point.usable_m)} m usable · ${n(point.speed_mps, 9)} m/s · formal margin ${n(point.formal_margin_mps, 9)} m/s · planning margin ${n(point.planning_margin_mps, 9)} m/s`}</title>
                <circle cx={x(point.usable_m)} cy={y(point.speed_mps)} r={selected ? 5.5 : 3.5} />
              </g>
            ))}
          </g>
        );
      })}
      <text x={left} y={421} className="wb-mass-small">
        Lines connect recorded samples for reading; they are not newly solved trajectories. Tiny
        positive results are not useful margin.
      </text>
    </g>
  );
}

function RailSchematic({ document: doc }: { document: WorkbenchDocument }) {
  const launch = doc.launch;
  const x = (length: number) =>
    72 +
    (length / Math.max(launch.illustrative_overall_mm, launch.illustrative_usable_mm, 1)) * 920;
  return (
    <g>
      <title>Illustrative overall guide versus usable travel · no longer baseline adopted</title>
      <text x={72} y={30} className="wb-mass-kicker">
        ILLUSTRATIVE GUIDE · EQUIPMENT / START / RELEASE GEOMETRY UNCONFIRMED
      </text>
      <text x={72} y={66}>
        Overall guide: {n(launch.illustrative_overall_mm)} mm (illustrative)
      </text>
      <rect
        className="wb-mass-rail"
        x={72}
        y={81}
        width={x(launch.illustrative_overall_mm) - 72}
        height={13}
        rx={3}
      />
      <path
        className="wb-mass-reference"
        d={`M72,74v28M${x(launch.illustrative_overall_mm)},74v28`}
      />
      <text x={72} y={135}>
        Usable travel: {n(launch.illustrative_usable_mm)} mm (separate reference length)
      </text>
      <path className="wb-mass-usable" d={`M72,155H${x(launch.illustrative_usable_mm)}`} />
      <path
        className="wb-mass-usable"
        d={`M72,148v14M${x(launch.illustrative_usable_mm)},148v14`}
      />
      <text x={72} y={198} className="wb-mass-small">
        Assumed pad offset: {n(launch.assumed_pad_offset_mm)} mm · guide element length:{' '}
        {n(launch.guide_length_mm)} mm
      </text>
      <text x={72} y={225} className="wb-mass-small">
        Upper / lower guide fronts: {n(launch.upper_guide_front_mm)} /{' '}
        {n(launch.lower_guide_front_mm)} mm from nose
      </text>
      <text x={72} y={252} className="wb-mass-small">
        Rows compare lengths only. Their shared origin is illustrative; no start/release alignment
        or support is asserted.
      </text>
      <text x={72} y={284} className="wb-mass-warning">
        Resolved usable-guide baseline stays {n(launch.baseline_usable_m)} m. Actual equipment:{' '}
        {launch.equipment_confirmed ? 'see recorded confirmation scope' : 'unconfirmed'}.
      </text>
    </g>
  );
}

export function MassLaunchViews({ document: doc, selectedPartId, onSelectPart }: Props) {
  const headingId = useId();
  const caseSelectId = useId();
  const [caseId, setCaseId] = useState<string | null>(null);
  const [burnout, setBurnout] = useState(false);
  const activeCase = doc.cases.find((item) => item.id === caseId) ?? doc.cases[0];
  const massRef = useRef<SVGSVGElement>(null);
  const groupRef = useRef<SVGSVGElement>(null);
  const revisionRef = useRef<SVGSVGElement>(null);
  const guideRef = useRef<SVGSVGElement>(null);
  const railRef = useRef<SVGSVGElement>(null);
  const selection = { selectedPartId, onSelectPart };
  const revisionRows = (doc.revision_mass_changes ?? []).filter((row) => row.revision === 'R1');
  if (!activeCase)
    return (
      <section className="wb-mass-launch">
        <h2>Mass, balance & launch guide</h2>
        <p>No compatible recorded cases are available. No values are inferred.</p>
      </section>
    );
  const cg = burnout ? activeCase.burnout_cg_mm : activeCase.cg_mm;
  const margin = burnout ? activeCase.burnout_margin_cal : activeCase.loaded_margin_cal;
  return (
    <section className="wb-mass-launch" aria-labelledby={headingId}>
      <div className="wb-mass-intro">
        <div>
          <p className="wb-mass-eyebrow">Mass, balance & launch guide</p>
          <h2 id={headingId}>One recorded package. Separate comparison cases.</h2>
        </div>
        <span className="wb-mass-status">
          Preliminary screens · all engineering gates remain open
        </span>
      </div>
      <p className="wb-mass-explanation">
        Explore the supplied ledger and recorded case results. C1 is the selected preliminary
        direction; R1 is a stopped reinforcement comparison. Mass/static results do not establish
        construction, thermal, fin/flutter, exact-motor or launch acceptance.
      </p>
      <div className="wb-mass-controls">
        <label htmlFor={caseSelectId}>
          Recorded case
          <select
            id={caseSelectId}
            value={activeCase.id}
            onChange={(event) => setCaseId(event.target.value)}
          >
            {doc.cases.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label} · {item.state}
              </option>
            ))}
          </select>
        </label>
        <div role="group" aria-label="Balance state">
          <button type="button" aria-pressed={!burnout} onClick={() => setBurnout(false)}>
            Loaded
          </button>
          <button type="button" aria-pressed={burnout} onClick={() => setBurnout(true)}>
            Burnout
          </button>
        </div>
      </div>
      <div className="wb-mass-metrics" aria-live="polite">
        <div>
          <span>Recorded loaded total</span>
          <strong>
            {n(activeCase.total_g)} <small>g</small>
          </strong>
        </div>
        <div>
          <span>{burnout ? 'Burnout' : 'Loaded'} CG</span>
          <strong>
            {n(cg)} <small>mm</small>
          </strong>
        </div>
        <div>
          <span>{burnout ? 'Burnout' : 'Loaded'} static margin</span>
          <strong>
            {n(margin, 6)} <small>cal</small>
          </strong>
        </div>
        <div>
          <span>Severe recovery mean screen</span>
          <strong>
            {n(activeCase.recovery_force_n)} <small>N</small>
          </strong>
        </div>
      </div>
      <p className="wb-mass-plain">
        A calibre (cal) is one body diameter. Static margin is a recorded balance/aerodynamic
        screen. The recovery value is a scalar energy-equivalent mean demand, not a measured peak or
        a spatial stress field.
      </p>
      <div className="wb-mass-balance">
        <Balance document={doc} activeCase={activeCase} burnout={burnout} />
      </div>
      <div className="wb-mass-budget-parts">
        <span>
          Nominal subtotal <strong>{n(activeCase.nominal_g)} g</strong>
        </span>
        <span>
          Separate growth allowance <strong>{n(activeCase.growth_g)} g</strong>
        </span>
        <span>
          Additional aft probe <strong>{n(activeCase.extra_aft_g)} g</strong>
        </span>
        <span>
          Recorded addition vs C1 <strong>{n(activeCase.added_mass_g)} g</strong>
        </span>
      </div>
      <p className="wb-mass-plain">
        The nominal subtotal is supplied by the recorded case and may already include its additional
        aft probe. These are reported accounting fields; the browser does not sum them. The full
        separate growth allowance stays counted once.
      </p>
      {activeCase.findings.length > 0 && (
        <ul className="wb-mass-findings">
          {activeCase.findings.map((finding) => (
            <li key={finding}>{finding}</li>
          ))}
        </ul>
      )}
      <div className="wb-mass-table-wrap">
        <table>
          <caption>
            Recorded complete-case comparison · selected C1 and stopped R1 remain separate
            identities
          </caption>
          <thead>
            <tr>
              <th scope="col">Case</th>
              <th scope="col">Nominal (g)</th>
              <th scope="col">Separate growth (g)</th>
              <th scope="col">Extra aft probe (g)</th>
              <th scope="col">Loaded total (g)</th>
              <th scope="col">Loaded / burnout margin (cal)</th>
              <th scope="col">Formal headroom (g)</th>
              <th scope="col">Planning headroom (g)</th>
            </tr>
          </thead>
          <tbody>
            {doc.cases.map((item, index) => (
              <tr key={item.id} className={item.id === activeCase.id ? 'is-active' : ''}>
                <th scope="row">
                  <button type="button" onClick={() => setCaseId(item.id)}>
                    <i style={{ background: COLORS[index % COLORS.length] }} />
                    {item.label}
                  </button>
                  <span>{item.state}</span>
                </th>
                <td>{n(item.nominal_g)}</td>
                <td>{n(item.growth_g)}</td>
                <td>{n(item.extra_aft_g)}</td>
                <td>{n(item.total_g)}</td>
                <td>
                  {n(item.loaded_margin_cal, 6)} / {n(item.burnout_margin_cal, 6)}
                </td>
                <td>{n(item.formal_headroom_g, 6)}</td>
                <td>{n(item.planning_headroom_g, 6)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="wb-mass-plain">
        Headroom is conditional on the recorded illustrative guide case and its assumptions. It is
        not a universal vehicle mass limit. Rounding never clears a failed criterion.
      </p>
      <Figure
        title="C1 source ledger · mass by station"
        note="This distribution is the frozen C1 source ledger, independent of the comparison-case selector. Source rows remain individual; extra R1 allocations are not invented into this plot."
        document={doc}
        svgRef={massRef}
      >
        <svg
          ref={massRef}
          viewBox="0 0 1100 390"
          role="img"
          aria-label="Recorded C1 mass distribution"
        >
          <MassDistribution document={doc} {...selection} />
        </svg>
      </Figure>
      <details className="wb-mass-ledger">
        <summary>Ledger key · select a recorded part</summary>
        <div>
          {doc.mass_distribution.map((entry) => (
            <button
              type="button"
              key={entry.id}
              disabled={!entry.part_id}
              aria-pressed={Boolean(entry.part_id && selectedPartId === entry.part_id)}
              onClick={() => entry.part_id && onSelectPart(entry.part_id)}
            >
              <span>{entry.label}</span>
              <strong>
                {n(entry.mass_g)} g · {n(entry.station_mm)} mm
              </strong>
              <small>
                {entry.state}
                {entry.part_id ? '' : ' · allowance; no physical part'}
              </small>
            </button>
          ))}
        </div>
      </details>
      <Figure
        title="C1 recorded mass groups"
        note="Bars use backend-provided group masses. Selecting a group activates its first associated part; all parts remain individually available in the ledger key."
        document={doc}
        svgRef={groupRef}
      >
        <svg
          ref={groupRef}
          viewBox={`0 0 1100 ${Math.max(150, 65 + doc.mass_groups.length * 53)}`}
          role="img"
          aria-label="Recorded C1 group masses"
        >
          <GroupBars document={doc} {...selection} />
        </svg>
      </Figure>
      {revisionRows.length > 0 ? (
        <Figure
          title="R1 mass-addition ledger"
          note="These per-item additions belong to the stopped R1 reinforcement comparison, not the active C1 distribution. Bar lengths and axial allocation stations come directly from the saved R1 ledger. Selecting a mapped row highlights its associated source component; it does not provide detailed R1 geometry."
          document={doc}
          svgRef={revisionRef}
        >
          <svg
            ref={revisionRef}
            viewBox={`0 0 1100 ${165 + revisionRows.length * 62}`}
            role="img"
            aria-label="R1 estimated mass additions by component and axial station, stopped comparison only"
          >
            <RevisionMassBars document={doc} {...selection} />
          </svg>
        </Figure>
      ) : (
        <p className="wb-mass-plain">
          Per-item R1 mass additions are unavailable in this document. The C1 source distribution
          remains separate.
        </p>
      )}
      <Figure
        title="Recorded usable-guide departure comparison"
        note={`The ${n(doc.launch.baseline_usable_m)} m baseline remains unchanged. Formal ${n(doc.launch.formal_mps)} m/s and separate ${n(doc.launch.planning_mps)} m/s planning targets remain distinct. Actual launch hardware and usable travel are unconfirmed unless explicitly recorded below.`}
        document={doc}
        svgRef={guideRef}
      >
        <svg
          ref={guideRef}
          viewBox="0 0 1100 445"
          role="img"
          aria-label="Recorded guide-speed comparison"
        >
          <GuideChart document={doc} activeCase={activeCase} onSelectCase={setCaseId} />
        </svg>
      </Figure>
      <div className="wb-mass-case-legend">
        {doc.cases.map((item, index) => (
          <button
            type="button"
            key={item.id}
            aria-pressed={item.id === activeCase.id}
            onClick={() => setCaseId(item.id)}
          >
            <i style={{ background: COLORS[index % COLORS.length] }} />
            {item.label}
          </button>
        ))}
      </div>
      <div className="wb-mass-table-wrap">
        <table>
          <caption>{activeCase.label} · exact recorded guide samples</caption>
          <thead>
            <tr>
              <th>Usable travel (m)</th>
              <th>Departure (m/s)</th>
              <th>Formal margin (m/s)</th>
              <th>Planning margin (m/s)</th>
            </tr>
          </thead>
          <tbody>
            {activeCase.guide_results.map((point) => (
              <tr key={point.usable_m}>
                <td>{n(point.usable_m)}</td>
                <td>{n(point.speed_mps, 9)}</td>
                <td>{n(point.formal_margin_mps, 9)}</td>
                <td>{n(point.planning_margin_mps, 9)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Figure
        title="Overall guide length versus usable travel"
        note="The illustration compares recorded lengths. It does not confirm an installation, usable release travel, rod-lug conversion, support, site, event date or flight acceptance."
        document={doc}
        svgRef={railRef}
      >
        <svg
          ref={railRef}
          viewBox="0 0 1100 310"
          role="img"
          aria-label="Illustrative overall and usable guide lengths"
        >
          <RailSchematic document={doc} />
        </svg>
      </Figure>
      <div className="wb-mass-hardware">
        <h3>Hardware and model conditions</h3>
        <p>{doc.launch.hardware_status}</p>
        <p>
          <strong>Equipment confirmation:</strong>{' '}
          {doc.launch.equipment_confirmed
            ? 'Recorded; inspect the exact source and scope'
            : 'Unconfirmed. No longer launch baseline is adopted.'}
        </p>
        <ul>
          {doc.launch.assumptions.map((assumption) => (
            <li key={assumption}>{assumption}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
