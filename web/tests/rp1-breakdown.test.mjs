import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import {
  getRp1Presentation,
  rp1BreakdownOffset,
  RP1_PRESENTATION_ID,
  RP1_PRESENTATION_SHA256,
} from '../src/components/rp1Breakdown.ts';

const geometry = JSON.parse(
  readFileSync(
    new URL('../../docs/studies/rp1-inspection-geometry-20261107/manifest.json', import.meta.url),
  ),
);
const groupIds = [
  'nose_airframe',
  'fins_roots',
  'motor_retention',
  'recovery',
  'avionics_power',
  'launch_finish',
];
// Synthetic display vectors and memberships exercise the helper independently;
// actual frozen55 IDs, source/shape/mesh hashes and recorded bounds are reused.
function fixture() {
  const source_tuple = {
    configuration_id: geometry.id,
    specification_sha256: geometry.identity.specification_sha256,
    inspection_geometry_sha256: geometry.identity.inspection_geometry_sha256,
  };
  const groups = groupIds.map((id) => ({
    id,
    label: id,
    part_ids: [],
    record_count: 0,
    mesh_count: 0,
  }));
  const presentation = {
    id: RP1_PRESENTATION_ID,
    schema_version: 1,
    presentation_sha256: RP1_PRESENTATION_SHA256,
    source_tuple,
    geometry_compatible: true,
    groups,
    breakdown: {
      kind: 'staged-display-illustration',
      assembly_stage_end: 0.5,
      units: 'm',
      manufacturing_clearance: false,
    },
  };
  const parts = geometry.parts.map((row) => {
    const group_id = ['motor', 'motor_tube', 'motor_retainer', 'forward_ring', 'aft_ring'].includes(
      row.id,
    )
      ? 'motor_retention'
      : ['parachute', 'shock_cord', 'recovery_connectors'].includes(row.id)
        ? 'recovery'
        : ['fin_set', 'fin_tabs', 'root_gussets'].includes(row.id)
          ? 'fins_roots'
          : 'nose_airframe';
    const group = groups.find((g) => g.id === group_id);
    group.part_ids.push(row.id);
    group.record_count++;
    group.mesh_count += Boolean(row.mesh);
    const detail =
      row.id === 'motor'
        ? [0.14, 0, 0]
        : row.id === 'fin_set' || row.id === 'fin_tabs'
          ? [0, 0, 0.12]
          : [0, 0, 0];
    const assembly =
      group_id === 'recovery'
        ? [-0.24, 0.12, 0.12]
        : group_id === 'motor_retention'
          ? [0.24, -0.1, 0]
          : [0, 0.2, 0];
    return {
      id: row.id,
      parent: null,
      material: 'fixture',
      type: 'fixture',
      learn: 'Helper fixture with actual frozen mesh bounds.',
      inspection_shape_sha256: row.inspection_shape_sha256,
      mesh_url: row.mesh
        ? `/api/design/${geometry.id}/inspection-mesh/${row.id}?spec=${source_tuple.specification_sha256}&geometry=${source_tuple.inspection_geometry_sha256}&mesh=${row.mesh.sha256}`
        : undefined,
      representation: {
        presentation: {
          id: row.id,
          group_id,
          source_parent: null,
          source_tuple,
          presentation_sha256: presentation.presentation_sha256,
          has_mesh: Boolean(row.mesh),
          inspection_shape_sha256: row.inspection_shape_sha256,
          mesh_sha256: row.mesh?.sha256,
          assembly_offset_m: assembly,
          detail_offset_m: detail,
        },
      },
    };
  });
  return {
    id: geometry.id,
    identity: {
      specification_sha256: source_tuple.specification_sha256,
      inspection_geometry_sha256: source_tuple.inspection_geometry_sha256,
    },
    parts,
    summary: { presentation },
  };
}
const bounds = (id, offset) =>
  geometry.parts.find((p) => p.id === id).bounds_m.map((v) => v.map((x, i) => x + offset[i]));
const disjoint = (a, b) => [0, 1, 2].some((i) => a[1][i] < b[0][i] || b[1][i] < a[0][i]);

