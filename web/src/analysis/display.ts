import { Color } from 'three';
import type { JsonValue } from '../types';
import type {
  AnalysisField,
  AnalysisIdentity,
  AnalysisManifest,
  AnalysisPayload,
  Quantity,
} from './types';

export const quantityName: Record<Quantity, string> = {
  temperature: 'Temperature',
  stress: 'Stress component',
  displacement: 'Displacement magnitude',
  design_margin: 'Design margin',
};
export const displayUnit: Record<Quantity, string> = {
  temperature: '°C',
  stress: 'MPa',
  displacement: 'mm',
  design_margin: 'dimensionless',
};
export const fixedRange: Record<Quantity, [number, number]> = {
  temperature: [0, 300],
  stress: [0, 25],
  displacement: [0, 5],
  design_margin: [-1, 3],
};
export function displayScalar(value: number, quantity: Quantity): number {
  return quantity === 'temperature'
    ? value - 273.15
    : quantity === 'stress'
      ? value / 1e6
      : quantity === 'displacement'
        ? value * 1000
        : value;
}
export function scalarText(value: number | null | undefined, quantity: Quantity): string {
  return value == null
    ? 'Unavailable'
    : `${displayScalar(value, quantity).toLocaleString(undefined, { maximumFractionDigits: 3 })} ${displayUnit[quantity]}`;
}

// This is a display palette, not an engineering calculation or pass/fail criterion.
export function fieldColor(value: number, minimum: number, maximum: number): string {
  const fraction = Math.max(0, Math.min(1, (value - minimum) / (maximum - minimum || 1)));
  const stops = ['#326b98', '#48bbc1', '#c1c285', '#d48653', '#bc5553'];
  const segment = Math.min(stops.length - 2, Math.floor(fraction * (stops.length - 1)));
  return `#${new Color(stops[segment]).lerp(new Color(stops[segment + 1]), fraction * (stops.length - 1) - segment).getHexString()}`;
}

export function identityMismatch(
  manifest: AnalysisManifest,
  vehicleId: string,
  expected?: Record<string, JsonValue>,
): string | null {
  if (!manifest.compatible)
    return manifest.incompatible_reason || 'The API rejected this historical analysis identity.';
  if (!expected) return 'The current vehicle identity is unavailable.';
  const actual: AnalysisIdentity = manifest.identity;
  if (!actual || typeof actual !== 'object') return 'Recorded analysis identity is unavailable.';
  if (actual.configuration_id !== vehicleId || expected.configuration_id !== vehicleId)
    return 'Configuration identifier does not match the current vehicle.';
  const sha = (value: unknown) => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
  if (
    !sha(actual.resolved_spec_sha256) ||
    !sha(expected.resolved_spec_sha256) ||
    actual.resolved_spec_sha256 !== expected.resolved_spec_sha256
  )
    return 'Resolved specification fingerprint does not match the current vehicle.';
  if (
    !sha(actual.cad_revision_sha256) ||
    !sha(expected.cad_revision_sha256) ||
    actual.cad_revision_sha256 !== expected.cad_revision_sha256
  )
    return 'CAD generator fingerprint does not match the current geometry.';
  const expectedParts = expected.part_shape_sha256;
  const actualParts = actual.part_shape_sha256;
  if (
    !expectedParts ||
    typeof expectedParts !== 'object' ||
    Array.isArray(expectedParts) ||
    !actualParts ||
    typeof actualParts !== 'object' ||
    Array.isArray(actualParts) ||
    !Object.keys(expectedParts).length ||
    !Object.values(expectedParts).every(sha) ||
    !Object.values(actualParts).every(sha)
  )
    return 'Part geometry fingerprints are unavailable.';
  if (
    Object.keys(actual.part_shape_sha256).length !== Object.keys(expectedParts).length ||
    Object.entries(actual.part_shape_sha256).some(([id, hash]) => expectedParts[id] !== hash)
  )
    return 'One or more part geometry fingerprints do not match.';
  return null;
}

