import type { JsonValue } from '../types';

export interface AnalysisIdentity {
  configuration_id: string;
  resolved_spec_sha256: string;
  cad_revision_sha256: string;
  part_shape_sha256: Record<string, string>;
}
export interface AnalysisCatalog {
  vehicle_id: string;
  status: string;
  analyses: {
    id: string;
    run_id: string;
    engineering_notice: string | null;
    compatible: boolean;
    incompatible_reason: string | null;
    manifest_url: string;
    quantities: string[];
    cases: Record<string, JsonValue>;
  }[];
}
export interface AnalysisEvidence {
  provenance: 'calculated' | 'estimated' | 'measured' | 'unavailable';
  validation: string;
  assumptions: string[];
  limits: string[];
  sources: string[];
  uncertainty: string;
  required_physical_tests: string[];
  known_case_verified: boolean;
  mesh_converged: boolean;
  report: string | null;
}
export type Quantity = 'temperature' | 'stress' | 'displacement' | 'design_margin';
export interface AnalysisField {
  id: string;
  case_id: string;
  quantity: Quantity;
  component: string;
  units: 'K' | 'Pa' | 'm' | '1';
  association: 'part' | 'node' | 'element' | 'integration_point' | 'measured_point';
  part_ids: string[];
  evidence: AnalysisEvidence;
  times_s: number[] | null;
  artifact: string | null;
  artifact_sha256: string | null;
  sample_count: number;
  unavailable_reason: string | null;
  mesh_sha256: string | null;
  registration: {
    type: string;
    matrix: number[][];
    source_frame: string;
    target_frame: string;
  } | null;
  reported_extrema: Record<string, JsonValue>;
  margin_definition: string | null;
  coverage_notes: string;
}
export interface AnalysisManifest {
  schema_version: string;
  run_id: string;
  api_id: string;
  engineering_notice: string | null;
  compatible: boolean;
  incompatible_reason: string | null;
  identity: AnalysisIdentity;
  coordinate_frame: string;
  cases: Record<string, Record<string, JsonValue>>;
  fields: AnalysisField[];
  tools: Record<string, string>;
  artifacts: Record<string, string>;
  input_sha256: Record<string, string>;
  flight_ready: false;
}
export interface AnalysisPayload {
  values: (number | null)[][];
  part_ids?: string[];
  resolution?: string;
  analysis_mesh?: {
    frame: string;
    part_id: string;
    coverage: string;
    nodes: { id: number; xyz_mm: [number, number, number] }[];
    elements: { id: number; type: string; nodes: number[] }[];
  };
}
