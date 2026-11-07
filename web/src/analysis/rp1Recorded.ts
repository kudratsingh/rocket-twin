import type { InspectionDocument, JsonValue } from '../types';
import {
  RP1_CONNECTIONS_CONFIGURATION,
  RP1_CONNECTIONS_SHA256,
} from '../workbench/rp1Connections.ts';

const object = (value: JsonValue | undefined): Record<string, JsonValue> =>
  value && typeof value === 'object' && !Array.isArray(value) ? value : {};
const finite = (value: JsonValue | undefined): number | null =>
  typeof value === 'number' && Number.isFinite(value) ? value : null;

/** Read saved scalar evidence only; do not infer a spatial field or installed result. */
export function rp1RecordedFindings(vehicle: InspectionDocument) {
  if (
    vehicle.id !== RP1_CONNECTIONS_CONFIGURATION ||
    vehicle.identity?.specification_sha256 !== RP1_CONNECTIONS_SHA256 ||
    vehicle.identity?.record_sha256 !==
      'bc349a24fe1cfaa4d883b9e00dc5b75387638a7be5cd4b05d9f32112ee8bd95b'
  )
    throw new Error('Recorded RP1 findings unavailable: source identity mismatch.');
  const fin = object(vehicle.evidence?.fin);
  const samples = fin.ideal_composite_strip_lower_deflection_only;
  const row = Array.isArray(samples)
    ? samples.map(object).find((s) => s.divisions === 1600)
    : undefined;
  const connections = object(vehicle.evidence?.connections);
  const route = object(vehicle.evidence?.cord_geometry);
  return {
    source: String(vehicle.identity.record_path || 'Unavailable'),
    sourceHash: String(vehicle.identity.record_sha256),
    finStressPa: finite(row?.maximum_bending_Pa),
    finMovementM: finite(row?.deflection_m),
    finStatus: fin.bonded_panel_stress_screen_pass_only === false ? 'failed-screen' : 'unavailable',
    installedMovementM: finite(fin.installed_displacement),
    installedPeelCapacityPa: finite(fin.normal_peel_capacity),
    recoveryCapacityN: finite(connections.finished_attachment_capacity_N),
    recoveryMeanOuterRingShearPa: finite(connections.outer_ring_mean_shear_Pa),
    cordReachMm: finite(route.available_external_reach_mm),
    notchPerFlankMm: finite(route.notch_min_per_flank_mm),
  };
}
