/** One-shot, source-keyed main-scene pose; never inferred from display angles. */
export type MainCameraPose = {
  position: [number, number, number];
  up: [number, number, number];
  target: [number, number, number];
  targetScope?: 'assembly' | 'selection';
  targetLabel?: string;
};
const captures = new Map<string, () => MainCameraPose>();
const snapshots = new Map<string, MainCameraPose>();
export function registerMainCamera(key: string, capture: () => MainCameraPose) {
  captures.set(key, capture);
  return () => {
    if (captures.get(key) === capture) captures.delete(key);
  };
}
export function captureMainCamera(key: string) {
  snapshots.delete(key);
  const value = captures.get(key)?.();
  if (value && [value.position, value.up, value.target].flat().every(Number.isFinite))
    snapshots.set(key, value);
}
export function consumeMainCamera(key: string) {
  const value = snapshots.get(key);
  snapshots.delete(key);
  return value;
}
export function clearMainCamera(key: string) {
  snapshots.delete(key);
}
export function mainCameraKey(id: string, specification: unknown) {
  return `${id}:${String(specification)}`;
}
/** Strict Mode effect replay is not a fresh user camera command. */
export function mainCameraCommand(previous: number | null, token: number, restored: boolean) {
  if (previous === token) return 'skip';
  return previous === null && restored ? 'restore' : 'frame';
}
