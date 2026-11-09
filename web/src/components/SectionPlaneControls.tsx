import type { SectionDimensions, SectionSettings } from './inspectionSection';

export function SectionPlaneControls({
  settings,
  dimensions,
  onChange,
}: {
  settings: SectionSettings;
  dimensions: SectionDimensions;
  onChange: (next: SectionSettings) => void;
}) {
  const radiusMm = dimensions.radiusM === null ? null : dimensions.radiusM * 1000;
  const lengthMm = dimensions.lengthM === null ? null : dimensions.lengthM * 1000;
  const update = (patch: Partial<SectionSettings>) => onChange({ ...settings, ...patch });
  return (
    <fieldset className="inspection-section-controls">
      <legend>Section cut · view only</legend>
      <p>
        Reveal existing modeled layers. A section hides one side; it does not add missing joint
        details or a solid cut face.
      </p>
      <label>
        Cut direction{' '}
        <select
          aria-label="Section cut direction"
          value={settings.mode}
          onChange={(e) => update({ mode: e.target.value as SectionSettings['mode'] })}
        >
          <option value="longitudinal">Along the rocket</option>
          <option value="transverse" disabled={lengthMm === null}>
            Across the rocket
          </option>
        </select>
      </label>
      {settings.mode === 'longitudinal' ? (
        <>
          <label>
            Rotate cut around rocket · {settings.angleDeg.toFixed(0)}°
            <input
              aria-label="Section rotation in degrees"
              type="range"
              min="0"
              max="360"
              step="1"
              value={settings.angleDeg}
              onChange={(e) => update({ angleDeg: Number(e.target.value) })}
            />
          </label>
          <div
            className="inspection-section-presets"
            role="group"
            aria-label="Section rotation presets"
          >
            {[0, 90, 150].map((angle) => (
              <button
                type="button"
                key={angle}
                aria-pressed={settings.angleDeg === angle}
                onClick={() => update({ angleDeg: angle })}
              >
                {angle}°
              </button>
            ))}
          </div>
          <label>
            Move cut sideways · {settings.offsetMm.toFixed(1)} mm
            <input
              aria-label="Section radial offset in millimetres"
              type="range"
              min={-(radiusMm ?? 0)}
              max={radiusMm ?? 0}
              step="0.1"
              disabled={radiusMm === null}
              value={settings.offsetMm}
              onChange={(e) => update({ offsetMm: Number(e.target.value) })}
            />
          </label>
          {radiusMm === null && (
            <p>Radial range unavailable: this source has no recorded body diameter.</p>
          )}
          <p>
            0° cuts the viewer X=0 plane; 90° cuts Z=0. The angle rotates the plane normal around
            the rocket’s Y axis. Sideways distance is from the centerline.
          </p>
        </>
      ) : (
        <>
          <label>
            Station aft from nose · {settings.stationMm.toFixed(1)} mm
            <input
              aria-label="Section station aft from nose in millimetres"
              type="range"
              min="0"
              max={lengthMm ?? 0}
              step="0.1"
              value={settings.stationMm}
              onChange={(e) => update({ stationMm: Number(e.target.value) })}
            />
          </label>
          <label>
            Exact station (mm)
            <input
              aria-label="Exact section station in millimetres"
              type="number"
              min="0"
              max={lengthMm ?? 0}
              step="0.1"
              value={Number(settings.stationMm.toFixed(1))}
              onChange={(e) => {
                if (e.target.value === '') return;
                const value = Number(e.target.value);
                if (Number.isFinite(value) && value >= 0 && lengthMm !== null && value <= lengthMm)
                  update({ stationMm: value });
              }}
            />
          </label>
          <p>
            Station 0 is the recorded nose tip. Larger numbers move toward the motor. Viewer Y =
            source length − station, in metres.
          </p>
        </>
      )}
      <label>
        <input
          type="checkbox"
          checked={settings.flipped}
          onChange={(e) => update({ flipped: e.target.checked })}
        />
        Show the opposite side of the cut
      </label>
      <button
        type="button"
        onClick={() =>
          onChange({ mode: 'longitudinal', angleDeg: 0, offsetMm: 0, stationMm: 0, flipped: false })
        }
      >
        Reset cut to centerline
      </button>
      <p>
        Millimetres (mm) are one thousandth of a metre. Display only: part mass, source geometry and
        engineering results do not change. Fit still uses conservative full-part bounds.
      </p>
    </fieldset>
  );
}
