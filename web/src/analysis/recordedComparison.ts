import { fieldBlockReason, validatePayload } from './display';
import type { AnalysisField, AnalysisManifest, AnalysisPayload } from './types';

export interface RecordedComparisonSource {
  manifest: AnalysisManifest;
  field: AnalysisField;
  payload: AnalysisPayload;
}

export interface RecordedComparisonOptions {
  leftSample?: number;
  rightSample?: number;
  /** Shared fixed limits in the original field units; never inferred from samples. */
  legend?: readonly [number, number];
}

export interface RecordedComparisonRow {
  sampleId: string;
  left: number | null;
  right: number | null;
  /** Display subtraction of the selected recorded samples, right minus left. */
  difference: number | null;
}

export interface RecordedComparisonModel {
  status: 'unavailable' | 'incompatible' | 'compatible';
  reasons: string[];
  left: RecordedComparisonSource | null;
  right: RecordedComparisonSource | null;
  leftSample: number;
  rightSample: number;
  leftTime: number | null;
  rightTime: number | null;
  legend: readonly [number, number] | null;
  rows: RecordedComparisonRow[];
  /** This comparison is a table, never a geometry-attachment authorization. */
  geometryAttachment: false;
}

function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  if (value && typeof value === 'object')
    return `{${Object.entries(value)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, item]) => `${JSON.stringify(key)}:${stable(item)}`)
      .join(',')}}`;
  return JSON.stringify(value) ?? 'undefined';
}

const nonempty = (value: unknown): value is string => typeof value === 'string' && value.length > 0;
const defaults: Record<AnalysisField['units'], readonly [number, number]> = {
  K: [273.15, 573.15],
  Pa: [0, 25e6],
  m: [0, 0.005],
  '1': [-1, 3],
};

function sourceProblems(source: RecordedComparisonSource, name: string): string[] {
  const { manifest, field, payload } = source;
  const reasons: string[] = [];
  const expectedUnits = { temperature: 'K', stress: 'Pa', displacement: 'm', design_margin: '1' };
  if (field.units !== expectedUnits[field.quantity])
    reasons.push(`${name}: quantity and original units disagree.`);
  if (!manifest.compatible)
    reasons.push(`${name}: ${manifest.incompatible_reason || 'manifest is incompatible'}`);
  const identity = manifest.identity;
  if (
    !identity ||
    ![identity.configuration_id, identity.resolved_spec_sha256, identity.cad_revision_sha256].every(
      nonempty,
    )
  )
    reasons.push(
      `${name}: exact configuration, resolved specification and CAD identity are required.`,
    );
  const shapes = identity?.part_shape_sha256;
  if (!shapes || !Object.keys(shapes).length || !Object.values(shapes).every(nonempty))
    reasons.push(`${name}: complete part shape fingerprints are unavailable.`);
  if (
    !manifest.fields.some(
      (entry) =>
        entry.id === field.id && entry.case_id === field.case_id && stable(entry) === stable(field),
    )
  )
    reasons.push(`${name}: selected field is not the exact field registered in this manifest.`);
  if (!Object.hasOwn(manifest.cases, field.case_id))
    reasons.push(`${name}: recorded case is not registered.`);
  if (
    !field.part_ids.length ||
    new Set(field.part_ids).size !== field.part_ids.length ||
    field.part_ids.some((id) => !nonempty(shapes?.[id]))
  )
    reasons.push(`${name}: unique part coverage must map to the manifest shape identities.`);
  if (
    !nonempty(field.artifact) ||
    !nonempty(field.artifact_sha256) ||
    !nonempty(manifest.artifacts[field.artifact ?? ''])
  )
    reasons.push(`${name}: recorded artifact identity is unavailable.`);
  const blocked = fieldBlockReason(field);
  if (blocked) reasons.push(`${name}: ${blocked}`);
  if (
    field.times_s &&
    (!field.times_s.length ||
      field.times_s.some(
        (time, index, times) => !Number.isFinite(time) || (index > 0 && time <= times[index - 1]),
      ))
  )
    reasons.push(`${name}: solver sample times must be finite, unique and increasing.`);
  try {
    validatePayload(field, payload);
  } catch (error) {
    reasons.push(`${name}: ${error instanceof Error ? error.message : 'invalid recorded payload'}`);
  }
  return reasons;
}

