import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

// Every value and digest below is a synthetic software fixture, never engineering evidence.
function source(label = 'A') {
  const field = {
    id: `fixture-field-${label}`,
    case_id: `fixture-case-${label}`,
    quantity: 'stress',
    component: 'xx',
    units: 'Pa',
    association: 'part',
    part_ids: ['a', 'b'],
    times_s: [0, 1, 2],
    artifact: 'field.json',
    artifact_sha256: `fixture-artifact-${label}`,
    sample_count: 2,
    unavailable_reason: null,
    mesh_sha256: null,
    registration: null,
    reported_extrema: {},
    margin_definition: null,
    coverage_notes: 'Exact two-part synthetic scalar coverage.',
    evidence: {
      provenance: 'calculated',
      validation: 'software-fixture-only',
      assumptions: [],
      limits: [],
      sources: [],
      uncertainty: 'Synthetic fixture; not physical evidence',
      required_physical_tests: [],
      known_case_verified: false,
      mesh_converged: false,
      report: null,
    },
  };
  const manifest = {
    schema_version: 'fixture',
    run_id: `fixture-run-${label}`,
    api_id: `fixture-api-${label}`,
    engineering_notice: 'Synthetic software fixture only',
    compatible: true,
    incompatible_reason: null,
    identity: {
      configuration_id: 'fixture-config',
      resolved_spec_sha256: 'fixture-spec',
      cad_revision_sha256: 'fixture-cad',
      part_shape_sha256: { a: 'fixture-shape-a', b: 'fixture-shape-b' },
    },
    coordinate_frame: 'fixture-frame',
    cases: { [field.case_id]: {} },
    fields: [field],
    tools: {},
    artifacts: { 'field.json': `/api/analyses/fixture-${label}/field` },
    input_sha256: {},
    flight_ready: false,
  };
  return {
    manifest,
    field,
    payload: {
      part_ids: ['a', 'b'],
      values: [
        [0, null],
        [10, 3],
        [null, 4],
      ],
    },
  };
}

async function modules(run) {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const pure = await server.ssrLoadModule('/src/analysis/recordedComparison.ts');
    const component = await server.ssrLoadModule('/src/analysis/RecordedCaseComparison.tsx');
    await run({ ...pure, ...component });
  } finally {
    await server.close();
  }
}

function parseCsv(text) {
  const rows = [];
  let row = [],
    cell = '',
    quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') {
      if (quoted && text[i + 1] === '"') {
        cell += '"';
        i++;
      } else quoted = !quoted;
    } else if (c === ',' && !quoted) {
      row.push(cell);
      cell = '';
    } else if (c === '\n' && !quoted) {
      row.push(cell.replace(/\r$/, ''));
      rows.push(row);
      row = [];
      cell = '';
    } else cell += c;
  }
  return rows
    .slice(1)
    .map((values) => Object.fromEntries(rows[0].map((key, index) => [key, values[index]])));
}

test('synthetic scalar comparison preserves zero/gaps, matches reordered part coverage and uses independent exact clocks', async () => {
  await modules(({ compareRecordedCases, recordedComparisonCsv }) => {
    const left = source(),
      right = source('B');
    right.field.part_ids = ['b', 'a'];
    right.payload.part_ids = ['b', 'a'];
    right.field.times_s = [0, 0.5, 7];
    right.payload.values = [
      [1, 4],
      [2, 8],
      [null, 9],
    ];
    const before = JSON.stringify({ left, right });
    const model = compareRecordedCases(left, right);
    assert.equal(model.status, 'compatible');
    assert.equal(model.geometryAttachment, false);
    assert.deepEqual(model.rows, [
      { sampleId: 'a', left: 0, right: 4, difference: 4 },
      { sampleId: 'b', left: null, right: 1, difference: null },
    ]);
    assert.deepEqual(model.legend, [0, 25e6]);
    const selected = compareRecordedCases(left, right, {
      leftSample: 2,
      rightSample: 1,
      legend: [-20, 20],
    });
    assert.equal(selected.leftTime, 2);
    assert.equal(selected.rightTime, 0.5);
    assert.equal(selected.rows[0].left, null);
    assert.equal(selected.rows[0].difference, null);
    const rows = parseCsv(recordedComparisonCsv(selected));
    assert.equal(rows.length, 2);
    assert.equal(rows[0].left_exact_time_s, '2');
    assert.equal(rows[0].right_exact_time_s, '0.5');
    assert.equal(rows[0].left_units, 'Pa');
    assert.equal(rows[0].left_resolved_spec_sha256, 'fixture-spec');
    assert.equal(rows[0].right_artifact_sha256, 'fixture-artifact-B');
    assert.equal(rows[0].left_value, '');
    assert.equal(rows[0].right_minus_left, '');
    assert.equal(rows[0].value_status, 'unavailable gap');
    assert.equal(parseCsv(recordedComparisonCsv(model))[0].left_value, '0');
    assert.equal(JSON.stringify({ left, right }), before);
    const unavailable = compareRecordedCases(left, right, { leftSample: 99 });
    assert.equal(unavailable.status, 'unavailable');
    assert.deepEqual(unavailable.rows, []);
    assert.match(unavailable.reasons.join(' '), /no nearest-time substitution/);
    const differentFrame = compareRecordedCases(left, right, { leftSample: 1, rightSample: 2 });
    assert.deepEqual(
      differentFrame.legend,
      model.legend,
      'legend must not auto-stretch across samples',
    );
  });
});

