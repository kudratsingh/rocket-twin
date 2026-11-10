import manifest from '../../../docs/studies/frontend-flight-computer-source-20261109/source-manifest.json';
import type { InspectionDocument, Part } from '../types';

export const FLIGHT_COMPUTER_SOURCE_MANIFEST_SHA256 =
  '952b973b6c7eb3489eb07f9becce178c024f5e37f80ebb28a442f9d0bfab8923';
const CONFIGURATION = 'G80-F2-RP1-AD1-definition-v2';
const SPECIFICATION = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
const SPEC_PATH = 'configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml';
const AUDIT_PATH = 'docs/studies/frontend-flight-computer-source-20261109/source-audit.md';
const OFFICIAL_REFERENCE = 'https://www.pjrc.com/store/teensy41_pins.html';
// Immutable source audit commit; the finding does not select this reference product.
export const FLIGHT_COMPUTER_AUDIT_REVISION = '2308648ecd2c4dbce857350316088524c10986ec';
const repositoryFile = (path: string, revision: string) =>
  `https://github.com/kudratsingh/rocket-twin/blob/${revision}/${path}`;

/** Only the audited frozen source allocation, never a board inferred from a box. */
export function hasFlightComputerSourceFinding(
  vehicle: InspectionDocument,
  selectedPart: Part | null,
): boolean {
  const frozen = manifest.frozen_source;
  const lead = manifest.reference_lead;
  const sourcePin = manifest.local_inputs.find((entry) => entry.path === SPEC_PATH);
  return (
    manifest.schema_version === 1 &&
    manifest.id === 'rp1-flight-computer-source-audit-20261109' &&
    frozen.configuration_id === CONFIGURATION &&
    frozen.part_id === 'flight_computer' &&
    frozen.exact_manufacturer === null &&
    frozen.exact_product === null &&
    frozen.exact_revision === null &&
    frozen.estimate === true &&
    frozen.bbox_mm.join(',') === '61,18,6' &&
    frozen.mass_kg === 0.012 &&
    sourcePin?.sha256 === SPECIFICATION &&
    lead.family === 'Teensy 4.1' &&
    lead.adopted === false &&
    lead.populated_height_mm === null &&
    lead.installed_transform === null &&
    lead.nominal_xy_mm.join(',') === '60.96,17.78' &&
    lead.nominal_xy_minus_frozen_envelope_mm.join(',') === '-0.04,-0.22' &&
    manifest.licence_and_redistribution.derived_populated_asset_admitted === false &&
    manifest.disposition.status === 'STOP_SOURCE_IDENTITY_AND_REFERENCE_DETAIL_GAPS' &&
    manifest.resources.some(
      (entry) => entry.id === 'pjrc-pins-variant' && entry.url === OFFICIAL_REFERENCE,
    ) &&
    vehicle.id === CONFIGURATION &&
    vehicle.identity?.configuration_id === CONFIGURATION &&
    vehicle.identity.specification_sha256 === SPECIFICATION &&
    selectedPart !== null &&
    selectedPart.id === 'flight_computer' &&
    vehicle.parts.includes(selectedPart)
  );
}

/** Read-only source finding; existing model, inspector actions and CAD stay intact. */
export function FlightComputerSourceFinding({
  vehicle,
  selectedPart,
}: {
  vehicle: InspectionDocument;
  selectedPart: Part | null;
}) {
  if (!hasFlightComputerSourceFinding(vehicle, selectedPart)) return null;
  return (
    <section
      className="notice small"
      aria-label="Flight computer source identity"
      style={{ display: 'block', minWidth: 0, overflowWrap: 'anywhere' }}
    >
      <h4>Flight-computer product not selected</h4>
      <p>
        This frozen record allocates a generic Cortex-M7 flight computer. The exact manufacturer,
        SKU and board revision are unknown, so detailed board CAD is unavailable for this source.
      </p>
      <p>
        <strong>61 × 18 × 6 mm and 12 g are estimates.</strong> Actual populated height, mounting
        pattern, connector population and installed fit remain unknown. The displayed box represents
        this source allocation.
      </p>
      <details>
        <summary>Official reference checked · Teensy not selected</summary>
        <p>
          <strong>Teensy 4.1 is not selected.</strong> It was checked only as an unadopted
          reference. PJRC describes a nominal 60.96 × 17.78 mm form factor: 0.04 mm shorter and 0.22
          mm narrower than the estimated RP1 box. Similar dimensions do not identify the board or
          prove fit; populated height remains unavailable.
        </p>
        <p>
          The bounded audit did not verify a controlled manufacturer 3D assembly or an applicable
          asset redistribution licence. No populated IC bodies, traces or connector geometry are
          inferred. No part replacement or mass credit follows from this reference.
        </p>
        <p>
          <a href={OFFICIAL_REFERENCE} target="_blank" rel="noreferrer">
            PJRC nominal reference · unadopted
          </a>
          {' · '}
          <a
            href={repositoryFile(AUDIT_PATH, FLIGHT_COMPUTER_AUDIT_REVISION)}
            target="_blank"
            rel="noreferrer"
          >
            Read the flight-computer source audit
          </a>
          {' · '}
          <a
            href={repositoryFile(SPEC_PATH, 'd46341f9c5e8974e383a7ef2d0e13385eff366e2')}
            target="_blank"
            rel="noreferrer"
          >
            Open frozen source specification
          </a>
        </p>
        <p>
          Source: <code>parts[id=flight_computer]</code> · specification SHA-256:{' '}
          <code>{SPECIFICATION}</code>
        </p>
      </details>
    </section>
  );
}
