import core from '../../../docs/studies/rp1-inspection-geometry-20261107/manifest.json' with { type: 'json' };
import type { InspectionDocument, Part } from '../types';

const CONFIGURATION = 'G80-F2-RP1-AD1-definition-v2';
const SPEC = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
const GEOMETRY = '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608';
const MECHANICAL = new Set([
  'fin_set',
  'fin_tabs',
  'root_gussets',
  'body',
  'motor_tube',
  'forward_ring',
  'aft_ring',
]);

type DepthAccess =
  | { available: false; reason: string }
  | { available: true; kind: 'pcb' | 'mechanical'; label: string };

/** Source-bound references supplement the vehicle; they never replace its physical definition. */
export function componentDepthAccess(vehicle: InspectionDocument, part: Part): DepthAccess {
  const source = core.parts.find((row) => row.id === part.id);
  if (
    vehicle.id !== CONFIGURATION ||
    vehicle.identity?.configuration_id !== CONFIGURATION ||
    vehicle.identity?.specification_sha256 !== SPEC ||
    vehicle.identity?.inspection_geometry_sha256 !== GEOMETRY ||
    !vehicle.parts.includes(part) ||
    vehicle.parts.length !== core.parts.length ||
    new Set(vehicle.parts.map((row) => row.id)).size !== core.parts.length ||
    vehicle.parts.some((row) => !core.parts.some((entry) => entry.id === row.id)) ||
    !source ||
    (part as unknown as Record<string, unknown>).inspection_shape_sha256 !==
      source.inspection_shape_sha256
  )
    return {
      available: false,
      reason: 'Component reference unavailable for this design, revision or part.',
    };
  if (part.id === 'high_g_accel')
    return { available: true, kind: 'pcb', label: 'Explore PCB structure in 3D' };
  if (MECHANICAL.has(part.id))
    return {
      available: true,
      kind: 'mechanical',
      label: 'Explore fin and motor-mount construction',
    };
  return {
    available: false,
    reason:
      'Detailed component geometry is not yet defined for this part. Its recorded envelope and source information remain available.',
  };
}
