import type { ReplayValidityRecord } from './replayValidity';
import { replayWindowStatus } from './replayWindow.ts';
import type { ReplayWindow } from './replayWindow.ts';

/** Event interpretation for a non-spatial storyboard, never a pose or recovery simulation. */
export function recoveryStoryboard(
  record: ReplayValidityRecord,
  time: number,
  window: ReplayWindow,
) {
  const read = (name: string) => {
    const value = record.events?.[name];
    return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null;
  };
  const apogee = read('apogee');
  const deployment = read('deployment');
  const landing = read('landing');
  const inWindow = replayWindowStatus(window, time) === 'inside';
  const inconsistent =
    (deployment !== null && apogee !== null && deployment < apogee) ||
    (landing !== null && deployment !== null && landing < deployment);
  const eligible = inWindow && deployment !== null && !inconsistent;
  const reached = eligible && time >= deployment;
  return {
    apogee,
    deployment,
    landing,
    status: !inWindow
      ? 'Outside valid recorded support: recovery sequence unavailable at this time.'
      : inconsistent
        ? 'Inconsistent event order: recovery sequence unavailable.'
        : deployment === null
          ? 'Deployment time unavailable: no canopy illustration is shown.'
          : reached
            ? landing !== null && time >= landing
              ? 'At or after the recorded landing marker.'
              : 'After the modeled deployment-start marker.'
            : 'Before the modeled deployment-start marker.',
    reached,
    landed: reached && landing !== null && time >= landing,
    pending: eligible && !reached,
    phaseSource: 'Derived from saved event times; not measured canopy or suspension state.',
  };
}
