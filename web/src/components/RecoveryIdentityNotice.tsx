import type { InspectionDocument, Part } from '../types';
import { recoveryIdentityFinding } from './recoveryIdentityFinding';

const repositoryFile = (path: string) =>
  `https://github.com/kudratsingh/rocket-twin/blob/d46341f9c5e8974e383a7ef2d0e13385eff366e2/${path}`;

/** Read-only source explanation; does not change generic inspection/export eligibility. */
export function RecoveryIdentityNotice({
  vehicle,
  selectedPart,
}: {
  vehicle: InspectionDocument;
  selectedPart: Part | null;
}) {
  const finding = recoveryIdentityFinding(vehicle, selectedPart);
  if (!finding) return null;
  return (
    <section
      className="notice small"
      aria-label="Recovery controller source identity"
      style={{ display: 'block', minWidth: 0, overflowWrap: 'anywhere' }}
    >
      <h4>Recovery controller identity unresolved</h4>
      <p>
        This source record names two different controllers. Its learning and dimension records
        propose <strong>{finding.proposedName}</strong>, while its engineering function identifies{' '}
        <strong>{finding.legacyName}</strong>.
      </p>
      <p>
        The exact controller, board revision, mounting and power details remain unresolved. The 3D
        representation for this record is a generic estimated envelope, not controller-specific CAD
        or a verified installed assembly.
      </p>
      <p>
        Different controllers can need different mounts and power wiring. Keep this record generic
        until the intended controller and revision are consistent. Its existing inspection files do
        not establish either installation.
      </p>
      <details>
        <summary>Exact source records and evidence</summary>
        <p>
          Source: <code style={{ overflowWrap: 'anywhere' }}>{finding.sourcePath}</code>
        </p>
        <ul>
          {finding.primaryLocators.map((locator) => (
            <li key={locator}>
              <code>{locator}</code> · Apogee proposal
            </li>
          ))}
          <li>
            <code>{finding.legacyLocator}</code> · EasyMini v3.0 legacy function
          </li>
        </ul>
        <p>
          Specification SHA-256:{' '}
          <code style={{ overflowWrap: 'anywhere' }}>{finding.specificationSha256}</code>
        </p>
        <p>
          <a href={repositoryFile(finding.sourcePath)} target="_blank" rel="noreferrer">
            Open frozen-source specification
          </a>{' '}
          ·{' '}
          <a href={repositoryFile(finding.evidencePath)} target="_blank" rel="noreferrer">
            Read the recorded source finding
          </a>{' '}
          ·{' '}
          <a href={repositoryFile(finding.evidenceDataPath)} target="_blank" rel="noreferrer">
            Source evidence JSON
          </a>
        </p>
      </details>
    </section>
  );
}
