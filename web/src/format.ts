import type { JsonValue, Part } from './types';

export const partName = (part: Part) => part.name || title(part.id);
export function title(text: string): string {
  return text.replace(/[_-]/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}
export const grams = (kg?: number) =>
  kg == null
    ? 'Unavailable'
    : `${(kg * 1000).toLocaleString(undefined, { maximumFractionDigits: 2 })} g`;
export const millimetres = (m?: number) =>
  m == null
    ? 'Unavailable'
    : `${(m * 1000).toLocaleString(undefined, { maximumFractionDigits: 1 })} mm`;
export const number = (value?: number, decimals = 3) =>
  value == null
    ? 'Unavailable'
    : value.toLocaleString(undefined, { maximumFractionDigits: decimals });
export function displayValue(key: string, value: JsonValue): string {
  if (value === null) return 'Unavailable';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number') {
    if (key.endsWith('_kg')) return grams(value);
    if (key.endsWith('_m')) return millimetres(value);
    if (key.endsWith('_mm')) return `${number(value, 2)} mm`;
    if (key.endsWith('_rad')) return `${number((value * 180) / Math.PI, 1)}°`;
    if (key.endsWith('_n')) return `${number(value, 2)} N`;
    if (key.endsWith('_ns')) return `${number(value, 2)} N·s`;
    if (key.endsWith('_s')) return `${number(value, 2)} s`;
    if (key.endsWith('_v')) return `${number(value, 2)} V`;
    if (key.endsWith('_a')) return `${number(value, 2)} A`;
    if (key.endsWith('_mah')) return `${number(value, 0)} mAh`;
    if (key.endsWith('_nm')) return `${number(value, 3)} N·m`;
    if (key.endsWith('_pct')) return `${number(value, 1)}%`;
    if (key.endsWith('_usd')) return `$${number(value, 2)} estimate`;
    if (key.endsWith('_c')) return `${number(value, 2)} °C`;
    if (key.endsWith('_k')) return `${number(value, 2)} K`;
    if (key.endsWith('_cal')) return `${number(value, 3)} calibres`;
    return number(value);
  }
  if (Array.isArray(value)) {
    if (value.every((entry) => typeof entry === 'number') && key.endsWith('_m'))
      return `${value.map((entry) => number(Number(entry) * 1000, 1)).join(' × ')} mm`;
    return value
      .map((entry) => (typeof entry === 'object' ? JSON.stringify(entry) : String(entry)))
      .join(' · ');
  }
  if (typeof value === 'object')
    return Object.entries(value)
      .map(([k, v]) => `${label(k)}: ${displayValue(k, v)}`)
      .join(' · ');
  return value;
}
export function label(key: string): string {
  const names: Record<string, string> = {
    cg_m: 'Balance point (CG), from nose',
    cp_m: 'Aerodynamic force point (CP), from nose',
    position_m: 'Leading station from nose',
    cg_station_m: 'Part balance point from nose',
    burnout_cg_m: 'Balance point at burnout',
    burnout_stability_margin_cal: 'Static margin at burnout',
    stability_margin_cal: 'Static stability margin',
    mass_kg: 'Mass',
    total_mass_kg: 'Loaded mass',
    diameter_m: 'Diameter',
    length_m: 'Length',
    overall_length_m: 'Overall hardware length',
    od_m: 'Outside diameter',
    id_m: 'Inside diameter',
    wall_m: 'Wall thickness',
    bbox_m: 'Envelope (length × width × height)',
    span_m: 'Outward reach (span)',
    root_chord_m: 'Length along body (root chord)',
    tip_chord_m: 'Length of outer edge (tip chord)',
    sweep_m: 'Front-edge offset (sweep)',
    thickness_m: 'Thickness',
    count: 'Number of instances',
    max_deflection_rad: 'Maximum gimbal deflection',
    cg_offset_m: 'Local balance-point offset',
    certified_average_thrust_n: 'Certified average thrust',
    total_impulse_ns: 'Total impulse',
    burn_time_s: 'Motor burn duration',
    nominal_v: 'Nominal voltage',
    supply_v: 'Supply voltage',
    capacity_mah: 'Battery capacity',
    bus: 'Communication bus',
  };
  return names[key] || title(key.replace(/_(kg|m|rad|n|ns|s|v|a|mah|cal)$/, ''));
}
