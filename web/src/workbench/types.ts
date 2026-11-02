export type EvidenceState =
  'calculated' | 'estimated' | 'measured' | 'unavailable' | 'failed' | 'historical' | 'superseded';
export type GeometryMaturity = 'detailed_cad' | 'envelope' | 'concept' | 'undefined';
export interface SourceRef {
  id: string;
  path: string;
  sha256: string;
  description: string;
}
export interface WorkbenchPart {
  id: string;
  label: string;
  source_part_ids: string[];
  subsystem: string;
  function: string;
  material: string;
  manufacturing: string;
  mass_g: number | null;
  mass_basis: string;
  geometry_maturity: GeometryMaturity;
  state: EvidenceState;
  shape: 'shell' | 'ring' | 'fin' | 'motor' | 'box' | 'harness' | 'envelope';
  start_mm: number | null;
  length_mm: number | null;
  radius_mm: number | null;
  inner_radius_mm?: number | null;
  thickness_mm?: number | null;
  span_mm?: number;
  root_chord_mm?: number;
  tip_chord_mm?: number;
  sweep_mm?: number;
  azimuth_deg?: number[];
  source_ids: string[];
  connections: string[];
  findings: string[];
}
export interface JointDetail {
  id: string;
  label: string;
  kind: 'fin_root' | 'recovery' | 'receiver_end' | 'motor' | 'compartment';
  part_ids: string[];
  description: string;
  state: EvidenceState;
  source_ids: string[];
  dimensions: { label: string; value: number | null; unit: string; state: EvidenceState }[];
  layers: {
    label: string;
    material: string;
    thickness_mm: number | null;
    part_id: string;
    state: EvidenceState;
  }[];
  findings: string[];
  assembly_steps: string[];
}
export interface PathNode {
  id: string;
  part_id: string | null;
  label: string;
  state: EvidenceState;
  note: string;
}
export interface PathEdge {
  id: string;
  from: string;
  to: string;
  label: string;
  part_ids: string[];
  state: EvidenceState;
  value: number | null;
  unit: string;
  note: string;
  source_ids: string[];
}
export interface LoadPath {
  id: string;
  label: string;
  case_id: string;
  description: string;
  state: EvidenceState;
  nodes: PathNode[];
  edges: PathEdge[];
  assumptions: string[];
  source_ids: string[];
  free_body: {
    part_id: string;
    label: string;
    arrows: {
      label: string;
      direction: 'up' | 'down' | 'left' | 'right' | 'moment';
      value: number | null;
      unit: string;
      state: EvidenceState;
    }[];
    supports: string[];
  };
}
export interface BudgetCase {
  id: string;
  label: string;
  state: EvidenceState;
  total_g: number;
  nominal_g: number;
  growth_g: number;
  extra_aft_g: number;
  cg_mm: number;
  cp_mm: number;
  burnout_cg_mm: number;
  loaded_margin_cal: number;
  burnout_margin_cal: number;
  recovery_force_n: number;
  added_mass_g: number;
  formal_headroom_g: number;
  planning_headroom_g: number;
  source_ids: string[];
  findings: string[];
  guide_results: {
    usable_m: number;
    speed_mps: number;
    formal_margin_mps: number;
    planning_margin_mps: number;
  }[];
}
export interface WorkbenchDocument {
  revision_mass_changes?: {
    id: string;
    revision: string;
    label: string;
    mass_g: number;
    station_mm: number;
    part_ids: string[];
    state: EvidenceState;
  }[];
  criteria?: {
    minimum_static_margin_cal: number;
    service_tip_limit_mm: number;
    hot_bond_shear_screen_mpa: number;
  };
  schema_version: string;
  id: string;
  label: string;
  status: string;
  generated_from: SourceRef[];
  identity: {
    configuration_id: string;
    specification_sha256: string;
    cad_revision: string | null;
    frame: string;
    units: string;
    status: string;
  };
  arrangement: {
    overall_length_mm: number;
    body_diameter_mm: number;
    nose_length_mm: number;
    reference: string;
    subsystem_ranges: { id: string; label: string; start_mm: number; end_mm: number }[];
  };
  parts: WorkbenchPart[];
  joints: JointDetail[];
  load_paths: LoadPath[];
  cases: BudgetCase[];
  mass_distribution: {
    id: string;
    label: string;
    station_mm: number;
    mass_g: number;
    subsystem: string;
    state: EvidenceState;
    part_id: string | null;
  }[];
  mass_groups: {
    id: string;
    label: string;
    mass_g: number;
    state: EvidenceState;
    part_ids: string[];
  }[];
  launch: {
    baseline_usable_m: number;
    formal_mps: number;
    planning_mps: number;
    equipment_confirmed: boolean;
    upper_guide_front_mm: number;
    lower_guide_front_mm: number;
    guide_length_mm: number;
    assumed_pad_offset_mm: number;
    illustrative_overall_mm: number;
    illustrative_usable_mm: number;
    hardware_status: string;
    assumptions: string[];
    source_ids: string[];
  };
  inventory: {
    id: string;
    label: string;
    category: 'frontend_code' | 'report_only' | 'export_needed' | 'engineering_missing';
    browser_verified: boolean;
    note: string;
  }[];
  gaps: {
    id: string;
    label: string;
    state: EvidenceState;
    part_ids: string[];
    next_verification: string;
    source_ids: string[];
  }[];
  historical_candidates: {
    id: string;
    label: string;
    state: EvidenceState;
    reason: string;
    source_ids: string[];
  }[];
}
