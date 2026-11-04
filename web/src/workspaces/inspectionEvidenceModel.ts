import type { InspectionDocument, JsonValue, Part } from '../types';

export function evidenceRecord(value: JsonValue | undefined): Record<string, JsonValue> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value) ? value : null;
}

export function evidenceStrings(value: JsonValue | undefined): string[] {
  if (typeof value === 'string' && value.trim()) return [value];
  return Array.isArray(value)
    ? value.flatMap((item) => (typeof item === 'string' ? [item] : []))
    : [];
}

export function evidenceText(value: JsonValue | undefined): string {
  if (value === undefined || value === null) return 'Not supplied';
  return typeof value === 'string' ? value : JSON.stringify(value);
}

export type EvidenceEndpoint = { id: string; label: string; mapped: boolean };
export function evidenceEndpoints(
  document: InspectionDocument,
  value: JsonValue | undefined,
): EvidenceEndpoint[] {
  return [...new Set(evidenceStrings(value))].map((id) => {
    const part = document.parts.find((candidate) => candidate.id === id);
    return { id, label: part?.name || id, mapped: !!part };
  });
}

/** Only declared hierarchy and source record endpoints; no proximity or name matching. */
export function componentEvidence(document: InspectionDocument, selectedId: string | null) {
  const part = document.parts.find((candidate) => candidate.id === selectedId);
  if (!part) return null;
  const records = (values: JsonValue[] | undefined) =>
    (values || []).flatMap((value) => {
      const record = evidenceRecord(value);
      return record ? [record] : [];
    });
  return {
    part,
    parent: evidenceEndpoints(document, part.parent ?? undefined),
    children: evidenceEndpoints(
      document,
      document.parts.filter((candidate) => candidate.parent === part.id).map((child) => child.id),
    ),
    interfaces: records(part.connections),
    requirements: records(part.requirements),
    failures: records(part.fmea_records),
    statuses: evidenceRecord(part.evidence_status),
  };
}

/** A selectable endpoint is checked again against this exact document at activation. */
export function selectEvidenceEndpoint(
  document: InspectionDocument,
  id: string,
  select: (id: string) => void,
): boolean {
  if (!document.parts.some((part: Part) => part.id === id)) return false;
  select(id);
  return true;
}
