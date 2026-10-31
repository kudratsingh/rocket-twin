import { useEffect, useRef } from 'react';
import uPlot from 'uplot';
import { displayScalar, displayUnit } from './display';
import type { AnalysisField, AnalysisPayload } from './types';

export function HistoryPlot({
  field,
  payload,
  partId,
  sample,
  onSample,
}: {
  field: AnalysisField;
  payload: AnalysisPayload;
  partId: string;
  sample: number;
  onSample: (index: number) => void;
}) {
  const holder = useRef<HTMLDivElement>(null);
  const plotRef = useRef<uPlot | null>(null);
  const syncingCursor = useRef(false);
  const partIndex = field.part_ids.indexOf(partId);
  useEffect(() => {
    const element = holder.current;
    if (!element || !field.times_s || partIndex < 0 || field.association !== 'part') return;
    const times = field.times_s;
    const plot = new uPlot(
      {
        width: element.clientWidth,
        height: 150,
        padding: [10, 7, 0, 0],
        scales: { x: { time: false } },
        legend: { show: false },
        cursor: { drag: { x: false, y: false } },
        axes: [
          {
            stroke: '#6f91a1',
            font: '8px system-ui',
            size: 24,
            grid: { stroke: '#29414e', width: 0.5 },
            values: (_plot, values) => values.map((value) => `${value}s`),
          },
          {
            stroke: '#6f91a1',
            font: '8px system-ui',
            size: 35,
            grid: { stroke: '#29414e', width: 0.5 },
          },
        ],
        series: [
          { label: 'Recorded analysis time (s)' },
          { label: displayUnit[field.quantity], stroke: '#6bd3cb', width: 1.5 },
        ],
        hooks: {
          setCursor: [
            (instance) => {
              if (syncingCursor.current) return;
              const left = instance.cursor.left;
              if (left == null || left < 0) return;
              const time = instance.posToVal(left, 'x');
              const index = times.findIndex((value) => value >= time);
              if (index >= 0) onSample(index);
            },
          ],
        },
      },
      [
        times,
        payload.values.map((frame) =>
          frame[partIndex] == null ? null : displayScalar(frame[partIndex]!, field.quantity),
        ),
      ],
      element,
    );
    plotRef.current = plot;
    const observer = new ResizeObserver(() =>
      plot.setSize({ width: element.clientWidth, height: 150 }),
    );
    observer.observe(element);
    return () => {
      observer.disconnect();
      plot.destroy();
      plotRef.current = null;
    };
  }, [field, payload, partIndex, onSample]);
  useEffect(() => {
    const plot = plotRef.current;
    if (plot && field.times_s) {
      syncingCursor.current = true;
      plot.setCursor({ left: plot.valToPos(field.times_s[sample], 'x'), top: 0 });
      syncingCursor.current = false;
    }
  }, [field, sample]);
  if (!field.times_s || field.association !== 'part' || partIndex < 0) return null;
  return (
    <div className="analysis-history">
      <span>Part history · {displayUnit[field.quantity]}</span>
      <div ref={holder} />
      <small>
        Recorded samples; cursor selects the first solver sample at or after the pointer. No
        flight-time coupling is implied.
      </small>
    </div>
  );
}
