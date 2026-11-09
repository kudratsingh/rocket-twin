import { useEffect, useState } from 'react';
import type { InspectionDocument } from '../types';
import { loadRp1Connections } from '../workbench/rp1Connections';
import type { Rp1ConnectionsDocument } from '../workbench/rp1Connections';
import { rp1PartEvidenceLinks } from '../workbench/rp1PartEvidenceLinks';

export default function Rp1PartEvidenceLinks({
  design,
  partId,
}: {
  design: InspectionDocument;
  partId: string;
}) {
  const [document, setDocument] = useState<Rp1ConnectionsDocument | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    void loadRp1Connections(controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setDocument(value);
      })
      .catch(() => {
        if (!controller.signal.aborted) setError('Recorded AD1 connection source unavailable.');
      });
    return () => controller.abort();
  }, []);
  const result = document ? rp1PartEvidenceLinks(design, partId, document) : null;
  return (
    <section className="detail-section" aria-label="Matching Engineering connections">
      <h3>Engineering connections</h3>
      {error ? (
        <p role="status">{error}</p>
      ) : result ? (
        <>
          <p>{result.message}</p>
          {result.links.length > 0 && (
            <ul>
              {result.links.map((link) => (
                <li key={link.id}>
                  <a href={link.href}>{link.label}</a>
                </li>
              ))}
            </ul>
          )}
          {result.sourceStatus && (
            <p className="small muted">Source status: {result.sourceStatus}</p>
          )}
        </>
      ) : (
        <p role="status">Loading source-pinned AD1 connections…</p>
      )}
    </section>
  );
}