test('zero is exact source placement for all55, with no meshless inferred solids', () => {
  const doc = fixture();
  assert.equal(getRp1Presentation(doc).groups.flatMap((g) => g.part_ids).length, 55);
  for (const part of doc.parts) {
    assert.deepEqual(rp1BreakdownOffset(doc, part.id, 0, 'motor_retention'), [0, 0, 0]);
    if (!part.mesh_url)
      assert.deepEqual(rp1BreakdownOffset(doc, part.id, 1, 'motor_retention'), [0, 0, 0]);
  }
});
test('groups separate first; only the openedgroup details move, using final offset once', () => {
  const doc = fixture();
  assert.deepEqual(rp1BreakdownOffset(doc, 'motor', 0.25, 'motor_retention'), [0.12, -0.05, 0]);
  assert.deepEqual(rp1BreakdownOffset(doc, 'motor', 0.5, 'motor_retention'), [0.24, -0.1, 0]);
  assert.deepEqual(rp1BreakdownOffset(doc, 'motor', 1, null), [0.24, -0.1, 0]);
  assert.deepEqual(rp1BreakdownOffset(doc, 'motor', 1, 'motor_retention'), [0.38, -0.1, 0]);
  assert.deepEqual(rp1BreakdownOffset(doc, 'motor', 1, 'recovery'), [0.24, -0.1, 0]);
  for (const s of [0, 0.25, 0.5, 0.75, 1])
    assert.deepEqual(
      rp1BreakdownOffset(doc, 'fin_set', s, 'fins_roots'),
      rp1BreakdownOffset(doc, 'fin_tabs', s, 'fins_roots'),
    );
});
test('actual recorded motor/tube and recovery/body bounds clear at full supported separation', () => {
  const doc = fixture();
  assert.ok(
    disjoint(
      bounds('motor', rp1BreakdownOffset(doc, 'motor', 1, 'motor_retention')),
      bounds('motor_tube', rp1BreakdownOffset(doc, 'motor_tube', 1, 'motor_retention')),
    ),
  );
  for (const id of ['parachute', 'shock_cord', 'recovery_connectors'])
    assert.ok(
      disjoint(
        bounds(id, rp1BreakdownOffset(doc, id, 1, 'recovery')),
        bounds('upper_body', rp1BreakdownOffset(doc, 'upper_body', 1, 'recovery')),
      ),
    );
  assert.equal(
    disjoint(
      bounds('motor', rp1BreakdownOffset(doc, 'motor', 1, null)),
      bounds('motor_tube', rp1BreakdownOffset(doc, 'motor_tube', 1, null)),
    ),
    false,
    'a closedgroup intentionally retains nesting; no all-pair clearance claim',
  );
});
test('foreign/unknown source, group, shape and asset tuples failclosed without RP1 fallback', () => {
  const doc = fixture();
  assert.deepEqual(rp1BreakdownOffset(doc, 'unknown', 1, null), [0, 0, 0]);
  assert.deepEqual(rp1BreakdownOffset(doc, 'motor', 1, 'foreign-group'), [0, 0, 0]);
  for (const corrupt of [
    (d) => (d.identity.specification_sha256 = '0'.repeat(64)),
    (d) => (d.summary.presentation.presentation_sha256 = '0'.repeat(64)),
    (d) => (d.parts.find((p) => p.id === 'motor').inspection_shape_sha256 = '0'.repeat(64)),
    (d) => (d.parts.find((p) => p.id === 'motor').mesh_url += 'wrong'),
    (d) => d.summary.presentation.groups[0].part_ids.push('foreign'),
  ]) {
    const wrong = structuredClone(doc);
    corrupt(wrong);
    assert.deepEqual(rp1BreakdownOffset(wrong, 'motor', 1, 'motor_retention'), [0, 0, 0]);
  }
  assert.deepEqual(rp1BreakdownOffset(doc, 'motor', NaN, null), [0, 0, 0]);
  assert.equal(rp1BreakdownOffset({ ...doc, id: 'archived-vehicle' }, 'motor', 1, null), null);
});
