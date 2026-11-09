import { useState } from 'react';
import type { RefObject } from 'react';
import { orbitBasis } from './inspectionOrbit';
import type { OrbitAngles, OrbitReadout } from './inspectionOrbit';

export function OrbitCameraControls({
  readout,
  dragMode = 'orbit',
  canTargetSelection,
  selectionLabel = 'Selected group / part',
  onAngles,
  onTarget,
  onPan,
  detailsRef,
}: {
  readout: OrbitReadout;
  dragMode?: 'orbit' | 'pan';
  canTargetSelection: boolean;
  selectionLabel?: string;
  onAngles: (angles: OrbitAngles) => void;
  onTarget: (target: 'assembly' | 'selection') => void;
  onPan: (direction: 'left' | 'right' | 'up' | 'down') => void;
  detailsRef?: RefObject<HTMLDetailsElement | null>;
}) {
  const [draft, setDraft] = useState<Record<keyof OrbitAngles, string> | null>(null);
  const [error, setError] = useState('');
  return (
    <div className="inspection-orbit-controls">
      <details
        ref={detailsRef}
        onKeyDown={(event) => {
          if (event.key !== 'Escape') return;
          event.preventDefault();
          event.stopPropagation();
          event.currentTarget.open = false;
          event.currentTarget.querySelector('summary')?.focus();
        }}
      >
        <summary>Orbit / camera · {readout.mode}</summary>
        <form
          noValidate
          onSubmit={(event) => {
            event.preventDefault();
            try {
              const angles = draft
                ? {
                    azimuth: Number(draft.azimuth),
                    tilt: Number(draft.tilt),
                    roll: Number(draft.roll),
                  }
                : readout;
              if (draft && Object.values(draft).some((value) => !value.trim()))
                throw new RangeError('Enter all three camera angles in degrees.');
              orbitBasis(angles);
              onAngles(angles);
              setDraft(null);
              setError('');
            } catch (reason) {
              setError(String(reason));
            }
          }}
        >
          <p>
            CAD +Y points to the nose. Horizontal 0° views from +Z; +90° views from +X. Tilt 0°
            looks from the nose, 180° from the motor end. At either pole, horizontal angle defines
            the up reference. Roll turns about the target-to-camera axis.
          </p>
          {(
            [
              ['azimuth', 'Horizontal angle (°)'],
              ['tilt', 'Nose-to-aft tilt (°)'],
              ['roll', 'View roll (°)'],
            ] as const
          ).map(([key, label]) => (
            <label key={key}>
              {label}
              <input
                type="number"
                step="any"
                value={draft?.[key] ?? readout[key].toFixed(2)}
                onChange={(event) => {
                  setDraft((previous) => ({
                    ...{
                      azimuth: String(readout.azimuth),
                      tilt: String(readout.tilt),
                      roll: String(readout.roll),
                    },
                    ...previous,
                    [key]: event.target.value,
                  }));
                  setError('');
                }}
              />
            </label>
          ))}
          <button type="submit">Apply camera angles</button>
          <button
            type="button"
            onClick={() => {
              setDraft(null);
              setError('');
            }}
          >
            Use actual angles
          </button>
          <label>
            Orbit target
            <select
              value={readout.target}
              onChange={(event) => onTarget(event.target.value as 'assembly' | 'selection')}
            >
              <option value="assembly">Assembly</option>
              <option value="selection" disabled={!canTargetSelection}>
                {selectionLabel}
              </option>
            </select>
          </label>
          <div aria-label="Keyboard pan controls">
            {(['left', 'right', 'up', 'down'] as const).map((direction) => (
              <button type="button" key={direction} onClick={() => onPan(direction)}>
                Pan {direction}
              </button>
            ))}
          </div>
          <p>
            Panning moves the pivot in the viewing plane. Choose an orbit target again to recenter
            it without changing angle or distance. Fit assembly and Frame selection retain angles;
            Reset camera returns to Overview.
          </p>
          {error && <p role="alert">{error}</p>}
        </form>
      </details>
      <output aria-label="Actual camera angles">
        Horizontal {readout.azimuth.toFixed(1)}° · Tilt {readout.tilt.toFixed(1)}° · Roll{' '}
        {readout.roll.toFixed(1)}° · Target:{' '}
        {readout.targetLabel ?? (readout.target === 'assembly' ? 'Assembly' : selectionLabel)}
      </output>
      <span className="inspection-gesture-hint">
        {dragMode === 'pan'
          ? 'Drag to move the rocket across the screen'
          : 'Drag to rotate around the rocket'}{' '}
        · Mouse wheel/trackpad scroll or pinch to zoom · Right/middle/Shift-drag always moves the
        view · Alt-drag to roll. Click a part to select. Whole rocket returns to the full overview.
      </span>
    </div>
  );
}
