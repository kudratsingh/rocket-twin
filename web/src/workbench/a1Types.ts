import type { EvidenceState, SourceRef } from './types';

/** Independent A1 concept snapshot. It never attaches to C1 CAD or changes A/B records. */
export interface A1Identity {
  candidate_id: string;
  source_identity: string;
  cad_revision: null;
  frame: string;
  units: string;
}
export interface A1Value {
  value: number | null;
  unit: string;
  state: EvidenceState;
  note: string;
}
export interface A1FitRow {
  id: string;
  label: string;
  result: A1Value;
  criterion: string;
  source_ids: string[];
}
export interface A1Path {
  id: string;
  label: string;
  sequence: string[];
  state: EvidenceState;
  note: string;
  source_ids: string[];
}
export interface A1Finding {
  id: string;
  label: string;
  state: EvidenceState;
  note: string;
  source_ids: string[];
}
export interface A1Feature {
  id: string;
  label: string;
  role: string;
  start_mm: number | null;
  end_mm: number | null;
  inner_radius_mm: number | null;
  outer_radius_mm: number | null;
  axes_deg: number[];
  widths_mm: number[];
  note: string;
  source_ids: string[];
}
export interface A1Case {
  id: string;
  label: string;
  state: EvidenceState;
  total_mass_g: number | null;
  loaded_cg_mm: number | null;
  burnout_cg_mm: number | null;
  reference_cp_mm: number | null;
  loaded_margin_cal: number | null;
  burnout_margin_cal: number | null;
  recovery_force_n: number | null;
  baseline_formal_headroom_g?: number | null;
  baseline_planning_headroom_g?: number | null;
  guide_results: { usable_m: number; speed_mps: number | null }[];
  note: string;
  source_ids: string[];
}
export interface A1JointDetail {
  radial_stack: { label: string; thickness_mm: number; source_ids: string[] }[];
  total_to_nut_end_mm: number;
  maximum_to_nut_end_mm: number;
  bolt_length_mm: number;
  minimum_protrusion_mm: number;
  hole_diameter_mm: number;
  upper_bond: { length_mm: number; radial_gap_mm: number; paper_wall_mm: number };
  root: {
    edge_patch_mm: [number, number];
    fillet_leg_mm: number;
    normal_outer_n: number;
    normal_inner_n: number;
    normal_peel_mpa: number;
    toe_z_mm: [number, number];
    heel_z_mm: [number, number];
    stop_radial_tangential_mm: [number, number];
  };
  note: string;
  source_ids: string[];
}
export interface A1Snapshot {
  schema_version: string;
  id: string;
  label: string;
  status: string;
  identity: A1Identity;
  generated_from: SourceRef[];
  geometry: {
    sleeve_length: A1Value;
    sleeve_outer_diameter: A1Value;
    sleeve_inner_diameter: A1Value;
    upper_stop_station: A1Value;
    axial_overlap: A1Value;
    index_feature_count: A1Value;
    retention_feature_count: A1Value;
    features: A1Feature[];
    note: string;
  };
  fit_rows: A1FitRow[];
  paths: A1Path[];
  protected_volumes: A1Finding[];
  mass: {
    net_delta: A1Value;
    ledger_rows: A1Finding[];
    note: string;
  };
  cases: A1Case[];
  joint_detail?: A1JointDetail;
  findings: A1Finding[];
}

export function a1ValueText(value: A1Value): string {
  return value.value === null || !Number.isFinite(value.value)
    ? 'Unavailable'
    : `${new Intl.NumberFormat('en', { maximumFractionDigits: 6 }).format(value.value)} ${value.unit}`.trim();
}

/** Only FastAPI's unmatched-route response permits the prepared A1 export. */
export function isMissingA1Route(status: number, detail: string): boolean {
  return status === 404 && detail === 'Not Found';
}

export function validateA1Snapshot(value: unknown): A1Snapshot {
  if (!value || typeof value !== 'object') throw new Error('A1 snapshot is not an object.');
  const candidate = value as Partial<A1Snapshot>;
  if (
    candidate.schema_version !== '1.0.0' ||
    candidate.identity?.candidate_id !== 'A1' ||
    candidate.identity.cad_revision !== null ||
    !candidate.identity.source_identity ||
    !candidate.identity.frame ||
    !candidate.identity.units ||
    !Array.isArray(candidate.generated_from) ||
    !candidate.geometry ||
    ![
      candidate.geometry.sleeve_length,
      candidate.geometry.sleeve_outer_diameter,
      candidate.geometry.sleeve_inner_diameter,
      candidate.geometry.upper_stop_station,
      candidate.geometry.axial_overlap,
      candidate.geometry.index_feature_count,
      candidate.geometry.retention_feature_count,
    ].every(
      (item) =>
        item &&
        (item.value === null || (typeof item.value === 'number' && Number.isFinite(item.value))) &&
        typeof item.unit === 'string' &&
        typeof item.state === 'string' &&
        typeof item.note === 'string',
    ) ||
    !Array.isArray(candidate.geometry.features) ||
    !candidate.geometry.features.every(
      (item) =>
        item &&
        typeof item.id === 'string' &&
        typeof item.label === 'string' &&
        typeof item.role === 'string' &&
        [item.start_mm, item.end_mm, item.inner_radius_mm, item.outer_radius_mm].every(
          (n) => n === null || (typeof n === 'number' && Number.isFinite(n)),
        ) &&
        Array.isArray(item.axes_deg) &&
        item.axes_deg.every((n) => typeof n === 'number' && Number.isFinite(n)) &&
        Array.isArray(item.widths_mm) &&
        item.widths_mm.every((n) => typeof n === 'number' && Number.isFinite(n)) &&
        Array.isArray(item.source_ids),
    ) ||
    !Array.isArray(candidate.fit_rows) ||
    !candidate.fit_rows.every(
      (item) =>
        item &&
        item.result &&
        (item.result.value === null ||
          (typeof item.result.value === 'number' && Number.isFinite(item.result.value))) &&
        Array.isArray(item.source_ids),
    ) ||
    !Array.isArray(candidate.paths) ||
    !candidate.paths.every(
      (item) => item && Array.isArray(item.sequence) && Array.isArray(item.source_ids),
    ) ||
    !Array.isArray(candidate.protected_volumes) ||
    !candidate.mass ||
    !candidate.mass.net_delta ||
    !Array.isArray(candidate.mass.ledger_rows) ||
    !Array.isArray(candidate.cases) ||
    !candidate.cases.every(
      (item) => item && Array.isArray(item.guide_results) && Array.isArray(item.source_ids),
    ) ||
    !Array.isArray(candidate.findings)
  )
    throw new Error('A1 snapshot version or source contract is incompatible.');
  return candidate as A1Snapshot;
}
