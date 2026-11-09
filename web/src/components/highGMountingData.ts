import layout from '../data/highGBoardLayout.json';

export interface HighGMountingSource {
  partId: string;
  configurationId: string;
  specificationSha256: string | null;
  boardLayoutId?: string | null;
  boardSourceSha256?: string | null;
}

const SOURCE_ID = 'adafruit-5374-pcb-2d-4a768fc9-v1';
const SOURCE_SHA256 = '7c089eb8cc0756b7dc5e30abd240978dc272113d93f602b497f8f442d532d68c';

export function matchesHighGMountingSource(source: HighGMountingSource): boolean {
  return (
    layout.id === SOURCE_ID &&
    layout.source.sha256 === SOURCE_SHA256 &&
    layout.units === 'mm' &&
    source.partId === layout.part_id &&
    source.configurationId === layout.configuration_id &&
    source.specificationSha256 === layout.specification_sha256 &&
    (source.boardLayoutId == null || source.boardLayoutId === layout.id) &&
    (source.boardSourceSha256 == null || source.boardSourceSha256 === layout.source.sha256)
  );
}

export function highGMountingReference(source: HighGMountingSource, selectedRef = 'U1') {
  if (!matchesHighGMountingSource(source)) return null;
  const placement = layout.placements.find((item) => item.ref === selectedRef);
  if (!placement) return null;
  const holes = layout.mounting_holes.map((hole) => ({
    ref: hole.ref,
    center_mm: [...hole.center_mm],
    diameter_mm: hole.radius_mm * 2,
    source_radius_mm: hole.radius_mm,
    role: hole.role,
    copper_outer_shape: hole.copper_outer_shape,
  }));
  if (holes.length !== 4 || holes.some((hole) => hole.diameter_mm !== 2.5 || hole.role !== 'drill'))
    return null;
  return {
    schema_version: 'rocket-twin.high-g-mounting-reference.v1',
    layout_id: layout.id,
    part_id: layout.part_id,
    configuration_id: layout.configuration_id,
    specification_sha256: layout.specification_sha256,
    units: layout.units,
    frame: layout.frame,
    pcb_size_mm: [...layout.pcb_size_mm],
    nominal_product_envelope_mm: [...layout.nominal_product_envelope_mm],
    mating_tolerance_mm: layout.mating_tolerance_mm,
    holes,
    selected_placement: JSON.parse(JSON.stringify(placement)) as typeof placement,
    source: { ...layout.source },
    license: { ...layout.license },
    maturity: layout.maturity,
    missing: [...layout.missing],
    engineering_accepted: layout.engineering_accepted,
  };
}

/** Exact tracked source JSON, including all 26 placements and explicit null heights. */
export function highGBoardSourceJson(source: HighGMountingSource): string | null {
  return matchesHighGMountingSource(source) ? JSON.stringify(layout, null, 2) : null;
}
