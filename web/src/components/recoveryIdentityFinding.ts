import report from '../../../docs/studies/frontend-desktop-detail-20261108/next-detail-sources.json' with { type: 'json' };
import core from '../../../docs/studies/rp1-inspection-geometry-20261107/manifest.json' with { type: 'json' };
import type { InspectionDocument, Part } from '../types';

export const RECOVERY_IDENTITY_REPORT_SHA256 =
  '915539c61d128005c4842399ebaeecee43672be311d14a0d4b9154c044e5b6ac';
const CONFIGURATION = 'G80-F2-RP1-AD1-definition-v2';
const SPECIFICATION = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
const GEOMETRY = '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608';
const PART = 'independent_recovery';
const sourceRecord = report.components.find((item) => item.part_id === PART);
const coreRecord = core.parts.find((item) => item.id === PART);

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

export interface RecoveryIdentityFinding {
  id: 'rp1-independent-recovery-identity-unresolved';
  partId: 'independent_recovery';
  state: 'unresolved';
  proposedName: 'Eggtimer Apogee';
  legacyName: 'Altus Metrum EasyMini v3.0';
  sourcePath: string;
  specificationSha256: string;
  inspectionGeometrySha256: string;
  primaryLocators: readonly string[];
  legacyLocator: string;
  evidencePath: string;
  evidenceDataPath: string;
  evidenceSha256: string;
}

/**
 * A registered source conflict, not a product choice or inference from box dimensions.
 * Missing mesh loading does not resolve source identity or suppress this finding.
 */
export function recoveryIdentityFinding(
  vehicle: InspectionDocument,
  selectedPart: Part | null = null,
): RecoveryIdentityFinding | null {
  if (
    report.id !== 'rp1-next-detail-primary-source-check-20261108' ||
    report.frozen_source.configuration_id !== CONFIGURATION ||
    report.frozen_source.sha256 !== SPECIFICATION ||
    report.frozen_source.path !== core.identity.specification_path ||
    sourceRecord?.exact_installed_identity !== 'unresolved' ||
    sourceRecord.source_conflict?.legacy_locator !==
      'parts[id=independent_recovery].engineering.function' ||
    !sourceRecord.source_conflict.legacy_text.includes('Altus Metrum EasyMini v3.0') ||
    !sourceRecord.reference_family?.startsWith('Eggtimer Apogee') ||
    core.identity.inspection_geometry_sha256 !== GEOMETRY ||
    !coreRecord ||
    vehicle.id !== CONFIGURATION ||
    vehicle.identity?.configuration_id !== CONFIGURATION ||
    vehicle.identity.specification_sha256 !== SPECIFICATION ||
    vehicle.identity.inspection_geometry_sha256 !== GEOMETRY ||
    !selectedPart ||
    selectedPart.id !== PART ||
    !vehicle.parts.includes(selectedPart) ||
    vehicle.parts.length !== 55 ||
    new Set(vehicle.parts.map((part) => part.id)).size !== 55 ||
    vehicle.parts.some((part) => !core.parts.some((row) => row.id === part.id)) ||
    (selectedPart as unknown as Record<string, unknown>).inspection_shape_sha256 !==
      coreRecord.inspection_shape_sha256 ||
    record(selectedPart.representation)?.role !== coreRecord.maturity
  )
    return null;
  return {
    id: 'rp1-independent-recovery-identity-unresolved',
    partId: PART,
    state: 'unresolved',
    proposedName: 'Eggtimer Apogee',
    legacyName: 'Altus Metrum EasyMini v3.0',
    sourcePath: report.frozen_source.path,
    specificationSha256: SPECIFICATION,
    inspectionGeometrySha256: GEOMETRY,
    primaryLocators: [...sourceRecord.source_conflict.primary_locators],
    legacyLocator: sourceRecord.source_conflict.legacy_locator,
    evidencePath: 'docs/studies/frontend-desktop-detail-20261108/next-detail-sources.md',
    evidenceDataPath: 'docs/studies/frontend-desktop-detail-20261108/next-detail-sources.json',
    evidenceSha256: RECOVERY_IDENTITY_REPORT_SHA256,
  };
}
