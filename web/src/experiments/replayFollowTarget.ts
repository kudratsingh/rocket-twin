import type { ReplayPose } from './replayPose';

export type ReplayCameraMode = 'follow' | 'follow-a' | 'follow-b' | 'pad' | 'free';
export type ReplayFollowTarget = {
  source: 'A' | 'B' | null;
  position: [number, number, number] | null;
  cameraMode: 'follow' | 'pad' | 'free';
  status: 'following' | 'held' | 'pad' | 'manual';
  label: string;
};

/** Select only an existing recorded world position; never change either actor's pose. */
export function replayFollowTarget(
  mode: ReplayCameraMode,
  a: ReplayPose | null,
  b: ReplayPose | null,
): ReplayFollowTarget {
  if (mode === 'pad' || mode === 'free')
    return {
      source: null,
      position: null,
      cameraMode: mode,
      status: mode === 'pad' ? 'pad' : 'manual',
      label:
        mode === 'pad'
          ? 'Camera: fixed pad · no run followed'
          : 'Camera: free orbit · no run followed',
    };
  const reason = (pose: ReplayPose | null) => {
    if (!pose) return 'run not loaded';
    if (pose.kind === 'unavailable') return pose.reason;
    if (
      (pose.kind !== 'pose' && pose.kind !== 'marker') ||
      !Array.isArray(pose.position) ||
      pose.position.length !== 3 ||
      ![0, 1, 2].every((index) => Number.isFinite(pose.position[index]))
    )
      return 'recorded position unavailable';
    return null;
  };
  const aReason = reason(a);
  const bReason = reason(b);
  const source =
    mode === 'follow-b'
      ? bReason === null
        ? 'B'
        : null
      : mode === 'follow-a'
        ? aReason === null
          ? 'A'
          : null
        : aReason === null
          ? 'A'
          : bReason === null
            ? 'B'
            : null;
  if (!source)
    return {
      source: null,
      position: null,
      cameraMode: 'follow',
      status: 'held',
      label: `Camera held · ${mode === 'follow-a' ? `A: ${aReason}` : mode === 'follow-b' ? `B: ${bReason}` : `A: ${aReason}; B: ${bReason}`}`,
    };
  const pose = source === 'A' ? a : b;
  // The source selection above admits only a finite position-bearing pose.
  if (!pose || pose.kind === 'unavailable') throw new Error('Invalid camera target selection');
  return {
    source,
    position: [pose.position[0], pose.position[1], pose.position[2]],
    cameraMode: 'follow',
    status: 'following',
    label: `Camera follows ${source}${pose.kind === 'marker' ? ' position marker' : ' recorded position'}${mode === 'follow' && source === 'B' ? ` · Auto fallback; A: ${aReason}` : mode === 'follow' ? ' · Auto' : ''} · view only`,
  };
}
