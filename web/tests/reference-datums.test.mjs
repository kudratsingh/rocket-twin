import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const digest = (data) => createHash('sha256').update(data).digest('hex');
const fixtureBytes = readFileSync(new URL('./fixtures/reference-parts.json', import.meta.url));
assert.equal(
  digest(fixtureBytes),
  '5db095fc80474ce25b1c0bb70087ca9c49abe4d696227a5b4810e4e6abfcd838',
);
const fixture = JSON.parse(fixtureBytes);
assert.equal(fixture.schema_version, 1);
assert.equal(fixture.generator, 'src.vehicle.reference_parts.build');
assert.equal(
  fixture.module_sha256,
  digest(readFileSync(new URL('../../src/vehicle/reference_parts.py', import.meta.url))),
);
const core = fixture.catalog;
assert.equal(core.schema_version, 1);
assert.equal(core.id, 'reference-local-v1');
assert.equal(
  core.revision_sha256,
  '8f6b7bf2f0dcc8dfb2714ba7a28688c820869dc3045060aba6ea5901983b7748',
);
assert.equal(core.scope, 'geometry_only_planning');
assert.equal(Object.hasOwn(core, 'availability'), false);
for (const [path, pin] of Object.entries(core.source_pins))
  assert.equal(digest(readFileSync(new URL(`../../${path}`, import.meta.url))), pin);