test('configuration/spec/CAD/shape, registered field, component/units/association/coverage mismatches block every difference and attachment', async () => {
  await modules(({ compareRecordedCases, recordedComparisonCsv }) => {
    const changes = [
      (s) => {
        s.manifest.identity.configuration_id = 'foreign';
      },
      (s) => {
        s.manifest.identity.resolved_spec_sha256 = 'foreign';
      },
      (s) => {
        s.manifest.identity.cad_revision_sha256 = 'foreign';
      },
      (s) => {
        s.manifest.identity.part_shape_sha256.a = 'foreign';
      },
      (s) => {
        s.field.quantity = 'temperature';
      },
      (s) => {
        s.field.units = 'm';
      },
      (s) => {
        s.field.component = 'yy';
      },
      (s) => {
        s.field.association = 'node';
      },
      (s) => {
        s.field.part_ids = ['a'];
      },
      (s) => {
        s.field.coverage_notes = 'Other coverage';
      },
      (s) => {
        s.manifest.coordinate_frame = 'foreign';
      },
      (s) => {
        s.field = { ...s.field, id: 'unregistered' };
      },
      (s) => {
        s.field.evidence.validation = 'failed';
      },
      (s) => {
        s.field.evidence.provenance = 'unavailable';
      },
      (s) => {
        s.field.artifact_sha256 = null;
      },
      (s) => {
        s.field.times_s = [0, 0, 2];
      },
      (s) => {
        s.payload.values[0][0] = Infinity;
      },
      (s) => {
        s.payload.part_ids = ['b', 'a'];
      },
      (s) => {
        s.manifest.identity.cad_revision_sha256 = null;
      },
    ];
    for (const mutate of changes) {
      const right = source('B');
      mutate(right);
      const model = compareRecordedCases(source(), right);
      assert.equal(model.status, 'incompatible', String(mutate));
      assert.equal(model.geometryAttachment, false);
      assert.deepEqual(model.rows, []);
      const exported = parseCsv(recordedComparisonCsv(model));
      assert.equal(exported[0].right_minus_left, '');
      assert.equal(exported[0].comparison_status, 'incompatible');
    }
    const invalidLegend = compareRecordedCases(source(), source('B'), { legend: [3, 3] });
    assert.equal(invalidLegend.status, 'incompatible');
  });
});

test('static cases have no fabricated time and spatial scalars require exact registered topology', async () => {
  await modules(({ compareRecordedCases, recordedComparisonCsv }) => {
    const left = source(),
      right = source('B');
    for (const s of [left, right]) {
      s.field.times_s = null;
      s.payload.values = [[0, null]];
    }
    const fixed = compareRecordedCases(left, right);
    assert.equal(fixed.status, 'compatible');
    assert.equal(fixed.leftTime, null);
    assert.equal(parseCsv(recordedComparisonCsv(fixed))[0].left_exact_time_s, '');
    for (const s of [left, right]) {
      s.field.association = 'node';
      s.field.part_ids = ['a'];
      s.field.sample_count = 6;
      s.field.mesh_sha256 = 'fixture-mesh';
      s.field.registration = {
        type: 'affine_4x4',
        matrix: [
          [1, 0, 0, 0],
          [0, 1, 0, 0],
          [0, 0, 1, 0],
          [0, 0, 0, 1],
        ],
        source_frame: 'fixture',
        target_frame: 'CAD_mm_registered_to_viewer_m',
      };
      s.payload = {
        values: [[0, 1, null, 3, 4, 5]],
        analysis_mesh: {
          frame: 'fixture',
          part_id: 'a',
          coverage: 'single synthetic shell',
          nodes: Array.from({ length: 6 }, (_, id) => ({ id, xyz_mm: [id, 0, 0] })),
          elements: [{ id: 10, type: 'S6', nodes: [0, 1, 2, 3, 4, 5] }],
        },
      };
    }
    const spatial = compareRecordedCases(left, right);
    assert.equal(spatial.status, 'compatible');
    assert.equal(spatial.geometryAttachment, false);
    assert.equal(spatial.rows[0].sampleId, 'node:0');
    assert.equal(spatial.rows[2].difference, null);
    right.payload.analysis_mesh.nodes[0].xyz_mm[0] = 0.1;
    assert.equal(compareRecordedCases(left, right).status, 'incompatible');
  });
});

test('SSR opens an explicit unavailable comparison or labeled software fixture table; CSV escapes labels safely', async () => {
  await modules(({ RecordedCaseComparison, compareRecordedCases, recordedComparisonCsv }) => {
    const unavailable = renderToStaticMarkup(
      React.createElement(RecordedCaseComparison, { left: null, right: null }),
    );
    assert.match(unavailable, /Recorded comparison unavailable/);
    assert.match(unavailable, /No eligible recorded field supplied/);
    assert.doesNotMatch(unavailable, /<table/);
    const left = source(),
      right = source('B');
    const html = renderToStaticMarkup(
      React.createElement(RecordedCaseComparison, {
        left,
        right,
        fixtureNotice: 'comparison regression only',
      }),
    );
    assert.match(html, /Synthetic software fixture/);
    assert.match(html, /Not engineering evidence/);
    assert.match(html, /Left exact analysis sample/);
    assert.match(html, /Right exact analysis sample/);
    assert.match(html, /Shared fixed legend: 0 to 25000000 Pa/);
    assert.match(html, /Unavailable — gap/);
    assert.match(html, />0<\/td>/);
    assert.match(html, /No interpolation, replay-clock coupling/);
    left.manifest.run_id = '=SUM(1,2)';
    const csv = recordedComparisonCsv(compareRecordedCases(left, right));
    assert.equal(parseCsv(csv)[0].left_run_id, "'=SUM(1,2)");
  });
});
