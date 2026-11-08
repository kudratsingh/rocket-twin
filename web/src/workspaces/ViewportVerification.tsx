import { useEffect, useState } from 'react';

export type WindowObservation = { width: number; height: number; dpr: number };
const targets = [
  [1440, 900],
  [1280, 720],
  [900, 720],
] as const;
/** Read-only measurement. Never resizes windows, changes zoom or invokes a developer protocol. */
export function ViewportVerificationPanel({
  observation,
  target,
  onTarget,
  onClose,
}: {
  observation: WindowObservation;
  target: number;
  onTarget: (value: number) => void;
  onClose: () => void;
}) {
  const expected = targets[target] ?? targets[0];
  const matches = observation.width === expected[0] && observation.height === expected[1];
  return (
    <aside
      aria-label="Manual viewport verification"
      style={{
        position: 'fixed',
        right: 10,
        bottom: 35,
        zIndex: 80,
        maxWidth: 'min(420px, calc(100vw - 20px))',
        padding: 12,
        background: '#11212bf5',
        color: '#e0edf2',
        border: '1px solid #68bdca',
        borderRadius: 6,
        fontSize: 13,
      }}
    >
      <strong>Manual browser-size verification</strong>
      <p role="status">
        Content area: {observation.width} × {observation.height} CSS px · device-pixel ratio{' '}
        {observation.dpr}.{' '}
        {matches
          ? 'Requested size matches.'
          : `Target ${expected[0]} × ${expected[1]} CSS px not reached.`}
      </p>
      <label>
        Requested size{' '}
        <select value={target} onChange={(event) => onTarget(Number(event.target.value))}>
          {targets.map(([width, height], index) => (
            <option key={width} value={index}>
              {width} × {height}
            </option>
          ))}
        </select>
      </label>
      <p>
        Resize this existing Chrome window manually. Keep browser zoom at100%. This panel only reads
        the content size; it does not resize anything or open developer tools. CSS pixels are not
        screenshot pixels.
      </p>
      <button type="button" onClick={onClose}>
        Hide measurement panel for inspection
      </button>
    </aside>
  );
}
export function ViewportVerification() {
  const [observation, setObservation] = useState<WindowObservation>(() => ({
    width: window.innerWidth,
    height: window.innerHeight,
    dpr: window.devicePixelRatio,
  }));
  const [target, setTarget] = useState(0);
  const [dismissed, setDismissed] = useState(false);
  useEffect(() => {
    const update = () =>
      setObservation({
        width: window.innerWidth,
        height: window.innerHeight,
        dpr: window.devicePixelRatio,
      });
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);
  return dismissed ? null : (
    <ViewportVerificationPanel
      observation={observation}
      target={target}
      onTarget={setTarget}
      onClose={() => setDismissed(true)}
    />
  );
}
