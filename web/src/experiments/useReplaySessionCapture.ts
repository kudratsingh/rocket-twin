import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import type { RefObject } from 'react';
import { browserHeap } from './playbackMode';
import { createPlaybackSessionCapture } from './playbackSessionCapture';
import type { PlaybackSessionContext, PlaybackFrameObservation } from './playbackSessionCapture';

type StableContext = Omit<PlaybackSessionContext, 'firstObservedCursorS' | 'startedWallMs'>;
type HeapObservation = ReturnType<typeof browserHeap>;
export type ReplaySessionObservationSnapshot = ReturnType<
  ReturnType<typeof createPlaybackSessionCapture>['snapshot']
> & {
  host_javascript_heap: { initial: HeapObservation; final: HeapObservation; scope: string };
};
export type SessionObservationEnvironment = {
  document: Pick<
    Document,
    'visibilityState' | 'hasFocus' | 'addEventListener' | 'removeEventListener'
  >;
  window: Pick<Window, 'addEventListener' | 'removeEventListener'>;
  IntersectionObserver?: typeof IntersectionObserver;
  ResizeObserver?: typeof ResizeObserver;
  now: () => number | null;
  readHeap?: () => HeapObservation;
};

export type MeasuredReplayCanvas = {
  contextKey: string;
  canvas: HTMLCanvasElement;
  ratio: number | null;
};

/** Warm actual IO evidence while paused; replacing the canvas invalidates the old measurement. */
export function warmReplayCanvas(
  contextKey: string,
  host: Pick<HTMLDivElement, 'querySelector'>,
  environment: Pick<SessionObservationEnvironment, 'IntersectionObserver'> & {
    MutationObserver?: typeof MutationObserver;
  },
  measured: (value: MeasuredReplayCanvas | null) => void,
) {
  let canvas: HTMLCanvasElement | null = null;
  let stopped = false;
  let observer: IntersectionObserver | null = null;
  const attach = () => {
    const next = host.querySelector('canvas');
    if (next === canvas) return;
    observer?.disconnect();
    canvas = next;
    measured(null);
    if (!canvas || !environment.IntersectionObserver) return;
    const observedCanvas = canvas;
    observer = new environment.IntersectionObserver(
      (entries) => {
        if (stopped || canvas !== observedCanvas) return;
        const entry = entries.find((item) => item.target === observedCanvas);
        if (!entry) return;
        const ratio = entry.intersectionRatio;
        measured({
          contextKey,
          canvas: observedCanvas,
          ratio: Number.isFinite(ratio) && ratio >= 0 && ratio <= 1 ? ratio : null,
        });
      },
      { threshold: [0, 0.25, 0.5, 0.75, 1] },
    );
    observer.observe(canvas);
  };
  attach();
  const mutations = environment.MutationObserver ? new environment.MutationObserver(attach) : null;
  mutations?.observe(host as HTMLDivElement, { childList: true, subtree: true });
  return () => {
    stopped = true;
    observer?.disconnect();
    mutations?.disconnect();
    measured(null);
  };
}

/** Browser adapters only; no animation scheduling, geometry reads or clock writes. */
export function beginReplaySessionObservation(
  context: StableContext,
  readCursor: () => number | null,
  canvas: HTMLCanvasElement | null,
  environment: SessionObservationEnvironment,
  warm: MeasuredReplayCanvas | null = null,
) {
  const readHeap = (): HeapObservation => {
    try {
      const value = environment.readHeap?.();
      return value ? { ...value } : null;
    } catch {
      return null;
    }
  };
  const initialHeap = readHeap();
  let finalHeap: HeapObservation = null;
  const capture = createPlaybackSessionCapture({
    ...context,
    firstObservedCursorS: readCursor(),
    startedWallMs: environment.now(),
  });
  let intersection: number | null =
    warm?.contextKey === JSON.stringify(context) &&
    warm.canvas === canvas &&
    typeof warm.ratio === 'number' &&
    Number.isFinite(warm.ratio) &&
    warm.ratio >= 0 &&
    warm.ratio <= 1
      ? warm.ratio
      : null;
  let endedWallMs: number | null = null;
  let stopped = false;
  let lastCursor: number | null = null;
  const state = (): Omit<PlaybackFrameObservation, 'deltaMs'> => {
    let focused: boolean | null = null;
    try {
      focused = environment.document.hasFocus();
    } catch {
      // Unsupported or inaccessible state stays unknown.
    }
    const visibility = environment.document.visibilityState;
    return {
      observedCursorS: readCursor(),
      documentVisibility: visibility === 'visible' || visibility === 'hidden' ? visibility : null,
      windowFocused: focused,
      canvasIntersectionFraction: intersection,
    };
  };
  const event = (kind: 'visibility' | 'focus' | 'resize' | 'intersection') => {
    if (!stopped) capture.observeEvent({ kind, ...state() });
  };
  const visibility = () => event('visibility');
  const focus = () => event('focus');
  const resize = () => event('resize');
  environment.document.addEventListener('visibilitychange', visibility);
  environment.window.addEventListener('focus', focus);
  environment.window.addEventListener('blur', focus);
  environment.window.addEventListener('resize', resize);
  const observer =
    canvas && environment.IntersectionObserver
      ? new environment.IntersectionObserver(
          (entries) => {
            if (stopped) return;
            const entry = entries.find((item) => item.target === canvas);
            if (!entry) return;
            intersection = Number.isFinite(entry.intersectionRatio)
              ? entry.intersectionRatio
              : null;
            event('intersection');
          },
          { threshold: [0, 0.25, 0.5, 0.75, 1] },
        )
      : null;
  if (canvas) observer?.observe(canvas);
  let lastSize: { width: number; height: number } | null = null;
  const resizeObserver =
    canvas && environment.ResizeObserver
      ? new environment.ResizeObserver((entries) => {
          if (stopped) return;
          const entry = entries.find((item) => item.target === canvas);
          if (!entry) return;
          const { width, height } = entry.contentRect;
          if (!Number.isFinite(width) || !Number.isFinite(height)) return;
          if (lastSize && (width !== lastSize.width || height !== lastSize.height)) resize();
          lastSize = { width, height };
        })
      : null;
  if (canvas) resizeObserver?.observe(canvas);
  return {
    observe(deltaMs: number) {
      if (!stopped) capture.appendFrame({ deltaMs, ...state() });
    },
    snapshot(): ReplaySessionObservationSnapshot {
      return {
        ...capture.snapshot({
          lastObservedCursorS: stopped ? lastCursor : readCursor(),
          endedWallMs,
        }),
        host_javascript_heap: {
          initial: initialHeap ? { ...initialHeap } : null,
          final: finalHeap ? { ...finalHeap } : null,
          scope:
            'Host-reported JavaScript heap at observation start and stop only; unsupported is null. Not total process or GPU memory, and not automatic acceptance.',
        },
      };
    },
    stop() {
      if (stopped) return;
      stopped = true;
      lastCursor = readCursor();
      endedWallMs = environment.now();
      finalHeap = readHeap();
      observer?.disconnect();
      resizeObserver?.disconnect();
      environment.document.removeEventListener('visibilitychange', visibility);
      environment.window.removeEventListener('focus', focus);
      environment.window.removeEventListener('blur', focus);
      environment.window.removeEventListener('resize', resize);
    },
  };
}