const close = (actual, expected, tolerance = 1e-12) =>
  assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} differs from ${expected}`);
const clone = (value) => structuredClone(value);

test('analytic datums use exact frozen local references and recorded CAD-to-viewer frame', async (t) => {
  const vite = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
    logLevel: 'silent',
  });
  try {
    const geometry = await vite.ssrLoadModule('/src/parts-bank/referenceDatumGeometry.ts');
    const ui = await vite.ssrLoadModule('/src/parts-bank/ReferenceDatumGuide.tsx');
    const [tube, ring] = core.definitions;
    await t.test(
      'actual Python build definitions admit independently of runtime availability',
      () => {
        assert.equal(core.definitions.length, 2);
        for (const definition of core.definitions) {
          const before = clone(definition);
          assert.equal(geometry.admitReferenceDefinition(definition), definition);
          assert.deepEqual(definition, before);
          assert.equal(definition.analytic_features.length, 5);
          assert.ok(Object.values(definition.unknown_properties).every((value) => value === null));
          assert.ok(Object.values(definition.readiness).every((value) => value === false));
          assert.equal(definition.representation.installed_transform, null);
          assert.equal(definition.interfaces, null);
          assert.equal(fixture.availability[definition.id].public_url_cache_verified, false);
        }
        const unavailable = clone(fixture);
        for (const row of Object.values(unavailable.availability)) {
          row.status = 'unavailable';
          row.geometry_available = false;
          row.missing_formats = ['glb'];
        }
        assert.deepEqual(unavailable.catalog, core);
        assert.ok(
          unavailable.catalog.definitions.every((row) => geometry.admitReferenceDefinition(row)),
        );
      },
    );
    await t.test(
      'point and dimensionless vector transforms preserve the documented axes and scale',
      () => {
        assert.deepEqual(geometry.cadPointToViewer([1000, 2000, 3000]), [1, -3, 2]);
        assert.deepEqual(geometry.cadPointToViewer([0, 0, 0]), [0, 0, 0]);
        assert.deepEqual(geometry.cadDirectionToViewer([0, 0, 1]), [0, -1, 0]);
        assert.deepEqual(geometry.cadDirectionToViewer([1, 0, 0]), [1, 0, 0]);
        assert.deepEqual(geometry.cadDirectionToViewer([0, 1, 0]), [0, 0, 1]);
        assert.deepEqual(geometry.cadDirectionToViewer([2, 3, 4]), [2, -4, 3]);
        assert.throws(() => geometry.cadPointToViewer([0, Infinity, 0]));
        assert.throws(() => geometry.cadDirectionToViewer([NaN, 0, 1]));
        assert.throws(() => geometry.cadPointToViewer([0, 0]));
      },
    );
    await t.test(
      'tube and annulus endpoints/radii match actual recorded STEP readback and GLB bounds',
      () => {
        for (const [definition, expected] of [
          [tube, [15.6845, 14.5845, 165]],
          [ring, [32.2, 15.95, 6]],
        ]) {
          const [outer, inner, length] = expected;
          const { recorded_readback: readback, bounds_m: glb } = definition.representation;
          assert.deepEqual(definition.parameters_mm, {
            outer_radius_mm: outer,
            inner_radius_mm: inner,
            length_mm: length,
          });
          assert.deepEqual(readback.bounds_mm, [
            [-outer, -outer, 0],
            [outer, outer, length],
          ]);
          assert.equal(readback.closed, true);
          assert.equal(readback.annular_bore, true);
          assert.equal(readback.solid_count, 1);
          close(readback.outer_diameter_mm, 2 * outer, 1e-8);
          close(readback.inner_diameter_mm, 2 * inner, 1e-8);
          const axis = geometry.referenceDatumGeometry(definition, 'axis');
          assert.deepEqual(axis.lines, [
            [
              [0, 0, 0],
              [0, -length / 1000, 0],
            ],
          ]);
          const idealBounds = {
            min: [-outer / 1000, -length / 1000, -outer / 1000],
            max: [outer / 1000, 0, outer / 1000],
          };
          for (const key of ['min', 'max'])
            idealBounds[key].forEach((value, index) => close(glb[key][index], value, 1e-8));
          for (const [id, radius] of [
            ['bore', inner],
            ['outer_cylinder', outer],
          ]) {
            const guide = geometry.referenceDatumGeometry(definition, id);
            assert.equal(guide.lines.length, 6);
            assert.equal(guide.annulus, null);
            for (const point of guide.lines.flat()) {
              close(Math.hypot(point[0], point[2]), radius / 1000);
              assert.ok(point[1] >= -length / 1000 && point[1] <= 0);
            }
            assert.deepEqual(guide.lines[2], [
              [radius / 1000, 0, 0],
              [radius / 1000, -length / 1000, 0],
            ]);
          }
          for (const [id, z] of [
            ['start_plane', 0],
            ['end_plane', length],
          ]) {
            const guide = geometry.referenceDatumGeometry(definition, id);
            assert.deepEqual(guide.annulus.center, [0, -z / 1000 || 0, 0]);
            assert.deepEqual(guide.annulus.normal, [0, -1, 0]);
            close(guide.annulus.innerRadiusM, inner / 1000);
            close(guide.annulus.outerRadiusM, outer / 1000);
            assert.match(guide.feature.normal_basis, /not a kernel face orientation/);
            for (const point of guide.lines.flat()) close(point[1], -z / 1000);
          }
        }
      },
    );
    await t.test(
      'foreign source/revision/frame, incomplete features, fabricated topology, assets and readiness fail closed',
      () => {
        const mutations = [
          (row) => {
            row.id = 'rp1:motor_tube';
          },
          (row) => {
            row.revision_sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.parameters_mm.length_mm = 200;
          },
          (row) => {
            row.source_part_id = 'motor_retainer';
          },
          (row) => {
            row.source_template_revision_sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.scope = 'installed';
          },
          (row) => {
            row.frames.local_cad_mm.units = 'm';
          },
          (row) => {
            row.frames.local_cad_mm.origin = 'nose_tip';
          },
          (row) => {
            row.frames.viewer.mapping = 'viewer=cad';
          },
          (row) => {
            row.analytic_features.pop();
          },
          (row) => {
            row.analytic_features.reverse();
          },
          (row) => {
            row.analytic_features[0].direction = [0, 1, 0];
          },
          (row) => {
            row.analytic_features[1].radius_mm = 15.95;
          },
          (row) => {
            row.analytic_features[3].normal = [0, 0, -1];
          },
          (row) => {
            row.analytic_features[0].cad_face_ids = [1];
          },
          (row) => {
            row.analytic_features[0].mesh_triangle_ids = [2];
          },
          (row) => {
            row.analytic_features[0].tolerance_mm = 0;
          },
          (row) => {
            row.analytic_features[0].mating_admitted = 0;
          },
          (row) => {
            row.unknown_properties.mass_kg = 0;
          },
          (row) => {
            row.readiness.simulation_eligible = true;
          },
          (row) => {
            row.readiness.connect_api = 0;
          },
          (row) => {
            row.representation.installed_transform = [];
          },
          (row) => {
            row.representation.assets.glb.sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.representation.assets.step.path = '/tmp/foreign.step';
          },
          (row) => {
            row.representation.assets.glb.url = 'https://foreign/model.glb';
          },
          (row) => {
            row.representation.assets.glb.bytes++;
          },
          (row) => {
            row.representation.bounds_m.min[1] = -0.2;
          },
          (row) => {
            row.provenance.specification_sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.provenance.geometry_manifest_sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.extra_schema = 1;
          },
        ];
        for (const mutate of mutations) {
          const row = clone(tube);
          mutate(row);
          assert.equal(geometry.admitReferenceDefinition(row), null);
          assert.equal(geometry.referenceDatumGeometry(row, 'axis'), null);
        }
        for (const id of [null, 'face-1', 'Axis', 'axis/../bore'])
          assert.equal(geometry.referenceDatumGeometry(tube, id), null);
      },
    );
    await t.test(
      'controlled keyboard list renders source limits with no network or automatic selection',
      () => {
        const original = globalThis.fetch;
        let requests = 0;
        let selections = 0;
        globalThis.fetch = async () => {
          requests++;
          throw new Error('Unexpected fetch');
        };
        try {
          const html = renderToStaticMarkup(
            React.createElement(ui.default, {
              definition: tube,
              selectedFeature: 'bore',
              onSelect: () => selections++,
            }),
          );
          assert.equal(requests, 0);
          assert.equal(selections, 0);
          assert.equal((html.match(/<button/g) ?? []).length, 6);
          assert.equal((html.match(/aria-pressed="true"/g) ?? []).length, 1);
          assert.match(html, /Radius 14.5845 mm; axial range 0–165 mm/);
          assert.match(html, /not extracted kernel faces or mesh triangle IDs/);
          assert.match(html, /not kernel or outward face normals/);
          assert.match(
            html,
            /No installed transform, physical mating, accepted tolerance or strength/,
          );
          assert.match(html, /remain false/);
          assert.doesNotMatch(html, /<canvas|Add part|Connect parts|<dialog/);
          const bad = renderToStaticMarkup(
            React.createElement(ui.default, {
              definition: { ...tube, scope: 'foreign' },
              selectedFeature: 'axis',
              onSelect: () => selections++,
            }),
          );
          assert.match(bad, /guides unavailable/);
          assert.doesNotMatch(bad, /<button/);
          assert.equal(
            ui.ReferenceDatumOverlay({
              definition: tube,
              selectedFeature: null,
              onSelect: () => {},
            }),
            null,
          );
          const overlay = ui.ReferenceDatumOverlay({
            definition: tube,
            selectedFeature: 'axis',
            onSelect: () => {},
          });
          assert.equal(overlay.type, 'group');
          assert.match(overlay.props.name, /^analytic-datum:reference-local-v1:/);
          assert.equal(requests, 0);
          assert.equal(selections, 0);
        } finally {
          globalThis.fetch = original;
        }
      },
    );
  } finally {
    await vite.close();
  }
});
