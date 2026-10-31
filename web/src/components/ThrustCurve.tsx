import { useEffect, useRef, useState } from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';
import { getJson } from '../api';

interface Curve {
  samples: [number, number][];
  source: string;
  provenance: string;
  sha256: string;
}

export function ThrustCurve({ motorId }: { motorId: string }) {
  const holder = useRef<HTMLDivElement>(null);
  const [curve, setCurve] = useState<Curve | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    void getJson<Curve>(`/api/motors/${encodeURIComponent(motorId)}/curve`, controller.signal)
      .then(setCurve)
      .catch((reason: unknown) => {
        if (!controller.signal.aborted)
          setError(reason instanceof Error ? reason.message : 'Source curve unavailable.');
      });
    return () => controller.abort();
  }, [motorId]);
  useEffect(() => {
    const element = holder.current;
    if (!element || !curve?.samples.length) return;
    const plot = new uPlot(
      {
        width: element.clientWidth,
        height: 130,
        padding: [8, 8, 0, 0],
        legend: { show: false },
        cursor: { drag: { x: false, y: false } },
        scales: { x: { time: false } },
        axes: [
          {
            stroke: '#698b9d',
            font: '8px system-ui',
            size: 22,
            grid: { stroke: '#29414e', width: 0.5 },
            ticks: { stroke: '#36505d', size: 3 },
            values: (_plot, values) => values.map((value) => `${value}s`),
          },
          {
            stroke: '#698b9d',
            font: '8px system-ui',
            size: 27,
            grid: { stroke: '#29414e', width: 0.5 },
            ticks: { stroke: '#36505d', size: 3 },
            values: (_plot, values) => values.map((value) => `${value}`),
          },
        ],
        series: [
          { label: 'Time (s)' },
          { label: 'Thrust (N)', stroke: '#6accc8', width: 1.5, fill: '#57c8c415' },
        ],
      },
      [curve.samples.map(([time]) => time), curve.samples.map(([, thrust]) => thrust)],
      element,
    );
    const observer = new ResizeObserver(() =>
      plot.setSize({ width: element.clientWidth, height: 130 }),
    );
    observer.observe(element);
    return () => {
      observer.disconnect();
      plot.destroy();
    };
  }, [curve]);
  return (
    <div className="thrust-curve">
      <div className="curve-label">
        <span>Source thrust curve</span>
        <small>Force (N) over time (s)</small>
      </div>
      <div ref={holder} />
      {error ? (
        <p className="small muted">Curve unavailable: {error}</p>
      ) : !curve ? (
        <p className="small muted">Loading source curve…</p>
      ) : (
        <p className="curve-source" title={`${curve.source} · SHA-256 ${curve.sha256}`}>
          {curve.provenance}. Source: {curve.source}
        </p>
      )}
    </div>
  );
}
