import packet from '../../../docs/studies/frontend-desktop-detail-20261108/cad-export.json' with { type: 'json' };
import core from '../../../docs/studies/rp1-inspection-geometry-20261107/manifest.json' with { type: 'json' };
import type { InspectionDocument, Part } from '../types';
import { inspectionGeometryAccess } from './inspectionGeometryDownload.ts';

export const INSPECTION_STEP_PROVENANCE_SHA256 =
  'a7af1fadc431dea8958a212e2a552cf2ee833b068dbeaf51dc151d6d7fbbf731';
const BASE = '/engineering-workbench/rp1-step/';
const ASSEMBLY = 'rp1_ad1_v2_inspection_26_records';
const EXPORTER_SHA256 = '63edd7cd49b0b68b9c51fc0c7aa0eedf4b6dab874e78b4398fee109cc451b972';
export type InspectionStepDownload = {
  available: true;
  joint?: true;
  partId: string | null;
  url: string;
  filename: string;
  assetSha256: string;
  provenanceUrl: string;
  provenanceFilename: string;
  label: string;
  maturity: string;
  units: 'mm';
  cadFrame: string;
  viewerMapping: string;
  limitations: readonly string[];
};
export type InspectionStepAccess = InspectionStepDownload | { available: false; reason: string };

function registeredPacket() {
  return (
    packet.status === 'complete_inspection_reconstruction' &&
    packet.identity.configuration_id === core.id &&
    packet.identity.specification_sha256 === core.identity.specification_sha256 &&
    packet.identity.inspection_geometry_sha256 === core.identity.inspection_geometry_sha256 &&
    packet.script.path === 'scripts/wo04_rp1_inspection_step.py' &&
    packet.script.sha256 === EXPORTER_SHA256 &&
    packet.units.step === 'mm' &&
    packet.engineering_accepted === false &&
    packet.manufacturing_clearance === false &&
    packet.flight_ready === false &&
    Object.entries(core.sources).every(
      ([path, hash]) => (packet.source_hashes as Record<string, string>)[path] === hash,
    ) &&
    packet.parts.length === 26 &&
    packet.source_records.length === 55 &&
    core.parts.every((row) => {
      const source = packet.source_records.find((item) => item.id === row.id);
      const step = packet.parts.find((item) => item.id === row.id);
      return (
        source?.inspection_shape_sha256 === row.inspection_shape_sha256 &&
        source.maturity === row.maturity &&
        (row.mesh
          ? step?.inspection_shape_sha256 === row.inspection_shape_sha256 &&
            step.maturity === row.maturity &&
            step.core_glb.sha256 === row.mesh.sha256 &&
            step.path === `output/rp1-inspection-step/parts/${row.id}.step`
          : !step)
      );
    })
  );
}

function registeredAsset(partId: string | null, joint = false) {
  if (joint) {
    const id = 'critical_motor_fin_ring_joint';
    const row = packet.assemblies.find((item) => item.id === id);
    return row?.path === `output/rp1-inspection-step/${id}.step`
      ? { url: `${BASE}${id}.step`, hash: row.sha256 }
      : null;
  }
  if (partId === null) {
    const row = packet.assemblies.find((item) => item.id === ASSEMBLY);
    return row?.path === `output/rp1-inspection-step/${ASSEMBLY}.step`
      ? { url: `${BASE}${ASSEMBLY}.step`, hash: row.sha256 }
      : null;
  }
  const row = packet.parts.find((item) => item.id === partId);
  return row?.path === `output/rp1-inspection-step/parts/${partId}.step`
    ? { url: `${BASE}parts/${partId}.step`, hash: row.sha256 }
    : null;
}

