import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { Matrix4, Vector3 } from '../node_modules/three/build/three.module.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const bytes = readFileSync(new URL('./fixtures/reference-parts.json', import.meta.url));
assert.equal(
  createHash('sha256').update(bytes).digest('hex'),
  '5db095fc80474ce25b1c0bb70087ca9c49abe4d696227a5b4810e4e6abfcd838',
);
const fixture = JSON.parse(bytes);
const [tube, ring] = fixture.catalog.definitions;
const clone = (value) => structuredClone(value);
const instances = [
  { id: 'geometry-reference:tube-1', definition: tube, translation_mm: [100, -25, 200] },
  { id: 'geometry-reference:ring-1', definition: ring, translation_mm: [-30, 20, -50] },
];
const close = (actual, expected, tolerance = 1e-12) =>
  assert.ok(Math.abs(actual - expected) < tolerance, `${actual} differs from ${expected}`);

// These are synthetic display transforms of actual frozen reference metadata.
// They do not perform CAD readback, fit/contact checks or physics validation.
test('two-reference arrangement display validates source and applies local viewer transforms', async (t) => {
  const vite = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
    logLevel: 'silent',
  });
  try {
    const display = await vite.ssrLoadModule('/src/parts-bank/referenceArrangementDisplay.ts');
    const { default: Scene } = await vite.ssrLoadModule(
      '/src/parts-bank/ReferenceArrangementScene.tsx',
    );
    await t.test(
      'actual definitions admit as two distinct planning entries without mutating source',
      () => {
        const before = clone(instances);
        assert.equal(display.admitArrangementDisplay(instances), instances);
        assert.deepEqual(instances, before);
        assert.equal(display.ARRANGEMENT_DISPLAY_FRAME, 'uninstalled-local-reference-arrangement');
        assert.deepEqual(display.admitArrangementDisplay([]), []);
        assert.equal(display.arrangementDisplayBounds([]), null);
        for (const instance of instances) {
          assert.equal(instance.definition.representation.installed_transform, null);
          assert.ok(
            Object.values(instance.definition.unknown_properties).every((value) => value === null),
          );
          assert.ok(Object.values(instance.definition.readiness).every((value) => value === false));
        }
      },
    );
    await t.test(
      'numeric local translation maps axes/scale once and keeps the source GLB bounds',
      () => {
        assert.deepEqual(display.arrangementTranslation(instances[0]), [0.1, -0.2, -0.025]);
        assert.deepEqual(display.arrangementTranslation(instances[1]), [-0.03, 0.05, 0.02]);
        const expectedTranslations = [
          [0.1, -0.2, -0.025],
          [-0.03, 0.05, 0.02],
        ];
        const placed = instances.map((instance, i) => {
          const source = instance.definition.representation.bounds_m;
          const matrix = new Matrix4().makeTranslation(...expectedTranslations[i]);
          const result = display.arrangementInstanceBounds(instance);
          for (const corner of ['min', 'max']) {
            const independent = new Vector3(...source[corner]).applyMatrix4(matrix).toArray();
            result[corner].forEach((value, axis) => close(value, independent[axis]));
          }
          return result;
        });
        const combined = display.arrangementDisplayBounds(instances);
        for (let axis = 0; axis < 3; axis++) {
          close(combined.min[axis], Math.min(placed[0].min[axis], placed[1].min[axis]));
          close(combined.max[axis], Math.max(placed[0].max[axis], placed[1].max[axis]));
        }
        const zero = { ...instances[0], translation_mm: [0, 0, 0] };
        assert.deepEqual(display.arrangementInstanceBounds(zero), tube.representation.bounds_m);
        close(tube.parameters_mm.length_mm, 165);
        close(ring.parameters_mm.length_mm, 6);
      },
    );
    await t.test(
      'translation limits/granularity are UI bounds and reject unsafe or malformed entries',
      () => {
        for (const translation of [
          [500, -500, 0],
          [1.001, -0.001, 0.123],
          [0, 0, 0],
        ]) {
          assert.doesNotThrow(() =>
            display.admitArrangementDisplay([{ ...instances[0], translation_mm: translation }]),
          );
        }
        for (const translation of [
          [500.001, 0, 0],
          [-500.001, 0, 0],
          [0.0001, 0, 0],
          [NaN, 0, 0],
          [Infinity, 0, 0],
          [0, 0],
          ['1', 0, 0],
          null,
        ]) {
          assert.throws(() =>
            display.admitArrangementDisplay([{ ...instances[0], translation_mm: translation }]),
          );
        }
        for (const value of [
          null,
          {},
          [...instances, instances[0]],
          [{ ...instances[0], id: '../source' }],
          [{ ...instances[0], id: '' }],
          [{ ...instances[0], rotation: [0, 0, 0] }],
          [instances[0], { ...instances[1], id: instances[0].id }],
          [instances[0], { ...instances[0], id: 'second-tube' }],
        ])
          assert.throws(() => display.admitArrangementDisplay(value));
      },
    );
    await t.test(
      'foreign definition, changed frame, dimensions and asset identities reject before loading',
      () => {
        for (const mutate of [
          (row) => {
            row.definition.id = 'rp1:motor_tube';
          },
          (row) => {
            row.definition.revision_sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.definition.frames.viewer.mapping = 'viewer=cad';
          },
          (row) => {
            row.definition.frames.local_cad_mm.units = 'm';
          },
          (row) => {
            row.definition.parameters_mm.length_mm = 200;
          },
          (row) => {
            row.definition.representation.assets.glb.url = 'https://foreign/model.glb';
          },
          (row) => {
            row.definition.representation.assets.glb.sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.definition.representation.bounds_m.max[1] = 1;
          },
          (row) => {
            row.definition.readiness.flight_ready = true;
          },
          (row) => {
            row.definition.unknown_properties.mass_kg = 0;
          },
        ]) {
          const row = clone(instances[0]);
          mutate(row);
          assert.throws(() => display.admitArrangementDisplay([row]));
          assert.throws(() => display.arrangementDisplayBounds([row]));
        }
      },
    );
    await t.test(
      'framing identity changes for instance set, preserving identity across pose or selection updates',
      () => {
        const identity = display.arrangementFramingIdentity(instances);
        const moved = clone(instances);
        moved[0].translation_mm = [-500, 500, 0.125];
        assert.equal(display.arrangementFramingIdentity(moved), identity);
        assert.equal(display.arrangementFramingIdentity([...instances].reverse()), identity);
        assert.notEqual(display.arrangementFramingIdentity([instances[0]]), identity);
        assert.notEqual(
          display.arrangementFramingIdentity([
            { ...instances[0], id: 'different-tube-instance' },
            instances[1],
          ]),
          identity,
        );
        assert.notDeepEqual(
          display.arrangementDisplayBounds(moved),
          display.arrangementDisplayBounds(instances),
        );
      },
    );
    await t.test(
      'SSR shows empty/loading/error without arbitrary solid, fetch or selection',
      () => {
        const original = globalThis.fetch;
        let requests = 0;
        let selections = 0;
        globalThis.fetch = async () => {
          requests++;
          throw new Error('Unexpected request');
        };
        try {
          const empty = renderToStaticMarkup(
            React.createElement(Scene, {
              instances: [],
              selectedInstanceId: null,
              onSelect: () => selections++,
            }),
          );
          assert.match(empty, /Empty arrangement/);
          assert.doesNotMatch(empty, /<canvas/);
          assert.equal((empty.match(/disabled=""/g) ?? []).length, 5);
          const loading = renderToStaticMarkup(
            React.createElement(Scene, {
              instances,
              selectedInstanceId: instances[0].id,
              onSelect: () => selections++,
            }),
          );
          assert.match(loading, /Verifying and loading exact local reference GLB bytes/);
          assert.match(loading, /Fit arrangement/);
          assert.match(loading, /Selection and translation preserve the view/);
          assert.match(loading, /no physical mating or fit result/);
          assert.doesNotMatch(loading, /<canvas|<mesh|<boxGeometry/);
          const invalid = renderToStaticMarkup(
            React.createElement(Scene, {
              instances: [{ ...instances[0], translation_mm: [1000, 0, 0] }],
              selectedInstanceId: null,
              onSelect: () => selections++,
            }),
          );
          assert.match(invalid, /placement is invalid/);
          assert.doesNotMatch(invalid, /<canvas|<button/);
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