// Failed numerical fields remain visible as evidence, but never color active geometry.
export function fieldBlockReason(field: AnalysisField | undefined): string {
  if (field?.evidence.validation === 'failed')
    return 'FAILED numerical validation: this recorded field cannot be attached to the active geometry.';
  if (field?.evidence.provenance === 'unavailable')
    return field.unavailable_reason || 'No recorded samples are available for this field.';
  return '';
}

export function validatePayload(field: AnalysisField, data: AnalysisPayload): void {
  if (
    field.times_s !== null &&
    field.times_s !== undefined &&
    (!Array.isArray(field.times_s) ||
      !field.times_s.length ||
      field.times_s.some(
        (time, index, times) => !Number.isFinite(time) || (index > 0 && time <= times[index - 1]),
      ))
  )
    throw new Error('Recorded field exact sample times are invalid; no time axis is inferred.');
  if (
    !data ||
    !Array.isArray(data.values) ||
    data.values.length !== (field.times_s?.length || 1) ||
    data.values.some(
      (frame) =>
        !Array.isArray(frame) ||
        frame.length !== field.sample_count ||
        frame.some(
          (value) => value !== null && (typeof value !== 'number' || !Number.isFinite(value)),
        ),
    )
  )
    throw new Error('Recorded field sample shape or values disagree with the manifest.');
  if (field.association === 'part') {
    if (field.sample_count !== field.part_ids.length)
      throw new Error('Part field sample count does not match declared part coverage.');
    if (
      data.part_ids &&
      (data.part_ids.length !== field.part_ids.length ||
        data.part_ids.some((id, index) => id !== field.part_ids[index]))
    )
      throw new Error('Recorded part order disagrees with the manifest.');
  } else {
    const mesh = data.analysis_mesh;
    if (
      !mesh ||
      !mesh.nodes.length ||
      !mesh.elements.length ||
      field.registration?.type !== 'affine_4x4' ||
      field.registration.target_frame !== 'CAD_mm_registered_to_viewer_m'
    )
      throw new Error('Spatial field has no supported, explicit geometry registration.');
    if (
      !Array.isArray(field.registration.matrix) ||
      field.registration.matrix.length !== 4 ||
      field.registration.matrix.some(
        (row) =>
          !Array.isArray(row) || row.length !== 4 || row.some((value) => !Number.isFinite(value)),
      )
    )
      throw new Error('Spatial field registration is not a finite four-by-four transform.');
    if (
      mesh.nodes.some(
        (node) =>
          !Array.isArray(node.xyz_mm) ||
          node.xyz_mm.length !== 3 ||
          node.xyz_mm.some((value) => !Number.isFinite(value)),
      )
    )
      throw new Error('Analysis mesh has invalid node coordinates.');
    const nodeIds = new Set(mesh.nodes.map((node) => node.id));
    if (
      nodeIds.size !== mesh.nodes.length ||
      mesh.elements.some((element) => element.nodes.some((id) => !nodeIds.has(id)))
    )
      throw new Error('Analysis mesh has duplicate nodes or unresolved element connectivity.');
    if (field.part_ids.length !== 1 || mesh.part_id !== field.part_ids[0])
      throw new Error('The spatial field is not registered to one declared part instance.');
    if (field.association !== 'node' && field.association !== 'element')
      throw new Error(
        `The viewer does not support ${field.association} coverage; no surface is inferred.`,
      );
    if (
      field.sample_count !==
      (field.association === 'node' ? mesh.nodes.length : mesh.elements.length)
    )
      throw new Error('Analysis mesh sample count disagrees with the field association.');
    if (mesh.elements.some((element) => element.type !== 'S6' || element.nodes.length !== 6))
      throw new Error('The viewer supports the recorded six-node triangular shell mesh only.');
  }
}
