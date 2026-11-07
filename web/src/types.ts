export type Vector3Tuple = [number, number, number];
export type JsonValue =
  string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

export interface CatalogEntry {
  id: string;
  name: string;
  label?: string;
  role?: string;
  status?: string;
  candidate?: boolean;
  design_status?: string;
  group?: string;
  description?: string;
  available?: boolean;
}

export interface Catalog {
  default_design_id?: string;
  vehicles: CatalogEntry[];
  status: string;
  candidates: CatalogEntry[];
  candidate_message?: string;
}

export interface Part {
  id: string;
  name?: string;
  type: string;
  parent: string | null;
  position_m?: number;
  function?: string;
  location?: {
    position_m: number;
    cg_station_m?: number;
    lateral_offset_m?: [number, number];
    explode_offset?: number;
  };
  material: string;
  mass_kg?: number;
  subtree_mass_kg?: number;
  cad_mass_kg?: number;
  cad_mass?: { mass_kg?: number; basis?: string; cg_local_body_m?: Vector3Tuple };
  geometry?: Record<string, JsonValue>;
  dimensions?: Record<string, JsonValue>;
  cad_bounding_size_mm?: number[];
  electrical?: Record<string, JsonValue> | null;
  learn: string;
  cite?: string | null;
  estimate?: boolean;
  build?: { method: string; generator: string; notes: string; cost_usd?: number } | null;
  cad?: {
    color?: string;
    role?: string;
    mass_basis?: string;
    notes?: string;
    generator?: string;
  } | null;
  engineering?: {
    function: string;
    material_profile?: string;
    tolerances_mm?: Record<string, number>;
    load_cases?: string[];
    thermal_cases?: string[];
    service_notes?: string;
    property_basis?: string;
    required_physical_verification?: string[];
  } | null;
  mesh_url?: string | null;
  viewer_center_m?: Vector3Tuple;
  explode_offset?: number;
  outer_body?: boolean;
  nose?: boolean;
  source?: {
    spec?: string;
    cad?: string;
    spec_path?: string;
    cad_generator?: string;
    shape_sha256?: string;
    spec_inputs?: { path: string; sha256: string }[];
  };
  manufacturing?: JsonValue;
  evidence_status?: JsonValue;
  mass_basis?: string;
  representation?: JsonValue;
  color?: string;
  raw?: Record<string, JsonValue>;
  evidence?: Record<string, JsonValue>;
  connections?: JsonValue[];
  requirements?: JsonValue[];
  fmea_records?: JsonValue[];
  failure_modes?: string[];
}

export interface MassSample {
  recorded_case_label?: string;
  burn_fraction?: number;
  mass_kg?: number;
  total_mass_kg?: number;
  cg_m?: number | Vector3Tuple;
  cp_m?: number;
  stability_margin_cal?: number;
}

export interface InspectionDocument {
  snapshot_only?: boolean;
  id: string;
  name?: string;
  label?: string;
  role?: string;
  status?: string;
  description?: string;
  identity?: Record<string, JsonValue>;
  geometry?: { length_m?: number; diameter_m?: number; overall_length_m?: number };
  airframe?: Record<string, JsonValue>;
  parts: Part[];
  summary: Record<string, JsonValue>;
  evidence?: Record<string, JsonValue>;
  engineering_open?: string[];
  motor?: Record<string, JsonValue> | null;
  mass_samples?: MassSample[];
  candidates?: CatalogEntry[];
  mesh_frame?: string;
  checks?: JsonValue;
  findings?: JsonValue;
  analysis_status?: JsonValue;
}
