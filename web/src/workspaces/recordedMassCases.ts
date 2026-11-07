import type { InspectionDocument, JsonValue, MassSample } from '../types';

export interface RecordedMassCase {
  id: string;
  label: string;
  description: string;
  mass: MassSample & { recorded_case_label: string };
}

const ID = 'G80-F2-RP1-AD1-definition-v2';
const SPEC = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
const RECORD = 'bc349a24fe1cfaa4d883b9e00dc5b75387638a7be5cd4b05d9f32112ee8bd95b';
const number = (value: JsonValue | undefined) =>
  typeof value === 'number' && Number.isFinite(value) ? value : undefined;
const converted = (value: JsonValue | undefined, divisor: number) => {
  const source = number(value);
  return source === undefined ? undefined : source / divisor;
};

/** Saved loaded estimates only. This performs unit conversion, never a mass/balance model.
 * In particular, growth/harness/aft allowances already belong to the recorded total;
 * no propellant subtraction, burnout reconstruction or canonical inertia is admitted.
 */
export function recordedMassCases(vehicle: InspectionDocument): RecordedMassCase[] {
  if (
    vehicle.id !== ID ||
    vehicle.identity?.configuration_id !== ID ||
    vehicle.identity?.specification_sha256 !== SPEC ||
    vehicle.identity?.record_sha256 !== RECORD
  )
    throw new Error(
      'Saved RP1 mass cases require the exact frozen AD1 design, specification and record identity.',
    );
  const cases = vehicle.summary.mass_cases;
  if (!Array.isArray(cases)) return [];
  const used = new Set<string>();
  return cases.map((value, index) => {
    if (!value || typeof value !== 'object' || Array.isArray(value))
      throw new Error('Saved RP1 mass case is not a source record.');
    const name = value.case;
    if (name !== 'nominal' && name !== 'adverse')
      throw new Error('Saved RP1 mass case has an unknown case identity.');
    const harness = number(value.nylon_mass_probe_g);
    if (harness !== undefined && harness !== 55 && harness !== 68)
      throw new Error('Saved RP1 harness probe is outside the frozen 55/68 g case scope.');
    const growth = number(value.growth_g);
    if (growth !== undefined && growth !== 50)
      throw new Error('Saved RP1 growth allowance differs from the frozen full 50 g case scope.');
    if (value.probe_is_bound === true)
      throw new Error('Saved RP1 harness probes cannot be promoted to qualified bounds.');
    const id = `${name}-harness-${harness ?? `unavailable-${index}`}-loaded`;
    if (used.has(id)) throw new Error('Saved RP1 mass case identities are duplicated.');
    used.add(id);
    const label = `Saved loaded estimate · ${name} · ${harness === undefined ? 'harness probe unavailable' : `${harness} g unverified harness probe`}`;
    const aft = number(value.extra_aft_g);
    const motor = number(value.motor_cg_probe_mm);
    const description = [
      'Recorded loaded/launch case; source estimates, not a measured vehicle.',
      growth === undefined
        ? 'Growth allowance unavailable; no extra allowance is added by this display.'
        : 'Full 50 g growth already included in the saved total; not added again.',
      harness === undefined
        ? 'Harness probe value unavailable.'
        : `${harness} g nylon/harness probe already represented by this saved case; unverified and not a bound.`,
      aft === undefined
        ? 'Extra aft mass unavailable.'
        : `Extra aft mass: ${aft} g, already included.`,
      motor === undefined ? 'Motor CG probe unavailable.' : `Motor CG probe: ${motor} mm.`,
      'CG, CP and stability are copied saved estimates. Burnout fields remain separate source metadata; no burn-state mass, inertia or flight model is derived.',
    ].join(' ');
    const mass = converted(value.total_mass_g, 1000);
    return {
      id,
      label,
      description,
      mass: {
        mass_kg: mass,
        total_mass_kg: mass,
        cg_m: converted(value.cg_mm, 1000),
        cp_m: converted(value.cp_mm, 1000),
        stability_margin_cal: number(value.margin_cal),
        recorded_case_label: label,
      },
    };
  });
}
