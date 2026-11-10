import type { InspectionDocument, JsonValue } from '../types';
import { admitDraftRevision } from './draftLibraryClient';
import type { DraftRevision } from './draftLibraryClient';

export interface DraftReviewExport {
  filename: string;
  text: string;
  /** Exact UTF-8 bytes of text, including its final newline. */
  bytes: Uint8Array<ArrayBuffer>;
  /** Digest of these exported bytes, never of the original server source bytes. */
  sha256: string;
}

/** Preserve JSON values, reject silent coercion and take an independent snapshot.
 * Ordering is for this review format, not the Python store's canonical encoding.
 */
function orderedJson(value: unknown, ancestors = new Set<object>()): JsonValue {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return value;
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new Error('Review export requires finite JSON numbers.');
    return value;
  }
  if (typeof value !== 'object') throw new Error('Review export requires saved JSON values.');
  if (ancestors.has(value)) throw new Error('Review export cannot contain a cycle.');
  if (Object.getOwnPropertySymbols(value).length)
    throw new Error('Review export cannot contain non-JSON properties.');
  const prototype = Object.getPrototypeOf(value);
  if (!Array.isArray(value) && prototype !== Object.prototype && prototype !== null)
    throw new Error('Review export requires plain saved JSON objects.');
  ancestors.add(value);
  try {
    if (Array.isArray(value)) {
      return Array.from(value, (entry) => orderedJson(entry, ancestors));
    }
    const descriptors = Object.getOwnPropertyDescriptors(value);
    const entries = Object.keys(value)
      .sort()
      .map((key) => {
        const descriptor = descriptors[key];
        if (!Object.hasOwn(descriptor, 'value'))
          throw new Error('Review export cannot evaluate accessor properties.');
        return [key, orderedJson(descriptor.value, ancestors)] as const;
      });
    return Object.fromEntries(entries);
  } finally {
    ancestors.delete(value);
  }
}

/** Build one source-fork review copy. No fetch, download, import or store mutation.
 * The caller must pass a saved snapshot, not its unsaved DraftEditor fields.
 * Admission validates original metadata/lineage before any export is produced.
 */
export async function exportDraftReviewRecord(
  revision: DraftRevision,
  vehicle: InspectionDocument,
): Promise<DraftReviewExport> {
  const copy = orderedJson(revision);
  const admitted = await admitDraftRevision(copy, vehicle);
  const document = orderedJson({
    schema_version: 1,
    format: 'rp1-saved-source-fork-review-v1',
    purpose: 'Structured review copy of one saved, unresolved source-fork revision',
    scope: {
      source_fork_only: true,
      status: 'unresolved_source_fork',
      included_revision_count: 1,
      complete_history_embedded: false,
      parent_history:
        'Parent revision identity is preserved; ancestor revision contents are not embedded',
      geometry_assets_embedded: false,
      geometry_scope:
        'Source asset references are retained; no CAD, mesh, image or other asset bytes are embedded or fetched',
      resolved_candidate: false,
      simulation_configuration: false,
      simulation_eligible: false,
      engineering_accepted: false,
      flight_ready: false,
      import_or_restore_supported: false,
      byte_exact_store_backup: false,
    },
    serialization: {
      encoding: 'UTF-8',
      json_format:
        'ECMAScript JSON.stringify with recursively sorted object keys, two-space indentation and one final newline',
      numeric_scope:
        'Parsed JSON values are preserved; numeric lexical forms may change, including Python 1.0 becoming JavaScript 1',
      source_sha256_scope:
        'draft.source_sha256 identifies the original server canonical source snapshot; it is not a digest of the reconstructed export draft.source bytes',
      revision_sha256_scope:
        'Original saved metadata revision identity, validated by existing draft admission; not the review-file digest',
      export_sha256_scope:
        'Returned separately as SHA-256 of the actual exported UTF-8 bytes; no self-referential file digest is embedded',
      restoration_scope:
        'Structured review only; not a byte-exact store backup, import/restore artifact, adopted candidate or simulation configuration',
    },
    draft: admitted,
  });
  const text = `${JSON.stringify(document, null, 2)}\n`;
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  const sha256 = Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('');
  return {
    filename: `rp1-draft-review-${admitted.draft_id}-r${admitted.sequence}-${admitted.revision_sha256.slice(0, 12)}.json`,
    text,
    bytes,
    sha256,
  };
}