/** Each Play/source/profile/speed epoch is separate; cursor commits never restart it. */
export function useReplaySessionCapture({
  playing,
  context,
  time,
  hostRef,
}: {
  playing: boolean;
  context: StableContext | null;
  time: number;
  hostRef: RefObject<HTMLDivElement | null>;
}) {
  const cursor = useRef<{ key: string | null; value: number | null }>({ key: null, value: null });
  const previousCursor = useRef(cursor.current);
  const current = useRef<ReturnType<typeof beginReplaySessionObservation> | null>(null);
  const retained = useRef<ReturnType<typeof beginReplaySessionObservation> | null>(null);
  const contextKey = JSON.stringify(context);
  const previousContextKey = useRef(contextKey);
  const measuredCanvas = useRef<MeasuredReplayCanvas | null>(null);
  const [readiness, setReadiness] = useState<{ key: string; ratio: number | null }>({
    key: '',
    ratio: null,
  });
  useLayoutEffect(() => {
    if (cursor.current.key !== contextKey) previousCursor.current = cursor.current;
    cursor.current = { key: contextKey, value: Number.isFinite(time) ? time : null };
  }, [time, contextKey]);
  useEffect(() => {
    measuredCanvas.current = null;
    const host = hostRef.current;
    if (contextKey === 'null' || !host) return;
    return warmReplayCanvas(
      contextKey,
      host,
      {
        IntersectionObserver:
          typeof IntersectionObserver === 'undefined' ? undefined : IntersectionObserver,
        MutationObserver: typeof MutationObserver === 'undefined' ? undefined : MutationObserver,
      },
      (value) => {
        measuredCanvas.current = value;
        setReadiness({ key: contextKey, ratio: value?.ratio ?? null });
      },
    );
  }, [contextKey, hostRef]);
  useEffect(() => {
    if (previousContextKey.current !== contextKey) retained.current = null;
    previousContextKey.current = contextKey;
    if (!playing || contextKey === 'null') return;
    const observation = beginReplaySessionObservation(
      JSON.parse(contextKey) as StableContext,
      () =>
        cursor.current.key === contextKey
          ? cursor.current.value
          : previousCursor.current.key === contextKey
            ? previousCursor.current.value
            : null,
      hostRef.current?.querySelector('canvas') ?? null,
      {
        document,
        window,
        IntersectionObserver:
          typeof IntersectionObserver === 'undefined' ? undefined : IntersectionObserver,
        ResizeObserver: typeof ResizeObserver === 'undefined' ? undefined : ResizeObserver,
        now: () => (typeof performance === 'undefined' ? null : performance.now()),
        readHeap: () => browserHeap(typeof performance === 'undefined' ? null : performance),
      },
      measuredCanvas.current,
    );
    current.current = observation;
    retained.current = null;
    return () => {
      observation.stop();
      retained.current = observation;
      if (current.current === observation) current.current = null;
    };
  }, [playing, contextKey, hostRef]);
  const observe = useCallback((deltaMs: number) => current.current?.observe(deltaMs), []);
  const snapshot = useCallback(
    () => current.current?.snapshot() ?? retained.current?.snapshot() ?? null,
    [],
  );
  return {
    observe,
    snapshot,
    canvasReadiness: readiness.key === contextKey ? readiness.ratio : null,
  };
}
