import type { InspectionDocument, JsonValue, Part } from '../types';
import { evidenceRecord, evidenceText } from './inspectionEvidenceModel';

const names: Record<string, string> = {
  length_m: 'Axial length',
  diameter_m: 'Diameter',
  od_m: 'Outside diameter',
  radius_m: 'Outer radius',
  inner_radius_m: 'Inner radius',
  inner_diameter_m: 'Inner diameter',
  wall_m: 'Wall thickness',
  wall_thickness_m: 'Wall thickness',
  thickness_m: 'Thickness',
  width_m: 'Width',
  height_m: 'Height',
  span_m: 'Fin span',
  root_chord_m: 'Fin root chord',
  tip_chord_m: 'Fin tip chord',
  sweep_m: 'Fin sweep',
  bbox_m: 'Box envelope (source order)',
  tab_length_m: 'Tab length',
  tab_width_m: 'Tab width',
  tab_thickness_m: 'Tab thickness',
  count: 'Count',
  position_m: 'Absolute axial station',
  cg_station_m: 'Centre-of-mass axial station',
  lateral_offset_m: 'Transverse offsets (source order)',
  mass_kg: 'Recorded component mass',
  cad_mass_kg: 'CAD mass',
  subtree_mass_kg: 'Assembly subtree mass',
};
const massBasisExplanation: Record<string, string> = {
  volume_density:
    'Source mass uses geometry volume and assigned density; it is not a measured as-built mass.',
  supplied_or_estimated:
    'Source mass is supplied or estimated; the label alone does not establish a weighing measurement.',
};
const numberText = (value: number) => Number(value.toPrecision(9)).toString();

/** Display units only; never derive wall, diameter, mass, fit or physical properties. */
export function dimensionValue(key: string, value: JsonValue | undefined): string {
  if (value === undefined || value === null) return 'Unavailable — not supplied';
  if (Array.isArray(value))
    return value.length
      ? value.map((item) => dimensionValue(key, item)).join(' × ')
      : 'Unavailable — empty source array';
  if (typeof value !== 'number') return evidenceText(value);
  if (!Number.isFinite(value)) return 'Unavailable — invalid source number';
  if (key.endsWith('_mm')) return `${numberText(value)} mm (${numberText(value / 1000)} m)`;
  if (key.endsWith('_m')) return `${numberText(value)} m (${numberText(value * 1000)} mm)`;
  if (key.endsWith('_kg')) return `${numberText(value)} kg (${numberText(value * 1000)} g)`;
  if (key.endsWith('_g')) return `${numberText(value)} g (${numberText(value / 1000)} kg)`;
  return numberText(value);
}

export function partDimensionModel(part: Part) {
  const fields = part.dimensions ?? part.geometry ?? {};
  const role = evidenceRecord(part.representation)?.role ?? part.representation;
  const roleText = typeof role === 'string' ? role : 'Unspecified';
  const envelope = /envelope|simplified|concept|allowance/i.test(roleText);
  return {
    fields,
    fieldSource:
      part.dimensions !== undefined
        ? 'dimensions'
        : part.geometry !== undefined
          ? 'geometry'
          : 'unavailable',
    role: roleText,
    maturity: envelope
      ? 'Simplified or conceptual envelope; detailed internal geometry is not established.'
      : part.mesh_url
        ? 'Recorded CAD mesh available; nominal geometry is not as-built verification.'
        : 'Recorded CAD mesh unavailable; dimensions alone do not establish detailed geometry.',
    wallAvailable: ['wall_m', 'wall_thickness_m', 'wall_mm', 'wall_thickness_mm'].some(
      (key) => typeof fields[key] === 'number' && Number.isFinite(fields[key]) && fields[key] > 0,
    ),
  };
}