/** The same registered, assembled nine-record joint inspected in the fin scene. */
export function inspectionJointStepAccess(vehicle: InspectionDocument): InspectionStepAccess {
  const admitted = inspectionStepAccess(vehicle);
  if (!admitted.available) return admitted;
  const asset = registeredAsset(null, true);
  if (!asset) return { available: false, reason: 'Registered joint STEP unavailable.' };
  const filename = `${vehicle.id}--motor-fin-ring-joint--${asset.hash.slice(0, 12)}.step`;
  return {
    ...admitted,
    joint: true,
    url: asset.url,
    assetSha256: asset.hash,
    filename,
    provenanceFilename: filename.replace(/\.step$/, '.step-provenance.json'),
  };
}

/** Exact live-document admission plus a fixed, completed source STEP registry. */
export function inspectionStepAccess(
  vehicle: InspectionDocument,
  selectedPart: Part | null = null,
): InspectionStepAccess {
  const geometry = inspectionGeometryAccess(vehicle, selectedPart);
  if (!geometry.available) return geometry;
  if (!registeredPacket())
    return { available: false, reason: 'Recorded STEP source packet is incompatible.' };
  const partId = selectedPart?.id ?? null;
  const asset = registeredAsset(partId);
  if (!asset)
    return {
      available: false,
      reason: 'No registered inspection STEP solid exists for this source record.',
    };
  const filename = `${vehicle.id}--${partId ?? 'assembly'}--inspection-${asset.hash.slice(0, 12)}.step`;
  return {
    available: true,
    partId,
    url: asset.url,
    filename,
    assetSha256: asset.hash,
    provenanceUrl: `${BASE}provenance.json`,
    provenanceFilename: filename.replace(/\.step$/, '.step-provenance.json'),
    label: geometry.label,
    maturity: geometry.maturity,
    units: 'mm',
    cadFrame: packet.cad_frame,
    viewerMapping: packet.viewer_mapping,
    limitations: packet.limitations,
  };
}

async function fetchRegistered(
  access: InspectionStepDownload,
  kind: 'step' | 'provenance',
  signal: AbortSignal | undefined,
  fetcher: typeof fetch,
) {
  const registered = registeredAsset(access.partId, access.joint);
  if (
    !registeredPacket() ||
    !registered ||
    access.url !== registered.url ||
    access.assetSha256 !== registered.hash ||
    access.provenanceUrl !== `${BASE}provenance.json`
  )
    throw new Error('Unregistered inspection STEP request.');
  const url = kind === 'step' ? registered.url : `${BASE}provenance.json`;
  const expected = kind === 'step' ? registered.hash : INSPECTION_STEP_PROVENANCE_SHA256;
  const response = await fetcher(url, { signal, redirect: 'error', credentials: 'same-origin' });
  if (!response.ok || response.redirected)
    throw new Error('Inspection STEP/provenance asset unavailable or redirected.');
  const bytes = await response.arrayBuffer();
  const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), (value) =>
    value.toString(16).padStart(2, '0'),
  ).join('');
  if (signal?.aborted) throw new DOMException('Download cancelled', 'AbortError');
  if (digest !== expected)
    throw new Error('Inspection STEP/provenance bytes do not match the registered SHA-256.');
  const text = new TextDecoder().decode(bytes);
  if (
    kind === 'step' &&
    (!text.startsWith('ISO-10303-21;') || !text.includes('SI_UNIT(.MILLI.,.METRE.)'))
  )
    throw new Error('Registered response is not the millimetre STEP packet.');
  if (kind === 'provenance' && JSON.parse(text).id !== packet.id)
    throw new Error('Registered provenance identity differs.');
  return bytes;
}

export function fetchInspectionStep(
  access: InspectionStepDownload,
  signal?: AbortSignal,
  fetcher: typeof fetch = fetch,
) {
  return fetchRegistered(access, 'step', signal, fetcher);
}
export function fetchInspectionStepProvenance(
  access: InspectionStepDownload,
  signal?: AbortSignal,
  fetcher: typeof fetch = fetch,
) {
  return fetchRegistered(access, 'provenance', signal, fetcher);
}
