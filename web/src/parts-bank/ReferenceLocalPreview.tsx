import { useEffect, useState } from 'react';
import LocalTemplatePreview from './LocalTemplatePreview';
import ReferenceDatumGuide, { ReferenceDatumOverlay } from './ReferenceDatumGuide';
import type { DatumFeatureId } from './referenceDatumGeometry';
import { createReferencePartsClient } from './referencePartsClient';
import type { ReferencePartDetail } from './referencePartsClient';
import type { TemplateRepresentation } from './templateGeometry';

/** Inspect the existing registered solid; analytic guides do not alter its CAD. */
export default function ReferenceLocalPreview({
  representation,
}: {
  representation: TemplateRepresentation;
}) {
  const [detail, setDetail] = useState<ReferencePartDetail | null>(null);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<DatumFeatureId | null>('axis');
  useEffect(() => {
    const abort = new AbortController();
    setDetail(null);
    setError('');
    setSelected('axis');
    createReferencePartsClient()
      .readForTemplate(representation.template_id, representation, abort.signal)
      .then((value) => {
        if (!abort.signal.aborted) setDetail(value);
      })
      .catch((reason: unknown) => {
        if (!abort.signal.aborted)
          setError(reason instanceof Error ? reason.message : 'Reference datums unavailable.');
      });
    return () => abort.abort();
  }, [representation]);
  const definition = detail?.availability.geometry_available ? detail.definition : null;
  const ghost = definition !== null && selected === 'bore';
  return (
    <div className="reference-local-inspection">
      {error ? (
        <p role="alert">
          Analytic datums unavailable: {error} The registered local CAD remains separate.
        </p>
      ) : !detail ? (
        <p role="status">Checking the matching local reference and analytic frame…</p>
      ) : !definition ? (
        <p role="status">
          Analytic datum overlay unavailable: registered local geometry cache is missing. No
          geometry was generated. The CAD preview below verifies its own registered asset bytes.
        </p>
      ) : (
        <ReferenceDatumGuide
          definition={definition}
          selectedFeature={selected}
          onSelect={setSelected}
        />
      )}
      {ghost && (
        <p role="status">
          Bore guide selected: the solid is ghosted for visibility. This changes display opacity
          only; STEP bytes and local coordinates are unchanged. Clear the guide or select another
          datum to restore the solid.
        </p>
      )}
      <LocalTemplatePreview
        representation={representation}
        ghost={ghost}
        overlay={
          definition ? (
            <ReferenceDatumOverlay
              definition={definition}
              selectedFeature={selected}
              onSelect={setSelected}
            />
          ) : undefined
        }
      />
    </div>
  );
}
