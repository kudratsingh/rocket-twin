/** A request is a complete archived configuration; no RP1/archive substitution. */
export const eligibleConfigurations = [
  'modular-performance-v1',
  'modular-performance-g54-hypothesis',
  'modular-tvc-finned-v1',
];
export type ExperimentRequest = {
  configuration: string;
  wind_mps: number;
  wind_direction_deg: number;
  gust_mps: number;
  preset: 'tiny' | 'sim';
  seed: number;
};
export const terminalStatuses = ['complete', 'failed', 'cancelled', 'interrupted'];
export function requestDraft(record: Record<string, unknown>, active: string): ExperimentRequest {
  if (
    !eligibleConfigurations.includes(active) ||
    record.configuration !== active ||
    record.controller !== 'locked, unguided'
  )
    throw new Error(
      'Select the same eligible complete configuration before reusing a recorded request.',
    );
  const s = record.settings as Partial<ExperimentRequest> | undefined;
  if (
    !s ||
    s.configuration !== active ||
    Object.keys(s).some(
      (key) =>
        !['configuration', 'wind_mps', 'wind_direction_deg', 'gust_mps', 'preset', 'seed'].includes(
          key,
        ),
    )
  )
    throw new Error('The saved request is unavailable or contains unsupported overrides.');
  const bounded = (v: unknown, low: number, high: number) =>
    typeof v === 'number' && Number.isFinite(v) && v >= low && v <= high;
  const seed = s.seed;
  if (
    !bounded(s.wind_mps, 0, 10) ||
    !bounded(s.wind_direction_deg, 0, 359.999999) ||
    !bounded(s.gust_mps, 0, 5) ||
    !['tiny', 'sim'].includes(s.preset ?? '') ||
    !Number.isInteger(seed) ||
    !bounded(seed, 0, 4294967295)
  )
    throw new Error('The saved request has unsupported ranges, seed or preset.');
  return { ...s, seed } as ExperimentRequest;
}
export function batchDeclaration(cases: readonly ExperimentRequest[]) {
  if (cases.length < 2 || cases.length > 4) throw new Error('Declare between two and four cases.');
  return {
    count: cases.length,
    concurrency: 1,
    resource: 'local-cpu',
    max_steps: cases.reduce((sum, c) => sum + (c.preset === 'tiny' ? 9000 : 360000), 0),
    cases: cases.map((c, index) => ({ member: index + 1, ...c })),
    cancellation:
      'Cooperative at model boundaries; current compiled JAX rollout can finish before acknowledgement.',
  };
}