export function PartDimensions({
  vehicle,
  partId,
}: {
  vehicle: InspectionDocument;
  partId: string;
}) {
  const part = vehicle.parts.find((candidate) => candidate.id === partId);
  if (!part)
    return (
      <p>
        Dimensions unavailable: component {partId} is not mapped in source {vehicle.id}.
      </p>
    );
  const model = partDimensionModel(part);
  const representation = evidenceRecord(part.representation);
  const rows = (fields: Record<string, JsonValue | undefined>) => (
    <dl className="research-dimension-list">
      {Object.entries(fields).map(([key, value]) => (
        <div key={key}>
          <dt>
            {names[key] || key.replaceAll('_', ' ')}
            <small>{key}</small>
          </dt>
          <dd>{dimensionValue(key, value)}</dd>
        </div>
      ))}
    </dl>
  );
  const tolerances = part.engineering?.tolerances_mm;
  return (
    <div className="research-part-dimensions">
      <p>
        <strong>{part.name || part.id}</strong> · source <code>{vehicle.id}</code> · representation:{' '}
        {model.role}
      </p>
      <p>
        {model.maturity}{' '}
        {representation?.description ? evidenceText(representation.description) : ''}
      </p>
      <h4>Size from source {model.fieldSource}</h4>
      <p>
        Values are display conversions only. Radius is distance from the axis; diameter is the full
        width across it. A box gives occupied bounds, not internal construction. Display rounding
        does not add measurement precision.
      </p>
      {Object.keys(model.fields).length ? (
        rows(model.fields)
      ) : (
        <p>Dimensions unavailable — no source dimensions or geometry supplied.</p>
      )}
      {!['length_m', 'length_mm', 'bbox_m', 'bbox_mm'].some((key) => key in model.fields) && (
        <p>Axial length unavailable.</p>
      )}
      {!['diameter_m', 'diameter_mm', 'od_m', 'od_mm'].some((key) => key in model.fields) && (
        <p>
          Diameter unavailable as a supplied value; no diameter is derived from another dimension.
        </p>
      )}
      {!model.wallAvailable && (
        <p>
          Wall thickness unavailable. An outside diameter, radius or box does not establish a hollow
          tube; no wall thickness is inferred.
        </p>
      )}
      {part.cad_bounding_size_mm && (
        <>
          <h4>Recorded CAD bounds</h4>
          {rows({ cad_bounding_size_mm: part.cad_bounding_size_mm })}
          <p>Bounding extents in source order; not wall thickness or internal dimensions.</p>
        </>
      )}
      {part.dimensions && part.geometry && (
        <details>
          <summary>Separate geometry record (not merged with dimensions)</summary>
          {rows(part.geometry)}
        </details>
      )}
      <h4>Location and coordinate reference</h4>
      <p>
        Inspection station convention: origin at the nose tip, increasing aft. Body +X points toward
        the nose, opposite increasing station. Stations are absolute; the parent identifies assembly
        membership, not an additional position offset. This is the vehicle schema convention, not a
        claim about an unspecified mesh frame.
      </p>
      {rows({
        position_m: part.location?.position_m ?? part.position_m,
        cg_station_m: part.location?.cg_station_m,
        lateral_offset_m: part.location?.lateral_offset_m,
      })}
      <p>
        Mesh frame: {vehicle.mesh_frame || 'Unavailable — not supplied'}. Transverse values retain
        source ordering; an absent offset is not assumed to be zero.
      </p>
      <h4>Material and mass basis</h4>
      {rows({
        material: part.material || undefined,
        material_profile: part.engineering?.material_profile,
        property_basis: part.engineering?.property_basis,
        mass_kg: part.mass_kg,
        mass_basis: part.mass_basis,
        cad_mass_kg: part.cad_mass_kg ?? part.cad_mass?.mass_kg,
        cad_mass_basis: part.cad_mass?.basis ?? part.cad?.mass_basis,
        subtree_mass_kg: part.subtree_mass_kg,
      })}
      <p>
        Component, CAD and subtree masses are separate source quantities, not values to add
        together. A subtree can include child components. No density or geometry-derived mass is
        calculated here.
      </p>
      {part.mass_basis && massBasisExplanation[part.mass_basis] && (
        <p>{massBasisExplanation[part.mass_basis]}</p>
      )}
      {part.estimate && <p>The source explicitly marks this component as estimated.</p>}
      <h4>Source tolerances and assumptions</h4>
      {tolerances && Object.keys(tolerances).length ? (
        rows(
          Object.fromEntries(
            Object.entries(tolerances).map(([key, value]) => [`${key}_mm`, value]),
          ),
        )
      ) : (
        <p>Tolerances unavailable — no source tolerance fields supplied.</p>
      )}
      <p>
        Tolerance entries retain their source meaning; no ± convention, fit acceptance or
        manufacturing capability is inferred.
      </p>
      {part.engineering?.service_notes && <p>{part.engineering.service_notes}</p>}
      {part.manufacturing && (
        <details>
          <summary>Manufacturing assumptions supplied by source</summary>
          <pre>{JSON.stringify(part.manufacturing, null, 2)}</pre>
        </details>
      )}
      <h4>Dimension provenance</h4>
      {rows({
        specification_path: part.source?.spec_path ?? part.source?.spec,
        cad_generator: part.source?.cad_generator ?? part.source?.cad,
        shape_sha256: part.source?.shape_sha256,
      })}
    </div>
  );
}
