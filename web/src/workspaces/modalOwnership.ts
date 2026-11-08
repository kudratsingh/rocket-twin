/** Native dialog keys belong to the dialog, before sidebar/Focus capture shortcuts. */
export function ownedByOpenDialog(target: unknown): boolean {
  if (!target || typeof target !== 'object') return false;
  const element = target as { closest?: (selector: string) => unknown };
  return typeof element.closest === 'function' && !!element.closest('dialog[open]');
}
