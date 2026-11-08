import type { AnalysisCatalog, AnalysisField, AnalysisManifest } from './types';

const object = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === 'object' && !Array.isArray(value);
const text = (value: unknown): value is string => typeof value === 'string' && value.length > 0;
const sha = (value: unknown): value is string =>
  typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const strings = (value: unknown): value is string[] =>
  Array.isArray(value) && value.every((item) => typeof item === 'string');

/** A foreign/malformed response is an error, never a prepared-field fallback. */
export function parseAnalysisCatalog(value: unknown, vehicleId: string): AnalysisCatalog {
  if (
    !object(value) ||
    value.vehicle_id !== vehicleId ||
    !Array.isArray(value.analyses) ||
    typeof value.status !== 'string' ||
    value.analyses.some(
      (entry) =>
        !object(entry) ||
        !text(entry.id) ||
        !text(entry.run_id) ||
        typeof entry.compatible !== 'boolean' ||
        entry.manifest_url !== `/api/analyses/${encodeURIComponent(entry.id)}`,
    )
  )
    throw new Error('Recorded analysis catalog is malformed or belongs to another configuration.');
  if (new Set(value.analyses.map((entry) => entry.id)).size !== value.analyses.length)
    throw new Error('Recorded analysis catalog contains ambiguous duplicate IDs.');
  return value as unknown as AnalysisCatalog;
}

export function parseAnalysisManifest(
  value: unknown,
  apiId: string,
  recordedRunId: string,
  configurationId?: string,
): AnalysisManifest {
  if (
    !object(value) ||
    value.api_id !== apiId ||
    value.run_id !== recordedRunId ||
    value.schema_version !== 'rocket-twin.analysis.v1' ||
    value.flight_ready !== false ||
    value.coordinate_frame !== 'CAD_mm_registered_to_viewer_m' ||
    typeof value.compatible !== 'boolean' ||
    !object(value.identity) ||
    !object(value.cases) ||
    !Array.isArray(value.fields) ||
    !object(value.artifacts) ||
    !object(value.tools) ||
    !object(value.input_sha256)
  )
    throw new Error(
      'Recorded manifest is malformed or does not match the selected analysis/run identity.',
    );
  const identity = value.identity;
  if (configurationId !== undefined && identity.configuration_id !== configurationId)
    throw new Error('Recorded manifest configuration does not match the selected vehicle.');
  if (
    (value.incompatible_reason != null && typeof value.incompatible_reason !== 'string') ||
    (value.engineering_notice != null && typeof value.engineering_notice !== 'string') ||
    Object.values(value.cases).some((item) => !object(item))
  )
    throw new Error('Recorded manifest case/reason metadata is malformed.');
  if (
    !text(identity.configuration_id) ||
    !sha(identity.resolved_spec_sha256) ||
    !sha(identity.cad_revision_sha256) ||
    !object(identity.part_shape_sha256) ||
    !Object.values(identity.part_shape_sha256).every(sha)
  )
    throw new Error(
      'Recorded manifest lacks exact specification/CAD/part-shape source fingerprints.',
    );
  const shapeIds = identity.part_shape_sha256;
  const fields = value.fields;
  const units = { temperature: 'K', stress: 'Pa', displacement: 'm', design_margin: '1' };
  for (const field of fields) {
    if (
      !object(field) ||
      !text(field.id) ||
      !text(field.case_id) ||
      !Object.hasOwn(value.cases, field.case_id) ||
      !text(field.quantity) ||
      !(field.quantity in units) ||
      field.units !== units[field.quantity as keyof typeof units] ||
      !strings(field.part_ids) ||
      !field.part_ids.length ||
      new Set(field.part_ids).size !== field.part_ids.length ||
      field.part_ids.some((id) => !sha(shapeIds[id])) ||
      !Number.isInteger(field.sample_count) ||
      (field.sample_count as number) < 0 ||
      typeof field.component !== 'string' ||
      typeof field.coverage_notes !== 'string' ||
      !object(field.reported_extrema) ||
      !['part', 'node', 'element', 'integration_point', 'measured_point'].includes(
        String(field.association),
      ) ||
      !object(field.evidence)
    )
      throw new Error(
        'Recorded field has invalid quantity/units, case, coverage or evidence metadata.',
      );
    const evidence = field.evidence;
    if (
      !['calculated', 'estimated', 'measured', 'unavailable'].includes(
        String(evidence.provenance),
      ) ||
      ![
        'unvalidated',
        'numerically_verified',
        'physically_validated',
        'failed',
        'unavailable',
      ].includes(String(evidence.validation)) ||
      !strings(evidence.assumptions) ||
      !strings(evidence.limits) ||
      !strings(evidence.sources) ||
      !strings(evidence.required_physical_tests) ||
      typeof evidence.uncertainty !== 'string'
    )
      throw new Error(`Recorded field ${field.id} lacks readable provenance/validation metadata.`);
    if (
      field.times_s !== null &&
      (!Array.isArray(field.times_s) ||
        !field.times_s.length ||
        field.times_s.some(
          (time, index, times) =>
            typeof time !== 'number' ||
            !Number.isFinite(time) ||
            (index > 0 && time <= times[index - 1]),
        ))
    )
      throw new Error(`Recorded field ${field.id} has invalid exact sample timestamps.`);
    if (
      (evidence.provenance === 'unavailable' && evidence.validation !== 'unavailable') ||
      (evidence.provenance === 'measured' && field.association !== 'measured_point') ||
      (field.association === 'part' &&
        field.sample_count !== 0 &&
        field.sample_count !== field.part_ids.length) ||
      (field.quantity === 'design_margin' && !text(field.margin_definition)) ||
      (evidence.provenance !== 'unavailable' &&
        field.association !== 'part' &&
        (!sha(field.mesh_sha256) || !object(field.registration)))
    )
      throw new Error(
        `Recorded field ${field.id} has inconsistent evidence, sample association or engineering criterion metadata.`,
      );
    if (evidence.provenance === 'unavailable') {
      if (!text(field.unavailable_reason) || field.sample_count !== 0 || field.artifact)
        throw new Error(
          `Unavailable field ${field.id} must carry a reason and no fabricated samples.`,
        );
    } else if (!text(field.artifact) || !sha(field.artifact_sha256) || field.sample_count === 0)
      throw new Error(`Recorded field ${field.id} lacks a hashed artifact or sample coverage.`);
  }
  if (new Set(fields.map((field) => field.id)).size !== fields.length)
    throw new Error('Recorded manifest contains ambiguous duplicate field IDs.');
  return value as unknown as AnalysisManifest;
}

/** An artifact belongs to this exact manifest, not merely a global API prefix. */
export function analysisArtifactUrl(manifest: AnalysisManifest, field: AnalysisField): string {
  const asset = field.artifact;
  if (
    !asset ||
    asset.startsWith('/') ||
    /[\\?#%]/.test(asset) ||
    asset.split('/').some((part) => !part || part === '.' || part === '..')
  )
    throw new Error('No allowlisted recorded field artifact is available.');
  const expected = `/api/analyses/${encodeURIComponent(manifest.api_id)}/artifacts/${asset}`;
  if (manifest.artifacts[asset] !== expected)
    throw new Error('Recorded artifact URL does not belong to the selected analysis identity.');
  return expected;
}
