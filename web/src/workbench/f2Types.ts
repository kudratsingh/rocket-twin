import type { EvidenceState, SourceRef } from './types';
import type {
  ConventionalCase,
  ConventionalComponent,
  ConventionalConnection,
  ConventionalFinding,
  ConventionalSection,
  ConventionalStep,
} from './conventionalG80Types';

/** F2 reuses display-row shapes only. No F1 result, CAD identity or part association is inherited. */
export interface F2Layer {
  component_id: string;
  label: string;
  z_start_mm: number | null;
  z_end_mm: number | null;
  inner_radius_mm: number | null;
  outer_radius_mm: number | null;
  state: EvidenceState;
  note: string;
  source_ids: string[];
}
export interface F2Joint {
  id: string;
  label: string;
  kind: string;
  station_mm: number | null;
  layers: F2Layer[];
  clearance_mm: number | null;
  state: EvidenceState;
  note: string;
  source_ids: string[];
}
export interface F2LedgerRow {
  id: string;
  label: string;
  mass_g: number | null;
  station_mm: number | null;
  role: string;
  replaces_id: string | null;
  state: EvidenceState;
  note: string;
  source_ids: string[];
}
export interface F2Snapshot {
  schema_version: '1.0.0';
  id: string;
  label: string;
  status: string;
  identity: {
    candidate_id: 'G80-F2';
    source_identity: string;
    specification_sha256: string | null;
    cad_revision: null;
    frame: string;
    units: string;
  };
  generated_from: SourceRef[];
  components: ConventionalComponent[];
  sections: ConventionalSection[];
  joints: F2Joint[];
  connections: ConventionalConnection[];
  sequences: { assembly: ConventionalStep[]; recovery: ConventionalStep[] };
  cases: ConventionalCase[];
  ledger: F2LedgerRow[];
  uncertainties: ConventionalFinding[];
  cad_manifest: null;
}

export function f2Number(value: number | null, unit: string): string {
  if (value === null || !Number.isFinite(value)) return 'Unavailable';
  const shown =
    value !== 0 && Math.abs(value) < 0.0005
      ? value.toExponential(2)
      : new Intl.NumberFormat('en', { maximumFractionDigits: 3 }).format(value);
  return `${shown} ${unit}`.trim();
}
export function isMissingF2Route(status: number, detail: string): boolean {
  return status === 404 && detail === 'Not Found';
}
const finiteOrNull = (value: unknown) =>
  value === null || (typeof value === 'number' && Number.isFinite(value));
const strings = (value: unknown) =>
  Array.isArray(value) && value.every((item) => typeof item === 'string');
const baseRow = (row: unknown): row is { id: string; label: string; source_ids: string[] } =>
  !!row &&
  typeof row === 'object' &&
  typeof (row as { id?: unknown }).id === 'string' &&
  typeof (row as { label?: unknown }).label === 'string' &&
  strings((row as { source_ids?: unknown }).source_ids);

export function validateF2Snapshot(value: unknown): F2Snapshot {
  if (!value || typeof value !== 'object') throw new Error('G80-F2 snapshot is not an object.');
  const item = value as Partial<F2Snapshot>;
  const identity = item.identity;
  if (
    item.schema_version !== '1.0.0' ||
    identity?.candidate_id !== 'G80-F2' ||
    identity.cad_revision !== null ||
    item.cad_manifest !== null ||
    !identity.source_identity ||
    !identity.frame ||
    !identity.units ||
    !(
      identity.specification_sha256 === null || typeof identity.specification_sha256 === 'string'
    ) ||
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
        baseRow(part) &&
        [
          part.mass_g,
          part.z_start_mm,
          part.z_end_mm,
          part.inner_radius_mm,
          part.outer_radius_mm,
        ].every(finiteOrNull) &&
        typeof part.function === 'string' &&
        typeof part.construction === 'string' &&
        typeof part.material === 'string' &&
        typeof part.category === 'string' &&
        typeof part.maturity === 'string' &&
        typeof part.state === 'string' &&
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
        baseRow(section) &&
        finiteOrNull(section.station_mm) &&
        strings(section.component_ids) &&
        typeof section.note === 'string',
    ) ||
    !Array.isArray(item.joints) ||
    !item.joints.every(
      (joint) =>
        baseRow(joint) &&
        finiteOrNull(joint.station_mm) &&
        finiteOrNull(joint.clearance_mm) &&
        typeof joint.kind === 'string' &&
        typeof joint.state === 'string' &&
        typeof joint.note === 'string' &&
        Array.isArray(joint.layers) &&
        joint.layers.every(
          (layer) =>
            layer &&
            typeof layer.label === 'string' &&
            strings(layer.source_ids) &&
            typeof layer.component_id === 'string' &&
            [layer.z_start_mm, layer.z_end_mm, layer.inner_radius_mm, layer.outer_radius_mm].every(
              finiteOrNull,
            ) &&
            typeof layer.state === 'string' &&
            typeof layer.note === 'string',
        ),
    ) ||
    !Array.isArray(item.connections) ||
    !item.connections.every(
      (connection) =>
        baseRow(connection) &&
        typeof connection.from_id === 'string' &&
        typeof connection.to_id === 'string' &&
        typeof connection.kind === 'string' &&
        typeof connection.state === 'string' &&
        typeof connection.note === 'string',
    ) ||
    !item.sequences ||
    !Array.isArray(item.sequences.assembly) ||
    !Array.isArray(item.sequences.recovery) ||
    ![...item.sequences.assembly, ...item.sequences.recovery].every(
      (step) =>
        baseRow(step) &&
        strings(step.acts_on_ids) &&
        typeof step.state === 'string' &&
        typeof step.note === 'string',
    ) ||
    !Array.isArray(item.cases) ||
    !item.cases.every(
      (caseRow) =>
        baseRow(caseRow) &&
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
        typeof caseRow.note === 'string',
    ) ||
    !Array.isArray(item.ledger) ||
    !item.ledger.every(
      (row) =>
        baseRow(row) &&
        finiteOrNull(row.mass_g) &&
        finiteOrNull(row.station_mm) &&
        typeof row.role === 'string' &&
        (row.replaces_id === null || typeof row.replaces_id === 'string') &&
        typeof row.state === 'string' &&
        typeof row.note === 'string',
    ) ||
    !Array.isArray(item.uncertainties) ||
    !item.uncertainties.every(
      (finding) =>
        baseRow(finding) && typeof finding.state === 'string' && typeof finding.note === 'string',
    )
  )
    throw new Error('G80-F2 snapshot version or source contract is incompatible.');
  return item as F2Snapshot;
}
