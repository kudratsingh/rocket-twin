import type { BudgetCase, EvidenceState, JointDetail, SourceRef, WorkbenchDocument } from './types';

export type ExtensionMode =
  'comparison' | 'recovery' | 'thermal' | 'electrical' | 'assembly' | 'requirements';
export interface RecordedQuantity {
  label: string;
  value: number | null;
  unit: string;
  state: EvidenceState;
}
export interface LinkedItem {
  id: string;
  label: string;
  state: EvidenceState;
  part_ids: string[];
  source_ids: string[];
  note: string;
}
export interface ExtensionNode extends LinkedItem {
  kind?: string;
  quantities?: RecordedQuantity[];
}
export interface ExtensionEdge extends ExtensionNode {
  from: string;
  to: string;
}
export interface ExtensionGraph {
  id: string;
  label: string;
  state: EvidenceState;
  configuration_id: string;
  compatible_with_c1: boolean;
  note: string;
  source_ids: string[];
  nodes: ExtensionNode[];
  edges: ExtensionEdge[];
}
export interface ExtensionStep extends Omit<LinkedItem, 'note'> {
  description: string;
}
export interface CandidateRecord extends Omit<LinkedItem, 'note'> {
  active: false;
  stop_reason: string;
  stop_joint_ids?: string[];
  net_added_mass_g: number | null;
  full_intrinsic_inertia: null;
  cases: Omit<BudgetCase, 'state' | 'added_mass_g'>[];
  quantities: RecordedQuantity[];
}
export interface HistoryRecord extends Omit<LinkedItem, 'part_ids'> {
  configuration_id: string;
  candidate_identity: string | null;
  cad_revision: string | null;
  compatible_with_c1: false;
  kind: string;
  metrics: RecordedQuantity[];
}
export interface ElectricalNet {
  id: string;
  net: string;
  from: string;
  to: string[];
  gauge_awg: number | null;
  pin: string | null;
  state: EvidenceState;
  part_ids: string[];
  source_ids: string[];
  note: string;
}
export interface ExtendedDocument {
  schema_version: string;
  id: string;
  label: string;
  status: string;
  identity: WorkbenchDocument['identity'];
  generated_from: SourceRef[];
  candidate_comparison: CandidateRecord[];
  recovery: {
    topology: ExtensionGraph;
    opening_assumptions: RecordedQuantity[];
    packing_steps: ExtensionStep[];
    extraction_steps: ExtensionStep[];
    notes: string[];
  };
  thermal: {
    topology: ExtensionGraph;
    current_interfaces: ExtensionGraph;
    materials: (LinkedItem & { properties: RecordedQuantity[] })[];
    openings: (LinkedItem & { dimensions: RecordedQuantity[] })[];
    history: HistoryRecord[];
    compatible_spatial_field: null;
    notes: string[];
  };
  electrical: {
    topology: ExtensionGraph;
    nets: ElectricalNet[];
    power_independence: string[];
    control_blocks: ExtensionGraph;
  };
  assembly: { joints: JointDetail[]; steps: ExtensionStep[]; notes: string[] };
  requirements: ExtensionGraph;
}
export function quantityText(quantity: Pick<RecordedQuantity, 'value' | 'unit'>): string {
  return quantity.value === null || !Number.isFinite(quantity.value)
    ? `Unavailable${quantity.unit ? ` (${quantity.unit})` : ''}`
    : `${new Intl.NumberFormat('en', { maximumFractionDigits: 9 }).format(quantity.value)}${quantity.unit ? ` ${quantity.unit}` : ''}`;
}
export function firstAvailablePart(
  ids: string[],
  availableIds: ReadonlySet<string>,
): string | null {
  return ids.find((id) => availableIds.has(id)) ?? null;
}
export function compatibleExtension(
  base: WorkbenchDocument['identity'],
  extended: ExtendedDocument['identity'],
): boolean {
  return (
    base.configuration_id === extended.configuration_id &&
    base.specification_sha256 === extended.specification_sha256 &&
    base.cad_revision === extended.cad_revision
  );
}
