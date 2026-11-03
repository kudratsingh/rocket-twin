import type { EvidenceState, GeometryMaturity, SourceRef } from './types';

/** Independent conventional fixed-motor G80-F1 projection, never a C1/A1 CAD mapping. */
export interface ConventionalComponent {
  id: string;
  label: string;
  category:
    'airframe' | 'fin' | 'motor' | 'recovery' | 'avionics' | 'hardware' | 'thermal' | 'unknown';
  function: string;
  construction: string;
  material: string;
  mass_g: number | null;
  z_start_mm: number | null;
  z_end_mm: number | null;
  inner_radius_mm: number | null;
  outer_radius_mm: number | null;
  maturity: GeometryMaturity;
  state: EvidenceState;
  source_ids: string[];
  note: string;
  dimensions?: Record<string, number>;
}
export interface ConventionalSection {
  id: string;
  label: string;
  station_mm: number | null;
  component_ids: string[];
  note: string;
  source_ids: string[];
}
export interface ConventionalConnection {
  id: string;
  label: string;
  from_id: string;
  to_id: string;
  kind: string;
  state: EvidenceState;
  note: string;
  source_ids: string[];
}
export interface ConventionalStep {
  id: string;
  label: string;
  acts_on_ids: string[];
  state: EvidenceState;
  note: string;
  source_ids: string[];
}
export interface ConventionalCase {
  id: string;
  label: string;
  total_mass_g: number | null;
  loaded_cg_mm: number | null;
  reference_cp_mm: number | null;
  margin_cal: number | null;
  guide_speed_mps: number | null;
  usable_guide_m: number | null;
  formal_headroom_g: number | null;
  planning_headroom_g: number | null;
  source_ids: string[];
  note: string;
}
export interface ConventionalFinding {
  id: string;
  label: string;
  state: EvidenceState;
  note: string;
  source_ids: string[];
}
export interface ConventionalSnapshot {
  schema_version: '1.0.0';
  id: string;
  label: string;
  status: string;
  identity: {
    candidate_id: 'G80-F1';
    source_identity: string;
    specification_sha256: string | null;
    cad_revision: string | null;
    frame: string;
    units: string;
  };
  generated_from: SourceRef[];
  components: ConventionalComponent[];
  sections: ConventionalSection[];
  connections: ConventionalConnection[];
  sequences: { assembly: ConventionalStep[]; recovery: ConventionalStep[] };
  cases: ConventionalCase[];
  uncertainties: ConventionalFinding[];
  cad_manifest: null | {
    revision: string;
    source_sha256: string;
    parts: { component_id: string; path: string; sha256: string }[];
  };
}

export function conventionalNumber(value: number | null, unit: string): string {
  if (value === null || !Number.isFinite(value)) return 'Unavailable';
  const shown =
    value !== 0 && Math.abs(value) < 0.0005
      ? value.toExponential(2)
      : new Intl.NumberFormat('en', { maximumFractionDigits: 3 }).format(value);
  return `${shown} ${unit}`.trim();
}
export function isMissingConventionalRoute(status: number, detail: string): boolean {
  return status === 404 && detail === 'Not Found';
}

const finiteOrNull = (value: unknown) =>
  value === null || (typeof value === 'number' && Number.isFinite(value));
const strings = (value: unknown) =>
  Array.isArray(value) && value.every((item) => typeof item === 'string');
