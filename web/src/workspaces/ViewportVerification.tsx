import { useEffect, useState } from 'react';

export type WindowObservation = { width: number; height: number; dpr: number };
const referenceSizes = [
  [1440, 900],
  [1280, 720],
  [900, 720],
] as const;

/** Read-only observation. It never changes Chrome, camera zoom or acceptance state. */
export function ViewportVerificationPanel({
  observation,
  onClose,
}: {
  observation: WindowObservation;
  onClose: () => void;
}) {
  return (
    <aside
      aria-label="Read-only browser size"
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
      <strong>Browser size · information only</strong>
      <p role="status">
        Current content area: {observation.width} × {observation.height} CSS px · device-pixel ratio{' '}
        {observation.dpr}.
      </p>
      <p>
        This panel measures the current size. It cannot resize Chrome or change page zoom. Use a
        comfortable window size; you do not need to match the references below to use Rocket Twin.
      </p>
      <details>
        <summary>Reference sizes for engineering-team layout checks</summary>
        <ul>
          {referenceSizes.map(([width, height]) => (
            <li key={width}>
              {width} × {height} CSS px
              {observation.width === width && observation.height === height
                ? ' — matches current dimensions; layout acceptance is still separate'
                : ''}
            </li>
          ))}
        </ul>
        <p>
          These are test references, not resize controls. Exact-size cases remain pending until
          checked. CSS pixels are not screenshot pixels. Device-pixel ratio does not by itself
          establish page zoom.
        </p>
      </details>
      <p>
        Chrome page zoom is in its upper-right three-dot menu. On Mac, ⌘0 resets page zoom to its
        default. Rocket Zoom in/out changes the 3D camera; macOS Window → Zoom changes window
        bounds.
      </p>
      <button type="button" onClick={onClose}>
        Hide size information
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
    <ViewportVerificationPanel observation={observation} onClose={() => setDismissed(true)} />
  );
}
