import type { InspectionDocument } from '../types';
import { partHref, readPartLink } from './partLinks.ts';

interface SelectionChange {
  selectedId: string | null;
  selectionIntent: number;
}

/** Loading resets are not an instruction to erase a source-bound incoming part. */
export function inspectionSelectionHref(
  href: string,
  source: InspectionDocument,
  state: SelectionChange,
  previous: SelectionChange,
  workspace: 'design' | 'analysis',
): string | null {
  if (
    state.selectedId === previous.selectedId ||
    state.selectionIntent === previous.selectionIntent ||
    !Number.isSafeInteger(state.selectionIntent) ||
    state.selectionIntent < 0 ||
    readPartLink(new URL(href, 'http://local.invalid').search, source).notice ||
    (state.selectedId !== null && !source.parts.some((part) => part.id === state.selectedId))
  )
    return null;
  return partHref(href, source, state.selectedId, workspace);
}
