import type { InspectionDocument } from '../types';
import {
  RP1_CONNECTIONS_CONFIGURATION,
  RP1_CONNECTIONS_SHA256,
  RP1_CONNECTION_PART_IDS,
  exactRp1EvidenceRouteSource,
  validateRp1Connections,
} from './rp1Connections.ts';
import type { Rp1ConnectionsDocument } from './rp1Connections.ts';

export const RP1_INSPECTION_GEOMETRY_SHA256 =
  '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608';

export type Rp1PartEvidenceResult =
  | { status: 'unavailable' | 'unmapped'; message: string; sourceStatus: string; links: [] }
  | {
      status: 'available';
      message: string;
      sourceStatus: string;
      links: { id: string; label: string; href: string }[];
    };

/** Only exact frozen source parts can acquire links from the recorded relationship document. */
export function rp1PartEvidenceLinks(
  source: InspectionDocument,
  partId: string,
  value: unknown,
): Rp1PartEvidenceResult {
  const unavailable = (message: string): Rp1PartEvidenceResult => ({
    status: 'unavailable',
    message,
    sourceStatus: '',
    links: [],
  });
  const ids = source.parts.map((part) => part.id);
  if (
    source.id !== RP1_CONNECTIONS_CONFIGURATION ||
    source.identity?.configuration_id !== RP1_CONNECTIONS_CONFIGURATION ||
    source.identity?.specification_sha256 !== RP1_CONNECTIONS_SHA256 ||
    source.identity?.inspection_geometry_sha256 !== RP1_INSPECTION_GEOMETRY_SHA256 ||
    ids.length !== RP1_CONNECTION_PART_IDS.length ||
    new Set(ids).size !== RP1_CONNECTION_PART_IDS.length ||
    !RP1_CONNECTION_PART_IDS.every((id) => ids.includes(id)) ||
    !ids.includes(partId)
  )
    return unavailable('RP1 connection links unavailable for this design, revision or part.');

  let document: Rp1ConnectionsDocument;
  try {
    document = validateRp1Connections(value);
  } catch {
    return unavailable('RP1 connection sources unavailable or incompatible with frozen AD1 v2.');
  }
  if (!exactRp1EvidenceRouteSource(document))
    return unavailable('RP1 connection source fingerprints or route membership changed.');
  const matching = document.connections.filter((connection) =>
    connection.part_ids.includes(partId),
  );
  if (!matching.length)
    return {
      status: 'unmapped',
      message:
        'Connection evidence unavailable for this part in the recorded AD1 study. No relationship is inferred.',
      sourceStatus: document.status,
      links: [],
    };
  return {
    status: 'available',
    message: 'Open a recorded connection route for this exact AD1 part.',
    sourceStatus: document.status,
    links: matching.map((connection) => ({
      id: connection.id,
      label: connection.label,
      href: `/?${new URLSearchParams({
        workspace: 'engineering',
        view: 'rp1-connections',
        design: RP1_CONNECTIONS_CONFIGURATION,
        spec: RP1_CONNECTIONS_SHA256,
        part: partId,
        connection: connection.id,
      })}`,
    })),
  };
}
