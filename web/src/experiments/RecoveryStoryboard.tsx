import { useId } from 'react';
import type { ReplayValidityRecord } from './replayValidity';
import type { ReplayWindow } from './replayWindow';
import { recoveryStoryboard } from './recoverySequenceState';

/** An event-linked explanatory graphic; never modifies the recorded 3D body pose. */
export function RecoveryStoryboard({
  record,
  time,
  window,
}: {
  record: ReplayValidityRecord;
  time: number;
  window: ReplayWindow;
}) {
  const state = recoveryStoryboard(record, time, window);
  const id = useId();
  const colour = state.reached ? '#6ed5c7' : '#8798a8';
  const fmt = (value: number | null) => (value === null ? 'Unavailable' : `${value.toFixed(3)} s`);
  return (
    <details className="recovery-storyboard">
      <summary>Recovery sequence · schematic explanation</summary>
      <p role="status">{state.status}</p>
      <div style={{ overflowX: 'auto' }} tabIndex={0} aria-label="Scrollable recovery schematic">
        <svg
          viewBox="0 0 900 310"
          role="img"
          aria-labelledby={`${id}-title ${id}-description`}
          style={{ width: '100%', minWidth: 760, background: '#11212b' }}
        >
          <title id={`${id}-title`}>Event-linked recovery storyboard — not a flight pose</title>
          <desc id={`${id}-description`}>
            Three non-spatial panels link a saved deployment marker to the point-drag recovery model
            and explicitly unavailable physical canopy, harness and separated-section behavior. The
            replay uses the recorded body attitude unchanged.
          </desc>
          <metadata>
            {JSON.stringify({
              run_id: record.run_id,
              configuration: record.configuration,
              simulation_code_sha256: record.code_sha256 ?? null,
              resolved_sha256: record.resolved_sha256 ?? null,
              units: 'seconds',
              frame: 'non-spatial diagram; not vehicle/world coordinates',
              evidence: 'event-derived schematic; no measured canopy geometry',
              requested_time_s: Number.isFinite(time) ? time : null,
              events: {
                apogee: state.apogee,
                deployment: state.deployment,
                landing: state.landing,
              },
            })}
          </metadata>
          {[20, 320, 620].map((x) => (
            <rect
              key={x}
              x={x}
              y="50"
              width="260"
              height="215"
              rx="8"
              fill="#182f3b"
              stroke="#63818d"
            />
          ))}
          <g fill="#e8f1f3" fontSize="18" fontFamily="sans-serif">
            <text x="25" y="28">
              Schematic only · no spatial scale · event times in seconds
            </text>
            <text x="35" y="80">
              1 · Saved event marker
            </text>
            <text x="335" y="80">
              2 · Current model
            </text>
            <text x="635" y="80">
              3 · Real mechanism
            </text>
          </g>
          <g fill="#b8cdd5" fontSize="15" fontFamily="sans-serif">
            <text x="35" y="112">
              Apogee: {fmt(state.apogee)}
            </text>
            <text x="35" y="139">
              Deployment: {fmt(state.deployment)}
            </text>
            <text x="35" y="166">
              Landing: {fmt(state.landing)}
            </text>
            <text x="35" y="210">
              Deployment is a modeled
            </text>
            <text x="35" y="233">
              start, not canopy confirmation.
            </text>
            <text x="335" y="180">
              One recorded rigid body
            </text>
            <text x="335" y="207">
              Point drag / modeled inflation
            </text>
            <text x="335" y="234">
              Suspended attitude approximate
            </text>
            <text x="635" y="112">
              Canopy shape: unavailable
            </text>
            <text x="635" y="139">
              Line forces: unavailable
            </text>
            <text x="635" y="166">
              Section poses: unavailable
            </text>
            <text x="635" y="207">
              No simulated separation
            </text>
            <text x="635" y="234">
              or harness equilibrium shown.
            </text>
          </g>
          <path
            d="M288 153h23m-8-6 8 6-8 6M588 153h23m-8-6 8 6-8 6"
            fill="none"
            stroke="#afc8d2"
            strokeWidth="2"
          />
          {state.reached ? (
            <g data-recovery-symbol="event-derived" stroke={colour} fill="none" strokeWidth="2">
              <path d="M390 123a42 23 0 0 1 84 0Z" />
              <text x="488" y="126" fill={colour} stroke="none" fontSize="13">
                symbol only
              </text>
            </g>
          ) : (
            <text x="345" y="130" fill={colour} fontSize="14">
              No canopy symbol at this time
            </text>
          )}
          <text x="25" y="294" fill="#d6e5e9" fontSize="15" fontFamily="sans-serif">
            The 3D rocket keeps its saved orientation; this diagram does not rotate it to match
            descent.
          </text>
        </svg>
      </div>
      <p>{state.phaseSource} Arrows show an explanation sequence, not forces or positions.</p>
      <p>
        Run {record.run_id} · {record.configuration}. The symbol does not establish deployment
        success, canopy dimensions or an approved recovery system.
      </p>
    </details>
  );
}
