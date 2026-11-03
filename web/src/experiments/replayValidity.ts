/** Interpretation of legacy experiment records, not new telemetry or a physics model. */
export type ReplayValidityRecord = {
  run_id: string;
  configuration: string;
  controller?: string;
  code_sha256?: string;
  resolved_sha256?: string;
  events?: Record<string, number | null>;
  trajectory_complete?: boolean;
};

const events = ['ignition', 'guide_exit', 'burnout', 'apogee', 'deployment', 'landing'] as const;

export function replayValidity(record: ReplayValidityRecord, time: number) {
  const eventTime = (name: string) => {
    const value = record.events?.[name];
    return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null;
  };
  const missingEvents = events.filter((name) => eventTime(name) === null);
  const deployment = eventTime('deployment');
  const apogee = eventTime('apogee');
  const landing = eventTime('landing');
  // These are event-derived labels, not recorded state transitions. Missing or
  // out-of-order markers must never manufacture a phase.
  let phase = 'Phase unavailable from recorded events';
  const inconsistent = apogee !== null && deployment !== null && deployment < apogee;
  if (Number.isFinite(time) && time >= 0 && !inconsistent) {
    if (landing !== null && time >= landing) phase = 'At or after recorded landing';
    else if (deployment !== null && apogee !== null && deployment >= apogee && time >= deployment)
      phase = 'After modeled deployment start';
    else if (apogee !== null && time >= apogee && (deployment === null || time < deployment))
      phase = 'After apogee trigger; deployment state unavailable or pending';
    else if (apogee !== null && time < apogee) phase = 'Before recorded apogee trigger';
  }
  return {
    identity: `${record.run_id} · ${record.configuration}`,
    controller: record.controller?.trim() || 'unavailable in record',
    sourceIdentity: {
      simulationCode: record.code_sha256 || 'unavailable',
      resolvedSpecification: record.resolved_sha256 || 'unavailable',
    },
    phase,
    missingEvents,
    completion:
      record.trajectory_complete === true
        ? landing === null
          ? 'Trajectory reports completion, but landing event time is unavailable.'
          : 'Landing reported in trajectory.'
        : record.trajectory_complete === false
          ? 'Incomplete trajectory: landing was not recorded within the simulated horizon.'
          : 'Trajectory completion is unavailable in the record.',
  };
}