const sourceIds = (value: unknown) => strings(value);
export function validateConventionalSnapshot(value: unknown): ConventionalSnapshot {
  if (!value || typeof value !== 'object')
    throw new Error('G80-F1 source snapshot is not an object.');
  const item = value as Partial<ConventionalSnapshot>;
  const identity = item.identity;
  if (
    item.schema_version !== '1.0.0' ||
    identity?.candidate_id !== 'G80-F1' ||
    !identity.source_identity ||
    typeof identity.frame !== 'string' ||
    typeof identity.units !== 'string' ||
    !(
      identity.specification_sha256 === null || typeof identity.specification_sha256 === 'string'
    ) ||
    !(identity.cad_revision === null || typeof identity.cad_revision === 'string') ||
    !Array.isArray(item.generated_from) ||
    !item.generated_from.every(
      (source) =>
        source &&
        typeof source.id === 'string' &&
        typeof source.path === 'string' &&
        /^[0-9a-f]{64}$/.test(source.sha256) &&
        typeof source.description === 'string',
    ) ||
    !Array.isArray(item.components) ||
    !item.components.every(
      (part) =>
        part &&
        typeof part.id === 'string' &&
        typeof part.label === 'string' &&
        typeof part.category === 'string' &&
        typeof part.function === 'string' &&
        typeof part.construction === 'string' &&
        typeof part.material === 'string' &&
        [
          part.mass_g,
          part.z_start_mm,
          part.z_end_mm,
          part.inner_radius_mm,
          part.outer_radius_mm,
        ].every(finiteOrNull) &&
        typeof part.maturity === 'string' &&
        typeof part.state === 'string' &&
        sourceIds(part.source_ids) &&
        typeof part.note === 'string' &&
        (part.dimensions === undefined ||
          (part.dimensions !== null &&
            typeof part.dimensions === 'object' &&
            Object.values(part.dimensions).every(
              (n) => typeof n === 'number' && Number.isFinite(n),
            ))),
    ) ||
    !Array.isArray(item.sections) ||
    !item.sections.every(
      (section) =>
        section &&
        typeof section.id === 'string' &&
        typeof section.label === 'string' &&
        finiteOrNull(section.station_mm) &&
        strings(section.component_ids) &&
        typeof section.note === 'string' &&
        sourceIds(section.source_ids),
    ) ||
    !Array.isArray(item.connections) ||
    !item.connections.every(
      (connection) =>
        connection &&
        typeof connection.id === 'string' &&
        typeof connection.label === 'string' &&
        typeof connection.from_id === 'string' &&
        typeof connection.to_id === 'string' &&
        typeof connection.kind === 'string' &&
        typeof connection.state === 'string' &&
        typeof connection.note === 'string' &&
        sourceIds(connection.source_ids),
    ) ||
    !item.sequences ||
    !Array.isArray(item.sequences.assembly) ||
    !Array.isArray(item.sequences.recovery) ||
    ![...item.sequences.assembly, ...item.sequences.recovery].every(
      (step) =>
        step &&
        typeof step.id === 'string' &&
        typeof step.label === 'string' &&
        strings(step.acts_on_ids) &&
        typeof step.state === 'string' &&
        typeof step.note === 'string' &&
        sourceIds(step.source_ids),
    ) ||
    !Array.isArray(item.cases) ||
    !item.cases.every(
      (caseRow) =>
        caseRow &&
        typeof caseRow.id === 'string' &&
        typeof caseRow.label === 'string' &&
        [
          caseRow.total_mass_g,
          caseRow.loaded_cg_mm,
          caseRow.reference_cp_mm,
          caseRow.margin_cal,
          caseRow.guide_speed_mps,
          caseRow.usable_guide_m,
          caseRow.formal_headroom_g,
          caseRow.planning_headroom_g,
        ].every(finiteOrNull) &&
        sourceIds(caseRow.source_ids) &&
        typeof caseRow.note === 'string',
    ) ||
    !Array.isArray(item.uncertainties) ||
    !item.uncertainties.every(
      (finding) =>
        finding &&
        typeof finding.id === 'string' &&
        typeof finding.label === 'string' &&
        typeof finding.state === 'string' &&
        typeof finding.note === 'string' &&
        sourceIds(finding.source_ids),
    ) ||
    !(
      item.cad_manifest === null ||
      (item.cad_manifest &&
        typeof item.cad_manifest.revision === 'string' &&
        typeof item.cad_manifest.source_sha256 === 'string' &&
        Array.isArray(item.cad_manifest.parts) &&
        item.cad_manifest.parts.every(
          (part) =>
            part &&
            typeof part.component_id === 'string' &&
            typeof part.path === 'string' &&
            /^[0-9a-f]{64}$/.test(part.sha256),
        ))
    )
  )
    throw new Error('G80-F1 snapshot version or source contract is incompatible.');
  if (item.cad_manifest === null && identity.cad_revision !== null)
    throw new Error('G80-F1 CAD identity lacks an exact manifest.');
  if (item.cad_manifest && identity.cad_revision !== item.cad_manifest.revision)
    throw new Error('G80-F1 CAD manifest revision differs from the snapshot.');
  return item as ConventionalSnapshot;
}
