import assert from 'node:assert/strict';
import test from 'node:test';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import {
  analysisArtifactUrl,
  parseAnalysisCatalog,
  parseAnalysisManifest,
} from '../src/analysis/responseGuard.ts';
import { identityMismatch, validatePayload } from '../src/analysis/display.ts';

// Explicit synthetic software-only metadata, never a source of RP1 spatial fields.
function fixture() {
  const identity = {
    configuration_id: 'software-only',
    resolved_spec_sha256: 'a'.repeat(64),
    cad_revision_sha256: 'b'.repeat(64),
    part_shape_sha256: { part: 'c'.repeat(64) },
  };
  const field = {
    id: 'temperature',
    case_id: 'case',
    quantity: 'temperature',
    component: 'mean',
    units: 'K',
    association: 'part',
    part_ids: ['part'],
    sample_count: 1,
    times_s: [0, 1],
    artifact: 'fields/temperature.json',
    artifact_sha256: 'd'.repeat(64),
    coverage_notes: 'Synthetic one-part scalar software fixture',
    reported_extrema: {},
    evidence: {
      provenance: 'calculated',
      validation: 'unvalidated',
      assumptions: [],
      limits: [],
      sources: [],
      uncertainty: 'Fixture only',
      required_physical_tests: [],
    },
  };
  return {
    schema_version: 'rocket-twin.analysis.v1',
    flight_ready: false,
    api_id: 'software-only--run',
    run_id: 'run',
    identity,
    coordinate_frame: 'CAD_mm_registered_to_viewer_m',
    compatible: true,
    cases: { case: {} },
    fields: [field],
    artifacts: {
      [field.artifact]: '/api/analyses/software-only--run/artifacts/fields/temperature.json',
    },
    tools: {},
    input_sha256: {},
  };
}

test('catalog/manifest responses must match exact selected configuration and run', () => {
  const catalog = {
    vehicle_id: 'software-only',
    status: 'Recorded',
    analyses: [
      {
        id: 'software-only--run',
        run_id: 'run',
        compatible: true,
        manifest_url: '/api/analyses/software-only--run',
      },
    ],
  };
  assert.equal(parseAnalysisCatalog(catalog, 'software-only'), catalog);
  assert.throws(() => parseAnalysisCatalog(catalog, 'foreign'), /another configuration/);
  assert.throws(
    () => parseAnalysisCatalog({ ...catalog, analyses: null }, 'software-only'),
    /malformed/,
  );
  const manifest = fixture();
  assert.equal(parseAnalysisManifest(manifest, manifest.api_id, 'run'), manifest);
  assert.throws(
    () => parseAnalysisManifest({ ...manifest, api_id: 'foreign' }, manifest.api_id, 'run'),
    /selected analysis/,
  );
  assert.throws(
    () => parseAnalysisManifest({ ...manifest, run_id: 'foreign' }, manifest.api_id, 'run'),
    /selected analysis/,
  );
  assert.throws(
    () => parseAnalysisManifest(manifest, manifest.api_id, 'run', 'foreign'),
    /selected vehicle/,
  );
  assert.throws(
    () => parseAnalysisManifest({ ...manifest, fields: [{}] }, manifest.api_id, 'run'),
    /Recorded field/,
  );
  assert.throws(
    () =>
      parseAnalysisManifest(
        { ...manifest, fields: [manifest.fields[0], manifest.fields[0]] },
        manifest.api_id,
        'run',
      ),
    /duplicate/,
  );
});

test('matching absent source hashes never authorize geometry attachment', () => {
  const manifest = fixture();
  assert.equal(identityMismatch(manifest, 'software-only', manifest.identity), null);
  for (const key of ['resolved_spec_sha256', 'cad_revision_sha256']) {
    const missing = { ...manifest.identity, [key]: null };
    assert.notEqual(
      identityMismatch({ ...manifest, identity: missing }, 'software-only', missing),
      null,
    );
  }
  assert.match(
    identityMismatch(
      { ...manifest, identity: { ...manifest.identity, part_shape_sha256: {} } },
      'software-only',
      { ...manifest.identity, part_shape_sha256: {} },
    ),
    /unavailable/,
  );
  assert.match(
    identityMismatch({ ...manifest, identity: null }, 'software-only', manifest.identity),
    /unavailable/,
  );
});

test('artifact allowlist is scoped to the exact selected manifest, including nested recorded paths', () => {
  const manifest = fixture(),
    field = manifest.fields[0];
  assert.equal(analysisArtifactUrl(manifest, field), manifest.artifacts[field.artifact]);
  assert.throws(
    () =>
      analysisArtifactUrl(
        {
          ...manifest,
          artifacts: {
            [field.artifact]: '/api/analyses/foreign/artifacts/fields/temperature.json',
          },
        },
        field,
      ),
    /selected analysis/,
  );
  for (const artifact of [
    '../outside.json',
    '/absolute.json',
    'fields/%2e%2e/other.json',
    'field.json?source=foreign',
  ])
    assert.throws(() => analysisArtifactUrl(manifest, { ...field, artifact }), /allowlisted/);
});

test('valid zero and null gaps survive while malformed timestamps/units/coverage fail closed', () => {
  const manifest = fixture(),
    field = manifest.fields[0],
    payload = { part_ids: ['part'], values: [[0], [null]] };
  assert.doesNotThrow(() => validatePayload(field, payload));
  assert.deepEqual(payload.values, [[0], [null]]);
  for (const times_s of [[], [0, 0], [1, 0], [0, NaN]]) {
    assert.throws(() => validatePayload({ ...field, times_s }, payload), /sample times/);
    assert.throws(
      () =>
        parseAnalysisManifest(
          { ...manifest, fields: [{ ...field, times_s }] },
          manifest.api_id,
          'run',
        ),
      /timestamps/,
    );
  }
  assert.throws(() => validatePayload(field, null), /shape/);
  assert.throws(
    () =>
      parseAnalysisManifest(
        { ...manifest, fields: [{ ...field, units: 'Pa' }] },
        manifest.api_id,
        'run',
      ),
    /quantity\/units/,
  );
  const unavailable = {
    ...field,
    id: 'missing',
    times_s: null,
    sample_count: 0,
    artifact: null,
    artifact_sha256: null,
    unavailable_reason: 'No source samples exist',
    evidence: { ...field.evidence, provenance: 'unavailable', validation: 'unavailable' },
  };
  assert.doesNotThrow(() =>
    parseAnalysisManifest({ ...manifest, fields: [unavailable] }, manifest.api_id, 'run'),
  );
});

test('existing optional saved legacy manifests pass the response contract without regeneration', (t) => {
  const folder = resolve('../build/wo03-fin-nominal-fields/modular-performance-v1');
  if (!existsSync(folder))
    return t.skip('Optional saved analysis assets absent from this checkout');
  let checked = 0;
  for (const entry of readdirSync(folder)) {
    const path = resolve(folder, entry, 'analysis-record/manifest.json');
    if (!existsSync(path)) continue;
    const record = JSON.parse(readFileSync(path, 'utf8')),
      api_id = `${record.identity.configuration_id}--${record.run_id}`;
    const manifest = {
      ...record,
      api_id,
      compatible: false,
      incompatible_reason: 'Historical source retained',
      artifacts: Object.fromEntries(
        record.fields
          .filter((f) => f.artifact)
          .map((f) => [f.artifact, `/api/analyses/${api_id}/artifacts/${f.artifact}`]),
      ),
    };
    assert.equal(parseAnalysisManifest(manifest, api_id, record.run_id), manifest);
    checked++;
  }
  assert.ok(checked > 0);
});
