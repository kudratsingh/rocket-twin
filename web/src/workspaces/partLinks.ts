import type { InspectionDocument } from '../types';

/** A part is meaningful only inside its exact saved design revision. */
export function readPartLink(search: string, source: InspectionDocument) {
  const params = new URLSearchParams(search);
  const part = params.get('part');
  const sha = String(
    source.identity?.specification_sha256 || source.identity?.resolved_spec_sha256 || '',
  );
  const bad = ['design', 'spec', 'part', 'cad'].some((key) => params.getAll(key).length > 1);
  if (
    bad ||
    (part !== null && !/^[a-f0-9]{64}$/.test(sha)) ||
    (params.has('design') && params.get('design') !== source.id) ||
    (params.has('spec') && params.get('spec') !== sha) ||
    (params.has('cad') &&
      params.get('cad') !==
        (source.identity?.cad_revision_sha256 || source.identity?.cad_revision)) ||
    (part !== null &&
      (!part ||
        !params.has('design') ||
        !params.has('spec') ||
        !source.parts.some((p) => p.id === part)))
  )
    return {
      part: null,
      notice:
        'Part link unavailable: the design, revision or part does not match this source. No historical part is substituted.',
    };
  return { part, notice: null };
}

export function partHref(
  href: string,
  source: InspectionDocument,
  part: string | null,
  workspace: 'design' | 'engineering' | 'analysis' = 'design',
) {
  if (part !== null && !source.parts.some((p) => p.id === part))
    throw new Error('Unknown source part');
  const sha = String(
    source.identity?.specification_sha256 || source.identity?.resolved_spec_sha256 || '',
  );
  if (!/^[a-f0-9]{64}$/.test(sha)) throw new Error('Source revision unavailable');
  const url = new URL(href, 'http://local.invalid');
  url.searchParams.delete('cad');
  url.searchParams.set('workspace', workspace);
  url.searchParams.set('design', source.id);
  url.searchParams.set(
    'spec',
    String(source.identity?.specification_sha256 || source.identity?.resolved_spec_sha256 || ''),
  );
  if (part === null) url.searchParams.delete('part');
  else url.searchParams.set('part', part);
  if (workspace === 'engineering') url.searchParams.set('view', 'rp1-connections');
  return `${url.pathname}${url.search}${url.hash}`;
}
