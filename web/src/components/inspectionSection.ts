import { Plane, Vector3 } from 'three';
import type { InspectionDocument } from '../types';

export type SectionSettings = {
  mode: 'longitudinal' | 'transverse';
  angleDeg: number;
  offsetMm: number;
  stationMm: number;
  flipped: boolean;
};
export const DEFAULT_SECTION: SectionSettings = {
  mode: 'longitudinal',
  angleDeg: 0,
  offsetMm: 0,
  stationMm: 0,
  flipped: false,
};
export type SectionDimensions = { lengthM: number | null; radiusM: number | null };
const positive = (v: unknown) => (typeof v === 'number' && Number.isFinite(v) && v > 0 ? v : null);
export function sectionDimensions(vehicle: InspectionDocument): SectionDimensions {
  const lengthM = positive(vehicle.geometry?.length_m) ?? positive(vehicle.summary.length_m);
  const diameter = positive(vehicle.geometry?.diameter_m) ?? positive(vehicle.summary.diameter_m);
  return { lengthM, radiusM: diameter === null ? null : diameter / 2 };
}

/** View coordinates in metres: axial +Y; station is measured aft from the nose. */
export function inspectionSectionPlane(s: SectionSettings, dims: SectionDimensions): Plane {
  if (![s.angleDeg, s.offsetMm, s.stationMm].every(Number.isFinite))
    throw new RangeError('Section values must be finite.');
  if (s.mode !== 'longitudinal' && s.mode !== 'transverse')
    throw new RangeError('Unknown section mode.');
  const sign = s.flipped ? -1 : 1;
  if (s.mode === 'transverse') {
    if (
      dims.lengthM === null ||
      !Number.isFinite(dims.lengthM) ||
      dims.lengthM <= 0 ||
      s.stationMm < 0 ||
      s.stationMm > dims.lengthM * 1000
    )
      throw new RangeError('A transverse section needs a known length and an in-range station.');
    return new Plane(new Vector3(0, -sign, 0), sign * (dims.lengthM - s.stationMm / 1000));
  }
  if (
    s.offsetMm !== 0 &&
    (dims.radiusM === null ||
      !Number.isFinite(dims.radiusM) ||
      dims.radiusM <= 0 ||
      Math.abs(s.offsetMm) > dims.radiusM * 1000)
  )
    throw new RangeError('A radial offset needs a known radius and an in-range value.');
  const angle = ((((s.angleDeg % 360) + 360) % 360) * Math.PI) / 180;
  return new Plane(
    new Vector3(-Math.cos(angle) * sign, 0, -Math.sin(angle) * sign),
    (s.offsetMm / 1000) * sign,
  );
}