/** Compare only registered recorded samples. No resampling, interpolation or spatial inference. */
export function compareRecordedCases(
  left: RecordedComparisonSource | null,
  right: RecordedComparisonSource | null,
  options: RecordedComparisonOptions = {},
): RecordedComparisonModel {
  const leftSample = options.leftSample ?? 0,
    rightSample = options.rightSample ?? 0;
  const model: RecordedComparisonModel = {
    status: 'unavailable',
    reasons: [],
    left,
    right,
    leftSample,
    rightSample,
    leftTime: null,
    rightTime: null,
    legend: null,
    rows: [],
    geometryAttachment: false,
  };
  if (!left || !right) {
    model.reasons = [
      'Two eligible recorded fields and their exact payloads are required. No eligible pair is supplied; no comparison or spatial field is fabricated.',
    ];
    return model;
  }
  const reasons = [...sourceProblems(left, 'Left'), ...sourceProblems(right, 'Right')];
  const a = left.manifest.identity,
    b = right.manifest.identity;
  for (const key of [
    'configuration_id',
    'resolved_spec_sha256',
    'cad_revision_sha256',
    'part_shape_sha256',
  ] as const)
    if (stable(a?.[key]) !== stable(b?.[key]))
      reasons.push(`Configuration/specification/CAD/part-shape compatibility failed: ${key}.`);
  for (const key of [
    'quantity',
    'component',
    'units',
    'association',
    'margin_definition',
    'coverage_notes',
  ] as const)
    if (stable(left.field[key]) !== stable(right.field[key]))
      reasons.push(`Recorded field compatibility failed: ${key}.`);
  if (left.manifest.coordinate_frame !== right.manifest.coordinate_frame)
    reasons.push('Recorded coordinate frames differ.');
  if (stable([...left.field.part_ids].sort()) !== stable([...right.field.part_ids].sort()))
    reasons.push('Recorded part coverage differs; uncovered regions cannot be compared.');
  if (left.field.sample_count !== right.field.sample_count)
    reasons.push('Recorded sample coverage differs.');
  if (left.field.association !== 'part') {
    if (
      !nonempty(left.field.mesh_sha256) ||
      left.field.mesh_sha256 !== right.field.mesh_sha256 ||
      stable(left.field.registration) !== stable(right.field.registration) ||
      stable(left.payload.analysis_mesh) !== stable(right.payload.analysis_mesh)
    )
      reasons.push(
        'Spatial comparison requires the same recorded mesh, topology, coverage and registration.',
      );
  }
  const legend = options.legend ?? defaults[left.field.units];
  if (!legend || !legend.every(Number.isFinite) || legend[1] <= legend[0])
    reasons.push('A finite increasing shared fixed legend in the recorded units is required.');
  if (reasons.length) {
    model.status = 'incompatible';
    model.reasons = reasons;
    return model;
  }
  model.legend = [...legend] as [number, number];
  for (const [name, source, sample] of [
    ['Left', left, leftSample],
    ['Right', right, rightSample],
  ] as const)
    if (!Number.isInteger(sample) || sample < 0 || sample >= source.payload.values.length)
      model.reasons.push(
        `${name}: requested exact sample is unavailable; no nearest-time substitution.`,
      );
  if (model.reasons.length) return model;
  model.leftTime = left.field.times_s?.[leftSample] ?? null;
  model.rightTime = right.field.times_s?.[rightSample] ?? null;
  model.status = 'compatible';
  model.rows = left.payload.values[leftSample].map((value, index) => {
    const sampleId =
      left.field.association === 'part'
        ? left.field.part_ids[index]
        : `${left.field.association}:${
            left.field.association === 'node'
              ? left.payload.analysis_mesh!.nodes[index].id
              : left.payload.analysis_mesh!.elements[index].id
          }`;
    const otherIndex =
      left.field.association === 'part' ? right.field.part_ids.indexOf(sampleId) : index;
    const other = right.payload.values[rightSample][otherIndex];
    return {
      sampleId,
      left: value,
      right: other,
      difference: value === null || other === null ? null : other - value,
    };
  });
  return model;
}

function csvCell(value: string | number | null) {
  if (value === null) return '';
  // Preserve numbers (including zero and negatives); source labels must not become formulas.
  const text =
    typeof value === 'number' ? String(value) : /^[=+@-]/.test(value) ? `'${value}` : value;
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

/** Bounded to the explicitly selected sample on each side; source values retain original units. */
export function recordedComparisonCsv(model: RecordedComparisonModel): string {
  const sourceHeaders = [
    'configuration_id',
    'resolved_spec_sha256',
    'cad_revision_sha256',
    'part_shape_sha256',
    'run_id',
    'api_id',
    'field_id',
    'case_id',
    'quantity',
    'component',
    'units',
    'association',
    'mesh_sha256',
    'artifact_sha256',
    'sample_index',
    'exact_time_s',
    'validation',
    'provenance',
  ];
  const metadata = (
    source: RecordedComparisonSource | null,
    sample: number,
    time: number | null,
  ) =>
    source
      ? [
          source.manifest.identity.configuration_id,
          source.manifest.identity.resolved_spec_sha256,
          source.manifest.identity.cad_revision_sha256,
          stable(source.manifest.identity.part_shape_sha256),
          source.manifest.run_id,
          source.manifest.api_id,
          source.field.id,
          source.field.case_id,
          source.field.quantity,
          source.field.component,
          source.field.units,
          source.field.association,
          source.field.mesh_sha256,
          source.field.artifact_sha256,
          sample,
          time,
          source.field.evidence.validation,
          source.field.evidence.provenance,
        ]
      : sourceHeaders.map(() => null);
  const header = [
    'comparison_status',
    'reason',
    'geometry_attachment',
    'legend_min',
    'legend_max',
    ...sourceHeaders.map((name) => `left_${name}`),
    ...sourceHeaders.map((name) => `right_${name}`),
    'sample_id',
    'left_value',
    'right_value',
    'right_minus_left',
    'value_status',
  ];
  const prefix = [
    model.status,
    model.reasons.join(' | '),
    'never attached',
    model.legend?.[0] ?? null,
    model.legend?.[1] ?? null,
    ...metadata(model.left, model.leftSample, model.leftTime),
    ...metadata(model.right, model.rightSample, model.rightTime),
  ];
  const rows = model.rows.length
    ? model.rows.map((row) => [
        ...prefix,
        row.sampleId,
        row.left,
        row.right,
        row.difference,
        row.left === null || row.right === null ? 'unavailable gap' : 'recorded samples',
      ])
    : [[...prefix, null, null, null, null, 'unavailable']];
  return [header, ...rows].map((row) => row.map(csvCell).join(',')).join('\r\n') + '\r\n';
}
