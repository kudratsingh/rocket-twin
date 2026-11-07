import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import test from 'node:test';
import { recordedMassCases } from '../src/workspaces/recordedMassCases.ts';

// Actual prepared source, read only. These assertions test display conversion,
// not the engineering validity of the saved source estimates.
const sourcePath = new URL(
  '../public/engineering-workbench/rp1-ad1-inspection.json',
  import.meta.url,
);
const actual = existsSync(sourcePath) ? JSON.parse(readFileSync(sourcePath, 'utf8')) : null;
// Clean source-only CI still exercises missing-value and identity behavior using
// a software fixture; it does not claim that the prepared source was present.
const source = actual ?? {
  id: 'G80-F2-RP1-AD1-definition-v2',
  identity: {
    configuration_id: 'G80-F2-RP1-AD1-definition-v2',
    specification_sha256: '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660',
    record_sha256: 'bc349a24fe1cfaa4d883b9e00dc5b75387638a7be5cd4b05d9f32112ee8bd95b',
  },
  parts: [],
  summary: {
    mass_cases: ['nominal', 'adverse'].flatMap((name) =>
      [55, 68].map((harness) => ({
        case: name,
        nylon_mass_probe_g: harness,
        probe_is_bound: false,
        total_mass_g: 934.5492181993527,
        growth_g: 50,
        extra_aft_g: name === 'adverse' ? 20 : 0,
        motor_cg_probe_mm: name === 'adverse' ? 12.8 : 0,
        cg_mm: 763.693415896063,
        cp_mm: 859.4422933913564,
        margin_cal: 1.433323515692546,
      })),
    ),
  },
};

test(
  'four frozen RP1 loaded cases copy actual saved mass/CG/CP with unit conversion only',
  {
    skip: !actual
      ? 'Prepared AD1 source absent; software fixture regressions remain active'
      : false,
  },
  () => {
    const before = JSON.stringify(source);
    const cases = recordedMassCases(source);
    assert.equal(cases.length, 4);
    assert.equal(new Set(cases.map((entry) => entry.id)).size, 4);
    for (const [index, entry] of cases.entries()) {
      const raw = source.summary.mass_cases[index];
      assert.equal(entry.mass.mass_kg, raw.total_mass_g / 1000);
      assert.equal(entry.mass.total_mass_kg, raw.total_mass_g / 1000);
      assert.equal(entry.mass.cg_m, raw.cg_mm / 1000);
      assert.equal(entry.mass.cp_m, raw.cp_mm / 1000);
      assert.equal(entry.mass.stability_margin_cal, raw.margin_cal);
      assert.equal(entry.mass.recorded_case_label, entry.label);
      assert.equal(entry.mass.burn_fraction, undefined);
      assert.match(entry.description, /Full 50 g growth already included.*not added again/);
      assert.match(entry.description, /unverified and not a bound/);
      assert.match(entry.description, /no burn-state mass, inertia or flight model is derived/);
    }
    assert.ok(Math.abs(cases[0].mass.mass_kg * 1000 - 934.5492181993527) < 1e-10);
    assert.ok(Math.abs(cases[0].mass.cg_m * 1000 - 763.693415896063) < 1e-10);
    assert.ok(Math.abs(cases[0].mass.cp_m * 1000 - 859.4422933913564) < 1e-10);
    assert.match(cases[0].label, /nominal.*55 g/);
    assert.match(cases[1].label, /adverse.*55 g/);
    assert.match(cases[2].label, /nominal.*68 g/);
    assert.match(cases[3].label, /adverse.*68 g/);
    assert.match(cases[1].description, /Extra aft mass: 20 g, already included/);
    assert.match(cases[1].description, /Motor CG probe: 12.8 mm/);
    assert.match(cases[0].description, /Extra aft mass: 0 g/);
    assert.equal(JSON.stringify(source), before);
  },
);

test('unknown source values stay undefined; saved growth/harness/probe data are never added to total again', () => {
  const copy = structuredClone(source);
  const row = copy.summary.mass_cases[0];
  row.total_mass_g = null;
  delete row.cg_mm;
  row.cp_mm = NaN;
  delete row.margin_cal;
  delete row.growth_g;
  delete row.extra_aft_g;
  delete row.motor_cg_probe_mm;
  const absent = recordedMassCases(copy)[0];
  for (const key of [
    'mass_kg',
    'total_mass_kg',
    'cg_m',
    'cp_m',
    'stability_margin_cal',
    'burn_fraction',
  ])
    assert.equal(absent.mass[key], undefined, key);
  assert.match(absent.description, /Growth allowance unavailable/);
  assert.match(absent.description, /Extra aft mass unavailable/);
  assert.match(absent.description, /Motor CG probe unavailable/);
  row.total_mass_g = 934.5492181993527;
  row.growth_g = 50;
  row.extra_aft_g = 20;
  row.motor_cg_probe_mm = 12.8;
  row.burnout_cg_mm = 0;
  row.burnout_margin_cal = 0;
  const restored = recordedMassCases(copy)[0];
  assert.equal(restored.mass.mass_kg, 934.5492181993527 / 1000);
  assert.equal(
    restored.mass.cg_m,
    undefined,
    'must not replace missing loaded CG with saved burnout CG',
  );
  assert.equal(restored.mass.stability_margin_cal, undefined);
  assert.equal(restored.mass.burn_fraction, undefined);
  copy.summary.mass_cases = [];
  assert.deepEqual(recordedMassCases(copy), []);
});

test('foreign or drifted identities and changed allowance scopes fail explicitly', () => {
  for (const mutate of [
    (s) => {
      s.id = 'modular-performance-v1';
    },
    (s) => {
      s.identity.configuration_id = 'foreign';
    },
    (s) => {
      s.identity.specification_sha256 = 'foreign';
    },
    (s) => {
      s.identity.record_sha256 = 'foreign';
    },
  ]) {
    const copy = structuredClone(source);
    mutate(copy);
    assert.throws(() => recordedMassCases(copy), /exact frozen AD1/);
  }
  for (const mutate of [
    (s) => {
      s.summary.mass_cases[0].growth_g = 0;
    },
    (s) => {
      s.summary.mass_cases[0].nylon_mass_probe_g = 60;
    },
    (s) => {
      s.summary.mass_cases[0].probe_is_bound = true;
    },
    (s) => {
      s.summary.mass_cases.push(structuredClone(s.summary.mass_cases[0]));
    },
  ]) {
    const copy = structuredClone(source);
    mutate(copy);
    assert.throws(() => recordedMassCases(copy));
  }
});
